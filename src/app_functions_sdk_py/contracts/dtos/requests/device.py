# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The device module of the App Functions SDK Python package.

This module defines the AddDeviceRequest class which represents a request to add a device.

Classes:
    AddDeviceRequest: Represents a request to add a device. It inherits from BaseRequest and adds a
    device attribute.
"""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from ..common.base import BaseRequest
from ..device import Device, UpdateDevice


@dataclass_json
@dataclass
class AddDeviceRequest(BaseRequest):
    """
    Represents a request to add a device.
    """
    device: Optional[Device] = None

@dataclass_json
@dataclass
class UpdateDeviceRequest(BaseRequest):
    """
    Represents a request to add a device.
    """
    device: Optional[UpdateDevice] = None
