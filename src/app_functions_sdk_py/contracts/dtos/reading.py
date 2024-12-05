# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The reading module of the App Functions SDK Python package.

This module defines the BaseReading class which represents a reading in the context of the App
Functions SDK. A reading is a single data point from a device.

Classes:
    BaseReading: Represents a reading. It has attributes like reading_id, origin, device_name,
    resource_name, profile_name, value_type, units, value, and tags.
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from dataclasses_json import dataclass_json

from .tags import Tags

@dataclass_json
@dataclass
class BaseReading:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=(invalid-name
    """
    Represents a base reading.

    A reading is a single data point from a device. It has attributes like reading_id, origin,
    device_name, resource_name, profile_name, value_type, units, value, and tags.

    Attributes:
        id (str): The ID of the reading.
        origin (int): The time the reading was generated.
        deviceName (str): The name of the device that generated the reading.
        resourceName (str): The name of the resource associated with the reading.
        profileName (str): The name of the profile associated with the device.
        valueType (str): The type of the value.
        units (str): The units of the value.
        value (str): The value of the reading.
        tags (Tags): The tags associated with the reading.
    """
    id: str
    origin: int
    deviceName: str
    resourceName: str
    profileName: str
    valueType: str
    # To allow value as null (https://github.com/edgexfoundry/go-mod-core-contracts/issues/931),
    # specify value as Optional[str]
    value: Optional[str] = None
    # binaryValue is bytes or using base64 str for JSON serializable
    units: str = ""
    binaryValue: Any = None
    objectValue: Any = None
    tags: Tags = field(default_factory=lambda: {}, init=True)
    mediaType: str = ""


def new_base_reading(
        profile_name: str, device_name: str,
        resource_name: str, value_type: str, value: str) -> BaseReading:
    """ new_base_reading creates and returns a new initialized BaseReading """
    return BaseReading(
        id=str(uuid.uuid4()),
        origin=time.time_ns(),
        deviceName=device_name,
        resourceName=resource_name,
        profileName=profile_name,
        valueType=value_type,
        units="",
        tags={},
        value=value,
        binaryValue="",
        objectValue=None,
        mediaType=""
    )
