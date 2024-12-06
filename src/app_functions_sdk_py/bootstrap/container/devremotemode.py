#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides helper functions for retrieving the DevRemoteMode instance from the DI
container
"""
from dataclasses import dataclass
from typing import Callable, Any, Optional

from ..di.type import type_instance_to_name


@dataclass
class DevRemoteMode:
    """
    DevRemoteMode is a data class that contains the information about if the current service is
    running in development mode and if the current service is running remotely
    """
    in_dev_mode: bool
    in_remote_mode: bool


# DevRemoteModeName contains the name of the DevRemoteMode's implementation in the DIC.
DevRemoteModeName = type_instance_to_name(DevRemoteMode)  # pylint: disable=invalid-name

def dev_remote_mode_from(get: Callable[[str], Any]) -> Optional[DevRemoteMode]:
    """
    dev_remote_mode_from helper function queries the DI container and returns the DevRemoteMode
    instance.
    """
    mode = get(DevRemoteModeName)
    if isinstance(mode, DevRemoteMode):
        return mode
    return None
