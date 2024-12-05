# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import os
import unittest
from unittest.mock import patch, MagicMock
from src.app_functions_sdk_py.bootstrap import environment

default_config_file = "configuration.yaml"
test_config_file = "test.yaml"
default_dir = "default"
test_dir = "test"
default_remote_hosts = ["localhost"]
test_remote_hosts = ["test1", "test2"]
test_timeout = "60s"
default_timeout = "30s"
test_provider = "test_provider"
default_provider = "consul.http://localhost:8500"


class TestEnvironment(unittest.TestCase):

    @patch.dict('os.environ', {'TEST_ENV_VAR': '123'})
    def test_get_env_var_as_int_valid(self):
        logger = MagicMock()
        result = environment.get_env_var_as_int(logger, 'TEST_ENV_VAR', 456)
        self.assertEqual(result, 123)

    @patch.dict('os.environ', {'TEST_ENV_VAR': 'abc'})
    def test_get_env_var_as_int_invalid(self):
        logger = MagicMock()
        result = environment.get_env_var_as_int(logger, 'TEST_ENV_VAR', 456)
        self.assertEqual(result, 456)
        logger.warn.assert_called_once()

    @patch('src.app_functions_sdk_py.bootstrap.environment.get_env_var_as_int')
    def test_get_startup_info(self, mock_get_env_var_as_int):
        logger = MagicMock()
        mock_get_env_var_as_int.side_effect = [60, 1]
        result = environment.get_startup_info(logger)
        self.assertEqual(result.duration, 60)
        self.assertEqual(result.interval, 1)

    @patch.dict('os.environ', {'TEST_ENV_VAR': 'True'})
    def test_get_env_var_as_bool_true(self):
        logger = MagicMock()
        result, override = environment.get_env_var_as_bool(logger, 'TEST_ENV_VAR',
                                                           False)
        self.assertTrue(result)
        self.assertTrue(override)

    @patch.dict('os.environ', {'TEST_ENV_VAR': 'False'})
    def test_get_env_var_as_bool_false(self):
        logger = MagicMock()
        result, override = environment.get_env_var_as_bool(logger, 'TEST_ENV_VAR',
                                                           True)
        self.assertFalse(result)
        self.assertTrue(override)

    @patch.dict('os.environ', {environment.ENV_KEY_USE_REGISTRY: 'true'})
    def test_use_registry(self):
        logger = MagicMock()
        result, override = environment.use_registry(logger)
        self.assertTrue(result)
        self.assertTrue(override)
        os.environ.pop(environment.ENV_KEY_USE_REGISTRY, None)
        result, override = environment.use_registry(logger)
        self.assertFalse(result)
        self.assertFalse(override)

    @patch.dict('os.environ', {environment.ENV_KEY_SECURITY_SECRET_STORE: 'TRUE'})
    def test_use_security_secret_store(self):
        logger = MagicMock()
        result = environment.use_security_secret_store(logger)
        self.assertTrue(result)
        os.environ.pop(environment.ENV_KEY_SECURITY_SECRET_STORE, None)
        result = environment.use_security_secret_store(logger)
        self.assertFalse(result)

    @patch.dict('os.environ', {environment.ENV_KEY_COMMON_CONFIG: test_config_file})
    def test_get_common_config(self):
        logger = MagicMock()
        result = environment.get_common_config_file_name(logger, default_config_file)
        self.assertEqual(result, test_config_file)
        os.environ.pop(environment.ENV_KEY_COMMON_CONFIG, None)
        result = environment.get_common_config_file_name(logger, default_config_file)
        self.assertEqual(result, default_config_file)

    @patch.dict('os.environ', {environment.ENV_KEY_CONFIG_FILE: test_config_file})
    def test_get_config_file(self):
        logger = MagicMock()
        result = environment.get_config_file_name(logger, default_config_file)
        self.assertEqual(result, test_config_file)
        os.environ.pop(environment.ENV_KEY_CONFIG_FILE, None)
        result = environment.get_config_file_name(logger, default_config_file)
        self.assertEqual(result, default_config_file)

    @patch.dict('os.environ', {environment.ENV_KEY_PROFILE: test_dir})
    def test_get_profile_dir(self):
        logger = MagicMock()
        result = environment.get_profile_directory(logger, default_dir)
        self.assertEqual(result, f"{test_dir}/")
        os.environ.pop(environment.ENV_KEY_PROFILE, None)
        result = environment.get_profile_directory(logger, default_dir)
        self.assertEqual(result, f"{default_dir}/")

    @patch.dict('os.environ',
                {environment.ENV_KEY_REMOTE_SERVICE_HOSTS: ','.join(test_remote_hosts)})
    def test_get_remote_service_hosts(self):
        logger = MagicMock()
        result = environment.get_remote_service_hosts(logger, default_remote_hosts)
        self.assertListEqual(result, test_remote_hosts)
        os.environ.pop(environment.ENV_KEY_REMOTE_SERVICE_HOSTS, None)
        result = environment.get_remote_service_hosts(logger, default_remote_hosts)
        self.assertListEqual(result, default_remote_hosts)

    @patch.dict('os.environ', {environment.ENV_KEY_CONFIG_DIR: test_dir})
    def test_get_config_dir(self):
        logger = MagicMock()
        result = environment.get_config_directory(logger, default_dir)
        self.assertEqual(result, test_dir)
        os.environ[environment.ENV_KEY_CONFIG_DIR] = ""
        result = environment.get_config_directory(logger, "")
        self.assertEqual(result, environment.DEFAULT_CONFIG_DIR)
        os.environ.pop(environment.ENV_KEY_PROFILE, None)
        result = environment.get_config_directory(logger, default_dir)
        self.assertEqual(result, default_dir)

    @patch.dict('os.environ', {environment.ENV_KEY_FILE_URI_TIMEOUT: test_timeout})
    def test_get_request_timeout(self):
        logger = MagicMock()
        result = environment.get_request_timeout(logger, default_timeout)
        self.assertEqual(result, test_timeout)
        os.environ[environment.ENV_KEY_FILE_URI_TIMEOUT] = ""
        result = environment.get_request_timeout(logger, "")
        self.assertEqual(result, environment.DEFAULT_FILE_URI_TIMEOUT)
        os.environ.pop(environment.ENV_KEY_FILE_URI_TIMEOUT, None)
        result = environment.get_request_timeout(logger, default_timeout)
        self.assertEqual(result, default_timeout)

    @patch.dict('os.environ', {environment.ENV_KEY_CONFIG_PROVIDER_URL: test_provider})
    def test_get_request_timeout(self):
        logger = MagicMock()
        result = environment.get_config_provider_url(logger, default_provider)
        self.assertEqual(result, test_provider)
        os.environ[environment.ENV_KEY_CONFIG_PROVIDER_URL] = environment.NO_CONFIG_PROVIDER
        result = environment.get_config_provider_url(logger, default_provider)
        self.assertEqual(result, "")
        os.environ.pop(environment.ENV_KEY_CONFIG_PROVIDER_URL, None)
        result = environment.get_config_provider_url(logger, default_provider)
        self.assertEqual(result, default_provider)


if __name__ == '__main__':
    unittest.main()
