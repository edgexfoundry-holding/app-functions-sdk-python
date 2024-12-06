# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
""" Provides Nats client functionality for publishing and subscribing to topics. """

import asyncio
import queue
import ssl
import threading
from typing import List

from nats.aio.client import Client as NATS
from nats.aio.subscription import Subscription

from ...contracts.clients.logger import Logger
from ...interfaces.messaging import (MessageBusConfig, MessageClient, MessageEnvelope,
                                     TopicMessageQueue, AUTH_MODE_CLIENT_CERT, AUTH_MODE_CACERT,
                                     TlsConfigurationOptions, decode_message_envelope)
from ...utils.strconv import parse_bool, parse_int

# common constants for messagebus.Optional properties
USERNAME = "Username"
PASSWORD = "Password"
CLIENT_ID = "ClientId"
FORMAT = "Format"
RETRY_ON_FAILED_RECONNECT = "RetryOnFailedConnect"
DURABLE = "Durable"
SUBJECT = "Subject"
AUTO_PROVISION = "AutoProvision"
CONNECT_TIMEOUT = "ConnectTimeout"
QUEUE_GROUP = "QueueGroup"
DELIVER = "Deliver"
DEFAULT_PUB_RETRY_ATTEMPTS = "DefaultPubRetryAttempts"
NKEY_SPEED_FILE = "NKeySeedFile"
CREDENTIALS_FILE = "CredentialsFile"
EXACTLY_ONCE = "ExactlyOnce"


class NatsClientOptions:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    """ Represents the configuration options for an Nats client. """
    def __init__(self, message_bus_config: MessageBusConfig):
        self.auth_mode = message_bus_config.auth_mode
        self.username = message_bus_config.optional.get(USERNAME, "")
        self.password = message_bus_config.optional.get(PASSWORD, "")
        self.connect_timeout = parse_int(message_bus_config.optional.get(CONNECT_TIMEOUT, "5"))
        self.retry_on_failed_connect = parse_bool(
            message_bus_config.optional.get(RETRY_ON_FAILED_RECONNECT, "False"))

        # jet stream
        self.durable = message_bus_config.optional.get(DURABLE, "")
        self.subject = message_bus_config.optional.get(SUBJECT, "")
        self.auto_provision = parse_bool(
            message_bus_config.optional.get(AUTO_PROVISION, "False"))
        self.default_pub_retry_attempts = parse_int(
            message_bus_config.optional.get(DEFAULT_PUB_RETRY_ATTEMPTS, "2"))
        self.format = message_bus_config.optional.get(FORMAT, "nats")
        self.nkey_seed_file = message_bus_config.optional.get(NKEY_SPEED_FILE, "")
        self.credentials_file = message_bus_config.optional.get(CREDENTIALS_FILE, "")
        self.deliver = message_bus_config.optional.get(DELIVER, "new")
        self.exactly_once = parse_bool(
            message_bus_config.optional.get(EXACTLY_ONCE, "False"))

        self.tls_config = TlsConfigurationOptions(message_bus_config)


class NatsSubscription:
    """ NatsSubscription hold the msg_queue and subscription """
    # pylint: disable=too-few-public-methods
    def __init__(self, topic_message_queue: TopicMessageQueue, sub: Subscription):
        self.topic_message_queue = topic_message_queue
        self.subscription = sub


