# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The event module of the App Functions SDK Python package.

This module defines the AddEventRequest class which represents a request to add an event.

Classes:
    AddEventRequest: Represents a request to add an event. It inherits from BaseRequest and adds an
    event attribute.
"""
from dataclasses import dataclass

from dataclasses_json import dataclass_json

from ..common.base import BaseRequest
from ..event import Event

@dataclass_json
@dataclass
class AddEventRequest(BaseRequest):
    """
    Represents a request to add an event.

    An AddEventRequest inherits from BaseRequest and adds an event attribute.

    Attributes:
        event (Event): The event to be added.
    """
    event: Event = Event()

def new_add_event_request(event: Event) -> AddEventRequest:
    """ new_add_event_request creates, initializes and returns an AddEventRequests """
    req = AddEventRequest()
    req.event = event
    return req
