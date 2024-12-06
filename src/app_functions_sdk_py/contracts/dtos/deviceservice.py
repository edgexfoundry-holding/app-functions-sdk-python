#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines the `DeviceService` and `UpdateDeviceService` data classes.

The `DeviceService` class represents a microservice that manages devices and their data. It includes
attributes such as id, name, description, labels, base address, and admin state.

The `UpdateDeviceService` class is used to update the attributes of an existing device service. It
includes attributes such as id, name, description, labels, base address, and admin state.

Classes:
    DeviceService: Represents a device service.
    UpdateDeviceService: Represents an update to a device service.
"""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from .dbtimestamp import DBTimestamp


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class DeviceService(DBTimestamp):
    """
    Represents a device service.

    A device service is a microservice that manages devices and their data. It has attributes like
    id, name, description, labels, base address, and admin state.

    Attributes:
        id (str): The ID of the device service.
        name (str): The name of the device service.
        description (str): A brief description of the device service.
        labels (Optional[list[str]]): A list of labels associated with the device service.
        baseAddress (str): The base address of the device service.
        adminState (str): The administrative state of the device service.
    """
    id: str = ""
    name: str = ""
    description: str = ""
    labels: Optional[list[str]] = None
    baseAddress: str = ""
    adminState: str = ""


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class UpdateDeviceService:
    """
    Represents an update to a device service.

    This class is used to update the attributes of an existing device service. It has attributes
    like id, name, description, labels, base address, and admin state.

    Attributes:
        id (str): The ID of the device service to be updated.
        name (str): The new name of the device service.
        description (str): The new description of the device service.
        labels (list[str]): The new list of labels associated with the device service.
        baseAddress (str): The new base address of the device service.
        adminState (str): The new administrative state of the device service.
    """
    id: str = ""
    name: str = ""
    description: str = ""
    labels: [str] = None
    baseAddress: str = ""
    adminState: str = ""
