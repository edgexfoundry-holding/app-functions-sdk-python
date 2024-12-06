#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for App Functions Runtime
"""
import asyncio
import base64
import json
import threading
import time
from copy import deepcopy
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Optional, Tuple

import isodate
from isodate import ISO8601Error
from pyformance.meters import Counter

from ..constants import (PIPELINE_ID_TXT, PIPELINE_MESSAGES_PROCESSED_NAME,
                         PIPELINE_MESSAGE_PROCESSING_TIME_NAME, PIPELINE_PROCESSING_ERRORS_NAME,
                         STORE_FORWARD_QUEUE_SIZE_NAME)
from ...bootstrap.container.configuration import configuration_from
from ...bootstrap.container.logging import logging_client_from
from ...bootstrap.container.metrics import metrics_manager_from
from ...bootstrap.container.store import store_client_from
from ...bootstrap.di.container import Container
from ...bootstrap.interface.metrics import MetricsManager
from ...constants import TOPIC_WILDCARD, TOPIC_SINGLE_LEVEL_WILDCARD, TOPIC_LEVEL_SEPERATOR, \
    KEY_RECEIVEDTOPIC, KEY_DEVICE_NAME, KEY_PROFILE_NAME, KEY_SOURCE_NAME, KEY_PIPELINEID, \
    DEFAULT_PIPELINE_ID
from ...contracts import errors
from ...contracts.common import constants
from ...contracts.common.constants import CONTENT_TYPE_JSON, CORRELATION_HEADER
from ...contracts.dtos.event import Event
from ...contracts.dtos.requests.event import AddEventRequest
from ...contracts.dtos.store_object import new_stored_object, StoredObject
from ...functions.context import Context
from ...interfaces import FunctionPipeline, AppFunctionContext, AppFunction, calculate_pipeline_hash
from ...interfaces.messaging import MessageEnvelope
from ...sync.waitgroup import WaitGroup
from ...utils.helper import is_base64_encoded

DEFAULT_MIN_RETRY_INTERVAL = 1


@dataclass
class MessageError:
    """
    MessageError represents an error that occurred during message processing
    """
    err: errors.EdgeX
    err_code: int


def process_custom_payload(envelope: MessageEnvelope, target: Any):
    """
    Processes custom types by unmarshalling into the target type.
    """
    content_type = envelope.contentType.lower()
    if content_type != CONTENT_TYPE_JSON:
        raise ValueError(f"unsupported content type: {content_type}")

    try:
        json.loads(envelope.payload, object_hook=target.__dict__.update)
    except json.JSONDecodeError as e:
        raise ValueError(f"failed to decode JSON payload: {e}") from e


class FunctionsPipelineRuntime:
    """
    FunctionsPipelineRuntime represents the runtime environment for App Services' Functions
    Pipelines
    """

    def __init__(self, service_key: str, target_type: Any, dic: Container):
        self._service_key = service_key
        self._logger = logging_client_from(dic.get)
        self._pipelines = {}
        self.target_type = target_type
        self._dic = dic
        self.is_busy_copying_lock = threading.Lock()
        self.store_forward = new_store_and_forward(self, dic, service_key)

    def get_pipeline_by_id(self, pipeline_id: str) -> FunctionPipeline:
        """
        get_pipeline_by_id returns the pipeline with the provided id
        """
        return self._pipelines.get(pipeline_id)

    def _log_error(self, err: Exception, correlation_id: str):
        self._logger.error("%s. %s=%s", err, CORRELATION_HEADER, correlation_id)

    def get_default_pipeline(self) -> FunctionPipeline:
        """
        get_default_pipeline returns the default pipeline
        """
        default_pipeline = self._pipelines.get(DEFAULT_PIPELINE_ID)
        if default_pipeline is None:
            default_pipeline = self._add_function_pipeline(DEFAULT_PIPELINE_ID,
                                                           [TOPIC_WILDCARD], )
        return default_pipeline

    def remove_all_function_pipelines(self):
        """
        remove_all_function_pipelines removes all pipelines from the runtime
        """
        metric_manager = metrics_manager_from(self._dic.get)
        with self.is_busy_copying_lock:
            for pipeline_id, _ in self._pipelines.items():
                self.unregister_pipeline_metric(metric_manager,
                                                PIPELINE_MESSAGES_PROCESSED_NAME, pipeline_id)
                self.unregister_pipeline_metric(metric_manager,
                                                PIPELINE_MESSAGE_PROCESSING_TIME_NAME, pipeline_id)
                self.unregister_pipeline_metric(metric_manager,
                                                PIPELINE_PROCESSING_ERRORS_NAME, pipeline_id)
            self._pipelines.clear()

    def _add_function_pipeline(self, pipeline_id: str, topics: list[str],
                               *transforms: AppFunction) -> FunctionPipeline:
        """
        _add_function_pipeline adds a new pipeline to the runtime
        """
        pipeline = FunctionPipeline(pipeline_id, topics, *transforms)
        with self.is_busy_copying_lock:
            self._pipelines[pipeline_id] = pipeline

        metric_manager = metrics_manager_from(self._dic.get)
        self.register_pipeline_metric(metric_manager, PIPELINE_MESSAGES_PROCESSED_NAME,
                                      pipeline.id, pipeline.message_processed)
        self.register_pipeline_metric(metric_manager, PIPELINE_MESSAGE_PROCESSING_TIME_NAME,
                                      pipeline.id, pipeline.message_processing_time)
        self.register_pipeline_metric(metric_manager, PIPELINE_PROCESSING_ERRORS_NAME,
                                      pipeline.id, pipeline.processing_errors)
        return pipeline

    def add_function_pipeline(self, pipeline_id: str, topics: list[str],
                              *transforms: AppFunction) -> Optional[errors.EdgeX]:
        """
        add_function_pipeline is thread safe to set transforms
        """
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline is not None:
            return errors.new_common_edgex(errors.ErrKind.STATUS_CONFLICT,
                                           f"pipeline with Id='{pipeline_id}' already exists")

        self._add_function_pipeline(pipeline_id, topics, *transforms)
        return None

    def set_functions_pipeline_transforms(self, pipeline_id: str, *transforms: AppFunction):
        """
        set_functions_pipeline_transforms sets the transforms for the pipeline with the provided id
        """
        pipeline = self._pipelines[pipeline_id]
        if pipeline is None:
            self._logger.warn(f"Unable to set transforms for {pipeline_id} pipeline: Pipeline "
                              f"not found")
            return
        with self.is_busy_copying_lock:
            pipeline.transforms = transforms
            pipeline.hash = calculate_pipeline_hash(*transforms)

        self._logger.info(f"Transform set for {pipeline_id} pipeline")

    def set_default_functions_pipeline(self, *transforms: AppFunction):
        """
        set_default_functions_pipeline sets the default pipelines for the runtime
        """
        pipeline = self.get_default_pipeline()
        self.set_functions_pipeline_transforms(pipeline.id, *transforms)

    def get_matching_pipelines(self, incoming_topic: str) -> list[FunctionPipeline]:
        """
        get_matching_pipelines returns a list of pipelines that match the incoming_topic
        """
        matches = []
        for _, pipeline in self._pipelines.items():
            if topic_matches(incoming_topic, pipeline.topics):
                matches.append(pipeline)
        return matches

    def decode_message(self, ctx: AppFunctionContext, envelope: MessageEnvelope) -> Any:
        """
        decode_message decodes the message received in the envelope and returns the data to be
        processed
        """
        if envelope is None:
            return None, False

        if self.target_type is None:
            self.target_type = Event()

        # Must make a copy of the type so that data isn't retained between calls for custom types
        target = deepcopy(self.target_type)

        if isinstance(target, bytes):
            self._logger.debug("Expecting raw byte data")
            target = envelope.payload
        elif isinstance(target, Event):
            self._logger.debug("Expecting an AddEventRequest or Event DTO")
            try:
                target = self.process_event_payload(envelope)
            except (ValueError, errors.EdgeX) as e:
                self._log_error(e, envelope.correlationID)
                return None
            ctx.add_value(KEY_DEVICE_NAME, target.deviceName)
            ctx.add_value(KEY_PROFILE_NAME, target.profileName)
            ctx.add_value(KEY_SOURCE_NAME, target.sourceName)
        else:
            custom_type_name = type(target).__name__
            self._logger.debug(f"Expecting a custom type of {custom_type_name}")
            try:
                process_custom_payload(envelope, target)
            except ValueError as e:
                self._log_error(ValueError(f"unable to process custom object received of type "
                                           f"'{custom_type_name}': {e}"), envelope.correlationID)
                return None

        ctx.set_correlation_id(envelope.correlationID)
        ctx.set_input_content_type(envelope.contentType)
        ctx.add_value(KEY_RECEIVEDTOPIC, envelope.receivedTopic)

        return target

    def process_event_payload(self, envelope: MessageEnvelope) -> Event:
        """
        process_event_payload processes the event payload from the message envelope
        """
        content_type = envelope.contentType.lower()
        if content_type != CONTENT_TYPE_JSON:
            raise ValueError(f"unsupported content type: {content_type}")

        try:
            # note that the message envelope received from the message bus is in JSON format
            # and the payload can be either plain-text bytes or decoded into base64 bytes, so we
            # need to determine if the payload is in base64 encoding and decode the payload here
            # before we can process it as an Event DTO
            if is_base64_encoded(envelope.payload):
                dto_bytes = base64.b64decode(envelope.payload)
            else:
                dto_bytes = envelope.payload
        except json.JSONDecodeError as e:
            raise ValueError(f"failed to decode JSON payload: {e}") from e
        self._logger.debug("Attempting to process Payload as an AddEventRequest DTO")
        try:
            request_dto = AddEventRequest.from_json(dto_bytes)  # pylint: disable=no-member
            event = request_dto.event
            return event
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.debug(f"Failed to process Payload as an AddEventRequest DTO: {e}"
                               f"Attempting to process Payload as an Event DTO")
        try:
            event = Event.from_json(dto_bytes)  # pylint: disable=no-member
            return event
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          f"failed to decode message envelope into "
                                          f"Event DTO: {e}")

    def process_message(self, ctx: AppFunctionContext, data: Any, pipeline: FunctionPipeline) -> (
            MessageError | None):
        """
        process_message process the decoded data
        """
        if len(pipeline.transforms) == 0:
            self._logger.debug(f"Pipeline {pipeline.id} has no transforms")
            return None

        self._logger.debug(f"Processing message with pipeline: {pipeline.id}")
        ctx.add_value(KEY_PIPELINEID, pipeline.id)

        self._logger.debug(f"Pipeline {pipeline.id} processing message with "
                           f"{len(pipeline.transforms)} transforms")

        return self.execute_pipeline(ctx, data, pipeline)

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def execute_pipeline(self, ctx: AppFunctionContext, data: Any, pipeline: FunctionPipeline,
                         start_position: int = 0, is_retry: bool = False) -> MessageError | None:
        """
        execute_pipeline executes the pipeline with the provided data
        """
        result = None
        continue_pipeline = False
        for function_index, func in enumerate(pipeline.transforms):
            if function_index < start_position:
                continue
            # clear retry data before each individual function execution
            ctx.set_retry_data(None)
            if result is None:
                continue_pipeline, result = func(ctx, data)
            else:
                continue_pipeline, result = func(ctx, result)

            if not continue_pipeline:
                if result is not None and isinstance(result, errors.EdgeX):
                    self._logger.error(f"Pipeline {pipeline.id} function #{function_index} resulted"
                                       f" in error: {result.debug_messages()} "
                                       f"({CORRELATION_HEADER}={ctx.correlation_id()})")
                    retry_data = ctx.retry_data()
                    if retry_data is not None and not is_retry:
                        self.store_forward.store_for_later_retry(
                            retry_data, ctx, pipeline, function_index)
                    pipeline.processing_errors.inc(1)
                    return MessageError(result, HTTPStatus.UNPROCESSABLE_ENTITY)
                break

            if isinstance(ctx, Context) and not is_retry and ctx.is_retry_triggered():
                threading.Thread(target=self.store_forward.trigger_retry).start()
                ctx.clone()

        return None

    # pylint: disable=too-many-positional-arguments
    def start_store_and_forward(
            self,
            app_wg: WaitGroup, app_ctx_done: threading.Event,
            store_forward_wg: WaitGroup, store_forward_ctx_done: threading.Event,
            service_key: str):
        """ start store and forward """
        self.store_forward.start_store_and_forward_retry_loop(
            app_wg, app_ctx_done, store_forward_wg, store_forward_ctx_done, service_key)

    def register_pipeline_metric(self, metric_manager: MetricsManager, metric_name: str,
                                 pipeline_id: str, metric: Any):
        """
        Register a metric with the provided name and pipeline id.
        """
        registered_name = metric_name.replace(PIPELINE_ID_TXT, pipeline_id, 1)
        try:
            metric_manager.register(registered_name, metric, {"pipeline": pipeline_id})
            self._logger.info("%s metric has been registered and will be reported (if enabled)",
                              metric_name)
        except errors.EdgeX as e:
            self._logger.warn("Unable to register %s metric. Metric will not be reported : %s",
                              registered_name, e)

    def unregister_pipeline_metric(self, metric_manager: MetricsManager, metric_name: str,
                                   pipeline_id: str):
        """
        Unregister a metric with the provided name and pipeline id.
        """
        registered_name = metric_name.replace(PIPELINE_ID_TXT, pipeline_id, 1)
        metric_manager.unregister(registered_name)


def topic_matches(incoming_topic: str, pipeline_topics: list[str]) -> bool:
    """
    topic_matches returns true if the incoming_topic matches any of the pipeline_topics
    """
    for topic in pipeline_topics:
        if topic == TOPIC_WILDCARD:
            return True

        wildcard_count = topic.count(TOPIC_WILDCARD) + topic.count(TOPIC_SINGLE_LEVEL_WILDCARD)
        if wildcard_count == 0:
            if incoming_topic == topic:
                return True
        else:

            topic_parts = topic.split(TOPIC_LEVEL_SEPERATOR)
            incoming_topic_parts = incoming_topic.split(TOPIC_LEVEL_SEPERATOR)

            if len(topic_parts) > len(incoming_topic_parts):
                continue

            for i, _ in enumerate(topic_parts):
                if topic_parts[i] == TOPIC_WILDCARD:
                    incoming_topic_parts[i] = TOPIC_WILDCARD
                elif topic_parts[i] == TOPIC_SINGLE_LEVEL_WILDCARD:
                    incoming_topic_parts[i] = TOPIC_SINGLE_LEVEL_WILDCARD

            incoming_with_wildcards = TOPIC_LEVEL_SEPERATOR.join(incoming_topic_parts)
            if incoming_with_wildcards.find(topic) == 0:
                return True
    return False


class StoreForwardInfo:
    """ StoreForwardInfo handle the retry process """

    # pylint: disable=too-many-arguments
    def __init__(self, runtime: FunctionsPipelineRuntime, dic: Container, service_key: str):
        self.runtime = runtime
        self.dic = dic
        self.lc = logging_client_from(dic.get)
        self.service_key = service_key
        self.data_count = Counter("")
        self.retry_in_progress_lock = threading.Lock()
        self.retry_in_progress = False

    # pylint: disable=too-many-positional-arguments
    def start_store_and_forward_retry_loop(
            self, app_wg: WaitGroup, app_ctx_done: threading.Event,
            store_forward_wg: WaitGroup, store_forward_ctx_done: threading.Event, service_key: str):
        """ start a loop for store and forward """

        app_wg.add(1)
        store_forward_wg.add(1)

        config = configuration_from(self.dic.get)
        store_client = store_client_from(self.dic.get)
        self.service_key = service_key

        items, err = store_client.retrieve_from_store(service_key)
        if err is not None:
            self.lc.error("Unable to initialize Store and Forward data count: "
                          "Failed to load items from DB: %v", err)
        else:
            self.data_count.clear()
            self.data_count.inc(len(items))

        def retry_loop():
            try:
                retry_interval_duration = isodate.parse_duration(
                    "PT" + config.Writable.StoreAndForward.RetryInterval.upper())
                retry_interval = retry_interval_duration.seconds
            except ISO8601Error as e:
                self.lc.warn(
                    "StoreAndForward RetryInterval failed to parse, %s",
                    e)
                retry_interval = DEFAULT_MIN_RETRY_INTERVAL

            if retry_interval < DEFAULT_MIN_RETRY_INTERVAL:
                self.lc.warn(
                    "StoreAndForward RetryInterval value %s is less than the allowed minimum value,"
                    " defaulting to %s seconds", retry_interval, DEFAULT_MIN_RETRY_INTERVAL)

            if config.Writable.StoreAndForward.MaxRetryCount < 0:
                self.lc.warn(
                    "StoreAndForward MaxRetryCount can not be less than 0, "
                    "defaulting to 1 seconds")
                config.Writable.StoreAndForward.MaxRetryCount = 1

            self.lc.info(
                "Starting StoreAndForward Retry Loop with %s seconds retry interval "
                "and %d max retries. %d stored items waiting for retry.",
                retry_interval,
                config.Writable.StoreAndForward.MaxRetryCount,
                len(items))

            start_time = time.time()
            next_time = start_time + retry_interval

            try:
                while not app_ctx_done.is_set() and not store_forward_ctx_done.is_set():
                    if time.time() < next_time:
                        continue

                    self.retry_stored_data(service_key)

                    start_time = time.time()
                    next_time = start_time + retry_interval
            finally:
                app_wg.done()
                store_forward_wg.done()
                self.lc.info("Exiting StoreAndForward Retry Loop")

        threading.Thread(target=retry_loop).start()

    def store_for_later_retry(
            self,
            payload: bytes,
            app_context: AppFunctionContext,
            pipeline: FunctionPipeline,
            pipeline_position: int):
        """ store data for later retry """

        item = new_stored_object(self.service_key, payload, pipeline.id,
                                 pipeline_position, pipeline.hash,
                                 app_context.get_values())
        item.correlationID = app_context.correlation_id()

        self.lc.trace("Storing data for later retry for pipeline '%s' (%s=%s)",
                      pipeline.id,
                      constants.CORRELATION_HEADER,
                      app_context.correlation_id())

        config = configuration_from(self.dic.get)
        if not config.Writable.StoreAndForward.Enabled:
            self.lc.error("Failed to store item for later retry for "
                          "pipeline '%s': StoreAndForward not enabled",
                          pipeline.id)
            return

        store_client = store_client_from(self.dic.get)
        _, err = store_client.store(item)
        if err is not None:
            self.lc.error(
                "Failed to store item for later retry for pipeline '%s': %s", pipeline.id, err)

        self.data_count.inc(1)

    def retry_stored_data(self, service_key: str):
        """ Skip if another thread is already doing the retry """
        if self.retry_in_progress:
            return

        with self.retry_in_progress_lock:
            try:
                self.retry_in_progress = True

                store_client = store_client_from(self.dic.get)

                items, err = store_client.retrieve_from_store(service_key)
                if err is not None:
                    self.lc.error("Unable to load store and forward items from DB: %s", err)
                    return

                self.lc.debug("%d stored data items found for retrying", len(items))

                if len(items) > 0:
                    items_to_remove, items_to_update = self.process_retry_items(items)

                    self.lc.debug(
                        " %d stored data items will be removed post retry", len(items_to_remove))
                    self.lc.debug(
                        " %d stored data items will be updated post retry", len(items_to_update))

                    for item in items_to_remove:
                        err = store_client.remove_from_store(item)
                        if err is not None:
                            self.lc.error(
                                "Unable to remove stored data item for "
                                "pipeline '%s' from DB, objectID=%s: %s",
                                item.pipelineId, err, item.id)

                    for item in items_to_update:
                        err = store_client.update(item)
                        if err is not None:
                            self.lc.error(
                                "Unable to update stored data item for "
                                "pipeline '%s' from DB, objectID=%s: %s",
                                item.pipelineId, err, item.id)

                    self.data_count.dec(len(items_to_remove))
            finally:
                self.retry_in_progress = False

    def process_retry_items(
            self, items: list[StoredObject]) -> Tuple[list[StoredObject], list[StoredObject]]:
        """ process the retry items """
        config = configuration_from(self.dic.get)

        items_to_remove: list[StoredObject] = []
        items_to_update: list[StoredObject] = []

        # Item will be removed from store if:
        #    - successfully retried
        #    - max retries exceeded
        #    - version no longer matches current Pipeline
        # Item will not be removed if retry failed and more retries available (hit 'continue' above)
        max_retry_count = config.Writable.StoreAndForward.MaxRetryCount
        for item in items:
            pipeline = self.runtime.get_pipeline_by_id(item.pipelineId)

            if pipeline is None:
                self.lc.error(
                    "Stored data item's pipeline '%s' no longer exists. Removing item from DB",
                    item.pipelineId)
                items_to_remove.append(item)
                continue

            if item.version != pipeline.hash:
                self.lc.error(
                    "Stored data item's pipeline Version doesn't match '%s' pipeline's Version. "
                    "Removing item from DB",
                    item.pipelineId)
                items_to_remove.append(item)
                continue

            if not self.retry_export_function(item, pipeline):
                item.retryCount += 1
                if max_retry_count == 0 or item.retryCount < max_retry_count:
                    self.lc.trace(
                        "Export retry failed for pipeline '%s'. retries=%d, "
                        "Incrementing retry count (%s=%s)",
                        item.pipelineId,
                        item.retryCount,
                        CORRELATION_HEADER,
                        item.correlationID)
                    items_to_update.append(item)
                    continue

                self.lc.trace(
                    "Max retries exceeded for pipeline '%s'. retries=%d, "
                    "Removing item from DB (%s=%s)",
                    item.pipelineId,
                    item.retryCount,
                    CORRELATION_HEADER,
                    item.correlationID)
                items_to_remove.append(item)

                # Note that item will be removed for DB below.
            else:
                self.lc.trace("Retry successful for pipeline '%s'. Removing item from DB (%s=%s)",
                              item.pipelineId,
                              CORRELATION_HEADER,
                              item.correlationID)
                items_to_remove.append(item)

        return items_to_remove, items_to_update

    def retry_export_function(self, item: StoredObject, pipeline: FunctionPipeline) -> bool:
        """ retry the export function """
        app_context = Context(item.correlationID, self.dic, "")

        for k, v in item.contextData.items():
            app_context.add_value(k.lower(), v)

        self.lc.trace("Retrying stored data for pipeline '%s' (%s=%s)",
                      item.pipelineId,
                      CORRELATION_HEADER,
                      app_context.correlation_id())

        return self.runtime.execute_pipeline(
            app_context,
            item.payload,
            pipeline,
            item.pipelinePosition,
            True) is None

    def trigger_retry(self):
        """ trigger the retry process """
        if self.data_count.counter > 0:
            config = configuration_from(self.dic.get)
            if not config.Writable.StoreAndForward.Enabled:
                self.lc.debug(
                    "Store and Forward not enabled, skipping triggering retry of failed data")
                return

            self.lc.debug("Triggering Store and Forward retry of failed data")
            self.retry_stored_data(self.service_key)


def new_store_and_forward(
        runtime: FunctionsPipelineRuntime, dic: Container, service_key: str) -> StoreForwardInfo:
    """ creates new StoreForward """
    sf = StoreForwardInfo(
        runtime=runtime,
        dic=dic,
        service_key=service_key,
    )
    lc = logging_client_from(dic.get)
    metrics_manager = metrics_manager_from(dic.get)
    if metrics_manager is None:
        lc.error("Unable to register %s metric: MetricsManager is not available.",
                 STORE_FORWARD_QUEUE_SIZE_NAME)
        return sf

    try:
        metrics_manager.register(STORE_FORWARD_QUEUE_SIZE_NAME, sf.data_count, None)
        lc.info("%s metric has been registered and will be reported (if enabled)",
                STORE_FORWARD_QUEUE_SIZE_NAME)
    except errors.EdgeX as e:
        lc.error("Unable to register metric %s. Collection will continue, "
                 "but metric will not be reported: %v",
                 STORE_FORWARD_QUEUE_SIZE_NAME, e)

    return sf
