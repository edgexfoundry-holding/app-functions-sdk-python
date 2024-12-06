#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines request data classes for adding and updating device resources in the EdgeX
Foundry core-metadata service.
"""
from dataclasses import dataclass

from dataclasses_json import dataclass_json

from ..common.base import BaseRequest
from ..deviceresource import DeviceResource, UpdateDeviceResource


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class AddDeviceResourceRequest(BaseRequest):
    """
    AddDeviceResourceRequest defines the request content for adding a new DeviceResource.
    """
    profileName: str = ""
    resource: DeviceResource = DeviceResource()

@dataclass_json
@dataclass
class UpdateDeviceResourceRequest(BaseRequest):
    """
    AddDeviceResourceRequest defines the request content for adding a new DeviceResource.
    """
    profileName: str = ""
    resource: UpdateDeviceResource = UpdateDeviceResource()
