# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
Provides MQTT client functionality for publishing and subscribing to topics using the Paho MQTT
library.

This module defines classes and functions to interact with an MQTT broker for message communication.
It includes the implementation of an MQTT client that supports various features such as Quality of
Service (QoS) levels, SSL/TLS connections, automatic reconnection, and more.

Classes:
    MQTTClientOptions: Configuration options for the MQTT client.
    MqttMessageClient: An MQTT client for publishing messages to topics and subscribing to topics
    for message reception.

Functions:
    _new_mqtt_client(message_bus_config: MessageBusConfig) -> Client: Creates and configures a new
    Paho MQTT Client instance.

The `MqttMessageClient` class implements the abstract methods defined in the `MessageClient`
abstract base class, providing concrete functionality for MQTT communication.

Usage:
    The module is intended to be used by importing and instantiating `MqttMessageClient` with the
    appropriate configuration. The client can then connect to an MQTT broker, publish messages,
    subscribe to topics, and handle incoming messages as defined by the application's requirements.
"""
import base64
import json
import queue
import ssl
import threading
from dataclasses import asdict
from queue import Queue
from typing import List, Any

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from . import USERNAME, PASSWORD, CLIENT_ID, QOS, KEEP_ALIVE, RETAINED, AUTO_RECONNECT, \
    CLEAN_SESSION, CONNECT_TIMEOUT
from ...interfaces.messaging import (MessageBusConfig, MessageClient, MessageEnvelope,
                                     TopicMessageQueue, AUTH_MODE_USERNAME_PASSWORD,
                                     AUTH_MODE_CLIENT_CERT, AUTH_MODE_CACERT,
                                     TlsConfigurationOptions, decode_message_envelope)
from ...utils.strconv import parse_bool, parse_int


class MQTTClientOptions:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    """
    Represents the configuration options for an MQTT client.

    Attributes:
        username (str): Username for MQTT broker authentication.
        password (str): Password for MQTT broker authentication.
        client_id (str | None): Unique client identifier. If None, the broker generates one.
        qos (int): Quality of Service level for message delivery (0, 1, or 2).
        keep_alive (int): Maximum period in seconds allowed between communications with the broker.
        retained (bool): If True, messages are retained by the broker for new subscribers.
        auto_reconnect (bool): If True, the client will automatically attempt to reconnect to the
        broker.
        clean_session (bool): If True, the broker removes all information about this client when it
        disconnects.
        connect_timeout (int): Maximum time in seconds to wait for a connection to succeed.
        skip_cert_verify (bool): If True, SSL/TLS certificate verification is skipped.
        cert_file (str): Path to the client's certificate file for SSL/TLS.
        key_file (str): Path to the client's private key file for SSL/TLS.
        ca_file (str): Path to the CA certificate file for SSL/TLS.
        cert_pem_block (str): Client's certificate PEM block as a string.
        key_pem_block (str): Client's private key PEM block as a string.
        ca_pem_block (str): CA certificate PEM block as a string.

    The configuration is extracted from the provided `MessageBusConfig` instance, with defaults
    for optional parameters.
    """

    def __init__(self, message_bus_config: MessageBusConfig):
        self.auth_mode = message_bus_config.auth_mode
        self.username = message_bus_config.optional.get(USERNAME, "")
        self.password = message_bus_config.optional.get(PASSWORD, "")
        self.client_id = message_bus_config.optional.get(CLIENT_ID)
        self.qos = parse_int(message_bus_config.optional.get(QOS, "0"))
        self.keep_alive = parse_int(message_bus_config.optional.get(KEEP_ALIVE, "60"))
        self.retained = parse_bool(message_bus_config.optional.get(RETAINED, "False"))
        self.auto_reconnect = parse_bool(message_bus_config.optional.get(AUTO_RECONNECT, "True"))
        self.clean_session = parse_bool(message_bus_config.optional.get(CLEAN_SESSION, "True"))
        self.connect_timeout = parse_int(message_bus_config.optional.get(CONNECT_TIMEOUT, "5"))
        self.tls_config = TlsConfigurationOptions(message_bus_config)


def _new_mqtt_client(client_options: MQTTClientOptions) -> mqtt.Client:
    """
    Creates a new MQTT client instance based on the provided configuration.

    Args:
        message_bus_config (MessageBusConfig): The message bus configuration.

    Returns:
        Client: The new MQTT client instance.
    """
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2,
                    client_id=client_options.client_id,
                    clean_session=client_options.clean_session,
                    reconnect_on_failure=client_options.auto_reconnect)
    if client_options.auth_mode == AUTH_MODE_USERNAME_PASSWORD:
        client.username_pw_set(client_options.username, client_options.password)
    elif client_options.auth_mode == AUTH_MODE_CLIENT_CERT:
        client.tls_set(ca_certs=client_options.tls_config.ca_file,
                       certfile=client_options.tls_config.cert_file,
                       keyfile=client_options.tls_config.key_file,
                       cert_reqs=ssl.CERT_REQUIRED if not client_options.tls_config.skip_cert_verify
                       else ssl.CERT_NONE)
    elif client_options.auth_mode == AUTH_MODE_CACERT:
        client.tls_set(ca_certs=client_options.tls_config.ca_file,
                       cert_reqs=ssl.CERT_REQUIRED if not client_options.tls_config.skip_cert_verify
                       else ssl.CERT_NONE)
    return client


def _on_connect(client: mqtt.Client, userdata: Any,
                flags: dict, rc: int, properties  # pylint: disable=unused-argument
                ):
    for topic in userdata:
        client.message_callback_add(topic, userdata[topic])


def _new_message_handler(message_queue: Queue, error_queue: Queue) -> mqtt.CallbackOnMessage:
    """
    Creates a new message handler for the MQTT client.

    Returns:
        CallbackOnMessage: The new message handler.
    """

    def on_message(client: mqtt.Client, userdata: Any,  # pylint: disable=unused-argument
                   message: mqtt.MQTTMessage):
        try:
            message_envelope = decode_message_envelope(message.payload)
        except Exception as ex:  # pylint: disable=broad-except
            error_queue.put(f"Failed to decode message into a MessageEnvelope: {ex}")
            return
        message_envelope.receivedTopic = message.topic
        message_queue.put(message_envelope)

    return on_message


class MqttMessageClient(MessageClient):
    """
    Implements an MQTT client for publishing and subscribing to topics.

    This client uses the Paho MQTT library to connect to an MQTT broker, publish messages,
    and subscribe to topics. It supports QoS levels 0, 1, and 2, clean and persistent sessions,
    SSL/TLS connections, and automatic reconnection.

    Methods:
        connect(): Establishes a connection to the MQTT broker.
        publish(message: MessageEnvelope, topic: str): Publishes a message to a specified topic.
        subscribe(topic_queues: List[TopicMessageQueue]): Subscribes to a list of topics.
        unsubscribe(topics: List[str]): Unsubscribes from a list of topics.
        disconnect(): Disconnects from the MQTT broker.

    The client maintains a list of subscribed topics and queues for incoming messages, ensuring
    thread safety with an asyncio lock. It handles connection, disconnection, and message
    reception events to manage subscriptions and deliver messages to the appropriate queues.
    """

    def __init__(self, message_bus_config: MessageBusConfig):
        self._broker_info = message_bus_config.broker_info
        self._client_options = MQTTClientOptions(message_bus_config)
        self._existing_subscriptions = dict[str, mqtt.CallbackOnMessage]()
        self._subscription_mutex = threading.Lock()
        self._client = _new_mqtt_client(self._client_options)
        self._client.on_connect = _on_connect
        self._client.user_data_set(self._existing_subscriptions)

    def connect(self):
        if self._client.is_connected():
            return

        try:
            rc = self._client.connect(self._broker_info.host, self._broker_info.port,
                                      self._client_options.keep_alive)
            if rc == mqtt.MQTT_ERR_SUCCESS:
                self._client.loop_start()
        except ValueError as ve:
            raise RuntimeError(f"Failed to connect to MQTT broker: {ve}") from ve

    def publish(self, message: MessageEnvelope, topic: str):
        try:
            message.payload = base64.b64encode(message.payload).decode('utf-8')
            marshaled_message = json.dumps(asdict(message))
            self._client.publish(topic=topic,
                                 payload=marshaled_message,
                                 qos=self._client_options.qos,
                                 retain=self._client_options.retained)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to publish message to MQTT broker: {e}") from e

    def subscribe(self, topic_queues: List[TopicMessageQueue], error_queue: queue.Queue):
        with self._subscription_mutex:
            try:
                for topic_q in topic_queues:
                    message_handler = _new_message_handler(topic_q.message_queue, error_queue)
                    self._client.message_callback_add(topic_q.topic, message_handler)
                    result, _ = self._client.subscribe(topic_q.topic, self._client_options.qos)
                    if result == 0:
                        self._existing_subscriptions[topic_q.topic] = message_handler
            except ValueError as ve:
                raise RuntimeError(f"Failed to subscribe to MQTT broker: {ve}") from ve

    def unsubscribe(self, topics: List[str]):
        with self._subscription_mutex:
            try:
                for topic in topics:
                    if topic not in self._existing_subscriptions:
                        continue
                    result, _ = self._client.unsubscribe(topic)
                    if result == 0:
                        self._existing_subscriptions.pop(topic)
            except ValueError as ve:
                raise RuntimeError(f"Failed to subscribe to MQTT broker: {ve}") from ve

    def disconnect(self):
        if self._client.is_connected():
            self._client.disconnect()
            self._client.loop_stop()
