#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from datetime import timedelta
from threading import Event
from typing import Any, Optional

from pyformance import MetricsRegistry
from pyformance import meters

from ...bootstrap.metrics.gauge_float64 import GaugeFloat64
from ...sync.waitgroup import WaitGroup


class MetricsReporter(ABC):
    """
    MetricsReporter reports the metrics.
    """
    @abstractmethod
    def report(self, registry: MetricsRegistry, metric_tags: dict):
        """
        Collects all the current metrics and reports them to the EdgeX MessageBus.
        """


class MetricsManager(ABC):
    """
    MetricsManager manages a services metrics
    """

    @abstractmethod
    def reset_interval(self, interval: timedelta):
        """
        Reset the interval between reporting the current metrics.
        """

    @abstractmethod
    def register(self, name: str, item: Any, tags: Optional[dict]):
        """
        Register a metric item such as a Counter.
        """

    @abstractmethod
    def is_registered(self, name: str) -> bool:
        """
        Check whether a metric has been registered.
        """

    @abstractmethod
    def unregister(self, name: str):
        """
        Unregister a metric item such as a Counter.
        """

    @abstractmethod
    def run(self, ctx_done: Event, wg: WaitGroup):
        """
        Start the collection of metrics.
        """

    @abstractmethod
    def get_counter(self, name: str) -> Optional[meters.Counter]:
        """
        Get the counter metric with the given name.
        """

    @abstractmethod
    def get_gauge(self, name: str) -> Optional[meters.Gauge]:
        """
        Get the gauge metric with the given name.
        """

    @abstractmethod
    def get_gauge_float64(self, name: str) -> Optional[GaugeFloat64]:
        """
        Get the float64 gauge metric with the given name.
        """

    @abstractmethod
    def get_timer(self, name: str) -> Optional[meters.Timer]:
        """
        Get the timer metric with the given name.
        """
