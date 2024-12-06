# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides the `RegistryClientABC` class, which is an abstract base class for interacting
with the registry APIs from Core Keeper.
"""

from abc import ABC, abstractmethod
from ...dtos.requests.registration import AddRegistrationRequest
from ...dtos.responses.registration import RegistrationResponse, MultiRegistrationResponse


class RegistryClientABC(ABC):
    """
    Defines the interface for interactions with the registry APIs from Core Keeper.
    """

    @abstractmethod
    def register(self, ctx: dict, req: AddRegistrationRequest):
        """
        Registers a service instance.
        """

    @abstractmethod
    def update_register(self, ctx: dict, req: AddRegistrationRequest):
        """
        Updates the registration data of the service.
        """

    @abstractmethod
    def registration_by_service_id(self, ctx: dict, service_id: str) -> RegistrationResponse:
        """
        Returns the registration data by service id.
        """

    @abstractmethod
    def all_registry(self, ctx: dict, deregistered: bool) -> MultiRegistrationResponse:
        """
        Returns the registration data of all registered service.
        """

    @abstractmethod
    def deregister(self, ctx: dict, service_id: str):
        """
        Deregisters a service by service id
        """
