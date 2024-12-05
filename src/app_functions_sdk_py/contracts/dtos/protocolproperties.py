# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The protocolproperties module of the App Functions SDK Python package.

This module defines the ProtocolProperties type which is a dictionary that maps strings to any type.
This is used to represent the properties of a protocol in the context of the App Functions SDK.

Types:
    ProtocolProperties: A dictionary type that maps strings to any type.
"""

from typing import Any

ProtocolProperties = dict[str, Any]
