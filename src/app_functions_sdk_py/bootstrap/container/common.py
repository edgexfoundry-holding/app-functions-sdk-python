#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for retrieving the common client instance from the
dependency injection container (DIC).

Functions:
    common_client_from: Queries the DIC and returns the CommonClient instance.

Constants:
    CommonClientName: The name of the CommonClient instance in the DIC.
"""

from typing import Callable, Any, Optional

from ...bootstrap.di.type import type_instance_to_name
from ...contracts.clients.common import CommonClient

# CommonClientName contains the name of the CommonClient instance in the DI container.
CommonClientName = type_instance_to_name(CommonClient)


def common_client_from(get: Callable[[str], Any]) -> Optional[CommonClient]:
    """
    common_client_from helper function queries the DI container and returns the CommonClient
    instance.
    """
    client = get(CommonClientName)
    if isinstance(client, CommonClient):
        return client
    return None
