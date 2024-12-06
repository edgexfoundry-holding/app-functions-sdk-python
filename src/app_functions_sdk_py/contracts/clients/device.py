#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the DeviceClient implementation.
"""
from dataclasses import dataclass
from typing import Optional

from .interfaces.authinjector import AuthenticationInjector
from .interfaces.device import DeviceClientABC
from .utils.common import PathBuilder
from .utils.request import post_request_with_raw_data, patch_request, get_request, delete_request
from .. import errors
from ..common.constants import API_DEVICE_ROUTE, OFFSET, LIMIT, LABELS, API_ALL_DEVICE_ROUTE, \
    DESCENDANTS_OF, MAX_LEVELS, CHECK, NAME, PROFILE, SERVICE
from ..dtos.common.base import BaseResponse, BaseWithIdResponse
from ..dtos.requests.device import UpdateDeviceRequest, AddDeviceRequest
from ..dtos.responses.device import MultiDevicesResponse, DeviceResponse
from ...constants import SPILT_COMMA


@dataclass
class DeviceClient(DeviceClientABC):
    """
    DeviceClient is an implementation of DeviceClientABC to interact with
    core-metadata service via REST APIs.
    """
    base_url: str
    auth_injector: Optional[AuthenticationInjector]
    enable_name_field_escape: bool = False

    def add(self, ctx: dict, reqs: [AddDeviceRequest]) -> [BaseWithIdResponse]:
        add_device_resp = [BaseWithIdResponse()]
        try:
            post_request_with_raw_data(ctx, add_device_resp, self.base_url, API_DEVICE_ROUTE,
                                       None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return add_device_resp

    def add_with_query_params(self, ctx: dict, reqs: [AddDeviceRequest], query_params: dict) -> \
            [BaseWithIdResponse]:
        add_resp = [BaseWithIdResponse()]
        try:
            post_request_with_raw_data(ctx, add_resp, self.base_url, API_DEVICE_ROUTE,
                                       query_params, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return add_resp

    def update(self, ctx: dict, reqs: [UpdateDeviceRequest]) -> [BaseResponse]:
        update_device_resp = [BaseResponse()]
        try:
            patch_request(ctx, update_device_resp, self.base_url, API_DEVICE_ROUTE,
                        None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return update_device_resp

    def update_with_query_params(self, ctx: dict, reqs: [UpdateDeviceRequest],
                                 query_params: dict) -> [BaseResponse]:
        update_resp = [BaseResponse()]
        try:
            patch_request(ctx, update_resp, self.base_url, API_DEVICE_ROUTE,
                        query_params, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return update_resp

    def all_devices(self, ctx: dict, labels: [str], offset: int, limit: int) -> \
            MultiDevicesResponse:
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        if labels is not None and len(labels) > 0:
            request_params[LABELS] = SPILT_COMMA.join(labels)
        all_devices_resp = MultiDevicesResponse()
        try:
            get_request(ctx, all_devices_resp, self.base_url, API_ALL_DEVICE_ROUTE,
                        request_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return all_devices_resp

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def all_devices_with_children(self, ctx: dict, parent: str, max_levels: int, labels: [str],
                                  offset: int, limit: int) -> MultiDevicesResponse:
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        if labels is not None and len(labels) > 0:
            request_params[LABELS] = SPILT_COMMA.join(labels)
        request_params[DESCENDANTS_OF] = parent
        request_params[MAX_LEVELS] = str(max_levels)
        all_devices_with_children_resp = MultiDevicesResponse()
        try:
            get_request(ctx, all_devices_with_children_resp, self.base_url, API_ALL_DEVICE_ROUTE,
                        request_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return all_devices_with_children_resp

    def device_name_exists(self, ctx: dict, name: str) -> BaseResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(CHECK).set_path(NAME).set_name_field_path(
            name).build_path()
        check_resp = BaseResponse()
        try:
            get_request(ctx, check_resp, self.base_url, path, None, self.auth_injector)
        except errors.EdgeX as e:
            # note that 404 is a valid response for this API when the name does not exist
            # so we need to handle this case separately
            if e.http_status_code() == 404:
                check_resp.statusCode = 404
                return check_resp
            raise errors.new_common_edgex_wrapper(e)
        return check_resp

    def device_by_name(self, ctx: dict, name: str) -> DeviceResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(NAME).set_name_field_path(name).build_path()
        device_resp = DeviceResponse()
        try:
            get_request(ctx, device_resp, self.base_url, path, None,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return device_resp

    def delete_device_by_name(self, ctx: dict, name: str) -> BaseResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(NAME).set_name_field_path(
            name).build_path()
        delete_device_resp = BaseResponse()
        try:
            delete_request(ctx, delete_device_resp, self.base_url, path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return delete_device_resp

    def devices_by_profile_name(self, ctx: dict, name: str, offset: int, limit: int) -> \
            MultiDevicesResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(PROFILE).set_path(NAME).set_name_field_path(
            name).build_path()
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        device_by_profile_resp = MultiDevicesResponse()
        try:
            get_request(ctx, device_by_profile_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return device_by_profile_resp

    def devices_by_service_name(self, ctx: dict, name: str, offset: int, limit: int) -> \
            MultiDevicesResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(SERVICE).set_path(NAME).set_name_field_path(
            name).build_path()
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        device_by_service_resp = MultiDevicesResponse()
        try:
            get_request(ctx, device_by_service_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return device_by_service_resp
