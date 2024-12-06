#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for Tags
"""
from typing import Any, Tuple

from ..contracts import errors
from ..contracts.dtos.event import Event
from ..interfaces import AppFunctionContext

TAGS = "tags"


class Tags:
    # pylint: disable=too-few-public-methods
    """ Tags contains the list of Tag key/values """

    def __init__(self, tags: dict):
        self.tags = tags

    def add_tags(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ add_tags adds the pre-configured list of tags to the Event's tags collection. """
        ctx.logger().debug("Adding tags to Event in pipeline '%s'", ctx.pipeline_id())

        if data is None:
            # We didn't receive a result
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"function AddTags in pipeline '{ctx.pipeline_id()}': No Data Received")

        if not isinstance(data, Event):
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function AddTags in pipeline '{ctx.pipeline_id()}': "
                f""
                f"type received is not an Event")

        if len(self.tags) > 0:
            if data.tags is None:
                data.tags = {}

            for key in self.tags.keys():
                data.tags[key] = self.tags[key]

            ctx.logger().debug(
                "Tags added to Event in pipeline '%s'. Event tags=%s",
                ctx.pipeline_id(), data.tags)
        else:
            ctx.logger().debug(
                "No tags added to Event in pipeline '%s'. Add tags list is empty.",
                ctx.pipeline_id())

        return True, data


def new_tags(tags: Any) -> Tags:
    """ new_tags creates, initializes and returns a new instance of Tags
    using generic interface values """
    return Tags(tags)
