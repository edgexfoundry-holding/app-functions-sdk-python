#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for StoreClient
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional

from ..contracts import errors
from ..contracts.dtos.store_object import StoredObject


class StoreClient(ABC):
    """ StoreClient establishes the contracts required to persist exported data
    before being forwarded. """

    @abstractmethod
    def store(self, o: StoredObject) -> Tuple[str, Optional[errors.EdgeX]]:
        """ Store persists a stored object to the data store and returns the assigned UUID """

    @abstractmethod
    def retrieve_from_store(self, app_service_key: str) \
            -> Tuple[list[StoredObject], Optional[errors.EdgeX]]:
        """ retrieve_from_store gets an object from the data store. """

    @abstractmethod
    def update(self, o: StoredObject) -> Optional[errors.EdgeX]:
        """ update replaces the data currently in the store with the provided data."""

    @abstractmethod
    def remove_from_store(self, o: StoredObject) -> Optional[Optional[errors.EdgeX]]:
        """ remove_from_store removes an object from the data store. """

    @abstractmethod
    def disconnect(self) -> Optional[errors.EdgeX]:
        """ disconnect ends the connection. """
