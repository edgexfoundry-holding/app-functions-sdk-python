#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines response data classes for device resources in the EdgeX Foundry core-metadata
service.
"""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from ..common.base import BaseResponse
from ..deviceresource import DeviceResource


@dataclass_json
@dataclass
class DeviceResourceResponse(BaseResponse):
    """
    DeviceResourceResponse defines the Response Content for GET DeviceResource DTOs.
    """
    resource: Optional[DeviceResource] = None
