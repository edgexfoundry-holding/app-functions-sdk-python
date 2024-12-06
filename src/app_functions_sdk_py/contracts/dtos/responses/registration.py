#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module defines the `RegistrationResponse` and `MultiRegistrationResponse`
data transfer objects (DTOs) for handling registration responses.

Classes:
    - RegistrationResponse: Represents a response to handle a single registration.
    - MultiRegistrationResponse: Represents a response to handle multiple registrations.
"""

from dataclasses import dataclass
from typing import Optional

from ..common.base import BaseResponse, BaseWithTotalCountResponse
from ..registration import Registration


@dataclass
class RegistrationResponse(BaseResponse):
    """
    Represents a response to handle a registration.
    """
    registration: Optional[Registration] = None


@dataclass
class MultiRegistrationResponse(BaseWithTotalCountResponse):
    """
    Represents a response to handle multiple registrations.
    """
    registrations: Optional[list[Registration]] = None
