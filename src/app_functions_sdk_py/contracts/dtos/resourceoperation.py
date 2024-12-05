# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The resourceoperation module of the App Functions SDK Python package.

This module defines the ResourceOperation class which represents a resource operation in the
context of the App Functions SDK. A resource operation is an operation that can be performed on a
device resource.

Classes:
    ResourceOperation: Represents a resource operation. It has attributes like device_resource,
    default_value, and mappings.
"""

from dataclasses import dataclass, field

from dataclasses_json import dataclass_json


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class ResourceOperation:
    """
    Represents a resource operation.

    A resource operation is an operation that can be performed on a device resource. It has
    attributes like device_resource, default_value, and mappings.

    Attributes:
        deviceResource (str): The device resource on which the operation is performed.
        defaultValue (str): The default value for the operation.
        mappings (dict[str, str]): The mappings for the operation.
    """
    deviceResource: str = ""
    defaultValue: str = ""
    mappings: dict[str, str] = field(default_factory=dict)
