#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides helper functions for retrieving configuration instances from the
dependency injection container (DIC).

Functions:
    configuration_from: Queries the DIC and returns the service's ConfigurationStruct
    implementation.
    config_client_from: Queries the DIC and returns the ConfigurationClient implementation.

Constants:
    ConfigurationName: The name of the ConfigurationStruct implementation in the DIC.
    ConfigClientInterfaceName: The name of the ConfigurationClient implementation in the DIC.
"""

from typing import Callable, Any, Optional

from ...bootstrap.di.type import type_instance_to_name
from ...configuration import ConfigurationClient
from ...internal.common.config import ConfigurationStruct

# ConfigurationName contains the name of data's common.ConfigurationStruct implementation in
# the DIC.
ConfigurationName = type_instance_to_name(ConfigurationStruct())  # pylint: disable=invalid-name


def configuration_from(get: Callable[[str], Any]) -> Optional[ConfigurationStruct]:
    """
    configuration_from helper function queries the DIC and returns service's ConfigurationStruct
    implementation.
    """
    config = get(ConfigurationName)
    if isinstance(config, ConfigurationStruct):
        return config
    return None


# ConfigClientInterfaceName contains the name of the ConfigurationClient implementation in the DIC.
ConfigClientInterfaceName = type_instance_to_name(ConfigurationClient)


def config_client_from(get: Callable[[str], Any]) -> Optional[ConfigurationClient]:
    """
    config_client_from helper function queries the DIC and returns the ConfigurationClient
    implementation.
    """
    client = get(ConfigClientInterfaceName)
    if isinstance(client, ConfigurationClient):
        return client
    return None
