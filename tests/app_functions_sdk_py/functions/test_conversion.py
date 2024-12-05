#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import unittest
import uuid
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.contracts.dtos.event import Event
from src.app_functions_sdk_py.functions import conversion
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.context import Context


class TestConversion(unittest.TestCase):
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

        params[conversion.TRANSFORM_TYPE] = conversion.TRANSFORM_XML
        transform = configurable.transform(params)
        self.assertIsNotNone(transform, "return result for Conversion should not be none")

        params[conversion.TRANSFORM_TYPE] = conversion.TRANSFORM_JSON
        transform = configurable.transform(params)
        self.assertIsNotNone(transform, "return result for Conversion should not be none")

        params[conversion.TRANSFORM_TYPE] = "unknown"
        transform = configurable.transform(params)
        self.assertIsNone(transform, "return result for Conversion should be none")

    def test_transform_to_xml(self):
        event_in = Event()
        event_in.deviceName = "device1"
        expected_result = (
            "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<Event><Id></Id>"
            "<DeviceName>device1</DeviceName><ProfileName></ProfileName><SourceName></SourceName>"
            "<Origin>0</Origin><Tags></Tags></Event>")
        conv = conversion.Conversion()

        continue_pipeline, result = conv.transform_to_xml(self.ctx, event_in)

        self.assertIsNotNone(result)
        self.assertTrue(continue_pipeline)
        self.assertEqual(expected_result, result)

    def test_transform_to_xml_no_data(self):
        conv = conversion.Conversion()
        continue_pipeline, result = conv.transform_to_xml(self.ctx, None)

        self.assertTrue("No Data Received" in str(result))
        self.assertFalse(continue_pipeline)

    def test_transform_to_xml_not_an_event(self):
        conv = conversion.Conversion()
        continue_pipeline, result = conv.transform_to_xml(self.ctx, "")

        self.assertTrue("unexpected type received" in str(result))
        self.assertFalse(continue_pipeline)

    def test_transform_to_json(self):
        event_in = Event()
        event_in.deviceName = "device1"
        expected_result = (
            '{"id": "", "deviceName": "device1", "profileName": "", '
            '"sourceName": "", "origin": 0, "readings": [], "tags": {}}')
        conv = conversion.Conversion()

        continue_pipeline, result = conv.transform_to_json(self.ctx, event_in)

        self.assertIsNotNone(result)
        self.assertTrue(continue_pipeline)
        self.assertEqual(expected_result, result.decode("utf-8"))

    def test_transform_to_json_no_data(self):
        conv = conversion.Conversion()
        continue_pipeline, result = conv.transform_to_json(self.ctx, None)

        self.assertTrue("No Data Received" in str(result))
        self.assertFalse(continue_pipeline)

    def test_transform_to_json_not_an_event(self):
        conv = conversion.Conversion()
        continue_pipeline, result = conv.transform_to_json(self.ctx, "")

        self.assertTrue("unexpected type received" in str(result))
        self.assertFalse(continue_pipeline)
