#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines the response DTOs for device-related operations in the EdgeX Foundry
core-metadata service.

Classes:
    DeviceResponse: Defines the response content for GET device DTOs.
    MultiDevicesResponse: Defines the response content for GET multiple device DTOs.
"""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from ..common.base import BaseResponse, BaseWithTotalCountResponse
from ..device import Device


@dataclass_json
@dataclass
class DeviceResponse(BaseResponse):
    """
    DeviceResponse defines the Response Content for GET Device DTOs.
    """
    device: Optional[Device] = None

@dataclass_json
@dataclass
class MultiDevicesResponse(BaseWithTotalCountResponse):
    """
    MultiDevicesResponse defines the Response Content for GET multiple Device DTOs.
    """
    devices: Optional[list[Device]] = None
