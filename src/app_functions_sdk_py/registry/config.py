#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `Config` class, which defines the information needed to connect to the
registry service and optionally register the service for discovery and health checks.

Classes:
    - Config: Contains configuration details for connecting to the registry service and managing
    service registration, health checks, and service discovery.
"""

from typing import Callable, Optional

from ..contracts.clients.interfaces.authinjector import AuthenticationInjector

GetAccessTokenCallback = Callable[[], str]


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments
class Config:
    """
    Config defines the information need to connect to the registry service and optionally register
    the service for discovery and health checks.

    Attributes:
        protocol (str): The Protocol that should be used to connect to the registry service. HTTP
        is used if not set.
        host (str): Host is the hostname or IP address of the registry service.
        port (int): Port is the HTTP port of the registry service.
        service_type (str): Type is the implementation type of the registry service, i.e. consul.
        service_key (str): ServiceKey is the key identifying the service for Registration and
        building the services base configuration path.
        service_host (Optional[str]): ServiceHost is the hostname or IP address of the current
        running service using this module. May be left empty if not using registration.
        service_port (Optional[int]): ServicePort is the HTTP port of the current running service
        using this module. May be left unset if not using registration
        service_protocol (Optional[str]): The ServiceProtocol that should be used to call the
        current running service using this module. May be left empty if not using registration.
        check_route (Optional[str]): Health check callback route for the current running service
        using this module. May be left empty if not using registration.
        check_interval (Optional[str]): Health check callback interval. May be left empty if not
        using registration.
        access_token (Optional[str]): AccessToken is the optional ACL token for accessing the
        Registry. This token is only needed when the Registry has been secured with an ACL.
        get_access_token (Optional[GetAccessTokenCallback]): get_access_token is a callback
        function that retrieves a new Access Token.
        auth_injector (Optional[AuthenticationInjector]): auth_injector is an interface to obtain a
        JWT and secure transport for remote service calls
        enable_name_field_escape (bool): enable_name_field_escape indicates whether enables
        NameFieldEscape in this service The name field escape could allow the system to use special
        or Chinese characters in the different name fields, including device, profile, and so on.
        If the EnableNameFieldEscape is false, some special characters might cause system error.
        TODO: remove in EdgeX 4.0

    Functions:
        get_registry_url(self) -> str: Returns the URL of the registry service.
        get_health_check_url(self) -> str: Returns the URL for health checks.
        get_expanded_route(self, route: str) -> str: Returns the expanded route for the service.
        get_registry_protocol(self) -> str: Returns the protocol used to connect to the registry
            service.
        get_service_protocol(self) -> str: Returns the protocol used to connect to the service.
    """
    # pylint: disable=too-many-positional-arguments
    def __init__(self,
                 protocol: str = "",
                 host: str = "",
                 port: int = 0,
                 service_type: str = "",
                 service_key: str = "",
                 service_host: Optional[str] = None,
                 service_port: Optional[int] = None,
                 service_protocol: Optional[str] = None,
                 check_route: Optional[str] = None,
                 check_interval: Optional[str] = None,
                 access_token: Optional[str] = None,
                 get_access_token: Optional[GetAccessTokenCallback] = None,
                 auth_injector: Optional[AuthenticationInjector] = None,
                 enable_name_field_escape: bool = False):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.service_type = service_type
        self.service_key = service_key
        self.service_host = service_host
        self.service_port = service_port
        self.service_protocol = service_protocol
        self.check_route = check_route
        self.check_interval = check_interval
        self.access_token = access_token
        self.get_access_token = get_access_token
        self.auth_injector = auth_injector
        self.enable_name_field_escape = enable_name_field_escape

    def get_registry_url(self) -> str:
        """
        get_registry_url returns the URL of the registry service.
        """
        return f"{self.get_registry_protocol()}://{self.host}:{self.port}"

    def get_health_check_url(self) -> str:
        """
        get_health_check_url returns the URL for health checks
        """
        return self.get_expanded_route(self.check_route)

    def get_expanded_route(self, route: str) -> str:
        """
        get_expanded_route returns the expanded route for the service.
        """
        return f"{self.get_service_protocol()}://{self.service_host}:{self.service_port}{route}"

    def get_registry_protocol(self) -> str:
        """
        get_registry_protocol returns the protocol used to connect to the registry service.
        """
        return self.protocol if self.protocol else "http"

    def get_service_protocol(self) -> str:
        """
        get_service_protocol returns the protocol used to connect to the service.
        """
        return self.service_protocol if self.service_protocol else "http"
