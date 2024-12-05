#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module defines the MQTT trigger for the application functions SDK.

The MQTT trigger is responsible for connecting to an external MQTT broker, subscribing to topics,
and processing incoming messages. It also handles publishing responses to a specified topic.
"""

import threading
import uuid
from typing import Optional, Any
from urllib.parse import urlparse

import isodate

from isodate import ISO8601Error
import paho.mqtt.client as pahomqtt

from .messageprocessor import MessageProcessor
from ..common.config import ExternalMqttConfig
from ...bootstrap.interface.secret import SecretProvider
from ...bootstrap.timer import new_timer
from ...contracts.clients.logger import Logger
from ...contracts import errors
from ...contracts.common.constants import CORRELATION_HEADER, CONTENT_TYPE_JSON, CONTENT_TYPE_CBOR
from ...interfaces import Trigger, Deferred, AppFunctionContext, FunctionPipeline
from ...interfaces.messaging import MessageEnvelope
from ...internal.trigger.servicebinding import ServiceBinding
from ...sync.waitgroup import WaitGroup
from ...utils.factory.mqtt import MQTTClientConfig, MQTTFactory
from ...utils.helper import delete_empty_and_trim
from ...utils.strconv import parse_int


DEFAULT_RETRY_DURATION = 600
DEFAULT_RETRY_INTERVAL = 5
DEFAULT_CONNECT_TIMEOUT = 30


# pylint: disable=too-many-instance-attributes
class MqttTrigger(Trigger):
    """
    Represents a MQTT trigger.
    """

    def __init__(self, service_binding: ServiceBinding, message_processor: MessageProcessor):
        self.message_processor = message_processor
        self.service_binding = service_binding
        self.mqtt_client: Optional[pahomqtt.Client] = None
        self.qos = "0"
        self.retain = False
        self.publish_topic = None
        self.done = None
        self.waiting_group = None

    # pylint: disable=too-many-locals
    def initialize(self, ctx_done: threading.Event, app_wg: WaitGroup) -> Optional[Deferred]:
        """
        Initializes the Trigger for an external MQTT broker
        """
        # Convenience shortcuts
        lc = self.service_binding.logger()
        config = self.service_binding.config()

        broker_config = config.Trigger.ExternalMqtt
        topics = config.Trigger.SubscribeTopics

        self.qos = broker_config.Qos
        self.retain = broker_config.Retain
        self.publish_topic = config.Trigger.PublishTopic

        lc.info("Initializing MQTT Trigger")

        if len([topic.strip() for topic in topics]) == 0:
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          "missing SubscribeTopics for MQTT Trigger. Must be "
                                          "present in [Trigger.ExternalMqtt] section")

        try:
            broker_url = urlparse(broker_config.Url)
        except TypeError as e:
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          f"invalid MQTT Broker Url '{broker_config.Url}': "
                                          f"{e}")

        try:
            qos = parse_int(self.qos)
        except ValueError as e:
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          f"invalid QoS value '{self.qos}': {e}")

        connect_timeout = DEFAULT_CONNECT_TIMEOUT
        if len(broker_config.ConnectTimeout) > 0:
            try:
                connect_timeout = isodate.parse_duration(
                    "PT" + broker_config.ConnectTimeout.upper()).total_seconds()
            except ISO8601Error as e:
                raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                              f"invalid ConnectTimeout value "
                                              f"'{broker_config.ConnectTimeout}': {e}")

        if broker_config.RetryDuration <= 0:
            broker_config.RetryDuration = DEFAULT_RETRY_DURATION

        if broker_config.RetryInterval <= 0:
            broker_config.RetryInterval = DEFAULT_RETRY_INTERVAL

        mqtt_client_config = MQTTClientConfig(
            broker_address=broker_url.hostname,
            topic=topics,
            secret_name=broker_config.SecretName,
            auth_mode=broker_config.AuthMode,
            client_id=broker_config.ClientId,
            qos=qos,
            retain=self.retain,
            auto_reconnect=broker_config.AutoReconnect,
            skip_verify=broker_config.SkipCertVerify,
            keep_alive=broker_config.KeepAlive,
            connect_timeout=connect_timeout,
            max_reconnect_interval=broker_config.RetryInterval,
            will=broker_config.Will
        )

        secret_provider = self.service_binding.secret_provider()

        timer = new_timer(broker_config.RetryDuration, broker_config.RetryInterval)

        err = None
        while timer.has_not_elapsed():
            try:
                self.mqtt_client = create_mqtt_client(secret_provider, lc, broker_config,
                                                      mqtt_client_config, self.on_connect_handler)
                err = None
                break
            except errors.EdgeX as e:
                lc.warn("failed to create MQTT client: %s. Retrying...", e)
                lc.warn("%s. Attempt to create MQTT client again after %d seconds...", e,
                        broker_config.RetryInterval)
                err = e

            if ctx_done.is_set():
                raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                              "aborted MQTT Trigger initialization")

            timer.sleep_for_interval()

        if err is not None:
            raise err

        def disconnect():
            lc.info("Disconnecting from broker for MQTT trigger")
            self.mqtt_client.disconnect()

        return disconnect

    # pylint: disable=unused-argument, too-many-arguments, too-many-positional-arguments
    def on_connect_handler(self, client: pahomqtt.Client, userdata: Any, flags: dict,
                           rc: int, properties):
        """
        on_connect_handler is a callback function that is called when the client connects to
        the broker
        """
        lc = self.service_binding.logger()
        config = self.service_binding.config()

        topics = delete_empty_and_trim(([t.strip()
                                         for t in config.Trigger.SubscribeTopics.split(',')]))
        try:
            for topic in topics:
                client.message_callback_add(sub=topic, callback=self.message_handler)
                client.subscribe(topic, qos=parse_int(self.qos))
        except ValueError as e:
            raise RuntimeError(f"could not subscribe to topics '{topics}' for MQTT trigger: {e}") \
                from e

        lc.info("Subscribed to topic(s): %s", config.Trigger.SubscribeTopics)

    def message_handler(self, client: pahomqtt.Client, userdata: Any,
                        message: pahomqtt.MQTTMessage):
        """
        on_message is a callback function that is called when a message is received
        """
        # Convenience shortcuts
        lc = self.service_binding.logger()

        data = message.payload
        content_type = CONTENT_TYPE_JSON

        if data[0] != ord('{') and data[0] != ord('['):
            # If not JSON then assume it is CBOR
            content_type = CONTENT_TYPE_CBOR

        correlation_id = str(uuid.uuid4())

        msg_envelope = MessageEnvelope(
            correlationID=correlation_id,
            contentType=content_type,
            payload=data,
            receivedTopic=message.topic
        )

        lc.debug(
            f"MQTT Trigger: Received message with {len(msg_envelope.payload)} bytes "
            f"on topic '{msg_envelope.receivedTopic}'. "
            f"Content-Type={msg_envelope.contentType}")
        lc.trace(f"{CORRELATION_HEADER}={correlation_id}")

        ctx = self.service_binding.build_context(msg_envelope)

        def process_message():
            try:
                self.message_processor.message_received(ctx, msg_envelope, self.response_handler)
            except Exception as e:  # pylint: disable=broad-except
                lc.error("MQTT Trigger: Failed to process message on pipeline(s): %s", e)

        threading.Thread(target=process_message).start()

    def response_handler(self, app_ctx: AppFunctionContext, pipeline: FunctionPipeline):
        """
        response_handler is a callback function that is called when a response is received
        """
        if app_ctx.response_data() and self.publish_topic:
            lc = self.service_binding.logger()

            try:
                formatted_topic = app_ctx.apply_values(self.publish_topic)
            except errors.EdgeX as err:
                lc.error(
                    "MQTT trigger: Unable to format topic '%s' for pipeline '%s': %s",
                    self.publish_topic, pipeline.id, err)
                return err

            try:
                qos = parse_int(self.qos)
            except ValueError as e:
                return errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                               f"invalid QoS value '{self.qos}': {e}")

            result = self.mqtt_client.publish(formatted_topic, app_ctx.response_data(), qos,
                                              self.retain)

            if result.rc != pahomqtt.MQTT_ERR_SUCCESS:
                lc.error(
                    "MQTT trigger: Could not publish to topic '%s' for pipeline '%s': %s",
                    formatted_topic, pipeline.id)
                return errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                               f"MQTT publish error: {result}")
            lc.debug(
                "MQTT Trigger: Published response message for pipeline '%s' on topic '%s' "
                "with %d bytes", pipeline.id, formatted_topic, len(app_ctx.response_data()))
            lc.trace("MQTT Trigger published message: CorrelationHeader="
                     "%s}", app_ctx.correlation_id())

        return None


def create_mqtt_client(sp: SecretProvider, lc: Logger, config: ExternalMqttConfig,
                       mqtt_config: MQTTClientConfig,
                       on_connect_handler: pahomqtt.CallbackOnConnect) -> pahomqtt.Client:
    """
    Create a new MQTT client instance.
    """
    mqtt_factory = MQTTFactory(sp,
                               lc,
                               config.AuthMode,
                               config.SecretName,
                               config.SkipCertVerify)
    mqtt_client, err = mqtt_factory.create(mqtt_config)
    if err is not None:
        raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                      f"failed to create MQTT client: {err}")

    mqtt_client.on_connect = on_connect_handler

    lc.info("Connecting to mqtt broker for MQTT trigger at: %s", config.Url)

    try:
        rc = mqtt_client.connect(mqtt_config.broker_address)
        if rc == pahomqtt.MQTT_ERR_SUCCESS:
            mqtt_client.loop_start()
    except Exception as e:
        raise errors.new_common_edgex(errors.ErrKind.SERVICE_UNAVAILABLE,
                                      f"could not connect to broker for MQTT trigger: {e}")

    lc.info("Connected to mqtt broker for MQTT trigger")
    return mqtt_client