class NatsMessageClient(MessageClient):
    """ Implements a Nats client for publishing and subscribing to topics """

    def __init__(self, message_bus_config: MessageBusConfig, logger: Logger):
        self._logger = logger
        self._broker_info = message_bus_config.broker_info
        self._client_options = NatsClientOptions(message_bus_config)
        self._subscribed_topics = dict[str, NatsSubscription]()
        self._subscription_mutex = threading.Lock()
        self._client = NATS()

    def connect(self):
        # if the client is already connected, skip the connection
        if self._client.is_connected:
            return

        # as nats-py library use async function to connect to NATS, and the MessageClient interface
        # is designed to be sync, we need to run the async function in a new async task
        async def _run_connect():
            self._logger.info(f"entering _run_connect. client.is_connected "
                              f"{self._client.is_connected}")
            tls = None
            if self._client_options.auth_mode == AUTH_MODE_CLIENT_CERT:
                tls = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
                tls.minimum_version = ssl.PROTOCOL_TLSv1_2
                tls.load_verify_locations(self._client_options.tls_config.ca_file)
                tls.load_cert_chain(
                    certfile=self._client_options.tls_config.cert_file,
                    keyfile=self._client_options.tls_config.key_file)
                tls.verify_mode = ssl.CERT_NONE if (
                    self._client_options.tls_config.skip_cert_verify) else ssl.CERT_REQUIRED
            elif self._client_options.auth_mode == AUTH_MODE_CACERT:
                tls = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
                tls.minimum_version = ssl.PROTOCOL_TLSv1_2
                tls.load_verify_locations(self._client_options.tls_config.ca_file)
                tls.verify_mode = ssl.CERT_NONE if (
                    self._client_options.tls_config.skip_cert_verify) else ssl.CERT_REQUIRED

            broker_url = f"nats://{self._broker_info.host}:{self._broker_info.port}"

            async def reconnected_cb():
                print('Reconnected to NATS...')

            async def error_cb(e):
                print(f'Got the NATS error: {e}')

            await self._client.connect(
                servers=[broker_url],
                tls=tls,
                user=self._client_options.username, password=self._client_options.password,
                connect_timeout=self._client_options.connect_timeout,
                error_cb=error_cb,
                reconnected_cb=reconnected_cb,
            )
            self._logger.info(f"exiting _run_connect. client.is_connected "
                              f"{self._client.is_connected}")

        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                loop.create_task(_run_connect())
            else:
                loop.run_until_complete(_run_connect())
        except Exception as e:
            raise ConnectionError("Failed to connect to NATS") from e
        if not self._client.is_connected:
            raise ConnectionError("Unable to connect NATS")

    def publish(self, message: MessageEnvelope, topic: str):
        async def _run_publish():
            self._logger.info(f"entering _run_publish. client.is_connected "
                              f"{self._client.is_connected}")
            await self._client.publish(subject=topic,payload=message.payload)
            self._logger.info(
                f"exiting _run_publish. client.is_connected {self._client.is_connected}")

        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                loop.create_task(_run_publish())
            else:
                loop.run_until_complete(_run_publish())
        except Exception as e:
            raise ConnectionError("Failed to publish to NATS") from e

    def subscribe(self, topic_queues: List[TopicMessageQueue], error_queue: queue.Queue):  # pylint: disable=invalid-overridden-method
        async def _run_subscribe():
            self._logger.info(f"entering _run_subscribe. client.is_connected "
                              f"{self._client.is_connected}")
            with self._subscription_mutex:
                for topic_q in topic_queues:
                    if topic_q.topic in self._subscribed_topics:
                        continue
                    # Cache the sub because the Nats unsubscribe function require it
                    message_handler = _new_message_handler(topic_q.message_queue, error_queue)
                    sub = await self._client.subscribe(topic_q.topic, cb=message_handler)
                    self._subscribed_topics[topic_q.topic] = NatsSubscription(topic_q, sub)
            self._logger.info(f"exiting _run_subscribe. client.is_connected: "
                              f"{self._client.is_connected} ")

        if not self._client.is_connected:
            raise ConnectionError("Unable to subscribe as NATS client is not connected")
        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                loop.create_task(_run_subscribe())
            else:
                loop.run_until_complete(_run_subscribe())
        except Exception as e:
            raise ConnectionError("Failed to subscribe for NATS") from e

    def unsubscribe(self, topics: List[str]):
        async def _run_unsubscribe():
            for topic in topics:
                if topic not in self._subscribed_topics:
                    continue
                existing_sub = self._subscribed_topics[topic].subscription
                await existing_sub.unsubscribe()
                self._subscribed_topics.pop(topic)

        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                loop.create_task(_run_unsubscribe())
            else:
                loop.run_until_complete(_run_unsubscribe())
        except Exception as e:
            raise ConnectionError("Failed to unsubscribe for NATS") from e

    def disconnect(self):
        async def _run_disconnect():
            await self._client.drain()

        loop = asyncio.get_event_loop()
        try:
            if loop.is_running():
                loop.create_task(_run_disconnect())
            else:
                loop.run_until_complete(_run_disconnect())
        except Exception as e:
            raise ConnectionError("Failed to disconnect from NATS") from e

def _new_message_handler(message_queue: queue.Queue, error_queue: queue.Queue):
    """ Creates a new message handler for the Nats client """
    async def on_message(msg):
        try:
            message_envelope = decode_message_envelope(msg.data)
        except Exception as ex:  # pylint: disable=broad-except
            error_queue.put(f"Failed to decode message into a MessageEnvelope: {ex}")
            return
        message_envelope.receivedTopic = msg.subject
        message_queue.put(message_envelope)
    return on_message
