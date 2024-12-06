#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `RegistryClient` class, which is a REST client for invoking
the registry APIs (/registry/*) from Core Keeper.

Classes:
    - RegistryClient: A client for interacting with the registry APIs.

Functions:
    - register: Registers a service instance.
    - update_register: Updates the registration data of the service.
    - registration_by_service_id: Retrieves the registration data of a service by its service ID.
    - all_registry: Returns the registration data of all registered services.
    - deregister: Deregisters a service by its service ID.
"""

from .interfaces.authinjector import AuthenticationInjector
from .interfaces.registry import RegistryClientABC
from .utils.common import PathBuilder
from .utils.request import post_request_with_raw_data, put_request, get_request, delete_request
from .. import errors
from ..common.constants import API_REGISTRY_ROUTE, SERVICE_ID, DEREGISTERED, API_ALL_REGISTRY_ROUTE
from ..dtos.requests.registration import AddRegistrationRequest
from ..dtos.responses.registration import RegistrationResponse, MultiRegistrationResponse

EMPTY_RESPONSE = any


class RegistryClient(RegistryClientABC):
    """
    RegistryClient is the REST client for invoking the registry APIs(/registry/*) from Core Keeper
    """
    def __init__(self, base_url: str, auth_injector: AuthenticationInjector,
                 enable_name_field_escape: bool):
        self.base_url = base_url
        self.auth_injector = auth_injector
        self.enable_name_field_escape = enable_name_field_escape

    def register(self, ctx: dict, req: AddRegistrationRequest):
        """Registers a service instance"""
        try:
            post_request_with_raw_data(ctx, EMPTY_RESPONSE, self.base_url, API_REGISTRY_ROUTE,
                                       None, req, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

    def update_register(self, ctx: dict, req: AddRegistrationRequest):
        """Updates the registration data of the service"""
        try:
            put_request(ctx, EMPTY_RESPONSE, self.base_url, API_REGISTRY_ROUTE, None, req,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

    def registration_by_service_id(self, ctx: dict, service_id: str) -> RegistrationResponse:
        """Retrieves the registration data of a service by its service id"""
        request_path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_REGISTRY_ROUTE).set_path(SERVICE_ID).set_name_field_path(service_id).build_path()
        res = RegistrationResponse()
        try:
            get_request(ctx, res, self.base_url, request_path, None, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

        return res

    def all_registry(self, ctx: dict, deregistered: bool) -> MultiRegistrationResponse:
        """Returns the registration data of all registered service"""
        request_params = {DEREGISTERED: [str(deregistered)]}
        res = MultiRegistrationResponse()
        try:
            get_request(ctx, res, self.base_url, API_ALL_REGISTRY_ROUTE, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

        return res

    def deregister(self, ctx: dict, service_id: str):
        """Deregisters a service by service id"""
        request_path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_REGISTRY_ROUTE).set_path(SERVICE_ID).set_name_field_path(service_id).build_path()
        try:
            delete_request(ctx, EMPTY_RESPONSE, self.base_url, request_path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
