#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import base64
import gzip
import unittest
import uuid
import zlib
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.functions import compression
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.functions.compression import new_compression
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.context import Context

clear_string = "This is the test string used for testing"


class TestCompression(unittest.TestCase):
    def setUp(self):
        self.logger = EdgeXLogger('test_service', DEBUG)
        self.dic = Container()
        self.dic.update({
            LoggingClientInterfaceName: lambda get: self.logger
        })
        self.ctx = Context(str(uuid.uuid4()), self.dic, "")

    def test_configurable_gzip(self):
        configurable = Configurable(logger=self.ctx.logger(), sp=Mock())
        params = dict()

        params[compression.ALGORITHM] = compression.COMPRESS_GZIP
        transform = configurable.compress(params)
        self.assertIsNotNone(transform, "return result for Compression should not be none")

        params[compression.ALGORITHM] = compression.COMPRESS_ZLIB
        transform = configurable.compress(params)
        self.assertIsNotNone(transform, "return result for Compression should not be none")

        params[compression.ALGORITHM] = "unknown"
        transform = configurable.compress(params)
        self.assertIsNone(transform, "return result for Compression should be none")

    def test_gzip(self):
        comp = new_compression()
        continue_pipeline, result = comp.compress_with_gzip(self.ctx, clear_string.encode())
        self.assertTrue(continue_pipeline)

        decoded = base64.b64decode(result)
        decompressed = gzip.decompress(decoded)
        self.assertTrue(clear_string, str(decompressed))

        continue_pipeline, result2 = comp.compress_with_gzip(self.ctx, clear_string.encode())
        self.assertTrue(continue_pipeline)
        self.assertEqual(result, result2)

    def test_zlib(self):
        comp = new_compression()
        continue_pipeline, result = comp.compress_with_zlib(self.ctx, clear_string.encode())
        self.assertTrue(continue_pipeline)

        decoded = base64.b64decode(result)
        decompressed = zlib.decompress(decoded)
        self.assertTrue(clear_string, str(decompressed))

        continue_pipeline, result2 = comp.compress_with_zlib(self.ctx, clear_string.encode())
        self.assertTrue(continue_pipeline)
        self.assertEqual(result, result2)
