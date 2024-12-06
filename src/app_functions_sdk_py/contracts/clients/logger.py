# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The logger module of the App Functions SDK.

This module provides the Logger abstract base class (ABC) which defines the interface for a logger,
and the EdgeXLogger class which is an implementation of the Logger interface. It also provides a
function to get a logger instance.

Classes:
    Logger: An abstract base class that defines the interface for a logger.
    EdgeXLogger: An implementation of the Logger interface.

Methods within the Logger class:
    trace(self, msg, *args, **kwargs): Abstract method for logging trace level messages.
    debug(self, msg, *args, **kwargs): Abstract method for logging debug level messages.
    info(self, msg, *args, **kwargs): Abstract method for logging info level messages.
    warn(self, msg, *args, **kwargs): Abstract method for logging warn level messages.
    error(self, msg, *args, **kwargs): Abstract method for logging error level messages.

Methods within the EdgeXLogger class:
    __init__(self, service_key: str, level=INFO): Initializes the EdgeXLogger instance.
    trace(self, msg, *args, **kwargs): Implementation of trace method.
    debug(self, msg, *args, **kwargs): Implementation of debug method.
    info(self, msg, *args, **kwargs): Implementation of info method.
    warn(self, msg, *args, **kwargs): Implementation of warn method.
    error(self, msg, *args, **kwargs): Implementation of error method.

Functions:
    get_logger(service_key: str, level=INFO) -> Logger: Function to get a logger instance.
"""

import logging
from abc import ABC, abstractmethod


class Logger(ABC):
    """
    Abstract base class for a logger.
    """

    @abstractmethod
    def trace(self, msg, *args, **kwargs):
        """
        Abstract method for logging trace level messages.
        """

    @abstractmethod
    def debug(self, msg, *args, **kwargs):
        """
        Abstract method for logging debug level messages.
        """

    @abstractmethod
    def info(self, msg, *args, **kwargs):
        """
        Abstract method for logging info level messages.
        """

    @abstractmethod
    def warn(self, msg, *args, **kwargs):
        """
        Abstract method for logging warn level messages.
        """

    @abstractmethod
    def error(self, msg, *args, **kwargs):
        """
        Abstract method for logging error level messages.
        """

    @abstractmethod
    def set_log_level(self, level_name: str):
        """
        Abstract method for setting the log level.
        """


# Define the logging levels to be compatible with edgexfoundry logging level
TRACE = 5
DEBUG = logging.DEBUG
INFO = logging.INFO
WARN = logging.WARNING
ERROR = logging.ERROR

VALID_LEVELS = {
    'TRACE': TRACE,
    'DEBUG': DEBUG,
    'INFO': INFO,
    'WARNING': WARN,
    'ERROR': ERROR
}

# Add a new logging level named TRACE
logging.addLevelName(TRACE, "TRACE")


class EdgeXLogger(Logger):
    """
    Logger implementation for EdgeX.
    """

    # Supported logging levels
    SUPPORTED_LEVELS = {TRACE, DEBUG, INFO, WARN, ERROR}
    # Default logging format
    DEFAULT_LOGGING_FORMAT = ("level=%(levelname)s ts=%(asctime)s app=%(name)s "
                              "source=%(filename)s:%(lineno)d msg=%("
                              "message)s")

    def __init__(self, service_key: str, level=INFO):
        """
        Initialize the logger with the given service key and level.
        """
        if level not in self.SUPPORTED_LEVELS:
            raise ValueError(f"Unsupported log level: {level}. Supported levels are: "
                             f"{self.SUPPORTED_LEVELS}")
        self.service_key = service_key
        self.logger = logging.getLogger(service_key)
        self.logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"level=%(levelname)s ts=%(asctime)s app={self.service_key} "
                                      f"source=%(filename)s:%(lineno)d msg=%(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def trace(self, msg, *args, **kwargs):
        """
        Implementation of trace method.
        """
        self.logger.log(TRACE, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """
        Implementation of debug method.
        """
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Implementation of info method.
        """
        self.logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """
        Implementation of warn method.
        """
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Implementation of error method.
        """
        self.logger.error(msg, *args, **kwargs)

    def set_log_level(self, level_name: str):
        """
        Set the log level.
        """
        if level_name not in VALID_LEVELS:
            raise ValueError(f"Unsupported log level: {level_name}. Supported levels are: "
                             f"{VALID_LEVELS.keys()}")
        self.logger.setLevel(VALID_LEVELS[level_name])


def get_logger(service_key: str, level=INFO) -> Logger:
    """
    Function to get a logger instance.
    """
    return EdgeXLogger(service_key, level)
