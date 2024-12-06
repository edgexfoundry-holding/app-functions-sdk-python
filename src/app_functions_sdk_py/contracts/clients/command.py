#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the CommandClient implementation.
"""
from typing import Any, Optional
from dataclasses import dataclass

from .interfaces.authinjector import AuthenticationInjector
from .interfaces.command import CommandClientABC
from .utils.common import PathBuilder
from .utils.request import get_request, put_request
from .. import errors
from ..common.constants import OFFSET, LIMIT, API_ALL_DEVICE_ROUTE, API_DEVICE_ROUTE, NAME, \
    VALUE_TRUE, VALUE_FALSE, PUSH_EVENT, RETURN_EVENT
from ..dtos.common.base import BaseResponse
from ..dtos.responses.command import DeviceCoreCommandResponse, MultiDeviceCoreCommandsResponse
from ..dtos.responses.event import EventResponse


@dataclass
class CommandClient(CommandClientABC):
    """
    CommandClient is an implementation of CommandClientABC to interact with core-command service via
    REST APIs.
    """
    base_url: str
    auth_injector: Optional[AuthenticationInjector]
    enable_name_field_escape: bool = False

    def all_device_core_commands(self, ctx: dict, offset: int, limit: int) -> \
            MultiDeviceCoreCommandsResponse:
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        resp = MultiDeviceCoreCommandsResponse()
        try:
            get_request(ctx, resp, self.base_url, API_ALL_DEVICE_ROUTE, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def device_core_commands_by_device_name(self, ctx: dict, device_name: str) -> \
            DeviceCoreCommandResponse:
        path = PathBuilder().enable_name_field_escape(self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(NAME).set_name_field_path(device_name).build_path()
        response = DeviceCoreCommandResponse()
        try:
            get_request(ctx, response, self.base_url, path, None, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return response

    #  pylint: disable=too-many-arguments, too-many-positional-arguments
    def issue_get_command_by_name(self, ctx: dict, device_name: str, command_name: str,
                                  ds_push_event: bool, ds_return_event: bool) -> EventResponse:
        request_params = {PUSH_EVENT: VALUE_TRUE if ds_push_event else VALUE_FALSE,
                          RETURN_EVENT: VALUE_TRUE if ds_return_event else VALUE_FALSE}
        path = PathBuilder().enable_name_field_escape(self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(NAME).set_name_field_path(device_name).set_name_field_path(
            command_name).build_path()
        response = EventResponse()
        try:
            get_request(ctx, response, self.base_url, path, request_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return response

    def issue_get_command_by_name_with_query_params(self, ctx: dict, device_name: str,
                                                    command_name: str,
                                                    query_params: dict[str, str]) -> EventResponse:
        path = PathBuilder().enable_name_field_escape(self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(NAME).set_name_field_path(device_name).set_name_field_path(
            command_name).build_path()
        resp = EventResponse()
        try:
            get_request(ctx, resp, self.base_url, path, query_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def issue_set_command_by_name(self, ctx: dict, device_name: str, command_name: str,
                                  settings: dict[str, str]) -> BaseResponse:
        return self._issue_set_command(ctx, device_name, command_name, settings)

    def issue_set_command_by_name_with_object(self, ctx: dict, device_name: str, command_name: str,
                                              settings: dict[str, Any]) -> BaseResponse:
        return self._issue_set_command(ctx, device_name, command_name, settings)

    def _issue_set_command(self, ctx: dict, device_name: str, command_name: str,
                                              settings: dict) -> BaseResponse:
        path = PathBuilder().enable_name_field_escape(self.enable_name_field_escape).set_path(
            API_DEVICE_ROUTE).set_path(NAME).set_name_field_path(device_name).set_name_field_path(
            command_name).build_path()
        resp = BaseResponse()
        try:
            put_request(ctx, resp, self.base_url, path, None, settings,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp
