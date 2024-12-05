# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""

This package defines the interfaces for App Functions SDK.

Classes:
    Secrets: Represents a dictionary of secrets with string keys and values.
    SecretProvider: An abstract base class that defines the interface for a secret provider.
    AppFunctionContext: An abstract base class that defines the interface for an application
    function context.
    ApplicationService: An abstract base class that defines the interface for an application
    service.
"""
import inspect
import threading
from abc import ABC, abstractmethod
from typing import Callable, Tuple, List, Any, Dict, Optional

from pyformance import meters

from .messaging import MessageEnvelope
from ..bootstrap.di.container import Container
from ..bootstrap.interface.metrics import MetricsManager
from ..bootstrap.interface.secret import SecretProvider
from ..contracts.clients.interfaces.command import CommandClientABC
from ..contracts.clients.interfaces.device import DeviceClientABC
from ..contracts.clients.interfaces.deviceprofile import DeviceProfileClientABC
from ..contracts.clients.interfaces.deviceservice import DeviceServiceClientABC
from ..contracts.clients.interfaces.event import EventClientABC
from ..contracts.clients.interfaces.reading import ReadingClientABC
from ..contracts.clients.logger import Logger
from ..contracts.dtos.deviceresource import DeviceResource
from ..internal.common.config import TriggerInfo, ConfigurationStruct
from ..registry.interface import Client
from ..sync.waitgroup import WaitGroup


# pylint: disable=too-many-public-methods
class AppFunctionContext(ABC):
    """
    An abstract base class that defines the interface for an application function context.

    This class provides an interface for cloning the context, getting and setting response data and
    content type, triggering retry for failed data, getting the secret provider, and getting the
    logger.

    Methods:
        clone() -> 'AppFunctionContext': Clones the context.
        correlation_id() -> str: Gets the correlation ID.
        input_content_type() -> str: Gets the input content type.
        set_response_data(data: bytes): Sets the response data.
        response_data() -> bytes: Gets the response data.
        set_response_content_type(content_type: str): Sets the response content type.
        response_content_type() -> str: Gets the response content type.
        set_retry_data(data: bytes): Sets the retry data.
        trigger_retry_failed_data(): Triggers retry for failed data.
        secret_provider() -> SecretProvider: Gets the secret provider.
        logger() -> 'Logger': Gets the logger.
    """

    @abstractmethod
    def clone(self) -> 'AppFunctionContext':
        """
        Clones the context.

        Returns:
            A clone of the context.
        """

    @abstractmethod
    def correlation_id(self) -> str:
        """
        Gets the correlation ID.

        Returns:
            The correlation ID.
        """

    @abstractmethod
    def set_correlation_id(self, correlation_id: str):
        """
        Sets the correlation ID.
        """

    @abstractmethod
    def input_content_type(self) -> str:
        """
        Gets the input content type.

        Returns:
            The input content type.
        """

    @abstractmethod
    def set_input_content_type(self, input_content_type: str):
        """
        Sets the input content type.
        """

    @abstractmethod
    def set_response_data(self, data: bytes):
        """
        Sets the response data.

        Args:
            data: The response data.
        """

    @abstractmethod
    def response_data(self) -> bytes:
        """
        Gets the response data.

        Returns:
            The response data.
        """

    @abstractmethod
    def set_response_content_type(self, content_type: str):
        """
        Sets the response content type.

        Args:
            content_type: The response content type.
        """

    @abstractmethod
    def response_content_type(self) -> str:
        """
        Gets the response content type.

        Returns:
            The response content type.
        """

    @abstractmethod
    def set_retry_data(self, data: bytes):
        """
        Sets the retry data.

        Args:
            data: The retry data.
        """

    @abstractmethod
    def retry_data(self) -> bytes:
        """
        Gets the retry data.
        """

    @abstractmethod
    def trigger_retry_failed_data(self):
        """
        Triggers retry for failed data.
        """

    @abstractmethod
    def secret_provider(self) -> SecretProvider:
        """
        Gets the secret provider.

        Returns:
            The secret provider.
        """

    @abstractmethod
    def logger(self) -> 'Logger':
        """
        Gets the logger.

        Returns:
            The logger.
        """

    @abstractmethod
    def pipeline_id(self) -> str:
        """
        Gets the pipeline ID.

        Returns:
            The pipeline ID.
        """

    @abstractmethod
    def add_value(self, key: str, value: str):
        """
        Adds the key and value to context_data.

        Returns:
            The pipeline ID.
        """

    @abstractmethod
    def remove_value(self, key: str):
        """
        Deletes a value stored in the context at the given key
        """

    @abstractmethod
    def get_value(self, key: str) -> Tuple[str, bool]:
        """
        Attempts to retrieve a value stored in the context at the given key
        """

    @abstractmethod
    def get_values(self) -> dict:
        """
        GetAllValues returns a read-only copy of all data stored in the context
        """

    @abstractmethod
    def apply_values(self, str_format: str) -> str:
        """
        apply_values looks in the provided string for placeholders of the form
        '{any-value-key}' and attempts to replace with the value stored under
        the key in context storage.  An error will be returned if any placeholders
        are not matched to a value in the context.
        """

    @abstractmethod
    def get_device_resource(self, device_name: str, resource_name: str) -> DeviceResource:
        """
        get_device_resource retrieves the DeviceResource for given profileName and resourceName
        """

    @abstractmethod
    def event_client(self) -> EventClientABC:
        """
        event_client returns the event client instance
        """

    @abstractmethod
    def reading_client(self) -> ReadingClientABC:
        """
        reading_client returns the reading client instance
        """

    @abstractmethod
    def command_client(self) -> CommandClientABC:
        """
        command_client returns the command client instance
        """

    @abstractmethod
    def device_service_client(self) -> DeviceServiceClientABC:
        """
        device_service_client returns the device service client instance
        """

    @abstractmethod
    def device_profile_client(self) -> DeviceProfileClientABC:
        """
        device_profile_client returns the device profile client instance
        """

    @abstractmethod
    def device_client(self) -> DeviceClientABC:
        """
        device_client returns the device client instance
        """

    @abstractmethod
    def metrics_manager(self) -> MetricsManager:
        """
        metrics_manager returns the Metrics Manager used to register counter, gauge, gaugeFloat64
        or timer metrics.
        """

    @abstractmethod
    def publish(self, data: Any, content_type: str):
        """
        publish pushes data to the MessageBus using configured topic
        """

    @abstractmethod
    def publish_with_topic(self, topic: str, data: Any, content_type: str):
        """
        publish_with_topic pushes data to the MessageBus using given topic
        """


Deferred = Callable[[], None]
AppFunction = Callable[[AppFunctionContext, Any], Tuple[bool, Any]]


def validate_app_function(func: AppFunction):
    """
    Validates the application function.
    """
    sig = inspect.signature(func)

    expected_params = (AppFunctionContext, Any)
    expected_return = Tuple[bool, Any]

    # Check the parameter types
    params = list(sig.parameters.values())
    if len(params) != len(expected_params):
        raise TypeError("function must accept exactly two arguments")

    for param, expected_type in zip(params, expected_params):
        if param.annotation != expected_type:
            raise TypeError(f"parameter {param.name} must be of type {expected_type}")

    # Check the return type
    if sig.return_annotation != expected_return:
        raise TypeError(f"function must return {expected_return}")


def calculate_pipeline_hash(*transforms: AppFunction) -> str:
    """
    Calculates the hash for a pipeline.

    Args:
        transforms: The pipeline to calculate the hash for.

    Returns:
        The hash for the pipeline.
    """
    result = "Pipeline-functions: "
    for func in transforms:
        result = f"{result} {func.__name__}"
    return result


class FunctionPipeline:  # pylint: disable=too-few-public-methods
    """
    Represents a pipeline of functions to be executed in sequence.

    Attributes:
        pipelineid (str): The unique identifier for the pipeline.
        topics (List[str]): A list of topics associated with the pipeline.
        transforms (List[AppFunction]): A list of functions to be executed in the pipeline.
    """
    def __init__(self, pipelineid: str, topics: List[str], *transforms: AppFunction):
        self.id = pipelineid
        self.transforms = transforms
        self.topics = topics
        self.hash = calculate_pipeline_hash(*transforms)
        self.message_processed = meters.Counter("")
        self.message_processing_time = meters.Timer("")
        self.processing_errors = meters.Counter("")


class Trigger(ABC):  # pylint: disable=too-few-public-methods
    """
    An abstract base class that defines the interface for a trigger.

    This class provides an interface for initializing a trigger, as well as getting the
    trigger type and name.

    Methods:
        initialize: Initializes the trigger with the given context, and wait group.
    """

    @abstractmethod
    def initialize(self, ctx_done: threading.Event, app_wg: WaitGroup) -> Optional[Deferred]:
        """
        initializes the trigger.

        Args:
            ctx_done (threading.Event): An event to signal when the context is done.
            app_wg (WaitGroup): A wait group to manage concurrent tasks.

        Returns:
            Deferred: A deferred function to be executed later.
            errors.EdgeX: An error object if initialization fails.

        Raises:
            RuntimeError: If the trigger fails to initialize.
        """


# TriggerMessageProcessor provides an interface that can be used by custom triggers to
# invoke the runtime.
TriggerMessageProcessor = Callable[[AppFunctionContext, MessageEnvelope], None]

# PipelineResponseHandler provides a function signature that can be passed to MessageProcessor to
# handle pipeline output(s)
PipelineResponseHandler = Callable[[AppFunctionContext, FunctionPipeline], None]

# TriggerMessageHandler provides an interface that can be used by custom triggers to invoke the
# runtime.
TriggerMessageHandler = Callable[
    [Optional[AppFunctionContext], MessageEnvelope, PipelineResponseHandler], None
]

# TriggerContextBuilder provides an interface to construct an AppFunctionContext for message.
TriggerContextBuilder = Callable[[MessageEnvelope], AppFunctionContext]

# TriggerConfigLoader provides an interface that can be used by custom triggers to load
# custom configuration elements.
TriggerConfigLoader = Callable[[Any, str], None]


# pylint: disable=too-few-public-methods
class TriggerConfig:
    """
    Represents the configuration for a trigger.

    This class provides the necessary configuration elements for setting up and managing a trigger.
    It includes the logger, context builder, message handler, and configuration loader.

    Attributes:
        logger (Logger): Exposes the logging client passed from the service.
        context_builder (TriggerContextBuilder): Constructs a context the trigger can specify for
        processing the received message.
        message_received (TriggerMessageHandler): Sends a message to the runtime for processing.
        config_loader (TriggerConfigLoader): A function that can be used to load custom
        configuration sections for the trigger.
    """
    def __init__(self, logger: Logger, context_builder: TriggerContextBuilder,
                 message_received: TriggerMessageHandler,
                 config_loader: TriggerConfigLoader):
        self.logger = logger
        self.context_builder = context_builder
        self.message_received = message_received
        self.config_loader = config_loader


class ApplicationService(ABC):
    """
    An abstract base class that defines the interface for an application service.
    """

    @abstractmethod
    def app_done_event(self) -> threading.Event:
        """
        app_done_event returns the application service threading event used to detect if the service
        is terminating, so that custom app service can appropriately exit any long-running
        functions.

        Returns:
            A threading.Event object
        """

    @abstractmethod
    def add_custom_route(self, route: str, use_auth: bool, handler: Callable,
                         methods: Optional[List[str]] = None):
        """
        Adds a custom route.

        Args:
            route: The route to be added.
            use_auth: Whether to use authentication.
            handler: The handler for the route.
            methods: The methods for the route.
        """

    @abstractmethod
    def logger(self) -> Logger:
        """
        Gets the logger.

        Returns:
            The logger.
        """

    @abstractmethod
    def application_settings(self) -> Dict[str, str]:
        """
        Gets the application settings.

        Returns:
            The application settings.
        """

    @abstractmethod
    def get_application_setting(self, key: str) -> str:
        """
        Gets an application setting.

        Args:
            key: The key of the setting.

        Returns:
            The setting.
        """

    @abstractmethod
    def get_application_setting_strings(self, key: str) -> [str]:
        """
        get_application_setting_strings returns the strings(in list) for the specified App Setting.

        Args:
            key: The key of the setting.

        Returns:
            The list values of the setting.
        """

    @abstractmethod
    def set_default_functions_pipeline(self, *functions: AppFunction):
        """
        Sets the default functions pipeline.

        Args:
            functions: The functions for the pipeline.
        """

    @abstractmethod
    def add_functions_pipeline_for_topics(self,
                                          pipeline_id: str,
                                          topics: List[str],
                                          functions: List[AppFunction]):
        """
        Adds a functions pipeline for topics.

        Args:
            pipeline_id: The ID of the pipeline.
            topics: The topics for the pipeline.
            functions: The functions for the pipeline.
        """

    @abstractmethod
    def remove_all_function_pipelines(self):
        """
        Removes all function pipelines.
        """

    @abstractmethod
    async def run(self):
        """
        Runs the application service.
        """

    @abstractmethod
    def setup_trigger(self, trigger_info: TriggerInfo) -> Trigger:
        """
        Sets up the trigger for the application service.

        This method is responsible for configuring and initializing the trigger mechanism
        that will be used to start and stop the application service. It ensures that the
        trigger is properly set up and ready to handle incoming events or requests.

        Raises:
            RuntimeError: If the trigger setup fails.
        """

    @abstractmethod
    def register_custom_trigger_factory(self, name: str,
                                        factory: Callable[[TriggerConfig], Trigger]):
        """
        register_custom_trigger_factory allows users to register builders for custom trigger types
        """

    @abstractmethod
    def registry_client(self) -> Client:
        """
        device_service_client returns the device service client instance
        """

    @abstractmethod
    def event_client(self) -> EventClientABC:
        """
        event_client returns the event client instance
        """

    @abstractmethod
    def reading_client(self) -> ReadingClientABC:
        """
        reading_client returns the reading client instance
        """

    @abstractmethod
    def command_client(self) -> CommandClientABC:
        """
        command_client returns the command client instance
        """

    @abstractmethod
    def device_service_client(self) -> DeviceServiceClientABC:
        """
        device_service_client returns the device service client instance
        """

    @abstractmethod
    def device_profile_client(self) -> DeviceProfileClientABC:
        """
        device_profile_client returns the device profile client instance
        """

    @abstractmethod
    def device_client(self) -> DeviceClientABC:
        """
        device_client returns the device client instance
        """

    @abstractmethod
    def secret_provider(self) -> SecretProvider:
        """
        Gets the secret provider.

        Returns:
            The secret provider.
        """

    @abstractmethod
    def publish(self, data: Any, content_type: str):
        """
        publish pushes data to the MessageBus using configured topic
        """

    @abstractmethod
    def publish_with_topic(self, topic: str, data: Any, content_type: str):
        """
        publish_with_topic pushes data to the MessageBus using given topic
        """

    @abstractmethod
    def load_custom_config(self, custom_config: Any, section_name: str):
        """
        load the service's custom configuration from local file or the Configuration Provider
        (if enabled) Configuration Provider will also be seeded with the custom configuration
        if service is using the Configuration Provider. UpdateFromRaw interface will be called on
        the custom configuration when the configuration is loaded from the Configuration Provider.
        """

    @abstractmethod
    def listen_for_custom_config_changes(self, config: Any, section_name: str,
                                         changed_callback: Callable[[Any], None]):
        """
        listen_for_custom_config_changes listens for configuration changes for the specified
        configuration section. When a change is detected, the callback function is invoked with
        the updated configuration.
        """

    @abstractmethod
    def dic(self) -> Container:
        """
        dic returns the Dependency Injection Container.
        """

    @abstractmethod
    def get_service_config(self) -> ConfigurationStruct:
        """
        service_config returns the service configuration.
        """
