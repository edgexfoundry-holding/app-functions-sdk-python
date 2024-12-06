# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import time
import unittest
from dataclasses import dataclass
from http.server import HTTPServer
from typing import Optional, Any

from numpy import int64, float64

from src.app_functions_sdk_py.configuration import ServiceConfig
from src.app_functions_sdk_py.configuration.keeper.client import new_keeper_client, KeeperClient
from tests.app_functions_sdk_py.configuration.keeper.mock_keeper import MockCoreKeeper

TEST_HOST = ""
PORT = 0
DUMMY_CONFIG = "dummy"


@dataclass
class LoggingInfo:
    enable_remote: bool = False
    file: str = ""


@dataclass
class TestConfig:
    logging: LoggingInfo = LoggingInfo()
    port: int = 0
    host: str = ""
    log_level: str = ""
    temp: float64 = float64(0.0)


def make_core_keeper_client(service_name):
    conf = ServiceConfig(
        protocol="http",
        host=TEST_HOST,
        port=PORT,
        type="keeper",
        base_path=service_name,
        access_token="",
        get_access_token=None,
        auth_injector=None,
        optional={}
    )
    client = new_keeper_client(conf)
    return client


def get_unique_service_name():
    return "serviceName" + str(time.time_ns())


def config_value_exists(key: str, client: KeeperClient):
    return client.configuration_value_exists(key)


def create_config_map() -> dict[str, Any]:
    return {
        "int": 1,
        "int64": int64(64),
        "float64": float64(1.4),
        "string": "hellp",
        "bool": True,
        "nestedNode": {
            "field1": "value1",
            "field2": "value2",
        },
    }


