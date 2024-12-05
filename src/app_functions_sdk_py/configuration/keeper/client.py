# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the KeeperClient class for interacting with a configuration service.
It provides methods to check, retrieve, and update configuration data, as well as to watch for
changes in the configuration. Additionally, it includes a utility function to create a new instance
of KeeperClient with specified service configuration.

Classes:
    KeeperClient: A client for interacting with a configuration service.

Functions:
    new_keeper_client(config: ServiceConfig) -> KeeperClient: Creates a new instance of
    KeeperClient.
"""
import base64
import json
import os
import queue
import threading

from dataclasses import dataclass
from http import HTTPStatus
from queue import Queue
from typing import Any, List, Dict, Optional

from ...configuration.config import ServiceConfig
from ...configuration.interfaces.configuration import ConfigurationClient
from ...contracts.clients import common
from ...contracts.clients.interfaces.common import CommonClientABC
from ...contracts.clients.interfaces.kvs import KVSClientABC
from ...contracts.clients.kvs import KVSClient
from ...contracts import errors
from ...contracts.common.constants import CONTENT_TYPE_JSON
from ...contracts.dtos.kvs import KVS
from ...contracts.dtos.requests import kvs
from ...configuration.keeper import (conversion, KEY_DELIMITER, KEEPER_TOPIC_PREFIX,
                                     deserialize_to_dataclass)
from ...configuration.keeper.decode import decode
from ...interfaces.messaging import MessageClient, TopicMessageQueue
from ...utils.functionexitcallback import FunctionExitCallback


@dataclass
class KeeperClient(ConfigurationClient):
    """
    A client for interacting with a configuration service, providing methods to check, retrieve,
    and update configuration data.

    Attributes:
        keeper_url (str): The URL of the configuration service.
        config_base_path (str): The base path for configuration data within the service.
        watching_done (Event): A queue used to signal when watching for configuration changes
        is done. common_client (CommonClient, optional): A client for common service interactions.
        Defaults to None.
        kvs_client (KVSClient, optional): A client for key-value store interactions.
        Defaults to None.

    Methods:
        full_path(name): Generates the full path by joining the base configuration path with the
        given name.
        has_configuration(): Checks if the service's configuration exists.
        has_sub_configuration(name): Checks if a sub-configuration exists.
        put_configuration_map(configuration, overwrite): Puts a map of configuration data.
        put_configuration(config_struct, overwrite): Puts a full configuration structure.
        get_configuration(config_struct): Retrieves the full configuration into a structure.
        watch_for_changes(update_channel, error_channel, configuration, wait_key, msg_client):
            Watches for changes in configuration.
        stop_watching(): Stops all configuration change watching processes.
        is_alive(): Checks if the configuration service is alive.
        configuration_value_exists(name): Checks if a specific configuration value exists.
        get_configuration_value(name): Retrieves a specific configuration value.
        get_configuration_value_by_full_path(full_path): Retrieves a configuration value by
        its full path.
        put_configuration_value(name, value): Puts a specific configuration value.
        get_configuration_keys(name): Retrieves all configuration keys under a specified name.
    """
    keeper_url: str
    config_base_path: str
    watching_done: threading.Event
    common_client: Optional[CommonClientABC]
    kvs_client: Optional[KVSClientABC]

    def full_path(self, name: str) -> str:
        """Generate the full path by joining the base configuration path with the given name."""
        if not self.config_base_path.endswith(KEY_DELIMITER) and len(name) > 0:
            return self.config_base_path + KEY_DELIMITER + name
        return self.config_base_path + name

    def has_configuration(self) -> bool:
        """Checks to see if the Configuration service contains the service's configuration."""
        try:
            self.kvs_client.list_keys({}, self.config_base_path)
            return True
        except errors.EdgeX as e:
            if e.http_status_code() == HTTPStatus.NOT_FOUND:
                return False
            raise errors.new_common_edgex_wrapper(e)

    def has_sub_configuration(self, name: str) -> bool:
        """Checks to see if the Configuration service contains the service's sub configuration."""
        key_path = self.full_path(name)
        try:
            self.kvs_client.list_keys({}, key_path)
            return True
        except errors.EdgeX as e:
            if e.http_status_code() == HTTPStatus.NOT_FOUND:
                return False
            raise errors.new_common_edgex_wrapper(e)

    def put_configuration_map(self, configuration: Dict[str, Any], overwrite: bool):
        """
        Puts a full map configuration into the Configuration service.
        The sub-paths to where the values are to be stored in the Configuration service are
        generated from the map key.
        """
        key_values = conversion.convert_interface_to_pairs("", configuration)

        for kv in key_values:
            try:
                exists = self.configuration_value_exists(kv.key)
            except errors.EdgeX as e:
                raise errors.new_common_edgex_wrapper(e)
            if not exists or overwrite:
                try:
                    self.put_configuration_value(kv.key, kv.value.encode('utf-8'))
                except errors.EdgeX as e:
                    raise errors.new_common_edgex_wrapper(e)

    def put_configuration(self, config_struct: Any, overwrite: bool):
        """Puts a full configuration struct into the Configuration service."""
        if overwrite:
            value = config_struct
            if isinstance(config_struct, bytes):
                value = config_struct.decode('utf-8')
            request = kvs.UpdateKeysRequest(value=value)
            self.kvs_client.update_values_by_key(
                {}, self.config_base_path, True, request
            )
            return

        kv_pairs = conversion.convert_interface_to_pairs("", config_struct)
        for kv in kv_pairs:
            try:
                exists = self.configuration_value_exists(kv.key)
            except errors.EdgeX as e:
                raise errors.new_common_edgex_wrapper(e)
            if not exists:
                try:
                    # Only create the key if not exists in core keeper
                    self.put_configuration_value(kv.key, kv.value.encode('utf-8'))
                except errors.EdgeX as e:
                    raise errors.new_common_edgex_wrapper(e)

    def get_configuration(self, config_struct: Any):
        """
        Gets the full configuration from Configuration Provider Service into the target
        configuration struct. Passed in struct is only a reference for Configuration service.
        Empty struct is fine.
        """
        exists = self.has_configuration()

        if not exists:
            raise errors.new_common_edgex(errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                                          f"the Configuration service (EdgeX Keeper) doesn't "
                                          f"contain configuration for {self.config_base_path}")

        resp = self.kvs_client.values_by_key({}, self.config_base_path)
        decode(prefix=self.config_base_path + KEY_DELIMITER,
               pairs=resp.response,
               config_target=config_struct)

    # pylint: disable=too-many-arguments, too-many-statements, too-many-positional-arguments
    def watch_for_changes(self, update_channel: Queue, error_channel: Queue,
                          configuration: Any,
                          wait_key: str, msg_client: MessageClient):
        """
        Sets up a watch for the target key and sends back updates on the update channel.
        Passed in struct is only a reference for Configuration service, empty struct is ok.
        Sends the configuration in the target struct as Any on update_channel,
        which caller must cast.
        """
        if msg_client is None:
            config_err = ValueError(
                "unable to use MessageClient to watch for configuration changes")
            error_channel.put(config_err)
            return

        messages = queue.Queue()
        topic = os.path.join(KEEPER_TOPIC_PREFIX, self.config_base_path, wait_key, "#")
        topics = [TopicMessageQueue(topic, messages)]

        try:
            msg_client.connect()
            msg_client.subscribe(topics, error_channel)
        except RuntimeError as err:
            msg_client.disconnect()
            error_channel.put(err)
            return

        def cleanup():
            msg_client.disconnect()
            update_channel.put(None)

        def watch_loop():  # pylint: disable=too-many-branches
            with FunctionExitCallback(cleanup):
                while True:  # pylint: disable=too-many-nested-blocks
                    try:
                        if self.watching_done.is_set():
                            return

                        try:
                            msg_envelope = messages.get_nowait()
                        except queue.Empty:
                            continue

                        if msg_envelope is not None:
                            if msg_envelope.contentType != CONTENT_TYPE_JSON:
                                error_channel.put(ValueError(
                                    f"invalid content type of configuration changes message, "
                                    f"expected: {CONTENT_TYPE_JSON}, "
                                    f"but got: {msg_envelope.contentType}"))
                                continue

                            try:
                                payload_bytes = base64.b64decode(msg_envelope.payload)
                                payload_dict = json.loads(payload_bytes)
                                updated_config = deserialize_to_dataclass(payload_dict, KVS)
                            except (TypeError, ValueError) as e:
                                error_channel.put(
                                    RuntimeError(
                                        f"failed to unmarshal the updated configuration: {e}"))
                                continue

                            key_prefix = os.path.join(self.config_base_path, wait_key)

                            try:
                                kv_configs = self.kvs_client.values_by_key({}, key_prefix)
                            except errors.EdgeX as e:
                                error_channel.put(ValueError(
                                    f"failed to get the configurations "
                                    f"with key prefix {key_prefix} "
                                    f"from Keeper: {e}"))
                                continue

                            if updated_config.key != key_prefix:
                                found_updated_key = False
                                for c in kv_configs.response:
                                    if c.key == updated_config.key:
                                        found_updated_key = True
                                        if c.value != updated_config.value:
                                            raise ValueError(
                                                "Values do not match, restarting the loop")
                                        break
                                if not found_updated_key:
                                    error_channel.put(ValueError(
                                        f"the updated key {updated_config.key} "
                                        f"hasn't been found in Keeper, skipping this message"))
                                    continue

                            try:
                                decode(key_prefix, kv_configs.response, configuration)
                            except TypeError as e:
                                error_channel.put(TypeError(
                                    f"failed to decode the updated configuration: {e}"))
                                continue

                            update_channel.put(configuration)
                    except ValueError:
                        continue
                    except Exception as e:  # pylint: disable=broad-except
                        error_channel.put(e)

        threading.Thread(target=watch_loop).start()

    def stop_watching(self):
        """Causes all WatchForChanges processing to stop and waits until they have stopped."""
        self.watching_done.set()

    def is_alive(self) -> bool:
        """Simply checks if Configuration service is up and running at the configured URL."""
        try:
            self.common_client.ping({})
            return True
        except errors.EdgeX:
            return False

    def configuration_value_exists(self, name: str) -> bool:
        """Checks if a configuration value exists in the Configuration service."""
        key_path = self.full_path(name)
        try:
            self.kvs_client.list_keys({}, key_path)
            return True
        except errors.EdgeX as e:
            if e.http_status_code() == HTTPStatus.NOT_FOUND:
                return False
            raise errors.new_common_edgex_wrapper(e)

    def get_configuration_value(self, name: str) -> bytes:
        """Gets a specific configuration value from the Configuration service."""
        key_path = self.full_path(name)
        return self.get_configuration_value_by_full_path(key_path)

    def get_configuration_value_by_full_path(self, full_path: str) -> bytes:
        """Gets a specific configuration value from the Configuration service by full path."""
        try:
            resp = self.kvs_client.values_by_key({}, full_path)
            if len(resp.response) == 0:
                raise errors.new_common_edgex(errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                                              f"{full_path} configuration not found")
            return resp.response[0].value.encode('utf-8')
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

    def put_configuration_value(self, name: str, value: bytes):
        """Puts a specific configuration value into the Configuration service."""
        key_path = self.full_path(name)
        request = kvs.UpdateKeysRequest(value=value.decode('utf-8'))
        try:
            self.kvs_client.update_values_by_key({}, key_path, False, request)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

    def get_configuration_keys(self, name: str) -> List[str]:
        """Returns all keys under name."""
        key_path = self.full_path(name)
        try:
            resp = self.kvs_client.list_keys({}, key_path)
            return resp.response
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)


def new_keeper_client(config: ServiceConfig) -> KeeperClient:
    """
    Creates a new instance of the KeeperClient with the provided configuration.

    This function initializes a KeeperClient object, setting up its URL, base path for
    configuration, and initializing the queues used for watching configuration changes.
    It also creates instances of CommonClient and KVSClient using the same base URL and
    authentication injector provided in the ServiceConfig. These clients are used for common
    service interactions and key-value store interactions, respectively.

    Parameters:
        config (ServiceConfig): The configuration object containing settings such as the URL of the
                                configuration service, the base path for configuration data, and
                                authentication details.

    Returns:
        KeeperClient: An instance of KeeperClient configured with the provided settings.
    """
    common_client = common.CommonClient(base_url=config.get_url(),
                                        auth_injector=config.auth_injector)
    kvs_client = KVSClient(base_url=config.get_url(), auth_injector=config.auth_injector)
    client = KeeperClient(
        keeper_url=config.get_url(),
        config_base_path=config.base_path,
        watching_done=threading.Event(),
        common_client=common_client,
        kvs_client=kvs_client,
    )
    return client
