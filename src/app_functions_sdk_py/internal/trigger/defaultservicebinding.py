#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines the `DefaultTriggerServiceBinding` and `DefaultTriggerMessageProcessor` classes
for managing the default trigger service binding and message processing in the application.

Classes:
    DefaultTriggerServiceBinding: Provides the default implementation for the service binding
                                  interface, managing the configuration, messaging client, and
                                  runtime for the trigger.
    DefaultTriggerMessageProcessor: Handles the processing of messages received by the trigger,
                                    orchestrating the runtime to pass the envelope to configured
                                    pipelines.

Usage:
    These classes are used to implement the default behavior for service binding and message
    processing in the application, allowing for the initialization, decoding, and processing of
    messages within the trigger context.

Example:
    service_binding = DefaultTriggerServiceBinding(logger, config, messaging_client,
                                                   pipeline_runtime)
    message_processor = DefaultTriggerMessageProcessor(service_binding)
"""
import threading
from typing import Any

from pyformance import meters

from .messageprocessor import MessageProcessor, PipelineResponseHandler
from .servicebinding import ServiceBinding
from ..common.config import ConfigurationStruct
from ..constants import MESSAGES_RECEIVED_NAME, INVALID_MESSAGES_RECEIVED_NAME
from ..runtime import FunctionsPipelineRuntime
from ...bootstrap.container.messaging import messaging_client_from
from ...bootstrap.container.secret import secret_provider_from
from ...bootstrap.interface.metrics import MetricsManager
from ...bootstrap.interface.secret import SecretProvider
from ...contracts.clients.logger import Logger
from ...contracts import errors
from ...functions.context import Context
from ...interfaces import FunctionPipeline, AppFunctionContext, ApplicationService
from ...interfaces.messaging import MessageClient, MessageEnvelope
from ...sync.waitgroup import WaitGroup


class DefaultTriggerServiceBinding(ServiceBinding):
    """
    Provides the default implementation for the service binding interface, managing the
    configuration, messaging client, and runtime for the trigger.

    Attributes:
        _runtime (FunctionsPipelineRuntime): The runtime for managing function pipelines.
        _svc (Service): The service instance.

    Methods:
        __init__: Initializes the DefaultTriggerServiceBinding with the given logger, config,
                  messaging client, and pipeline runtime.
        decode_message: Decodes the message received in the envelope and returns the data to be
                        processed.
        process_message: Provides access to the runtime's ProcessMessage function to process the
                         decoded data.
        logger: Provides access to this service's logger.
        config: Provides access to this service's configuration.
        messaging_client: Provides access to this service's messaging client.
        build_context: Builds the context for the trigger.
        get_matching_pipelines: Retrieves the pipelines that match the incoming topic.
    """
    # pylint: disable=too-many-arguments
    def __init__(self,
                 pipeline_runtime: FunctionsPipelineRuntime,
                 svc: ApplicationService):
        self._runtime = pipeline_runtime
        self._svc = svc

    def decode_message(self, ctx: AppFunctionContext, envelope: MessageEnvelope) -> Any:
        """
        decodes the message received in the envelope and returns the data to be processed
        """
        return self._runtime.decode_message(ctx, envelope)

    def process_message(self, ctx: AppFunctionContext, data: Any, pipeline: FunctionPipeline):
        """
        provides access to the runtime's ProcessMessage function to process the
        decoded data
        """
        self._runtime.process_message(ctx, data, pipeline)

    def logger(self) -> Logger:
        """
        provides access to this service's configuration for the trigger
        """
        return self._svc.logger()

    def config(self) -> ConfigurationStruct:
        """
        provides access to this service's configuration for the trigger
        """
        return self._svc.get_service_config()

    def build_context(self, envelope: MessageEnvelope) -> AppFunctionContext:
        """
        builds the context for the trigger
        """
        return Context(envelope.correlationID, self._svc.dic(), envelope.contentType)

    def get_matching_pipelines(self, incoming_topic: str) -> list[FunctionPipeline]:
        """
        get_matching_pipelines returns a list of pipelines that match the incoming_topic
        """
        return self._runtime.get_matching_pipelines(incoming_topic)

    def get_default_pipeline(self) -> FunctionPipeline:
        """
        get_default_pipeline provides access to the runtime's get_defaultPipeline function
        """
        return self._runtime.get_default_pipeline()

    def load_custom_config(self, config: Any, section_name: str):
        """
        load_custom_config provides access to the service's load_custom_config function
        """
        return self._svc.load_custom_config(config, section_name)

    def secret_provider(self) -> SecretProvider:
        """
        secret_provider provides access to the service's secret provider
        """
        return secret_provider_from(self._svc.dic().get)

    def messaging_client(self) -> MessageClient:
        """
        messaging_client provides access to the service's messaging client
        """
        return messaging_client_from(self._svc.dic().get)


class DefaultTriggerMessageProcessor(MessageProcessor):
    """
    Handles the processing of messages received by the trigger, orchestrating the runtime to pass
    the envelope to configured pipelines.

    Attributes:
        service_binding (ServiceBinding): The service binding instance for managing configuration,
                                          messaging client, and runtime.

    Methods:
        __init__: Initializes the DefaultTriggerMessageProcessor with the given service binding.
        message_received: Processes the received message, decodes it, and passes it to the
                          appropriate pipelines.
        received_invalid_message: Handles the event when an invalid message is received, allowing
                                  for metrics counter increment.
    """
    def __init__(self, service_binding: ServiceBinding, metrics_manager: MetricsManager):
        self.service_binding = service_binding
        self.messages_received = meters.Counter("")
        self.invalid_messages_received = meters.Counter("")

        lc = service_binding.logger()

        try:
            metrics_manager.register(MESSAGES_RECEIVED_NAME, self.messages_received, None)
            lc.info("%s metric has been registered and will be reported", MESSAGES_RECEIVED_NAME)
        except errors.EdgeX as e:
            lc.warn("%s metric failed to register and will not be reported: %s",
                    MESSAGES_RECEIVED_NAME, e)

        try:
            metrics_manager.register(INVALID_MESSAGES_RECEIVED_NAME,
                                     self.invalid_messages_received, None)
            lc.info("%s metric has been registered and will be reported (if enabled)",
                    INVALID_MESSAGES_RECEIVED_NAME)
        except errors.EdgeX as e:
            lc.warn("%s metric failed to register and will not be reported: %s",
                    INVALID_MESSAGES_RECEIVED_NAME, e)

    def message_received(self, ctx: AppFunctionContext,
                         envelope: MessageEnvelope,
                         output_handler: PipelineResponseHandler):
        """
        message_received provides runtime orchestration to pass the envelope to configured
        pipeline(s)
        """
        self.messages_received.inc(1)
        # pylint: disable=broad-exception-caught
        lc = self.service_binding.logger()
        lc.debug(f"trigger attempting to find pipeline(s) for topic '{envelope.receivedTopic}'")
        if not isinstance(ctx, Context):
            ctx = self.service_binding.build_context(envelope)

        pipelines = self.service_binding.get_matching_pipelines(envelope.receivedTopic)
        lc.debug(f"trigger found {len(pipelines)} pipeline(s) that match the incoming topic "
                 f"'{envelope.receivedTopic}'")
        if not pipelines:
            return

        def pipeline_process_message(function_pipeline: FunctionPipeline,
                                     wait_group: WaitGroup,
                                     data: Any):
            with function_pipeline.message_processing_time.time():
                lc.debug(f"trigger sending message to pipeline {function_pipeline.id} for "
                         f"envelope {envelope.correlationID}")
                try:
                    self.service_binding.process_message(ctx.clone(), data, function_pipeline)
                except Exception as ex:
                    lc.error(f"error processing message in pipeline {function_pipeline.id} for "
                             f"envelope {envelope.correlationID}: {ex}")
                else:
                    if output_handler is not None:
                        try:
                            output_handler(ctx, function_pipeline)
                        except Exception as ex:
                            lc.error(f"failed to process output for message {ctx.correlation_id()}"
                                     f" on pipeline {function_pipeline.id} : {ex}")
                finally:
                    wait_group.done()

        pipeline_wg = WaitGroup()

        try:
            target_data = self.service_binding.decode_message(ctx, envelope)
            for pipeline in pipelines:
                pipeline_wg.add(1)
                pipeline.message_processed.inc(1)
                threading.Thread(target=pipeline_process_message,
                                 args=(pipeline, pipeline_wg, target_data)).start()
        except Exception as e:
            self.invalid_messages_received.inc(1)
            lc.error(f"failed to decode message: {e}")

    def received_invalid_message(self):
        """
        ReceivedInvalidMessage is called when an invalid message is received so the metrics counter
        can be incremented.
        """
        self.messages_received.inc(1)
        self.invalid_messages_received.inc(1)
        lc = self.service_binding.logger()
        lc.warn("received invalid message")
