#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the abstract class definition for the ReadingClient.
"""
from abc import ABC, abstractmethod

from ...dtos.common.count import CountResponse
from ...dtos.responses.reading import MultiReadingsResponse


class ReadingClientABC(ABC):  #  pylint: disable=too-many-arguments
    """
    An abstract base class that defines the interface for a reading client.
    """
    @abstractmethod
    def all_readings(self, ctx: dict, offset: int, limit: int) -> MultiReadingsResponse:
        """
        An abstract method that should be implemented to get all readings.
        """

    @abstractmethod
    def reading_count(self, ctx: dict) -> CountResponse:
        """
        An abstract method that should be implemented to get the count of all readings.
        """

    @abstractmethod
    def reading_count_by_device_name(self, ctx: dict, device_name: str) -> CountResponse:
        """
        An abstract method that should be implemented to get the count of all readings by device
        name.
        """

    @abstractmethod
    def readings_by_device_name(self, ctx: dict, device_name: str, offset: int, limit: int) -> \
            MultiReadingsResponse:
        """
        An abstract method that should be implemented to get all readings by device name.
        """

    @abstractmethod
    def readings_by_resource_name(self, ctx: dict, resource_name: str, offset: int, limit: int) -> \
            MultiReadingsResponse:
        """
        An abstract method that should be implemented to get all readings by resource name.
        """

    #  pylint: disable=too-many-arguments, too-many-positional-arguments
    @abstractmethod
    def readings_by_time_range(self, ctx: dict, start: int, end: int, offset: int, limit: int) -> \
            MultiReadingsResponse:
        """
        An abstract method that should be implemented to get all readings by time range.
        """

    #  pylint: disable=too-many-positional-arguments
    @abstractmethod
    def readings_by_resource_name_and_time_range(self, ctx: dict, resource_name: str,
                                                 start: int, end: int,
                                                 offset: int, limit: int) -> MultiReadingsResponse:
        """
        An abstract method that should be implemented to get all readings by resource name and time
        range.
        """

    # pylint: disable=too-many-positional-arguments
    @abstractmethod
    def readings_by_device_name_and_resource_name(self, ctx: dict,
                                                  device_name: str, resource_name: str,
                                                  offset: int, limit: int) -> MultiReadingsResponse:
        """
        An abstract method that should be implemented to get all readings by device name and
        resource name.
        """

    # pylint: disable=too-many-positional-arguments
    @abstractmethod
    def readings_by_device_name_and_resource_name_and_time_range(self, ctx: dict,
                                                                 device_name: str,
                                                                 resource_name: str,
                                                                 start: int, end: int,
                                                                 offset: int, limit: int) -> \
            MultiReadingsResponse:
        """
        An abstract method that should be implemented to get all readings by device name and time
        range.
        """

    # pylint: disable=too-many-positional-arguments
    @abstractmethod
    def readings_by_device_name_and_resource_names_and_time_range(self, ctx: dict,
                                                                  device_name: str,
                                                                  resource_names: [str],
                                                                  start: int, end: int,
                                                                  offset: int, limit: int) -> \
            MultiReadingsResponse:
        """
        An abstract method that should be implemented to get all readings by device name and
        resource names and time range.
        """
