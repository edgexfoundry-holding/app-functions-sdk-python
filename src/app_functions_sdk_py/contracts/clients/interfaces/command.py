#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
The command module of the App Functions SDK.

This module provides the CommandClient abstract base class (ABC) which defines the interface for an
command client.
"""
from abc import ABC, abstractmethod
from typing import Any

from ...dtos.common.base import BaseResponse
from ...dtos.responses.command import MultiDeviceCoreCommandsResponse, DeviceCoreCommandResponse
from ...dtos.responses.event import EventResponse


class CommandClientABC(ABC):
    """
    An abstract base class that defines the interface for a command client.
    """
    @abstractmethod
    def all_device_core_commands(self, ctx: dict, offset: int, limit: int) -> \
            MultiDeviceCoreCommandsResponse:
        """
        An abstract method that should be implemented to get all device core commands.
        """

    @abstractmethod
    def device_core_commands_by_device_name(self, ctx: dict, device_name: str) -> \
            DeviceCoreCommandResponse:
        """
        An abstract method that should be implemented to get device core command by device name.
        """

    #  pylint: disable=too-many-arguments, too-many-positional-arguments
    @abstractmethod
    def issue_get_command_by_name(self, ctx: dict, device_name: str, command_name: str,
                                  ds_push_event: bool, ds_return_event: bool) -> EventResponse:
        """
        An abstract method that should be implemented to issue a GET command by name.
        """

    @abstractmethod
    def issue_get_command_by_name_with_query_params(self, ctx: dict,
                                                    device_name: str,
                                                    command_name: str,
                                                    query_params: dict[str, str]) -> EventResponse:
        """
        An abstract method that should be implemented to issue a GET command by name with query
        parameters.
        """

    @abstractmethod
    def issue_set_command_by_name(self, ctx: dict, device_name: str, command_name: str,
                                  settings: dict[str, str]) -> BaseResponse:
        """
        An abstract method that should be implemented to issue the specified write command
        referenced by the command name to the device/sensor that is also referenced by name.
        """

    @abstractmethod
    def issue_set_command_by_name_with_object(self, ctx: dict, device_name: str, command_name: str,
                                  settings: dict[str, Any]) -> BaseResponse:
        """
        An abstract method that should be implemented to issue the specified write command and the
        settings supports object value type
        """
