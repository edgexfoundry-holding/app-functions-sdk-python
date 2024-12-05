#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides utility functions for handling secrets.
"""
from .helper import is_security_enabled
from ..bootstrap.interface.secret import SecretProvider
from ..bootstrap.secret.secret import SecretData
from ..constants import SECRET_USERNAME_KEY, SECRET_PASSWORD_KEY, SECRET_CLIENT_KEY, \
    SECRET_CLIENT_CERT, SECRET_CA_CERT
from ..contracts import errors
from ..contracts.errors import EdgeX
from ..interfaces.messaging import AUTH_MODE_NONE, AUTH_MODE_USERNAME_PASSWORD, \
    AUTH_MODE_CLIENT_CERT, AUTH_MODE_CACERT


def get_secret_data(auth_mode: str, secret_name: str, provider: SecretProvider) -> (SecretData |
                                                                                    None,
                                                                                    EdgeX |
                                                                                    None):
    """
    Get secret data from the secret provider based on the auth mode.
    """
    # No Auth? No Problem!...No secrets required.
    if auth_mode == AUTH_MODE_NONE:
        return None, None

    secrets = provider.get_secrets(secret_name=secret_name)
    data = SecretData(
        username=secrets.get(SECRET_USERNAME_KEY, ""),
        password=secrets.get(SECRET_PASSWORD_KEY, ""),
        key_pem_block=secrets.get(SECRET_CLIENT_KEY, ""),
        cert_pem_block=secrets.get(SECRET_CLIENT_CERT, ""),
        ca_pem_block=secrets.get(SECRET_CA_CERT, ""))
    return data, None


def validate_secret_data(auth_mode: str, secret_name: str, secret_data: SecretData) -> EdgeX | None:
    """
    Validate secret data based on the auth mode.
    """
    if auth_mode == AUTH_MODE_NONE:
        return None

    if auth_mode == AUTH_MODE_USERNAME_PASSWORD:
        if is_security_enabled() and (secret_data.username == "" or secret_data.password == ""):
            return errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"{auth_mode} selected however username or password was not found for "
                f"secret={secret_name}")

    if auth_mode == AUTH_MODE_CLIENT_CERT:
        if len(secret_data.key_pem_block) <= 0 or len(secret_data.cert_pem_block) <= 0:
            return errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"{auth_mode} selected however client key or cert was not found for "
                f"secret={secret_name}")

    if auth_mode == AUTH_MODE_CACERT:
        if len(secret_data.ca_pem_block) <= 0:
            return errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"{auth_mode} selected however CA cert was not found for "
                f"secret={secret_name}")
    else:
        return errors.new_common_edgex(
            errors.ErrKind.CONTRACT_INVALID,
            f"invalid auth mode {auth_mode} selected")

    return None
