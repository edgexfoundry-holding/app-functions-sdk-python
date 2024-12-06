#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for retrieving the registry client instance from the
dependency injection container (DIC).

Functions:
    registry_from: Queries the DIC and returns the Registry Client implementation.

Constants:
    RegistryClientInterfaceName: The name of the Registry Client implementation in the DIC.
"""

from typing import Callable, Any, Optional

from ...bootstrap.di.type import type_instance_to_name
from ...registry.interface import Client

# RegistryClientInterfaceName contains the name of the Registry Client implementation in the DIC.
RegistryClientInterfaceName = type_instance_to_name(Client)


def registry_from(get: Callable[[str], Any]) -> Optional[Client]:
    """
    registry_from helper function queries the DIC and returns the Registry Client implementation.
    """
    registry_client = get(RegistryClientInterfaceName)
    if isinstance(registry_client, Client):
        return registry_client
    return None
