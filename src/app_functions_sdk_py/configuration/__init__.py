# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
    This module provides a function to create a new configuration client based on the specified
    service configuration.
"""

from ..configuration.interfaces.configuration import ConfigurationClient
from .keeper.client import new_keeper_client
from .config import ServiceConfig


def new_configuration_client(svc_config: ServiceConfig) -> ConfigurationClient:
    """
    Creates a new configuration client based on the specified service configuration.

    This function determines the type of configuration client to create based on the `type`
    attribute of the provided `ServiceConfig` object. Currently, it supports creating a "keeper"
    type configuration client. If the `host` or `port` in the `ServiceConfig` is not set, or if an
    unsupported `type` is specified, it raises an exception.

    Parameters:
        svc_config (ServiceConfig): The configuration settings for the service, including the
                                    type of configuration client to create, and the host and port
                                    of the configuration service.

    Returns:
        ConfigurationClient: An instance of a subclass of `ConfigurationClient` that corresponds to
                             the specified `type` in `svc_config`.

    Raises:
        Exception: If `svc_config.host` is not set, `svc_config.port` is 0, or if an unsupported
                   `type` is specified in `svc_config`.
    """
    if not svc_config.host or svc_config.port == 0:
        raise ValueError("unable to create Configuration Client: Configuration service host and/or "
                         "port not set")

    if svc_config.type == "keeper":
        client = new_keeper_client(svc_config)
        return client
    raise ValueError(f"unknown configuration client type '{svc_config.type}' requested")
