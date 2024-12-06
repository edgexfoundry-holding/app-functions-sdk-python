#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Optional
from unittest.mock import MagicMock, Mock, patch
import json

from pyformance.meters import Counter, SimpleGauge, Timer, Histogram
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.bootstrap.metrics.deletable_metrics_registry import DeletableMetricsRegistry
from src.app_functions_sdk_py.bootstrap.metrics.gauge_float64 import GaugeFloat64
from src.app_functions_sdk_py.bootstrap.metrics.reporter import SERVICE_NAME_TAG_KEY, MessageBusReporter, \
    COUNTER_COUNT_NAME, GAUGE_VALUE_NAME, TIMER_COUNT_NAME, TIMER_MEAN_NAME, TIMER_MIN_NAME, TIMER_MAX_NAME, \
    TIMER_STDDEV_NAME, TIMER_VARIANCE_NAME, HISTOGRAM_COUNT_NAME, HISTOGRAM_MIN_NAME, HISTOGRAM_MAX_NAME, \
    HISTOGRAM_MEAN_NAME, HISTOGRAM_STDDEV_NAME, HISTOGRAM_VARIANCE_NAME, GAUGE_FLOAT64_VALUE_NAME
from src.app_functions_sdk_py.bootstrap.metrics.samples import UniformSample
from src.app_functions_sdk_py.contracts.common.constants import DEFAULT_BASE_TOPIC, METRICS_PUBLISH_TOPIC
from src.app_functions_sdk_py.contracts.common.utils import build_topic
from src.app_functions_sdk_py.contracts.dtos.metric import MetricTag, MetricField, Metric
from src.app_functions_sdk_py.interfaces import MessageEnvelope
from src.app_functions_sdk_py.internal.common.config import TelemetryInfo
from src.app_functions_sdk_py.internal.constants import METRICS_RESERVOIR_SIZE


