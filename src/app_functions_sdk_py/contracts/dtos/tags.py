# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The tags module of the App Functions SDK Python package.

This module defines the Tags type which represents a dictionary of tags in the context of the App
Functions SDK. Tags are key-value pairs that can be associated with various entities in the SDK.

Types:
    Tags: Represents a dictionary of tags. It is a dictionary where both the keys and values are
    strings.
"""

from typing import Any

Tags = dict[str, Any]
"""
Represents a dictionary of tags.

Tags are key-value pairs that can be associated with various entities in the SDK. Both the keys and 
values are strings.
"""
