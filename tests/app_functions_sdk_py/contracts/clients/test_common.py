# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json

from src.app_functions_sdk_py.contracts.clients.common import CommonClient
from src.app_functions_sdk_py.contracts.clients.utils.request import HTTPMethod
from src.app_functions_sdk_py.contracts.dtos.common import config, ping, version, base, secret
from src.app_functions_sdk_py.contracts.common import constants


class TestHandler(BaseHTTPRequestHandler):
    def __init__(self, http_method, api_route, expected_response, *args, **kwargs):
        self.http_method = http_method
        self.api_route = api_route
        self.expected_response = expected_response
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self._handle_request(HTTPMethod.GET.value)

    def do_POST(self):
        content_len = int(self.headers.get('content-length'))
        self.rfile.read(content_len)
        self._handle_request(HTTPMethod.POST.value)

    def do_PUT(self):
        content_len = int(self.headers.get('content-length'))
        self.rfile.read(content_len)
        self._handle_request(HTTPMethod.PUT.value)

    def do_DELETE(self):
        self._handle_request(HTTPMethod.DELETE.value)

    def _handle_request(self, method):
        if self.http_method != method or urlparse(self.path).path != self.api_route:
            self.send_response(405 if self.http_method != method else 400)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header(constants.CONTENT_TYPE, constants.CONTENT_TYPE_JSON)
        self.end_headers()
        self.wfile.write(json.dumps(self.expected_response).encode('utf-8'))


def new_test_server(http_method, api_route, expected_response):
    class Handler(TestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(http_method, api_route, expected_response, *args, **kwargs)
    return HTTPServer(('localhost', 0), Handler)


def run_test_server(http_method, api_route, expected_response, client_cls, test_func):
    server = new_test_server(http_method, api_route, expected_response.__dict__)
    server_address = server.server_address
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    client = client_cls(f'http://{server_address[0]}:{server_address[1]}', None)

    try:
        test_func(client)
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()


class TestCommonClient(unittest.TestCase):

    def test_get_config(self):
        expected_response = config.ConfigResponse(config={})
        run_test_server(HTTPMethod.GET.value, constants.API_CONFIG_ROUTE, expected_response, CommonClient,
                        lambda client: self.assertEqual(client.configuration({}).__dict__, expected_response.__dict__))

    def test_ping(self):
        expected_response = ping.PingResponse()
        run_test_server(HTTPMethod.GET.value, constants.API_PING_ROUTE, expected_response, CommonClient,
                        lambda client: self.assertEqual(client.ping({}).__dict__, expected_response.__dict__))

    def test_version(self):
        expected_response = version.VersionResponse()
        run_test_server(HTTPMethod.GET.value, constants.API_VERSION_ROUTE, expected_response, CommonClient,
                        lambda client: self.assertEqual(client.version({}).__dict__, expected_response.__dict__))

    def test_add_secret(self):
        expected_response = base.BaseResponse()
        run_test_server(HTTPMethod.POST.value, constants.API_SECRET_ROUTE, expected_response, CommonClient,
                        lambda client: self.assertIsInstance(client.add_secret({}, secret.SecretRequest()), base.BaseResponse))


if __name__ == '__main__':
    unittest.main()
