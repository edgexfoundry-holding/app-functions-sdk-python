# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module contains a concrete implementation of the CommonClientABC abstract class for
interacting with various services.
"""

from dataclasses import dataclass
from typing import Optional

from ...contracts.clients.interfaces.authinjector import AuthenticationInjector
from ...contracts.dtos.common import config, ping, version, base, secret
from ...contracts.clients.utils import request
from ...contracts.clients.interfaces.common import CommonClientABC
from ...contracts.common import constants
from ...contracts import errors


@dataclass
class CommonClient(CommonClientABC):
    """
    A concrete implementation of the CommonClient interface for interacting with various services.

    This class provides concrete implementations for the methods defined in the CommonClient
    interface, facilitating operations such as fetching configuration information, testing service
    availability, obtaining version details, and managing secrets within the service's
    secret store. It utilizes the `request` utility functions for making HTTP requests to the
    service's endpoints, handling authentication via an optional `AuthenticationInjector`.

    Attributes:
        base_url (str): The base URL of the service to which the client will make requests.
        auth_injector (AuthenticationInjector, optional): An injector for adding authentication
            details to the requests. Defaults to None.

    Methods:
        configuration(ctx: dict) -> config.ConfigResponse:
            Fetches configuration information from the service.

        ping(ctx: dict) -> ping.PingResponse:
            Tests the availability of the service.

        version(ctx: dict) -> version.VersionResponse:
            Retrieves the service's version information.

        add_secret(ctx: dict, req: secret.SecretRequest) -> base.BaseResponse:
            Adds EdgeX Service exclusive secret to the Secret Store.
    """
    base_url: str
    auth_injector: Optional[AuthenticationInjector]

    def configuration(self, ctx: dict) -> config.ConfigResponse:
        cr = config.ConfigResponse()
        try:
            request.get_request(ctx, cr, self.base_url, constants.API_CONFIG_ROUTE, None,
                                self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return cr

    def ping(self, ctx: dict) -> ping.PingResponse:
        pr = ping.PingResponse()
        try:
            request.get_request(ctx, pr, self.base_url, constants.API_PING_ROUTE, None,
                                self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return pr

    def version(self, ctx: dict) -> version.VersionResponse:
        vr = version.VersionResponse()
        try:
            request.get_request(ctx, vr, self.base_url, constants.API_VERSION_ROUTE, None,
                                self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return vr

    def add_secret(self, ctx: dict, req: secret.SecretRequest) -> base.BaseResponse:
        br = base.BaseResponse()
        try:
            request.post_request_with_raw_data(ctx, br, self.base_url,
                                               constants.API_SECRET_ROUTE, None, req,
                                               self.auth_injector)
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)
        return br
