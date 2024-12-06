# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The count module of the App Functions SDK Python package.

This module defines the CountResponse class which represents the count response of a service.

Classes:
    CountResponse: Represents the count response of a service. It inherits from BaseResponse and
    adds a count attribute.
"""

from dataclasses import dataclass

from dataclasses_json import dataclass_json

from .base import BaseResponse

@dataclass_json
@dataclass
class CountResponse(BaseResponse):  # pylint: disable=too-few-public-methods
    """
    Represents the count response of a service.

    A CountResponse inherits from BaseResponse and adds a count attribute.

    Attributes:
        count (int): The count of the response.
    """
    count: int = 0
