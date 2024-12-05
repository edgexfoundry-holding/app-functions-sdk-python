# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The version module of the App Functions SDK Python package.

This module defines the VersionResponse and VersionSdkResponse classes which represent the version
information of the service and SDK respectively.

Classes:
    VersionResponse: Represents the version information of the service. It has attributes like
    service_name, version, and api_version.
    VersionSdkResponse: Represents the version information of the SDK. It inherits from
    VersionResponse and adds an sdk_version attribute.
"""

from dataclasses import dataclass, field
from ..common.base import Versionable
from ...common.constants import API_VERSION


# pylint: disable=invalid-name
@dataclass
class VersionResponse(Versionable):
    """
    Represents the version information of the service.

    A VersionResponse has attributes like service_name, version, and api_version.

    Attributes:
        serviceName (str): The name of the service.
        version (str): The version of the service.
        apiVersion (str): The API version.
    """
    serviceName: str = ""
    version: str = ""
    apiVersion: str = field(default=API_VERSION)


class VersionSdkResponse(VersionResponse):  # pylint: disable=too-few-public-methods
    """
    Represents the version information of the SDK.

    A VersionSdkResponse inherits from VersionResponse and adds an sdk_version attribute.

    Attributes:
        sdkVersion (str): The version of the SDK.
    """
    sdkVersion: str

    def __post_init__(self):
        super().__init__(self.serviceName, self.version)
