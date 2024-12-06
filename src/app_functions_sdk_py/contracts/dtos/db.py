# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The db module of the App Functions SDK Python package.

This module defines the DBTimestamp class which represents a timestamp in the context of the App
Functions SDK. A DBTimestamp is a data structure that holds the creation and update times of a
database entry.

Classes:
    DBTimestamp: Represents a timestamp. It has attributes like created and updated.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class DBTimestamp:
    """
    Represents a database timestamp.

    A DBTimestamp is a data structure that holds the creation and update times of a database entry.
    It has attributes like created and updated.

    Attributes:
        created (datetime): The time the database entry was created.
        modified (datetime): The time the database entry was last updated.
    """
    created: Optional[datetime]
    modified: Optional[datetime]
