# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
import time
import unittest

from src.app_functions_sdk_py.contracts.common.constants import API_VERSION
from src.app_functions_sdk_py.contracts.dtos.event import Event
from src.app_functions_sdk_py.contracts.dtos.reading import BaseReading, new_base_reading
from src.app_functions_sdk_py.contracts.dtos.tags import Tags

TestEventId = "TestEvent"
TestDeviceName = "TestDevice"
TestProfileName = "TestProfile"
TestSourceName = "TestSource"
TestOrigin = 1594963842
TestReadingId = "TestReading"
TestResourceName = "TestResource"
TestTags = Tags({"tag1": "value1", "tag2": "value2"})
TestUUID = "7a1707f0-166f-4c4b-bc9d-1d54c74e0137"
TestTag1 = "TestTag1"
TestTag2 = "TestTag2"
TestValueType = "Int8"


class TestEvent(unittest.TestCase):
    def setUp(self):
        self.event = Event(
            id=TestEventId,
            deviceName=TestDeviceName,
            profileName=TestProfileName,
            sourceName=TestSourceName,
            origin=TestOrigin,
            readings=[BaseReading(TestReadingId, time.time_ns(), TestDeviceName, TestResourceName,
                                  TestProfileName, "TestValueType", "TestUnits", "TestValue",
                                  TestTags, objectValue=None, tags=None, mediaType="")],
            tags=TestTags
        )

    def test_event_creation(self):
        self.assertEqual(self.event.id, "TestEvent")
        self.assertEqual(self.event.deviceName, "TestDevice")
        self.assertEqual(self.event.profileName, "TestProfile")
        self.assertEqual(self.event.sourceName, "TestSource")
        self.assertIsInstance(self.event.origin, int)
        self.assertIsInstance(self.event.readings, list)
        self.assertIsInstance(self.event.tags, dict)

    def test_event_to_xml(self):
        reading = new_base_reading(TestProfileName, TestDeviceName, TestSourceName, TestValueType, "123")
        reading.Tags = {"1": TestTag1, "2": TestTag2}
        reading.origin = TestOrigin
        reading.id = TestUUID

        dto = Event()
        dto.apiVersion = API_VERSION
        dto.id = TestUUID
        dto.deviceName = TestDeviceName
        dto.profileName = TestProfileName
        dto.sourceName = TestSourceName
        dto.origin = TestOrigin
        dto.tags = {
            "GatewayID": "Houston-0001",
            "Latitude": "29.630771",
            "Longitude": "-95.377603",
        }
        dto.readings = [reading]

        contains = [
            "<Event>",
            "<Id>7a1707f0-166f-4c4b-bc9d-1d54c74e0137</Id><DeviceName>TestDevice</DeviceName>",
            "<ProfileName>TestProfile</ProfileName><SourceName>TestSource</SourceName>","<Origin>1594963842</Origin>",
            "<Tags><GatewayID>Houston-0001</GatewayID><Latitude>29.630771</Latitude>",
            "<Longitude>-95.377603</Longitude></Tags>",
            "<Readings>",
            "<Id>7a1707f0-166f-4c4b-bc9d-1d54c74e0137</Id><Origin>1594963842</Origin>",
            "<DeviceName>TestDevice</DeviceName><ResourceName>TestSource</ResourceName>",
            "<ProfileName>TestProfile</ProfileName><ValueType>Int8</ValueType>",
            "<Value>123</Value><Units></Units>",
            "<Tags><1>TestTag1</1><2>TestTag2</2></Tags>",
            "</Readings>",
            "</Event>",
        ]
        actual, error = dto.to_xml()
        print(actual)
        self.assertIsNone(error)
        for item in contains:
            self.assertTrue(item in actual, f"Missing item '{item}'")


if __name__ == '__main__':
    unittest.main()
