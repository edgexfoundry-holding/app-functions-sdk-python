# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The deviceresource module of the App Functions SDK Python package.

This module defines the DeviceResource class which represents a device resource in the context of
the App Functions SDK. A device resource is a data point on a device that can be read or written to.
"""

from dataclasses import dataclass, field
from typing import Optional, Any

from dataclasses_json import dataclass_json

from .resourceproperties import ResourceProperties

# pylint: disable=invalid-name
@dataclass_json
@dataclass
class DeviceResource:
    """
    Represents a device resource.
    """
    name: str = ""
    description: str = ""
    isHidden: bool = False
    properties: ResourceProperties = ResourceProperties()
    attributes: dict[str, Any] = field(default_factory=dict)
    tags: Optional[dict[str, Any]] = None


@dataclass_json
@dataclass
class UpdateDeviceResource:
    """
    Represents a updated device resource.
    """
    name: str = ""
    description: str = ""
    isHidden: bool = False
