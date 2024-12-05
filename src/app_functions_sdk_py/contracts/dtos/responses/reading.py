#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module defines data transfer objects (DTOs) related to the reading.
"""
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from ..common.base import BaseWithTotalCountResponse, BaseResponse
from ..reading import BaseReading


@dataclass_json
@dataclass
class ReadingResponse(BaseResponse):
    """
    ReadingResponse defines the Response Content for GET reading DTO.
    """
    reading: Optional[BaseReading] = None

@dataclass_json
@dataclass
class MultiReadingsResponse(BaseWithTotalCountResponse):
    """
    MultiReadingsResponse defines the Response Content for GET multiple reading DTOs.
    """
    readings: Optional[list[BaseReading]] = None
