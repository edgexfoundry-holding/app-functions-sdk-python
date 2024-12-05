# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the ConfigurationClient abstract base class for creating configuration clients.
These clients are designed to interact with a configuration service, enabling operations such as
checking for the existence of configuration, retrieving and updating configuration data,
and watching for configuration changes.
"""

from abc import ABC, abstractmethod
from queue import Queue
from typing import Any, Dict, List

from ...interfaces.messaging import MessageClient


class ConfigurationClient(ABC):
    """
    Abstract base class for a Configuration Client.

    Methods:
        has_configuration() -> bool:
            Checks if the Configuration service contains the service's configuration.

        has_sub_configuration(name: str) -> bool:
            Checks if the Configuration service contains the service's sub configuration.

        put_configuration_map(configuration: Dict[str, Any], overwrite: bool):
            Puts a full map configuration into the Configuration service.

        put_configuration(config_struct: Any, overwrite: bool):
            Puts a full configuration struct into the Configuration service.

        get_configuration(config_struct: Any) -> Any:
            Retrieves the full configuration from the Configuration service.

        watch_for_changes(update_channel: Any, error_channel: Any, configuration: Any,
                          wait_key: str, msg_client: Any):
            Sets up a watch for configuration changes and sends updates on the update channel.

        stop_watching():
            Stops all watch_for_changes processing.

        is_alive() -> bool:
            Checks if the Configuration service is up and running.

        configuration_value_exists(name: str) -> bool:
            Checks if a configuration value exists in the Configuration service.

        get_configuration_value(name: str) -> bytes:
            Retrieves a specific configuration value from the Configuration service.

        get_configuration_value_by_full_path(full_path: str) -> bytes:
            Retrieves a specific configuration value by full path from the Configuration service.

        put_configuration_value(name: str, value: bytes):
            Puts a specific configuration value into the Configuration service.

        get_configuration_keys(name: str) -> List[str]:
            Returns all keys under a specified name.
    """

    @abstractmethod
    def has_configuration(self) -> bool:
        """Checks to see if the Configuration service contains the service's configuration."""

    @abstractmethod
    def has_sub_configuration(self, name: str) -> bool:
        """Checks to see if the Configuration service contains the service's sub configuration."""

    @abstractmethod
    def put_configuration_map(self, configuration: Dict[str, Any], overwrite: bool):
        """
        Puts a full map configuration into the Configuration service.
        The sub-paths to where the values are to be stored in the Configuration service are
        generated from the map key.
        """

    @abstractmethod
    def put_configuration(self, config_struct: Any, overwrite: bool):
        """Puts a full configuration struct into the Configuration service."""

    @abstractmethod
    def get_configuration(self, config_struct: Any):
        """
        Gets the full configuration from Configuration Provider Service into the target
        configuration struct. Passed in struct is only a reference for Configuration service.
        Empty struct is fine.
        """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    @abstractmethod
    def watch_for_changes(self, update_channel: Queue, error_channel: Queue,
                          configuration: Any,
                          wait_key: str, msg_client: MessageClient):
        """
        Sets up a watch for the target key and sends back updates on the update channel.
        Passed in struct is only a reference for Configuration service, empty struct is ok.
        Sends the configuration in the target struct as Any on update_channel, which caller
        must cast.
        """

    @abstractmethod
    def stop_watching(self):
        """Causes all WatchForChanges processing to stop and waits until they have stopped."""

    @abstractmethod
    def is_alive(self) -> bool:
        """Simply checks if Configuration service is up and running at the configured URL."""

    @abstractmethod
    def configuration_value_exists(self, name: str) -> bool:
        """Checks if a configuration value exists in the Configuration service."""

    @abstractmethod
    def get_configuration_value(self, name: str) -> bytes:
        """Gets a specific configuration value from the Configuration service."""

    @abstractmethod
    def get_configuration_value_by_full_path(self, full_path: str) -> bytes:
        """Gets a specific configuration value from the Configuration service by full path."""

    @abstractmethod
    def put_configuration_value(self, name: str, value: bytes):
        """Puts a specific configuration value into the Configuration service."""

    @abstractmethod
    def get_configuration_keys(self, name: str) -> List[str]:
        """Returns all keys under name."""
