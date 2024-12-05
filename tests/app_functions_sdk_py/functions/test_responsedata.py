#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import json
import unittest
import uuid
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.contracts.clients.utils.common import convert_any_to_dict
from src.app_functions_sdk_py.contracts.common.constants import VALUE_TYPE_INT32
from src.app_functions_sdk_py.contracts.dtos.event import new_event
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.functions import responsedata
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.context import Context


class TestCompression(unittest.TestCase):
    def setUp(self):
        self.logger = EdgeXLogger('test_service', DEBUG)
        self.dic = Container()
        self.dic.update({
            LoggingClientInterfaceName: lambda get: self.logger
        })
        self.ctx = Context(str(uuid.uuid4()), self.dic, "")

    def test_configurable(self):
        configurable = Configurable(logger=self.ctx.logger(), sp=Mock())

        class TestData:
            def __init__(self, name: str, params: dict):
                self.name = name
                self.params = params

        tests = [
            TestData("Non Existent Parameter", {}),
            TestData("Valid Parameter With Value", {responsedata.RESPONSE_CONTENT_TYPE: "application/json"}),
            TestData("Valid Parameter Without Value", {responsedata.RESPONSE_CONTENT_TYPE: ""}),
            TestData("Unknown Parameter", {"Unknown": "scary/text"}),
        ]
        for tt in tests:
            with self.subTest(msg=tt.name):
                trx = configurable.set_response_data(tt.params)
                self.assertIsNotNone(trx, "return result from SetResponseData should not be None")

    def test_set_string(self):
        expected = self.get_expected_event_xml()
        target = responsedata.ResponseData("")

        continue_pipeline, result = target.set_response_data(self.ctx, expected)

        self.assertTrue(continue_pipeline)
        self.assertIsNotNone(result)

        self.assertEqual(expected, self.ctx.response_data().decode())

    def test_set_bytes(self):
        expected = self.get_expected_event_xml().encode()
        target = responsedata.ResponseData("")

        continue_pipeline, result = target.set_response_data(self.ctx, expected)

        self.assertTrue(continue_pipeline)
        self.assertIsNotNone(result)

        self.assertEqual(expected, self.ctx.response_data())

    def test_set_event(self):
        event = new_event("profile1", "dev1", "source1")
        expected = json.dumps(convert_any_to_dict(event)).encode()
        target = responsedata.ResponseData("")

        continue_pipeline, result = target.set_response_data(self.ctx, event)

        self.assertTrue(continue_pipeline)
        self.assertIsNotNone(result)

        self.assertEqual(expected, self.ctx.response_data())

    def test_set_no_data(self):
        target = responsedata.ResponseData("")
        continue_pipeline, result = target.set_response_data(self.ctx, None)

        self.assertFalse(continue_pipeline)
        self.assertTrue("No Data Received" in str(result))

    def get_expected_event_xml(self) -> str:
        event = new_event("profile1", "dev1", "source1")
        event.add_base_reading("resource1", VALUE_TYPE_INT32, 32)

        xml, err = event.to_xml()
        self.assertIsNone(err)
        return xml
