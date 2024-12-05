# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The ping module of the App Functions SDK Python package.

This module defines the PingResponse class which represents the response of a ping request.

Classes:
    PingResponse: Represents the response of a ping request. It has attributes like timestamp,
    service_name, and api_version.
"""

from dataclasses import dataclass, field
from ..common.base import Versionable
from ...common.constants import API_VERSION


# pylint: disable=invalid-name
@dataclass
class PingResponse(Versionable):
    """
    Represents the response of a ping request.

    A PingResponse has attributes like timestamp, service_name, and api_version.

    Attributes:
        timestamp (str): The timestamp of the ping response.
        serviceName (str): The name of the service.
        apiVersion (str): The API version.
    """
    timestamp: str = ""
    serviceName: str = ""
    apiVersion: str = field(default=API_VERSION)
