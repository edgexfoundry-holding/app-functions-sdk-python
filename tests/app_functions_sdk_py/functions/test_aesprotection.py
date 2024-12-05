#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import unittest
import uuid
from typing import Any
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.bootstrap.interface.secret import SecretProvider, Secrets
from src.app_functions_sdk_py.bootstrap.secret.insecure import InsecureProvider
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions import aesprotection
from src.app_functions_sdk_py.functions.aesprotection import AESProtection
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.functions.context import Context
from src.app_functions_sdk_py.utils.helper import coerce_type

test_secret_name = str(uuid.uuid4())
test_secret_value_key = str(uuid.uuid4())
test_key = ("217A24432646294A404E635266556A586E3272357538782F413F442A472D4B6150645"
            "367566B59703373367639792442264529482B4D6251655468576D5A7134")
test_plain_str = "This is the test string used for testing"


class TestAESProtection(unittest.TestCase):
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
            def __init__(
                    self, name: str, algorithm: str, secret_name:str,
                    secret_value_key: str, expect_none: bool):
                self.name = name
                self.algorithm = algorithm
                self.secret_name = secret_name
                self.secret_value_key = secret_value_key
                self.expect_none = expect_none
        tests = [
            TestData(
                "AES256 - Bad - No secrets ", aesprotection.ENCRYPT_AES256,
                "", "", True),
            TestData(
                "AES256 - good - secrets", aesprotection.ENCRYPT_AES256,
                str(uuid.uuid4()), str(uuid.uuid4()), False),
        ]

        for test_case in tests:
            with self.subTest(msg=test_case.name):
                params = dict()
                if len(test_case.algorithm) > 0:
                    params[aesprotection.ALGORITHM] = test_case.algorithm
                if len(test_case.secret_name) > 0:
                    params[aesprotection.SECRET_NAME] = test_case.secret_name
                if len(test_case.secret_value_key) > 0:
                    params[aesprotection.SECRET_VALUE_KEY] = test_case.secret_value_key

                transform = configurable.encrypt(params)
                self.assertEqual(test_case.expect_none, transform is None)

    def test_aes_protection_encrypt(self):
        test_ctx = MockContext(str(uuid.uuid4()), self.dic, "")

        enc = AESProtection(secret_name=test_secret_name, secret_value_key=test_secret_value_key)

        continue_pipeline, encrypted = enc.encrypt(test_ctx, test_plain_str.encode())
        self.assertTrue(continue_pipeline)

        continue_pipeline, decrypted = enc.decrypt(test_ctx, encrypted)
        self.assertTrue(continue_pipeline)
        byte_data, err = coerce_type(decrypted)
        self.assertIsNone(err)
        self.assertEqual(test_plain_str, byte_data.decode())


class MockSecretProvider(InsecureProvider):
    def __init__(self):
        super().__init__(Any, Any, Any)

    def get_secrets(self, secret_name: str, *secret_keys: str) -> Secrets:
        return Secrets({test_secret_value_key: test_key})


class MockContext(Context):

    def secret_provider(self) -> SecretProvider:
        return MockSecretProvider()
