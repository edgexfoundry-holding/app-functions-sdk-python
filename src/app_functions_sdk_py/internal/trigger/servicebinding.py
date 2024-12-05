# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module defines the `ServiceBinding` abstract base class, which provides an interface for
service bindings in the application.

Classes:
    ServiceBinding: An abstract base class that defines the interface for a service binding,
                    including methods for starting and stopping the service, and accessing
                    configuration, logging, and messaging clients.

Usage:
    This class should be subclassed to create specific service bindings that implement the
    abstract methods defined in the `ServiceBinding` class.

Example:
    class MyServiceBinding(ServiceBinding):
        def decode_message(self, ctx: AppFunctionContext, envelope: MessageEnvelope) -> Any:
            # Implementation here
            pass

        def process_message(self, ctx: AppFunctionContext, data: Any, pipeline: FunctionPipeline):
            # Implementation here
            pass

        def logger(self) -> Logger:
            # Implementation here
            pass

        def config(self) -> ConfigurationStruct:
            # Implementation here
            pass

        def messaging_client(self) -> MessageClient:
            # Implementation here
            pass

        def build_context(self, envelope: MessageEnvelope) -> AppFunctionContext:
            # Implementation here
            pass

        def get_matching_pipelines(self, incoming_topic: str) -> list[FunctionPipeline]:
            # Implementation here
            pass
"""
from abc import ABC, abstractmethod
from typing import Any

from ..common.config import ConfigurationStruct
from ...bootstrap.interface.secret import SecretProvider
from ...contracts.clients.logger import Logger
from ...interfaces import FunctionPipeline, AppFunctionContext
from ...interfaces.messaging import MessageEnvelope, MessageClient


class ServiceBinding(ABC):
    """
    An abstract base class that defines the interface for a service binding.

    This class provides an interface for starting and stopping a service binding, as well as getting
    the service binding type and name.

    Methods:
        start: Starts the service binding.
        stop: Stops the service binding.
        get_type: Gets the service binding type.
        get_name: Gets the service binding name.
    """

    @abstractmethod
    def decode_message(self, ctx: AppFunctionContext, envelope: MessageEnvelope) -> Any:
        """
        decodes the message received in the envelope and returns the data to be processed
        """

    @abstractmethod
    def process_message(self, ctx: AppFunctionContext, data: Any, pipeline: FunctionPipeline):
        """
        provides access to the runtime's ProcessMessage function to process the
        decoded data
        """

    @abstractmethod
    def logger(self) -> Logger:
        """
        provides access to this service's configuration for the trigger
        """

    @abstractmethod
    def config(self) -> ConfigurationStruct:
        """
        provides access to this service's configuration for the trigger
        """

    @abstractmethod
    def messaging_client(self) -> MessageClient:
        """
        provides access to this service's messaging client for the trigger
        """

    @abstractmethod
    def build_context(self, envelope: MessageEnvelope) -> AppFunctionContext:
        """
        builds the context for the message
        """

    @abstractmethod
    def get_matching_pipelines(self, incoming_topic: str) -> list[FunctionPipeline]:
        """
        get_matching_pipelines returns a list of pipelines that match the incoming_topic
        """

    @abstractmethod
    def get_default_pipeline(self) -> FunctionPipeline:
        """
        get_default_pipeline provides access to the runtime's get_defaultPipeline function
        """

    @abstractmethod
    def load_custom_config(self, config: Any, section_name: str):
        """
        load_custom_config provides access to the service's load_custom_config function
        """

    @abstractmethod
    def secret_provider(self) -> SecretProvider:
        """
        secret_provider provides access to this service's secret provider for the trigger
        """
