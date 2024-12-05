# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides utility functions for making HTTP requests.
It includes functions for sending GET, POST, PUT, PATCH, and DELETE requests,
with support for adding query parameters, authentication, and handling request and response data.


Functions:
    get_request: Initiates a GET request to a specified URL with optional query parameters and
    authentication.
    post_request: Sends a POST request to a specified URL with data and optional authentication.
    put_request: Sends a PUT request to a specified URL with data and optional query parameters
    and authentication.
    patch_request: Sends a PATCH request to a specified URL with binary data, including optional
    query parameters and authentication.
    delete_request: Sends a DELETE request to a specified URL without query parameters but with
    optional authentication.
    delete_request_with_params: Sends a DELETE request to a specified URL with query parameters
    and optional authentication.
    create_request: Constructs a request object with the specified parameters.
    create_request_with_encoded_data: Constructs a request object with specified parameters and
    encoded data.
    create_request_with_raw_data: Constructs a request object for sending data as raw JSON,
    including handling of query parameters.
    process_request: Processes a given request, sending it to the specified endpoint and updating
    the return value object with the response.
    send_request: Sends a prepared request using the requests library, optionally applying
    authentication data.
    make_request: Sends a request using a session from the requests library, with optional
    authentication.
    post_request_with_raw_data: Sends a POST request with raw data to a specified URL,
    including optional query parameters and authentication.

Utilities:
    correlated_id: Generates or retrieves a correlation ID from the given context.
    from_context: Retrieves a string value from a context dictionary based on a given key.
