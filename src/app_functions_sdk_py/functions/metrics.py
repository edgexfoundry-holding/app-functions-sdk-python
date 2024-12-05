#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for Metrics
"""
from typing import Optional, Tuple, Any

from ..contracts import errors
from ..contracts.dtos import metric
from ..interfaces import AppFunctionContext


class MetricsProcessor:
    # pylint: disable=too-few-public-methods
    """ MetricsProcessor contains functions to process the Metric DTO """

    def __init__(self, additional_tags: list[metric.MetricTag]):
        self.additional_tags = additional_tags

    def to_line_protocol(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ to_line_protocol transforms a Metric DTO to a string conforming to Line Protocol syntax
         which is most commonly used with InfluxDB. For more information on Line Protocol
        see: https://docs.influxdata.com/influxdb/v2.0/reference/syntax/line-protocol/ """
        ctx.logger().debug(f"ToLineProtocol called in pipeline '{ctx.pipeline_id()}'")

        if data is None:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"function AddTags in pipeline '{ctx.pipeline_id()}': No Data Received")

        if not isinstance(data, metric.Metric):
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function ToLineProtocol in pipeline '{ctx.pipeline_id()}'"
                f", type received is not an Metric")

        if len(self.additional_tags) > 0:
            data.tags.extend(self.additional_tags)

        # New line is needed if the resulting metric data is batched
        # and sent in chunks to service like InfluxDB
        result = str(data.to_line_protocol())

        ctx.logger().debug(f"Transformed Metric to '{result}' in pipeline '{ctx.pipeline_id()}'")

        return True, result


def new_metrics_processor(additional_tags: dict) -> Tuple[MetricsProcessor, Optional[errors.EdgeX]]:
    """ new_metrics_processor creates a new MetricsProcessor with additional tags
    to add to the Metrics that are processed """
    mp = MetricsProcessor(additional_tags=[])

    for name, value in additional_tags.items():
        err = metric.validate_metric_name(name, "Tag")
        if err is not None:
            return mp, err
        tag = metric.MetricTag(name=name, value=str(value))
        mp.additional_tags.append(tag)

    return mp, None
