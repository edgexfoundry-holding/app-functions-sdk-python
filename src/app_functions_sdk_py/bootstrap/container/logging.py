#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for retrieving the logging client instance from the
dependency injection container (DIC).

Functions:
    logging_client_from: Queries the DIC and returns the Logger instance.

Constants:
    LoggingClientInterfaceName: The name of the Logger implementation in the DIC.
"""

from typing import Callable, Any, Optional

from ...bootstrap.di.type import type_instance_to_name
from ...contracts.clients.logger import Logger

# LoggingClientInterfaceName contains the name of the Logger implementation in the DIC.
LoggingClientInterfaceName = type_instance_to_name(Logger)


def logging_client_from(get: Callable[[str], Any]) -> Optional[Logger]:
    """
    logging_client_from helper function queries the DI container and returns the Logger instance.
    """
    client = get(LoggingClientInterfaceName)
    if isinstance(client, Logger):
        return client
    return None
