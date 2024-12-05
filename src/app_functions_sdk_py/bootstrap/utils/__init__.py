# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module contains utility functions for string and dictionary manipulation,
specifically focusing on converting camel case strings to snake case and converting
dictionary keys from camel case to snake case. It provides a straightforward approach for
adapting naming conventions between different programming styles or requirements.

Functions:
    camel_to_snake(name: str) -> str:
        Converts a camel case string to snake case format by inserting underscores between words
        and converting all characters to lowercase.

    convert_dict_keys_to_snake_case(d: dict, replacements: dict = None) -> dict:
        Converts all keys in a dictionary from camel case to snake case, with an option for custom
        replacements for specific keys.

Examples:
    Converting a camel case string to snake case:
        camel_to_snake('CamelCaseString') returns 'camel_case_string'

    Converting dictionary keys to snake case:
        convert_dict_keys_to_snake_case({'CamelCaseKey': 'value'}) returns
        {'camel_case_key': 'value'}
"""
import re
from dataclasses import is_dataclass
from typing import Any, Dict, get_type_hints

from ...contracts.clients.utils.common import convert_any_to_dict

PATH_SEP = "/"


def camel_to_snake(name: str) -> str:
    """
    Converts a camel case string to snake case.

    This function takes a string in camel case format and converts it to snake case format by
    inserting underscores between words and converting all characters to lowercase.

    Parameters:
        name (str): The camel case string to be converted.

    Returns:
        str: The converted string in snake case format.
    """
    # Convert camel case to snake case for each segment around special characters
    def convert_segment(segment: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', segment)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    # Split the name by special characters
    segments = re.split('([^a-zA-Z0-9])', name)

    # Convert each segment and join them back together
    converted_segments = [convert_segment(segment)
                          if segment.isalnum() else segment for segment in segments]

    return ''.join(converted_segments)


def convert_dict_keys_to_snake_case(d: dict, replacements: dict = None) -> dict:
    """
     Converts all keys in a dictionary from camel case to snake case.

     This function iterates through a dictionary, converting all keys from camel case to
     snake case. It supports custom replacements for specific keys. If a key is present in the
     replacements dictionary, its corresponding value is used as the new key. Otherwise, the key
     is converted using the camel_to_snake function.

     Parameters:
         d (dict): The dictionary whose keys are to be converted.
         replacements (dict, optional): A dictionary of custom replacements for specific keys.
         Defaults to None.

     Returns:
         dict: A new dictionary with all keys converted to snake case.
     """
    replacements = replacements or {}
    new_dict = {}
    for key, value in d.items():
        new_key = replacements.get(key, camel_to_snake(key))
        if isinstance(value, dict):
            new_dict[new_key] = convert_dict_keys_to_snake_case(value, replacements)
        elif isinstance(value, list):
            new_dict[new_key] = [
                convert_dict_keys_to_snake_case(item, replacements)
                if isinstance(item, dict) else item for item in value
            ]
        else:
            new_dict[new_key] = value
    return new_dict

def convert_dict_keys_to_lower_camelcase(obj: dict) -> Any:
    """
    convert the dictionary key to lower camelcase
    """
    if isinstance(obj, dict):
        return {
            k[0].lower() + k[1:]: convert_dict_keys_to_lower_camelcase(v) for k, v in obj.items()}
    if hasattr(obj, '__dict__'):
        return {
            k[0].lower() + k[1:]: convert_dict_keys_to_lower_camelcase(v)
            for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [convert_dict_keys_to_lower_camelcase(e) for e in obj]
    return obj

def string_list_to_dict(src: [str]) -> dict:
    """
    Convert a list of strings to a dictionary with the strings as keys and None as values.

    Parameters:
        src ([str]): A list of strings.

    Returns:
        dict: A dictionary with the strings as keys and None as values.
    """
    result = {value: None for value in src}
    return result


def remove_unused_settings(src: Any, base_key: str,
                           used_setting_keys: dict[str, Any]) -> dict[str, Any]:
    """
    Removes unused settings from a dictionary based on a set of valid keys.

    This function converts the source object to a dictionary and removes any keys that are not
    present in the valid keys dictionary.

    Parameters:
        src (Any): The source object to be cleaned.
        base_key (str): The base key for nested dictionaries.
        used_setting_keys (dict[str, Any]): A dictionary of valid keys.

    Returns:
        dict[str, Any]: The cleaned dictionary with only valid keys.
    """
    src_dict = convert_any_to_dict(src)

    remove_unused_settings_from_dict(src_dict, base_key, used_setting_keys)

    return src_dict


def remove_unused_settings_from_dict(target: dict[str, Any], base_key: str,
                                     valid_keys: dict[str, Any]):
    """
    Helper function to recursively remove unused settings from a dictionary.

    This function iterates through a dictionary and removes any keys that are not present in the
    valid keys dictionary. It is called recursively for nested dictionaries.

    Parameters:
        target (dict[str, Any]): The target dictionary to be cleaned.
        base_key (str): The base key for nested dictionaries.
        valid_keys (dict[str, Any]): A dictionary of valid keys.
    """
    remove_keys = []
    for key, value in target.items():
        next_base_key = build_base_key(base_key, key)
        if isinstance(value, dict):
            remove_unused_settings_from_dict(value, next_base_key, valid_keys)
            if not value:
                remove_keys.append(key)
            continue
        if next_base_key not in valid_keys:
            remove_keys.append(key)

    for key in remove_keys:
        del target[key]


def build_base_key(*keys):
    """
    Builds a base key by joining multiple keys with a path separator.

    This function takes multiple keys as arguments and joins them into a single string using the
    path separator.

    Parameters:
        *keys: Multiple keys to be joined.

    Returns:
        str: The joined base key.
    """
    return PATH_SEP.join(keys)


def update_object_from_data(instance: Any, data: Dict[str, Any]):
    """
    Update the attributes of the instance with data from the data dictionary.

    This function updates the attributes of a dataclass instance with values from a dictionary.
    It performs type checking and conversion to ensure the values match the expected types.

    Parameters:
        instance (Any): The dataclass instance to be updated.
        data (Dict[str, Any]): The dictionary containing the data to update the instance with.

    Raises:
        ValueError: If the instance is not a dataclass or if the data contains incorrect types.
    """
    if not is_dataclass(instance):
        raise ValueError(f"The instance {instance} is not a dataclass")

    # Get the type hints for the instance's individual fields
    field_types = get_type_hints(instance)

    for key, value in data.items():  # pylint: disable=too-many-nested-blocks
        if key in field_types:
            expected_type = field_types[key]
            type_info = field_types.get(key)
            if isinstance(value, dict):
                if is_dataclass(expected_type): # handle the case where expected_type is dataclass
                    update_object_from_data(getattr(instance, key), value)
                else:  # handle the case where expected_type is dict[str, dataclass]
                    dict_key_type = type_info.__args__[0]
                    dict_value_type = type_info.__args__[1]
                    str_type = type(str.__name__)
                    if str_type == dict_key_type:
                        for k, v in value.items():
                            if dict_key_type and is_dataclass(dict_value_type):
                                new_value_in_type = dict_value_type(**v)
                                value[k] = new_value_in_type
                                continue
                            value[k] = dict_value_type(v)
                        getattr(instance, key).update(value)
            else:
                try:
                    setattr(instance, key, expected_type(value))
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Incorrect type for field '{key}': "
                                     f"expected {expected_type}, got {type(value)}") from e
        else:
            setattr(instance, key, value)
