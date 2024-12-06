#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

from urllib.request import Request

from requests.adapters import BaseAdapter

from ..interface.secret import SecretProviderExt
from ...contracts.clients.interfaces.authinjector import AuthenticationInjector


class JWTSecretProvider(AuthenticationInjector):
    """
    JWTSecretProvider inherits the AuthenticationInjector and provides the ability to add
    JWT tokens from the secret store.
    """

    def __init__(self, secret_provider: SecretProviderExt):
        self._secret_provider = secret_provider

    def add_authentication_data(self, request: Request):
        if self._secret_provider is None:
            return

        # Otherwise if there is a secret provider, get the JWT token from the secret provider
        jwt = self._secret_provider.get_self_jwt()
        # Only add authorization header if we get non-empty token back
        if len(jwt) > 0:
            request.add_header('Authorization', f'Bearer {jwt}')

    def round_tripper(self) -> BaseAdapter:
        if self._secret_provider is not None:
            return self._secret_provider.http_transport()
