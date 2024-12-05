# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides a set of utility functions and classes for handling errors within the EdgeX.
"""

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus


class EdgeX(Exception, ABC):
    """
    EdgeX provides an abstraction for all internal EdgeX exceptions.
    """

    @abstractmethod
    def debug_messages(self) -> str:
        """Returns a detailed string for debug purposes."""

    @abstractmethod
    def first_level_message(self) -> str:
        """Returns the first level error message without further details."""

    @abstractmethod
    def http_status_code(self) -> int:
        """Returns the status code of this error."""


class ErrKind(Enum):
    """
    A categorical identifier used to give high-level insight as to the error type.
    """
    UNKNOWN = "Unknown"
    DATABASE_ERROR = "Database"
    COMMUNICATION_ERROR = "Communication"
    ENTITY_DOES_NOT_EXIST = "NotFound"
    CONTRACT_INVALID = "ContractInvalid"
    SERVER_ERROR = "UnexpectedServerError"
    LIMIT_EXCEEDED = "LimitExceeded"
    STATUS_CONFLICT = "StatusConflict"
    DUPLICATE_NAME = "DuplicateName"
    INVALID_ID = "InvalidId"
    SERVICE_UNAVAILABLE = "ServiceUnavailable"
    NOT_ALLOWED = "NotAllowed"
    SERVICE_LOCKED = "ServiceLocked"
    NOT_IMPLEMENTED = "NotImplemented"
    RANGE_NOT_SATISFIABLE = "RangeNotSatisfiable"
    IO_ERROR = "IOError"
    OVERFLOW_ERROR = "OverflowError"
    NAN_ERROR = "NaNError"


@dataclass
class CommonEdgeX(EdgeX):
    """
    CommonEdgeX generalizes an error structure which can be used for any type of EdgeX exception.

    This class extends the base EdgeX exception class, providing additional attributes and methods
    for more detailed error information. It is designed to encapsulate common error patterns,
    such as categorizing errors (via `ErrKind`), capturing caller information, and wrapping
    underlying exceptions.

    Attributes:
        caller_info (str): Information about the caller that raised the exception, typically
                           including the file name, function, and line number.
        err_kind (ErrKind): An enumeration value categorizing the type of error.
        message (str): A human-readable message describing the error.
        code (int): An HTTP status code that corresponds to the error.
        err (Exception, optional): An optional wrapped exception that triggered this error.

    Methods:
        __str__(self): Returns a string representation of the error, including the message and any
                       underlying error messages.
        debug_messages(self): Returns a detailed string for debugging purposes, including caller
                              information and any nested error messages.
        first_level_message(self): Returns the first level error message without further details.
        http_status_code(self): Returns the HTTP status code of the error.
    """
    caller_info: str = ""
    err_kind: ErrKind = ErrKind.UNKNOWN
    message: str = ""
    code: int = 0
    err: Exception = None

    def __str__(self):
        if self.err is None:
            return self.message
        if self.message:
            return f"{self.message} -> {str(self.err)}"
        return str(self.err)

    def debug_messages(self) -> str:
        if self.err is None:
            return f"{self.caller_info}: {self.message}"

        if isinstance(self.err, CommonEdgeX):
            return f"{self.caller_info}: {self.message} -> {self.err.debug_messages()}"  # pylint: disable=no-member
        return f"{self.caller_info}: {self.message} -> {str(self.err)}"

    def first_level_message(self) -> str:
        if self.message == "" and self.err is not None:
            if isinstance(self.err, CommonEdgeX):
                return self.err.first_level_message()  # pylint: disable=no-member
            return str(self.err)
        return self.message

    def http_status_code(self) -> int:
        return self.code


def kind(err: Exception) -> ErrKind:
    """
    Determines the ErrKind associated with an error by inspecting the chain of errors. The top-most
    matching Kind is returned or KindUnknown if no Kind can be determined.
    """
    if not isinstance(err, CommonEdgeX):
        return ErrKind.UNKNOWN

    # Return the first "kind" that isn't UNKNOWN.
    if err.err_kind != ErrKind.UNKNOWN or err.err is None:
        return err.err_kind

    return kind(err.err)


def get_caller_information() -> str:
    """
    Generates information about the caller function. This function skips the caller which has
    invoked this function, but rather introspects the calling function 3 frames below this frame in
    the call stack. This function is a helper function which eliminates the need for the
    'callerInfo' field in the `CommonEdgeX` class and providing an 'callerInfo' string when
    creating an 'CommonEdgeX'

    Returns:
        str: A string containing the caller's file name, function name, and line number in a
        formatted manner.
    """
    stack = inspect.stack()
    frame = stack[3]
    info = inspect.getframeinfo(frame[0])
    file = info.filename
    line = info.lineno
    function_name = frame.function
    return f"[{file}]-{function_name}(line {line})"


def code_mapping(err_kind: ErrKind) -> int:  # pylint: disable=too-many-return-statements
    """
    Determines the correct HTTP response code for the given error kind.

    Args:
        err_kind (ErrKind): The kind of error as defined by the ErrKind enumeration.

    Returns:
        int: The corresponding HTTP status code for the given error kind.
    """
    match err_kind:
        case ErrKind.UNKNOWN | ErrKind.DATABASE_ERROR | ErrKind.SERVER_ERROR \
             | ErrKind.OVERFLOW_ERROR | ErrKind.NAN_ERROR:
            return HTTPStatus.INTERNAL_SERVER_ERROR
        case ErrKind.COMMUNICATION_ERROR:
            return HTTPStatus.BAD_GATEWAY
        case ErrKind.ENTITY_DOES_NOT_EXIST:
            return HTTPStatus.NOT_FOUND
        case ErrKind.CONTRACT_INVALID | ErrKind.INVALID_ID:
            return HTTPStatus.BAD_REQUEST
        case ErrKind.STATUS_CONFLICT | ErrKind.DUPLICATE_NAME:
            return HTTPStatus.CONFLICT
        case ErrKind.LIMIT_EXCEEDED:
            return HTTPStatus.REQUEST_ENTITY_TOO_LARGE
        case ErrKind.SERVICE_UNAVAILABLE:
            return HTTPStatus.SERVICE_UNAVAILABLE
        case ErrKind.SERVICE_LOCKED:
            return HTTPStatus.LOCKED
        case ErrKind.NOT_IMPLEMENTED:
            return HTTPStatus.NOT_IMPLEMENTED
        case ErrKind.NOT_ALLOWED:
            return HTTPStatus.METHOD_NOT_ALLOWED
        case ErrKind.RANGE_NOT_SATISFIABLE:
            return HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE
        case ErrKind.IO_ERROR:
            return HTTPStatus.FORBIDDEN
        case _:
            return HTTPStatus.INTERNAL_SERVER_ERROR


def kind_mapping(code: int) -> ErrKind:  # pylint: disable=too-many-return-statements
    """
    Determines the correct EdgeX error kind for the given HTTP response code.

    Args:
        code (int): The HTTP status code to be mapped.

    Returns:
        ErrKind: The corresponding ErrKind enumeration value for the given HTTP status code.
    """
    match code:
        case HTTPStatus.INTERNAL_SERVER_ERROR:
            return ErrKind.SERVER_ERROR
        case HTTPStatus.BAD_GATEWAY:
            return ErrKind.COMMUNICATION_ERROR
        case HTTPStatus.NOT_FOUND:
            return ErrKind.ENTITY_DOES_NOT_EXIST
        case HTTPStatus.BAD_REQUEST:
            return ErrKind.CONTRACT_INVALID
        case HTTPStatus.CONFLICT:
            return ErrKind.STATUS_CONFLICT
        case HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
            return ErrKind.LIMIT_EXCEEDED
        case HTTPStatus.SERVICE_UNAVAILABLE:
            return ErrKind.SERVICE_UNAVAILABLE
        case HTTPStatus.LOCKED:
            return ErrKind.SERVICE_LOCKED
        case HTTPStatus.NOT_IMPLEMENTED:
            return ErrKind.NOT_IMPLEMENTED
        case HTTPStatus.METHOD_NOT_ALLOWED:
            return ErrKind.NOT_ALLOWED
        case HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE:
            return ErrKind.RANGE_NOT_SATISFIABLE
        case _:
            return ErrKind.UNKNOWN


def new_common_edgex(err_kind: ErrKind, message: str, wrapped_error: Exception = None) \
        -> CommonEdgeX:
    """
    Creates a new CommonEdgeX exception instance with specified error kind, message, and an
    optional wrapped error.

    This function simplifies the creation of CommonEdgeX exceptions by automatically populating
    the `caller_info` attribute using the `get_caller_information` function. It also maps the
    provided `err_kind` to an HTTP status code using the `code_mapping` function. This utility
    function is designed to streamline the instantiation process for CommonEdgeX exceptions,
    ensuring that all necessary information is included and correctly formatted.

    Args:
        err_kind (ErrKind): The kind of error, as defined by the ErrKind enumeration.
        message (str): A human-readable message describing the error.
        wrapped_error (Exception, optional): An optional exception that is wrapped by this
                                             CommonEdgeX exception. Defaults to None.

    Returns:
        CommonEdgeX: An instance of the CommonEdgeX class initialized with the provided arguments
                     and additional automatically determined information such as caller info and
                     HTTP status code.
    """
    return CommonEdgeX(
        caller_info=get_caller_information(),
        err_kind=err_kind,
        message=message,
        code=code_mapping(err_kind),
        err=wrapped_error
    )


def new_common_edgex_wrapper(wrapped_error: Exception) -> CommonEdgeX:
    """
    Creates a new CommonEdgeX exception instance specifically for wrapping another exception.

    This function is a convenience wrapper around the `new_common_edgex` function. It automatically
    determines the `ErrKind` of the provided `wrapped_error` (if it is a `CommonEdgeX` instance) or
    defaults to `ErrKind.UNKNOWN`. It then creates a new `CommonEdgeX` instance with this error
    kind, an empty message, and the provided `wrapped_error`. The `caller_info` and `code` are
    automatically determined and set based on the error kind.

    Args:
        wrapped_error (Exception): The exception to be wrapped by the new `CommonEdgeX` instance.

    Returns:
        CommonEdgeX: An instance of the `CommonEdgeX` class initialized to wrap the provided
                     exception, with automatically determined `caller_info`, `err_kind`,
                     and `code`.
    """
    kind_val = kind(wrapped_error)
    return CommonEdgeX(
        caller_info=get_caller_information(),
        err_kind=kind_val,
        message="",
        code=code_mapping(kind_val),
        err=wrapped_error
    )
