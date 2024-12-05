# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
Messaging Initialization Module.

This module serves as the entry point for creating message clients, specifically focusing on MQTT
protocol-based communication. It provides a factory function to instantiate message clients based
on the provided configuration, supporting the integration with different types of message buses as
needed by the application.

The module abstracts the complexity of directly interacting with specific message bus
implementations, offering a simplified interface for client creation.
This allows for easy extension and integration of additional message bus types in the future.

Functions:
    new_message_client(message_bus_config: MessageBusConfig) -> MessageClient: Factory function that
    creates and returns a new instance of a message client based on the provided message bus
    configuration.

Examples:
    To create a new MQTT message client:
        config = MessageBusConfig(type=MQTT, broker_info={'host': 'localhost', 'port': 1883})
        mqtt_client = new_message_client(config)

Note:
    Currently, this module supports only MQTT-based message clients. Future versions may include
    support for other protocols.

See Also:
    - `MqttMessageClient` in `mqtt.client` for the MQTT client implementation.
    - `MessageBusConfig` in `interfaces.messaging` for the configuration structure.
"""
from .mqtt.client import MqttMessageClient
from .nats.client import NatsMessageClient
from ..contracts.clients.logger import Logger
from ..interfaces.messaging import MessageBusConfig, MessageClient, MQTT, HostInfo, NATS_CORE
from ..internal.common.config import MessageBusInfo


def new_message_client(message_bus_info: MessageBusInfo, logger: Logger) -> MessageClient:
    """
    Factory function to create a new MessageClient based on the provided MessageBusInfo config.

    Args:
        message_bus_info: The MessageBusInfo configuration used to create the MessageClient.

    Returns:
        MessageClient: A new MessageClient instance.
    """
    message_bus_config = MessageBusConfig(
        broker_info=HostInfo(
            protocol=message_bus_info.Protocol,
            host=message_bus_info.Host,
            port=message_bus_info.Port),
        auth_mode=message_bus_info.AuthMode,
        message_bus_type=message_bus_info.Type.lower(),
        optional=message_bus_info.Optional)

    if message_bus_config.type.lower() == MQTT:
        return MqttMessageClient(message_bus_config)
    if message_bus_config.type.lower() == NATS_CORE:
        return NatsMessageClient(message_bus_config, logger)

    raise ValueError(f"Unsupported message client type: {type}")
