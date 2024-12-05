#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for MQTTExport
"""
import threading
import time
from datetime import datetime
from typing import Any, Tuple

import paho.mqtt.client as pahomqtt
from pyformance import meters

from .helpers import register_metric
from .string_values_formatter import StringValuesFormatter, default_string_value_formatter
from ..bootstrap.interface.secret import SecretProvider
from ..bootstrap.metrics.samples import UniformSample
from ..contracts import errors
from ..contracts.clients.logger import Logger
from ..contracts.common.constants import CORRELATION_HEADER
from ..contracts.errors import EdgeX
from ..interfaces import AppFunctionContext
from ..internal.constants import (METRICS_RESERVOIR_SIZE, MQTT_EXPORT_ERRORS_NAME,
                                  MQTT_EXPORT_SIZE_NAME)
from ..utils.helper import coerce_type
from ..utils.factory.mqtt import MQTTClientConfig, MQTTFactory

# pylint: disable=too-many-instance-attributes
class MQTTSender:
    """
    MQTTSender is a class that sends data to the specified MQTT broker.
    """

    def __init__(self,
                 mqtt_config: MQTTClientConfig,
                 topic_formatter: StringValuesFormatter = default_string_value_formatter,
                 persist_on_error: bool = False):
        self._mqtt_config = mqtt_config
        self.secrets_last_retrieved = datetime(1,1,1)
        self._client = None
        self._persist_on_error = persist_on_error
        self._topic_formatter = topic_formatter
        self._lock = threading.Lock()
        self.mqtt_error_metrics = meters.Counter("")
        self.mqtt_size_metrics = meters.Histogram("", sample=UniformSample(METRICS_RESERVOIR_SIZE))

    def _initialize_mqtt_client(self, lc: Logger, sp: SecretProvider) -> EdgeX | None:
        """
        InitializeMQTTClient initializes the MQTT client for export.
        """
        with self._lock:
            if (self._client is not None and
                    self.secrets_last_retrieved >= sp.secrets_last_updated()):
                return None

            lc.info("Initializing MQTT Client")

            mqtt_client_factory = MQTTFactory(sp, lc,
                                              self._mqtt_config.auth_mode,
                                              self._mqtt_config.secret_name,
                                              self._mqtt_config.skip_verify)

            client, err = mqtt_client_factory.create(self._mqtt_config)
            if err is not None:
                return errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                               f"unable to create MQTT Client for export: "
                                               f"{err.debug_messages()}")
            self._client = client
            self.secrets_last_retrieved = datetime.now()
            return None

    def _connect_to_broker(self, lc: Logger) -> EdgeX | None:
        """
        ConnectToBroker connects to the specified MQTT broker
        """
        with self._lock:
            if self._client.is_connected():
                return None
            lc.info(f"MQTTSender connecting to MQTT Broker({self._mqtt_config.broker_address})")
            try:
                rc = self._client.connect(self._mqtt_config.broker_address)
                if rc != pahomqtt.MQTT_ERR_SUCCESS:
                    raise ValueError(f"Failed to connect to MQTT Broker"
                                     f"({self._mqtt_config.broker_address}), return code is {rc}")
                lc.info(f"Successfully send CONNECT packet to MQTT Broker"
                        f"({self._mqtt_config.broker_address}) for network connection. "
                        f"Now attempt to start the loop to handle network traffic.")
                # per design of paho mqtt python library, loop_start() should be called after
                # connect() to start the network loop; otherwise the network traffic will not be
                # handled and self._client.is_connected() may return False.
                # See https://github.com/eclipse/paho.mqtt.python/issues/454#issuecomment-949075809
                # for more details.
                self._client.loop_start()
                return None
            except Exception as e:  # pylint: disable=broad-exception-caught
                return errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,f"{e}")

    def pre_connect_to_broker(self, lc: Logger, sp: SecretProvider, pre_connect_retry_count: int,
                              retry_interval: int):
        """
        PreConnectToBroker pre-connects to the specified MQTT broker
        """
        if self._client is None:
            init_err = self._initialize_mqtt_client(lc, sp)
            if init_err is not None:
                lc.error(f"Failed to pre-connect to MQTT Broker: {init_err}. "
                         f"Will try again on first export")
                return

        if self._client.is_connected():
            lc.info("Already connected to MQTT Broker, so skip the pre-connect attempt.")
            return

        lc.info("Attempting to pre-connect to MQTT Broker for export")
        for i in range(pre_connect_retry_count):
            lc.info(f"Pre-connect to MQTT Broker on attempt {i + 1}")
            try:
                err = self._connect_to_broker(lc)
                if err is None:
                    lc.info("Successfully pre-connected to MQTT Broker")
                    return
                raise ValueError(f"Failed to connect to MQTT Broker:{err}")
            except Exception as e:  # pylint: disable=broad-exception-caught
                lc.warn(f"Failed to pre-connect to MQTT Broker on attempt {i + 1}: {e}."
                        f" trying again in {retry_interval} seconds.")
                time.sleep(retry_interval)

        lc.error(f"Failed to pre-connect to MQTT Broker after attempting "
                 f"{pre_connect_retry_count} times. Will try again on first export")


    def set_retry_data(self, ctx: AppFunctionContext, export_data: bytes):
        """
        SetRetryData sets the retry data for the context
        """
        if self._persist_on_error:
            ctx.set_retry_data(export_data)

    def mqtt_send(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """
        MQTTSend sends data from the previous function to the specified MQTT broker.
        If no previous function exists, then the event that triggered the pipeline will be used.
        """
        lc = ctx.logger()

        lc.debug(f"MQTT Exporting in pipeline '{ctx.pipeline_id()}'")

        if data is None:
            # not receive a result
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"function MQTTSend in pipeline '{ctx.pipeline_id()}': No Data Received")

        export_data, error = coerce_type(data)
        if error is not None:
            return False, errors.new_common_edgex_wrapper(error)

        secret_provider = ctx.secret_provider()
        if (self._client is None or
                self.secrets_last_retrieved < secret_provider.secrets_last_updated()):
            error = self._initialize_mqtt_client(lc, secret_provider)
            if error is not None:
                lc.error(f"failed to initialize MQTT client in pipeline '{ctx.pipeline_id()}': "
                         f"{error.debug_messages()}")
                return False, errors.new_common_edgex_wrapper(error)

        publish_topic = self._topic_formatter(self._mqtt_config.topic, ctx, data)
        tag_value = f"{self._mqtt_config.broker_address}/{publish_topic}"
        tag = {"address/topic": tag_value}

        register_metric(ctx, lambda: f"{MQTT_EXPORT_ERRORS_NAME}-{tag_value}",
                        lambda: self.mqtt_error_metrics, tag)

        register_metric(ctx, lambda: f"{MQTT_EXPORT_SIZE_NAME}-{tag_value}",
                        lambda: self.mqtt_size_metrics, tag)

        if not self._client.is_connected():
            error = self._connect_to_broker(lc)
            if error is not None:
                self.mqtt_error_metrics.inc(1)
                lc.error(f"failed to connect to Broker in pipeline '{ctx.pipeline_id()}': "
                         f"{error.debug_messages()}")
                self.set_retry_data(ctx, export_data)
                return False, errors.new_common_edgex_wrapper(error)

        result = self._client.publish(publish_topic, export_data, self._mqtt_config.qos,
                                      self._mqtt_config.retain)
        if result.rc != pahomqtt.MQTT_ERR_SUCCESS:
            self.mqtt_error_metrics.inc(1)
            lc.error(f"failed to publish message in pipeline '{ctx.pipeline_id()}': {result}")
            self.set_retry_data(ctx, export_data)
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"failed to publish message in pipeline '{ctx.pipeline_id()}': {result}")
        if self._persist_on_error:
            ctx.trigger_retry_failed_data()

        self.mqtt_size_metrics.add(len(export_data))

        lc.debug(f"Sent {len(export_data)} bytes of data to MQTT Broker in pipeline "
                 f"'{ctx.pipeline_id()}' to topic '{publish_topic}'")
        lc.trace(f"Data exported to MQTT Broker in pipeline '{ctx.pipeline_id()}': "
                 f"{CORRELATION_HEADER}={ctx.correlation_id()}")

        return True, None


def new_mqtt_sender(mqtt_config: MQTTClientConfig,
                    topic_formatter: StringValuesFormatter = default_string_value_formatter,
                    persist_on_error: bool = False) -> MQTTSender:
    """
    new_mqtt_sender creates a new instance of MQTTSender
    """
    return MQTTSender(mqtt_config, topic_formatter, persist_on_error)
