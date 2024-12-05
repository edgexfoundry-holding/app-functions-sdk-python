# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from src.app_functions_sdk_py.contracts.dtos.deviceresource import DeviceResource


class TestDeviceResource(unittest.TestCase):
    def setUp(self):
        self.device_resource = DeviceResource(
            name="TestDeviceResource",
            description="This is a test device resource",
            isHidden=False,
            tags={"TestTag": "TestValue"},
            properties=["Property1", "Property2"],
            attributes=["Attribute1", "Attribute2"]
        )

    def test_device_resource_creation(self):
        self.assertEqual(self.device_resource.name, "TestDeviceResource")
        self.assertEqual(self.device_resource.description, "This is a test device resource")
        self.assertFalse(self.device_resource.isHidden)
        self.assertEqual(self.device_resource.tags, {"TestTag": "TestValue"})
        self.assertEqual(self.device_resource.properties, ["Property1", "Property2"])
        self.assertEqual(self.device_resource.attributes, ["Attribute1", "Attribute2"])

    def test_device_resource_str(self):
        expected_str = ("DeviceResource(name='TestDeviceResource', description='This is a test "
                        "device resource', isHidden=False, properties=['Property1',"
                        " 'Property2'], attributes=['Attribute1', 'Attribute2'],"
                        " tags={'TestTag': 'TestValue'})")
        self.assertEqual(str(self.device_resource), expected_str)


if __name__ == '__main__':
    unittest.main()
