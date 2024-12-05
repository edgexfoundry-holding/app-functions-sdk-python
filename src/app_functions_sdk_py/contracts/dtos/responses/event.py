#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines data transfer objects (DTOs) related to the event.
"""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from ..common.base import BaseWithTotalCountResponse, BaseResponse
from ..event import Event

@dataclass_json
@dataclass
class EventResponse(BaseResponse):
    """
    EventResponse defines the Response Content for GET Event DTO.
    """
    event: Optional[Event] = None

@dataclass_json
@dataclass
class MultiEventsResponse(BaseWithTotalCountResponse):
    """
    MultiEventsResponse defines the Response Content for GET multiple event DTOs.
    """
    events: Optional[list[Event]] = None
