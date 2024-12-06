#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
from typing import Callable

from ..environment import get_env_var_as_bool, ENV_KEY_DISABLE_JWT_VALIDATION
from ...bootstrap.interface.secret import SecretProviderExt
from ...contracts.clients.logger import Logger
from ...utils.helper import is_security_enabled


def nil_authentication_handler_func() -> Callable:
    """
    nil_authentication_handler_func returns a HandlerFunc that does not do any authentication.
    """
    def nil_authentication_handler():
        pass
    return nil_authentication_handler


def auto_config_authentication_func(secret_provider: SecretProviderExt, lc: Logger) -> Callable:
    """
    auto_config_authentication_func auto-selects between a HandlerFunc wrapper that does
    authentication and a HandlerFunc wrapper that does not. By default, JWT validation is enabled
    in secure mode (i.e. when using a real secrets provider instead of a no-op stub)

    Set EDGEX_DISABLE_JWT_VALIDATION to 1, t, T, TRUE, true, or True to disable JWT validation.
    This might be wanted for an EdgeX adopter that wanted to only validate JWT's at the
    proxy layer, or as an escape hatch for a caller that cannot authenticate.
    """
    disable_jwt_validation, _ = get_env_var_as_bool(lc, ENV_KEY_DISABLE_JWT_VALIDATION, False)
    authentication_hook = nil_authentication_handler_func()
    if is_security_enabled() and not disable_jwt_validation:
        # TODO: Implement secret provider in milestone E
        # authentication_hook = openbao_authentication_handler_func(secret_provider, lc)
        pass
    return authentication_hook
