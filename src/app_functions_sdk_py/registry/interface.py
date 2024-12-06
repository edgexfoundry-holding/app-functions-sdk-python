#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `Client` abstract base class, which defines the interface for interactions
with the Keeper service.

Classes:
    - Client: Abstract base class that defines methods for checking service availability,
    registering, unregistering, and retrieving service endpoints.
"""

from abc import ABC, abstractmethod
from typing import List

from .keeper.client import ServiceEndpoint


class Client(ABC):
    """
    Defines the interface for interactions with the Keeper service.

    Methods:
        is_alive() -> bool:
            Checks if Keeper is up and running at the configured URL.

        register() -> None:
            Registers the current service with Keeper for discovery and health check.

        unregister() -> None:
            De-registers the current service from Keeper.

        get_service_endpoint(service_key: str) -> ServiceEndpoint:
            Retrieves the port, service ID, and host of a known endpoint from Keeper.

        get_all_service_endpoints() -> List[ServiceEndpoint]:
            Retrieves all registered endpoints from Keeper.

        is_service_available(service_key: str) -> bool:
            Checks with Keeper if the target service is registered and healthy.
    """

    @abstractmethod
    def is_alive(self) -> bool:
        """
        Simply checks if Registry is up and running at the configured URL.
        """

    @abstractmethod
    def register(self) -> None:
        """
        Registers the current service with Registry for discover and health check.
        """

    @abstractmethod
    def unregister(self) -> None:
        """
        Un-registers the current service with Registry for discover and health check
        """

    @abstractmethod
    def get_service_endpoint(self, service_key: str) -> ServiceEndpoint:
        """
        Gets the service endpoint information for the target ID from the Registry
        """

    @abstractmethod
    def get_all_service_endpoints(self) -> List[ServiceEndpoint]:
        """
        Gets all the service endpoints information from the Registry
        """

    @abstractmethod
    def is_service_available(self, service_key: str) -> bool:
        """
        Checks with the Registry if the target service is available, i.e. registered and healthy
        """
