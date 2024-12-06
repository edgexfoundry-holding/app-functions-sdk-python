# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module provides the foundational classes and functions for messaging capabilities within the
application. It defines the abstract base class for message clients, concrete implementations for
MQTT messaging, and utilities for message and configuration handling.

Classes:
    HostInfo: Represents the host information for the message broker, including protocol, host
    address, and port.
    MessageBusConfig: Configuration for the message bus, including broker information and optional
    parameters.
    MessageEnvelope: Encapsulates the data and metadata for a message, including payload and topic.
    TopicMessageQueue: Associates a message topic with an asyncio Queue for message handling.
    MessageClient: Abstract base class defining the interface for message clients.
    MqttMessageClient: Concrete implementation of MessageClient for MQTT messaging.

Functions:
    new_message_client(message_bus_config: MessageBusConfig) -> MessageClient: Factory function to
    create a new MessageClient instance based on the provided configuration.

The module also sets default values for various message bus properties and initializes the message
bus configuration with these defaults.
"""
import json
from queue import Queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any
from uuid import uuid4

from dataclasses_json import dataclass_json

from ..contracts.common.constants import API_VERSION, CONTENT_TYPE_JSON
from ..contracts.dtos.common.base import Versionable
from ..utils.strconv import parse_bool

# define constants for the message bus type
MQTT = "mqtt"
NATS_CORE = "nats-core"

# define the message bus authentication modes
AUTH_MODE_NONE = "none"
AUTH_MODE_USERNAME_PASSWORD = "usernamepassword"
AUTH_MODE_CACERT = "cacert"
AUTH_MODE_CLIENT_CERT = "clientcert"

# define constants for the message bus related properties default values
DEFAULT_MESSAGEBUS_PROTOCOL = "tcp"
DEFAULT_MESSAGEBUS_HOST = "localhost"
DEFAULT_MESSAGEBUS_PORT = 1883
DEFAULT_MESSAGEBUS_TYPE = MQTT

SKIP_CERT_VERIFY = "SkipCertVerify"
CERT_FILE = "CertFile"
KEY_FILE = "KeyFile"
CA_FILE = "CaFile"
KEY_PEM_BLOCK = "KeyPEMBlock"
CERT_PEM_BLOCK = "CertPEMBlock"
CA_PEM_BLOCK = "CaPEMBlock"


@dataclass
class HostInfo:
    """
    Represents the host information for the message broker.

    This class encapsulates the protocol, host address, and port number required to connect to a
    message broker. It provides utility methods to construct the host URL and check if the host
    information is empty.

    Attributes:
        protocol (str): The communication protocol used to connect to the broker (e.g., 'tcp').
        host (str): The hostname or IP address of the broker.
        port (int): The port number on which the broker is listening.

    Methods:
        get_host_url: Constructs and returns the full URL to the broker based on the protocol, host,
        and port.
        is_host_info_empty: Checks if the host and port information is not provided.
    """
    protocol: str = field(default=DEFAULT_MESSAGEBUS_PROTOCOL)
    host: str = field(default=DEFAULT_MESSAGEBUS_HOST)
    port: int = field(default=DEFAULT_MESSAGEBUS_PORT)

    def get_host_url(self) -> str:
        """Constructs and returns the full URL to the broker."""
        return f"{self.protocol}://{self.host}:{self.port}"

    def is_host_info_empty(self) -> bool:
        """Checks if the host and port information is not provided."""
        return self.host == "" or self.port == 0


@dataclass
class MessageBusConfig:
    """
    Configuration for the message bus.

    This class holds the configuration details required to set up a message bus client, including
    the broker information and any optional parameters that may be needed for different types of
    message bus implementations.

    Attributes:
        broker_info (HostInfo): An instance of HostInfo containing the protocol, host, and port for
        the message broker.
        type (str): The type of message bus (e.g., MQTT). This is used to determine the appropriate
        message client implementation.
        optional (dict[str, str]): A dictionary of optional parameters that can be used to provide
        additional configuration settings specific to the message bus type.
        auth_mode (str): The authentication mode for the message bus.

    """
    def __init__(self,
                 broker_info: HostInfo,
                 message_bus_type: str,
                 optional: dict[str, str],
                 auth_mode: str = AUTH_MODE_NONE):
        self.broker_info = broker_info
        self.auth_mode = auth_mode
        self.type = message_bus_type
        self.optional = optional


class TlsConfigurationOptions:
    # pylint: disable=too-few-public-methods
    """ TLS configuration for connecting the message bus. """
    def __init__(self, message_bus_config: MessageBusConfig):
        self.skip_cert_verify = parse_bool(
            message_bus_config.optional.get(SKIP_CERT_VERIFY, "False"))
        self.cert_file = message_bus_config.optional.get(CERT_FILE, "")
        self.key_file = message_bus_config.optional.get(KEY_FILE, "")
        self.ca_file = message_bus_config.optional.get(CA_FILE, "")
        self.cert_pem_block = message_bus_config.optional.get(CERT_PEM_BLOCK, "")
        self.key_pem_block = message_bus_config.optional.get(KEY_PEM_BLOCK, "")
        self.ca_pem_block = message_bus_config.optional.get(CA_PEM_BLOCK, "")

@dataclass_json
@dataclass
class MessageEnvelope(Versionable):
    # pylint: disable=too-many-instance-attributes, invalid-name
    # Eight is reasonable in this case.
    """
    Encapsulates the data and metadata for a message, including payload and topic.

    This class inherits from `Versionable` to ensure compatibility across different
    versions of the messaging system. It includes attributes for the received topic,
    correlation and request IDs, error code, payload, content type, and query
    parameters. It also provides a method to create an instance from a byte
    representation of the data.

    Attributes:
        received_topic (str): The topic on which the message was received.
        correlation_id (str): A unique identifier to correlate this message with others in a
        transaction or conversation.
        request_id (str): A unique identifier for the request, useful for tracking and logging.
        error_code (int): An error code associated with the message, if any.
        payload (bytes): The raw payload of the message.
        content_type (str): The format of the payload (e.g., 'json').
        query_params (dict[str, str]): Any query parameters associated with the message.
        api_version (str): The API version of the message, inherited from `Versionable`.

    Methods:
        from_bytes(bytes_data: bytes) -> MessageEnvelope: Class method to create an instance of
        `MessageEnvelope` from a byte representation of the data.
    """
    receivedTopic: str = ""
    correlationID: str = ""
    requestID: str = ""
    errorCode: int = 0
    payload: bytes = b""
    contentType: str = CONTENT_TYPE_JSON
    queryParams: Optional[dict[str, str]] = None
    apiVersion: str = field(default=API_VERSION, init=False)

def new_message_envelope(payload: Any, content_type: str = CONTENT_TYPE_JSON) -> MessageEnvelope:
    """
    Creates a new MessageEnvelope object with the provided payload and content type.

    Args:
        payload (Any): The payload to be included in the message envelope.
        content_type (str): The content type of the payload (default: 'application/json').

    Returns:
        MessageEnvelope: A new MessageEnvelope object with the specified payload and content type.

    """
    message = MessageEnvelope()
    message.correlationID = str(uuid4())
    message.contentType = content_type
    # to ensure that data can be properly serialized using json.dumps, convert data to dict
    data_in_dict = payload.__dict__ if hasattr(payload, "__dict__") else payload
    # note that message.payload needs to be bytes, so use json.dumps serialize the data into
    # json str and encode the json str into bytes
    message.payload = json.dumps(data_in_dict).encode("utf-8")
    return message

def decode_message_envelope(payload: bytes):
    """
    Decodes a message payload into a MessageEnvelope object.
    """
    # decode the message payload into a dict using json.loads
    payload_json_decoded = json.loads(payload.decode())
    # note that the payload_json_decoded["payload"] will be decoded as str by json.loads
    # so we need to encode it back to bytes
    payload_json_decoded["payload"] = payload_json_decoded["payload"].encode()
    # the MessageEnvelope is declared with @dataclass_json, so we can use the handy
    # from_dict function to create a MessageEnvelope object from the decoded dict
    message_envelope = MessageEnvelope.from_dict(payload_json_decoded)  # pylint: disable=no-member
    return message_envelope

@dataclass
class TopicMessageQueue:
    """
    Associates a message topic with an asyncio Queue for message handling.

    This class is designed to hold messages for a specific topic in an asyncio Queue, facilitating
    asynchronous message processing. It provides a straightforward way to manage the flow of
    messages by topic, ensuring that messages are processed in the order they are received.

    Attributes:
        topic (str): The message topic associated with this queue.
        message_queue (asyncio.Queue): The asyncio Queue that holds messages for the associated
        topic.

    Methods:
        There are no methods defined in this class other than the constructor.
    """
    topic: str
    message_queue: Queue


class MessageClient(ABC):
    """
    Abstract base class defining the interface for message clients.

    This class outlines the essential methods that any message client must implement to interact
    with a message bus system. It serves as a blueprint for creating concrete message client
    implementations that can connect to, publish messages to, subscribe to topics from, unsubscribe
    from topics, and disconnect from a message bus.

    Methods:
        connect: Establishes a connection to the message bus.
        publish(message: MessageEnvelope, topic: str): Publishes a message to a specified topic on
        the message bus.
        subscribe(topics: List[TopicMessageQueue]): Subscribes to a list of topics on the message
        bus.
        unsubscribe(topics: List[str]): Unsubscribes from a list of topics on the message bus.
        disconnect: Closes the connection to the message bus.
    """

    @abstractmethod
    def connect(self):
        """
        Establishes a connection to the message bus.

        This method should implement the logic necessary to connect the message client to the
        message bus, using the configuration provided during the client's initialization.

        """

    @abstractmethod
    def publish(self, message: MessageEnvelope, topic: str):
        """
        Publishes a message to a specified topic on the message bus.

        Args:
            message (MessageEnvelope): The message envelope containing the payload and metadata to
            be published.
            topic (str): The topic to which the message should be published.

        """

    @abstractmethod
    def subscribe(self, topic_queues: List[TopicMessageQueue], error_queue: Queue):
        """
        Subscribes to a list of topics on the message bus.

        This method should implement the logic necessary to subscribe the message client to a list
        of topics, enabling it to receive messages published to these topics.

        Args:
            topic_queues (List[TopicMessageQueue]): A list of TopicMessageQueue instances
            representing the topics to subscribe to.
            error_queue (Queue): A queue for handling errors that occur during message processing.

        """

    @abstractmethod
    def unsubscribe(self, topics: List[str]):
        """
        Unsubscribes from a list of topics on the message bus.

        This method should implement the logic necessary to unsubscribe the message client from a
        list of topics, stopping it from receiving messages published to these topics.

        Args:
            topics (List[str]): A list of topic strings from which to unsubscribe.

        """

    @abstractmethod
    def disconnect(self):
        """
        Closes the connection to the message bus.

        This method should implement the logic necessary to cleanly disconnect the message client
        from the message bus, ensuring that all resources are properly released.

        """
