# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The module defines a `Pair` class to encapsulate key-value pairs and a utility function
`convert_interface_to_pairs` for the conversion process. The function supports nested structures
including lists and dictionaries, making it versatile for various configuration data formats
encountered in the EdgeX framework.
"""

from dataclasses import dataclass
from typing import Any, List

from ...configuration.keeper import KEY_DELIMITER


@dataclass
class Pair:
    """
    Represents a key-value pair.

    Attributes:
        key (str): The key of the pair.
        value (str): The value of the pair.
    """
    key: str
    value: str


def convert_interface_to_pairs(path: str, interface_map: Any) -> List[Pair]:
    """
    Converts a nested interface map into a flat list of Pair objects, with keys representing the
    path.

    This function recursively traverses the interface map, which can be a combination of lists and
    dictionaries, and converts it into a flat list of Pair objects. Each Pair object represents a
    key-value pair, where the key is a string representing the path to the value in the nested
    structure.

    Parameters:
        path (str): The initial path prefix.
        interface_map (Any): The nested interface map to be converted. Can be a list, dictionary,
        or a basic data type.

    Returns:
        List[Pair]: A list of Pair objects representing the flattened key-value pairs from the
        interface map.
    """
    pairs = []

    path_pre = ""
    if path:
        path_pre = f"{path}" + KEY_DELIMITER

    if isinstance(interface_map, list):
        for index, item in enumerate(interface_map):
            next_pairs = convert_interface_to_pairs(f"{path_pre}{index}", item)
            pairs.extend(next_pairs)
    elif isinstance(interface_map, dict):
        for key, item in interface_map.items():
            next_pairs = convert_interface_to_pairs(f"{path_pre}{key}", item)
            pairs.extend(next_pairs)
    else:
        pairs.append(Pair(key=path, value=str(interface_map)))

    return pairs
