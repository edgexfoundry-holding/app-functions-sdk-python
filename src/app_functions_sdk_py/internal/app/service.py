# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=too-many-lines
"""
The service module of the App Functions SDK.

This module provides the Service class which is an implementation of the ApplicationService
interface. It provides methods for initializing the service, adding custom routes, and managing the
application context.

Classes:
    Service: An implementation of the ApplicationService interface.
"""
import asyncio
import inspect
import os
import queue
import signal
import sys
import threading
import time
from typing import Any, Dict, List, Callable, Optional

import isodate

from .configupdates import set_pipeline_function_parameter_names_lowercase
from ..store.sqlite.client import new_sqlite_client
from ..trigger.defaultservicebinding import (DefaultTriggerServiceBinding,
                                             DefaultTriggerMessageProcessor)
from ...bootstrap.container.metrics import MetricsManagerInterfaceName, metrics_manager_from
from ...bootstrap.container.store import StoreClientInterfaceName
from ...bootstrap.handlers.auth_middleware import auto_config_authentication_func
from ...bootstrap.interface.metrics import MetricsManager
from ...bootstrap.metrics.manager import Manager
from ...bootstrap.metrics.reporter import MessageBusReporter
from ...bootstrap.utils import camel_to_snake, convert_dict_keys_to_snake_case
from ..constants import API_TRIGGER_ROUTE
from ...bootstrap.interface.secret import SecretProvider
from ...contracts.clients.command import CommandClient
from ...contracts.clients.device import DeviceClient
from ...contracts.clients.deviceprofile import DeviceProfileClient
from ...contracts.clients.deviceservice import DeviceServiceClient
from ...contracts.clients.interfaces.authinjector import AuthenticationInjector
from ...contracts.clients.interfaces.command import CommandClientABC
from ...contracts.clients.interfaces.device import DeviceClientABC
from ...contracts.clients.interfaces.deviceprofile import DeviceProfileClientABC
from ...contracts.clients.interfaces.deviceservice import DeviceServiceClientABC
from ...contracts.clients.interfaces.event import EventClientABC
from ...contracts.clients.interfaces.reading import ReadingClientABC
from ...contracts.clients.reading import ReadingClient
from ...contracts.common.utils import build_topic
from ...contracts.dtos.event import Event
from ...contracts.dtos.metric import Metric
from ...contracts.errors import EdgeX
from ..runtime import FunctionsPipelineRuntime
from ..trigger.http import HttpTrigger
from ..trigger.messagebus import MessageBusTrigger
from ..trigger.mqtt import MqttTrigger
from ...bootstrap.container.clients import EventClientName, CommandClientName, ReadingClientName, \
    DeviceServiceClientName, event_client_from, reading_client_from, command_client_from, \
    device_service_client_from, DeviceProfileClientName, DeviceClientName, \
    device_profile_client_from, device_client_from
from ...bootstrap.container.configuration import ConfigurationName, configuration_from
from ...bootstrap.container.devremotemode import dev_remote_mode_from
from ...bootstrap.container.logging import LoggingClientInterfaceName, logging_client_from
from ...bootstrap.container.messaging import MessagingClientName, messaging_client_from
from ...bootstrap.container.registry import RegistryClientInterfaceName, registry_from
from ...bootstrap.container.secret import secret_provider_ext_from
from ...bootstrap.di.container import Container
from ...bootstrap.secret.jwtsecret import JWTSecretProvider
from ...constants import (TRIGGER_TYPE_MESSAGEBUS, TRIGGER_TYPE_HTTP, TRIGGER_TYPE_MQTT,
                          DEFAULT_PIPELINE_ID, TOPIC_WILDCARD, SPILT_COMMA,
                          SECRET_USERNAME_KEY, SECRET_PASSWORD_KEY)
from ...contracts.clients.event import EventClient
from ...functions.configurable import Configurable
from ...interfaces import (AppFunction, ApplicationService, Deferred, Trigger, TriggerConfig,
                           FunctionPipeline, validate_app_function)
from ...bootstrap.secret.secret import new_secret_provider
from ...contracts.clients.logger import get_logger, Logger
from ...bootstrap import environment
from ...bootstrap.registration.registry import register_with_registry
from ...contracts import errors
from ...bootstrap.commandline import CommandLineParser
from ...bootstrap.timer import new_startup_timer, Timer
from ...bootstrap.config.config import Processor, new_processor_for_custom_config
from ..common.config import (ConfigurationStruct, TriggerInfo, PipelineFunction,
                             DatabaseInfo, Credentials)
