#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for retrieving the secret provider instances from the
dependency injection container (DIC).

Functions:
    secret_provider_from: Queries the DIC and returns the SecretProvider implementation.
    secret_provider_ext_from: Queries the DIC and returns the SecretProviderExt implementation.

Constants:
    SecretProviderName: The name of the SecretProvider implementation in the DIC.
    SecretProviderExtName: The name of the SecretProviderExt implementation in the DIC.
"""

from typing import Callable, Any, Optional

from ..interface.secret import SecretProvider, SecretProviderExt
from ...bootstrap.di.type import type_instance_to_name

# SecretProviderName contains the name of the SecretProvider implementation in the DIC.
SecretProviderName = type_instance_to_name(SecretProvider)


def secret_provider_from(get: Callable[[str], Any]) -> Optional[SecretProvider]:
    """
    secret_provider_from helper function queries the DI container and returns the SecretProvider
    implementation.
    """
    provider = get(SecretProviderName)
    if isinstance(provider, SecretProvider):
        return provider
    return None


# SecretProviderExtName contains the name of the SecretProviderExt implementation in the DIC.
SecretProviderExtName = type_instance_to_name(SecretProviderExt)


def secret_provider_ext_from(get: Callable[[str], Any]) -> Optional[SecretProviderExt]:
    """
    secret_provider_ext_from helper function queries the DI container and returns the
    SecretProviderExt implementation.
    """
    provider = get(SecretProviderExtName)
    if isinstance(provider, SecretProviderExt):
        return provider
    return None
