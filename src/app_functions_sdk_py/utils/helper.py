# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module provides help functions
"""
import os
import base64
import json
from typing import Any, Optional, Tuple

from ..bootstrap.environment import ENV_KEY_SECURITY_SECRET_STORE
from ..contracts import errors
from ..contracts.clients.utils.common import convert_any_to_dict
from ..contracts.common import constants
from ..contracts.dtos.event import Event

value_types = [
    constants.VALUE_TYPE_BOOL, constants.VALUE_TYPE_STRING,
    constants.VALUE_TYPE_UINT8, constants.VALUE_TYPE_UINT16,
    constants.VALUE_TYPE_UINT32, constants.VALUE_TYPE_UINT64,
    constants.VALUE_TYPE_INT8, constants.VALUE_TYPE_INT16,
    constants.VALUE_TYPE_INT32, constants.VALUE_TYPE_INT64,
    constants.VALUE_TYPE_FLOAT32, constants.VALUE_TYPE_FLOAT64,
    constants.VALUE_TYPE_BINARY,
    constants.VALUE_TYPE_BOOL_ARRAY, constants.VALUE_TYPE_STRING_ARRAY,
    constants.VALUE_TYPE_UINT8_ARRAY, constants.VALUE_TYPE_UINT16_ARRAY,
    constants.VALUE_TYPE_UINT32_ARRAY, constants.VALUE_TYPE_UINT64_ARRAY,
    constants.VALUE_TYPE_INT8_ARRAY, constants.VALUE_TYPE_INT16_ARRAY,
    constants.VALUE_TYPE_INT32_ARRAY, constants.VALUE_TYPE_INT64_ARRAY,
    constants.VALUE_TYPE_FLOAT32_ARRAY, constants.VALUE_TYPE_FLOAT64_ARRAY,
    constants.VALUE_TYPE_OBJECT, constants.VALUE_TYPE_OBJECT_ARRAY,
]


def coerce_type(param: Any) -> Tuple[bytes, Optional[errors.EdgeX]]:
    """ CoerceType will accept a string, bytes, or json.Marshaller type and
    convert it to a bytes for use and consistency in the SDK """
    if isinstance(param, str):
        return param.encode(), None

    if isinstance(param, bytes):
        return param, None

    try:
        # since bytes is not JSON serializable, we should do base64 encode
        if isinstance(param, Event):
            for r in param.readings:
                if r.valueType == constants.VALUE_TYPE_BINARY:
                    r.binaryValue = base64.b64encode(r.binaryValue).decode()
        json_encoded_data = json.dumps(convert_any_to_dict(param)).encode('utf-8')
        return json_encoded_data, None
    except TypeError as e:
        return bytes(), errors.new_common_edgex(
            errors.ErrKind.CONTRACT_INVALID,
            "failed to encode input data to JSON", e)


def normalize_value_type(value_type: str) -> Tuple[str, Optional[errors.EdgeX]]:
    """ NormalizeValueType normalizes the valueType to upper camel case """
    for v in value_types:
        if value_type.casefold() == v.casefold():
            return v, None
    return "", errors.new_common_edgex(
        errors.ErrKind.CONTRACT_INVALID,
        f"unable to normalize the unknown value type {value_type}")


def is_security_enabled() -> bool:
    """ IsSecurityEnabled returns whether security is enabled """
    env = os.getenv(ENV_KEY_SECURITY_SECRET_STORE)
    return env != "false"


def delete_empty_and_trim(str_list: list[str]) -> list[str]:
    """ delete_empty_and_trim removes empty strings from a slice """
    result = []
    for s in str_list:
        s = s.strip()
        if s != "":
            result.append(s)
    return result

def is_base64_encoded(data: bytes) -> bool:
    """ is_base64_encoded checks if the input data is base64 encoded """
    # to check if incoming bytes is base64 encoded or not, we can decode, then re-encode. If the
    # re-encoded string is equal to the encoded string, then it is base64 encoded.
    try:
        return base64.b64encode(base64.b64decode(data)) == data
    except Exception:  # pylint: disable=broad-except
        # for cases where exception raised, we can assume it is not base64 encoded so return False
        return False
