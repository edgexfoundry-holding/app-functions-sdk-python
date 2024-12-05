# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest

from src.app_functions_sdk_py.contracts.clients.utils.request import HTTPMethod
from src.app_functions_sdk_py.contracts.dtos.responses import kvs
from src.app_functions_sdk_py.contracts.clients.kvs import KVSClient
from src.app_functions_sdk_py.contracts.common import constants
from src.app_functions_sdk_py.contracts.dtos.requests import kvs as kvs_req
from tests.app_functions_sdk_py.contracts.clients.test_common import run_test_server


class TestKVSClients(unittest.TestCase):

    def setUp(self):
        self.test_key = "TestWritable"

    def test_update_values_by_key(self):
        expected_response = kvs.KeysResponse()
        run_test_server(HTTPMethod.PUT.value,
                        constants.API_KVS_ROUTE + "/" + constants.KEY + "/" + self.test_key,
                        expected_response, KVSClient,
                        lambda client: self.assertIsInstance(
                            client.update_values_by_key({}, self.test_key, True,
                                                        kvs_req.UpdateKeysRequest()),
                            kvs.KeysResponse)
                        )

    def test_values_by_key(self):
        expected_response = kvs.MultiKeyValueResponse()
        run_test_server(HTTPMethod.GET.value,
                        constants.API_KVS_ROUTE + "/" + constants.KEY + "/" + self.test_key,
                        expected_response, KVSClient,
                        lambda client: self.assertIsInstance(
                            client.values_by_key({}, self.test_key),
                            kvs.MultiKeyValueResponse)
                        )

    def test_list_keys(self):
        expected_response = kvs.KeysResponse()
        run_test_server(HTTPMethod.GET.value,
                        constants.API_KVS_ROUTE + "/" + constants.KEY + "/" + self.test_key,
                        expected_response, KVSClient,
                        lambda client: self.assertIsInstance(
                            client.list_keys({}, self.test_key),
                            kvs.KeysResponse)
                        )

    def test_delete_key(self):
        expected_response = kvs.KeysResponse()
        run_test_server(HTTPMethod.DELETE.value,
                        constants.API_KVS_ROUTE + "/" + constants.KEY + "/" + self.test_key,
                        expected_response, KVSClient,
                        lambda client: self.assertIsInstance(
                            client.delete_key({}, self.test_key),
                            kvs.KeysResponse)
                        )

    def test_delete_keys_by_prefix(self):
        expected_response = kvs.KeysResponse()
        run_test_server(HTTPMethod.DELETE.value,
                        constants.API_KVS_ROUTE + "/" + constants.KEY + "/" + self.test_key,
                        expected_response, KVSClient,
                        lambda client: self.assertIsInstance(
                            client.delete_keys_by_prefix({}, self.test_key),
                            kvs.KeysResponse)
                        )


if __name__ == '__main__':
    unittest.main()
