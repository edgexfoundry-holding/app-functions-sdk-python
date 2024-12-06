# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for Configurable
"""
import json
from json import JSONDecodeError
from typing import Tuple, Optional

from . import metrics
from ..bootstrap.interface.secret import SecretProvider
from ..functions import (
    batch, conversion, compression, jsonlogic, aesprotection, responsedata, tags, filters)
from ..contracts.common import constants
from ..contracts.clients.logger import Logger
from ..contracts import errors
from ..functions import http
from ..functions import wrap_into_event
from ..functions.http import (
    new_http_sender_with_options, HTTPSenderOptions, EXPORT_METHOD,
    URL, MIME_TYPE, PERSIST_ON_ERROR, CONTINUE_ON_SEND_ERROR,
    RETURN_INPUT_DATA, HEADER_NAME, SECRET_NAME, SECRET_VALUE_KEY,
    HTTP_REQUEST_HEADERS)
from ..interfaces import AppFunction
from ..utils import helper
from ..utils.helper import normalize_value_type
from ..utils.strconv import parse_bool, parse_int


class Configurable:
    """
    Configurable contains the helper functions that return the function pointers
    for building the configurable function pipeline. They transform the parameters map
    from the Pipeline configuration in to the actual parameters required by the function.
    """
    def __init__(self, logger: Logger, sp: SecretProvider):
        self._logger = logger
        self._sp = sp

    def http_export(self, parameters: dict) -> Optional[AppFunction]:
        """
        http_export will send data from the previous function
        to the specified Endpoint via http POST or PUT.
        If no previous function exists, then the event that triggered the pipeline will be used.
        Passing an empty string to the mimetype method will default to application/json.
        This function is a configuration function and returns a function pointer.
        """
        options, method, err = self.process_http_export_parameters(parameters)
        if err is not None:
            self._logger.error(err)
            return None

        transform = new_http_sender_with_options(options)

        # Unmarshal and set httpRequestHeaders
        http_request_headers = {}
        if HTTP_REQUEST_HEADERS in parameters and parameters[HTTP_REQUEST_HEADERS] != "":
            try:
                http_request_headers = json.loads(parameters[HTTP_REQUEST_HEADERS])
            except JSONDecodeError as e:
                self._logger.error(f"Unable to unmarshal http request headers : {e}")
                return None

        transform.set_http_request_headers(http_request_headers)

        match method.lower():
            case http.EXPORT_METHOD_POST:
                return transform.http_post
            case http.EXPORT_METHOD_PUT:
                return transform.http_put
            case _:
                self._logger.error(
                    f"Invalid HTTPExport method of '{method}'. "
                    f"Must be '{http.EXPORT_METHOD_POST}' or '{http.EXPORT_METHOD_PUT}'")
                return None

    def process_http_export_parameters(
            self, parameters: dict) -> Tuple[HTTPSenderOptions, str, Optional[errors.EdgeX]]:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        """ process http export parameters """
        result = HTTPSenderOptions()

        if EXPORT_METHOD in parameters:
            method = parameters[EXPORT_METHOD]
        else:
            return result, "", errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID, f"HTTPExport Could not find {EXPORT_METHOD}")

        if URL in parameters:
            result.url = str(parameters[URL]).strip()
        else:
            return result, "", errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID, f"HTTPExport Could not find {URL}")

        if MIME_TYPE in parameters:
            result.mime_type = str(parameters[MIME_TYPE]).strip()
        else:
            return result, "", errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID, f"HTTPExport Could not find {MIME_TYPE}")

        #  PersistOnError is optional and is false by default.
        if PERSIST_ON_ERROR in parameters:
            val = parameters[PERSIST_ON_ERROR]
            try:
                result.persist_on_error = parse_bool(val)
            except ValueError as e:
                return result, "", errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"HTTPExport Could not parse '{val}' to a bool "
                    f"for '{PERSIST_ON_ERROR}' parameter", e)

        # ContinueOnSendError is optional and is false by default.
        if CONTINUE_ON_SEND_ERROR in parameters:
            val = parameters[CONTINUE_ON_SEND_ERROR]
            try:
                result.continue_on_send_error = parse_bool(val)
            except ValueError as e:
                return result, "", errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"HTTPExport Could not parse '{val}' to a bool "
                    f"for '{CONTINUE_ON_SEND_ERROR}' parameter", e)

        # ReturnInputData is optional and is false by default.
        if RETURN_INPUT_DATA in parameters:
            val = parameters[RETURN_INPUT_DATA]
            try:
                result.return_input_data = parse_bool(val)
            except ValueError as e:
                return result, "", errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"HTTPExport Could not parse '{val}' to a bool "
                    f"for '{RETURN_INPUT_DATA}' parameter", e)

        if HEADER_NAME in parameters:
            result.http_header_name = str(parameters[HEADER_NAME]).strip()
        else:
            result.http_header_name = ""

        if SECRET_NAME in parameters:
            result.secret_name = str(parameters[SECRET_NAME]).strip()
        else:
            result.secret_name = ""

        if SECRET_VALUE_KEY in parameters:
            result.secret_value_key = str(parameters[SECRET_VALUE_KEY]).strip()
        else:
            result.secret_value_key = ""

        if (len(result.http_header_name) == 0 and len(result.secret_name) != 0
                and len(result.secret_value_key) != 0):
            return result, "", errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"HTTPExport missing {HEADER_NAME} "
                f"since {SECRET_NAME} & {SECRET_VALUE_KEY} are specified")

        if (len(result.secret_name) == 0 and len(result.http_header_name) != 0
                and len(result.secret_value_key) != 0):
            return result, "", errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"HTTPExport missing {SECRET_NAME} "
                f"since {HEADER_NAME} & {SECRET_VALUE_KEY} are specified")

        if (len(result.secret_value_key) == 0 and len(result.secret_name) != 0
                and len(result.http_header_name) != 0):
            return result, "", errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"HTTPExport missing {SECRET_VALUE_KEY} "
                f"since {SECRET_NAME} & {HEADER_NAME} are specified")

        return result, method, None

    def batch(self, parameters: dict) -> Optional[AppFunction]:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        """ Batch sets up Batching of events based on the specified mode parameter
        (BatchByCount, BatchByTime or BatchByTimeAndCount) and mode specific parameters.
        This function is a configuration function and returns a function pointer. """
        if batch.MODE in parameters:
            mode = str(parameters[batch.MODE])
        else:
            self._logger.error("Could not find '%s' parameter for Batch", batch.MODE)
            return None

        match mode.lower():
            case batch.BATCH_BY_COUNT:
                if batch.BATCH_THRESHOLD in parameters:
                    batch_threshold = parameters[batch.BATCH_THRESHOLD]
                else:
                    self._logger.error(
                        "Could not find '%s' parameter for BatchByCount", batch.BATCH_THRESHOLD)
                    return None
                try:
                    threshold_value = parse_int(batch_threshold)
                except ValueError as e:
                    self._logger.error(
                        "Could not parse '%s' to an int for '%s' parameter for BatchByCount: %s",
                        batch_threshold, batch.BATCH_THRESHOLD, e)
                    return None

                transform = batch.new_batch_by_count(threshold_value)

            case batch.BATCH_BY_TIME:
                if batch.TIME_INTERVAL in parameters:
                    time_interval = parameters[batch.TIME_INTERVAL]
                else:
                    self._logger.error(
                        "Could not find '%s' parameter for BatchByTime", batch.TIME_INTERVAL)
                    return None

                transform, err = batch.new_batch_by_time(time_interval)
                if err is not None:
                    self._logger.error(err)
                    return None

            case batch.BATCH_BY_TIME_COUNT:
                if batch.TIME_INTERVAL in parameters:
                    time_interval = parameters[batch.TIME_INTERVAL]
                else:
                    self._logger.error(
                        "Could not find '%s' parameter for BatchByTime", batch.TIME_INTERVAL)
                    return None
                if batch.BATCH_THRESHOLD in parameters:
                    batch_threshold = parameters[batch.BATCH_THRESHOLD]
                else:
                    self._logger.error(
                        "Could not find '%s' parameter for BatchByCount", batch.BATCH_THRESHOLD)
                    return None
                try:
                    threshold_value = parse_int(batch_threshold)
                except ValueError as e:
                    self._logger.error(
                        "Could not parse '%s' to an int for '%s' parameter for BatchByCount: %s",
                        batch_threshold, batch.BATCH_THRESHOLD, e)
                    return None

                transform, err = batch.new_batch_by_time_and_count(time_interval, threshold_value)
                if err is not None:
                    self._logger.error(err)
                    return None
            case _:
                self._logger.error(
                    "Invalid batch mode '%s'. Must be '%s', '%s' or '%s'",
                    mode,
                    batch.BATCH_BY_COUNT,
                    batch.BATCH_BY_TIME,
                    batch.BATCH_BY_TIME_COUNT)
                return None

        # is_event_data is optional
        if batch.IS_EVENT_DATA in parameters:
            is_event_data_value = parameters[batch.IS_EVENT_DATA]
            try:
                is_event_data = parse_bool(is_event_data_value)
            except ValueError as e:
                self._logger.error(
                    "Could not parse '%s' to a bool for '%s' parameter: %s",
                    is_event_data_value, batch.IS_EVENT_DATA, e)
                return None
            transform.is_event_data = is_event_data

        # merge_on_send is optional
        if batch.MERGE_ON_SEND in parameters:
            merge_on_send_value = parameters[batch.MERGE_ON_SEND]
            try:
                merge_on_send = parse_bool(merge_on_send_value)
            except ValueError as e:
                self._logger.error(
                    "Could not parse '%s' to a bool for '%s' parameter: %s",
                    merge_on_send_value, batch.MERGE_ON_SEND, e)
                return None
            transform.merge_on_send = merge_on_send

        return transform.batch

    def compress(self, parameters: dict) -> Optional[AppFunction]:
        """ Compress compresses data received as either a string, bytes
        using the specified algorithm (GZIP or ZLIB) and returns a base64 encoded string as bytes.
        This function is a configuration function and returns a function. """
        if compression.ALGORITHM in parameters:
            algorithm = str(parameters[compression.ALGORITHM]).strip()
        else:
            self._logger.error("Could not find '%s' parameter for Compress", compression.ALGORITHM)
            return None

        transform = compression.new_compression()

        match algorithm.lower():
            case compression.COMPRESS_GZIP:
                return transform.compress_with_gzip
            case compression.COMPRESS_ZLIB:
                return transform.compress_with_zlib
            case _:
                self._logger.error(
                    "Invalid compression algorithm '%s'. Must be '%s' or '%s'",
                    algorithm,
                    compression.COMPRESS_GZIP,
                    compression.COMPRESS_ZLIB)
                return None

    def transform(self, parameters: dict) -> Optional[AppFunction]:
        """ transform transforms an EdgeX event to XML or JSON based on specified transform type.
        It will return an error and stop the pipeline if a non-edgex event is received or
        if no data is received. This is a configuration function and returns a app function. """
        if conversion.TRANSFORM_TYPE in parameters:
            transform_type = str(parameters[conversion.TRANSFORM_TYPE]).strip()
        else:
            self._logger.error(
                "Could not find '%s' parameter for transform",
                conversion.TRANSFORM_TYPE)
            return None

        transform = conversion.Conversion()

        match transform_type.lower():
            case conversion.TRANSFORM_XML:
                return transform.transform_to_xml
            case conversion.TRANSFORM_JSON:
                return transform.transform_to_json
            case _:
                self._logger.error(
                    "Invalid transform type '%s'. Must be '%s' or '%s'",
                    transform_type,
                    conversion.TRANSFORM_XML,
                    conversion.TRANSFORM_JSON)
                return None

    def wrap_into_event(self, parameters: dict) -> Optional[AppFunction]:
        # pylint: disable=too-many-return-statements
        """ WrapIntoEvent wraps the provided value as an EdgeX Event using the configured
        event/reading metadata that have been set. The new Event/Reading is returned to the next
        pipeline function. This function is a configuration function and returns a function
        pointer """
        if wrap_into_event.PROFILE_NAME in parameters:
            profile_name = str(parameters[wrap_into_event.PROFILE_NAME]).strip()
        else:
            self._logger.error(
                "Could not find '%s' parameter for WrapIntoEvent",
                wrap_into_event.PROFILE_NAME)
            return None

        if wrap_into_event.DEVICE_NAME in parameters:
            device_name = str(parameters[wrap_into_event.DEVICE_NAME]).strip()
        else:
            self._logger.error(
                "Could not find '%s' parameter for WrapIntoEvent",
                wrap_into_event.DEVICE_NAME)
            return None

        if wrap_into_event.RESOURCE_NAME in parameters:
            resource_name = str(parameters[wrap_into_event.RESOURCE_NAME]).strip()
        else:
            self._logger.error(
                "Could not find '%s' parameter for WrapIntoEvent",
                wrap_into_event.RESOURCE_NAME)
            return None

        if wrap_into_event.VALUE_TYPE in parameters:
            value_type = str(parameters[wrap_into_event.VALUE_TYPE]).strip()
        else:
            self._logger.error(
                "Could not find '%s' parameter for WrapIntoEvent",
                wrap_into_event.VALUE_TYPE)
            return None

        # Converts to upper case and validates it is a valid value_type
        value_type, err = normalize_value_type(value_type)
        if err is not None:
            self._logger.error(err)
            return None

        match value_type:
            case constants.VALUE_TYPE_BINARY:
                if wrap_into_event.MEDIA_TYPE in parameters:
                    media_type = str(parameters[wrap_into_event.MEDIA_TYPE]).strip()
                else:
                    self._logger.error(
                        "Could not find '%s' parameter for WrapIntoEvent",
                        wrap_into_event.MEDIA_TYPE)
                    return None

                if len(media_type) == 0:
                    self._logger.error("MediaType can not be empty when ValueType=Binary")
                    return None

                transform = wrap_into_event.new_event_wrapper_binary_reading(
                    profile_name, device_name, resource_name, media_type)
            case constants.VALUE_TYPE_OBJECT:
                transform = wrap_into_event.new_event_wrapper_object_reading(
                    profile_name, device_name, resource_name)

            case _:
                transform = wrap_into_event.new_event_wrapper_simple_reading(
                    profile_name, device_name, resource_name, value_type)

        return transform.wrap

    def json_logic(self, parameters: dict) -> Optional[AppFunction]:
        """ json_logic configure JsonLogic rules and return the AppFunction """
        if jsonlogic.RULE not in parameters:
            self._logger.error(
                "Could not find '%s' parameter for JSONLogic", jsonlogic.RULE)
            return None
        rule = parameters[jsonlogic.RULE]

        transform, err = jsonlogic.new_json_logic(rule)
        if err is not None:
            self._logger.error(
                "Could not load the JSON rule '%s' for JSONLogic", rule)
            return None
        return transform.evaluate

    def encrypt(self, parameters: dict) -> Optional[AppFunction]:
        """ Encrypt encrypts either a string, bytes, or json.Marshaller type using encryption
        algorithm (AES only at this time). It will return a byte[] of the encrypted data.
        This function is a configuration function and returns a function pointer. """
        if aesprotection.ALGORITHM not in parameters:
            self._logger.error(
                "Could not find '%s' parameter for Encrypt", aesprotection.ALGORITHM)
            return None
        algorithm = str(parameters[aesprotection.ALGORITHM])
        if aesprotection.SECRET_NAME not in parameters:
            self._logger.error(
                "Could not find '%s' parameter for Encrypt", aesprotection.SECRET_NAME)
            return None
        secret_name = parameters[aesprotection.SECRET_NAME]
        if aesprotection.SECRET_VALUE_KEY not in parameters:
            self._logger.error(
                "Could not find '%s' parameter for Encrypt", aesprotection.SECRET_VALUE_KEY)
            return None
        secret_value_key = parameters[aesprotection.SECRET_VALUE_KEY]

        # SecretName & SecretValueKey both must be specified
        if len(secret_name) == 0 or len(secret_value_key) == 0:
            self._logger.error(
                "'%s' and '%s' both must be set in configuration", secret_name, secret_value_key)
            return None

        match algorithm.lower():
            case aesprotection.ENCRYPT_AES256:
                return aesprotection.AESProtection(
                    secret_name=secret_name, secret_value_key=secret_value_key,
                ).encrypt
            case _:
                self._logger.error(
                    "Invalid encryption algorithm '%s'. Must be '%s",
                    algorithm,
                    aesprotection.ENCRYPT_AES256)
                return None

    def set_response_data(self, parameters: dict) -> Optional[AppFunction]:
        """ SetResponseData sets the response data to that passed in from the previous function
        and the response content type to that set in the ResponseContentType configuration
        parameter. """
        transform = responsedata.ResponseData("")
        if (responsedata.RESPONSE_CONTENT_TYPE in parameters
                and len(parameters[responsedata.RESPONSE_CONTENT_TYPE]) > 0):
            transform.response_content_type = parameters[responsedata.RESPONSE_CONTENT_TYPE]

        return transform.set_response_data

    def add_tags(self, parameters: dict) -> Optional[AppFunction]:
        """ add_tags adds the configured list of tags to Events passed to the transform.
        This function is a configuration function and returns a function pointer. """
        event_tags, err = self.process_tags_parameter(parameters)
        if err is not None:
            self._logger.error(err)
            return None

        transform = tags.new_tags(event_tags)
        return transform.add_tags

    def process_tags_parameter(self, parameters: dict) -> Tuple[dict, Optional[errors.EdgeX]]:
        """ process_tags_parameter process the AddTags parameter """
        if parameters is None or tags.TAGS not in parameters:
            return {}, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"Could not find '{tags.TAGS}' parameter for AddTags")

        tags_spec = [x.strip() for x in parameters[tags.TAGS].split(',')]
        tag_key_values = helper.delete_empty_and_trim(tags_spec)

        event_tags = {}
        for tag in tag_key_values:
            key_value = helper.delete_empty_and_trim([x.strip() for x in tag.split(':')])
            if len(key_value) != 2:
                return {}, errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"Bad Tags specification format. "
                    f"Expect comma separated list of 'key:value'. Got `{tag}`")

            if len(key_value[0]) == 0:
                return {}, errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"Tag key missing. Got `{tag}`")

            if len(key_value[1]) == 0:
                return {}, errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"Tag value missing. Got `{tag}`")

            event_tags[key_value[0]] = key_value[1]

        return event_tags, None

    def filter_by_profile_name(self, parameters: dict) -> Optional[AppFunction]:
        """ FilterByProfileName - Specify the profile names of interest to filter for data
        coming from certain sensors. The Filter by Profile Name transform looks at the Event
        in the message and looks at the profile names of interest list, provided by this function,
        and filters out those messages whose Event is for profile names not in the profile names
        of interest. """
        transform, ok = self.process_filter_parameters(
            "FilterByProfileName", parameters, filters.PROFILE_NAMES)
        if not ok:
            return None

        return transform.filter_by_profile_name

    def filter_by_device_name(self, parameters: dict) -> Optional[AppFunction]:
        """ FilterByDeviceName - Specify the device names of interest to filter for data
        coming from certain sensors. The Filter by Device Name transform looks at the Event
        in the message and looks at the device names of interest list, provided by this function,
        and filters out those messages whose Event is for device names not in the device names of
        interest. """
        transform, ok = self.process_filter_parameters(
            "FilterByDeviceName", parameters, filters.DEVICE_NAMES)
        if not ok:
            return None

        return transform.filter_by_device_name

    def filter_by_source_name(self, parameters: dict) -> Optional[AppFunction]:
        """ FilterBySourceName - Specify the source names (resources and/or commands) of interest
        to filter for data coming from certain sensors. The Filter by Source Name transform looks
        at the Event in the message and looks at the source names of interest list, provided by
        this function, and filters out those messages whose Event is for source names not in the
        source names of interest. """
        transform, ok = self.process_filter_parameters(
            "FilterBySourceName", parameters, filters.SOURCE_NAMES)
        if not ok:
            return None

        return transform.filter_by_source_name

    def filter_by_resource_name(self, parameters: dict) -> Optional[AppFunction]:
        """ FilterByResourceName - Specify the resource name of interest to filter for data from
        certain types of IoT objects, such as temperatures, motion, and so forth, that may come
        from an array of sensors or devices. The Filter by resource name assesses the data in
        each Event and Reading, and removes readings that have a resource name that is not in
        the list of resource names of interest for the application."""
        transform, ok = self.process_filter_parameters(
            "FilterByResourceName", parameters, filters.RESOURCE_NAMES)
        if not ok:
            return None

        return transform.filter_by_resource_name

    def process_filter_parameters(
            self, func_name: str,
            parameters: dict, param_name: str) -> Tuple[Optional[filters.Filter], bool]:
        """ process_filter_parameters process the fileter parameters """

        if param_name not in parameters:
            self._logger.error("Could not find '%s' parameter for %s", param_name, func_name)
            return None, False

        names = parameters[param_name]

        filter_out_bool = False
        if filters.FILTER_OUT in parameters:
            try:
                filter_out_bool = parse_bool(parameters[filters.FILTER_OUT])
            except ValueError as e:
                self._logger.error(
                    "Could not convert filterOut value `%s` to bool for %s: %s",
                    filter_out_bool, func_name, e)
                return None, False

        names_cleaned = helper.delete_empty_and_trim([x.strip() for x in names.split(',')])

        transform = filters.Filter(
            filter_values=names_cleaned,
            filter_out=filter_out_bool,
        )

        return transform, True

    def to_line_protocol(self, parameters: dict) -> Optional[AppFunction]:
        """ ToLineProtocol transforms the Metric DTO passed to the transform to a string conforming
         to Line Protocol syntax. This function is a configuration function and returns a function
         pointer. """
        metric_tags, failed = self.process_tags_parameter(parameters)
        if failed is not None:
            return None

        mp, err = metrics.new_metrics_processor(metric_tags)
        if err is not None:
            self._logger.error(f"unable to configure ToLineProtocol function: {err}")
            return None

        return mp.to_line_protocol