from ...contracts.common.constants import CONFIG_STEM_APP, CORE_DATA_SERVICE_KEY, \
    FUNCTION_KEYS_REPLACEMENTS, CORE_COMMAND_SERVICE_KEY, CORE_METADATA_SERVICE_KEY, \
    API_PING_ROUTE, API_CONFIG_ROUTE, API_VERSION_ROUTE, API_SECRET_ROUTE
from ..web_server import server
from ...interfaces.messaging import new_message_envelope
from ...interfaces.store import StoreClient
from ...messaging import new_message_client
from ...registry.interface import Client
from ...sync.waitgroup import WaitGroup
from ... import constants
from ...utils.helper import delete_empty_and_trim


def fatal_error(err: Exception, lc: Logger):
    """
    Logs the error and exits the program.
    """
    lc.error(str(err))
    sys.exit(1)


class Service(ApplicationService):
    """
    An implementation of the ApplicationService interface.

    This class provides methods for initializing the service, adding custom routes, and managing
    the application context.

    Attributes:
        target_type (Any): The target type for the new service.
        service_key (str): The service key for the service.
        profile_suffix_placeholder (str): The profile suffix placeholder for the new service.
    """

    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    def __init__(self, service_key: str, target_type: Any = None,
                 profile_suffix_placeholder: str = ""):
        self.target_type = target_type
        self.profile_suffix_placeholder = profile_suffix_placeholder
        self._logger = get_logger(service_key)
        self.flags = CommandLineParser()
        self.service_key = self.flags.service_key() if self.flags.service_key() is not None else (
            service_key)
        self.service_config = ConfigurationStruct()
        self.web_server = server.WebServer(self._logger, self.service_key, self.service_config)
        self.runtime = None
        self.deferred_funcs = []
        self.ctx_done = threading.Event()
        self.store_forward_ctx_done = threading.Event()
        self.store_forward_wait_group = WaitGroup()
        self.wait_group = WaitGroup()
        self.custom_trigger_factories = None
        self._dic = None
        self.using_configurable_pipeline = False
        self._config_processor = None
        # handle SIGINT and SIGTERM signals below with _exit for gracefully exit
        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def app_done_event(self) -> threading.Event:
        return self.ctx_done

    def add_custom_route(self, route: str, use_auth: bool, handler: Callable,
                         methods: Optional[List[str]] = None):
        """
        add_custom_route allows you to leverage the existing webserver to add routes.
        """
        if route in (API_PING_ROUTE, API_CONFIG_ROUTE, API_VERSION_ROUTE, API_SECRET_ROUTE,
                     API_TRIGGER_ROUTE):
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          f"cannot add custom route for builtin route ({route})")

        if use_auth:
            lc = logging_client_from(self._dic.get)
            secret_provider = secret_provider_ext_from(self._dic.get)
            authentication_hook = auto_config_authentication_func(secret_provider, lc)
            self.web_server.add_route(route, handler, authentication_hook, methods=methods)
            return

        self.web_server.add_route(route, handler, methods=methods)

    def logger(self) -> Logger:
        """
        logger returns the logger instance
        """
        return self._logger

    def initialize(self):
        """
        initialize and bootstraps the application service making it ready to accept functions for
        the pipeline and to run the configured trigger.
        :return:
        """
        self._dic = Container()
        self._dic.update({
            LoggingClientInterfaceName: lambda get: self._logger
        })

        self._logger.info(f"app service {self.service_key} initialize invoked")
        # initialize a timer
        startup_timer = new_startup_timer(self._logger)
        # initialize the configuration
        config_updated = queue.Queue()

        # TODO: translateInterruptToCancel  # pylint: disable=fixme

        secret_provider = new_secret_provider(self.service_config, self.ctx_done, startup_timer,
                                              self._dic, self.service_key)

        cp = Processor(lc=self._logger, flags=self.flags, startup_timer=startup_timer,
                       ctx_done=self.ctx_done, wg=self.wait_group, config_updated=config_updated,
                       dic=self._dic)
        try:
            cp.process(self.service_key, CONFIG_STEM_APP, self.service_config, secret_provider)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.error(f"failed to process configuration: {e}")
            raise e

        self.runtime = FunctionsPipelineRuntime(self.service_key, self.target_type, self._dic)

        registry_client = None
        env_use_registry, was_overridden = environment.use_registry(self._logger)
        if env_use_registry or (self.flags.registry() and not was_overridden):
            try:
                registry_client = register_with_registry(self.ctx_done, startup_timer,
                                                         self.service_config, self._logger,
                                                         self.service_key, None)
            except errors.EdgeX as err:
                fatal_error(err, self._logger)

            def deferred():
                self._logger.info("Un-Registering service from the Registry")
                try:
                    registry_client.unregister()
                except errors.EdgeX as err:
                    self._logger.error("Unable to Un-Register service from the Registry",
                                      "error", str(err))

            self.deferred_funcs.append(deferred)

        self._dic.update({
            ConfigurationName: lambda get: self.service_config,
            RegistryClientInterfaceName: lambda get: registry_client
        })

        try:
            # initialize the messaging client right after the configuration is properly loaded for
            # correct message bus configuration
            self._initialize_message_client(startup_timer)
            # initialize the app context
            # initialize the service clients
            self._initialize_service_clients(startup_timer)
            # initialize service metrics
            self._initialize_service_metrics()
        except errors.EdgeX as err:
            fatal_error(err, self._logger)

        # initialize the web server
        self.web_server.init_web_server()

        self._logger.info(f"Service started in: {startup_timer.since_as_string()}")

    def application_settings(self) -> Dict[str, str]:
        """
        Gets the application settings.
        wait for later implementation
        """
        return self.service_config.ApplicationSettings

    def get_application_setting(self, key: str) -> str:
        """
        Gets an application setting.
        wait for later implementation
        """
        if self.service_config.ApplicationSettings is None:
            raise ValueError(f"{key} setting not found: ApplicationSettings section is missing")
        if key not in self.service_config.ApplicationSettings:
            raise ValueError(f"{key} setting not found")
        return self.service_config.ApplicationSettings[key]

    def get_application_setting_strings(self, key: str) -> [str]:
        """
        Gets an application setting as a list of strings.
        """
        str_value = self.get_application_setting(key)
        return str_value.split(SPILT_COMMA)

    def set_default_functions_pipeline(self, *functions: AppFunction):
        """
        Sets the default functions pipeline.
        wait for later implementation
        """
        if len(functions) == 0:
            raise ValueError("no functions provided to pipeline")
        self.runtime.target_type = self.target_type
        self.runtime.set_default_functions_pipeline(*functions)
        self._logger.debug(f"Default pipeline added with {len(functions)} functions")

    def add_functions_pipeline_for_topics(self, pipeline_id: str, topics: List[str],
                                          *functions: AppFunction):
        """
        Adds a functions pipeline for topics.
        """
        if not functions:
            raise ValueError("No transforms provided to pipeline")

        if not topics:
            raise ValueError("Topics for pipeline cannot be empty")

        for t in topics:
            if t.strip() == "":
                raise ValueError("Blank topic not allowed")

        # Must add the base topic to all the input topics
        full_topics = [
            build_topic(self.service_config.MessageBus.get_base_topic_prefix(), topic)
            for topic in topics
        ]

        try:
            self.runtime.add_function_pipeline(pipeline_id, full_topics, *functions)
        except Exception as err:
            raise err

        self._logger.debug(
            f"Pipeline '{pipeline_id}' added for topics '{full_topics}' "
            f"with {len(functions)} transform(s)")

    def remove_all_function_pipelines(self):
        """
        Removes all function pipelines.
        wait for later implementation
        """
        self.runtime.remove_all_function_pipelines()

    async def run(self):
        """
        Runs the application service.
        wait for later implementation
        """
        # start web server
        web_server = asyncio.create_task(self.web_server.start_web_server())

        # setup and initial the Trigger
        trigger = self.setup_trigger(self.service_config.Trigger)
        if trigger is None:
            self._logger.error("Failed to setup trigger")
            return
        deferred = trigger.initialize(self.ctx_done, self.wait_group)
        self._add_deferred(deferred)

        # init the persistent layer and start store forward mechanism
        err = self._initialize_store_client()
        if err is not None:
            fatal_error(err, self._logger)

        if self.service_config.Writable.StoreAndForward.Enabled:
            self.start_store_forward()
        else:
            self._logger.info("StoreAndForward disabled. Not running retry loop.")

        await web_server

    def setup_trigger(self, trigger_info: TriggerInfo) -> Trigger | None:
        """
        Set up the trigger for the service
        """

        service_binding = DefaultTriggerServiceBinding(self.runtime, self)
        message_processor = DefaultTriggerMessageProcessor(service_binding, self.metrics_manager())

        if trigger_info.Type.upper() == TRIGGER_TYPE_MESSAGEBUS:
            return MessageBusTrigger(service_binding, message_processor, self._dic)
        if trigger_info.Type.upper() == TRIGGER_TYPE_HTTP:
            return HttpTrigger(service_binding, message_processor, self.web_server.router)
        if trigger_info.Type.upper() == TRIGGER_TYPE_MQTT:
            return MqttTrigger(service_binding, message_processor)

        if trigger_info.Type.upper() in self.custom_trigger_factories:
            return self.custom_trigger_factories[trigger_info.Type.upper()]()
        if len(trigger_info.Type) == 0:
            self._logger.error("trigger type not found, missing common config? "
                              "Use -cp or -cc flags for common config")
        else:
            self._logger.error(f"invalid Trigger type of '{trigger_info.Type}' specified")

        return None

    def registry_client(self) -> Client:
        """
        registry_client returns the registry client instance
        """
        return registry_from(self._dic.get)

    def event_client(self) -> EventClientABC:
        """
        event_client returns the event client instance
        """
        return event_client_from(self._dic.get)

    def reading_client(self) -> ReadingClientABC:
        """
        reading_client returns the reading client instance
        """
        return reading_client_from(self._dic.get)

    def command_client(self) -> CommandClientABC:
        """
        command_client returns the command client instance
        """
        return command_client_from(self._dic.get)

    def device_service_client(self) -> DeviceServiceClientABC:
        """
        device_service_client returns the device service client instance
        """
        return device_service_client_from(self._dic.get)

    def device_profile_client(self) -> DeviceProfileClientABC:
        """
        device_profile_client returns the device profile client instance
        """
        return device_profile_client_from(self._dic.get)

    def device_client(self) -> DeviceClientABC:
        """
        device_client returns the device client instance
        """
        return device_client_from(self._dic.get)

    def secret_provider(self) -> SecretProvider:
        """
        secret_provider returns the secret provider instance
        """
        return secret_provider_ext_from(self._dic.get)

    def register_custom_trigger_factory(self, name: str,
                                        factory: Callable[[TriggerConfig], Trigger]):
        """
        register_custom_trigger_factory allows users to register builders for custom trigger types
        """
        nu = name.upper()
        if nu in [TRIGGER_TYPE_MESSAGEBUS, TRIGGER_TYPE_HTTP, TRIGGER_TYPE_MQTT]:
            raise ValueError(f"cannot register custom trigger for builtin type ({name})")

        if self.custom_trigger_factories is None:
            self.custom_trigger_factories = {}

        self.custom_trigger_factories[nu] = lambda: self._create_custom_trigger(factory)

    def publish(self, data: Any, content_type: str):
        """
        publish pushes data to the MessageBus using configured topic
        """
        self.publish_with_topic(self.service_config.Trigger.PublishTopic, data, content_type)

    def publish_with_topic(self, topic: str, data: Any, content_type: str):
        """
        publish_with_topic pushes data to the MessageBus using given topic
        """
        messaging_client = messaging_client_from(self._dic.get)
        if messaging_client is None:
            raise ValueError("MessageBus client not available")

        message = new_message_envelope(data, content_type)
        publish_topic = build_topic(
            build_topic(self.service_config.MessageBus.BaseTopicPrefix, topic))

        messaging_client.publish(message, publish_topic)

    def _exit(self, signum, frame):
        self.ctx_done.set()
        if self.service_config.Writable.StoreAndForward.Enabled:
            self.store_forward_ctx_done.set()
            self.store_forward_wait_group.wait()
        self._logger.info(f"Service {self.service_key} received signal {signum} and frame {frame}, "
                         f"prepare to exit.")
        for deferred in self.deferred_funcs:
            deferred()  # pylint: disable=abstract-class-instantiated
        os._exit(0)

    def _add_deferred(self, deferred: Deferred):
        """
        Add a deferred function to the list of deferred functions
        """
        self.deferred_funcs.append(deferred)

    def _initialize_message_client(self, startup_timer: Timer):
        """
        Initializes the messaging client.
        """
        message_bus_info = self.service_config.MessageBus
        if message_bus_info.Disabled:
            self._logger.info("MessageBus is disabled in configuration, skipping setup.")
            return

        if (len(message_bus_info.Host) == 0 or message_bus_info.Port == 0 or
                len(message_bus_info.Protocol) == 0 or len(message_bus_info.Type) == 0):
            raise ValueError("MessageBus configuration is incomplete, missing common config? Use "
                             "-cp or -cc flags for common config.")

        # pylint: disable=fixme
        # TODO: parse secrets per message_bus_info.auth_mode and add into secret provider when ready

        messaging_client = new_message_client(message_bus_info, self._logger)

        if startup_timer is None:
            startup_timer = new_startup_timer(self._logger)

        while startup_timer.has_not_elapsed():
            if self.ctx_done.is_set():
                return
            try:
                messaging_client.connect()
                self._dic.update({
                    MessagingClientName: lambda get: messaging_client
                })
                break
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.warn(f"Unable to connect MessageBus: {e}")
                startup_timer.sleep_for_interval()
                continue

        def messaging_client_disconnect():
            while self.ctx_done.is_set():
                if messaging_client is not None:
                    messaging_client.disconnect()
                self.wait_group.done()
                break

        self.wait_group.add(1)
        threading.Thread(target=messaging_client_disconnect).start()

    def _create_custom_trigger(self, factory: Callable[[TriggerConfig], Trigger]) -> Trigger:
        service_binding = DefaultTriggerServiceBinding(self.runtime, self)
        message_processor = DefaultTriggerMessageProcessor(service_binding, self.metrics_manager())

        cfg = TriggerConfig(
            logger=self._logger,
            context_builder=service_binding.build_context,
            message_received=message_processor.message_received,
            config_loader=service_binding.load_custom_config,
        )

        return factory(cfg)

    def _initialize_service_clients(self, startup_timer: Timer):
        """
        Initializes the clients.
        """
        if self.service_config.Clients is None:
            return

        jwt_secret_provider = JWTSecretProvider(secret_provider_ext_from(self._dic.get))

        service_base_url = ""
        enable_name_field_escape = self.service_config.Service.EnableNameFieldEscape
        for service_key, service_info in self.service_config.Clients.items():
            if not service_info.UseMessageBus:
                try:
                    service_base_url = self._get_client_url(service_key, service_info.url(),
                                                            startup_timer)
                except EdgeX as err:
                    self._logger.error(f"failed to get service client URL: {err}")
                    raise errors.new_common_edgex_wrapper(err)

            if service_key == CORE_DATA_SERVICE_KEY:
                self._create_event_client(service_base_url, jwt_secret_provider,
                                          enable_name_field_escape)
                self._create_reading_client(service_base_url, jwt_secret_provider,
                                            enable_name_field_escape)

            if service_key == CORE_COMMAND_SERVICE_KEY:
                self._create_command_client(service_base_url, jwt_secret_provider,
                                            enable_name_field_escape)

            if service_key == CORE_METADATA_SERVICE_KEY:
                self._create_device_service_client(service_base_url, jwt_secret_provider,
                                                   enable_name_field_escape)
                self._create_device_profile_client(service_base_url, jwt_secret_provider,
                                                   enable_name_field_escape)
                self._create_device_client(service_base_url, jwt_secret_provider,
                                           enable_name_field_escape)

    def _initialize_service_metrics(self):
        """
        Initializes the service metrics.
        """
        lc = logging_client_from(self._dic.get)
        service_config = configuration_from(self._dic.get)

        telemetry_config = service_config.Writable.Telemetry

        if telemetry_config.Interval == "":
            telemetry_config.Interval = "PT0S"
        else:
            telemetry_config.Interval = "PT" + telemetry_config.Interval.upper()

        try:
            interval = isodate.parse_duration(telemetry_config.Interval)
        except isodate.ISO8601Error as err:
            msg = "Telemetry interval is invalid time duration"
            lc.error("%s: %s", msg, err)
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          "msg", err)
        if interval.total_seconds() == 0:
            lc.info("0 specified for metrics reporting interval. Setting to a very large duration "
                    "to effectively disable reporting.")
            interval = isodate.parse_duration(f"PT{2^31-1}S")

        base_topic = service_config.MessageBus.get_base_topic_prefix()
        reporter = MessageBusReporter(lc, base_topic, self.service_key, self._dic, telemetry_config)
        manager = Manager(lc, interval, reporter)

        manager.run(self.ctx_done, self.wait_group)

        self._dic.update({
            MetricsManagerInterfaceName: lambda get: manager
        })

    def _get_client_url(self, service_key: str, default_url: str, startup_timer: Timer) -> str:
        """
        Gets the service client URL.
        """
        registry_client = registry_from(self._dic.get)
        mode = dev_remote_mode_from(self._dic.get)
        if registry_client is None or mode is None or mode.in_dev_mode or not mode.in_remote_mode:
            self._logger.info(f"Using REST for {service_key} clients at {default_url}")
            return default_url

        endpoint = None
        while startup_timer.has_not_elapsed():
            try:
                endpoint = registry_client.get_service_endpoint(service_key)
                break
            except errors.EdgeX as err:
                self._logger.warn(f"failed to get service endpoint from registry: {err}. "
                                 f"retrying...")
                startup_timer.sleep_for_interval()

        if endpoint is None:
            raise errors.new_common_edgex(errors.ErrKind.SERVER_ERROR,
                                          f"unable to get service endpoint from registry "
                                          f"for {service_key}. Giving up")

        result = f"http://{endpoint.host}:{endpoint.port}"
        self._logger.info(f"Using service endpoint {result} for {service_key}")
        return result

    def _create_event_client(self, base_url: str, auth_injector: AuthenticationInjector,
                             enable_name_field_escape: bool):
        event_client = EventClient(
            base_url=base_url,
            auth_injector=auth_injector,
            enable_name_field_escape=enable_name_field_escape)
        self._dic.update({
            EventClientName: lambda get: event_client
        })

    def _create_reading_client(self, base_url: str, auth_injector: AuthenticationInjector,
                               enable_name_field_escape: bool):
        reading_client = ReadingClient(
            base_url=base_url,
            auth_injector=auth_injector,
            enable_name_field_escape=enable_name_field_escape)
        self._dic.update({
            ReadingClientName: lambda get: reading_client
        })

    def _create_command_client(self, base_url: str, auth_injector: AuthenticationInjector,
                               enable_name_field_escape: bool):
        command_client = CommandClient(
            base_url=base_url,
            auth_injector=auth_injector,
            enable_name_field_escape=enable_name_field_escape)
        self._dic.update({
            CommandClientName: lambda get: command_client
        })

    def _create_device_service_client(self, base_url: str, auth_injector: AuthenticationInjector,
                                      enable_name_field_escape: bool):
        ds_client = DeviceServiceClient(
            base_url=base_url,
            auth_injector=auth_injector,
            enable_name_field_escape=enable_name_field_escape)
        self._dic.update({
            DeviceServiceClientName: lambda get: ds_client
        })

    def _create_device_profile_client(self, base_url: str, auth_injector: AuthenticationInjector,
                                      enable_name_field_escape: bool):
        dp_client = DeviceProfileClient(
            base_url=base_url,
            auth_injector=auth_injector,
            enable_name_field_escape=enable_name_field_escape)
        self._dic.update({
            DeviceProfileClientName: lambda get: dp_client
        })

    def _create_device_client(self, base_url: str, auth_injector: AuthenticationInjector,
                                      enable_name_field_escape: bool):
        device_client = DeviceClient(
            base_url=base_url,
            auth_injector=auth_injector,
            enable_name_field_escape=enable_name_field_escape)
        self._dic.update({
            DeviceClientName: lambda get: device_client
        })

    def _find_matching_function(self, configurable: Any, function_name: str) -> \
            [Any, inspect.Signature]:
        # Find if there is a method with name identical to the functionName
        function_value = getattr(configurable, function_name, None)

        if function_value is None:
            longest_matched_name_length = 0
            # Iterate over all method names to find a match
            for method_name, method in inspect.getmembers(
                    configurable, predicate=inspect.ismethod):
                # If the target configuration function name starts with actual method name then
                # it is a match. If there are multiple matches then pick the one with the longest
                # name
                if (function_name.startswith(method_name) and
                        len(method_name) > longest_matched_name_length):
                    longest_matched_name_length = len(method_name)
                    function_value = method

        if function_value is None:
            raise ValueError(f"Function {function_name} is not a built-in SDK function")
        if not callable(function_value):
            raise ValueError(f"invalid configuration for {function_name}")

        function_type = inspect.signature(function_value)
        return function_value, function_type

    def _secret_provider(self) -> SecretProvider:
        return secret_provider_ext_from(self._dic.get)

    def load_configurable_function_pipelines(self) -> dict[str, FunctionPipeline]:
        """
        Returns the configured function pipelines (default and per topic) from configuration.
        """
        pipelines = {}
        self.using_configurable_pipeline = True

        self.target_type = None

        target_type = self.service_config.Writable.Pipeline.TargetType.strip().lower()

        match target_type:
            case constants.TARGET_TYPE_RAW:
                self.target_type = bytes()
            case constants.TARGET_TYPE_METRIC:
                self.target_type = Metric()
            case constants.TARGET_TYPE_EMPTY | constants.TARGET_TYPE_EVENT:
                self.target_type = Event()
            case _:
                raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                              f"pipeline TargetType of '{target_type}' is not "
                                              f"supported")

        configurable = Configurable(self._logger, self._secret_provider())
        pipeline_config = self.service_config.Writable.Pipeline

        default_execution_order = pipeline_config.ExecutionOrder.strip()

        if len(default_execution_order) == 0 and len(pipeline_config.PerTopicPipelines) == 0:
            raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                          "Default ExecutionOrder has 0 functions specified and "
                                          "PerTopicPipelines is empty")

        if len(default_execution_order) > 0:
            self._logger.debug(f"Default Function Pipeline Execution Order: "
                              f"[{pipeline_config.ExecutionOrder}]")
            function_names = delete_empty_and_trim(default_execution_order.split(','))

            try:
                transforms = self._load_configurable_pipeline_transforms(
                    DEFAULT_PIPELINE_ID,
                    function_names,
                    pipeline_config.Functions,
                    configurable)
            except errors.EdgeX as err:
                raise errors.new_common_edgex_wrapper(err)

            pipeline = FunctionPipeline(
                DEFAULT_PIPELINE_ID,
                [TOPIC_WILDCARD],
                *transforms,
            )

            pipelines[pipeline.id] = pipeline

        if pipeline_config.PerTopicPipelines:
            for _, per_topic_pipeline in pipeline_config.PerTopicPipelines.items():
                self._logger.debug(
                    f"'{per_topic_pipeline.Id}' Function Pipeline Execution Order: "
                    f"[{per_topic_pipeline.ExecutionOrder}]")

                function_names = delete_empty_and_trim(
                    per_topic_pipeline.ExecutionOrder.split(','))
                function_names = list(convert_dict_keys_to_snake_case(
                    {k: None for k in function_names}, FUNCTION_KEYS_REPLACEMENTS).keys())

                transforms = self._load_configurable_pipeline_transforms(
                    per_topic_pipeline.Id, function_names, pipeline_config.Functions, configurable)

                pipeline = FunctionPipeline(
                    per_topic_pipeline.Id,
                    delete_empty_and_trim(per_topic_pipeline.Topics.split(',')),
                    *transforms
                )

                pipelines[pipeline.id] = pipeline

        return pipelines

    def _load_configurable_pipeline_transforms(self, pipeline_id: str,
                                               execution_order: List[str],
                                               functions: Dict[str, PipelineFunction],
                                               configurable: Any) -> List[AppFunction]:
        transforms = []

        # Set pipeline function parameter names to lowercase to avoid casing issues from what is in
        # source configuration
        set_pipeline_function_parameter_names_lowercase(
            self.service_config.Writable.Pipeline.Functions)

        for function_name in execution_order:
            function_name = camel_to_snake(function_name.strip())
            configuration = functions.get(function_name)
            if configuration is None:
                raise errors.new_common_edgex(errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                                              f"function '{function_name}' configuration "
                                              f"not found in Pipeline.Functions section "
                                              f"for pipeline '{pipeline_id}'")

            try:
                function_value, function_type = self._find_matching_function(configurable,
                                                                             function_name)
            except ValueError as err:
                raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                              f"{err} for pipeline '{pipeline_id}'")

            input_parameters = []

            for parameter in function_type.Parameters.values():
                if parameter.annotation == dict:
                    input_parameters.append(configuration.Parameters)
                else:
                    raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                                  f"Function {function_name} for pipeline "
                                                  f"'{pipeline_id}' has an unsupported parameter "
                                                  f"type: {parameter.annotation}")

            function = function_value(*input_parameters)
            try:
                validate_app_function(function)
            except TypeError as err:
                raise errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"Function {function_name} for pipeline '{pipeline_id}' "
                    f"does not match the expected signature: {err}")

            if function is None:
                raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                              f"{function_name} from configuration failed for "
                                              f"pipeline '{pipeline_id}'")

            transforms.append(function)
            self._logger.debug(
                f"{function_name} function added to '{pipeline_id}' configurable pipeline with "
                f"parameters: [{', '.join(configuration.Parameters)}]")

        return transforms

    def load_custom_config(self, custom_config: Any, section_name: str):
        """
        load_custom_config attempts to load service's custom configuration. It uses the same command
        line flags to process the custom config in the same manner as the standard configuration.
        """
        if self._config_processor is None:
            self._config_processor = new_processor_for_custom_config(
                self.flags, self.ctx_done, self.wait_group, self._dic
            )

        try:
            self._config_processor.load_custom_config_section(custom_config, section_name)
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

        self.web_server.set_custom_config_info(custom_config)

    def listen_for_custom_config_changes(self, config: Any, section_name: str,
                                         changed_callback: Callable[[Any], None]):
        """
        listen_for_custom_config_changes uses the Config Processor from go-mod-bootstrap to watch
        for changes in the service's custom configuration. It uses the same command line flags to
        process the custom config in the same manner as the standard configuration.
        """
        if self._config_processor is None:
            raise errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"custom configuration must be loaded before '{section_name}' section can be "
                f"watched for changes")

        threading.Thread(target=self._config_processor.listen_for_custom_config_changes,
                         args=(config, section_name,
                               changed_callback)).start()

    def start_store_forward(self):
        """ start store and forward """
        self.store_forward_ctx_done.clear()
        self.runtime.start_store_and_forward(
            self.wait_group, self.ctx_done, self.store_forward_wait_group,
            self.store_forward_ctx_done, self.service_key)

    def stop_store_forward(self):
        """ stop store and forward """
        self._logger.info("Canceling Store and Forward retry loop")
        if self.store_forward_ctx_done is not None:
            self.store_forward_ctx_done.set()
        self.store_forward_wait_group.wait()

    def _initialize_store_client(self) -> Optional[errors.EdgeX]:
        """ initialize the store client """
        # Only need the database client if Store and Forward is enabled
        if not self.service_config.Writable.StoreAndForward.Enabled:
            self._dic.update({
                StoreClientInterfaceName: lambda get: None
            })
            return None

        try:
            secrets = self.secret_provider().get_secrets(self.service_config.Database.Type)
        except errors.EdgeX as e:
            return errors.new_common_edgex_wrapper(e)

        credentials = Credentials(
            Username=secrets[SECRET_USERNAME_KEY],
            Password=secrets[SECRET_PASSWORD_KEY],
        )

        startup = environment.get_startup_info(self._logger)
        timeout = time.time() + startup.duration
        store_client: Optional[StoreClient] = None
        err: Optional[errors.EdgeX] = None
        while time.time() < timeout:
            try:
                store_client = _create_store_client(
                    self.service_config.Database, credentials, self._logger)
            except errors.EdgeX as err:
                self._logger.warn(
                    "unable to initialize Database '%s' for Store and Forward: %s",
                    self.service_config.Database.Type, err)
                time.sleep(startup.interval)
                continue
            if err is None:
                break

        if err is not None:
            return errors.new_common_edgex(
                errors.kind(err), "initialize Database for Store and Forward failed", err)

        self._dic.update({
            StoreClientInterfaceName: lambda get: store_client
        })

        return None

    def metrics_manager(self) -> MetricsManager:
        """
        Return the Metrics Manager used to register counter, gauge, gaugeFloat64 or timer metrics.
        """
        return metrics_manager_from(self._dic.get)

    def dic(self) -> Container:
        """
        Returns the dependency injection container.
        """
        return self._dic

    def get_service_config(self) -> ConfigurationStruct:
        """
        Returns the service configuration.
        """
        return self.service_config


def _create_store_client(database: DatabaseInfo,
                        _: Credentials, lc: Logger) -> Optional[StoreClient]:
    """ create store client """
    match database.Type.lower():
        case constants.DB_SQLITE:
            return new_sqlite_client(database.Host, lc)
        case _:
            raise errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"unsupported database type '{database.Type}'")
