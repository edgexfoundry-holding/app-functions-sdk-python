# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The base module of the App Functions SDK Python package.

This module defines several base classes which are used as the foundation for other classes in the
SDK. These classes include Versionable, BaseRequest, BaseResponse, BaseWithIdResponse,
BaseWithTotalCountResponse, BaseWithServiceNameResponse, and BaseWithConfigResponse.

Classes:
    Versionable: Represents a versionable entity. It has an attribute api_version.
    BaseRequest: Represents a base request. It has attributes like request_id and api_version.
    BaseResponse: Represents a base response. It has attributes like request_id, message,
    status_code, and api_version.
    BaseWithIdResponse: Represents a base response with an ID. It inherits from BaseResponse and
    adds an id attribute.
    BaseWithTotalCountResponse: Represents a base response with a total count. It inherits from
    BaseResponse and adds a total_count attribute.
    BaseWithServiceNameResponse: Represents a base response with a service name. It inherits from
    BaseResponse and adds a service_name attribute.
    BaseWithConfigResponse: Represents a base response with a config. It inherits from BaseResponse
    and adds a config attribute.
"""

from dataclasses import dataclass, field
from typing import Any
import uuid

from dataclasses_json import dataclass_json

from ...common.constants import API_VERSION

@dataclass_json
@dataclass
class Versionable:
    # pylint: disable=invalid-name
    """
    Represents a versionable entity.

    A versionable entity has an attribute api_version.

    Attributes:
        apiVersion (str): The API version.
    """
    apiVersion: str = ""

# pylint: disable=invalid-name
@dataclass_json
@dataclass
class BaseRequest(Versionable):  # pylint: disable=too-few-public-methods
    """
    Represents a base request.

    A base request has attributes like request_id and api_version.

    Attributes:
        requestId (str): The ID of the request.
        apiVersion (str): The API version.
    """
    requestId: str = field(default_factory=lambda: str(uuid.uuid4()))
    apiVersion: str = field(default=API_VERSION)

@dataclass_json
@dataclass
class BaseResponse(Versionable):
    """
    Represents a base response.

    A base response has attributes like request_id, message, status_code, and api_version.

    Attributes:
        requestId (str): The ID of the request.
        message (str): The message of the response.
        statusCode (int): The status code of the response.
        apiVersion (str): The API version.
    """
    requestId: str = ""
    message: str = ""
    statusCode: int = 0
    apiVersion: str = field(default=API_VERSION)

@dataclass_json
@dataclass
class BaseWithIdResponse(BaseResponse):
    """
    Represents a base response with an ID.

    A base response with an ID inherits from BaseResponse and adds an id attribute.

    Attributes:
        id (str): The ID of the response.
    """
    id: str = ""

@dataclass_json
@dataclass
class BaseWithTotalCountResponse(BaseResponse):
    """
    Represents a base response with a total count.

    A base response with a total count inherits from BaseResponse and adds a total_count attribute.

    Attributes:
        totalCount (int): The total count of the response.
    """
    totalCount: int = 0

@dataclass_json
@dataclass
class BaseWithServiceNameResponse(BaseResponse):
    """
    Represents a base response with a service name.

    A base response with a service name inherits from BaseResponse and adds a service_name
    attribute.

    Attributes:
        serviceName (str): The service name of the response.
    """
    serviceName: str = ""

@dataclass_json
@dataclass
class BaseWithConfigResponse(BaseResponse):
    """
    Represents a base response with a config.

    A base response with a config inherits from BaseResponse and adds a config attribute.

    Attributes:
        config (Any): The config of the response.
    """
    config: Any = None
