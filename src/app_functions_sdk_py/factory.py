# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The factory module of the App Functions SDK.

This module provides a factory function to create and initialize a new ApplicationService instance.

Functions:
    new_app_service(service_key: str, target_type: Any) -> (ApplicationService, bool):
        Creates a new ApplicationService instance and initializes it.
"""

from typing import Any
from . import constants
from .interfaces import ApplicationService
from .internal.app.service import Service


def new_app_service(service_key: str, target_type: Any = None) -> (ApplicationService, bool):
    """
    Creates a new ApplicationService instance and initializes it.

    This function creates a new Service instance with the provided service_key and target_type.
    It then attempts to initialize the service. If the initialization is successful, the function
    returns the service instance and True. If the initialization fails, the function logs an error
    message and returns None and False.

    Args:
        service_key (str): The service key for the new service.
        target_type (Any): The target type for the new service.

    Returns:
        tuple: A tuple containing the new ApplicationService instance (or None if initialization
        failed) and a boolean indicating whether the initialization was successful.
    """
    service = Service(service_key, target_type, constants.DEFAULT_PROFILE_SUFFIX_PLACEHOLDER)
    try:
        service.initialize()
        return service, True
    except Exception as e:  # pylint: disable=broad-except
        service.logger().error(f"Failed to create and initialize service: {e}")
        return None, False
