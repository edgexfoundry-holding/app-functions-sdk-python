#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `DeletableMetricsRegistry` class, which extends the `MetricsRegistry`
class from the `pyformance` library to allow for the removal of metrics.

Classes:
- DeletableMetricsRegistry: Extends `MetricsRegistry` to support deleting metrics by name.

Functions:
- remove: Removes a metric by name from the registry.
- all_metrics: Retrieves all metrics currently in the registry.
"""

from typing import Dict, Any

from pyformance import MetricsRegistry
from pyformance.meters import BaseMetric


class DeletableMetricsRegistry(MetricsRegistry):
    """
    DeletableMetricsRegistry extends the MetricsRegistry class from the pyformance library to
    support the removal of metrics by name.
    """

    def remove(self, name: str):
        """Remove a metric by name from the registry."""
        metric_key = BaseMetric(name)
        if metric_key in self._histograms:
            del self._histograms[metric_key]
        if metric_key in self._timers:
            del self._timers[metric_key]
        if metric_key in self._counters:
            del self._counters[metric_key]
        if metric_key in self._gauges:
            del self._gauges[metric_key]
        if metric_key in self._meters:
            del self._meters[metric_key]
        if metric_key in self._events:
            del self._events[metric_key]

    def all_metrics(self) -> Dict[str, Any]:
        """Get all metrics in the registry."""
        metrics = {}
        for base_metric, metric in self._histograms.items():
            metrics[base_metric.key] = metric
        for base_metric, metric in self._timers.items():
            metrics[base_metric.key] = metric
        for base_metric, metric in self._counters.items():
            metrics[base_metric.key] = metric
        for base_metric, metric in self._gauges.items():
            metrics[base_metric.key] = metric
        for base_metric, metric in self._meters.items():
            metrics[base_metric.key] = metric
        for base_metric, metric in self._events.items():
            metrics[base_metric.key] = metric
        return metrics

    # pylint: disable=too-many-return-statements
    def get_metric(self, name: str) -> Any:
        """Get a metric by name."""
        metric_key = BaseMetric(name)
        if metric_key in self._histograms:
            return self._histograms[metric_key]
        if metric_key in self._timers:
            return self._timers[metric_key]
        if metric_key in self._counters:
            return self._counters[metric_key]
        if metric_key in self._gauges:
            return self._gauges[metric_key]
        if metric_key in self._meters:
            return self._meters[metric_key]
        if metric_key in self._events:
            return self._events[metric_key]
        return None
