# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module provides the classes and functions for AppFunctionContext
"""
import re
from typing import Tuple, Any

from ..bootstrap.container.clients import event_client_from, reading_client_from, \
    command_client_from, device_service_client_from, device_profile_client_from, device_client_from
from ..bootstrap.container.configuration import configuration_from
from ..bootstrap.container.logging import logging_client_from
from ..bootstrap.container.messaging import messaging_client_from
from ..bootstrap.container.metrics import metrics_manager_from
from ..bootstrap.container.secret import secret_provider_from
from ..bootstrap.di.container import Container
from ..bootstrap.interface.metrics import MetricsManager
from ..constants import KEY_PIPELINEID
from ..bootstrap.interface.secret import SecretProvider
from ..contracts.clients.interfaces.command import CommandClientABC
from ..contracts.clients.interfaces.device import DeviceClientABC
from ..contracts.clients.interfaces.deviceprofile import DeviceProfileClientABC
from ..contracts.clients.interfaces.deviceservice import DeviceServiceClientABC
from ..contracts.clients.interfaces.event import EventClientABC
from ..contracts.clients.interfaces.reading import ReadingClientABC
from ..contracts.clients.logger import Logger
from ..contracts import errors
from ..contracts.common.utils import build_topic
from ..contracts.dtos.deviceresource import DeviceResource
from ..interfaces import AppFunctionContext
from ..interfaces.messaging import new_message_envelope


# pylint: disable=too-many-public-methods
class Context(AppFunctionContext):
    """ AppFunctionContext implementation. """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, correlation_id: str, dic: Container, input_content_type: str):
        self._correlation_id = correlation_id
        self._dic = dic
        self._input_content_type = input_content_type
        self._response_data = None
        self._response_content_type = None
        self._retry_data = bytes()
        self.trigger_retry = False
        self._context_data = {}
        self._value_placeholder_spec = re.compile("{[^}]*}")

    # pylint: disable=protected-access
    def clone(self) -> AppFunctionContext:
        """ Clones the context. """
        ctx_data_copy = {}
        for key, value in self._context_data.items():
            ctx_data_copy[key] = value
        clone_ctx = Context(self._correlation_id, self._dic, self._input_content_type)
        clone_ctx._response_data = self._response_data
        clone_ctx._response_content_type = self._response_content_type
        clone_ctx._retry_data = self._retry_data
        clone_ctx._context_data = ctx_data_copy
        return clone_ctx

    def set_correlation_id(self, correlation_id: str):
        """ Sets the correlation_id. """
        self._correlation_id = correlation_id

    def correlation_id(self) -> str:
        """ Returns the correlation_id. """
        return self._correlation_id

    def set_input_content_type(self, input_content_type: str):
        self._input_content_type = input_content_type

    def input_content_type(self) -> str:
        """ Returns the input_content_type. """
        return self._input_content_type

    def set_response_data(self, data: bytes):
        """ Sets the response_data. """
        self._response_data = data

    def response_data(self) -> bytes:
        """ Returns the response_data. """
        return self._response_data

    def set_response_content_type(self, content_type: str):
        """ Sets the response content_type. """
        self._response_content_type = content_type

    def response_content_type(self) -> str:
        """ Returns the response content_type. """
        return self._response_content_type

    def set_retry_data(self, data: bytes):
        """ Sets the retry data. """
        self._retry_data = data

    def retry_data(self) -> bytes:
        """ Gets the retry data. """
        return self._retry_data

    def trigger_retry_failed_data(self):
        """ sets the flag to trigger retry of failed data """
        self.trigger_retry = True

    def clear_retry_trigger_flag(self):
        """ Clears the flag to trigger retry of failed data.
        This function is not part of the AppFunctionContext interface,
        so it is internal SDK use only """
        self.trigger_retry = False

    def is_retry_triggered(self) -> bool:
        """ Gets the flag to trigger retry of failed data.
        This function is not part of the AppFunctionContext interface,
        so it is internal SDK use only """
        return self.trigger_retry

    def secret_provider(self) -> SecretProvider:
        """ Returns the secret_provider. """
        return secret_provider_from(self._dic.get)

    def logger(self) -> Logger:
        """ Returns the logger. """
        return logging_client_from(self._dic.get)

    def pipeline_id(self) -> str:
        pipelineid, exists = self.get_value(KEY_PIPELINEID)
        if exists:
            return pipelineid
        return ""

    def add_value(self, key: str, value: str):
        self._context_data[key.lower()] = value

    def remove_value(self, key: str):
        del self._context_data[key.lower()]

    def get_value(self, key: str) -> Tuple[str, bool]:
        if key in self._context_data:
            return self._context_data[key], True
        return "", False

    def get_values(self) -> dict:
        return self._context_data.copy()

    def apply_values(self, str_format: str) -> str:
        attempts = {}
        result = str_format

        targets = self._value_placeholder_spec.findall(str_format)

        for placeholder in targets:
            if placeholder in attempts:
                continue

            key = str(placeholder).lstrip("{").rstrip("}")

            value, found = self.get_value(key)

            attempts[placeholder] = found

            if found:
                result = result.replace(placeholder, value)

        for _, succeeded in attempts.items():
            if not succeeded:
                raise errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"failed to replace all context placeholders in "
                    f"input ('{result}' after replacements)"
                )

        return result

    def get_device_resource(self, device_name: str, resource_name: str) -> DeviceResource:
        """
        get_device_resource retrieves the DeviceResource for given profileName and resourceName
        """
        device_profile_client  = self.device_profile_client()
        if device_profile_client is None:
            raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                          "device profile client not initialized. Core "
                                          "Metadata is missing from clients configuration")
        res = device_profile_client.device_resource_by_profile_name_and_resource_name({},
                                                                                      device_name,
                                                                                      resource_name)
        return res.resource

    def publish_with_topic(self, topic: str, data: Any, content_type: str):
        """
        publish_with_topic pushes data to the MessageBus using given topic
        """
        messaging_client = messaging_client_from(self._dic.get)
        if messaging_client is None:
            raise ValueError("MessageBus client not available")

        config = configuration_from(self._dic.get)
        if config is None:
            raise ValueError("Configuration not available")

        message = new_message_envelope(data, content_type)

        full_topic = build_topic(build_topic(config.MessageBus.BaseTopicPrefix, topic))

        messaging_client.publish(message, full_topic)

    def publish(self, data: Any, content_type: str):
        """
        publish pushes data to the MessageBus using configured topic
        """
        config = configuration_from(self._dic.get)
        if config is None:
            raise ValueError("Configuration not available")
        self.publish_with_topic(config.Trigger.PublishTopic, data, content_type)

    def device_client(self) -> DeviceClientABC:
        """
        device_client returns the device client instance
        """
        return device_client_from(self._dic.get)

    def device_profile_client(self) -> DeviceProfileClientABC:
        """
        device_profile_client returns the device profile client instance
        """
        return device_profile_client_from(self._dic.get)

    def device_service_client(self) -> DeviceServiceClientABC:
        """
        device_service_client returns the device service client instance
        """
        return device_service_client_from(self._dic.get)

    def command_client(self) -> CommandClientABC:
        """
        command_client returns the command client instance
        """
        return command_client_from(self._dic.get)

    def reading_client(self) -> ReadingClientABC:
        """
        reading_client returns the reading client instance
        """
        return reading_client_from(self._dic.get)

    def event_client(self) -> EventClientABC:
        """
        event_client returns the event client instance
        """
        return event_client_from(self._dic.get)

    def metrics_manager(self) -> MetricsManager:
        """
        Return the Metrics Manager used to register counter, gauge, gaugeFloat64 or timer metrics.
        """
        return metrics_manager_from(self._dic.get)
