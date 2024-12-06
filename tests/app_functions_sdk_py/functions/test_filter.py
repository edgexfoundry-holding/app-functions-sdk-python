# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
import uuid
from typing import cast
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.contracts.common.constants import VALUE_TYPE_INT32
from src.app_functions_sdk_py.contracts.dtos.reading import BaseReading, new_base_reading
from src.app_functions_sdk_py.contracts.dtos.event import Event, new_event
from src.app_functions_sdk_py.functions.context import Context
from src.app_functions_sdk_py.functions.filters import new_filter_out, new_filter_for, PROFILE_NAMES, FILTER_OUT
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG

profile_name1 = "profile1"
profile_name2 = "profile2"
device_name1 = "device1"
device_name2 = "device2"
source_name1 = "source1"
source_name2 = "source2"
resource1 = "resource1"
resource2 = "resource2"
resource3 = "resource3"
resource10 = "resource10"
resource_regexp = "[a-z]*.1"


class TestData:
    def __init__(self,
                 name: str,
                 filters: list[str],
                 filter_out: bool,
                 event: Event = None,
                 expected_none_result: bool = False,
                 expected_reading_count: int = 0):
        self.name = name
        self.filters = filters
        self.filter_out = filter_out
        self.event = event
        self.expected_none_result = expected_none_result
        self.expected_reading_count = expected_reading_count


def create_event() -> Event:
    return new_event(
        profile_name=profile_name1, device_name=device_name1, source_name=source_name1)


def create_reading(resource_name: str) -> BaseReading:
    return new_base_reading(
        resource_name=resource_name, value_type=VALUE_TYPE_INT32,
        value="123", device_name=device_name1, profile_name=profile_name1)


