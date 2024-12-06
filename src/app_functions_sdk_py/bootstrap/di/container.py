#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module defines the dependency injection container for the SDK. The container is used to
manage services and their instances.

The container maintains a list of services, their constructors, and their constructed instances
in a thread-safe manner. It provides methods to update the service constructors and retrieve
constructed instances.

Classes:
    Service: Represents a service with its constructor and constructed instance.
    Container: Manages the services and their instances, ensuring thread-safe access and updates.
"""

import threading
from typing import Callable, Dict, Any

Get = Callable[[str], Any]

# ServiceConstructor defines the contract for a function/closure to create a service.
ServiceConstructor = Callable[[Get], Any]


# pylint: disable=too-few-public-methods
class Service:
    """
    Service is an internal structure used to track a specific service's constructor and
    constructed instance.
    """
    def __init__(self, constructor: ServiceConstructor):
        self.constructor = constructor
        self.instance = None


class Container:
    """
    Maintains a list of services, their constructors, and their constructed instances in a
    thread-safe manner.
    """
    def __init__(self, service_constructors: Dict[str, ServiceConstructor] = None):
        self.service_map: Dict[str, Service] = {}
        self.mutex = threading.RLock()
        if service_constructors:
            self.update(service_constructors)

    def update(self, service_constructors: Dict[str, ServiceConstructor]):
        """
        Set updates its internal service map with the contents of the provided service constructors.
        """
        with self.mutex:
            for service_name, constructor in service_constructors.items():
                self.service_map[service_name] = Service(constructor)

    def _get(self, service_name: str) -> Any:
        """
        _get looks up the requested serviceName and, if it exists, returns a constructed instance.
        If the requested service does not exist, it returns nil.  Get wraps instance construction
        in a singleton; the implementation assumes an instance, once constructed, will be reused
        and returned for all subsequent get(serviceName) calls.
        """
        service = self.service_map.get(service_name)
        if not service:
            return None
        if service.instance is None:
            service.instance = service.constructor(self.get)
            self.service_map[service_name] = service
        return service.instance

    def get(self, service_name: str) -> Any:
        """
        get wraps _get to make it thread-safe.
        """
        with self.mutex:
            return self._get(service_name)
