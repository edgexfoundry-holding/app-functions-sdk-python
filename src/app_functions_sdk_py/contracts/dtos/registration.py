#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module defines data transfer objects (DTOs) for registration and health check functionalities.

Classes:
    - HealthCheck: Represents a health check with interval, path, and type attributes.
    - Registration: Represents a registration with serverId, status, host, port, and healthCheck
                    attributes. Inherits from DBTimestamp.
"""

from dataclasses import dataclass
from typing import Optional

from .dbtimestamp import DBTimestamp


@dataclass
class HealthCheck:
    """
    Represents a health check.
    """
    interval: str
    path: str
    type: str


# pylint: disable=invalid-name
@dataclass
class Registration(DBTimestamp):
    """
    Represents a registration.
    """
    serviceId: str = ""
    status: str = ""
    host: str = ""
    port: int = 0
    healthCheck: Optional[HealthCheck] = None
