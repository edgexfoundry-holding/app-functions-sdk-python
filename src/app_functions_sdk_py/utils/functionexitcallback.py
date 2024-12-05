#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `FunctionExitCallback` class, which is used to execute
a callback function when exiting a context.

Classes:
    - FunctionExitCallback: Executes a callback function upon exiting a context.
"""


class FunctionExitCallback:
    """
    FunctionExitCallback executes a callback function upon exiting a context.
    """
    def __init__(self, callback):
        self.callback = callback

    def __enter__(self):
        # Code to execute when entering the context (before the function runs)
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        # Code to execute when exiting the context (after the function runs)
        self.callback()
