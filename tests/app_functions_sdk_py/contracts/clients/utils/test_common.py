# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from dataclasses import dataclass

from src.app_functions_sdk_py.contracts.clients.utils.common import url_encode, escape_and_join_path, PathBuilder


class TestUrlEncode(unittest.TestCase):

    def test_urlEncode_withSpecialCharacters_shouldEncodeCorrectly(self):
        self.assertEqual(url_encode("test+string"), "test%2Bstring")
        self.assertEqual(url_encode("test-string"), "test%2Dstring")
        self.assertEqual(url_encode("test.string"), "test%2Estring")
        self.assertEqual(url_encode("test_string"), "test%5Fstring")
        self.assertEqual(url_encode("test~string"), "test%7Estring")


class TestEscapeAndJoinPath(unittest.TestCase):

    def test_escapeAndJoinPath_withMultiplePathVariables(self):
        self.assertEqual(escape_and_join_path("/api", "test+path", "another/path"), "/api/test%2Bpath/another%2Fpath")

    def test_escapeAndJoinPath_withNoPathVariables(self):
        self.assertEqual(escape_and_join_path("/api"), "/api")

    def test_escapeAndJoinPath_withSpecialCharactersInApiRoutePath(self):
        self.assertEqual(escape_and_join_path("/api+route", "test+path"), "/api+route/test%2Bpath")


class TestPathBuild(unittest.TestCase):

    def test_path_build(self):
        @dataclass
        class Test:
            name: str
            enable_name_field_escape: bool
            prefix_path: str
            device_service_name: str
            device_name: str
            expected_path: str

        tests = [
            Test("valid with name field escape",
                 True,
                 "edgex/system-events/core-metadata/device/add",
                 "^[this]+{is}?test:string*#",
                 "this-is_test.string~哈囉世界< >/!#%^*()+,`@$&",
                 "edgex/system-events/core-metadata/device/add/%5E%5Bthis%5D%2B%7Bis%7D%3Ftest:str"
                 "ing%2A%23/this%2Dis%5Ftest%2Estring%7E%E5%93%88%E5%9B%89%E4%B8%96%E7%95%8C%3C%20"
                 "%3E%2F%21%23%25%5E%2A%28%29%2B%2C%60@$&"
                 ),
            Test("valid without name field escape",
                 False,
                 "edgex/system-events/core-metadata/device/add",
                 "device-onvif-camera",
                 "camera-device",
                 "edgex/system-events/core-metadata/device/add/device-onvif-camera/camera-device"
                 )
        ]

        for tt in tests:
            with self.subTest(msg=tt.name):
                self.maxDiff = None
                res = (PathBuilder()
                       .enable_name_field_escape(tt.enable_name_field_escape)
                       .set_path(tt.prefix_path)
                       .set_name_field_path(tt.device_service_name)
                       .set_name_field_path(tt.device_name)
                       .build_path())
                self.assertEqual(tt.expected_path, res)


if __name__ == '__main__':
    unittest.main()
