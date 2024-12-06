# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides a utility function to decode key-value pairs into a configuration object.
"""
from typing import Any, List
from numpy import int8, int16, int32, int64, float32, float64
from ...configuration.keeper import KEY_DELIMITER, deserialize_to_dataclass
from ...contracts.dtos.kvs import KVS


def _process_key_value(p: KVS, prefix: str, raw: dict) -> tuple[str, dict]:
    """
    Processes a single key-value pair, trimming the prefix and handling nested keys.

    Parameters:
        p (KVS): The key-value storage object containing the key and value.
        prefix (str): The prefix to be trimmed from the key.
        raw (dict): The dictionary to populate with the processed key-value pair.

    Returns:
        tuple: The final key and the dictionary where the value should be stored.

    Raises:
        TypeError: If a key is found in both a dict and as a direct value.
    """
    # Trim the prefix off our key first
    key = p.key[len(prefix):] if p.key.startswith(prefix) else p.key

    # Determine what map we're writing the value to. We split by '/'
    # to determine any sub-maps that need to be created.
    m = raw
    children = key.split(KEY_DELIMITER)
    if len(children) > 0:
        key = children.pop()
        for child in children:
            if child not in m:
                m[child] = {}
            if not isinstance(m[child], dict):
                raise TypeError(f"child is both a data item and dir: {child}")
            m = m[child]
    return key, m


def decode(prefix: str, pairs: List[KVS], config_target: Any):
    """
    Decodes a list of key-value pairs into a configuration object.

    This function processes a list of KVS (key-value storage) objects, extracting their keys and
    values to populate the attributes of a given configuration target object. It supports nested
    configurations by using a delimiter(defined by KEY_DELIMITER) to indicate hierarchy in keys.

    Parameters:
        prefix (str): The prefix used to filter and trim the keys in the KVS objects.
        pairs (List[KVS]): A list of KVS objects representing the key-value pairs to be decoded.
        config_target (Any): The target object that will be populated with the decoded
        configuration data.

    Raises:
        TypeError: If a key is found in both a dict and as a direct value, or if an unsupported
        data type is encountered.
    """
    # Check if the prefix ends with the '/' char
    prefix = prefix + KEY_DELIMITER if not prefix.endswith(KEY_DELIMITER) else prefix

    m, raw = {}, {}
    for p in pairs:
        key, m = _process_key_value(p, prefix, raw)

        value = p.value
        if isinstance(value, (bool, int, int8, int16, int32, int64, float32, float64, str)):
            m[key] = value
        else:
            raise TypeError("unknown data type of the stored value")

    target_type = type(config_target)
    data_instance = deserialize_to_dataclass(raw, target_type)
    config_target.__dict__.update(data_instance.__dict__)
