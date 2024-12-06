#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `KeeperClient` class for interacting with the Keeper service,
which handles service registration, health checks, and service discovery.

Classes:
    - ServiceEndpoint: Represents the service information needed to connect to a target service.
    - KeeperClient: Manages interactions with the Keeper service, including service registration,
    health checks, and service discovery.
"""

from http import HTTPStatus
from abc import ABC, abstractmethod
from typing import List

from ...contracts import errors
from ...contracts.clients.common import CommonClient
from ...contracts.clients.registry import RegistryClient
from ...contracts.dtos.registration import Registration, HealthCheck
from ...contracts.dtos.requests.registration import AddRegistrationRequest
from ..config import Config

STATUS_HALT = "HALT"


class ServiceEndpoint:
    """
    ServiceEndpoint defines the service information returned by GetServiceEndpoint() need to
    connect to the target service.
    """

    def __init__(self, service_id: str, host: str, port: int):
        self.service_id = service_id
        self.host = host
        self.port = port


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


class KeeperClient(Client):
    def __init__(self, config: Config):
        self.config = config
        self.service_key = config.service_key
        self.keeper_url = config.get_registry_url()

        # service_host will be empty when client isn't registering the service
        if config.service_host != "":
            self.service_host = config.service_host
            self.service_port = config.service_port
            self.health_check_route = config.check_route
            self.health_check_interval = config.check_interval

        # Create the common and registry http clients for invoking APIs from Keeper
        self.common_client = CommonClient(self.keeper_url, config.auth_injector)
        self.registry_client = RegistryClient(self.keeper_url, config.auth_injector,
                                              config.enable_name_field_escape)

    def is_alive(self) -> bool:
        """
        is_alive simply checks if Keeper is up and running at the configured URL.
        """
        try:
            self.common_client.ping({})
            return True
        except errors.EdgeX:
            return False

    def register(self) -> None:
        """
        register registers the current service with Keeper for discovery and health check
        """
        if not all([self.service_key, self.service_host, self.service_port,
                    self.health_check_route, self.health_check_interval]):
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          "unable to register service with keeper: "
                                          "Service information not set")

        registration_req = AddRegistrationRequest(
            registration=Registration(
                serviceId=self.service_key,
                host=self.service_host,
                port=self.service_port,
                healthCheck=HealthCheck(
                    interval=self.health_check_interval,
                    path=self.health_check_route,
                    type="http"
                )
            )
        )

        # check if the service registry exists first
        resp = None
        try:
            resp = self.registry_client.registration_by_service_id({}, self.service_key)
        except errors.EdgeX as err:
            if err.http_status_code() != HTTPStatus.NOT_FOUND:
                raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                              f"failed to check the {self.service_key} "
                                              f"service registry status: {err}")

        # call the UpdateRegister to update the registry if the service already exists
        # otherwise, call Register to create a new registry
        if resp is not None and resp.statusCode == HTTPStatus.OK:
            try:
                self.registry_client.update_register({}, registration_req)
            except errors.EdgeX as err:
                raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                              f"failed to update the {self.service_key} "
                                              f"service registry: {err}")
        else:
            try:
                self.registry_client.register({}, registration_req)
            except errors.EdgeX as err:
                raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                              f"failed to register the {self.service_key} "
                                              f"service: {err}")

    def register_check(self, service_id: str, name: str, notes: str, url: str, interval: str):
        """
        keeper combines service discovery and health check into one single register request
        """
        pass

    def unregister_check(self, service_id: str):
        """
        keeper combines service discovery and health check into one single unregister request
        """
        pass

    def unregister(self) -> None:
        """
        unregister de-registers the current service from Keeper
        """
        registration_req = AddRegistrationRequest(
            registration=Registration(
                serviceId=self.service_key,
                host=self.service_host,
                port=self.service_port,
                healthCheck=HealthCheck(
                    interval=self.health_check_interval,
                    path=self.health_check_route,
                    type="http"
                ),
                status=STATUS_HALT
            )
        )

        try:
            self.registry_client.update_register({}, registration_req)
        except errors.EdgeX as err:
            raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                          f"failed to de-register the {self.service_key} "
                                          f"service: {err}")

    def get_service_endpoint(self, service_key: str) -> ServiceEndpoint:
        """
        get_service_endpoint retrieves the port, service ID and host of a known endpoint from
        Keeper. If this operation is successful and a known endpoint is found, it is returned.
        Otherwise, an error is returned.
        """
        try:
            resp = self.registry_client.registration_by_service_id({}, service_key)
        except errors.EdgeX as err:
            raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                          f"failed to get the {service_key} "
                                          f"service endpoint: {err}")

        return ServiceEndpoint(service_id=service_key, host=resp.registration.host,
                               port=resp.registration.port)

    def get_all_service_endpoints(self) -> List[ServiceEndpoint]:
        """
        get_all_service_endpoints retrieves all registered endpoints from Keeper.
        """
        try:
            resp = self.registry_client.all_registry({}, False)
        except errors.EdgeX as err:
            raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                          f"failed to get all service endpoints: {err}")

        return [ServiceEndpoint(service_id=reg.serviceId, host=reg.host, port=reg.port)
                for reg in resp.registrations]

    def is_service_available(self, service_key: str):
        """
        is_service_available checks with Keeper if the target service is registered and healthy
        """
        try:
            resp = self.registry_client.registration_by_service_id({}, service_key)
        except errors.EdgeX as err:
            raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                          f"failed to get {service_key} service registry: {err}")

        match resp.statusCode:
            case HTTPStatus.OK:
                if str.casefold(resp.registration.status) == str.casefold(STATUS_HALT):
                    raise errors.new_common_edgex(errors.ErrKind.SERVICE_UNAVAILABLE,
                                                  f"{service_key} service has been unregistered")
                if str.casefold(resp.registration.status) != "up":
                    raise errors.new_common_edgex(errors.ErrKind.SERVICE_UNAVAILABLE,
                                                    f"{service_key} service not healthy")
            case HTTPStatus.NOT_FOUND:
                raise errors.new_common_edgex(errors.ErrKind.SERVICE_UNAVAILABLE,
                                              f"{service_key} service is not registered")
            case _:
                raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                              "failed to check service availability")
