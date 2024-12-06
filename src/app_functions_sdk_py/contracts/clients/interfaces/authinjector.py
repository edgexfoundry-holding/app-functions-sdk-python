# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the AuthenticationInjector abstract class for injecting authentication data
into requests within the EdgeX framework. It extends the SecureTransportProvider abstract class,
focusing on ensuring that all requests made through the secure transport layer are authenticated.

Classes:
    SecureTransportProvider: An abstract class that provides a secure transport layer.
    AuthenticationInjector: An abstract class for injecting authentication data into requests,
    extending SecureTransportProvider.
"""

from abc import abstractmethod, ABC
from urllib.request import Request
from requests.adapters import BaseAdapter


class SecureTransportProvider(ABC):  # pylint: disable=too-few-public-methods
    """
    Defines an abstract class for obtaining a secure transport adapter.
    """
    @abstractmethod
    def round_tripper(self) -> BaseAdapter:
        """
        Obtain a secure transport adapter.
        """


class AuthenticationInjector(SecureTransportProvider):
    """
    Defines an abstract class for injecting authentication data into requests for secure transport.

    This class extends the SecureTransportProvider to not only provide a secure transport layer
    but also to ensure that all requests made through this layer are authenticated. Implementing
    classes are required to define the `add_authentication_data` method, which should add the
    necessary authentication tokens or credentials to the requests before they are sent.

    Methods:
        add_authentication_data(request: Request): Abstract method to be implemented by subclasses
                                                   for adding authentication data to the request.
    """
    @abstractmethod
    def add_authentication_data(self, request: Request):
        """
        Mutates an HTTP request to add authentication data (such as an Authorization: header)
        to an outbound HTTP request.
        """
