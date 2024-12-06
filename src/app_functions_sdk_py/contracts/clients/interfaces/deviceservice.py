#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module defines the `DeviceServiceClientABC` abstract base class, which specifies the interface
for interactions with the Device Service endpoint on the EdgeX Foundry core-metadata service.

The `DeviceServiceClientABC` class includes methods for adding, updating, retrieving, and deleting
device services.

Classes:
    DeviceServiceClientABC: Abstract base class defining the interface for device service
                            interactions.
"""
from abc import ABC, abstractmethod

from ...dtos.common.base import BaseWithIdResponse, BaseResponse
from ...dtos.requests.deviceservice import AddDeviceServiceRequest, UpdateDeviceServiceRequest
from ...dtos.responses.deviceservice import MultiDeviceServicesResponse, DeviceServiceResponse


class DeviceServiceClientABC(ABC):
    """
    DeviceServiceClientABC defines the interface for interactions with the Device Service endpoint
    on the EdgeX Foundry core-metadata service.
    """
    @abstractmethod
    def add(self, ctx: dict, reqs: [AddDeviceServiceRequest]) -> [BaseWithIdResponse]:
        """
        Add a new device service to the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def update(self, ctx: dict, reqs: [UpdateDeviceServiceRequest]) -> [BaseResponse]:
        """
        Update a device service in the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def all_device_services(self, ctx: dict, labels: [str], offset: int, limit: int) -> \
            MultiDeviceServicesResponse:
        """
        Return all device services from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def device_service_by_name(self, ctx: dict, name: str) -> DeviceServiceResponse:
        """
        Return a device service by name from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def delete_by_name(self, ctx: dict, name: str) -> BaseResponse:
        """
        Delete a device service by name from the EdgeX Foundry core-metadata service.
        """
