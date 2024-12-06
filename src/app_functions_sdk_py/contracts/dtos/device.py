# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The device module of the App Functions SDK Python package.

This module defines the Device class which represents a device in the context of the App Functions
SDK. A device is an entity that generates data.

Classes:
    Device: Represents a device. It has attributes like device_id, name, parent, description,
    admin_state, operating_state, labels, location, service_name, profile_name, auto_events,
    protocols, tags, and properties.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from dataclasses_json import dataclass_json

from .autoevent import AutoEvent
from .dbtimestamp import DBTimestamp
from .protocolproperties import ProtocolProperties
from .tags import Tags


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class Device(DBTimestamp):  # pylint: disable=too-many-instance-attributes
    """
    Represents a device.
    """
    id: Optional[str] = None
    name: str = ""
    parent: Optional[str] = None
    description: Optional[str] = None
    adminState: str = ""
    operatingState: str = ""
    labels: Optional[list[str]] = None
    location: Optional[Any] = None
    serviceName: str = ""
    profileName: Optional[str] = None
    autoEvents: Optional[list[AutoEvent]] = None
    protocols: dict[str, ProtocolProperties] = field(default_factory=dict)
    tags: Optional[Tags] = None
    properties: Optional[dict[str, Any]] = None

# pylint: disable=invalid-name
@dataclass_json
@dataclass
class UpdateDevice:  # pylint: disable=too-many-instance-attributes
    """
    Represents a device for update.
    """
    id: Optional[str] = None
    name: str = ""
    parent: Optional[str] = None
    description: Optional[str] = None
    adminState: Optional[str] = None
    operatingState: Optional[str] = None
    labels: Optional[list[str]] = None
    location: Optional[Any] = None
    serviceName: Optional[str] = None
    profileName: Optional[str] = None
    autoEvents: Optional[list[AutoEvent]] = None
    protocols: dict[str, ProtocolProperties] = field(default_factory=dict)
    tags: Optional[Tags] = None
    properties: Optional[dict[str, Any]] = None