"""

import json
import os
import uuid
from dataclasses import fields
from enum import Enum
from typing import Any, List
from urllib.parse import urljoin, urlencode

import requests

from ....bootstrap.utils import convert_dict_keys_to_lower_camelcase
from ....contracts.clients.interfaces.authinjector import AuthenticationInjector
from ....contracts.common import constants
from ....contracts import errors
from ....contracts.clients.utils.common import convert_any_to_dict


ERROR_MSG_1 = "failed to parse baseUrl and requestPath"


class HTTPMethod(Enum):
    """
    Enumeration of common HTTP methods for use in constructing requests.
    """
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


# pylint: disable=too-many-arguments, too-many-positional-arguments
def get_request(context: dict,
                return_value_pointer: Any,
                base_url: str,
                request_path: str,
                request_params: dict[str, List[str]] | None,
                auth_injector: AuthenticationInjector | None):
    """
    Initiates a GET request to a specified URL with optional query parameters and authentication.

    This function constructs and sends a GET request to a service endpoint. It allows for the
    inclusion of query parameters and supports injecting authentication data into the request.
    The response is processed and mapped onto a provided return value object.

    Parameters:
        context (dict): A dictionary containing context-specific data for the request.
        return_value_pointer (Any): An object that will hold the processed response data.
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        request_params (dict[str, List[str]] | None): Optional dictionary of query parameters to
        include in the request.
        auth_injector (AuthenticationInjector | None): Optional authentication injector for adding
        authentication data to the request.

    Raises:
        errors.EdgeX: If an error occurs during request creation or processing.
    """
    if request_params is None:
        request_params = {}
    try:
        req = create_request(context, HTTPMethod.GET.value, base_url, request_path, request_params)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)

#  pylint: disable=too-many-arguments, too-many-positional-arguments
def get_request_with_body_raw_data(context: dict,
                                   return_value_pointer: Any,
                                   base_url: str,
                                   request_path: str,
                                   request_params: dict[str, List[str]] | None,
                                   data: Any,
                                   auth_injector: AuthenticationInjector | None):
    """
    get_request_with_body_raw_data makes the GET request with JSON raw data as request body and
    return the response
    """
    try:
        req = create_request_with_raw_data(context, HTTPMethod.GET.value, base_url, request_path,
                                           request_params, data)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)


def create_request(context: dict,
                   http_method: str,
                   base_url: str,
                   request_path: str,
                   request_params: dict[str, List[str]] | None) -> requests.Request:
    """
    Constructs a request object with the specified parameters.

    This function prepares a request object using the provided HTTP method, base URL, request path,
    and optional query parameters. It also includes a correlation ID in the request headers to
    facilitate tracing the request across different services or components.

    Parameters:
        context (dict): A dictionary containing context-specific data for the request, used to
                        extract the correlation ID.
        http_method (str): The HTTP method to be used for the request (e.g., 'GET', 'POST').
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        request_params (dict[str, List[str]] | None): Optional dictionary of query parameters to
                                                      include in the request.

    Returns:
        requests.Request: The constructed request object.
    """
    try:
        u = urljoin(base_url, request_path)
    except Exception as err:
        raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR, ERROR_MSG_1, err)

    if request_params:
        u = f"{u}?{urlencode(request_params)}"

    req = requests.Request(http_method, u)
    req.headers[constants.CORRELATION_HEADER] = correlated_id(context)
    return req


def correlated_id(context: dict) -> str:
    """
    Generates or retrieves a correlation ID from the given context.

    This function checks the provided context dictionary for an existing correlation ID under a
    predefined key. If found, it returns this ID. If not, it generates a new UUID4 string to be
    used as a correlation ID. This ensures that each request or transaction can be uniquely
    identified, facilitating tracing and debugging across different services or components.

    Parameters:
        context (dict): A dictionary potentially containing a correlation ID.

    Returns:
        str: A correlation ID, either retrieved from the context or newly generated.
    """
    correlation = context.get(constants.CORRELATION_HEADER)
    if not correlation:
        correlation = str(uuid.uuid4())
    return correlation


def from_context(ctx: dict, key: str) -> str:
    """
    Retrieves a string value from a context dictionary based on a given key.

    This function looks up a key in the provided context dictionary and returns its value if it is
    a string. If the key does not exist or the value is not a string, an empty string is returned.
    This is useful for safely extracting string values from dictionaries without raising exceptions
    for missing keys or type mismatches.

    Parameters:
        ctx (dict): The context dictionary from which to retrieve the value.
        key (str): The key for the value to be retrieved.

    Returns:
        str: The value associated with the key if it exists and is a string; otherwise,
        an empty string.
    """
    value = ctx.get(key)
    if not isinstance(value, str):
        value = ""
    return value


def process_request(return_value_object: Any, req: requests.Request,
                    auth_injector: AuthenticationInjector):
    """
    Processes a given request, sending it to the specified endpoint and updating the return value
    object with the response.

    This function is responsible for sending a prepared request to its destination, optionally
    using an authentication injector for adding authentication data. After sending the request,
    it processes the response by decoding it and updating the provided return value object with
    the response data, ensuring the data matches the structure of the return value object's type.

    Parameters:
        return_value_object (Any): An object that will be updated with the data from the response.
        req (requests.Request): The prepared request object to be sent.
        auth_injector (AuthenticationInjector): An optional authentication injector that can add
                                                authentication data to the request before it is
                                                sent.

    Raises:
        errors.EdgeX: If an error occurs during the request sending or response processing, an
                      appropriate EdgeX error is raised to indicate the failure.

    Note:
        The function assumes that the response data is in JSON format and attempts to decode it
        accordingly. It also relies on the structure of the return value object to filter and map
        the response data correctly.
    """
    try:
        resp = send_request(req, auth_injector)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    if not resp:
        return

    try:
        # loads the response body into a dictionary and converts the keys to lower camel case
        data_dict = json.loads(resp.decode('utf-8'))
        data_dict_lcc = convert_dict_keys_to_lower_camelcase(data_dict)

        if isinstance(return_value_object, list):
            # if the return value object is a list, we assume that the list must contain a single
            # item representing the target dataclass instance as response. the response body is a
            # list of dictionaries, and we convert each dictionary into a dataclass instance
            return_value_type = type(return_value_object[0])
            return_value_object.clear()
            for item in data_dict_lcc:
                dataclass_instance = return_value_type.from_dict(item)
                return_value_object.append(dataclass_instance)
            return

        # get the type of return value object and then decode the response body (in dict) into the
        # dataclass_instance using dataclass_json library. note that the from_dict method only
        # available when the dataclass is decorated with @dataclass_json
        return_value_type = type(return_value_object)
        dataclass_instance = return_value_type.from_dict(data_dict_lcc)

        # the dataclass_instance is newly created and returned from from_dict, we need to copy the
        # data from the dataclass_instance to the return_value_object
        for field in fields(return_value_type):
            setattr(return_value_object, field.name, getattr(dataclass_instance, field.name))
    except Exception as err:
        raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                      "failed to parse the response body", err)


def send_request(req: requests.Request, auth_injector: AuthenticationInjector) -> bytes:
    """
    Sends a prepared request using the requests library, optionally applying authentication data.

    This function takes a prepared request object and an optional authentication injector. If an
    authentication injector is provided, it applies authentication data to the request.
    The request is then sent, and the response content is returned as bytes. If the response
    indicates a failure (status code greater than 207), an error is raised.

    Parameters:
        req (requests.Request): The prepared request object to be sent.
        auth_injector (AuthenticationInjector): An optional object capable of adding authentication
                                               data to the request.

    Returns:
        bytes: The content of the response, expected to be in bytes.

    Raises:
        errors.EdgeX: If the request fails (based on the status code of the response) or if any
                      other error occurs during the request sending process, an appropriate EdgeX
                      error is raised to indicate the failure.
    """
    try:
        resp = make_request(req, auth_injector)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    if resp.status_code <= 207:
        return resp.content

    msg = f"request failed, status code: {resp.status_code}, err: {resp.text}"
    err_kind = errors.kind_mapping(resp.status_code)
    raise errors.new_common_edgex(err_kind, msg)


def make_request(req: requests.Request, auth_injector: AuthenticationInjector):
    """
    Sends a request using a session from the requests library, with optional authentication.

    This function creates a session and optionally configures it with authentication data using an
    authentication injector. It then sends the prepared request through this session. This approach
    allows for more complex HTTP interactions, such as those requiring authentication or session
    persistence.

    Parameters:
        req (requests.Request): The prepared request object to be sent.
        auth_injector (AuthenticationInjector): An optional authentication injector that can add
                                                authentication data to the request before it is
                                                sent.

    Returns:
        requests.Response: The response object received after sending the request.

    Raises:
        errors.EdgeX: Wraps and raises any exceptions encountered during the request sending
                      process as an EdgeX error, providing a unified error handling mechanism.
    """
    client = requests.Session()

    if auth_injector:
        try:
            auth_injector.add_authentication_data(req)
            adapter = auth_injector.round_tripper()
            if adapter:
                # It's fine to use http within the EdgeX network.
                client.mount('http://', adapter)  # NOSONAR
                client.mount('https://', adapter)
        except Exception as err:
            raise errors.new_common_edgex_wrapper(err)

    try:
        resp = client.send(req.prepare())
    except Exception as err:
        raise errors.new_common_edgex(errors.ErrKind.SERVICE_UNAVAILABLE,
                                      "failed to send a http request", err)

    if resp is None:
        raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                      "the response should not be None")

    return resp


#  pylint: disable=too-many-arguments, too-many-positional-arguments
def post_request(ctx: dict,
                 return_value_pointer,
                 base_url: str,
                 request_path: str,
                 data: bytes,
                 encoding: str,
                 auth_injector: AuthenticationInjector):
    """
    Sends a POST request to a specified URL with data and optional authentication.

    This function constructs and sends a POST request to a service endpoint, including the
    specified data in the request body. It supports specifying the content encoding of the data and
    injecting authentication data into the request. The response is processed and mapped onto a
    provided return value object.

    Parameters:
        ctx (dict): A dictionary containing context-specific data for the request.
        return_value_pointer (Any): An object that will hold the processed response data.
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        data (bytes): The data to be sent in the request body.
        encoding (str): The encoding of the data being sent.
        auth_injector (AuthenticationInjector): Optional authentication injector for adding
                                                authentication data to the request.

    Raises:
        errors.EdgeX: If an error occurs during request creation or processing.
    """
    try:
        req = create_request_with_encoded_data(ctx, HTTPMethod.POST.value, base_url,
                                               request_path, data, encoding)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)


def create_request_with_encoded_data(ctx: dict,  # pylint: disable=too-many-arguments
                                     http_method: str,
                                     base_url: str,
                                     request_path: str,
                                     data: bytes,
                                     encoding: str) -> requests.Request:
    """
    Constructs a request object with specified parameters and encoded data.

    This function prepares a request object using the provided HTTP method, base URL, request path,
    and data. It sets the content type of the request based on the specified encoding or retrieves
    it from the context if not explicitly provided. A correlation ID is also included in the
    request headers to facilitate tracing the request across different services or components.

    Parameters:
        ctx (dict): A dictionary containing context-specific data for the request, used to extract
                    the correlation ID and default content type if the encoding is not specified.
        http_method (str): The HTTP method to be used for the request (e.g., 'GET', 'POST').
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        data (bytes): The data to be sent in the request body, already encoded.
        encoding (str): The encoding of the data being sent. If not specified, the content type
                        will be retrieved from the context.

    Returns:
        requests.Request: The constructed request object, ready to be sent.
    """
    try:
        url = urljoin(base_url, request_path)
    except Exception as err:
        raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR, ERROR_MSG_1, err)

    content = encoding if encoding else ctx.get(constants.CONTENT_TYPE,
                                                constants.CONTENT_TYPE_JSON)

    req = requests.Request(http_method, url, data=data)
    req.headers[constants.CONTENT_TYPE] = content
    req.headers[constants.CORRELATION_HEADER] = correlated_id(ctx)
    return req


# pylint: disable=too-many-arguments, too-many-positional-arguments
def post_request_with_raw_data(ctx: dict,
                               return_value_pointer,
                               base_url: str,
                               request_path: str,
                               request_params: dict[str, List[str]] | None,
                               data: Any,
                               auth_injector: AuthenticationInjector):
    """
    Sends a POST request with raw data to a specified URL, including optional query parameters and
    authentication.

    This function constructs and sends a POST request to a service endpoint, directly including the
    provided data in the request body. It supports the inclusion of query parameters and the
    injection of authentication data into the request. The response is processed and mapped onto a
    provided return value object.

    Parameters:
        ctx (dict): A dictionary containing context-specific data for the request.
        return_value_pointer (Any): An object that will hold the processed response data.
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        request_params (dict[str, List[str]] | None): Optional dictionary of query parameters to
        include in the request.
        data (Any): The data to be sent in the request body. If the data is an object, it will be
        converted to a dictionary.
        auth_injector (AuthenticationInjector): Optional authentication injector for adding
        authentication data to the request.

    Raises:
        errors.EdgeX: If an error occurs during request creation or processing.
    """
    try:
        req = create_request_with_raw_data(ctx, HTTPMethod.POST.value, base_url, request_path,
                                           request_params, data)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)


# pylint: disable=too-many-positional-arguments
def post_by_file_request(ctx: dict,
                         return_value_pointer,
                         base_url: str,
                         request_path: str,
                         file_path: str,
                         auth_injector: AuthenticationInjector):
    """
    Sends a POST request to a specified URL with the specified file as the request body.
    """
    try:
        req = create_request_from_file_path(ctx, HTTPMethod.POST.value, base_url, request_path,
                                            file_path)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)


def put_by_file_request(ctx: dict,
                        return_value_pointer,
                        base_url: str,
                        request_path: str,
                        file_path: str,
                        auth_injector: AuthenticationInjector):
    """
    Sends a PUT request to a specified URL with the specified file as the request body.
    """
    try:
        req = create_request_from_file_path(ctx, HTTPMethod.PUT.value, base_url, request_path,
                                            file_path)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)


def create_request_from_file_path(ctx: dict,
                                  http_method: str,
                                  base_url: str,
                                  request_path: str,
                                  file_path: str) -> requests.Request:
    """
    creates multipart/form-data request with the specified file at file_path.
    """
    try:
        url = urljoin(base_url, request_path)
    except Exception as e:
        raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR, ERROR_MSG_1, e)
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
        files = {'file': (os.path.basename(file_path), content)}
        req = requests.Request(http_method, url, files=files)
    except Exception as e:
        raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                      f"failed to read file content from {file_path}", e)

    req.headers[constants.CORRELATION_HEADER] = correlated_id(ctx)

    return req


# pylint: disable=too-many-arguments, too-many-positional-arguments
def create_request_with_raw_data(ctx: dict,
                                 http_method: str,
                                 base_url: str,
                                 request_path: str,
                                 request_params: dict[str, List[str]],
                                 data: Any) -> requests.Request:
    """
    Constructs a request object for sending data as raw JSON, including handling of query
    parameters.

    This function prepares a request object with the specified HTTP method, URL constructed from
    the base URL and request path, and data to be sent as raw JSON. It supports adding query
    parameters to the URL. The function also ensures that the appropriate content type is set in
    the request headers, along with a correlation ID for tracing. The data is serialized to JSON
    if it's not already a string.

    Parameters:
        ctx (dict): Context dictionary containing additional information such as the
        correlation ID.
        http_method (str): The HTTP method to be used for the request.
        base_url (str): The base URL of the service to which the request is being sent.
        request_path (str): The path to the specific resource or endpoint.
        request_params (dict[str, List[str]]): Query parameters to be appended to the URL.
        data (Any): The data to be sent in the request body. If it's an object,
        it will be converted to a dictionary.

    Returns:
        requests.Request: The constructed request object, ready to be sent.

    Raises:
        errors.EdgeX: If there's an error in constructing the URL or serializing the data to JSON.
    """
    try:
        url = urljoin(base_url, request_path)
    except Exception as e:
        raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR, ERROR_MSG_1, e)

    if request_params:
        url += '?' + urlencode(request_params, doseq=True)

    try:
        json_encoded_data = json.dumps(convert_any_to_dict(data)).encode('utf-8')
    except Exception as e:
        raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                      "failed to encode input data to JSON", e)

    content = from_context(ctx, constants.CONTENT_TYPE)
    if not content:
        content = constants.CONTENT_TYPE_JSON

    try:
        req = requests.Request(http_method, url, data=json_encoded_data)
    except Exception as e:
        raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                      "failed to create a http request", e)

    req.headers[constants.CONTENT_TYPE] = content
    req.headers[constants.CORRELATION_HEADER] = correlated_id(ctx)

    return req


# pylint: disable=too-many-arguments, too-many-positional-arguments
def put_request(ctx: dict,
                return_value_pointer,
                base_url: str,
                request_path: str,
                request_params: dict[str, List[str]] | None,
                data: Any,
                auth_injector: AuthenticationInjector):
    """
    Sends a PUT request to a specified URL with data and optional query parameters and
    authentication.

    This function constructs and sends a PUT request to a service endpoint, directly including the
    provided data in the request body. It supports the inclusion of query parameters and the
    injection of authentication data into the request. The response is processed and mapped onto a
    provided return value object.

    Parameters:
        ctx (dict): A dictionary containing context-specific data for the request.
        return_value_pointer (Any): An object that will hold the processed response data.
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        request_params (dict[str, List[str]] | None): Optional dictionary of query parameters to
        include in the request.
        data (Any): The data to be sent in the request body. If the data is an object, it will be
        converted to a dictionary.
        auth_injector (AuthenticationInjector): Optional authentication injector for adding
        authentication data to the request.

    Raises:
        errors.EdgeX: If an error occurs during request creation or processing.
    """
    try:
        req = create_request_with_raw_data(ctx, HTTPMethod.PUT.value, base_url, request_path,
                                           request_params, data)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)


# pylint: disable=too-many-arguments, too-many-positional-arguments
def patch_request(ctx: dict,
                  return_value_pointer,
                  base_url: str,
                  request_path: str,
                  request_params: dict[str, List[str]] | None,
                  data: bytes,
                  auth_injector: AuthenticationInjector):
    """
    Sends a PATCH request to a specified URL with binary data, including optional query parameters
    and authentication.

    This function constructs and sends a PATCH request to a service endpoint, directly including
    the provided binary data in the request body. It supports the inclusion of query parameters and
    the injection of authentication data into the request. The response is processed and mapped
    onto a provided return value object.

    Parameters:
        ctx (dict): A dictionary containing context-specific data for the request.
        return_value_pointer (Any): An object that will hold the processed response data.
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        request_params (dict[str, List[str]] | None): Optional dictionary of query parameters to
        include in the request.
        data (bytes): The binary data to be sent in the request body.
        auth_injector (AuthenticationInjector): Optional authentication injector for adding
        authentication data to the request.

    Raises:
        errors.EdgeX: If an error occurs during request creation or processing.
    """
    try:
        req = create_request_with_raw_data(ctx, HTTPMethod.PATCH.value, base_url, request_path,
                                           request_params, data)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)


def delete_request(ctx: dict,
                   return_value_pointer,
                   base_url: str,
                   request_path: str,
                   auth_injector: AuthenticationInjector):
    """
    Sends a DELETE request to a specified URL without query parameters but with optional
    authentication.

    This function constructs and sends a DELETE request to a service endpoint. It does not support
    query parameters in this variant of the function. Authentication data can be injected into the
    request if an authentication injector is provided. The response is processed and mapped onto a
    provided return value object.

    Parameters:
        ctx (dict): A dictionary containing context-specific data for the request.
        return_value_pointer (Any): An object that will hold the processed response data.
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        auth_injector (AuthenticationInjector): Optional authentication injector for adding
                                                authentication data to the request.

    Raises:
        errors.EdgeX: If an error occurs during request creation or processing.
    """
    try:
        req = create_request(ctx, HTTPMethod.DELETE.value, base_url, request_path, None)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)


# pylint: disable=too-many-arguments, too-many-positional-arguments
def delete_request_with_params(ctx: dict,
                               return_value_pointer,
                               base_url: str,
                               request_path: str,
                               request_params: dict[str, List[str]],
                               auth_injector: AuthenticationInjector):
    """
    Sends a DELETE request to a specified URL with query parameters and optional authentication.

    This function constructs and sends a DELETE request to a service endpoint, including query
    parameters in the request. It supports injecting authentication data into the request if an
    authentication injector is provided. The response is processed and mapped onto a provided
    return value object.

    Parameters:
        ctx (dict): A dictionary containing context-specific data for the request.
        return_value_pointer (Any): An object that will hold the processed response data.
        base_url (str): The base URL of the service to which the request is made.
        request_path (str): The specific path of the service endpoint.
        request_params (dict[str, List[str]]): Dictionary of query parameters to include
        in the request.
        auth_injector (AuthenticationInjector): Optional authentication injector for adding
                                                authentication data to the request.

    Raises:
        errors.EdgeX: If an error occurs during request creation or processing.
    """
    try:
        req = create_request(ctx, HTTPMethod.DELETE.value, base_url, request_path, request_params)
    except errors.EdgeX as err:
        raise errors.new_common_edgex_wrapper(err)

    return process_request(return_value_pointer, req, auth_injector)
