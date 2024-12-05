#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import unittest
import uuid
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.functions import jsonlogic
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.context import Context


class TestBatch(unittest.TestCase):
    def setUp(self):
        self.logger = EdgeXLogger('test_service', DEBUG)
        self.dic = Container()
        self.dic.update({
            LoggingClientInterfaceName: lambda get: self.logger
        })
        self.ctx = Context(str(uuid.uuid4()), self.dic, "")

    def test_configurable(self):
        configurable = Configurable(logger=self.ctx.logger(), sp=Mock())
        params = dict()
        params[jsonlogic.RULE] = "{}"

        trx = configurable.json_logic(params)
        self.assertIsNotNone(trx)

    def test_simple(self):
        json_logic, err = jsonlogic.new_json_logic('{"==": [1, 1]}')
        self.assertIsNone(err)
        data = "{}"

        continue_pipeline, result = json_logic.evaluate(self.ctx, data)

        self.assertIsNotNone(result)
        self.assertTrue(continue_pipeline)
        self.assertEqual(data, result)

    def test_advanced(self):
        json_logic, err = jsonlogic.new_json_logic("""{ "and" : [
            {"<" : [ { "var" : "temp" }, 110 ]},
            {"==" : [ { "var" : "sensor.type" }, "temperature" ] }
          ] }""")
        self.assertIsNone(err)
        data = '{"temp": 100, "sensor": {"type": "temperature"}}'

        continue_pipeline, result = json_logic.evaluate(self.ctx, data)

        self.assertIsNotNone(result)
        self.assertTrue(continue_pipeline)
        self.assertEqual(data, result)

    def test_malformed_json_rule(self):
        # missing quote
        _, err = jsonlogic.new_json_logic('{"==: [1, 1]}')
        self.assertIsNotNone(err)

    def test_valid_json_bad_rule(self):
        json_logic, err = jsonlogic.new_json_logic('{"notAnOperator": [1, 1]}')
        self.assertIsNone(err)
        data = "{}"

        continue_pipeline, result = json_logic.evaluate(self.ctx, data)

        self.assertIsNotNone(result)
        self.assertFalse(continue_pipeline)
        self.assertTrue("unable to apply JSONLogic rule" in str(result))

    def test_non_json_data(self):
        json_logic, err = jsonlogic.new_json_logic('{"==": [1, 1]}')
        self.assertIsNone(err)
        data = "iAmNotJson"

        continue_pipeline, result = json_logic.evaluate(self.ctx, data)

        self.assertIsNotNone(result)
        self.assertFalse(continue_pipeline)
        self.assertTrue("JSONLogic input data should be JSON format" in str(result))
