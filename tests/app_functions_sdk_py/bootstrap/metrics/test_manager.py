#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

import logging
import threading
import unittest
from datetime import timedelta
from typing import Any
from unittest.mock import Mock, patch
import time
from threading import Event

from pyformance.meters import Counter, Gauge, Timer

from src.app_functions_sdk_py.bootstrap.metrics.gauge_float64 import GaugeFloat64
from src.app_functions_sdk_py.bootstrap.metrics.manager import Manager
from src.app_functions_sdk_py.bootstrap.metrics.reporter import MessageBusReporter
from src.app_functions_sdk_py.contracts import errors
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger
from src.app_functions_sdk_py.sync.waitgroup import WaitGroup


class TestMessageBusReporter(unittest.TestCase):
    def test_new_message_bus_reporter(self):
        logger_mock = Mock()
        expected_interval = timedelta(seconds=5)
        reporter_mock = Mock()
        m = Manager(logger_mock, expected_interval, reporter_mock)

        self.assertEqual(expected_interval, m._interval)
        self.assertEqual(logger_mock, m._lc)
        self.assertEqual(reporter_mock, m._reporter)
        self.assertIsNotNone(m._registry)
        self.assertIsNotNone(m._metric_tags)

    def test_manager_get(self):
        mock_logger = Mock()
        target = Manager(mock_logger, timedelta(seconds=5), Mock())
        name = "my-metric"

        class TestData:
            def __init__(self, case_name: str, target_type: Any, wrong_type: Any, expected: Any):
                self.name = case_name
                self.target_type = target_type
                self.wrong_type = wrong_type
                self.expected = expected

        test_cases = [
            TestData("Happy path Counter", Counter(""), None, Counter("")),
            TestData("Not registered Counter", Counter(""), None, None),
            TestData("Wrong type Counter", Counter(""), Gauge(""), None),
            TestData("Happy path Gauge", Gauge(""), None, Gauge("")),
            TestData("Not registered Gauge", Gauge(""), None, None),
            TestData("Wrong type Gauge", Gauge(""), Counter(""), None),
            TestData("Happy path GaugeFloat64", GaugeFloat64(""), None, GaugeFloat64("")),
            TestData("Not registered GaugeFloat64", GaugeFloat64(""), None, None),
            TestData("Wrong type GaugeFloat64", GaugeFloat64(""), Counter(""), None),
            TestData("Happy path Timer", Timer(""), None, Timer("")),
            TestData("Not registered Timer", Timer(""), None, None),
            TestData("Wrong type Timer", Timer(""), Counter(""), None),
        ]

        for test in test_cases:
            with self.subTest(test.name):
                if test.expected is not None:
                    target.register(name, test.expected, None)
                else:
                    target.unregister(name)

                if isinstance(test.target_type, Counter):
                    actual = target.get_counter(name)
                elif isinstance(test.target_type, Gauge):
                    actual = target.get_gauge(name)
                elif isinstance(test.target_type, GaugeFloat64):
                    actual = target.get_gauge_float64(name)
                elif isinstance(test.target_type, Timer):
                    actual = target.get_timer(name)
                else:
                    self.fail("Unexpected metric type")

                self.assertEqual(test.expected, actual)

    def test_manager_register_unregister(self):
        expected_name = "my-counter"
        expected_tags = {"my-tag": "my-value"}
        m = Manager(Mock(), timedelta(seconds=5), Mock())

        expected_metric = Counter("")
        m.register(expected_name, expected_metric, expected_tags)

        self.assertEqual(expected_metric, m._registry.get_metric(expected_name))
        self.assertEqual(expected_tags, m._metric_tags[expected_name])

        m.unregister(expected_name)
        self.assertIsNone(m._registry.get_metric(expected_name))
        self.assertIsNone(m._metric_tags.get(expected_name))

    def test_manager_register_error(self):
        m = Manager(Mock(), timedelta(seconds=5), Mock())

        # Invalid metric name
        with self.assertRaises(errors.EdgeX):
            m.register("  ", Counter(""), None)

        # Invalid Tag name
        with self.assertRaises(errors.EdgeX):
            m.register("my-counter", Counter(""), {"  ": "value"})

        # Duplicate error
        m.register("my-counter", Counter(""), None)
        with self.assertRaises(errors.EdgeX):
            m.register("my-counter", Counter(""), None)

    @patch("src.app_functions_sdk_py.bootstrap.metrics.reporter.MessageBusReporter.report")
    def test_manager_run(self, mock_report):
        reporter = MessageBusReporter(Mock(), "", "", Mock(), Mock())

        ctx_down = Event()
        wg = WaitGroup()
        m = Manager(Mock(), timedelta(milliseconds=1), reporter)

        m.run(ctx_down, wg)
        time.sleep(0.1)

        mock_report.assert_called()

        run_exited = Event()

        def stop_run():
            wg.wait()
            run_exited.set()

        threading.Thread(target=stop_run).start()

        ctx_down.set()
        time.sleep(0.1)
        self.assertTrue(run_exited.is_set())

    @patch("src.app_functions_sdk_py.contracts.clients.logger.EdgeXLogger.error")
    def test_manager_run_error(self, mock_error):
        mock_reporter = Mock()

        def report_side_effect(*args, **kwargs):
            raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR, "test error")
        mock_reporter.report.side_effect = report_side_effect

        ctx_down = Event()
        wg = WaitGroup()
        lc = EdgeXLogger("test", logging.ERROR)
        m = Manager(lc, timedelta(milliseconds=1), mock_reporter)

        m.run(ctx_down, wg)
        time.sleep(0.1)

        mock_reporter.report.assert_called()
        mock_error.assert_called()

        ctx_down.set()
        time.sleep(0.1)

    def test_manager_reset_interval(self):
        mock_reporter = Mock()
        mock_logger = Mock()

        expected = timedelta(milliseconds=1)
        m = Manager(mock_logger, expected, mock_reporter)
        self.assertEqual(expected, m._interval)

        expected = timedelta(milliseconds=5)
        m.reset_interval(expected)
        self.assertEqual(expected, m._interval)


if __name__ == '__main__':
    unittest.main()
