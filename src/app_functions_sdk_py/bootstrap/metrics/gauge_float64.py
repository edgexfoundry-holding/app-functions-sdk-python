#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the GaugeFloat64 class, which extends the Gauge class from the
pyformance library.
"""

from pyformance.meters.gauge import Gauge


class GaugeFloat64(Gauge):
    """
    GaugeFloat64 is a floating-point number gauge.
    """
    def __init__(self, key, tags=None):
        super().__init__(key, tags)
        self.value = 0.0  # Initialize as a floating-point number

    def set_value(self, new_value: float):
        """Set the gauge to a floating point value."""
        self.value = float(new_value)

    def get_value(self):
        """Get the current gauge value."""
        return self.value
