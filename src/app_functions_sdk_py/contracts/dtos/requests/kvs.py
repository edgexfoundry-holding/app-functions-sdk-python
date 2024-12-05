# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides the data structures necessary for creating and validating requests to update
keys in the key-value store (KVS). It defines the `UpdateKeysRequest` class, which includes methods
for validating the request data. Additionally, it contains a utility function
`update_keys_req_to_kvs` for converting an`UpdateKeysRequest` object into a `KVS` DTO, suitable for
interaction with the KVS endpoint of the core-keeper service.
"""

from dataclasses import dataclass
from typing import Any

from ..common import base
from ....contracts import errors
from ....contracts.dtos.kvs import KVS


@dataclass
class UpdateKeysRequest(base.BaseRequest):
    """
    Defines the Request Content for PUT Key DTO.
    """
    value: Any = None

    def validate(self):
        """
        Checks if the fields are valid of the UpdateKeysRequest struct
        """
        if self.value is None:
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          "the value field is undefined")
        if isinstance(self.value, dict) and len(self.value) == 0:
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          "the value field is an empty object")


def update_keys_req_to_kvs(req: UpdateKeysRequest, key: str) -> KVS:
    """
    Converts an UpdateKeysRequest object into a KVS DTO.
    """
    return KVS(key=key, value=req.value)
