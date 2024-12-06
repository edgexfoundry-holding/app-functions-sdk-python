#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for Metric
"""
import builtins
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

import numpy

from ...contracts import errors
from ...contracts.dtos.common.base import Versionable


@dataclass
class MetricField:
    """ MetricField defines a metric field associated with a metric """
    name: str = ""
    value: Any = None


@dataclass
class MetricTag:
    """ MetricTag defines a metric tag associated with a metric """
    name: str = ""
    value: str = ""


@dataclass
class Metric(Versionable):
    """ Metric defines the metric data for a specific named metric """
    name: str = ""
    fields: list[MetricField] = field(default_factory=lambda: [], init=True)
    tags: list[MetricTag] = field(default_factory=lambda: [], init=True)
    timestamp: int = 0

    def to_line_protocol(self) -> str:
        """ToLineProtocol transforms the Metric to Line Protocol syntax
        which is most commonly used with InfluxDB For more information on Line Protocol see:
        https://docs.influxdata.com/influxdb/v2.0/reference/syntax/line-protocol/
        Examples:

            measurementName fieldKey="field string value" 1556813561098000000
            myMeasurement,tag1=value1,tag2=value2 fieldKey="fieldValue" 1556813561098000000

        Note that this is a simple helper function for those receiving this DTO that are pushing
        metrics to an endpoint that receives"""
        fields = ""
        is_first = True
        for f in self.fields:
            # Fields section doesn't have a leading comma per syntax above so need
            # to skip the comma on the first field
            if is_first:
                is_first = False
            else:
                fields += ","
            fields += f.name + "=" + format_line_protocol_value(f.value)

        # Tags section does have a leading comma per syntax above
        tags = ""
        for tag in self.tags:
            tags += "," + tag.name + "=" + tag.value

        result = f"{self.name}{tags} {fields} {self.timestamp}"

        return result


def new_metric(name: str, fields: list[MetricField], tags: list[MetricTag]
               ) -> Tuple[Metric, Optional[errors.EdgeX]]:
    """ NewMetric creates a new metric for the specified data """
    err = validate_metric_name(name, "metric")
    if err is not None:
        return Metric(), err

    if len(fields) == 0:
        return Metric(), errors.new_common_edgex(
            errors.ErrKind.CONTRACT_INVALID,
            "one or more metric fields are required")

    for f in fields:
        err = validate_metric_name(f.name, "field")
        if err is not None:
            return Metric(), err

    for tag in tags:
        err = validate_metric_name(tag.name, "tag")
        if err is not None:
            return Metric(), err

    metric = Metric(
        name=name,
        fields=fields,
        tags=tags,
        timestamp=time.time_ns()
    )

    return metric, None


def validate_metric_name(name: str, name_type: str) -> Optional[errors.EdgeX]:
    """ validates the metric name """
    if len(name.strip()) == 0:
        return errors.new_common_edgex(
            errors.ErrKind.CONTRACT_INVALID,
            f"{name_type} name can not be empty or blank")
    return None


def format_line_protocol_value(value: Any) -> str:
    """ format the value to line protocol """
    match type(value):
        case builtins.str:
            return str(value)
        case builtins.int:
            return f"{value}i"
        case numpy.integer | numpy.int8 | numpy.int16 | numpy.int64:
            return f"{value}i"
        case numpy.uint | numpy.uint8 | numpy.uint16 | numpy.uint64:
            return f"{value}u"
        case _:
            return str(value)