class TestNewMessageBusReporter(unittest.TestCase):
    def test_new_message_bus_reporter(self):
        expected_service_name = "test-service"
        expected_base_topic = build_topic(DEFAULT_BASE_TOPIC, METRICS_PUBLISH_TOPIC, expected_service_name)

        expected_telemetry_config = TelemetryInfo(
            Interval="30s",
            Metrics={"MyMetric": True},
            Tags=None
        )

        expected_single_tag = [MetricTag(name=SERVICE_NAME_TAG_KEY, value=expected_service_name)]
        expected_multi_tags = expected_single_tag + [MetricTag(name="gateway", value="my-gateway")]

        gateway_tag = {expected_multi_tags[1].name: expected_multi_tags[1].value}

        class TestData:
            def __init__(self, name: str, expected_svc_name: str, tags: Optional[dict], expected_tags: list):
                self.name = name
                self.expected_svc_name = expected_svc_name
                self.tags = tags
                self.expected_tags = expected_tags

        tests = [
            TestData("Happy path no additional tags", expected_service_name, None, expected_single_tag),
            TestData("Happy path with additional tags", expected_service_name, gateway_tag, expected_multi_tags),
        ]

        for test in tests:
            with self.subTest(test.name):
                reporter = MessageBusReporter(
                    logger=MagicMock(),
                    base_topic=DEFAULT_BASE_TOPIC,
                    service_name=test.expected_svc_name,
                    dic=Container(),
                    config=expected_telemetry_config
                )
                self.assertIsNotNone(reporter)
                self.assertEqual(expected_service_name, reporter.service_name)
                self.assertEqual(expected_telemetry_config, reporter.config)
                self.assertEqual(expected_base_topic, reporter.base_metrics_topic)

    @patch("src.app_functions_sdk_py.bootstrap.metrics.reporter.messaging_client_from")
    def test_message_bus_reporter_report(self, mock_messaging_client_from):
        expected_service_name = "test-service"
        expected_metric_name = "test-metric"
        unexpected_metric_name = "disabled-metric"
        expected_topic = build_topic(DEFAULT_BASE_TOPIC, METRICS_PUBLISH_TOPIC, expected_service_name, expected_metric_name)

        expected_telemetry_config = TelemetryInfo(
            Interval="30s",
            Metrics={
                expected_metric_name: True,
                unexpected_metric_name: False,
            },
            Tags=None
        )

        expected_tags = [MetricTag(name=SERVICE_NAME_TAG_KEY, value=expected_service_name)]

        int_value = 50
        expected_counter_metric = Metric(
            name=expected_metric_name,
            fields=[MetricField(name=COUNTER_COUNT_NAME, value=float(int_value))],
            tags=expected_tags
        )

        reg = DeletableMetricsRegistry()

        counter = Counter("")
        counter.inc(int_value)

        disabled_counter = Counter("")
        disabled_counter.inc(int_value)
        reg.add(unexpected_metric_name, disabled_counter)

        gauge = SimpleGauge("")
        gauge.set_value(int_value)
        expected_gauge_metric = Metric(
            name=expected_metric_name,
            fields=[MetricField(name=GAUGE_VALUE_NAME, value=float(int_value))],
            tags=expected_tags
        )

        float_value = 50.55
        expected_gauge_float64_metric = Metric(
            name=expected_metric_name,
            fields=[MetricField(name=GAUGE_FLOAT64_VALUE_NAME, value=float_value)],
            tags=expected_tags
        )
        gauge_float64 = GaugeFloat64("")
        gauge_float64.set_value(float_value)

        expected_timer_metric = Metric(
            name=expected_metric_name,
            fields=[
                MetricField(name=TIMER_COUNT_NAME, value=float(0)),
                MetricField(name=TIMER_MIN_NAME, value=float(0)),
                MetricField(name=TIMER_MAX_NAME, value=float(0)),
                MetricField(name=TIMER_MEAN_NAME, value=float(0)),
                MetricField(name=TIMER_STDDEV_NAME, value=float(0)),
                MetricField(name=TIMER_VARIANCE_NAME, value=float(0)),
            ],
            tags=expected_tags
        )
        timer = Timer("", sample=UniformSample(METRICS_RESERVOIR_SIZE))

        expected_histogram_metric = Metric(
            name=expected_metric_name,
            fields=[
                MetricField(name=HISTOGRAM_COUNT_NAME, value=float(0)),
                MetricField(name=HISTOGRAM_MIN_NAME, value=float(0)),
                MetricField(name=HISTOGRAM_MAX_NAME, value=float(0)),
                MetricField(name=HISTOGRAM_MEAN_NAME, value=float(0)),
                MetricField(name=HISTOGRAM_STDDEV_NAME, value=float(0)),
                MetricField(name=HISTOGRAM_VARIANCE_NAME, value=float(0)),
            ],
            tags=expected_tags)
        histogram = Histogram("", sample=UniformSample(METRICS_RESERVOIR_SIZE))

        class TestData:
            def __init__(self, name: str, metric, expected_metric, expect_error: bool):
                self.name = name
                self.metric = metric
                self.expected_metric = expected_metric
                self.expect_error = expect_error

        tests = [
            TestData("Happy path - Counter", counter, expected_counter_metric, False),
            TestData("Happy path - Gauge", gauge, expected_gauge_metric, False),
            TestData("Happy path - GaugeFloat64", gauge_float64, expected_gauge_float64_metric, False),
            TestData("Happy path - Timer", timer, expected_timer_metric, False),
            TestData("Happy path - Histogram", histogram, expected_histogram_metric, False),
            TestData("No Metrics", None, None, False),
            TestData("Unsupported Metric", reg.meter("unsupported"), None, True),
        ]

        for test in tests:
            with self.subTest(test.name):
                mock_client = Mock()

                def publish_side_effect(*args):
                    metric_arg = args[0]
                    assert metric_arg is not None, "metricArg should not be None"

                    message = metric_arg
                    assert isinstance(message, MessageEnvelope), "metricArg should be of type MessageEnvelope"
                    actual = Metric.from_dict(json.loads(message.payload.decode("utf-8")))
                    assert actual.name == test.expected_metric.name, "Metric name mismatch"

                    actual.timestamp = test.expected_metric.timestamp

                    assert actual == test.expected_metric, "Expected metric doesn't match actual"

                    topic_arg = args[1]
                    assert topic_arg is not None, "Topic argument should not be None"
                    assert topic_arg == expected_topic, "Topic doesn't match expected value"

                mock_client.publish.side_effect = publish_side_effect

                mock_messaging_client_from.return_value = mock_client

                reporter = MessageBusReporter(logger=MagicMock(), base_topic=DEFAULT_BASE_TOPIC,
                                              service_name=expected_service_name,
                                              dic=Container(),
                                              config=expected_telemetry_config)

                if test.metric is not None:
                    try:
                        reg.add(expected_metric_name, test.metric)
                    except Exception as e:
                        self.fail(f"Failed to add metric: {e}")

                if test.expect_error:
                    with self.assertRaises(Exception):
                        reporter.report(reg, None)
                    mock_client.publish.assert_not_called()
                else:
                    try:
                        reporter.report(reg, None)
                    except Exception as e:
                        self.fail(f"Failed to report metrics: {e}")
                    if test.expected_metric is None:
                        mock_client.publish.assert_not_called()

                reg.remove(expected_metric_name)


if __name__ == "__main__":
    unittest.main()
