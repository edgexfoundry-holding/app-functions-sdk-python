# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the ProviderInfo class which encapsulates the configuration necessary for
connecting to a Configuration Provider service. It includes details such as the host, port, and
type of the Configuration Provider service, as well as authentication details.
"""

from typing import Any

from ...bootstrap import environment
from ...contracts.clients.logger import Logger
from ...configuration import ServiceConfig


class ProviderInfo:
    """
    ProviderInfo class encapsulates the configuration necessary for connecting to a
    Configuration Provider service.

    Attributes:
        logger (Logger): Logger instance for logging.
        _service_config (ServiceConfig): Service configuration instance.
    """
    def __init__(self, lc: Logger, provider_url: str):
        self.logger = lc
        self._service_config = ServiceConfig()

        try:
            # initialize config provider configuration for URL set in commandline options
            if provider_url:
                self._service_config.populate_from_url(provider_url)

            # override file-based configuration with environment variables
            self._service_config = environment.override_config_provider_info(lc,
                                                                             self._service_config)
        except ValueError as e:
            self.logger.error(f"error initializing configuration provider: {e}")
            raise

    def use_provider(self):
        """
        Returns whether the Configuration Provider should be used or not.
        """
        return self._service_config.host != ""

    def set_host(self, host):
        """
        Sets the host name for the Configuration Provider.
        """
        self._service_config.host = host

    def service_config(self):
        """
        Returns service configuration for the Configuration Provider
        """
        return self._service_config

    def set_auth_injector(self, auth_injector: Any):
        """
        Sets the Authentication Injector for the Configuration Provider
        """
        self._service_config.auth_injector = auth_injector
