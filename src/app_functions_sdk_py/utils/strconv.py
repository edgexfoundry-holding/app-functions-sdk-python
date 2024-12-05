# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Utility Functions for String Conversion.

This module provides utility functions for converting strings to various data types, such as boolean
and integer, with specific handling tailored for IoT application requirements. These functions are
designed to be robust, supporting case-insensitive conversions and validating input strings to
ensure they can be accurately converted to the desired type. This module is part of the
app_functions_sdk_py package, aimed at facilitating the development of IoT applications by providing
common utility operations.

Functions:
    parse_bool(s: str) -> bool: Converts a string to a boolean value, recognizing various true and
    false representations.
    parse_int(s: str) -> int: Converts a string to an integer, raising an exception if the string
    cannot be converted.

Examples:
    To convert a string to a boolean:
        >>> parse_bool("Yes")
        True

    To convert a string to an integer:
        >>> parse_int("123")
        123

Note:
    The `parse_bool` function recognizes 'true', '1', 't', 'y', 'yes' as truthy values, and 'false',
    '0', 'f', 'n', 'no' as falsy values, case-insensitively.
    The `parse_int` function raises a ValueError if the provided string cannot be converted to an
    integer.
"""


def parse_bool(s: str) -> bool:
    """
    Convert a string to a boolean.

    This function is case-insensitive and recognizes several representations of truthy and falsy
    values. True values are 'true', '1', 't', 'y', and 'yes'. False values are 'false', '0', 'f',
    'n', and 'no'. An exception is raised if the string does not match any of these.

    Args:
        s (str): The string to convert.

    Returns:
        bool: True if the string represents a truthy value, False otherwise.

    Raises:
        ValueError: If the string cannot be recognized as either truthy or falsy.
    """

    # Define true and false str values
    true_values = {"true", "1", "t", "y", "yes"}
    false_values = {"false", "0", "f", "n", "no"}

    # Convert the string to lowercase to make the function case-insensitive
    lower_s = s.lower()

    if lower_s in true_values:
        return True

    if lower_s in false_values:
        return False

    raise ValueError(f"Cannot convert '{s}' to boolean")


def parse_int(s: str) -> int:
    """
    Convert a string to an integer.

    This function attempts to convert the given string into an integer. It raises an exception if
    the string cannot be converted, for example, if the string contains non-numeric characters
    (excluding leading and trailing whitespace, which are ignored).

    Args:
        s (str): The string to convert.

    Returns:
        int: The integer representation of the string.

    Raises:
        ValueError: If the string cannot be converted to an integer.
    """
    try:
        return int(s)
    except ValueError as ve:
        raise ValueError(f"Cannot convert '{s}' to integer") from ve


def join_str(strings: list, sep: str) -> str:
    """
    Concatenates multiple strings into a single string, with a specified separator between each.

    Parameters:
        strings (list): A list of strings to concatenate.
        sep (str): The separator string to place between each individual string.

    Returns:
        str: The concatenated string with separators.
    """
    return sep.join(strings)
