# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
StringValuesFormatter defines a function signature to
perform string formatting operations using an AppFunction payload.
"""
from typing import Callable, Any

from ..interfaces import AppFunctionContext

StringValuesFormatter = Callable[[str, AppFunctionContext, Any], str]


def default_string_value_formatter(str_format: str, ctx: AppFunctionContext, _: Any) -> str:
    """ returning the result of ctx.ApplyValues(format) """
    return ctx.apply_values(str_format)
