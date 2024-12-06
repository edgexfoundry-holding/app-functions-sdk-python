#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides various sampling functions and classes for statistical analysis.

Functions:
- sample_max: Returns the maximum value from a list of integers.
- sample_mean: Returns the mean value from a list of integers.
- sample_min: Returns the minimum value from a list of integers.
- sample_percentile: Returns a specific percentile from a list of integers.
- sample_percentiles: Returns multiple percentiles from a list of integers.
- sample_stddev: Returns the standard deviation from a list of integers.
- sample_variance: Returns the variance from a list of integers.

Classes:
- SampleSnapshot: A snapshot of sampled values.
- UniformSample: A reservoir sampling implementation.
"""

import math
import threading
import random
from typing import List

from pyformance.stats import Snapshot


def sample_max(values: List[int]) -> int:
    """
    SampleMax returns the maximum value of the list of int.
    """
    if len(values) == 0:
        return 0
    return max(values)


def sample_mean(values: List[int]) -> float:
    """
    SampleMean returns the mean value of the list of int.
    """
    if len(values) == 0:
        return 0.0
    return sum(values) / len(values)


def sample_min(values: List[int]) -> int:
    """
    SampleMin returns the minimum value of the list of int.
    """
    if len(values) == 0:
        return 0
    return min(values)


def sample_percentile(values: List[int], p: float) -> float:
    """
    SamplePercentile returns an arbitrary percentile of the list of int.
    """
    return sample_percentiles(values, [p])[0]


def sample_percentiles(values: List[int], ps: List[float]) -> List[float]:
    """
    SamplePercentiles returns a list of arbitrary percentiles of the list of int.
    """
    if len(values) == 0:
        return [0.0] * len(ps)

    sorted_values = sorted(values)
    size = len(sorted_values)
    scores = []

    for p in ps:
        pos = p * (size + 1)
        if pos < 1.0:
            scores.append(float(sorted_values[0]))
        elif pos >= size:
            scores.append(float(sorted_values[-1]))
        else:
            lower = float(sorted_values[int(pos) - 1])
            upper = float(sorted_values[int(pos)])
            scores.append(lower + (pos - math.floor(pos)) * (upper - lower))

    return scores


def sample_stddev(values: List[int]) -> float:
    """
    SampleStdDev returns the standard deviation of the list of integers.
    """
    return math.sqrt(sample_variance(values))


def sample_variance(values: List[int]) -> float:
    """
    SampleVariance returns the variance of the list of integers.
    """
    if len(values) == 0:
        return 0.0
    mean = sample_mean(values)
    sum_sq_diff = sum((v - mean) ** 2 for v in values)
    return sum_sq_diff / len(values)


class SampleSnapshot(Snapshot):
    """
    SampleSnapshot extends Snapshot and adds a count field.
    """
    def __init__(self, count: int, values: List[int]):
        super().__init__(values)
        self.count = count

    def get_count(self) -> int:
        """
        get current count
        """
        return self.count


class UniformSample:
    """
    A uniform sample using Vitter's Algorithm R.
    http://www.cs.umd.edu/~samir/498/vitter.pdf
    """
    def __init__(self, reservoir_size: int):
        self._reservoir_size = reservoir_size
        self._values = []
        self._count = 0
        self._lock = threading.Lock()

    def clear(self):
        """
        Clear all samples.
        """
        with self._lock:
            self._count = 0
            self._values = []

    def count(self) -> int:
        """
        Return the number of samples recorded, which may exceed the reservoir size.
        """
        with self._lock:
            return self._count

    def max(self) -> int:
        """
        Return the maximum value in the sample, which may not be the maximum value ever to be part
        of the sample.
        """
        with self._lock:
            return sample_max(self._values)

    def mean(self) -> float:
        """
        Return the mean of the values in the sample.
        """
        with self._lock:
            return sample_mean(self._values)

    def min(self) -> int:
        """
        Return the minimum value in the sample, which may not be the minimum
        value ever to be part of the sample.
        """
        with self._lock:
            return sample_min(self._values)

    def percentile(self, p: float) -> float:
        """
        Return an arbitrary percentile of values in the sample.
        """
        with self._lock:
            return sample_percentile(self._values, p)

    def percentiles(self, ps: list) -> list:
        """
        Return a slice of arbitrary percentiles of values in the sample.
        """
        with self._lock:
            return sample_percentiles(self._values, ps)

    def size(self) -> int:
        """
        Return the size of the sample, which is at most the reservoir size.
        """
        with self._lock:
            return len(self._values)

    def get_snapshot(self):
        """
        Return a snapshot of the sample's values.
        """
        with self._lock:
            values_copy = self._values.copy()
            return SampleSnapshot(self._count, list(values_copy))

    def stddev(self) -> float:
        """
        Return the standard deviation of the values in the sample.
        """
        with self._lock:
            return sample_stddev(self._values)

    def sum(self) -> int:
        """
        Return the sum of the values in the sample.
        """
        with self._lock:
            return sum(self._values)

    def update(self, v: int):
        """
        Sample a new value.
        """
        with self._lock:
            self._count += 1
            if len(self._values) < self._reservoir_size:
                self._values.append(v)
            else:
                r = random.randint(0, self._count - 1)
                if r < self._reservoir_size:
                    self._values[r] = v

    def values(self) -> List[int]:
        """
        Return a copy of the values in the sample.
        """
        with self._lock:
            values_copy = self._values.copy()
            return values_copy

    def variance(self) -> float:
        """
        Return the variance of the values in the sample.
        """
        with self._lock:
            return sample_variance(self._values)
