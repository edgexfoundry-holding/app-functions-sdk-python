#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Callable


class Secrets(dict):
    """
    Represents a dictionary of secrets with string keys and values.

    This class inherits from the built-in Python dictionary (dict) and overrides the __setitem__
    method to ensure that both keys and values are strings.

    Raises:
        ValueError: If the key or value is not a string.
    """

    def __setitem__(self, key, value):
        """
        Overrides the __setitem__ method to ensure that both keys and values are strings.

        Args:
            key: The key of the secret.
            value: The value of the secret.

        Raises:
            ValueError: If the key or value is not a string.
        """
        if not isinstance(key, str):
            raise ValueError(f"Key must be a str, not {type(key).__name__}")
        if not isinstance(value, str):
            raise ValueError(f"Value must be a str, not {type(value).__name__}")
        super().__setitem__(key, value)


class SecretProvider(ABC):
    """
    An abstract base class that defines the interface for a secret provider.

    This class provides an interface for storing and retrieving secrets, checking the last update
    time of secrets, listing secret names, checking the existence of secrets, and registering or
    deregistering secret update callbacks.

    Methods:
        store_secrets(secret_name: str, secrets: Secrets): Stores secrets.
        get_secrets(secret_name: str, *secret_keys: str) -> Secrets: Retrieves secrets.
        secrets_last_updated() -> datetime: Checks the last update time of secrets.
        list_secret_names() -> List[str]: Lists secret names.
        has_secrets(secret_name: str) -> bool: Checks the existence of secrets.
        register_secret_update_callback(secret_name: str, callback: Callable[[str], None]):
        Registers a secret update callback.
        deregister_secret_update_callback(secret_name: str): Deregisters a secret update callback.
    """

    @abstractmethod
    def store_secrets(self, secret_name: str, secrets: Secrets):
        """
        Stores secrets.

        Args:
            secret_name: The name of the secret.
            secrets: The secrets to be stored.
        """

    @abstractmethod
    def get_secrets(self, secret_name: str, *secret_keys: str) -> Secrets:
        """
        Retrieves secrets.

        Args:
            secret_name: The name of the secret.
            secret_keys: The keys of the secrets to be retrieved.

        Returns:
            The retrieved secrets.
        """

    @abstractmethod
    def secrets_last_updated(self) -> datetime:
        """
        Checks the last update time of secrets.

        Returns:
            The last update time of secrets.
        """

    @abstractmethod
    def list_secret_names(self) -> List[str]:
        """
        Lists secret names.

        Returns:
            A list of secret names.
        """

    @abstractmethod
    def has_secret(self, secret_name: str) -> bool:
        """
        Checks the existence of secrets.

        Args:
            secret_name: The name of the secret.

        Returns:
            True if the secret exists, False otherwise.
        """

    @abstractmethod
    def register_secret_update_callback(self, secret_name: str, callback: Callable[[str], None]):
        """
        Registers a secret update callback.

        Args:
            secret_name: The name of the secret.
            callback: The callback to be registered.
        """

    @abstractmethod
    def deregister_secret_update_callback(self, secret_name: str):
        """
        Deregisters a secret update callback.

        Args:
            secret_name: The name of the secret.
        """


class SecretProviderExt(SecretProvider, ABC):
    """
    Defines the extended contract for secret provider implementations that provide additional APIs
    needed only from the bootstrap code.
    """

    @abstractmethod
    def secrets_updated(self):
        """
        Sets the secrets last updated time to current time.
        """

    @abstractmethod
    def get_access_token(self, token_type: str, service_key: str) -> str:
        """
        Return an access token for the specified token type and service key.
        Service key is use as the access token role which must have been previously setup.
        """

    @abstractmethod
    def secret_updated_at_secret_name(self, secret_name: str):
        """
        Performs updates and callbacks for an updated secret or secretName.
        """

    @abstractmethod
    def get_metrics_to_register(self) -> dict[str, any]:
        """
        Returns all metric objects that needs to be registered.
        """

    @abstractmethod
    def get_self_jwt(self) -> str:
        """
        Returns an encoded JWT for the current identity-based secret store token.
        """

    @abstractmethod
    def is_jwt_valid(self, jwt: str) -> bool:
        """
        Evaluates a given JWT and returns a true/false if the JWT is valid
        (i.e. belongs to us and current) or not.
        """

    @abstractmethod
    def http_transport(self):
        """
        Returns the http.RoundTripper to be used by http-based clients.
        TODO: Find the equivalent to http.RoundTripper in Python.  # pylint: disable=fixme
        """

    @abstractmethod
    def set_http_transport(self, transport):
        """
        Sets the http.RoundTripper to be used by http-based clients.
        TODO: Find the equivalent to http.RoundTripper in Python.  # pylint: disable=fixme
        """

    @abstractmethod
    def is_zero_trust_enabled(self) -> bool:
        """
        Returns whether zero trust principles are enabled.
        """

    @abstractmethod
    def enable_zero_trust(self):
        """
        Marks the provider as being zero trust enabled.
        """
