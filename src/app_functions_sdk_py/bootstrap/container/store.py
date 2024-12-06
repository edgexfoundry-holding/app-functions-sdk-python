#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for retrieving the StoreClient instance from the
dependency injection container (DIC).

Functions:
    store_client_from: Queries the DIC and returns the store client instance.

Constants:
    StoreClientInterfaceName: The name of the Store implementation in the DIC.
"""

from typing import Callable, Any, Optional

from ...bootstrap.di.type import type_instance_to_name
from ...interfaces.store import StoreClient

# StoreClientInterfaceName contains the name of the Logger implementation in the DIC.
StoreClientInterfaceName = type_instance_to_name(StoreClient)


def store_client_from(get: Callable[[str], Any]) -> Optional[StoreClient]:
    """
    store_client_from helper function queries the DI container and returns the StoreClient instance.
    """
    client = get(StoreClientInterfaceName)
    if isinstance(client, StoreClient):
        return client
    return None
