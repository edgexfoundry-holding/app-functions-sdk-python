#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `WaitGroup` class, which is used to synchronize the completion of
multiple threads.

Classes:
    - WaitGroup: Manages a counter to keep track of the number of threads and provides methods
    to add to the counter, mark a thread as done, and wait for all threads to complete.
"""

import threading


class WaitGroup:
    """
    WaitGroup manages a counter to keep track of the number of threads and provides methods to add
    to the counter, mark a thread as done, and wait for all threads to complete.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._counter = 0

    def add(self, delta: int):
        """
        Add adds delta, which may be negative, to the WaitGroup counter.
        If the counter becomes zero, all threads blocked on Wait are released.
        If the counter goes negative, Add panics.
        """
        with self._lock:
            self._counter += delta
            if self._counter < 0:
                raise ValueError("sync: negative WaitGroup counter")
            if self._counter == 0:
                self._cond.notify_all()

    def done(self):
        """
        Done decrements the WaitGroup counter by one.
        """
        self.add(-1)

    def wait(self):
        """
        Wait blocks until the WaitGroup counter is zero.
        """
        with self._lock:
            while self._counter > 0:
                self._cond.wait()
