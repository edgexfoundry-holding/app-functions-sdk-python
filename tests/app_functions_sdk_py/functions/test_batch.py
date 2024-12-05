# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
import json
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.contracts.clients.utils.common import convert_any_to_dict
from src.app_functions_sdk_py.contracts.common.constants import (
    VALUE_TYPE_STRING, VALUE_TYPE_FLOAT64)
from src.app_functions_sdk_py.contracts.dtos.event import Event, new_event
from src.app_functions_sdk_py.functions import batch
from src.app_functions_sdk_py.functions.batch import new_batch_by_count, new_batch_by_time_and_count, BatchConfig, \
    new_batch_by_time
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.context import Context, KEY_PIPELINEID

data_to_batch: list[bytes] = [b"Test1", b"Test2", b"Test3"]


class TestBatch(unittest.TestCase):
    def setUp(self):
        self.logger = EdgeXLogger('test_service', DEBUG)
        self.dic = Container()
        self.dic.update({
            LoggingClientInterfaceName: lambda get: self.logger
        })
        self.ctx = Context(str(uuid.uuid4()), self.dic,"")
        self.ctx.add_value(KEY_PIPELINEID, str(uuid.uuid4()))

    def test_configurable_batch_by_count(self):
        configurable = Configurable(logger=self.ctx.logger(), sp=Mock())

        params = dict()
        params[batch.MODE] = batch.BATCH_BY_COUNT
        params[batch.BATCH_THRESHOLD] = "30"
        params[batch.IS_EVENT_DATA] = "true"

        transform = configurable.batch(params)
        self.assertIsNotNone(transform, "return result for BatchByCount should not be nil")

    def test_configurable_batch_by_time(self):
        configurable = Configurable(logger=self.ctx.logger(), sp=Mock())

        params = dict()
        params[batch.MODE] = batch.BATCH_BY_TIME
        params[batch.TIME_INTERVAL] = "10s"
        params[batch.IS_EVENT_DATA] = "false"

        transform = configurable.batch(params)
        self.assertIsNotNone(transform, "return result for BatchByTime should not be nil")

    def test_configurable_batch_by_time_and_count(self):
        configurable = Configurable(logger=self.ctx.logger(), sp=Mock())

        params = dict()
        params[batch.MODE] = batch.BATCH_BY_TIME_COUNT
        params[batch.BATCH_THRESHOLD] = "30"
        params[batch.TIME_INTERVAL] = "10s"

        transform = configurable.batch(params)
        self.assertIsNotNone(transform, "return result for BatchByTimeAndCount should not be nil")

    def test_batch_no_data(self):
        bs = new_batch_by_count(1)
        continue_pipeline, err = bs.batch(self.ctx, None)
        self.assertFalse(continue_pipeline)
        self.assertTrue("No Data Received" in str(err))

    def test_batch_in_count_mode(self):
        bs = new_batch_by_count(3)

        continue_pipeline1, result1 = bs.batch(self.ctx, data_to_batch[0])
        self.assertFalse(continue_pipeline1)
        self.assertIsNone(result1)
        self.assertEqual(len(bs.batch_data.all()), 1, "Should have 1 record")

        continue_pipeline2, result2 = bs.batch(self.ctx, data_to_batch[0])
        self.assertFalse(continue_pipeline2)
        self.assertIsNone(result2)
        self.assertEqual(len(bs.batch_data.all()), 2, "Should have 2 records")

        continue_pipeline3, result3 = bs.batch(self.ctx, data_to_batch[0])
        self.assertTrue(continue_pipeline3)
        self.assertEqual(result3, [b'Test1', b'Test1', b'Test1'])
        self.assertEqual(len(result3), 3, "Should have 3 records")
        self.assertEqual(len(bs.batch_data.all()), 0, "Records should have been cleared")

        continue_pipeline4, result4 = bs.batch(self.ctx, data_to_batch[0])
        self.assertFalse(continue_pipeline4)
        self.assertIsNone(result4)
        self.assertEqual(len(bs.batch_data.all()), 1, "Should have 1 record")

        continue_pipeline5, result5 = bs.batch(self.ctx, data_to_batch[1])
        self.assertFalse(continue_pipeline5)
        self.assertIsNone(result5)
        self.assertEqual(len(bs.batch_data.all()), 2, "Should have 2 records")

        continue_pipeline6, result6 = bs.batch(self.ctx, data_to_batch[2])
        self.assertTrue(continue_pipeline6)
        self.assertEqual(result6, data_to_batch)
        self.assertEqual(len(result6), 3, "Should have 3 records")
        self.assertEqual(len(bs.batch_data.all()), 0, "Records should have been cleared")

    def test_batch_is_event_data(self):
        events: list[Event] = [
            new_event("p1", "d1", "s1"),
            new_event("p1", "d1", "s1"),
            new_event("p1", "d1", "s1"),
        ]
        events[0].add_base_reading("r1", VALUE_TYPE_STRING, "Hello")
        events[1].add_base_reading("r2", VALUE_TYPE_FLOAT64, 89.90)
        events[2].add_binary_reading("r3", b"TestData", "text/plain")

        class TestData:
            def __init__(self, name: str, is_event_data: bool):
                self.name = name
                self.is_event_data = is_event_data

        tests = [
            TestData("Is Events", True),
            TestData("Is Not Events", False)
        ]
        for test in tests:
            with self.subTest(msg=test.name):
                bbc = new_batch_by_count(3)
                bbc.is_event_data = test.is_event_data

                if test.is_event_data:
                    continue_pipeline, result = bbc.batch(self.ctx, events[0])
                    self.assertFalse(continue_pipeline)
                    self.assertIsNone(result)

                    continue_pipeline, result = bbc.batch(self.ctx, events[1])
                    self.assertFalse(continue_pipeline)
                    self.assertIsNone(result)

                    continue_pipeline, result = bbc.batch(self.ctx, events[2])
                    self.assertTrue(continue_pipeline)
                    self.assertIsNotNone(result)

                    self.assertTrue(isinstance(result, list))
                    # change the binaryValue back from base64 str to binary
                    events[2].readings[0].binaryValue = b"TestData"
                    self.assertEqual(events, result)
                else:
                    continue_pipeline, result = bbc.batch(self.ctx, events[0])
                    self.assertFalse(continue_pipeline)
                    self.assertIsNone(result)

                    continue_pipeline, result = bbc.batch(self.ctx, events[1])
                    self.assertFalse(continue_pipeline)
                    self.assertIsNone(result)

                    continue_pipeline, result = bbc.batch(self.ctx, events[2])
                    self.assertTrue(continue_pipeline)
                    self.assertIsNotNone(result)

                    self.assertTrue(isinstance(result, list))
                    expected = list(map(lambda e: json.dumps(convert_any_to_dict(e)).encode('utf-8'), events))
                    self.assertEqual(expected, result)

    def test_batch_in_time_and_count_mode_time_elapsed(self):
        bs, err = new_batch_by_time_and_count("2s", 10)
        self.assertIsNone(err)

        # Key to this test is this call occurs first and will be blocked until
        # batch time interval has elapsed. In the meantime, the other thread have to execute
        # before the batch time interval has elapsed
        with ThreadPoolExecutor() as e:
            e.submit(self.batch_data, bs, data_to_batch[0], True)
            e.submit(self.batch_data, bs, data_to_batch[1], False)
            e.submit(self.batch_data, bs, data_to_batch[2], False)

    def test_batch_in_time_and_count_mode_count_meet(self):
        bs, err = new_batch_by_time_and_count("10s", 3)
        self.assertIsNone(err)

        with ThreadPoolExecutor() as e:
            e.submit(self.batch_data, bs, data_to_batch[0], False)
            e.submit(self.batch_data, bs, data_to_batch[1], False)
            e.submit(self.batch_data, bs, data_to_batch[2], True)

    def test_batch_in_time_mode(self):
        bs, err = new_batch_by_time("3s")
        self.assertIsNone(err)

        with ThreadPoolExecutor() as e:
            e.submit(self.batch_data, bs, data_to_batch[0], True)
            time.sleep(1)
            e.submit(self.batch_data, bs, data_to_batch[1], False)
            e.submit(self.batch_data, bs, data_to_batch[2], False)

    def batch_data(self, bs: BatchConfig, data: Any, expected_continue_pipeline: bool):
        with self.subTest(msg=f"batch {data} and expect continue {expected_continue_pipeline}"):
            continue_pipeline, result = bs.batch(self.ctx, data)
            self.assertEqual(expected_continue_pipeline, continue_pipeline)
            if expected_continue_pipeline:
                self.assertTrue(isinstance(result, list))
                self.assertEqual(data_to_batch, result)
                self.assertEqual(len(bs.batch_data.all()), 0, "Should have 0 records")
            else:
                self.assertIsNone(result)

    def test_batch_merge_on_send(self):
        expected = data_to_batch[0] + data_to_batch[1] + data_to_batch[2]

        bbc = new_batch_by_count(len(data_to_batch))
        bbc.merge_on_send = True

        result = None
        for item in data_to_batch:
            _, result = bbc.batch(self.ctx, item)

        self.assertTrue(isinstance(result, bytes))
        self.assertEqual(expected, result)
