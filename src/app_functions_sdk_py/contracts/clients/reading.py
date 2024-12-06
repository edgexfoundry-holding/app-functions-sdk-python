#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the implementation of the ReadingClient.
"""
from dataclasses import dataclass
from typing import Optional

from .interfaces.authinjector import AuthenticationInjector
from .interfaces.reading import ReadingClientABC
from .utils.common import escape_and_join_path, PathBuilder
from .utils.request import get_request, get_request_with_body_raw_data
from .. import errors
from ..common.constants import OFFSET, LIMIT, API_ALL_READING_ROUTE, API_READING_COUNT_ROUTE, \
    DEVICE, NAME, API_READING_ROUTE, RESOURCE_NAME, START, END, RESOURCE_NAMES
from ..dtos.common.count import CountResponse
from ..dtos.responses.reading import MultiReadingsResponse


@dataclass
class ReadingClient(ReadingClientABC):
    """
    ReadingClient is an implementation of ReadingClientABS to interact with core-data service via
    REST APIs.
    """
    base_url: str
    auth_injector: Optional[AuthenticationInjector]
    enable_name_field_escape: bool = False

    def all_readings(self, ctx: dict, offset: int, limit: int) -> MultiReadingsResponse:
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        response = MultiReadingsResponse()
        try:
            get_request(ctx, response, self.base_url, API_ALL_READING_ROUTE, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return response

    def reading_count(self, ctx: dict) -> CountResponse:
        response = CountResponse()
        try:
            get_request(ctx, response, self.base_url, API_READING_COUNT_ROUTE, None,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return response

    def reading_count_by_device_name(self, ctx: dict, device_name: str) -> CountResponse:
        path = escape_and_join_path(API_READING_COUNT_ROUTE, DEVICE, NAME, device_name)
        count_resp = CountResponse()
        try:
            get_request(ctx, count_resp, self.base_url, path, None, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return count_resp

    def readings_by_device_name(self, ctx: dict, device_name: str, offset: int, limit: int) -> \
            MultiReadingsResponse:
        path = escape_and_join_path(API_READING_ROUTE, DEVICE, NAME, device_name)
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        response = MultiReadingsResponse()
        try:
            get_request(ctx, response, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return response

    def readings_by_resource_name(self, ctx: dict, resource_name: str, offset: int, limit: int) -> \
            MultiReadingsResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_READING_ROUTE).set_path(
            RESOURCE_NAME).set_name_field_path(
            resource_name).build_path()
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        readings_resp = MultiReadingsResponse()
        try:
            get_request(ctx, readings_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return readings_resp

    #  pylint: disable=too-many-arguments, too-many-positional-arguments
    def readings_by_time_range(self, ctx: dict, start: int, end: int, offset: int, limit: int) -> \
            MultiReadingsResponse:
        path = escape_and_join_path(API_READING_ROUTE, START, str(start), END,
                                    str(end))
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        readings_resp = MultiReadingsResponse()
        try:
            get_request(ctx, readings_resp, self.base_url, path, request_params, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return readings_resp

    # pylint: disable=too-many-positional-arguments
    def readings_by_resource_name_and_time_range(self, ctx: dict, resource_name: str, start: int,
                                                 end: int, offset: int,
                                                 limit: int) -> MultiReadingsResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_READING_ROUTE).set_path(
            RESOURCE_NAME).set_name_field_path(
            resource_name).set_path(START).set_path(str(start)).set_path(
            END).set_path(str(end)).build_path()
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        readings_resp = MultiReadingsResponse()
        try:
            get_request(ctx, readings_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return readings_resp

    # pylint: disable=too-many-positional-arguments
    def readings_by_device_name_and_resource_name(self, ctx: dict, device_name: str,
                                                  resource_name: str, offset: int,
                                                  limit: int) -> MultiReadingsResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_READING_ROUTE).set_path(
            DEVICE).set_path(NAME).set_name_field_path(
            device_name).set_path(RESOURCE_NAME).set_name_field_path(resource_name).build_path()
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        readings_resp = MultiReadingsResponse()
        try:
            get_request(ctx, readings_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return readings_resp

    # pylint: disable=too-many-positional-arguments
    def readings_by_device_name_and_resource_name_and_time_range(self, ctx: dict, device_name: str,
                                                                 resource_name: str, start: int,
                                                                 end: int, offset: int,
                                                                 limit: int) -> \
            MultiReadingsResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_READING_ROUTE).set_path(
            DEVICE).set_path(NAME).set_name_field_path(
            device_name).set_path(RESOURCE_NAME).set_name_field_path(resource_name).set_path(
            START).set_path(str(start)).set_path(END).set_path(str(end)).build_path()
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        readings_resp = MultiReadingsResponse()
        try:
            get_request(ctx, readings_resp, self.base_url, path, request_params,
                        self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return readings_resp

    # pylint: disable=too-many-positional-arguments
    def readings_by_device_name_and_resource_names_and_time_range(self, ctx: dict, device_name: str,
                                                                  resource_names: [str], start: int,
                                                                  end: int, offset: int,
                                                                  limit: int) -> \
            MultiReadingsResponse:
        path = PathBuilder().enable_name_field_escape(
            self.enable_name_field_escape).set_path(
            API_READING_ROUTE).set_path(
            DEVICE).set_path(NAME).set_name_field_path(
            device_name).set_path(START).set_path(str(start)).set_path(
            END).set_path(str(end)).build_path()
        request_params = {OFFSET: str(offset), LIMIT: str(limit)}
        query_payload = {}
        if len(resource_names)  > 0:
            query_payload[RESOURCE_NAMES] = resource_names
        readings_resp = MultiReadingsResponse()
        try:
            get_request_with_body_raw_data(ctx, readings_resp, self.base_url, path, request_params,
                                           query_payload, self.auth_injector)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)
        return readings_resp