class TestFilter(unittest.TestCase):
    def setUp(self):
        self.logger = EdgeXLogger('test_service', DEBUG)
        self.dic = Container()
        self.dic.update({
            LoggingClientInterfaceName: lambda get: self.logger
        })
        self.ctx = Context(str(uuid.uuid4()), self.dic, "")

    def test_filter_by_profile_name(self):
        profile1_event = create_event()

        tests = [
            TestData("filter for - no event", [profile_name1], False, None, True),
            TestData("filter for - no filter values", [], False, profile1_event, False),
            TestData("filter for - found", [profile_name1], False, profile1_event, False),
            TestData("filter for - not found", [profile_name2], False, profile1_event, True),
            TestData("filter for - regexp found", ["profile*"], False, profile1_event, False),

            TestData("filter out - no event", [profile_name1], True, None, True),
            TestData("filter out - no filter values", [], True, profile1_event, False),
            TestData("filter out extra param - found", [profile_name1], True, profile1_event, True),
            TestData("filter out - found", [profile_name1], True, profile1_event, True),
            TestData("filter out - not found", [profile_name2], True, profile1_event, False),
            TestData("filter out - regexp not found", ["test*"], True, profile1_event, False),
        ]
        for test in tests:
            with self.subTest(msg=test.name):
                if test.filter_out:
                    event_filter = new_filter_out(test.filters)
                else:
                    event_filter = new_filter_for(test.filters)

                if test.event is None:
                    continue_pipeline, result = event_filter.filter_by_profile_name(self.ctx, None)
                    self.assertTrue("FilterByProfileName: no Event Received" in str(result))
                    self.assertFalse(continue_pipeline)
                else:
                    expected_continue = not test.expected_none_result
                    continue_pipeline, result = event_filter.filter_by_profile_name(self.ctx, test.event)
                    self.assertEqual(expected_continue, continue_pipeline)
                    self.assertEqual(test.expected_none_result, result is None)
                    if result is not None and test.event is not None:
                        self.assertEqual(test.event, result)

    def test_filter_by_device_name(self):
        device1_event = create_event()

        tests = [
            TestData("filter for - no event", [device_name1], False, None, True),
            TestData("filter for - no filter values", [], False, device1_event, False),
            TestData("filter for - found", [device_name1], False, device1_event, False),
            TestData("filter for - not found", [device_name2], False, device1_event, True),
            TestData("filter for regexp - found", ["device*"], False, device1_event, False),
            TestData("filter for regexp - not found", ["test"], False, device1_event, True),

            TestData("filter out - no event", [device_name1], True, None, True),
            TestData("filter out - no filter values", [], True, device1_event, False),
            TestData("filter out extra param - found", [device_name1], True, device1_event, True),
            TestData("filter out - found", [device_name1], True, device1_event, True),
            TestData("filter out - not found", [device_name2], True, device1_event, False),
            TestData("filter out regexp - found", [device_name1], True, device1_event, True),
            TestData("filter out regexp - not found", ["test"], True, device1_event, False),
        ]

        for test in tests:
            with self.subTest(msg=test.name):
                if test.filter_out:
                    event_filter = new_filter_out(test.filters)
                else:
                    event_filter = new_filter_for(test.filters)

                if test.event is None:
                    continue_pipeline, result = event_filter.filter_by_device_name(self.ctx, None)
                    self.assertTrue("FilterByDeviceName: no Event Received" in str(result))
                    self.assertFalse(continue_pipeline)
                else:
                    expected_continue = not test.expected_none_result
                    continue_pipeline, result = event_filter.filter_by_device_name(self.ctx, test.event)
                    self.assertEqual(expected_continue, continue_pipeline)
                    self.assertEqual(test.expected_none_result, result is None)
                    if result is not None and test.event is not None:
                        self.assertEqual(test.event, result)

    def test_filter_by_source_name(self):
        device1_event = create_event()

        tests = [
            TestData("filter for - no event", [source_name1], False, None, True),
            TestData("filter for - no filter values", [], False, device1_event, False),
            TestData("filter for - found", [source_name1], False, device1_event, False),
            TestData("filter for - not found", [source_name2], False, device1_event, True),
            TestData("filter for regexp - found", ["source*"], False, device1_event, False),
            TestData("filter for regexp - not found", ["test"], False, device1_event, True),

            TestData("filter out - no event", [source_name1], True, None, True),
            TestData("filter out - no filter values", [], True, device1_event, False),
            TestData("filter out extra param - found", [source_name1], True, device1_event, True),
            TestData("filter out - found", [source_name1], True, device1_event, True),
            TestData("filter out - not found", [source_name2], True, device1_event, False),
            TestData("filter out regexp - found", ["source*"], True, device1_event, True),
            TestData("filter out regexp - not found", ["test"], True, device1_event, False),
        ]

        for test in tests:
            with self.subTest(msg=test.name):
                if test.filter_out:
                    event_filter = new_filter_out(test.filters)
                else:
                    event_filter = new_filter_for(test.filters)

                if test.event is None:
                    continue_pipeline, result = event_filter.filter_by_source_name(self.ctx, None)
                    self.assertTrue("FilterBySourceName: no Event Received" in str(result))
                    self.assertFalse(continue_pipeline)
                else:
                    expected_continue = not test.expected_none_result
                    continue_pipeline, result = event_filter.filter_by_source_name(self.ctx, test.event)
                    self.assertEqual(expected_continue, continue_pipeline)
                    self.assertEqual(test.expected_none_result, result is None)
                    if result is not None and test.event is not None:
                        self.assertEqual(test.event, result)

    def test_filter_by_resource_name(self):
        # event with a reading for resource 1
        resource1_event = create_event()
        resource1_event.readings.append(create_reading(resource1))

        # event with a reading for resource 2
        resource2_event = create_event()
        resource2_event.readings.append(create_reading(resource2))

        # event with a reading for resource 3
        resource3_event = create_event()
        resource3_event.readings.append(create_reading(resource3))

        # event with readings for resource 1 & 2
        two_resource_event = create_event()
        two_resource_event.readings.append(create_reading(resource1))
        two_resource_event.readings.append(create_reading(resource2))

        # event with readings for resource 1 & 2 & 10
        three_resource_event = create_event()
        three_resource_event.readings.append(create_reading(resource1))
        three_resource_event.readings.append(create_reading(resource2))
        three_resource_event.readings.append(create_reading(resource10))

        tests = [
            TestData("filter for - no event", [resource1], False, None, True, 0),
            TestData("filter for 0 in R1 - no change", [], False, resource1_event, False, 1),
            TestData("filter for 1 in R1 - 1 of 1 found", [resource1], False, resource1_event, False, 1),
            TestData("filter for 1 in 2R - 1 of 2 found", [resource1], False, two_resource_event, False, 1),
            TestData("filter for 2 in R1 - 1 of 1 found", [resource1, resource2], False, resource1_event, False, 1),
            TestData("filter for 2 in 2R - 2 of 2 found", [resource1, resource2], False, two_resource_event, False, 2),
            TestData("filter for 2 in R2 - 1 of 2 found", [resource1, resource2], False, resource2_event, False, 1),
            TestData("filter for 1 in R2 - not found", [resource1], False, resource2_event, True, 0),
            TestData("filter for 1 in 3R via regexp - 2 found", [resource_regexp], False, three_resource_event, False, 2),

            TestData("filter out - no event", [resource1], True, None, True, 0),
            TestData("filter out extra param - found", [resource1], True, resource1_event, True, 0),
            TestData("filter out 0 in R1 - no change", [], True, resource1_event, False, 1),
            TestData("filter out 1 in R1 - 1 of 1 found", [resource1], True, resource1_event, True, 0),
            TestData("filter out 1 in R2 - not found", [resource1], True, resource2_event, False, 1),
            TestData("filter out 1 in 2R - 1 of 2 found", [resource1], True, two_resource_event, False, 1),
            TestData("filter out 2 in R1 - 1 of 1 found", [resource1, resource2], True, resource1_event, True, 0),
            TestData("filter out 2 in R2 - 1 of 1 found", [resource1, resource2], True, resource2_event, True, 0),
            TestData("filter out 2 in 2R - 2 of 2 found", [resource1, resource2], True, two_resource_event, True, 0),
            TestData("filter out 2 in R3 - not found", [resource1, resource2], True, resource3_event, False, 1),
            TestData("filter out 2 in 3R via regexp - 1 found", [resource_regexp], True, three_resource_event, False, 1),
        ]

        for test in tests:
            with self.subTest(msg=test.name):
                if test.filter_out:
                    event_filter = new_filter_out(test.filters)
                else:
                    event_filter = new_filter_for(test.filters)

                if test.event is None:
                    continue_pipeline, result = event_filter.filter_by_resource_name(self.ctx, None)
                    self.assertTrue("FilterByResourceName: no Event Received" in str(result))
                    self.assertFalse(continue_pipeline)
                else:
                    expected_continue = not test.expected_none_result
                    continue_pipeline, result = event_filter.filter_by_resource_name(self.ctx, test.event)
                    self.assertEqual(expected_continue, continue_pipeline)
                    self.assertEqual(test.expected_none_result, result is None)
                    if result is not None:
                        self.assertTrue(isinstance(result, Event))
                        event = cast(Event, result)
                        self.assertEqual(device_name1, event.deviceName)
                        self.assertEqual(profile_name1, event.profileName)
                        self.assertEqual(source_name1, event.sourceName)
                        self.assertEqual(test.expected_reading_count, len(event.readings))

    def test_configurable(self):
        configurable = Configurable(logger=self.ctx.logger(), sp=Mock())

        class TestData:
            def __init__(self, name: str, params: dict, expect_none: bool):
                self.name = name
                self.params = params
                self.expect_none = expect_none

        tests = [
            TestData("Non Existent Parameters", {"": ""}, True),
            TestData("Empty Parameters", {PROFILE_NAMES: ""}, False),
            TestData("Valid Parameters", {PROFILE_NAMES: "GS1-AC-Drive, GS0-DC-Drive, GSX-ACDC-Drive"}, False),
            TestData("Empty FilterOut Parameters",
                     {PROFILE_NAMES: "GS1-AC-Drive, GS0-DC-Drive, GSX-ACDC-Drive", FILTER_OUT: ""}, True),
            TestData("Valid FilterOut Parameters",
                     {PROFILE_NAMES: "GS1-AC-Drive, GS0-DC-Drive, GSX-ACDC-Drive", FILTER_OUT: "true"}, False),
        ]
        for tt in tests:
            with self.subTest(msg=tt.name):
                trx = configurable.filter_by_profile_name(tt.params)
                if tt.expect_none:
                    self.assertIsNone(trx, "return result from FilterByProfileName should be nil")
                else:
                    self.assertIsNotNone(trx, "return result from FilterByProfileName should not be nil")

if __name__ == '__main__':
    unittest.main()
