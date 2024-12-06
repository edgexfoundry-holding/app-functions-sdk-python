#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the DeviceProfileClient implementation.
"""
import threading
from dataclasses import dataclass
from typing import Optional

from .interfaces.authinjector import AuthenticationInjector
from .interfaces.deviceprofile import DeviceProfileClientABC
from .utils.common import PathBuilder, escape_and_join_path
from .utils.request import post_request_with_raw_data, patch_request, post_by_file_request, \
    delete_request, get_request, put_by_file_request, put_request
from .. import errors
from ..common.constants import API_DEVICE_PROFILE_ROUTE, API_DEVICE_PROFILE_UPLOAD_FILE_ROUTE, \
    NAME, OFFSET, LIMIT, LABELS, API_ALL_DEVICE_PROFILE_ROUTE, \
    API_ALL_DEVICE_PROFILE_BASIC_INFO_ROUTE, MODEL, MANUFACTURER, \
    API_DEVICE_PROFILE_BASIC_INFO_ROUTE, API_DEVICE_PROFILE_RESOURCE_ROUTE, RESOURCE, \
    DEVICE_COMMAND, API_DEVICE_PROFILE_DEVICE_COMMAND_ROUTE, API_DEVICE_RESOURCE_ROUTE, PROFILE
from ..dtos.common.base import BaseResponse, BaseWithIdResponse
from ..dtos.requests.devicecommand import UpdateDeviceCommandRequest, AddDeviceCommandRequest
from ..dtos.requests.deviceprofile import DeviceProfileBasicInfoRequest, DeviceProfileRequest
from ..dtos.requests.deviceresource import UpdateDeviceResourceRequest, AddDeviceResourceRequest
from ..dtos.responses.deviceprofile import MultiDeviceProfilesResponse, \
    MultiDeviceProfileBasicInfoResponse, DeviceProfileResponse
from ..dtos.responses.deviceresource import DeviceResourceResponse
from ...constants import SPILT_COMMA


@dataclass
class DeviceProfileClient(DeviceProfileClientABC):
    """
    DeviceServiceClient is an implementation of DeviceServiceClientABC to interact with
    core-metadata service via REST APIs.
    """
    base_url: str
    auth_injector: Optional[AuthenticationInjector]
    enable_name_field_escape: bool = False

    def __post_init__(self):
        self._mutex = threading.Lock()
        self._resource_cache = dict[str, DeviceResourceResponse]()

    def add(self, ctx: dict, reqs: [DeviceProfileRequest]) -> [BaseWithIdResponse]:
        add_dp_resp = [BaseWithIdResponse()]
        try:
            post_request_with_raw_data(ctx, add_dp_resp, self.base_url, API_DEVICE_PROFILE_ROUTE,
                                       None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return add_dp_resp

    def update(self, ctx: dict, reqs: [DeviceProfileRequest]) -> [BaseResponse]:
        update_dp_resp = [BaseResponse()]
        try:
            put_request(ctx, update_dp_resp, self.base_url, API_DEVICE_PROFILE_ROUTE,
                        None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return update_dp_resp

    def add_by_yaml(self, ctx: dict, yaml_file_path: str) -> BaseWithIdResponse:
        id_resp = BaseWithIdResponse()
        try:
            post_by_file_request(ctx, id_resp, self.base_url,
                                 API_DEVICE_PROFILE_UPLOAD_FILE_ROUTE,
                                 yaml_file_path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return id_resp

    def update_by_yaml(self, ctx: dict, yaml_file_path: str) -> BaseResponse:
        update_resp = BaseResponse()
        try:
            put_by_file_request(ctx, update_resp, self.base_url,
                                API_DEVICE_PROFILE_UPLOAD_FILE_ROUTE,
                                yaml_file_path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return update_resp

    def delete_by_name(self, ctx: dict, name: str) -> BaseResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_PROFILE_ROUTE).set_path(NAME).set_name_field_path(
            name).build_path()
        delete_dp_resp = BaseResponse()
        try:
            delete_request(ctx, delete_dp_resp, self.base_url, path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return delete_dp_resp

    def device_profile_by_name(self, ctx: dict, name: str) -> DeviceProfileResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_PROFILE_ROUTE).set_path(NAME).set_name_field_path(
            name).build_path()
        dp_resp = DeviceProfileResponse()
        try:
            get_request(ctx, dp_resp, self.base_url, path, None, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return dp_resp

    def all_device_profiles(self, ctx: dict, labels: [str], offset: int, limit: int) -> \
            MultiDeviceProfilesResponse:
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        if labels is not None and len(labels) > 0:
            request_params[LABELS] = SPILT_COMMA.join(labels)
        all_dp_resp = MultiDeviceProfilesResponse()
        try:
            get_request(ctx, all_dp_resp, self.base_url, API_ALL_DEVICE_PROFILE_ROUTE,
                        request_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return all_dp_resp

    def all_device_profile_basic_infos(self, ctx: dict, labels: [str], offset: int, limit: int) -> \
            MultiDeviceProfileBasicInfoResponse:
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        if labels is not None and len(labels) > 0:
            request_params[LABELS] = SPILT_COMMA.join(labels)
        all_bi_resp = MultiDeviceProfileBasicInfoResponse()
        try:
            get_request(ctx, all_bi_resp, self.base_url, API_ALL_DEVICE_PROFILE_BASIC_INFO_ROUTE,
                        request_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return all_bi_resp

    def device_profile_by_model(self, ctx: dict, model: str, offset: int, limit: int) -> \
            MultiDeviceProfilesResponse:
        path = escape_and_join_path(API_DEVICE_PROFILE_ROUTE, MODEL, model)
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        dp_by_model_resp = MultiDeviceProfilesResponse()
        try:
            get_request(ctx, dp_by_model_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return dp_by_model_resp

    def device_profile_by_manufacturer(self, ctx: dict, manufacturer: str, offset: int,
                                       limit: int) -> MultiDeviceProfilesResponse:
        path = escape_and_join_path(API_DEVICE_PROFILE_ROUTE, MANUFACTURER,
                                    manufacturer)
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        dp_by_manufacturer_resp = MultiDeviceProfilesResponse()
        try:
            get_request(ctx, dp_by_manufacturer_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return dp_by_manufacturer_resp

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def device_profile_by_manufacturer_and_model(self, ctx: dict, manufacturer: str, model: str,
                                                 offset: int,
                                                 limit: int) -> MultiDeviceProfilesResponse:
        path = escape_and_join_path(API_DEVICE_PROFILE_ROUTE, MANUFACTURER,
                                    manufacturer, MODEL, model)
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        dp_resp = MultiDeviceProfilesResponse()
        try:
            get_request(ctx, dp_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return dp_resp

    def device_resource_by_profile_name_and_resource_name(self, ctx: dict, profile_name: str,
                                                          resource_name: str) -> \
            DeviceResourceResponse:
        resource_cache_key = f"{profile_name}:{resource_name}"
        resource_resp = self._resource_by_cache_key(resource_cache_key)
        if resource_resp is not None:
            return resource_resp
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_RESOURCE_ROUTE).set_path(PROFILE).set_name_field_path(
            profile_name).set_path(RESOURCE).set_name_field_path(resource_name).build_path()
        dr_resp = DeviceResourceResponse()
        try:
            get_request(ctx, dr_resp, self.base_url, path, None, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        self._set_resource_cache(resource_cache_key, dr_resp)
        return dr_resp

    def _resource_by_cache_key(self, key: str) -> DeviceResourceResponse:
        with self._mutex:
            return self._resource_cache.get(key)

    def _set_resource_cache(self, key: str, resource: DeviceResourceResponse):
        with self._mutex:
            self._resource_cache[key] = resource

    def _clean_resource_cache(self):
        with self._mutex:
            self._resource_cache.clear()

    def update_device_profile_basic_info(self, ctx: dict,
                                         reqs: [DeviceProfileBasicInfoRequest]) -> [BaseResponse]:
        update_bi_resp = [BaseResponse()]
        try:
            patch_request(ctx, update_bi_resp, self.base_url, API_DEVICE_PROFILE_BASIC_INFO_ROUTE,
                          None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return update_bi_resp

    def add_device_profile_resource(self, ctx: dict, reqs: [AddDeviceResourceRequest]) -> \
            [BaseResponse]:
        add_res_resp = [BaseResponse()]
        try:
            post_request_with_raw_data(ctx, add_res_resp, self.base_url,
                                       API_DEVICE_PROFILE_RESOURCE_ROUTE,None, reqs,
                                       self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return add_res_resp

    def update_device_profile_resource(self, ctx: dict, reqs: [UpdateDeviceResourceRequest]) -> [
        BaseResponse]:
        update_res_resp = [BaseResponse()]
        try:
            patch_request(ctx, update_res_resp, self.base_url, API_DEVICE_PROFILE_RESOURCE_ROUTE,
                          None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return update_res_resp

    def delete_device_resource_by_name(self, ctx: dict, profile_name: str, resource_name: str) -> \
            BaseResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_PROFILE_ROUTE).set_path(NAME).set_name_field_path(
            profile_name).set_path(RESOURCE).set_name_field_path(
            resource_name).build_path()
        delete_dr_resp = BaseResponse()
        try:
            delete_request(ctx, delete_dr_resp, self.base_url, path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return delete_dr_resp

    def add_device_profile_device_command(self, ctx: dict, reqs: [AddDeviceCommandRequest]) -> \
            [BaseResponse]:
        add_dc_resp = [BaseResponse()]
        try:
            post_request_with_raw_data(ctx, add_dc_resp, self.base_url,
                                       API_DEVICE_PROFILE_DEVICE_COMMAND_ROUTE,
                                       None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return add_dc_resp

    def update_device_profile_device_command(self, ctx: dict,
                                             reqs: [UpdateDeviceCommandRequest]) -> [BaseResponse]:
        update_dc_resp = [BaseResponse()]
        try:
            patch_request(ctx, update_dc_resp, self.base_url,
                          API_DEVICE_PROFILE_DEVICE_COMMAND_ROUTE,
                          None, reqs, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return update_dc_resp

    def delete_device_command_by_name(self, ctx: dict, profile_name: str, command_name: str) -> \
            BaseResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_DEVICE_PROFILE_ROUTE).set_path(NAME).set_name_field_path(
            profile_name).set_path(DEVICE_COMMAND).set_name_field_path(
            command_name).build_path()
        delete_dc_resp = BaseResponse()
        try:
            delete_request(ctx, delete_dc_resp, self.base_url, path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return delete_dc_resp
