# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import threading
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, unquote

from src.app_functions_sdk_py.contracts.common import constants
from src.app_functions_sdk_py.contracts.dtos.kvs import KVS, KeyOnly
from src.app_functions_sdk_py.configuration.keeper.conversion import convert_interface_to_pairs
from src.app_functions_sdk_py.contracts.dtos.common.base import BaseResponse
from src.app_functions_sdk_py.contracts.dtos.requests.kvs import UpdateKeysRequest
from src.app_functions_sdk_py.contracts.dtos.responses.kvs import MultiKeyValueResponse, KeysResponse

API_KV_ROUTE = constants.API_KVS_ROUTE + "/" + constants.KEY


class MockCoreKeeper:
    def __init__(self):
        self.server_thread = None
        self.key_value_store = dict[str, KVS]()

    def reset(self):
        self.key_value_store = dict[str, KVS]()

    def check_for_prefix(self, prefix: str) -> tuple[list[KVS], bool]:
        pairs = [v for k, v in self.key_value_store.items() if k.startswith(prefix)]
        if len(pairs) == 0:
            return pairs, False
        return pairs, True

    def update_kv_store(self, key: str, value: Any):
        if key in self.key_value_store:
            self.key_value_store[key].value = value
        else:
            self.key_value_store[key] = KVS(key=key, value=value)

    def start(self) -> HTTPServer:
        def handler_factory(mock_core_keeper, *args, **kwargs):
            class MockRequestHandler(BaseHTTPRequestHandler):
                def do_PUT(self):
                    url_path = unquote(urlparse(self.path).path)
                    if API_KV_ROUTE in url_path:
                        key = url_path.replace(f"{API_KV_ROUTE}/", "", 1)
                        content_length = int(self.headers['Content-Length'])
                        body = self.rfile.read(content_length)
                        try:
                            update_keys_request = UpdateKeysRequest(**json.loads(body))
                        except json.JSONDecodeError as e:
                            logging.error(f"Error decoding the request body: {e}")
                            self.send_response(400)
                            self.end_headers()
                            return

                        query = parse_qs(urlparse(self.path).query)
                        is_flatten = constants.FLATTEN in query

                        if is_flatten:
                            kv_pairs = convert_interface_to_pairs(key, update_keys_request.value)
                            for kv_pair in kv_pairs:
                                mock_core_keeper.update_kv_store(kv_pair.key, kv_pair.value)
                        else:
                            mock_core_keeper.update_kv_store(key, update_keys_request.value)
                        self.send_response(204)
                        self.end_headers()

                def do_GET(self):
                    url_path = unquote(urlparse(self.path).path)
                    query = parse_qs(urlparse(self.path).query)
                    if API_KV_ROUTE in url_path:
                        key = url_path.replace(f"{API_KV_ROUTE}/", "", 1)
                        all_keys_requested = constants.KEY_ONLY in query

                        pairs, prefix_found = mock_core_keeper.check_for_prefix(key)
                        if not prefix_found:
                            resp = BaseResponse(
                                message=f"query key {key} not found",
                                statusCode=404,
                            )
                            self.send_response(404)
                        else:
                            if all_keys_requested:
                                keys = [KeyOnly(kv_pair.key) for kv_pair in pairs]
                                resp = KeysResponse(response=keys)
                            else:
                                kvs = [
                                    KVS(key=kv_pair.key, value=kv_pair.value)
                                    for kv_pair in pairs
                                ]
                                resp = MultiKeyValueResponse(response=kvs)
                            self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps(resp, default=lambda o: o.__dict__).encode('utf-8'))
                    elif constants.API_PING_ROUTE in url_path:
                        self.send_response(200)
                        self.end_headers()

            return MockRequestHandler(*args, **kwargs)

        server = HTTPServer(('localhost', 0), partial(handler_factory, self))
        self.server_thread = threading.Thread(target=server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        return server
