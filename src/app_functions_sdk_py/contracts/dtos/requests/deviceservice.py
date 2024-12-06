#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
The deviceservice module of the App Functions SDK Python package.
"""
from dataclasses import dataclass

from dataclasses_json import dataclass_json

from ..common.base import BaseRequest
from ..deviceservice import DeviceService, UpdateDeviceService


@dataclass_json
@dataclass
class AddDeviceServiceRequest(BaseRequest):
    """
    Represents a request to add a device service.
    """
    service: DeviceService = DeviceService()

def new_add_device_service_request(device_service: DeviceService) -> AddDeviceServiceRequest:
    """
    new_add_device_service_request creates, initializes and returns an AddDeviceServiceRequest
    """
    req = AddDeviceServiceRequest()
    req.service = device_service
    return req


@dataclass_json
@dataclass
class UpdateDeviceServiceRequest(BaseRequest):
    """
    Represents a request to add a device service.
    """
    service: UpdateDeviceService = UpdateDeviceService()

def new_update_device_service_request(device_service: UpdateDeviceService) -> \
        UpdateDeviceServiceRequest:
    """
    new_update_device_service_request creates, initializes and returns an UpdateDeviceServiceRequest
    """
    req = UpdateDeviceServiceRequest()
    req.service = device_service
    return req
