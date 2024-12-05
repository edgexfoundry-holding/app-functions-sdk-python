# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines data transfer objects (DTOs) related to the database timestamp functionality.
"""

from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class DBTimestamp:
    """
    Represents a pair of timestamps for database records.

    Attributes:
        created (int): The timestamp when the record was created.
        modified (int): The timestamp when the record was last modified.
    """

    created: int = 0
    modified: int = 0
