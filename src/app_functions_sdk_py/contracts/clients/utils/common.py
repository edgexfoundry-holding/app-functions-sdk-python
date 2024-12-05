# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides utility functions for URL encoding and path manipulation within
the EdgeX framework. It includes functions for encoding strings to be safely transmitted in URLs
and for constructing API endpoint paths with properly escaped special characters.
These utilities support the creation of robust and error-resistant URL paths for various services,
ensuring compatibility with web standards and client expectations.

Functions:
    url_encode(s: str) -> str:
        Encodes a string for safe transmission by escaping all special characters. This function is
        tailored for encoding strings to be used in URLs, especially useful for MQTT topics, Regex
        commands, and Redis topics which may include reserved characters.

    escape_and_join_path(api_route_path: str, *path_variables: str) -> str:
        Escapes URL special characters in path variables and joins them with the API route path.
        Useful for constructing API endpoint paths that include dynamic segments needing URL
        encoding.
"""

import urllib.parse
from typing import Any


def url_encode(s: str) -> str:
    """
    Encodes a string for safe transmission by escaping all special characters.

    This function is specifically tailored for encoding strings to be used in URLs, where certain
    characters such as '+', '-', '.', '_', and '~' have special meanings. It ensures these
    characters are properly escaped to avoid misinterpretation by web servers and clients.
    The function is particularly useful for encoding MQTT topics, Regex commands, and Redis topics
    which may include reserved characters.

    Parameters:
        s (str): The string to be URL-encoded.

    Returns:
        str: The URL-encoded version of the input string, with special characters escaped.
    """
    # In Golang url.PathEscape, ':', '@', '$', '&' are reserved characters
    res = urllib.parse.quote(s, safe=':@$&')
    res = res.replace("+", "%2B")  # MQTT topic reserved char
    res = res.replace("-", "%2D", -1)
    res = res.replace(".", "%2E", -1)  # RegexCmd and Redis topic reserved char
    res = res.replace("_", "%5F", -1)
    res = res.replace("~", "%7E", -1)
    return res


def escape_and_join_path(api_route_path: str, *path_variables: str) -> str:
    """
    Escapes URL special characters in path variables and joins them with the API route path.

    This function takes an API route path and an arbitrary number of path variables, escapes URL
    special characters in the path variables using the `url_encode` function, and then joins them
    together into a single path string. This is particularly useful for constructing API endpoint
    paths that include dynamic segments, such as IDs or names that may contain characters which
    need to be URL-encoded.

    Parameters:
        api_route_path (str): The base path of the API route.
        *path_variables (str): Variable number of path segments to be joined with the API route
        path.

    Returns:
        str: The fully constructed and escaped API path.
    """
    elements = [api_route_path] + [url_encode(e) for e in path_variables]
    return '/'.join(elements)


def convert_any_to_dict(obj: Any) -> dict[Any, dict[str, Any]] | list[dict[str, Any]] | Any:
    """
    Converts an object to a dictionary.

    This function converts an object to a dictionary by iterating over its attributes and
    recursively converting them to dictionaries. It is particularly useful for converting
    dataclasses and other complex objects to dictionaries for serialization and transmission.

    Parameters:
        obj (Any): The object to be converted to a dictionary.

    Returns:
        Dict[str, Any]: A dictionary representation of the input object.
    """
    if isinstance(obj, dict):
        return {k: convert_any_to_dict(v) for k, v in obj.items()}
    if hasattr(obj, '__dict__'):
        return {k: convert_any_to_dict(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [convert_any_to_dict(e) for e in obj]
    return obj


class PathBuilder:
    """
    A utility class for building API endpoint paths with properly escaped special characters.
    """
    def __init__(self):
        self._sb = []
        self._enable_name_field_escape = False

    def enable_name_field_escape(self, enable_name_field_escape: bool):
        """
        Enables or disables URL encoding of name fields in the path.
        """
        self._enable_name_field_escape = enable_name_field_escape
        return self

    def set_path(self, path: str):
        """
        Sets the base path of the API endpoint.
        """
        self._sb.append(path + "/")
        return self

    def set_name_field_path(self, name_path: str):
        """
        Sets a name field path segment in the API endpoint.
        """
        if self._enable_name_field_escape:
            name_path = url_encode(name_path)
        self._sb.append(name_path + "/")
        return self

    def build_path(self):
        """
        Builds and returns the final API endpoint path.
        """
        return "".join(self._sb).rstrip("/")
