#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines data transfer objects (DTOs) related to the device service.
"""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from ..common.base import BaseWithTotalCountResponse, BaseResponse
from ..deviceservice import DeviceService

@dataclass_json
@dataclass
class DeviceServiceResponse(BaseResponse):
    """
    DeviceServiceResponse defines the Response Content for GET DeviceService DTOs.
    """
    service: Optional[DeviceService] = None

@dataclass_json
@dataclass
class MultiDeviceServicesResponse(BaseWithTotalCountResponse):
    """
    MultiDeviceServicesResponse defines the Response Content for GET multiple DeviceService DTOs.
    """
    services: Optional[list[DeviceService]] = None
