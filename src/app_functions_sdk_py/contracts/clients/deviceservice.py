#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the DeviceServiceClient implementation.
"""
from dataclasses import dataclass
from typing import Optional

from .interfaces.authinjector import AuthenticationInjector
from .interfaces.deviceservice import DeviceServiceClientABC
from .utils.common import PathBuilder
from .utils.request import post_request_with_raw_data, patch_request, get_request, delete_request
from .. import errors
from ..common.constants import API_DEVICE_SERVICE_ROUTE, OFFSET, LIMIT, LABELS, NAME, \
    API_ALL_DEVICE_SERVICE_ROUTE
from ..dtos.common.base import BaseWithIdResponse, BaseResponse
from ..dtos.requests.deviceservice import AddDeviceServiceRequest, UpdateDeviceServiceRequest
from ..dtos.responses.deviceservice import MultiDeviceServicesResponse, DeviceServiceResponse
from ...constants import SPILT_COMMA


@dataclass
class DeviceServiceClient(DeviceServiceClientABC):
    """
    DeviceServiceClient is an implementation of DeviceServiceClientABC to interact with
    core-metadata service via REST APIs.
    """
    base_url: str
    auth_injector: Optional[AuthenticationInjector]
    enable_name_field_escape: bool = False

    def add(self, ctx: dict, reqs: [AddDeviceServiceRequest]) -> [BaseWithIdResponse]:
        add_ds_resp = [BaseWithIdResponse()]
        try:
            post_request_with_raw_data(ctx, add_ds_resp, self.base_url, API_DEVICE_SERVICE_ROUTE,
                                       None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return add_ds_resp

    def update(self, ctx: dict, reqs: [UpdateDeviceServiceRequest]) -> [BaseResponse]:
        update_ds_resp = [BaseResponse()]
        try:
            patch_request(ctx, update_ds_resp, self.base_url, API_DEVICE_SERVICE_ROUTE,
                                       None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return update_ds_resp

    def all_device_services(self, ctx: dict, labels: [str], offset: int, limit: int) -> \
            MultiDeviceServicesResponse:
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        if labels is not None and len(labels) > 0:
            request_params[LABELS] = SPILT_COMMA.join(labels)
        all_ds_resp = MultiDeviceServicesResponse()
        try:
            get_request(ctx, all_ds_resp, self.base_url, API_ALL_DEVICE_SERVICE_ROUTE,
                        request_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return all_ds_resp

    def device_service_by_name(self, ctx: dict, name: str) -> DeviceServiceResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_SERVICE_ROUTE).set_path(NAME).set_name_field_path(
            name).build_path()
        ds_resp = DeviceServiceResponse()
        try:
            get_request(ctx, ds_resp, self.base_url, path, None, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return ds_resp

    def delete_by_name(self, ctx: dict, name: str) -> BaseResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_SERVICE_ROUTE).set_path(NAME).set_name_field_path(
            name).build_path()
        delete_ds_resp = BaseResponse()
        try:
            delete_request(ctx, delete_ds_resp, self.base_url, path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return delete_ds_resp
