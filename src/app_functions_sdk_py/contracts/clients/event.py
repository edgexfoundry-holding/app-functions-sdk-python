#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the EventClient implementation.
"""
from dataclasses import dataclass
from typing import Optional

from .utils.common import PathBuilder
from .utils.request import post_request, delete_request
from .interfaces.authinjector import AuthenticationInjector
from .interfaces.event import EventClientABC
from .utils.common import escape_and_join_path
from .utils.request import get_request
from .. import errors
from ..common.constants import API_EVENT_ROUTE, API_ALL_EVENT_ROUTE, OFFSET, LIMIT, \
    API_EVENT_COUNT_ROUTE, DEVICE, NAME, START, END, AGE, ID, CONTENT_TYPE_JSON
from ..dtos.common.base import BaseResponse, BaseWithIdResponse
from ..dtos.common.count import CountResponse
from ..dtos.requests.event import AddEventRequest
from ..dtos.responses.event import MultiEventsResponse

@dataclass
class EventClient(EventClientABC):
    """
    EventClient is an implementation of EventClientABC to interact with core-data service via
    REST APIs.
    """
    base_url: str
    auth_injector: Optional[AuthenticationInjector]
    enable_name_field_escape: bool = False

    def add(self, ctx: dict, service_name: str, req: AddEventRequest) -> BaseWithIdResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_EVENT_ROUTE).set_name_field_path(
            service_name).set_name_field_path(
            req.event.profileName).set_name_field_path(
            req.event.deviceName).set_name_field_path(
            req.event.sourceName).build_path()

        try:
            encoded_data = req.to_json().encode('utf-8')
        except Exception as e:
            raise errors.new_common_edgex_wrapper(e)
        resp = BaseWithIdResponse()
        try:
            post_request(ctx, resp, self.base_url, path, encoded_data, CONTENT_TYPE_JSON,
                         self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def all_events(self, ctx: dict, offset: int, limit: int) -> MultiEventsResponse:
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        resp = MultiEventsResponse()
        try:
            get_request(ctx, resp, self.base_url, API_ALL_EVENT_ROUTE, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def event_count(self, ctx: dict) -> CountResponse:
        resp = CountResponse()
        try:
            get_request(ctx, resp, self.base_url, API_EVENT_COUNT_ROUTE, None,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def event_count_by_device_name(self, ctx: dict, device_name: str) -> CountResponse:
        path = escape_and_join_path(API_EVENT_COUNT_ROUTE, DEVICE, NAME, device_name)
        resp = CountResponse()
        try:
            get_request(ctx, resp, self.base_url, path, None, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def events_by_device_name(self, ctx: dict, device_name: str, offset: int, limit: int) -> \
            MultiEventsResponse:
        path = escape_and_join_path(API_EVENT_ROUTE, DEVICE, NAME, device_name)
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        resp = MultiEventsResponse()
        try:
            get_request(ctx, resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def delete_by_device_name(self, ctx: dict, device_name: str) -> BaseResponse:
        path = escape_and_join_path(API_EVENT_ROUTE, DEVICE, NAME, device_name)
        resp = BaseResponse()
        try:
            delete_request(ctx, resp, self.base_url, path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    #  pylint: disable=too-many-arguments, too-many-positional-arguments
    def events_by_time_range(self, ctx: dict, start: int, end: int, offset: int, limit: int) -> \
            MultiEventsResponse:
        path = escape_and_join_path(API_EVENT_ROUTE, START, str(start), END, str(end))
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        resp = MultiEventsResponse()
        try:
            get_request(ctx, resp, self.base_url, path, request_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def delete_by_age(self, ctx: dict, age: int) -> BaseResponse:
        path = escape_and_join_path(API_EVENT_ROUTE, AGE, str(age))
        resp = BaseResponse()
        try:
            delete_request(ctx, resp, self.base_url, path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp

    def delete_by_id(self, ctx: dict, event_id: str) -> BaseResponse:
        path = escape_and_join_path(API_EVENT_ROUTE, ID, event_id)
        resp = BaseResponse()
        try:
            delete_request(ctx, resp, self.base_url, path, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return resp
