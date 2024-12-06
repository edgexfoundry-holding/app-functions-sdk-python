#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
CoreCommand module contains the data classes for core command.
"""
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

# pylint: disable=invalid-name
@dataclass_json
@dataclass
class CoreCommandParameter:
    """
    CoreCommandParameter defines the parameter of a core command.
    """
    resourceName: str = ""
    valueType: str = ""

@dataclass_json
@dataclass
class CoreCommand:
    """
    CoreCommand defines the command details
    """
    name: str = ""
    get: bool = False
    set: bool = False
    path: str = ""
    url: str = ""
    parameters: list[CoreCommandParameter] = field(default_factory=lambda: [], init=True)

@dataclass_json
@dataclass
class DeviceCoreCommand:
    """
    DeviceCoreCommand defines the core command details for a specific device and its profiles
    """
    deviceName: str
    profileName: str
    coreCommands: list[CoreCommand] = field(default_factory=lambda: [], init=True)
