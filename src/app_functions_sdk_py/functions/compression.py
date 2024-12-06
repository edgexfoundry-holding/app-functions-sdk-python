#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for compression
"""
import base64
import zlib
from typing import Any, Tuple
import gzip

from ..contracts import errors
from ..contracts.common.constants import CONTENT_TYPE_TEXT
from ..interfaces import AppFunctionContext
from ..utils.helper import coerce_type

ALGORITHM = "algorithm"
COMPRESS_GZIP = "gzip"
COMPRESS_ZLIB = "zlib"


class Compression:
    """ Compression compress the data from the pipeline """
    def compress_with_gzip(
            self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ compress_with_gzip compresses data received as either a string, bytes
        using gzip algorithm and returns a base64 encoded string as a bytes. """
        if data is None:
            # We didn't receive a result
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function CompressWithGZIP in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug("Compression with GZIP in pipeline '%s'", ctx.pipeline_id())
        byte_data, err = coerce_type(data)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        try:
            compressed = gzip.compress(byte_data)
        except (ValueError, OSError) as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"failed to compress data to GZIP in pipeline '{ctx.pipeline_id()}'", e)

        # Set response "content-type" header to "text/plain"
        ctx.set_response_content_type(CONTENT_TYPE_TEXT)
        try:
            encoded = base64.b64encode(compressed)
        except (ValueError, TypeError) as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"failed to encode GZIP data to base64 in pipeline '{ctx.pipeline_id()}'", e)

        return True, encoded

    def compress_with_zlib(
            self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ CompressWithZLIB compresses data received as either a string,[]byte
        using zlib algorithm returns a base64 encoded string as bytes. """
        # as zlib writer is not allowed to be used by multiple goroutines,
        # to avoid data race, use mutex lock to ensure atomic zlib writer operation.
        if data is None:
            # We didn't receive a result
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function CompressWithZLIB in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug("Compression with ZLIB in pipeline '%s'", ctx.pipeline_id())
        byte_data, err = coerce_type(data)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        try:
            compressed = zlib.compress(byte_data)
        except (ValueError, OSError) as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"failed to compress data to ZLIB in pipeline '{ctx.pipeline_id()}'", e)

        # Set response "content-type" header to "text/plain"
        ctx.set_response_content_type(CONTENT_TYPE_TEXT)
        try:
            encoded = base64.b64encode(compressed)
        except (ValueError, TypeError) as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"failed to encode ZLIB data to base64 in pipeline '{ctx.pipeline_id()}'", e)

        return True, encoded


def new_compression() -> Compression:
    """ new_compression creates, initializes and returns a new instance of Compression """
    return Compression()
