#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines data transfer objects (DTOs) related to the device core commands.
"""
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

from ..common.base import BaseResponse, BaseWithTotalCountResponse
from ..corecommand import DeviceCoreCommand

# pylint: disable=invalid-name
@dataclass_json
@dataclass
class DeviceCoreCommandResponse(BaseResponse):
    """
    DeviceCoreCommandResponse defines the Response Content for GET DeviceCoreCommand DTO.
    """
    deviceCoreCommand: DeviceCoreCommand = None


@dataclass_json
@dataclass
class MultiDeviceCoreCommandsResponse(BaseWithTotalCountResponse):
    """
    MultiDeviceCoreCommandsResponse defines the Response Content for GET multiple DeviceCoreCommand
    DTOs.
    """
    deviceCoreCommands: list[DeviceCoreCommand]= field(default_factory=lambda: [], init=True)
