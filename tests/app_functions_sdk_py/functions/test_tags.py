#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import unittest
import uuid
from typing import Any
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.functions import tags
from src.app_functions_sdk_py.contracts.dtos.event import Event, new_event
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.context import Context


class TestTags(unittest.TestCase):

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
            def __init__(
                    self, name: str, param_name: str,
                    tags_spec: str, expect_none: bool
            ):
                self.name = name
                self.param_name = param_name
                self.tags_spec = tags_spec
                self.expect_none = expect_none

        tests = [
            TestData("Good - non-empty list", tags.TAGS,
                     "GatewayId:HoustonStore000123,Latitude:29.630771,Longitude:-95.377603", False),
            TestData("Good - empty list", tags.TAGS, "", False),
            TestData("Bad - No : separator", tags.TAGS,
                     "GatewayId HoustonStore000123, Latitude:29.630771,Longitude:-95.377603", True),
            TestData("Bad - Missing value", tags.TAGS, "GatewayId:,Latitude:29.630771,Longitude:-95.377603", True),
            TestData("Bad - Missing key", tags.TAGS, "GatewayId:HoustonStore000123,:29.630771,Longitude:-95.377603",
                     True),
            TestData("Bad - Missing key & value", tags.TAGS, ":,:,:", True),
            TestData("Bad - No Tags parameter", "NotTags", ":,:,:", True),
        ]

        for test_case in tests:
            with self.subTest(msg=test_case.name):
                params = dict()
                params[test_case.param_name] = test_case.tags_spec

                transform = configurable.add_tags(params)
                self.assertEqual(test_case.expect_none, transform is None)

    def test_add_tags(self):
        coordinates = {
            "Latitude": 29.630771,
            "Longitude": -95.377603,
        }

        tags_to_add = {
            "GatewayId": "HoustonStore000123",
            "Coordinates": coordinates,
        }

        all_tags_added = {
            "Tag1": 1,
            "Tag2": 2,
            "GatewayId": "HoustonStore000123",
            "Coordinates": coordinates,
        }

        event_without_tags = new_event("profile1", "dev1", "source1")
        event_with_existing_tags = new_event("profile1", "dev1", "source2")
        event_with_existing_tags.tags = {
            "Tag1": 1,
            "Tag2": 2,
        }

        class TestData:
            def __init__(
                    self, name: str, function_input: Any,
                    event_tags: dict, expected: dict,
                    error_expected: bool, error_contains: str,
            ):
                self.name = name
                self.function_input = function_input
                self.event_tags = event_tags
                self.expected = expected
                self.error_expected = error_expected
                self.error_contains = error_contains

        tests = [
            TestData("Happy path - no existing Event tags", event_without_tags, tags_to_add, tags_to_add, False, ""),
            TestData("Happy path - Event has existing tags", event_with_existing_tags, tags_to_add, all_tags_added,
                     False, ""),
            TestData("Happy path - No tags added", event_with_existing_tags, dict(), event_with_existing_tags.tags,
                     False, ""),
            TestData("Error - No data", None, dict(), dict(), True, "No Data Received"),
            TestData("Error - Input not event", "Not an Event", dict(), dict(), True, "type received is not an Event")
        ]

        for test_case in tests:
            with self.subTest():
                target = tags.new_tags(test_case.event_tags)

                if test_case.function_input is not None:
                    continue_pipeline, result = target.add_tags(self.ctx, test_case.function_input)
                else:
                    continue_pipeline, result = target.add_tags(self.ctx, None)

                if test_case.error_expected:
                    self.assertIsNotNone(result)
                    self.assertTrue(test_case.error_contains, str(result))
                    self.assertFalse(continue_pipeline)
                else:
                    self.assertTrue(continue_pipeline)
                    self.assertTrue(isinstance(result, Event))
                    self.assertEqual(test_case.expected, result.tags)
