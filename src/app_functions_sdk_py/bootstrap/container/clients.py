#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides helper functions for retrieving the client instances from the DI container
"""
from typing import Callable, Any, Optional

from ..di.type import type_instance_to_name
from ...contracts.clients.command import CommandClient
from ...contracts.clients.device import DeviceClient
from ...contracts.clients.deviceprofile import DeviceProfileClient
from ...contracts.clients.deviceservice import DeviceServiceClient
from ...contracts.clients.event import EventClient
from ...contracts.clients.reading import ReadingClient

# EventClientName contains the name of the EventClient's implementation in the DIC.
EventClientName = type_instance_to_name(EventClient)


def event_client_from(get: Callable[[str], Any]) -> Optional[EventClient]:
    """
    event_client_from helper function queries the DI container and returns the EventClient
    instance.
    """
    client = get(EventClientName)
    if isinstance(client, EventClient):
        return client
    return None


# ReadingClientName contains the name of the ReadingClient's implementation in the DIC.
ReadingClientName = type_instance_to_name(ReadingClient)


def reading_client_from(get: Callable[[str], Any]) -> Optional[ReadingClient]:
    """
    reading_client_from helper function queries the DI container and returns the ReadingClient
    instance.
    """
    client = get(ReadingClientName)
    if isinstance(client, ReadingClient):
        return client
    return None


# CommandClientName contains the name of the CommandClient's implementation in the DIC.
CommandClientName = type_instance_to_name(CommandClient)


def command_client_from(get: Callable[[str], Any]) -> Optional[CommandClient]:
    """
    command_client_from helper function queries the DI container and returns the CommandClient
    instance.
    """
    client = get(CommandClientName)
    if isinstance(client, CommandClient):
        return client
    return None


# DeviceServiceClientName contains the name of the DeviceServiceClient's implementation in the DIC.
DeviceServiceClientName = type_instance_to_name(DeviceServiceClient)


def device_service_client_from(get: Callable[[str], Any]) -> Optional[DeviceServiceClient]:
    """
    device_service_client_from helper function queries the DI container and returns the
    DeviceServiceClient instance.
    """
    client = get(DeviceServiceClientName)
    if isinstance(client, DeviceServiceClient):
        return client
    return None


# DeviceProfileClientName contains the name of the DeviceProfileClient's implementation in the
# DIC.
DeviceProfileClientName = type_instance_to_name(DeviceProfileClient)


def device_profile_client_from(get: Callable[[str], Any]) -> Optional[DeviceProfileClient]:
    """
    device_profile_client_from helper function queries the DI container and returns the
    DeviceProfileClient instance.
    """
    client = get(DeviceProfileClientName)
    if isinstance(client, DeviceProfileClient):
        return client
    return None


# DeviceClientName contains the name of the DeviceClient's implementation in the
# DIC.
DeviceClientName = type_instance_to_name(DeviceClient)


def device_client_from(get: Callable[[str], Any]) -> Optional[DeviceClient]:
    """
    device_client_from helper function queries the DI container and returns the
    DeviceClient instance.
    """
    client = get(DeviceClientName)
    if isinstance(client, DeviceClient):
        return client
    return None
