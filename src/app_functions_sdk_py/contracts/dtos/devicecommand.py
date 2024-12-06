# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The devicecommand module of the App Functions SDK Python package.

This module defines the DeviceCommand class which represents a device command in the context of the
App Functions SDK. A device command is a command that can be executed on a device.

Classes:
    DeviceCommand: Represents a device command. It has attributes like name, is_hidden, read_write,
    resource_operations, and tags.
"""

from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import dataclass_json

from .resourceoperation import ResourceOperation
from .tags import Tags
from ..common.constants import READ_WRITE_R


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class DeviceCommand:
    """
    Represents a device command.
    """
    name: str = ""
    isHidden: bool = False
    readWrite: str = READ_WRITE_R
    resourceOperations: list[ResourceOperation] = field(default_factory=list)
    tags: Optional[Tags] = None


@dataclass_json
@dataclass
class UpdateDeviceCommand:
    """
    Represents a updated device command.
    """
    name: str = ""
    isHidden: bool = False
