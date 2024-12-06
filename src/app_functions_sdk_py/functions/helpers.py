#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for registering metrics.
"""

from typing import Callable

from ..interfaces import AppFunctionContext
from ..contracts import errors


def register_metric(ctx: AppFunctionContext, full_name_func: Callable[[], str],
                    get_metric: Callable[[], any], tags: dict):
    """
    Register a metric with the metrics manager.
    """
    lc = ctx.logger()
    full_name = full_name_func()

    metrics_manager = ctx.metrics_manager()
    if metrics_manager is None:
        lc.error(f"Metrics manager not available. Unable to register {full_name} metric.")
        return

    # Only register the metric if it hasn't been registered yet.
    if not metrics_manager.is_registered(full_name):
        lc.debug(f"Registering metric {full_name}.")
        try:
            metrics_manager.register(full_name, get_metric(), tags)
        except errors.EdgeX as err:
            # In case of race condition, check again if metric was registered by another thread
            if not metrics_manager.is_registered(full_name):
                lc.error(f"Unable to register metric {full_name}. Collection will continue, "
                         f"but metric will not be reported: {str(err)}")
            return

        lc.info(f"{full_name} metric has been registered and will be reported (if enabled).")
