#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for ResponseData
"""
from typing import Any, Tuple

from ..contracts import errors
from ..interfaces import AppFunctionContext
from ..utils.helper import coerce_type

RESPONSE_CONTENT_TYPE = "responsecontenttype"


class ResponseData:
    # pylint: disable=too-few-public-methods
    """ ResponseData houses transform for outputting data
    to configured trigger response, i.e. message bus """

    def __init__(self, response_content_type: str):
        self.response_content_type = response_content_type

    def set_response_data(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ SetResponseData sets the response data to that passed in from the previous function """
        if data is None:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function SetResponseData in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug("Setting response data in pipeline '%s'", ctx.pipeline_id())

        byte_data, err = coerce_type(data)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        if len(self.response_content_type) > 0:
            ctx.set_response_content_type(self.response_content_type)

        # By setting this the data will be posted back
        # to configured trigger response, i.e. message bus
        ctx.set_response_data(byte_data)

        return True, data
