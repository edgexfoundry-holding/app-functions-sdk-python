# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines data transfer objects (DTOs) related to the key-value store (KVS).
"""

from dataclasses import dataclass
from typing import List

from ..common.base import BaseResponse
from ...dtos import kvs


@dataclass
class MultiKVResponse(BaseResponse):
    """
    MultiKVResponse defines the Response Content for GET Keys of core-keeper
    (GET /kvs/key/{key} API).
    """
    response: List[kvs.KVResponse] = None


@dataclass
class MultiKeyValueResponse(BaseResponse):
    """
    MultiKeyValueResponse defines the Response DTO for ValuesByKey HTTP client.
    This DTO is obtained from GET /kvs/key/{key} API with keyOnly is false.
    """
    response: List[kvs.KVS] = None


@dataclass
class KeysResponse(BaseResponse):
    """
    KeysResponse defines the Response Content for DELETE Keys controller of core-keeper
    (DELETE /kvs/key/{key} API).
    This DTO also defines the Response Content obtained from GET /kvs/key/{key} API with keyOnly is
    true.
    """
    response: List[kvs.KeyOnly] = None
