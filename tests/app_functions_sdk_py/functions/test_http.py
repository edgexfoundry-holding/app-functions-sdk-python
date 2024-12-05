# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
import threading
import unittest
import uuid
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.contracts.clients.utils.request import HTTPMethod
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.functions.context import Context
from src.app_functions_sdk_py.functions.http import (EXPORT_METHOD_POST, EXPORT_METHOD_PUT,
                                                     EXPORT_METHOD, URL, MIME_TYPE,
                                                     PERSIST_ON_ERROR, HEADER_NAME, SECRET_NAME,
                                                     SECRET_VALUE_KEY, HTTP_REQUEST_HEADERS,
                                                     CONTINUE_ON_SEND_ERROR, RETURN_INPUT_DATA,
                                                     new_http_sender)

msgStr = "test message"
path = "/some-path/foo"
badPath = "/some-path/bad"
formatPath = "/some-path/{test}"
badFormatPath = "/some-path/{test}/{test2}"


class MockServer:
    def __init__(self):
        self.server_thread = None

    def start(self) -> HTTPServer:
        def handler_factory(*args, **kwargs):
            class MockRequestHandler(BaseHTTPRequestHandler):
                def do_POST(self):
                    self.do_request()

                def do_PUT(self):
                    self.do_request()

                def do_request(self):
                    content_len = int(self.headers.get('content-length'))
                    self.rfile.read(content_len)
                    if self.path == badPath:
                        self.send_response(404)
                    else:
                        self.send_response(204)
                    self.end_headers()

            return MockRequestHandler(*args, **kwargs)

        server = HTTPServer(('localhost', 0), partial(handler_factory))
        self.server_thread = threading.Thread(target=server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        return server


class TestHttp(unittest.TestCase):
    def setUp(self):
        self.mock_server = MockServer()
        self.test_mock_server = self.mock_server.start()
        self.logger = EdgeXLogger('test_service', DEBUG)
        self.dic = Container()
        self.dic.update({
            LoggingClientInterfaceName: lambda get: self.logger
        })
        self.ctx = Context(str(uuid.uuid4()), self.dic, "")

    def test_http_export_configurable(self):
        configurable = Configurable(logger=self.ctx.logger(), sp=Mock())

        test_url = "http://url"
        test_mime_type = "application/json"
        test_persist_on_error = "false"
        test_bad_persist_on_error = "bogus"
        test_continue_on_send_error = "True"
        test_bad_continue_on_send_error = "bogus"
        test_return_input_data = "True"
        test_bad_return_input_data = "bogus"

        test_header_name = "My-Header"
        test_secret_name = "my-secret"
        test_secret_value_key = "header"

        test_http_request_headers = """{
            "Connection": "keep-alive",
            "From": "[user@example.com](mailto:user@example.com)"
          }"""

        test_bad_http_request_headers = """{
            "Connection": "keep-alive",
            "From":
          """

        class TestData:
            def __init__(
                    self,
                    name: str, method: str, url: str, mime_type: str,
                    persist_on_error: str, continue_on_send_error: str,
                    return_input_data: str, header_name: str, secret_name: str,
                    secret_value_key: str, http_request_headers: str,
                    expect_valid: bool):
                self.name = name
                self.method = method
                self.url = url
                self.mime_type = mime_type
                self.persist_on_error = persist_on_error
                self.continue_on_send_error = continue_on_send_error
                self.return_input_data = return_input_data
                self.header_name = header_name
                self.secret_name = secret_name
                self.secret_value_key = secret_value_key
                self.http_request_headers = http_request_headers
                self.expect_valid = expect_valid

        tests = [
            TestData("Valid Post - ony required params", EXPORT_METHOD_POST, test_url, test_mime_type, None, None, None, None, None, None, None, True),
            TestData("Valid Post - w/o secrets", HTTPMethod.POST.value, test_url, test_mime_type, test_persist_on_error, None, None, None, None, None, None, True),
            TestData("Valid Post - with secrets", EXPORT_METHOD_POST, test_url, test_mime_type, None, None, None, test_header_name, test_secret_name, test_secret_value_key, None, True),
            TestData("Valid Post - with http requet headers", EXPORT_METHOD_POST, test_url, test_mime_type, None, None, None, None, None, None, test_http_request_headers, True),
            TestData("Valid Post - with all params", EXPORT_METHOD_POST, test_url, test_mime_type, test_persist_on_error, test_continue_on_send_error, test_return_input_data, test_header_name, test_secret_name, test_secret_value_key, test_http_request_headers, True),
            TestData("Invalid Post - no url", EXPORT_METHOD_POST, None, test_mime_type, None, None, None, None, None, None, None, False),
            TestData("Invalid Post - no mimeType", EXPORT_METHOD_POST, test_url, None, None, None, None, None, None, None, None, False),
            TestData("Invalid Post - bad persistOnError", EXPORT_METHOD_POST, test_url, test_mime_type, test_bad_persist_on_error, None, None, None, None, None, None, False),
            TestData("Invalid Post - missing headerName", EXPORT_METHOD_POST, test_url, test_mime_type, test_persist_on_error, None, None, None, test_secret_name, test_secret_value_key, None, False),
            TestData("Invalid Post - missing secretName", EXPORT_METHOD_POST, test_url, test_mime_type, test_persist_on_error, None, None, test_header_name, None, test_secret_value_key, None, False),
            TestData("Invalid Post - missing secretValueKey", EXPORT_METHOD_POST, test_url, test_mime_type, test_persist_on_error, None, None, test_header_name, test_secret_name, None, None, False),
            TestData("Invalid Post - unmarshal error for http requet headers", EXPORT_METHOD_POST, test_url, test_mime_type, None, None, None, None, None, None, test_bad_http_request_headers, False),
            TestData("Valid Put - ony required params", EXPORT_METHOD_PUT, test_url, test_mime_type, None, None, None, None, None, None, None, True),
            TestData("Valid Put - w/o secrets", EXPORT_METHOD_PUT, test_url, test_mime_type, test_persist_on_error, None, None, None, None, None, None, True),
            TestData("Valid Put - with secrets", HTTPMethod.PUT.value, test_url, test_mime_type, None, None, None, test_header_name, test_secret_name, test_secret_value_key, None, True),
            TestData("Valid Put - with http request headers", EXPORT_METHOD_PUT, test_url, test_mime_type, None, None, None, None, None, None, test_http_request_headers, True),
            TestData("Valid Put - with all params", EXPORT_METHOD_PUT, test_url, test_mime_type, test_persist_on_error, None, None, test_header_name, test_secret_name, test_secret_value_key, test_http_request_headers, True),
            TestData("Invalid Put - no url", EXPORT_METHOD_PUT, None, test_mime_type, None, None, None, None, None, None, None, False),
            TestData("Invalid Put - no mimeType", EXPORT_METHOD_PUT, test_url, None, None, None, None, None, None, None, None, False),
            TestData("Invalid Put - bad persistOnError", EXPORT_METHOD_PUT, test_url, test_mime_type, test_bad_persist_on_error, None, None, None, None, None, None, False),
            TestData("Invalid Put - bad continueOnSendError", EXPORT_METHOD_PUT, test_url, test_mime_type, None, test_bad_continue_on_send_error, None, None, None, None, None, False),
            TestData("Invalid Put - bad returnInputData", EXPORT_METHOD_PUT, test_url, test_mime_type, None, None, test_bad_return_input_data, None, None, None, None, False),
            TestData("Invalid Put - missing headerName", EXPORT_METHOD_PUT, test_url, test_mime_type, test_persist_on_error, None, None, None, test_secret_name, test_secret_value_key, None, False),
            TestData("Invalid Put - missing secretName", EXPORT_METHOD_PUT, test_url, test_mime_type, test_persist_on_error, None, None, test_header_name, None, test_secret_value_key, None, False),
            TestData("Invalid Put - missing secretValueKey", EXPORT_METHOD_PUT, test_url, test_mime_type, test_persist_on_error, None, None, test_header_name, test_secret_name, None, None, False),
            TestData("Invalid Put - unmarshal error for http requet headers", EXPORT_METHOD_PUT, test_url, test_mime_type, None, None, None, None, None, None, test_bad_http_request_headers, False),
        ]

        for test in tests:
            with self.subTest(msg=test.name):
                params = {EXPORT_METHOD: test.method}
                if test.url is not None:
                    params[URL] = test.url

                if test.mime_type is not None:
                    params[MIME_TYPE] = test.mime_type

                if test.persist_on_error is not None:
                    params[PERSIST_ON_ERROR] = test.persist_on_error

                if test.continue_on_send_error is not None:
                    params[CONTINUE_ON_SEND_ERROR] = test.continue_on_send_error

                if test.return_input_data is not None:
                    params[RETURN_INPUT_DATA] = test.return_input_data

                if test.header_name is not None:
                    params[HEADER_NAME] = test.header_name

                if test.secret_name is not None:
                    params[SECRET_NAME] = test.secret_name

                if test.secret_value_key is not None:
                    params[SECRET_VALUE_KEY] = test.secret_value_key

                if test.http_request_headers is not None:
                    params[HTTP_REQUEST_HEADERS] = test.http_request_headers

                transform = configurable.http_export(params)
                self.assertEqual(test.expect_valid, transform is not None)

    def test_http_post_put(self):
        class TestData:
            def __init__(
                    self,
                    name: str, path: str,
                    persist_on_error: bool, retry_data_set: bool,
                    return_input_data: bool, continue_on_send_error: bool,
                    expected_continue_executing: bool, expected_method: str):
                self.name = name
                self.path = path
                self.persist_on_error = persist_on_error
                self.retry_data_set = retry_data_set
                self.return_input_data = return_input_data
                self.continue_on_send_error = continue_on_send_error
                self.expected_continue_executing = expected_continue_executing
                self.expected_method = expected_method

        tests = [
            TestData("Successful POST", path, True, False, False, False, True, HTTPMethod.POST.value),
            TestData("Successful POST Format", formatPath, True, False, False, False, True, HTTPMethod.POST.value),
            TestData("Successful PUT", path, False, False, False, False, True, HTTPMethod.PUT.value),
            TestData("Successful PUT Format", formatPath, False, False, False, False, True, HTTPMethod.PUT.value),
            TestData("Failed POST no persist", badPath, False, False, False, False, False, HTTPMethod.POST.value),
            TestData("Failed POST continue on error", badPath, False, False, True, True, True, HTTPMethod.POST.value),
            TestData("Failed POST with persist", badPath, True, True, False, False, False, HTTPMethod.POST.value),
            TestData("Failed POST with PersistOnFail", path, True, False, True, True, False, ""),
            TestData("Failed PUT no persist", badPath, False, False, False, False, False, HTTPMethod.PUT.value),
            TestData("Failed PUT with persist", badPath, True, True, False, False, False, HTTPMethod.PUT.value),
            TestData("Successful return inputData", path, False, False, True, False, True, HTTPMethod.POST.value),
            TestData("Failed with persist and returnInputData", badPath, True, True, True, False, False, HTTPMethod.PUT.value),
            TestData("Failed continueOnSendError w/o returnInputData", path, False, False, False, True, False, ""),
            TestData("Failed continueOnSendError with PersistOnFail", path, True, False, True, True, False, ""),
            # PUT is the default, do not think this is worth adding another value to test struct to support testing both
            TestData("Failed PUT with missed replacement", badFormatPath, True, False, True, True, False, ""),
        ]

        for test in tests:
            with self.subTest(msg=test.name):
                self.ctx.add_value("test", "foo")
                self.ctx.set_retry_data(None)
                sender = new_http_sender(f"http://{self.test_mock_server.server_address[0]}:{self.test_mock_server.server_address[1]}"+test.path, "", test.persist_on_error)
                sender.return_input_data = test.return_input_data
                sender.continue_on_send_error = test.continue_on_send_error

                if test.expected_method == HTTPMethod.POST.value:
                    continue_executing, result_data = sender.http_post(self.ctx, msgStr)
                else:
                    continue_executing, result_data = sender.http_put(self.ctx, msgStr)

                self.assertEqual(test.expected_continue_executing, continue_executing)

                if test.expected_continue_executing:
                    if test.return_input_data:
                        self.assertEqual(msgStr, result_data)
                    else:
                        self.assertNotEqual(msgStr, result_data)

                self.assertEqual(test.retry_data_set, self.ctx.retry_data() is not None)
                self.ctx.remove_value("test")
