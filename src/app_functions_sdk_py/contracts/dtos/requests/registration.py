#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module defines the `AddRegistrationRequest` data transfer object (DTO) for handling
registration requests.

Classes:
    - AddRegistrationRequest: Represents a request to add a registration, containing a
    `Registration` object.
"""

from dataclasses import dataclass
from typing import Optional

from ..common.base import BaseRequest
from ..registration import Registration


@dataclass
class AddRegistrationRequest(BaseRequest):
    """
    Represents a request to add a registration.
    """
    registration: Optional[Registration] = None
