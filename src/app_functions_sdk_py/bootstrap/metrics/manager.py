#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `Manager` class for managing and reporting metrics.

Classes:
- Manager: Manages the registration, unregistration, and reporting of metrics.

Functions:
- reset_interval: Resets the interval between reporting the current metrics.
- register: Registers a metric item.
- is_registered: Checks whether a metric has been registered.
- unregister: Unregisters a metric item.
- run: Periodically reports the collected metrics using the configured `MetricsReporter`.
- get_counter: Retrieves a `Counter` metric by name.
- get_gauge: Retrieves a `Gauge` metric by name.
- get_gauge_float64: Retrieves a `GaugeFloat64` metric by name.
- get_timer: Retrieves a `Timer` metric by name.
"""

import threading
from datetime import timedelta
from typing import Optional, Any

from pyformance.meters import Counter, Gauge, Timer

from .gauge_float64 import GaugeFloat64
from ...bootstrap.interface.metrics import MetricsReporter, MetricsManager
from ...bootstrap.metrics.deletable_metrics_registry import DeletableMetricsRegistry
from ...contracts.clients.logger import Logger
from ...contracts.dtos.metric import validate_metric_name
from ...contracts import errors
from ...sync.waitgroup import WaitGroup
from ...utils.functionexitcallback import FunctionExitCallback


# pylint: disable=too-many-instance-attributes
class Manager(MetricsManager):
    """
    Manager manages the registration, unregistration, and reporting of metrics.
    """

    def __init__(self, lc: Logger, interval: timedelta, reporter: MetricsReporter):
        self._lc = lc
        self._metric_tags = {}
        self._tags_lock = threading.RLock()
        self._registry = DeletableMetricsRegistry()
        self._reporter = reporter
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread = None

    def reset_interval(self, interval: timedelta):
        """
        Reset the interval between reporting the current metrics.
        """
        self._interval = interval
        if self._thread:
            self._lc.info(f"Metrics Manager report interval changed to "
                         f"{self._interval.seconds} seconds")

    def register(self, name: str, item: Any, tags: Optional[dict]):
        """
        Register a metric item.
        """
        err = validate_metric_name(name, "metric")
        if err is not None:
            raise errors.new_common_edgex_wrapper(err)

        try:
            if tags:
                self._set_metric_tags(name, tags)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

        try:
            self._registry.add(name, item)
        except LookupError as e:
            raise errors.new_common_edgex(errors.ErrKind.STATUS_CONFLICT,
                                          "metric already exists", e)
        except TypeError as e:
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          "invalid metric type", e)

    def is_registered(self, name: str) -> bool:
        """
        Check whether a metric has been registered.
        """
        return bool(self._registry.get_metrics(name))

    def unregister(self, name: str):
        """
        Unregister a metric item.
        """
        with self._tags_lock:
            self._registry.remove(name)
            if name in self._metric_tags:
                del self._metric_tags[name]

    def run(self, ctx_done: threading.Event, wg: WaitGroup):
        """
        Periodically (based on configured interval) reports the collected metrics using the
        configured MetricsReporter.
        """
        self._stop_event.clear()
        wg.add(1)
        self._thread = threading.Thread(target=self._run_loop, args=(ctx_done, wg))
        self._thread.start()
        self._lc.info(f"Metrics Manager started with a report interval of "
                     f"{self._interval} seconds")

    def _run_loop(self, ctx_done: threading.Event, wg: WaitGroup):
        with FunctionExitCallback(wg.done):
            while not self._stop_event.is_set():
                if ctx_done.is_set():
                    self._stop_event.set()
                    if self._thread is not threading.current_thread():
                        self._thread.join()
                    self._lc.info("Exited Metrics Manager Run...")
                    return
                with self._tags_lock:
                    tags = {name: tags.copy() for name, tags in self._metric_tags.items()}

                try:
                    self._reporter.report(self._registry, tags)
                    self._lc.debug("Reported metrics...")
                except errors.EdgeX as e:
                    self._lc.error(e)
                self._stop_event.wait(self._interval.total_seconds())

    def _set_metric_tags(self, metric_name: str, tags: dict):
        for tag_name in tags.keys():
            err = validate_metric_name(tag_name, "Tag")
            if err is not None:
                raise errors.new_common_edgex_wrapper(err)

        with self._tags_lock:
            self._metric_tags[metric_name] = tags

    def get_counter(self, name: str) -> Optional[Counter]:
        """
        Retrieve the specified registered Counter.
        Return None if named item not registered or not a Counter.
        """
        metric = self._registry.get_metric(name)
        if isinstance(metric, Counter):
            return metric
        self._lc.warn(f"Metric '{name}' is not a Counter.")
        return None

    def get_gauge(self, name: str) -> Optional[Gauge]:
        """
        Retrieve the specified registered Gauge.
        Return None if named item not registered or not a Gauge.
        """
        metric = self._registry.get_metric(name)
        if isinstance(metric, Gauge):
            return metric
        self._lc.warn(f"Metric '{name}' is not a Gauge.")
        return None

    def get_gauge_float64(self, name: str) -> Optional[GaugeFloat64]:
        """
        Retrieve the specified registered GaugeFloat64.
        Return None if named item not registered or not a GaugeFloat64.
        """
        metric = self._registry.get_metric(name)
        if isinstance(metric, GaugeFloat64):
            return metric
        self._lc.warn(f"Metric '{name}' is not a GaugeFloat64.")
        return None

    def get_timer(self, name: str) -> Optional[Timer]:
        """
        Retrieve the specified registered Timer.
        Return None if named item not registered or not a
        """
        metric = self._registry.get_metric(name)
        if isinstance(metric, Timer):
            return metric
        self._lc.warn(f"Metric '{name}' is not a Timer.")
        return None
