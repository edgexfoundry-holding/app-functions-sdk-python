# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from dataclasses import dataclass

from src.app_functions_sdk_py.configuration import ServiceConfig


class TestServiceConfig(unittest.TestCase):

    def setUp(self):
        self.config = ServiceConfig()

    def test_get_url(self):
        self.config.protocol = "http"
        self.config.host = "localhost"
        self.config.port = 8080
        self.assertEqual(self.config.get_url(), "http://localhost:8080")

    def test_populate_from_url(self):

        @dataclass
        class TestData:
            name: str
            url: str
            expected_type: str
            expected_protocol: str
            expected_host: str
            expected_port: int
            expected_error: str

        tests = [
            TestData("Success, protocol specified", "consul.https://localhost:8080", "consul", "https", "localhost", 8080, ""),
            TestData("Success, protocol not specified", "consul://localhost:8080", "consul", "http", "localhost", 8080, ""),
            TestData("Bad URL format", "not a url\r\n", "", "", "", 0, "the format of Provider URL is incorrect"),
            TestData("Bad Port", "consul.https://localhost:eight", "", "", "", 0, "the port from Provider URL is incorrect"),
            TestData("Missing Type and Protocol spec", "://localhost:800", "", "", "", 0, "the format of Provider URL is incorrect"),
            TestData("Bad Type and Protocol spec", "xyz.consul.http://localhost:800", "", "", "", 0, "the Type and Protocol spec from Provider URL is incorrect"),
        ]

        target = ServiceConfig()

        for test in tests:
            with self.subTest(msg=test.name):
                if test.expected_error:
                    with self.assertRaises(ValueError) as cm:
                        target.populate_from_url(test.url)
                    self.assertIn(test.expected_error, str(cm.exception))
                else:
                    target.populate_from_url(test.url)
                    self.assertEqual(test.expected_type, target.type)
                    self.assertEqual(test.expected_protocol, target.protocol)
                    self.assertEqual(test.expected_host, target.host)
                    self.assertEqual(test.expected_port, target.port)


if __name__ == '__main__':
    unittest.main()
