#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import sqlite3
import unittest
import uuid
from typing import Any, Tuple

from app_functions_sdk_py.contracts.common.constants import CONTENT_TYPE_JSON
from app_functions_sdk_py.functions.context import Context
from src.app_functions_sdk_py.bootstrap.container.store import StoreClientInterfaceName, store_client_from
from src.app_functions_sdk_py.functions.http import new_http_sender
from src.app_functions_sdk_py.internal.store.sqlite.client import Client
from src.app_functions_sdk_py.bootstrap.container.configuration import ConfigurationName
from src.app_functions_sdk_py.contracts.dtos.store_object import new_stored_object
from src.app_functions_sdk_py.internal.common.config import StoreAndForwardInfo
from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.internal.common.config import ConfigurationStruct, WritableInfo
from src.app_functions_sdk_py.contracts import errors
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.interfaces import AppFunctionContext, AppFunction, FunctionPipeline
from src.app_functions_sdk_py.internal.runtime import FunctionsPipelineRuntime

SERVICE_KEY = "AppService-UnitTest"


class TestStoreForward(unittest.TestCase):

    def setUp(self):
        self.logger = EdgeXLogger('test_service', DEBUG)
        config = ConfigurationStruct(
            Writable=WritableInfo(
                LogLevel="DEBUG",
                StoreAndForward=StoreAndForwardInfo(Enabled=True, MaxRetryCount=10)
            )
        )
        conn = sqlite3.connect(":memory:")
        client = Client(conn, self.logger)
        self.dic = Container()
        self.dic.update({
            LoggingClientInterfaceName: lambda get: self.logger,
            ConfigurationName: lambda get: config,
            StoreClientInterfaceName: lambda get: client,
        })

    def test_process_retry_items(self):
        self.target_transform_was_called = False
        expected_payload = "This is a sample payload"
        context_data = {"x": "y"}

        def transform_pass_thru(_: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
            return True, data

        def success_transform(app_context: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
            self.target_transform_was_called = True

            self.assertTrue(isinstance(data, bytes), "Expected []byte payload")
            self.assertEqual(expected_payload, data.decode())
            self.assertEqual(context_data, app_context.get_values())
            return False, None

        def failure_transform(app_context: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
            self.target_transform_was_called = True
            self.assertEqual(context_data, app_context.get_values())
            return False, errors.new_common_edgex(errors.ErrKind.SERVER_ERROR, "transform failed")

        class TestData:
            def __init__(self, name: str, target_transform: AppFunction, target_transform_was_called: bool,
                         expected_payload: str, retry_count: int, expected_retry_count: int,
                         remove_count: int, bad_version: bool, context_data: dict, use_per_topic: bool):
                self.name = name
                self.target_transform = target_transform
                self.target_transform_was_called = target_transform_was_called
                self.expected_payload = expected_payload
                self.retry_count = retry_count
                self.expected_retry_count = expected_retry_count
                self.remove_count = remove_count
                self.bad_version = bad_version
                self.context_data = context_data
                self.use_per_topic = use_per_topic

        tests = [
            TestData("Happy Path - Default", success_transform, True, expected_payload, 0, 0, 1, False, context_data,
                     False),
            TestData("RetryCount Increased - Default", failure_transform, True, expected_payload, 4, 5, 0, False,
                     context_data, False),
            TestData("Max Retries - Default", failure_transform, True, expected_payload, 9, 9, 1, False, context_data,
                     False),
            TestData("Bad Version - Default", success_transform, False, expected_payload, 0, 0, 1, True, context_data,
                     False),
            TestData("Happy Path - Per Topics", success_transform, True, expected_payload, 0, 0, 1, False, context_data,
                     True),
            TestData("RetryCount Increased - Per Topics", failure_transform, True, expected_payload, 4, 5, 0, False,
                     context_data, True),
            TestData("Max Retries - Per Topics", failure_transform, True, expected_payload, 9, 9, 1, False,
                     context_data, True),
            TestData("Bad Version - Per Topics", success_transform, False, expected_payload, 0, 0, 1, True,
                     context_data, True),
        ]

        for test in tests:
            with self.subTest(msg=test.name):
                self.target_transform_was_called = False
                runtime = FunctionsPipelineRuntime(SERVICE_KEY, self.logger, self.dic)

                if test.use_per_topic:
                    err = runtime.add_function_pipeline("per-topic", ["#"], transform_pass_thru, transform_pass_thru,
                                                        test.target_transform)
                    self.assertIsNone(err)
                    pipeline = runtime.get_pipeline_by_id("per-topic")
                    self.assertIsNotNone(pipeline)
                else:
                    runtime.set_default_functions_pipeline(transform_pass_thru, transform_pass_thru,
                                                           test.target_transform)
                    pipeline = runtime.get_default_pipeline()
                    self.assertIsNotNone(pipeline)

                version = pipeline.hash
                if test.bad_version:
                    version = "some bad version"

                stored_object = new_stored_object("dummy", expected_payload.encode(), pipeline.id, 2, version,
                                                  context_data)
                stored_object.retryCount = test.retry_count

                removes, updates = runtime.store_forward.process_retry_items([stored_object])
                self.assertEqual(test.target_transform_was_called, self.target_transform_was_called,
                                 "Target transform not called")
                if test.retry_count != test.expected_retry_count:
                    if self.assertTrue(len(updates) > 0, "Remove count not as expected"):
                        self.assertEqual(test.expected_retry_count, updates[0].RetryCount,
                                         "Retry Count not as expected")

                self.assertEqual(test.remove_count, len(removes), "Remove count not as expected")

    def test_store_and_forward_retry(self):
        payload = "My Payload".encode()

        http_post = new_http_sender("http://nowhere", "", True).http_post

        def success_transform(app_context: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
            return False, None

        def transform_pass_thru(app_context: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
            return True, data

        class TestData:
            def __init__(self, name: str, target_transform: AppFunction,
                         retry_count: int, expected_retry_count: int,
                         expected_object_count: int, use_per_topic: bool):
                self.name = name
                self.target_transform = target_transform
                self.retry_count = retry_count
                self.expected_retry_count = expected_retry_count
                self.expected_object_count = expected_object_count
                self.use_per_topic = use_per_topic

        tests = [
            TestData("RetryCount Increased - Default", http_post, 1, 2, 1, False),
            TestData("Max Retries - Default", http_post, 9, 0, 0, False),
            TestData("Retry Success - Default", success_transform, 1, 0, 0, False),
            TestData("RetryCount Increased - Per Topics", http_post, 1, 2, 1, True),
            TestData("Max Retries - Per Topics", http_post, 9, 0, 0, True),
            TestData("Retry Success - Per Topics", success_transform, 1, 0, 0, True),
        ]

        for test in tests:
            with self.subTest(msg=test.name):
                runtime = FunctionsPipelineRuntime(SERVICE_KEY, self.logger, self.dic)
                runtime.store_forward.data_count.inc(1)

                if test.use_per_topic:
                    err = runtime.add_function_pipeline("per-topic", ["#"], transform_pass_thru, test.target_transform)
                    self.assertIsNone(err)
                    pipeline = runtime.get_pipeline_by_id("per-topic")
                    self.assertIsNotNone(pipeline)
                else:
                    runtime.set_default_functions_pipeline(transform_pass_thru, test.target_transform)
                    pipeline = runtime.get_default_pipeline()
                    self.assertIsNotNone(pipeline)

                obj = new_stored_object(SERVICE_KEY, payload, pipeline.id, 1, pipeline.hash, {})
                obj.correlationID = "CorrelationID"
                obj.retryCount = test.retry_count

                store_client = store_client_from(self.dic.get)
                store_client.store(obj)

                # Target of this test
                runtime.store_forward.retry_stored_data(SERVICE_KEY)

                objects, err = store_client.retrieve_from_store(SERVICE_KEY)
                self.assertIsNone(err)
                self.assertEqual(len(objects), runtime.store_forward.data_count.get_count())

                if self.assertEqual(test.expected_object_count, len(objects)) and test.expected_object_count > 0:
                    self.assertEqual(test.expected_retry_count, objects[0].retryCount)
                    self.assertEqual(SERVICE_KEY, objects[0].appServiceKey, "AppServiceKey not as expected")
                    self.assertEqual(obj.correlationID, objects[0].correlationID, "CorrelationID not as expected")

                err = store_client.remove_from_store(obj)
                self.assertIsNone(err)

    def test_store_for_later_retry(self):
        payload = "My Payload".encode()
        pipeline = FunctionPipeline(
            pipelineid="pipeline.Id",
            topics=[]
        )
        ctx = Context(str(uuid.uuid4()), self.dic, CONTENT_TYPE_JSON)
        runtime = FunctionsPipelineRuntime(SERVICE_KEY, None, self.dic)
        self.assertEqual(0, runtime.store_forward.data_count.get_count())

        runtime.store_forward.store_for_later_retry(payload, ctx, pipeline, 0)

        self.assertEqual(1, runtime.store_forward.data_count.get_count())

    def test_trigger_retry(self):
        ctx = Context(str(uuid.uuid4()), self.dic, CONTENT_TYPE_JSON)

        def transform_pass_thru(app_context: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
            return True, data

        runtime = FunctionsPipelineRuntime(SERVICE_KEY, None, self.dic)
        err = runtime.add_function_pipeline("test-pipeline-id", ["#"], transform_pass_thru)
        self.assertIsNone(err)
        pipeline = runtime.get_pipeline_by_id("test-pipeline-id")

        runtime.store_forward.store_for_later_retry("dummy".encode(), ctx, pipeline, 0)
        self.assertEqual(runtime.store_forward.data_count.get_count(), 1)

        runtime.store_forward.trigger_retry()
        self.assertEqual(runtime.store_forward.data_count.get_count(), 0)