class TestKeeperClient(unittest.TestCase):
    def setUp(self):
        global TEST_HOST, PORT
        if TEST_HOST == "" or PORT != 59883:
            self.mock_core_keeper = MockCoreKeeper()
            self.test_mock_server = self.mock_core_keeper.start()

            server_url = self.test_mock_server.server_address
            TEST_HOST = server_url[0]
            PORT = server_url[1]

    def tearDown(self):
        if self.test_mock_server is not None:
            self.test_mock_server.shutdown()
            self.test_mock_server.server_close()

    def reset(self, client: KeeperClient):
        if self.mock_core_keeper is not None:
            self.mock_core_keeper.reset()
        else:
            # delete the key(s) created in each test if testing on real Keeper service
            key = client.config_base_path
            client.kvs_client.delete_keys_by_prefix({}, key)

    def test_is_alive(self):
        client = make_core_keeper_client(get_unique_service_name())
        try:
            actual = client.is_alive()
            self.assertTrue(actual)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_has_configuration_false(self):
        client = make_core_keeper_client(get_unique_service_name())
        try:
            actual = client.has_configuration()
            self.assertFalse(actual)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_has_configuration_true(self):
        client = make_core_keeper_client(get_unique_service_name())
        try:
            client.put_configuration(DUMMY_CONFIG, True)
            actual = client.has_configuration()
            self.assertTrue(actual)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_has_sub_configuration_false(self):
        client = make_core_keeper_client(get_unique_service_name())
        try:
            actual = client.has_sub_configuration(DUMMY_CONFIG)
            self.assertFalse(actual)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_has_sub_configuration_true(self):
        client = make_core_keeper_client(get_unique_service_name())
        try:
            client.put_configuration_value(DUMMY_CONFIG, DUMMY_CONFIG.encode('utf-8'))
            actual = client.has_sub_configuration(DUMMY_CONFIG)
            self.assertTrue(actual)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_put_configuration_map_no_pre_values(self):
        client = make_core_keeper_client(get_unique_service_name())
        self.addCleanup(self.reset, client)

        config_map = create_config_map()
        try:
            client.put_configuration_map(config_map, False)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_put_configuration_map_without_overwrite(self):
        client = make_core_keeper_client(get_unique_service_name())
        self.addCleanup(self.reset, client)

        config_map = create_config_map()
        try:
            client.put_configuration_map(config_map, False)
            expected = client.get_configuration_value("nestedNode/field1")
            config_map["nestedNode"] = {"field1": "overwrite1", "field2": "overwrite2"}
            client.put_configuration_map(config_map, False)
            actual = client.get_configuration_value("nestedNode/field1")
            self.assertEqual(expected, actual, "Values for nestedNode/field1 are not equal, expected equal")
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_put_configuration_map_with_overwrite(self):
        client = make_core_keeper_client(get_unique_service_name())
        self.addCleanup(self.reset, client)

        try:
            config_map = create_config_map()
            client.put_configuration_map(config_map, False)
            expected = client.get_configuration_value("nestedNode/field1")
            config_map["nestedNode"] = {"field1": "overwrite1", "field2": "overwrite2"}
            client.put_configuration_map(config_map, True)
            actual = client.get_configuration_value("nestedNode/field1")
            self.assertNotEqual(expected, actual, "Values for nestedNode/field1 are equal, expected not equal")
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_put_configuration(self):
        client = make_core_keeper_client(get_unique_service_name())
        self.addCleanup(self.reset, client)

        expected = TestConfig(
            logging=LoggingInfo(enable_remote=True, file="NONE"),
            port=8000,
            host="localhost",
            log_level="debug",
            temp=float64(36.123456)
        )

        try:
            client.put_configuration(expected, True)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

        try:
            actual = client.has_configuration()
            self.assertTrue(actual, "failed to put configuration")
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

        self.assertTrue(config_value_exists("logging/enable_remote", client))
        self.assertTrue(config_value_exists("logging/file", client))
        self.assertTrue(config_value_exists("port", client))
        self.assertTrue(config_value_exists("host", client))
        self.assertTrue(config_value_exists("log_level", client))
        self.assertTrue(config_value_exists("temp", client))

    def test_get_configuration(self):
        client = make_core_keeper_client(get_unique_service_name())
        self.addCleanup(self.reset, client)

        expected = TestConfig(
            logging=LoggingInfo(enable_remote=True, file="NONE"),
            port=8000,
            host="localhost",
            log_level="debug",
            temp=float64(36.123456)
        )

        try:
            client.put_configuration(expected, True)
            actual = client.get_configuration(TestConfig())
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

        self.assertEqual(expected.logging.enable_remote, actual.logging.enable_remote, "logging.enable_remote not as expected")
        self.assertEqual(expected.logging.file, actual.logging.file, "logging.file not as expected")
        self.assertEqual(expected.port, actual.port, "port not as expected")
        self.assertEqual(expected.host, actual.host, "host not as expected")
        self.assertEqual(expected.log_level, actual.log_level, "log_level not as expected")
        self.assertEqual(expected.temp, actual.temp, "temp not as expected")

    def test_configuration_value_exists(self):
        client = make_core_keeper_client(get_unique_service_name())
        self.addCleanup(self.reset, client)

        key = "Foo"
        value = "bar".encode('utf-8')

        try:
            actual = client.configuration_value_exists(key)
            self.assertFalse(actual)
            client.put_configuration_value(key, value)
            actual = client.configuration_value_exists(key)
            self.assertTrue(actual)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_get_configuration_value(self):
        client = make_core_keeper_client(get_unique_service_name())
        self.addCleanup(self.reset, client)

        key = "Foo"
        expected = "bar".encode('utf-8')

        try:
            client.put_configuration_value(key, expected)
            actual = client.get_configuration_value(key)
            self.assertEqual(expected, actual)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_put_configuration_value(self):
        client = make_core_keeper_client(get_unique_service_name())
        self.addCleanup(self.reset, client)

        key = "Foo"
        expected = "bar".encode('utf-8')

        try:
            client.put_configuration_value(key, expected)
            resp = client.kvs_client.values_by_key({}, client.full_path(key))

            actual = str(resp.response[0].value).encode('utf-8')
            self.assertEqual(expected, actual)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")


if __name__ == '__main__':
    unittest.main()
