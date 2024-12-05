#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import unittest
import uuid

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.utils import helper
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.context import Context


class TestHelper(unittest.TestCase):

    def setUp(self):
        self.logger = EdgeXLogger('test_service', DEBUG)
        self.dic = Container()
        self.dic.update({
            LoggingClientInterfaceName: lambda get: self.logger
        })
        self.ctx = Context(str(uuid.uuid4()), self.dic, "")

    def test_delete_empty_and_trim(self):
        target = [" Hel lo", "test ", " "]
        results = helper.delete_empty_and_trim(target)
        # Should have 4 elements (space counts as an element)
        self.assertEqual(2, len(results))
        self.assertEqual("Hel lo", results[0])
        self.assertEqual("test", results[1])
