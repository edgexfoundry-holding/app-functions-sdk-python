#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for retrieving the messaging client instance from the
dependency injection container (DIC).

Functions:
    messaging_client_from: Queries the DIC and returns the MessageClient instance.

Constants:
    MessagingClientName: The name of the MessageClient instance in the DIC.
"""

from typing import Callable, Any, Optional

from ...bootstrap.di.type import type_instance_to_name
from ...interfaces.messaging import MessageClient

# MessagingClientName contains the name of the messaging client instance in the DIC.
MessagingClientName = type_instance_to_name(MessageClient)


def messaging_client_from(get: Callable[[str], Any]) -> Optional[MessageClient]:
    """
    messaging_client_from helper function queries the DIC and returns the messaging client.
    """
    client = get(MessagingClientName)
    if isinstance(client, MessageClient):
        return client
    return None
