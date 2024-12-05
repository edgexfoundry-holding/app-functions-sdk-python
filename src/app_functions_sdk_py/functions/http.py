# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for HttpExport
"""
from typing import Any, Tuple, Optional
from urllib.parse import urlparse
import requests
from pyformance import meters

from .helpers import register_metric
from .string_values_formatter import StringValuesFormatter, default_string_value_formatter
from ..bootstrap.metrics.samples import UniformSample
from ..contracts.clients.utils.request import HTTPMethod
from ..contracts import errors
from ..contracts.common.constants import CORRELATION_HEADER, CONTENT_TYPE_JSON
from ..interfaces import AppFunctionContext
from ..internal.constants import (METRICS_RESERVOIR_SIZE, HTTP_EXPORT_ERRORS_NAME,
                                  HTTP_EXPORT_SIZE_NAME)
from ..utils.helper import coerce_type

EXPORT_METHOD = "method"
EXPORT_METHOD_POST = "post"
EXPORT_METHOD_PUT = "put"
URL = "url"
MIME_TYPE = "mimetype"
PERSIST_ON_ERROR = "persistonerror"
CONTINUE_ON_SEND_ERROR = "continueonsenderror"
RETURN_INPUT_DATA = "ReturnInputData"
HEADER_NAME = "headername"
SECRET_NAME = "secretname"
SECRET_VALUE_KEY = "secretvaluekey"
HTTP_REQUEST_HEADERS = "httprequestheaders"


class HTTPSender:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    """ HTTPSender is used to post or put the HTTP request """

    def __init__(self, url: str, mime_type: str, persist_on_error: bool,
                 continue_on_send_error: bool, return_input_data: bool,
                 http_header_name: str, secret_value_key: str,
                 secret_name: str,
                 url_formatter: StringValuesFormatter = default_string_value_formatter,
                 http_request_headers=None):
        if http_request_headers is None:
            http_request_headers = {}
        self.url = url
        self.mime_type = mime_type
        self.persist_on_error = persist_on_error
        self.continue_on_send_error = continue_on_send_error
        self.return_input_data = return_input_data
        self.http_header_name = http_header_name
        self.secret_value_key = secret_value_key
        self.secret_name = secret_name
        self.url_formatter = url_formatter
        self.http_request_headers = http_request_headers
        self.http_error_metrics = meters.Counter("")
        self.http_size_metrics = meters.Histogram("", sample=UniformSample(METRICS_RESERVOIR_SIZE))

    def set_retry_data(self, ctx: AppFunctionContext, export_data: bytes):
        """ set retry data in app function context """
        if self.persist_on_error:
            ctx.set_retry_data(export_data)

    def determine_if_using_secrets(
            self, ctx: AppFunctionContext) -> Tuple[bool, Optional[errors.EdgeX]]:
        """ determine if using secrets """
        # not using secrets if both are empty
        if len(self.secret_name) == 0 and len(self.secret_value_key) == 0:
            if len(self.http_header_name) == 0:
                return False, None

            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"in pipeline '{ctx.pipeline_id()}', "
                f"secretName & secretValueKey must be specified when HTTP Header Name is specified")

        # check if one field but not others are provided for secrets
        if len(self.secret_value_key) == 0:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"in pipeline '{ctx.pipeline_id()}', "
                f"secretName was specified but no secretName was provided")

        if len(self.secret_name) == 0:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"in pipeline '{ctx.pipeline_id()}', "
                f"HTTP Header secretName was provided but no secretName was provided")

        if len(self.http_header_name) == 0:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"in pipeline '{ctx.pipeline_id()}', HTTP Header Name required when using secrets")

        # using secrets, all required fields are provided
        return True, None

    def http_send(self, ctx: AppFunctionContext, data: Any, method: str) -> Tuple[bool, Any]:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        """ util function to send the http request """
        lc = ctx.logger()

        lc.debug(f"HTTP Exporting in pipeline '{ctx.pipeline_id()}'")

        if data is None:
            # We didn't receive a result
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function HTTP{method} in pipeline '{ctx.pipeline_id()}': No Data Received")

        if self.persist_on_error and self.continue_on_send_error:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"in pipeline '{ctx.pipeline_id()}' persist_on_error & "
                f"continue_on_send_error can not both be set to true for HTTP Export")

        if self.continue_on_send_error and not self.return_input_data:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"in pipeline '{ctx.pipeline_id()}' continueOnSendError "
                f"can only be used in conjunction returnInputData for multiple HTTP Export")

        if self.mime_type == "":
            self.mime_type = CONTENT_TYPE_JSON

        export_data, error = coerce_type(data)
        if error is not None:
            return False, errors.new_common_edgex_wrapper(error)

        using_secrets, error = self.determine_if_using_secrets(ctx)
        if error is not None:
            return False, errors.new_common_edgex_wrapper(error)

        formatted_url = self.url_formatter(self.url, ctx, data)

        try:
            parsed_url = urlparse(formatted_url)
        except TypeError as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"failed to parse the formatted url '{formatted_url}'", e)

        register_metric(ctx, lambda: f"{HTTP_EXPORT_ERRORS_NAME}-{parsed_url.geturl()}",
                        lambda: self.http_error_metrics,
                        {"url": parsed_url.geturl()})
        register_metric(ctx, lambda: f"{HTTP_EXPORT_SIZE_NAME}-{parsed_url.geturl()}",
                        lambda: self.http_size_metrics,
                        {"url": parsed_url.geturl()})

        req = requests.Request(method, parsed_url.geturl(), data=export_data)

        the_secrets = {}
        if using_secrets:
            # TODO will use the secret store at milestone E  # pylint: disable=fixme
            # the_secrets = ctx.SecretProvider().GetSecret(sender.secretName, sender.secretValueKey)

            lc.debug(
                (f"Setting HTTP Header '{self.http_header_name}' with secret value "
                 f"from SecretStore at secretName='{self.secret_name}' "
                 f"& secretValueKey='{self.secret_value_key}' "
                 f"in pipeline '{ctx.pipeline_id()}'"))

            req.headers[self.http_header_name] = the_secrets[self.secret_value_key]

        req.headers["Content-Type"] = self.mime_type

        # Set all the http request headers
        for key, element in self.http_request_headers.items():
            req.headers[key] = element

        lc.debug(f"POSTing data to {parsed_url.geturl()} {parsed_url.path} "
                 f"in pipeline '{ctx.pipeline_id()}'")

        with requests.Session() as s:
            try:
                response = s.send(req.prepare())
                response.raise_for_status()

                # Data successfully sent, so retry any failed data,
                # if Store and Forward enabled and data has been saved
                if self.persist_on_error:
                    ctx.trigger_retry_failed_data()

                # capture the size into metrics
                export_data_bytes = len(export_data)
                self.http_size_metrics.add(export_data_bytes)

                lc.debug(
                    f"Sent {export_data_bytes} bytes of data "
                    f"in pipeline '{ctx.pipeline_id()}'. Response status is {response.status_code}")
                lc.trace(
                    f"Data exported for pipeline "
                    f"'{ctx.pipeline_id()}' ({CORRELATION_HEADER}={ctx.correlation_id()})")

                # This allows multiple HTTP Exports to be chained in the pipeline
                # to send the same data to different destinations
                # Don't need to read response data since not going to return it so just return now.
                if self.return_input_data:
                    return True, data

                return True, response.content
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.http_error_metrics.inc(1)

                # Continuing pipeline on error
                # This is in support of sending to multiple export destinations
                # by chaining export functions in the pipeline.
                lc.error(f"Continuing pipeline on error in pipeline '{ctx.pipeline_id()}': {e}")

                # If continuing on send error then can't be persisting on error since Store
                # and Forward retries starting with the function that failed and
                # stopped the execution of the pipeline.
                if not self.continue_on_send_error:
                    self.set_retry_data(ctx, export_data)
                    return False, errors.new_common_edgex_wrapper(e)

                # Return input data since must have some data for the next function to operate on.
                return True, data

    def set_http_request_headers(self, http_request_headers: dict):
        """ SetHttpRequestHeaders will set all the header parameters for the http request """
        if http_request_headers is not None:
            self.http_request_headers = http_request_headers

    def http_post(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """
        HTTPPost will send data from the previous function to the specified Endpoint via http POST.
        If no previous function exists, then the event that triggered the pipeline will be used.
        An empty string for the mimetype will default to application/json. """
        return self.http_send(ctx, data, HTTPMethod.POST.value)

    def http_put(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """
        http_put will send data from the previous function to the specified Endpoint via http PUT.
        If no previous function exists, then the event that triggered the pipeline will be used.
        An empty string for the mimetype will default to application/json. """
        return self.http_send(ctx, data, HTTPMethod.PUT.value)


class HTTPSenderOptions:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-positional-arguments
    """ HTTPSenderOptions is used hold the HTTP request configuration """

    def __init__(self, url: str = "", mime_type: str = "", persist_on_error: bool = False,
                 http_header_name: str = "", secret_name: str = "",
                 secret_value_key: str = "",
                 url_formatter: StringValuesFormatter = default_string_value_formatter,
                 continue_on_send_error: bool = False, return_input_data: bool = False):
        # url specifies the URL of destination
        self.url = url
        # mime_type specifies MimeType to send to destination
        self.mime_type = mime_type
        # persist_on_error enables use of store & forward loop if true
        self.persist_on_error = persist_on_error
        # http_header_name to use for passing configured secret
        self.http_header_name = http_header_name
        # secret_name is the name of the secret in the SecretStore
        self.secret_name = secret_name
        # secret_value_key is the key for the value in the secret data from the SecretStore
        self.secret_value_key = secret_value_key
        # url_formatter specifies custom formatting behavior to be applied to configured URL.
        # If nothing specified, default behavior is to attempt to replace placeholders in the
        # form '{some-context-key}' with the values found in the context storage.
        self.url_formatter = url_formatter  # Assuming StringValuesFormatter is defined elsewhere
        # continue_on_send_error allows execution of subsequent chained senders after errors if true
        self.continue_on_send_error = continue_on_send_error
        # return_input_data enables chaining multiple HTTP senders if true
        self.return_input_data = return_input_data


def new_http_sender(url: str, mime_type: str, persist_on_error: bool) -> HTTPSender:
    """ new_http_sender creates, initializes and returns a new instance of HTTPSender """
    return new_http_sender_with_options(HTTPSenderOptions(
        url=url,
        mime_type=mime_type,
        persist_on_error=persist_on_error
    ))


def new_http_sender_with_options(options: HTTPSenderOptions) -> HTTPSender:
    """ new_http_sender_with_options creates, initializes and returns a new instance of HTTPSender
     configured with provided options """
    return HTTPSender(
        url=options.url,
        mime_type=options.mime_type,
        persist_on_error=options.persist_on_error,
        continue_on_send_error=options.continue_on_send_error,
        return_input_data=options.return_input_data,
        http_header_name=options.http_header_name,
        secret_value_key=options.secret_value_key,
        secret_name=options.secret_name,
        url_formatter=options.url_formatter
    )
