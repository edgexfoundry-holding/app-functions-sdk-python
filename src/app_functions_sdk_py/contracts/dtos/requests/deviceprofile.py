# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The deviceprofile module of the App Functions SDK Python package.

This module defines the DeviceProfileRequest class which represents a request to handle a device
profile.

Classes:
    DeviceProfileRequest: Represents a request to handle a device profile. It inherits from
    BaseRequest and adds a profile attribute.
"""

from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from ..common.base import BaseRequest
from ..deviceprofile import DeviceProfile, UpdateDeviceProfileBasicInfo


@dataclass_json
@dataclass
class DeviceProfileRequest(BaseRequest):
    """
    Represents a request to handle a device profile.
    """
    profile: Optional[DeviceProfile] = None

@dataclass_json
@dataclass
class DeviceProfileBasicInfoRequest(BaseRequest):
    """
    Represents a request to handle a device profile basic info.
    """
    basicinfo: Optional[UpdateDeviceProfileBasicInfo] = None
