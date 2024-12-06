#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines the abstract base class for the device client in the EdgeX Foundry core-metadata
service.

Classes:
    DeviceClientABC: Abstract base class for device client operations.
"""
from abc import abstractmethod, ABC

from ...dtos.common.base import BaseWithIdResponse, BaseResponse
from ...dtos.requests.device import AddDeviceRequest, UpdateDeviceRequest
from ...dtos.responses.device import MultiDevicesResponse, DeviceResponse


class DeviceClientABC(ABC):
    """
    DeviceClientABC is the abstract class for device client.
    """
    @abstractmethod
    def add(self, ctx: dict, reqs: [AddDeviceRequest]) -> [BaseWithIdResponse]:
        """
        Add new devices to the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def add_with_query_params(self, ctx: dict, reqs: [AddDeviceRequest], query_params: dict) -> \
            [BaseWithIdResponse]:
        """
        Add new devices to the EdgeX Foundry core-metadata service with query parameters.
        """

    @abstractmethod
    def update(self, ctx: dict, reqs: [UpdateDeviceRequest]) -> [BaseResponse]:
        """
        Update devices in the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def update_with_query_params(self, ctx: dict, reqs: [UpdateDeviceRequest],
                                 query_params: dict) -> [BaseResponse]:
        """
        Update devices to the EdgeX Foundry core-metadata service with query parameters.
        """

    @abstractmethod
    def all_devices(self, ctx: dict, labels: [str], offset: int, limit: int) -> \
            MultiDevicesResponse:
        """
        Return all devices from the EdgeX Foundry core-metadata service.
        """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    @abstractmethod
    def all_devices_with_children(self, ctx: dict, parent:str, max_levels: int,
                                  labels: [str], offset: int, limit: int) -> MultiDevicesResponse:
        """
        all_devices_with_children returns all devices who have parent, grandparent, etc. of the
        given device name. Devices can also be filtered by labels.
	    Device tree is descended at most maxLevels. If maxLevels is 0, there is no limit.
	    The result can be limited in a certain range by specifying the offset and limit parameters.
	    offset: The number of items to skip before starting to collect the result set. Default is 0.
	    limit: The number of items to return. Specify -1 will return all remaining items after
	    offset. The maximum will be the MaxResultCount as defined in the configuration of service.
	    Default is 20.
        """

    @abstractmethod
    def device_name_exists(self, ctx: dict, name: str) -> BaseResponse:
        """
        Check whether the device name exists in the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def device_by_name(self, ctx: dict, name: str) -> DeviceResponse:
        """
        Return a device by name from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def delete_device_by_name(self, ctx: dict, name: str) -> BaseResponse:
        """
        Delete a device by name from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def devices_by_profile_name(self, ctx: dict, name: str, offset:int, limit: int) -> \
            MultiDevicesResponse:
        """
        Return devices by profile name from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def devices_by_service_name(self, ctx: dict, name: str, offset:int, limit: int) -> \
            MultiDevicesResponse:
        """
        Return devices by service name from the EdgeX Foundry core-metadata service.
        """
