# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The module defines a utility function `deserialize_to_dataclass` that takes a dictionary or a list
and a target data class, then recursively converts the input into an instance of the data class or
a list of instances if the input is a list.
This process includes handling of nested data classes and lists of data classes, making it
versatile for various configuration data formats encountered in the EdgeX framework.
"""

from dataclasses import is_dataclass, fields
from typing import Any, get_origin, get_args

from ...utils.strconv import parse_bool

KEY_DELIMITER = '/'
KEEPER_TOPIC_PREFIX = 'edgex/configs'


def deserialize_list(data: list, data_class: Any) -> list:
    """Recursively deserialize a list of items."""
    item_type = get_args(data_class)[0]
    return [deserialize_to_dataclass(item, item_type) for item in data]


def deserialize_dict(data: dict, key_type: Any, value_type: Any) -> dict:
    """Recursively deserialize a dictionary with specific key and value types."""
    deserialized_dict = {}
    for key, value in data.items():
        deserialized_key = key_type(key)
        deserialized_value = deserialize_field(value, value_type)
        deserialized_dict[deserialized_key] = deserialized_value
    return deserialized_dict


def deserialize_field(value: Any, field_type: Any) -> Any:
    """Deserialize a single field value."""
    # pylint: disable=too-many-return-statements
    if value is None:
        return value
    if is_dataclass(field_type):
        return deserialize_to_dataclass(value, field_type)
    if get_origin(field_type) is list:
        return deserialize_list(value, field_type)
    if get_origin(field_type) is dict:
        key_type, value_type = get_args(field_type)
        return deserialize_dict(value, key_type, value_type)
    if field_type is bool and isinstance(value, str):
        # Convert string to boolean is tricky in Python while both bool("False") and bool("True")
        # return True, so use custom function to handle it
        return parse_bool(value)
    try:
        # Attempt to convert value to the appropriate field type
        return field_type(value)
    except (TypeError, ValueError):
        # If direct conversion fails, treat it as a nested dataclass
        return deserialize_to_dataclass(value, field_type)


def deserialize_to_dataclass(data: dict | list, data_class: Any) -> Any:
    """
    Recursively converts a dictionary or list to a dataclass instance or list of dataclass
    instances.
    """
    if isinstance(data, list):
        return deserialize_list(data, data_class)

    if not is_dataclass(data_class):
        return data

    field_types = {f.name: f.type for f in fields(data_class)}

    # Only keep keys that exist in the dataclass
    init_values = {key: deserialize_field(value, field_types[key])
                   for key, value in data.items() if key in field_types}

    return data_class(**init_values)
