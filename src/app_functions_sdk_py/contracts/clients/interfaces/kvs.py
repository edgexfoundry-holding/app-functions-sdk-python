# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the KVSClientABC abstract base class for interactions with the
key-value store (KVS) endpoint in the EdgeX core-keeper service. It outlines the essential
operations for managing key-value pairs, including updating, retrieving, listing, and deleting keys
or keys by prefix.
"""

from abc import ABC, abstractmethod

from ....contracts.dtos.requests import kvs as kvs_request
from ....contracts.dtos.responses import kvs as kvs_response


class KVSClientABC(ABC):
    """
    Defines the interface for interactions with the kvs endpoint on the EdgeX core-keeper service.

    This interface defines the essential operations for interacting with a key-value store,
    including updating values by key, retrieving values by key, listing keys, and deleting keys or
    keys by prefix. Implementations of this class are expected to provide concrete methods for
    these operations, tailored to a specific key-value store backend.

    Methods:
        update_values_by_key(ctx: dict, key: str, flatten: bool, reqs: UpdateKeysRequest) ->
        KeysResponse:
            Updates values of the specified key and the child keys defined in the request payload.
            If no key exists at the given path, the key(s) will be created.
            If 'flatten' is true, the request json object would be flattened before storing
            into database.

        values_by_key(ctx: dict, key: str) -> MultiKeyValueResponse:
            Returns the values of the specified key prefix.

        list_keys(ctx: dict, key: str) -> KeysResponse:
            Returns the list of the keys with the specified key prefix.

        delete_key(ctx: dict, key: str) -> KeysResponse:
            Deletes the specified key.

        delete_keys_by_prefix(ctx: dict, key: str) -> KeysResponse:
            Deletes all keys with the specified prefix.
    """
    @abstractmethod
    def update_values_by_key(self, ctx: dict, key: str, flatten: bool,
                             req: kvs_request.UpdateKeysRequest) -> kvs_response.KeysResponse:
        """
        Updates values of the specified key and the child keys defined in the request payload.
        """

    @abstractmethod
    def values_by_key(self, ctx: dict, key: str) -> kvs_response.MultiKeyValueResponse:
        """
        Returns the values of the specified key prefix.
        """

    @abstractmethod
    def list_keys(self, ctx: dict, key: str) -> kvs_response.KeysResponse:
        """
        Returns the list of the keys with the specified key prefix.
        """

    @abstractmethod
    def delete_key(self, ctx: dict, key: str) -> kvs_response.KeysResponse:
        """
        Deletes the specified key.
        """

    @abstractmethod
    def delete_keys_by_prefix(self, ctx: dict, key: str) -> kvs_response.KeysResponse:
        """
        Deletes all keys with the specified prefix.
        """
