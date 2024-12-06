#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides utility functions for building topics for the MessageBus.
"""


def build_topic(*parts: str) -> str:
    """
    build_topic is a helper function to build MessageBus topic from multiple parts.
    """
    return "/".join(parts)
