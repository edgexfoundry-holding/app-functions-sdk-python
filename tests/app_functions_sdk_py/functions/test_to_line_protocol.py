#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import time
import unittest
import uuid
from typing import Optional
from unittest.mock import Mock

import numpy

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.contracts.dtos import metric
from src.app_functions_sdk_py.functions import tags, metrics
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.context import Context


class TestToLineProtocol(unittest.TestCase):
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
            def __init__(self, name: str, params: Optional[dict], expect_none: bool):
                self.name = name
                self.params = params
                self.expect_name = expect_none

        tests = [
            TestData("Valid, empty tags parameter", {tags.TAGS: ""}, False),
            TestData("Valid, some tags", {tags.TAGS: "tag1:value1, tag2:value2"}, False),
            TestData("Invalid, no tags parameter", None, True),
            TestData("Invalid, bad tags", {tags.TAGS: "tag1 = value1, tag2 =value2"}, True),
        ]
        for test in tests:
            with self.subTest(msg=test.name):
                actual = configurable.to_line_protocol(test.params)
                self.assertEqual(test.expect_name, actual is None)

    def test_new_metrics_processor(self):
        actual, err = metrics.new_metrics_processor({})
        self.assertIsNone(err)
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual.additional_tags), 0)

        input_tags = {
            "Tag1": "str1",
            "Tag2": 123,
            "Tag3": 12.34,
        }
        expected_tags = [
            metric.MetricTag(name="Tag1", value="str1"),
            metric.MetricTag(name="Tag2", value="123"),
            metric.MetricTag(name="Tag3", value="12.34"),
        ]

        actual, err = metrics.new_metrics_processor(input_tags)
        self.assertIsNone(err)
        self.assertIsNotNone(actual)
        self.assertEqual(actual.additional_tags, expected_tags)

    def test_metrics_processor_to_line_protocol(self):
        target, err = metrics.new_metrics_processor({"Tag1": "value1"})
        self.assertIsNone(err)
        expected_timestamp = int(time.time_ns() / 1000)
        expected_continue = True
        expected_result = f"UnitTestMetric,ServiceName=UnitTestService,SomeTag=SomeValue,Tag1=value1 int=12i,float=12.35,uint=99u {expected_timestamp}"
        source = metric.Metric(
            name="UnitTestMetric",
            fields=[
                metric.MetricField(
                    name="int",
                    value=12,
                ),
                metric.MetricField(
                    name="float",
                    value=12.35,
                ),
                metric.MetricField(
                    name="uint",
                    value=numpy.uint(99),
                ),
            ],
            tags=[
                metric.MetricTag(
                    name="ServiceName",
                    value="UnitTestService",
                ),
                metric.MetricTag(
                    name="SomeTag",
                    value="SomeValue",
                ),
            ],
            timestamp=expected_timestamp,
        )
        expected_orig_tag_count = len(source.tags)
        actual_continue, actual_result = target.to_line_protocol(self.ctx, source)
        self.assertEqual(expected_continue, actual_continue)
        self.assertEqual(expected_result, actual_result)
