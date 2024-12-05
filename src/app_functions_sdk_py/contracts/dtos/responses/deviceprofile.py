#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines response data classes for device profiles in the EdgeX Foundry core-metadata
service.
"""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from ..common.base import BaseResponse, BaseWithTotalCountResponse
from ..deviceprofile import DeviceProfile, DeviceProfileBasicInfo


@dataclass_json
@dataclass
class DeviceProfileResponse(BaseResponse):
    """
    DeviceProfileResponse defines the Response Content for GET DeviceProfile DTOs.
    """
    profile: Optional[DeviceProfile] = None

@dataclass_json
@dataclass
class MultiDeviceProfilesResponse(BaseWithTotalCountResponse):
    """
    MultiDeviceProfilesResponse defines the Response Content for GET multiple DeviceProfile DTOs.
    """
    profiles: Optional[list[DeviceProfile]] = None

@dataclass_json
@dataclass
class MultiDeviceProfileBasicInfoResponse(BaseWithTotalCountResponse):
    """
    MultiDeviceProfileBasicInfoResponse defines the Response Content for GET multiple DeviceProfile
    basic info DTOs.
    """
    profiles: Optional[list[DeviceProfileBasicInfo]] = None
