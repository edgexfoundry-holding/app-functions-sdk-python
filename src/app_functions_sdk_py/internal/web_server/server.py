# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides functionality for processing http request
"""
from datetime import datetime
from typing import Optional, List, Any, Callable

import isodate
from fastapi import FastAPI, Depends
from uvicorn import Config, Server

from ..common.config import ConfigurationStruct
from ...contracts.clients.logger import Logger
from ...contracts.common.constants import (
    API_PING_ROUTE, API_VERSION_ROUTE, API_CONFIG_ROUTE, APPLICATION_VERSION)
from ...contracts.dtos.common.ping import PingResponse
from ...contracts.dtos.common.version import VersionResponse
from ...contracts.dtos.common.config import ConfigResponse


class WebServer:
    """ WebServer handles the webserver configuration and router """

    def __init__(self, logger: Logger, service_key: str, service_config: ConfigurationStruct):
        self.service_key = service_key
        self.service_config = service_config
        self.custom_config = None
        self.logger = logger
        self.router = FastAPI()

    def init_web_server(self):
        """ init_web_server initialize web server and add common route """
        self.router.add_api_route(API_PING_ROUTE, self.ping)
        self.router.add_api_route(API_CONFIG_ROUTE, self.config)
        self.router.add_api_route(API_VERSION_ROUTE, self.version)

    def add_route(self, path: str, handler, *middleware_func: Callable,
                  methods: Optional[List[str]] = None):
        """ add_route add a route to the web server """
        self.router.add_api_route(
            path, handler, methods=methods,
            # In the Go version of the App SDK, the middleware function set for a route is used to
            # perform authentication before executing the handler. Although FastAPI can also add
            # middleware, it works with every request and does not fit our needs.
            # To achieve the same functionality in FastAPI, we can use route dependencies.
            # A route dependency is a callable function that is called before the handler, and the
            # Request and Response objects can be accessed by injecting them as parameters.
            # For example: `def middleware_func(req: Request, resp: Response):`
            dependencies=[Depends(middleware) for middleware in middleware_func
                          if callable(middleware)])

    async def start_web_server(self):
        """ start_web_server starts the web server with the specified host, port """
        await self.create_http_server().serve()

    def create_http_server(self):
        """ since the asyncio only allow one event loop
            and `uvicorn.run` will try to control the event loop and throw below error
            `RuntimeError: asyncio.run() cannot be called from a running event loop`
            so we need to prevert using the `uvicorn.run` to start the http server
            and use `Server.serve()` instead.
            https://github.com/encode/uvicorn/issues/706#issuecomment-938180658"""

        bind_address = self.service_config.Service.Host
        if self.service_config.Service.ServerBindAddr != "":
            bind_address = self.service_config.Service.ServerBindAddr
        timeout = isodate.parse_duration("PT" + self.service_config.Service.RequestTimeout.upper())

        config = Config(
            host=bind_address,
            port=self.service_config.Service.Port,
            timeout_keep_alive=timeout.total_seconds(),
            app=self.router)
        return Server(config)

    def ping(self):
        """ ping is used to test if the service is working """
        return PingResponse(serviceName=self.service_key, timestamp=str(datetime.now()))

    def config(self):
        """ config is used to request the service's configuration """
        return ConfigResponse(serviceName=self.service_key, config=self.service_config)

    def version(self):
        """ version is used to request the service's versions """
        return VersionResponse(serviceName=self.service_key, version=APPLICATION_VERSION)

    def set_custom_config_info(self, custom_config: Any):
        """ set_custom_config_info set custom config info """
        self.custom_config = custom_config
