# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines data transfer objects (DTOs) related to the key-value store (KVS)
functionality. It includes abstract base classes and data classes for handling responses from the
KVS endpoint of the core-keeper service, facilitating the representation and manipulation of
key-value data with timestamp information.

Classes:
    KVResponse: An abstract base class defining the interface for KVS response content.
    StoredData: A data class representing stored data with timestamp information.
    KVS: A concrete class representing the response content for key-value pairs, including the key,
    value, and timestamp.
    KeyOnly: A concrete class representing the response content for requests that retrieve only the
    keys, without the associated values.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .dbtimestamp import DBTimestamp


class KVResponse(ABC):  # pylint: disable=too-few-public-methods
    """
    Defines the Response Content for GET Keys of core-keeper (GET /kvs/key/{key} API).
    """
    @abstractmethod
    def set_key(self, new_key: str):
        """
        Set the key for the response content.
        """


@dataclass
class StoredData(DBTimestamp):
    """
    Represents the stored data with timestamp information.
    """
    value: Any = None


@dataclass
class KVS(StoredData, KVResponse):
    """
    Defines the Response Content for GET Keys controller with keyOnly is false which inherits
    KVResponse abstract class.
    """
    key: str = ""

    def set_key(self, new_key: str):
        self.key = new_key


class KeyOnly(str, KVResponse):
    """
    Defines the Response Content for GET Keys with keyOnly is true which inherits KVResponse
    abstract class.
    """
    def set_key(self, new_key: str):
        self.__dict__['_str'] = new_key
