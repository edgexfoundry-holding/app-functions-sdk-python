#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for Conversion
"""
import json
from typing import Any, Tuple

from ..contracts import errors
from ..contracts.clients.utils.common import convert_any_to_dict
from ..contracts.common.constants import CONTENT_TYPE_XML, CONTENT_TYPE_JSON
from ..contracts.dtos.event import Event
from ..interfaces import AppFunctionContext

TRANSFORM_TYPE = "type"
TRANSFORM_XML = "xml"
TRANSFORM_JSON = "json"


class Conversion:
    """ Conversion convert the data from the pipeline """
    def transform_to_xml(
            self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """  TransformToXML transforms an EdgeX event to XML. It will return an error and stop
        the pipeline if a non-edgex event is received or if no data is received."""
        if data is None:
            # We didn't receive a result
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function TransformToXML in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug("Transforming to XML in pipeline '%s'", ctx.pipeline_id())

        if isinstance(data, Event):
            xml, err = data.to_xml()
            if err is not None:
                return False, errors.new_common_edgex(
                    errors.ErrKind.SERVER_ERROR,
                    f"unable to marshal Event to XML in pipeline '{ctx.pipeline_id()}'",
                    err
                )
            ctx.set_response_content_type(CONTENT_TYPE_XML)
            return True, xml
        return False, errors.new_common_edgex(
            errors.ErrKind.SERVER_ERROR,
            f"function TransformToXML in pipeline '{ctx.pipeline_id()}': unexpected type received")

    def transform_to_json(
            self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """  TransformToJSON transforms an EdgeX event to JSON. It will return an error and stop
        the pipeline if a non-edgex event is received or if no data is received."""
        if data is None:
            # We didn't receive a result
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function TransformToJSON in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug("Transforming to JSON in pipeline '%s'", ctx.pipeline_id())

        if isinstance(data, Event):
            try:
                b = json.dumps(convert_any_to_dict(data)).encode('utf-8')
            except TypeError as e:
                return False, errors.new_common_edgex(
                    errors.ErrKind.SERVER_ERROR,
                    f"unable to marshal Event to JSON in pipeline '{ctx.pipeline_id()}'",
                    e
                )

            ctx.set_response_content_type(CONTENT_TYPE_JSON)
            return True, b
        return False, errors.new_common_edgex(
            errors.ErrKind.SERVER_ERROR,
            f"function TransformToJSON in pipeline '{ctx.pipeline_id()}': unexpected type received")
