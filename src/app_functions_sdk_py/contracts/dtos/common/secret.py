# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The secret module of the App Functions SDK Python package.

This module defines the SecretDataKeyValue and SecretRequest classes which are used for handling
secrets.

Classes:
    SecretDataKeyValue: Represents a key-value pair for secret data. It has attributes like key and
    value.
    SecretRequest: Represents a secret request. It has attributes like secret_name, secret_data,
    and request_id.
"""

from dataclasses import dataclass, field
from .base import BaseRequest


@dataclass
class SecretDataKeyValue:
    """
    Represents a key-value pair for secret data.

    A SecretDataKeyValue has attributes like key and value.

    Attributes:
        key (str): The key of the secret data.
        value (str): The value of the secret data.
    """
    key: str
    value: str


# pylint: disable=invalid-name
@dataclass
class SecretRequest(BaseRequest):
    """
    Represents a secret request.

    A SecretRequest has attributes like secret_name, secret_data, and request_id.

    Attributes:
        secretName (str): The name of the secret.
        secretData (List[SecretDataKeyValue]): The data of the secret.
        requestId (str): The ID of the request.
    """
    secretName: str = ""
    secretData: [SecretDataKeyValue] = field(default_factory=list)
    requestId: str = ""

    def __post_init__(self):
        super().__init__(self.requestId)
