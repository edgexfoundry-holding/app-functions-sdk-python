# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The deviceprofile module of the App Functions SDK Python package.

This module defines the DeviceProfile and DeviceProfileBasicInfo classes which represent a device
profile and its basic information in the context of the App Functions SDK. A device profile is a
collection of specifications that define the device's capabilities.

Classes:
    DeviceProfileBasicInfo: Represents the basic information of a device profile. It has attributes
    like profile_id, name, manufacturer, description, model, and labels.
    DeviceProfile: Represents a device profile. It has attributes like created, updated,
    profile_basic_info, device_resources, and device_commands.
"""

from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from .dbtimestamp import DBTimestamp
from .devicecommand import DeviceCommand
from .deviceresource import DeviceResource


@dataclass_json
@dataclass
class DeviceProfileBasicInfo(DBTimestamp):
    """
    Represents the basic information of a device profile.

    A device profile's basic information includes attributes like profile_id, name, manufacturer,
    description, model, and labels.
    """
    id: str = ""
    name: str = ""
    manufacturer: str = ""
    description: str = ""
    model: str = ""
    labels: Optional[list[str]] = None

@dataclass_json
@dataclass
class UpdateDeviceProfileBasicInfo:
    """
    Represents the basic information of a device profile.
    """
    id: str = ""
    name: str = ""
    manufacturer: str = ""
    description: str = ""
    model: str = ""
    labels: Optional[list[str]] = None


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class DeviceProfile(DeviceProfileBasicInfo):
    """
    Represents a device profile.

    A device profile is a collection of specifications that define the device's capabilities. It has
    attributes like created, updated, profile_basic_info, device_resources, and device_commands.
    """
    deviceResources: Optional[list[DeviceResource]] = None
    deviceCommands: Optional[list[DeviceCommand]] = None
