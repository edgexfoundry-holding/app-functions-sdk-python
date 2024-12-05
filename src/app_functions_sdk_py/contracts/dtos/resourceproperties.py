# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The resourceproperties module of the App Functions SDK Python package.

This module defines the ResourceProperties class which represents the properties of a resource in
the context of the App Functions SDK. A resource property defines the characteristics of a device
resource.

Classes:
    ResourceProperties: Represents the properties of a device resource. It has attributes like
    value_type, read_write, units, minimum, maximum, default_value, mask, shift, scale, offset,
    base, assertion, media_type, and optional.
"""

from typing import Any, Optional
from dataclasses import dataclass
import numpy as np
from dataclasses_json import dataclass_json


# pylint: disable=invalid-name
@dataclass_json
@dataclass
class ResourceProperties:  # pylint: disable=too-many-instance-attributes
    """
    Represents the properties of a device resource.
    """
    valueType: str = ""
    readWrite: str = ""
    units: str = ""
    defaultValue: str = ""
    assertion: str = ""
    mediaType: str = ""
    minimum: Optional[np.float64] = None
    maximum: Optional[np.float64] = None
    mask: Optional[np.uint64] = None
    shift: Optional[np.int64] = None
    scale: Optional[np.float64] = None
    offset: Optional[np.float64] = None
    base: Optional[np.float64] = None
    optional: Optional[dict[str, Any]] = None
