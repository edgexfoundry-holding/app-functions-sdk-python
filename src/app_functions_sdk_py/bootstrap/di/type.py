#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the utility function type_instance_to_name for converting an instance of a
type to a unique name, handling both regular classes and interface types.
"""

from typing import Any
import inspect


def type_instance_to_name(v: Any) -> str:
    """
    type_instance_to_name converts an instance of a type to a unique name.
    """
    t = type(v)

    if inspect.isclass(v):
        # Handle the case where v is a class type
        t = v

    # Non-interface types or regular classes
    if t.__name__:
        return f"{t.__module__}.{t.__name__}"

    # Interface types or abstract base classes
    e = t.__bases__[0]
    return f"{e.__module__}.{e.__name__}"
