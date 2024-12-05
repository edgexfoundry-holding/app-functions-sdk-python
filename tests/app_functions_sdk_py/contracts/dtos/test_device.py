# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from datetime import datetime
from src.app_functions_sdk_py.contracts.dtos.device import Device
from src.app_functions_sdk_py.contracts.dtos.autoevent import AutoEvent
from src.app_functions_sdk_py.contracts.dtos.protocolproperties import ProtocolProperties
from src.app_functions_sdk_py.contracts.dtos.tags import Tags


class TestDevice(unittest.TestCase):
    def setUp(self):
        self.timstamp = datetime.now()
        self.auto_event = AutoEvent(interval="30s", onChange=False, sourceName="test_source")
        self.protocol_properties = ProtocolProperties({"TestStrProp": "TestValue",
                                                       "TestIntProp": 8080})
        self.properties = {"property1": "value1", "property2": "value2"}
        self.tags = Tags({"tag1": "value1", "tag2": "value2"})
        self.device = Device(
            created=self.timstamp,
            modified=self.timstamp,
            id="device1",
            name="Device 1",
            parent="parent1",
            description="Test device",
            adminState="LOCKED",
            operatingState="ENABLED",
            labels=["label1", "label2"],
            location="location1",
            serviceName="service1",
            profileName="profile1",
            autoEvents=[self.auto_event],
            protocols={"protocol1": self.protocol_properties},
            tags=self.tags,
            properties=self.properties
        )

    def test_device_creation(self):
        self.assertEqual(self.device.created, self.timstamp)
        self.assertEqual(self.device.modified, self.timstamp)
        self.assertEqual(self.device.id, "device1")
        self.assertEqual(self.device.name, "Device 1")
        self.assertEqual(self.device.parent, "parent1")
        self.assertEqual(self.device.description, "Test device")
        self.assertEqual(self.device.adminState, "LOCKED")
        self.assertEqual(self.device.operatingState, "ENABLED")
        self.assertEqual(self.device.labels, ["label1", "label2"])
        self.assertEqual(self.device.location, "location1")
        self.assertEqual(self.device.serviceName, "service1")
        self.assertEqual(self.device.profileName, "profile1")
        self.assertEqual(self.device.autoEvents, [self.auto_event])
        self.assertEqual(self.device.protocols, {"protocol1": self.protocol_properties})
        self.assertEqual(self.device.tags, self.tags)
        self.assertEqual(self.device.properties, self.properties)


if __name__ == "__main__":
    unittest.main()
