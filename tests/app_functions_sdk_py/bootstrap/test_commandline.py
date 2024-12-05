# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import argparse
import unittest
from unittest.mock import patch
from src.app_functions_sdk_py.bootstrap.commandline import CommandLineParser


class TestCommandLineParser(unittest.TestCase):
    @patch('argparse.ArgumentParser.parse_args')
    def test_command_line_parser(self, mock_args):
        mock_args.return_value = argparse.Namespace(
            configDir='test_dir',
            configFile='test_file',
            configProvider='test_provider',
            commonConfig='test_common',
            profile='test_profile',
            registry=True,
            overwrite=True,
            skipVersionCheck=True,
            serviceKey='test_key',
            dev=True,
            remoteServiceHosts='192.0.1.20,192.0.1.5,localhost'
        )

        parser = CommandLineParser()
        self.assertEqual(parser.config_directory(), 'test_dir')
        self.assertEqual(parser.config_file(), 'test_file')
        self.assertEqual(parser.config_provider(), 'test_provider')
        self.assertEqual(parser.common_config(), 'test_common')
        self.assertEqual(parser.profile(), 'test_profile')
        self.assertEqual(parser.registry(), True)
        self.assertEqual(parser.overwrite(), True)
        self.assertEqual(parser.skip_version_check(), True)
        self.assertEqual(parser.service_key(), 'test_key')
        self.assertEqual(parser.dev_mode(), True)
        self.assertEqual(parser.remote_service_hosts(), ['192.0.1.20', '192.0.1.5', 'localhost'])


if __name__ == '__main__':
    unittest.main()
