#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
The event module of the App Functions SDK.

This module provides the EventClient abstract base class (ABC) which defines the interface for an
event client.
"""

from abc import ABC, abstractmethod

from ...dtos.common.count import CountResponse
from ...dtos.common.base import BaseResponse, BaseWithIdResponse
from ...dtos.requests.event import AddEventRequest
from ...dtos.responses.event import MultiEventsResponse


class EventClientABC(ABC):
    """
    An abstract base class that defines the interface for an event client.

    This class provides a method for adding an event.

    Methods:
        add(self, service_name: str, request: AddEventRequest): An abstract method that should be
        implemented to add an event.
    """
    @abstractmethod
    def add(self, ctx: dict, service_name: str, req: AddEventRequest) -> BaseWithIdResponse:
        """
        An abstract method that should be implemented to add an event.
        """

    @abstractmethod
    def all_events(self, ctx: dict, offset: int, limit: int) -> MultiEventsResponse:
        """
        An abstract method that should be implemented to get all events.
        """

    @abstractmethod
    def event_count(self, ctx: dict) ->  CountResponse:
        """
        An abstract method that should be implemented to get the count of all events.
        """

    @abstractmethod
    def event_count_by_device_name(self, ctx: dict, device_name: str) ->  CountResponse:
        """
        An abstract method that should be implemented to get the count of all events by device name.
        """

    @abstractmethod
    def events_by_device_name(self, ctx: dict, device_name: str, offset: int, limit: int) ->  \
            MultiEventsResponse:
        """
        An abstract method that should be implemented to get all events by device name.
        """

    @abstractmethod
    def delete_by_device_name(self, ctx: dict, device_name: str) -> BaseResponse:
        """
        An abstract method that should be implemented to delete all events by device name.
        """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    @abstractmethod
    def events_by_time_range(self, ctx: dict, start: int, end: int, offset: int, limit: int) -> \
            MultiEventsResponse:
        """
        An abstract method that should be implemented to get all events by time range
        """

    @abstractmethod
    def delete_by_age(self, ctx: dict, age: int) -> BaseResponse:
        """
        An abstract method that should be implemented to delete all events by age.
        """

    @abstractmethod
    def delete_by_id(self, ctx: dict, event_id: str) -> BaseResponse:
        """
        An abstract method that should be implemented to delete an event by its ID.
        """
