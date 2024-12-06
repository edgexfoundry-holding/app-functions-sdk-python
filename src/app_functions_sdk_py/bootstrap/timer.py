# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides a Timer class for managing time-related operations.

Functions:
    new_startup_timer(logger: Logger) -> Timer: Creates a new Timer instance configured
                                                for application startup.

Classes:
    Timer: A Timer class for managing time-related operations.
"""

import time

from datetime import datetime, timedelta
from dataclasses import dataclass

from ..bootstrap import environment
from ..contracts.clients.logger import Logger


@dataclass
class Timer:
    """
    A Timer class for managing time-related operations.

    Attributes:
        start_time (datetime): The time when the timer starts.
        duration (timedelta): The total duration of the timer.
        interval (timedelta): The interval at which certain operations are performed.

    Methods:
        since_as_string: Returns the elapsed time since the timer started as a string.
        remaining_as_string: Returns the remaining time until the timer ends as a string.
        has_not_elapsed: Checks if the timer's duration has not yet elapsed.
        sleep_for_interval: Pauses execution for the duration of the interval.
    """

    start_time: datetime
    duration: timedelta
    interval: timedelta

    def since_as_string(self) -> str:
        """Returns the elapsed time since the timer started as a string."""
        elapsed = datetime.now() - self.start_time
        return str(timedelta(seconds=round(elapsed.total_seconds())))

    def remaining_as_string(self) -> str:
        """
        Returns the remaining time until the timer ends as a string.
        If the remaining time is negative, it returns '0'.
        """
        remaining = self.duration - (datetime.now() - self.start_time)
        remaining = max(remaining, timedelta(0))
        remaining_seconds = round(remaining.total_seconds())
        return str(timedelta(seconds=remaining_seconds))

    def has_not_elapsed(self) -> bool:
        """Checks if the timer's duration has not yet elapsed."""
        return datetime.now() < self.start_time + self.duration

    def sleep_for_interval(self):
        """Pauses execution for the duration of the interval."""
        time.sleep(self.interval.total_seconds())


def new_startup_timer(logger: Logger) -> Timer:
    """
    Creates a new Timer instance configured for application startup.

    Parameters:
        logger (Logger): The logger instance for logging startup information.

    Returns: Timer: A new Timer instance with start time, duration, and interval set based on the
                    application's startup configuration.
    """
    startup = environment.get_startup_info(logger)
    return Timer(
        start_time=datetime.now(),
        duration=timedelta(seconds=startup.duration),
        interval=timedelta(seconds=startup.interval)
    )


def new_timer(duration: int, interval: int) -> Timer:
    """
    Returns a Timer initialized with passed in duration and interval.

    Parameters:
        duration (int): The duration of the timer in seconds.
        interval (int): The interval of the timer in seconds.

    Returns: Timer: A new Timer instance with start time, duration, and interval set based on the
                    application's startup configuration.
    """
    return Timer(
        start_time=datetime.now(),
        duration=timedelta(seconds=duration),
        interval=timedelta(seconds=interval)
    )
