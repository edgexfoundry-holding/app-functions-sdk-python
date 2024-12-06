#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
The deviceprofile module of the App Functions SDK Python package.

This module defines the `DeviceProfileClientABC` abstract base class, which specifies the interface
for interactions with the Device Profile endpoint on the EdgeX Foundry core-metadata service.

The `DeviceProfileClientABC` class includes methods for adding, updating, retrieving, and deleting
device profiles, as well as managing device resources and commands.

Classes:
    DeviceProfileClientABC: Abstract base class defining the interface for device profile
                            interactions.
"""
from abc import ABC, abstractmethod

from ...dtos.common.base import BaseWithIdResponse, BaseResponse
from ...dtos.requests.devicecommand import AddDeviceCommandRequest, UpdateDeviceCommandRequest
from ...dtos.requests.deviceprofile import DeviceProfileRequest, DeviceProfileBasicInfoRequest
from ...dtos.requests.deviceresource import AddDeviceResourceRequest, UpdateDeviceResourceRequest
from ...dtos.responses.deviceprofile import DeviceProfileResponse, MultiDeviceProfilesResponse, \
    MultiDeviceProfileBasicInfoResponse
from ...dtos.responses.deviceresource import DeviceResourceResponse


class DeviceProfileClientABC(ABC):
    """
    DeviceProfileClientABC is the interface for interacting with the EdgeX Foundry core-metadata
    """

    @abstractmethod
    def add(self, ctx: dict, reqs: [DeviceProfileRequest]) -> [BaseWithIdResponse]:
        """
        Add new device profiles to the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def update(self, ctx: dict, reqs: [DeviceProfileRequest]) -> [BaseResponse]:
        """
        Update device profiles in the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def add_by_yaml(self, ctx: dict, yaml_file_path: str) -> BaseWithIdResponse:
        """
        adds new profile by uploading a file in YAML format.
        """

    @abstractmethod
    def update_by_yaml(self, ctx: dict, yaml_file_path: str) -> BaseResponse:
        """
        updates a profile by uploading a file in YAML format.
        """

    @abstractmethod
    def delete_by_name(self, ctx: dict, name: str) -> BaseResponse:
        """
        Delete a device profile by name from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def device_profile_by_name(self, ctx: dict, name: str) -> DeviceProfileResponse:
        """
        Return a device profile by name from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def all_device_profiles(self, ctx: dict, labels: [str], offset: int, limit: int) -> \
            MultiDeviceProfilesResponse:
        """
        Return all device profiles from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def all_device_profile_basic_infos(self, ctx: dict, labels: [str], offset: int, limit: int) -> \
            MultiDeviceProfileBasicInfoResponse:
        """
        Return all device profile basic infos from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def device_profile_by_model(self, ctx: dict, model: str, offset: int, limit: int) -> \
            MultiDeviceProfilesResponse:
        """
        Return device profiles by model from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def device_profile_by_manufacturer(self, ctx: dict, manufacturer: str,
                                       offset: int, limit: int) -> MultiDeviceProfilesResponse:
        """
        Return device profiles by manufacturer from the EdgeX Foundry core-metadata service.
        """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    @abstractmethod
    def device_profile_by_manufacturer_and_model(self, ctx: dict, manufacturer: str, model: str,
                                                 offset: int, limit: int) -> (
            MultiDeviceProfilesResponse):
        """
        Return device profiles by manufacturer and model from the EdgeX Foundry core-metadata
        service.
        """

    @abstractmethod
    def device_resource_by_profile_name_and_resource_name(self, ctx: dict,
                                                          profile_name: str,
                                                          resource_name: str) -> \
            DeviceResourceResponse:
        """
        Return device resource by profile name and resource name from the EdgeX Foundry
        core-metadata service.
        """

    @abstractmethod
    def update_device_profile_basic_info(self, ctx: dict, reqs: [DeviceProfileBasicInfoRequest]) \
            -> [BaseResponse]:
        """
        Update the basic info of device profiles in the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def add_device_profile_resource(self, ctx: dict, reqs: [AddDeviceResourceRequest]) -> \
            [BaseResponse]:
        """
        Add new device resources to the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def update_device_profile_resource(self, ctx: dict, reqs: [UpdateDeviceResourceRequest]) -> [
        BaseResponse]:
        """
        Update device resources to the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def delete_device_resource_by_name(self, ctx: dict, profile_name: str, resource_name: str) -> \
            BaseResponse:
        """
        Delete a device resource by name from the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def add_device_profile_device_command(self, ctx: dict, reqs: [AddDeviceCommandRequest]) -> \
            [BaseResponse]:
        """
        Add new device commands to the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def update_device_profile_device_command(self, ctx: dict,
                                             reqs: [UpdateDeviceCommandRequest]) -> [BaseResponse]:
        """
        Update device commands to the EdgeX Foundry core-metadata service.
        """

    @abstractmethod
    def delete_device_command_by_name(self, ctx: dict, profile_name: str, command_name: str) -> \
            BaseResponse:
        """
        Delete a device command by name from the EdgeX Foundry core-metadata service.
        """
