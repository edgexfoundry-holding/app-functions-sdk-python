# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The config module of the App Functions SDK Python package.

This module defines the ConfigResponse class which represents the configuration response of a
service.

Classes:
    ConfigResponse: Represents the configuration response of a service. It has attributes like
    service_name, config, and api_version.
"""

from dataclasses import dataclass, field
from typing import Any
from .base import Versionable
from ...common.constants import API_VERSION


# pylint: disable=invalid-name
@dataclass
class ConfigResponse(Versionable):
    """
    Represents the configuration response of a service.

    A ConfigResponse has attributes like service_name, config, and api_version.

    Attributes:
        serviceName (str): The name of the service.
        config (Any): The configuration of the service.
        apiVersion (str): The API version.
    """
    serviceName: str = ""
    config: Any = Any
    apiVersion: str = field(default=API_VERSION)
