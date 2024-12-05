# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the ServiceConfig data class which encapsulates the configuration necessary for
connecting to and interacting with a Configuration service. It includes details such as the
protocol, host, port, and type of the Configuration service, as well as authentication details.
Additionally, it provides a method for constructing the service URL based on the provided
configuration.

Classes:
    ServiceConfig: A data class that holds the configuration details for connecting to a
    Configuration service.

Functions:
    GetAccessTokenCallback: A type alias for a callback function that returns an
    access token string.
"""

from typing import Callable, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse

from ..contracts.clients.interfaces.authinjector import AuthenticationInjector

GetAccessTokenCallback = Callable[[], str]
DEFAULT_PROTOCOL = "http"


@dataclass
class ServiceConfig:  # pylint: disable=too-many-instance-attributes
    """
    Defines the information need to connect to the Configuration service and optionally register
    the service

    Attributes:
        protocol (str): The Protocol that should be used to connect to the Configuration service.
        HTTP is used if not set.
        host (str): The hostname or IP address of the Configuration service.
        port (int): The HTTP port of the Configuration service.
        type (str): The implementation type of the Configuration service, i.e. keeper.
        base_path (str): the base path with in the Configuration service where the service's
        configuration is stored.
        access_token (str): The token that is used to access the service configuration.
        get_access_token (Optional[get_access_token_callback]): A callback function to retrieve a
        new access token.
        auth_injector (AuthenticationInjector): An optional mechanism for injecting authentication
        details into service requests.
        optional (dict): A dictionary for additional optional settings specific to
        the service.

    Methods:
        get_url(self) -> str:
            Constructs and returns the full URL for the service based on the protocol, host,
            and port.
    """
    protocol: str = ""
    host: str = ""
    port: int = 0
    type: str = ""
    base_path: str = ""
    access_token: str = ""
    get_access_token: Optional[GetAccessTokenCallback] = None
    auth_injector: Optional[AuthenticationInjector] = None
    optional: dict = field(default_factory=dict)

    def get_url(self) -> str:
        """
        Constructs and returns the full URL for the Configuration service.

        Returns:
            str: The full URL as a string.
        """
        return f"{self.protocol}://{self.host}:{self.port}"

    def populate_from_url(self, provider_url: str):
        """
        Populate the ServiceConfig object from the provided URL.
        """
        parsed_url = urlparse(provider_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError(f"the format of Provider URL is incorrect: {provider_url}")

        self.host = parsed_url.hostname
        try:
            self.port = parsed_url.port
        except ValueError as e:
            raise ValueError(f"the port from Provider URL is incorrect: {provider_url}") from e

        type_and_protocol = parsed_url.scheme.split('.')

        # TODO: Enforce both Type and Protocol present for release V2.0.0  # pylint: disable=fixme
        # Support for default protocol is for backwards compatibility with Fuji Device Services.
        if len(type_and_protocol) == 1:
            self.type = type_and_protocol[0]
            self.protocol = DEFAULT_PROTOCOL
        elif len(type_and_protocol) == 2:
            self.type = type_and_protocol[0]
            self.protocol = type_and_protocol[1]
        else:
            raise ValueError(
                f"the Type and Protocol spec from Provider URL is incorrect: {provider_url}")
