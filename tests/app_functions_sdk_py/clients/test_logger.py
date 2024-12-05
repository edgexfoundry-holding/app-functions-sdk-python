# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import patch
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, INFO, TRACE, DEBUG, WARN, ERROR


class TestEdgeXLogger(unittest.TestCase):
    def setUp(self):
        self.service_key = 'test_service'
        self.level = INFO
        self.logger = EdgeXLogger(self.service_key, self.level)

    def test_initialization_with_valid_level(self):
        self.assertEqual(self.logger.service_key, self.service_key)
        self.assertEqual(self.logger.logger.level, self.level)

    def test_initialization_with_invalid_level_raises_error(self):
        with self.assertRaises(ValueError):
            EdgeXLogger(self.service_key, 'INVALID')

    @patch.object(EdgeXLogger, 'trace')
    def test_trace(self, mock_trace):
        self.logger.trace('test trace')
        mock_trace.assert_called_once_with('test trace')

    @patch.object(EdgeXLogger, 'debug')
    def test_debug(self, mock_debug):
        self.logger.debug('test debug')
        mock_debug.assert_called_once_with('test debug')

    @patch.object(EdgeXLogger, 'info')
    def test_info(self, mock_info):
        self.logger.info('test info')
        mock_info.assert_called_once_with('test info')

    @patch.object(EdgeXLogger, 'warn')
    def test_warn(self, mock_warning):
        self.logger.warn('test warning')
        mock_warning.assert_called_once_with('test warning')

    @patch.object(EdgeXLogger, 'error')
    def test_error(self, mock_error):
        self.logger.error('test error')
        mock_error.assert_called_once_with('test error')

    def test_set_log_level_to_debug(self):
        self.logger.set_log_level('DEBUG')
        self.assertEqual(self.logger.logger.level, DEBUG)

    def test_set_log_level_to_invalid_level_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.logger.set_log_level('INVALID')


if __name__ == '__main__':
    unittest.main()
