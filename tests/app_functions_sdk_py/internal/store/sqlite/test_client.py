#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import base64
import copy
import sqlite3
import unittest
import uuid

from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.contracts.dtos.store_object import StoredObject
from src.app_functions_sdk_py.internal.store.sqlite.client import new_sqlite_client, Client


class TestSqliteClient(unittest.TestCase):

    def setUp(self):
        self.logger = EdgeXLogger('test_service', DEBUG)
        conn = sqlite3.connect(":memory:")
        self.client = Client(conn, self.logger)

    def test_store(self):
        no_id = StoredObject(
            appServiceKey="test-app-service",
            payload="test".encode(),
            retryCount=2,
            pipelineId="test-pipeline",
            pipelinePosition=1337,
            version="v3",
            correlationID="test"
        )
        no_app_service_key = copy.deepcopy(no_id)
        no_app_service_key.appServiceKey = ""

        no_payload = copy.deepcopy(no_id)
        no_payload.payload = bytes()

        no_version = copy.deepcopy(no_id)
        no_version.version = ""

        class TestData:
            def __init__(self, name: str, to_store: StoredObject, expected_error: bool):
                self.name = name
                self.to_store = to_store
                self.expected_error = expected_error

        tests = [
            TestData(
                "Success, no ID",
                copy.deepcopy(no_id),
                False,
            ),
            TestData(
                "Success, no ID double store",
                copy.deepcopy(no_id),
                False,
            ),
            TestData(
                "Failure, no app service key",
                no_app_service_key,
                True,
            ),
            TestData(
                "Failure, no payload",
                no_payload,
                True,
            ),
            TestData(
                "Failure, no version",
                no_version,
                True,
            ),
        ]
        for test in tests:
            with self.subTest(msg=test.name):
                return_val, err = self.client.store(test.to_store)
                if test.expected_error:
                    self.assertIsNotNone(err)
                    continue

                self.assertIsNone(err)
                self.assertEqual(test.to_store.id, return_val)

                objects, err = self.client.retrieve_from_store(test.to_store.appServiceKey)
                self.assertIsNone(err)
                self.assertTrue(len(objects) == 1)
                self.assertEqual(test.to_store, objects[0])

                err = self.client.remove_from_store(test.to_store)
                self.assertIsNone(err)

    def test_update(self):
        test_object = StoredObject(
            appServiceKey="test-app-service",
            payload="test".encode(),
            retryCount=2,
            pipelineId="test-pipeline",
            pipelinePosition=1337,
            version="v3",
            correlationID="test"
        )

        test_object.id, err = self.client.store(test_object)
        self.assertIsNone(err)

        update_payload = copy.deepcopy(test_object)
        update_payload.payload = "test update".encode(),

        no_payload = copy.deepcopy(test_object)
        no_payload.payload = bytes()

        no_version = copy.deepcopy(test_object)
        no_version.version = ""

        not_exist = copy.deepcopy(test_object)
        not_exist.id = str(uuid.uuid4())

        class TestData:
            def __init__(self, name: str, to_update: StoredObject, expected_error: bool):
                self.name = name
                self.to_update = to_update
                self.expected_error = expected_error

        tests = [
            TestData(
                "Success",
                copy.deepcopy(test_object),
                False,
            ),
            TestData(
                "Success, update payload",
                copy.deepcopy(test_object),
                False,
            ),
            TestData(
                "Failure, no payload",
                no_payload,
                True,
            ),
            TestData(
                "Failure, no version",
                no_version,
                True,
            ),
            TestData(
                "Failure, not exist",
                not_exist,
                True,
            ),
        ]
        for test in tests:
            with self.subTest(msg=test.name):
                err = self.client.update(test.to_update)
                if test.expected_error:
                    self.assertIsNotNone(err)
                    continue
                self.assertIsNone(err)

                objects, err = self.client.retrieve_from_store(test.to_update.appServiceKey)
                self.assertIsNone(err)
                self.assertTrue(len(objects) == 1)
                self.assertEqual(test.to_update, objects[0])
