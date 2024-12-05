# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
A concrete implementation of the KVSClient interface for interacting with the
EdgeX core-keeper service.
"""

from dataclasses import dataclass
from typing import Optional

from ...contracts.clients.interfaces.authinjector import AuthenticationInjector
from ...contracts.clients.interfaces.kvs import KVSClientABC
from ...contracts.dtos.requests import kvs as kvs_req
from ...contracts.dtos.responses import kvs as kvs_res
from ...contracts.clients.utils import common as common_utils
from ...contracts.clients.utils import request as request_utils
from ...contracts import errors
from ...contracts.common import constants


@dataclass
class KVSClient(KVSClientABC):
    """
    A concrete implementation of the KVSClient interface for interacting with the
    EdgeX core-keeper service.

    This class provides concrete implementations for the methods defined in the KVSClient
    interface, facilitating operations such as fetching, updating, and deleting key-value pairs
    from the EdgeX core-keeper service.

    Attributes:
        base_url (str): The base URL of the EdgeX core-keeper service to which the client will make
        requests.
        auth_injector (AuthenticationInjector, optional): An injector for adding authentication
        details to the requests.

    Methods:
        update_values_by_key(ctx: dict, key: str, flatten: bool, req: UpdateKeysRequest) ->
        KeysResponse:
            Updates values of the specified key and the child keys defined in the request payload.
            If no key exists at the given path, the key(s) will be created.
            If 'flatten' is true, the request json object would be flattened before storing into
            database.

        values_by_key(ctx: dict, key: str) -> MultiKeyValueResponse:
            Returns the values of the specified key prefix.

        list_keys(ctx: dict, key: str) -> KeysResponse:
            Returns the list of the keys with the specified key prefix.

        delete_key(ctx: dict, key: str) -> KeysResponse:
            Deletes the specified key.

        delete_keys_by_prefix(ctx: dict, key: str) -> KeysResponse:
            Deletes all keys with the specified prefix.
    """
    base_url: str
    auth_injector: Optional[AuthenticationInjector]

    def update_values_by_key(self, ctx: dict, key: str, flatten: bool,
                             req: kvs_req.UpdateKeysRequest) -> kvs_res.KeysResponse:
        path = common_utils.escape_and_join_path(constants.API_KVS_ROUTE, constants.KEY, key)
        query_params = {constants.FLATTEN: [str(flatten).lower()]}
        res = kvs_res.KeysResponse()
        try:
            request_utils.put_request(ctx, res, self.base_url, path, query_params, req,
                                      self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return res

    def values_by_key(self, ctx: dict, key: str) -> kvs_res.MultiKeyValueResponse:
        path = common_utils.escape_and_join_path(constants.API_KVS_ROUTE, constants.KEY, key)
        query_params = {constants.PLAINTEXT: constants.VALUE_TRUE}
        res = kvs_res.MultiKeyValueResponse()
        try:
            request_utils.get_request(ctx, res, self.base_url, path, query_params,
                                      self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return res

    def list_keys(self, ctx: dict, key: str) -> kvs_res.KeysResponse:
        path = common_utils.escape_and_join_path(constants.API_KVS_ROUTE, constants.KEY, key)
        query_params = {constants.KEY_ONLY: constants.VALUE_TRUE}
        res = kvs_res.KeysResponse()
        try:
            request_utils.get_request(ctx, res, self.base_url, path, query_params,
                                      self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return res

    def delete_key(self, ctx: dict, key: str) -> kvs_res.KeysResponse:
        path = common_utils.escape_and_join_path(constants.API_KVS_ROUTE, constants.KEY, key)
        res = kvs_res.KeysResponse()
        try:
            request_utils.delete_request(ctx, res, self.base_url, path, self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return res

    def delete_keys_by_prefix(self, ctx: dict, key: str) -> kvs_res.KeysResponse:
        path = common_utils.escape_and_join_path(constants.API_KVS_ROUTE, constants.KEY, key)
        query_params = {constants.PREFIX_MATCH: constants.VALUE_TRUE}
        res = kvs_res.KeysResponse()
        try:
            request_utils.delete_request_with_params(ctx, res, self.base_url, path,
                                                     query_params, self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return res
