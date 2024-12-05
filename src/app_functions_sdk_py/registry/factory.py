#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `new_registry_client` function, which creates a new registry client based
on the registry configuration provided.
"""

from ..registry.config import Config
from ..registry.keeper.client import KeeperClient, Client


def new_registry_client(registry_config: Config) -> Client:
    """
    new_registry_client creates a new registry client based on the registry configuration provided.
    """
    if not registry_config.host or registry_config.port == 0:
        raise ValueError("unable to create client: registry host and/or port or serviceKey not set")

    if registry_config.service_type == "keeper":
        registry_client = KeeperClient(registry_config)
        return registry_client

    raise ValueError(f"Unknown registry type '{registry_config.service_type}' requested")
