#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for retrieving the metrics manager instance from the
dependency injection container (DIC).

Functions:
    metrics_manager_from: Queries the DIC and returns the MetricsManager instance.

Constants:
    MetricsManagerInterfaceName: The name of the MetricsManager instance in the DIC.
"""

from typing import Callable, Any, Optional

from ..interface.metrics import MetricsManager
from ...bootstrap.di.type import type_instance_to_name

# MetricsManagerInterfaceName contains the name of the metrics.Manager implementation in the DIC.
MetricsManagerInterfaceName = type_instance_to_name(MetricsManager)


def metrics_manager_from(get: Callable[[str], Any]) -> Optional[MetricsManager]:
    """
    metrics_manager_from helper function queries the DIC and returns the metrics.Manager
    implementation.
    """
    manager = get(MetricsManagerInterfaceName)
    if isinstance(manager, MetricsManager):
        return manager
    return None
