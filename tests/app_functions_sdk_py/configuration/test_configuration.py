# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import patch
from src.app_functions_sdk_py.configuration import new_configuration_client
from src.app_functions_sdk_py.configuration.config import ServiceConfig


class ServiceConfigMock(ServiceConfig):
    def __init__(self, host, port, type):
        self.host = host
        self.port = port
        self.type = type


class ConfigurationClientTests(unittest.TestCase):

    @patch('src.app_functions_sdk_py.configuration.new_keeper_client')
    def test_create_config_client_with_keeper_type(self, mock_new_keeper_client):
        svc_config = ServiceConfigMock("localhost", 8080, "keeper")
        new_configuration_client(svc_config)
        mock_new_keeper_client.assert_called_once_with(svc_config)

    def test_create_config_client_with_invalid_host(self):
        svc_config = ServiceConfigMock("", 8080, "keeper")
        with self.assertRaises(Exception) as context:
            new_configuration_client(svc_config)
        self.assertTrue("Configuration service host and/or port not set" in str(context.exception))

    def test_create_config_client_with_invalid_port(self):
        svc_config = ServiceConfigMock("localhost", 0, "keeper")
        with self.assertRaises(Exception) as context:
            new_configuration_client(svc_config)
        self.assertTrue("Configuration service host and/or port not set" in str(context.exception))

    def test_create_config_client_with_invalid_type(self):
        svc_config = ServiceConfigMock("localhost", 8080, "unknown")
        with self.assertRaises(Exception) as context:
            new_configuration_client(svc_config)
        self.assertTrue("unknown configuration client type 'unknown' requested" in str(context.exception))


if __name__ == '__main__':
    unittest.main()
