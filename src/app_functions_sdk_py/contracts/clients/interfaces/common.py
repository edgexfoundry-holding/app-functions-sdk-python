# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the CommonClientABC abstract base class for common client interactions within
the EdgeX network. It provides a unified interface for essential operations such as fetching
configuration information, testing service availability, obtaining version details, and managing
secrets within the service's secret store.
"""

from abc import ABC, abstractmethod

from ....contracts.dtos.common.config import ConfigResponse
from ....contracts.dtos.common.ping import PingResponse
from ....contracts.dtos.common.version import VersionResponse
from ....contracts.dtos.common.base import BaseResponse
from ....contracts.dtos.common import secret


class CommonClientABC(ABC):
    """
    Abstract base class for a common client interface used in interacting with various services.

    This class outlines the fundamental operations such as fetching configuration information,
    testing service availability, obtaining version details, and managing secrets within the
    service's secret store. Implementations of this class are expected to provide concrete methods
    for these operations.

    Methods:
        configuration(ctx: dict) -> ConfigResponse:
            Obtain configuration information from the target service.

        ping(ctx: dict) -> PingResponse:
            Test whether the service is operational.

        version(ctx: dict) -> VersionResponse:
            Retrieve version information of the service.

        add_secret(ctx: dict, req: secret.SecretRequest) -> BaseResponse:
            Add EdgeX Service exclusive secret to the Secret Store.
    """

    @abstractmethod
    def configuration(self, ctx: dict) -> ConfigResponse:
        """
        Obtain configuration information from the target service.
        """

    @abstractmethod
    def ping(self, ctx: dict) -> PingResponse:
        """
        Test whether the service is working.
        """

    @abstractmethod
    def version(self, ctx: dict) -> VersionResponse:
        """
        Obtain version information from the target service.
        """

    @abstractmethod
    def add_secret(self, ctx: dict, req: secret.SecretRequest) -> BaseResponse:
        """
        Add EdgeX Service exclusive secret to the Secret Store.
        """
