#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for WrapIntoEvent
"""
from typing import Tuple, Any

from ..contracts import errors
from ..contracts.common import constants
from ..contracts.dtos.event import new_event
from ..contracts.dtos.requests.event import new_add_event_request
from ..interfaces import AppFunctionContext
from ..utils.helper import coerce_type

VALUE_TYPE = "valuetype"
MEDIA_TYPE = "mediatype"
PROFILE_NAME = "profilename"
DEVICE_NAME = "devicename"
SOURCE_NAME = "sourcename"
RESOURCE_NAME = "resourcename"


class EventWrapper:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-positional-arguments
    """ EventWrapper wraps the received data as event """
    def __init__(
            self, profile_name: str, device_name: str, resource_name: str,
            value_type: str, media_type: str):
        self.profile_name = profile_name
        self.device_name = device_name
        self.resource_name = resource_name
        self.value_type = value_type
        self.media_type = media_type

    def wrap(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ wrap creates an EventRequest using the Event/Reading metadata that have been set. """
        if data is None:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function EventWrapper in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug("Creating Event...")
        event = new_event(self.profile_name, self.device_name, self.resource_name)

        match self.value_type:
            case constants.VALUE_TYPE_BINARY:
                reading, err = coerce_type(data)
                if err is not None:
                    return False, err

                event.add_binary_reading(self.resource_name, reading, self.media_type)
                if err is not None:
                    return False, err
                ctx.logger().debug("Wrap event with the binary reading value")
            case constants.VALUE_TYPE_STRING:
                reading, err = coerce_type(data)
                if err is not None:
                    return False, err

                event.add_base_reading(self.resource_name, self.value_type, str(reading))
                ctx.logger().debug("Wrap event with the string reading value")
            case constants.VALUE_TYPE_OBJECT:
                event.add_object_reading(self.resource_name, data)
                ctx.logger().debug("Wrap event with the object reading value")
            case _:
                event.add_base_reading(self.resource_name, self.value_type, str(data))
                ctx.logger().debug("Wrap event with the simple reading value")

        # unsetting content type to send back as event
        ctx.set_response_content_type("")
        ctx.add_value(PROFILE_NAME, self.profile_name)
        ctx.add_value(DEVICE_NAME, self.device_name)
        ctx.add_value(SOURCE_NAME, self.resource_name)

        # need to wrap in Add Event Request for Core Data
        # to process it if published to the MessageBus
        event_request = new_add_event_request(event)

        return True, event_request


def new_event_wrapper_binary_reading(profile_name: str, device_name: str, resource_name: str,
                                     media_type: str) -> EventWrapper:
    """ new_event_wrapper_binary_reading is provided to
    interact with EventWrapper to add a binary reading """
    return EventWrapper(
        profile_name=profile_name,
        device_name=device_name,
        resource_name=resource_name,
        value_type=constants.VALUE_TYPE_BINARY,
        media_type=media_type,
    )


def new_event_wrapper_object_reading(
        profile_name: str, device_name: str, resource_name: str) -> EventWrapper:
    """ new_event_wrapper_binary_reading is provided to
    interact with EventWrapper to add a binary reading """
    return EventWrapper(
        profile_name=profile_name,
        device_name=device_name,
        resource_name=resource_name,
        value_type=constants.VALUE_TYPE_OBJECT,
        media_type=""
    )


def new_event_wrapper_simple_reading(
        profile_name: str, device_name: str, resource_name: str, value_type: str) -> EventWrapper:
    """ new_event_wrapper_binary_reading is provided to
    interact with EventWrapper to add a binary reading """
    return EventWrapper(
        profile_name=profile_name,
        device_name=device_name,
        resource_name=resource_name,
        value_type=value_type,
        media_type="",
    )
