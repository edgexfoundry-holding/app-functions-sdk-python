# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The devicecommand module of the App Functions SDK Python package.

This module defines the AddDeviceCommandRequest class which represents a request to add a device
command.

Classes:
    AddDeviceCommandRequest: Represents a request to add a device command. It inherits from
    BaseRequest and adds a profile_name and device_command attributes.
"""

from dataclasses import dataclass

from dataclasses_json import dataclass_json

from ..common.base import BaseRequest
from ..devicecommand import DeviceCommand, UpdateDeviceCommand


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class AddDeviceCommandRequest(BaseRequest):
    """
    Represents a request to add a device command.
    """
    profileName: str = ""
    deviceCommand: DeviceCommand = DeviceCommand()

@dataclass_json
@dataclass
class UpdateDeviceCommandRequest(BaseRequest):
    """
    Represents a request to add a device command.
    """
    profileName: str = ""
    deviceCommand: UpdateDeviceCommand = UpdateDeviceCommand()
