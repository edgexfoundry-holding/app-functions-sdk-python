#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `MessageBusReporter` class for reporting metrics to a message bus.

Classes:
- MessageBusReporter: Reports metrics to the EdgeX MessageBus.

Functions:
- build_metric_tags: Builds metric tags from a dictionary of tags.
"""

import json
import uuid
from copy import copy
from typing import List, Optional

from pyformance.meters.counter import Counter
from pyformance.meters.gauge import Gauge
from pyformance.meters.timer import Timer
from pyformance.meters.histogram import Histogram

from .deletable_metrics_registry import DeletableMetricsRegistry
from .gauge_float64 import GaugeFloat64
from ..interface.metrics import MetricsReporter
from ...bootstrap.container.messaging import messaging_client_from
from ...bootstrap.di.container import Container
from ...contracts.clients.logger import Logger
from ...contracts.clients.utils.common import convert_any_to_dict
from ...contracts.common import utils
from ...contracts.common import constants
from ...contracts.common.constants import CONTENT_TYPE_JSON
from ...contracts.dtos.metric import MetricTag, MetricField, new_metric
from ...interfaces import MessageEnvelope
from ...internal.common.config import TelemetryInfo
from ...contracts import errors

SERVICE_NAME_TAG_KEY = "service"
COUNTER_COUNT_NAME = "counter-count"
GAUGE_VALUE_NAME = "gauge-value"
GAUGE_FLOAT64_VALUE_NAME = "gaugeFloat64-value"
TIMER_COUNT_NAME = "timer-count"
TIMER_MEAN_NAME = "timer-mean"
TIMER_MIN_NAME = "timer-min"
TIMER_MAX_NAME = "timer-max"
TIMER_STDDEV_NAME = "timer-stddev"
TIMER_VARIANCE_NAME = "timer-variance"
HISTOGRAM_COUNT_NAME = "histogram-count"
HISTOGRAM_MEAN_NAME = "histogram-mean"
HISTOGRAM_MIN_NAME = "histogram-min"
HISTOGRAM_MAX_NAME = "histogram-max"
HISTOGRAM_STDDEV_NAME = "histogram-stddev"
HISTOGRAM_VARIANCE_NAME = "histogram-variance"


# pylint: disable=too-few-public-methods
class MessageBusReporter(MetricsReporter):
    """
    The MessageBusReporter class reports metrics to the EdgeX MessageBus.
    """
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(self, logger: Logger, base_topic: str, service_name: str, dic: Container,
                 config: TelemetryInfo):
        """
        Initializes the MessageBusReporter which reports metrics to a message bus.
        """
        self.logger = logger
        self.service_name = service_name
        self.dic = dic
        self.config = config
        self.base_metrics_topic = utils.build_topic(base_topic, constants.METRICS_PUBLISH_TOPIC,
                                                    service_name)
        self.message_client = None

    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    def report(self, registry: DeletableMetricsRegistry, metric_tags: Optional[dict]):
        """
        Collects all the current metrics and reports them to the EdgeX MessageBus.
        """
        errs = []
        published_count = 0

        # App Services create the messaging client after bootstrapping,
        # so must get it from DIC when the first time.
        if not self.message_client:
            self.message_client = messaging_client_from(self.dic.get)

        # If messaging client nil, then service hasn't set it up and can not report metrics this
        # pass. This may happen during bootstrapping if interval time is lower than time to
        # bootstrap, but will be resolved one messaging client has been added to the DIC.
        if not self.message_client:
            raise errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                "messaging client not available. Unable to report metrics")

        # Build the service tags each time we report since that can be changed in the
        # Writable config
        service_tags = []
        if self.config.Tags:
            service_tags = build_metric_tags(self.config.Tags)
        service_tags.append(MetricTag(name=SERVICE_NAME_TAG_KEY, value=self.service_name))

        # If item_name matches a configured Metric name, use the configured Metric name in case it
        # is a partial match. The metric item will have the extra name portion as a tag.
        # This is important for Metrics for App Service Pipelines, when the Metric name reported
        # need to be the same for all pipelines, but each will have to have unique name
        # (with pipeline ID added) registered. The Pipeline id will also be added as a tag.
        for item_name, item in registry.all_metrics().items():
            name, is_enabled = self.config.get_enabled_metric_name(item_name)
            if not is_enabled:
                # This metric is not enable so do not report it.
                continue

            tags = []
            tags.extend(service_tags)
            if metric_tags:
                tags.extend(build_metric_tags(metric_tags.get(item_name, {})))

            if isinstance(item, Counter):
                snapshot = copy(item)
                fields = [MetricField(name=COUNTER_COUNT_NAME, value=snapshot.get_count())]
                next_metric, err = new_metric(name, fields, tags)
            elif isinstance(item, GaugeFloat64):
                snapshot = copy(item)
                fields = [MetricField(name=GAUGE_FLOAT64_VALUE_NAME, value=snapshot.get_value())]
                next_metric, err = new_metric(name, fields, tags)
            elif isinstance(item, Gauge):
                snapshot = copy(item)
                fields = [MetricField(name=GAUGE_VALUE_NAME, value=snapshot.get_value())]
                next_metric, err = new_metric(name, fields, tags)
            elif isinstance(item, Timer):
                snapshot = copy(item)
                hist_snapshot = snapshot.get_snapshot()
                fields = [
                    MetricField(name=TIMER_COUNT_NAME, value=snapshot.get_count()),
                    MetricField(name=TIMER_MIN_NAME, value=hist_snapshot.get_min()),
                    MetricField(name=TIMER_MAX_NAME, value=hist_snapshot.get_max()),
                    MetricField(name=TIMER_MEAN_NAME, value=hist_snapshot.get_mean()),
                    MetricField(name=TIMER_STDDEV_NAME, value=hist_snapshot.get_stddev()),
                    MetricField(name=TIMER_VARIANCE_NAME, value=hist_snapshot.get_var())
                ]
                next_metric, err = new_metric(name, fields, tags)
            elif isinstance(item, Histogram):
                snapshot = item.get_snapshot()
                fields = [
                    MetricField(name=HISTOGRAM_COUNT_NAME, value=snapshot.get_count()),
                    MetricField(name=HISTOGRAM_MIN_NAME, value=snapshot.get_min()),
                    MetricField(name=HISTOGRAM_MAX_NAME, value=snapshot.get_max()),
                    MetricField(name=HISTOGRAM_MEAN_NAME, value=snapshot.get_mean()),
                    MetricField(name=HISTOGRAM_STDDEV_NAME, value=snapshot.get_stddev()),
                    MetricField(name=HISTOGRAM_VARIANCE_NAME, value=snapshot.get_var())
                ]
                next_metric, err = new_metric(name, fields, tags)
            else:
                err = errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"metric type {type(item)} not supported")
                errs.append(err)
                continue

            if err is not None:
                err = errors.new_common_edgex(
                    errors.ErrKind.SERVER_ERROR,
                    f"unable to create metric for {name}: {err}")
                errs.append(err)

            payload = json.dumps(convert_any_to_dict(next_metric)).encode('utf-8')
            message = MessageEnvelope(
                correlationID=str(uuid.uuid4()),
                payload=payload,
                contentType=CONTENT_TYPE_JSON
            )

            topic = utils.build_topic(self.base_metrics_topic, name)
            try:
                self.message_client.publish(message, topic)
            except RuntimeError as e:
                err = errors.new_common_edgex(
                    errors.ErrKind.SERVER_ERROR,
                    f"failed to publish metric {name} to topic {topic}: {e}")
                errs.append(err)
                continue
            published_count += 1

        self.logger.debug(f"Published {published_count} metrics to the "
                          f"'{self.base_metrics_topic}' base topic")
        if errs:
            flatten_errs = Exception("\n".join([str(e) for e in errs]))
            raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                          "errors occurred:", flatten_errs)


def build_metric_tags(tags: dict) -> List[MetricTag]:
    """
    Builds metric tags.
    """
    return [MetricTag(name=tag_name, value=tag_value) for tag_name, tag_value in tags.items()]
