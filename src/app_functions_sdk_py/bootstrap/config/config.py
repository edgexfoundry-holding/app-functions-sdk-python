# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=too-many-lines
"""
This module provides functionality for processing configuration files in the application.

It includes capabilities to determine the configuration file location, load and merge
configurations from different sources (common and private), and apply overrides based on
environment settings.

Classes:
    Processor: Handles configuration processing.

Functions:
    get_config_file_location(lc: Logger, flags: CommandLineParser) -> str: Determines the
    configuration file location.
    get_local_ip() -> str: Retrieves the local IP address of the host machine.
"""
import copy
import os
import queue
import threading
import urllib.parse
import socket
from dataclasses import dataclass
from typing import Optional, Any, Callable

import isodate
from deepdiff import DeepDiff

from .provider import ProviderInfo
from .. import timer
from ..container.configuration import ConfigClientInterfaceName, config_client_from
from ..container.devremotemode import DevRemoteMode, DevRemoteModeName
from ..container.logging import logging_client_from
from ..container.messaging import messaging_client_from
from ..di.container import Container
from ..interface.secret import SecretProviderExt
from ..utils import update_object_from_data
from ...bootstrap import environment
from ...bootstrap.commandline import CommandLineParser
from ...bootstrap.timer import Timer
from ...contracts.clients.logger import Logger
from ...configuration.config import GetAccessTokenCallback
from ...contracts import errors
from ...contracts.common.constants import CORE_COMMON_CONFIG_SERVICE_KEY
from ...internal.common.config import ConfigurationStruct, empty_writable_ptr
from ...configuration import new_configuration_client, config, ServiceConfig
from ...configuration.interfaces.configuration import ConfigurationClient
from ...bootstrap import utils
from ...sync.waitgroup import WaitGroup
from ...utils.functionexitcallback import FunctionExitCallback
from ...utils.strconv import parse_bool

WRITABLE_KEY = "Writable"
INSECURE_SECRETS_KEY = "InsecureSecrets"
SECRET_NAME_KEY = "SecretName"
SECRET_DATA_KEY = "SecretData"

CONFIG_PROVIDER_TYPE_KEEPER = "keeper"
ALL_SERVICES_KEY = "all-services"
APP_SERVICES_KEY = "app-services"
COMMON_CONFIG_DONE = "IsCommonConfigReady"

CreateProviderCallback = Callable[
    [Logger, str, str, GetAccessTokenCallback, ServiceConfig], ConfigurationClient]


def get_config_file_location(lc: Logger, flags: CommandLineParser) -> str:
    """
    Determines the configuration file location based on command line arguments
    or environment settings.

    Parameters:
        lc (Logger): Logger instance for logging messages.
        flags (CommandLineParser): Parsed command line arguments.

    Returns:
        str: The full path to the configuration file.
    """
    config_file_name = environment.get_config_file_name(lc, flags.config_file())

    try:
        parsed_url = urllib.parse.urlparse(config_file_name)
    except Exception as err:
        lc.error(f"Could not parse file path: {err}")
        raise err

    if parsed_url.scheme in ["http", "https"]:
        return config_file_name

    config_dir = environment.get_config_directory(lc, flags.config_directory())
    profile_dir = environment.get_profile_directory(lc, flags.profile())
    return os.path.join(config_dir, profile_dir, config_file_name)


def get_local_ip() -> str:
    """
    Get the local IP address of the host machine.

    Returns:
        str: The local IP address.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Because of how UDP works, the connection is not established - no handshake is performed,
        # no data is sent. The purpose of this is to get the local IP address that a UDP connection
        # would use if it were sending data to the external destination address.
        s.connect(('8.8.8.8', 80))  # NOSONAR
        ip = s.getsockname()[0]
    except socket.error:
        # Since this is for Dev Mode, just default to localhost when can't get the actual IP
        ip = 'localhost'
    finally:
        s.close()
    return ip


def load_config_from_provider(service_config: ConfigurationStruct,
                              private_config_client: ConfigurationClient):
    """
    Load the configuration from the provider.

    Parameters:
        service_config (ConfigurationStruct): The service configuration structure to be updated.
        private_config_client (ConfigurationClient): The configuration client to use for fetching
        the private configuration.

    Returns:
        None
    """
    private_config_client.get_configuration(service_config)


def apply_remote_hosts(service_config: ConfigurationStruct, remote_hosts: list[str]):
    """
    Applies remote host configuration values to the service configuration.

    Parameters:
        service_config (ConfigurationStruct): The service configuration structure to be updated.
        remote_hosts (list[str]): A list containing the host addresses for the service,
        message bus, and registry configurations.

    Returns:
        None
    """
    if len(remote_hosts) != 3:
        raise ValueError(
            "-rsh/--remoteServiceHosts must contain 3 and only 3 comma separated host names")

    service_config.Service.Host = remote_hosts[0]
    service_config.Service.ServerBindAddr = remote_hosts[2]

    if service_config.MessageBus:
        service_config.MessageBus.Host = remote_hosts[1]

    if service_config.Registry:
        service_config.Registry.Host = remote_hosts[1]

    if service_config.Database:
        service_config.Database.Host = remote_hosts[1]

    if service_config.Clients:
        for client in service_config.Clients.values():
            client.Host = remote_hosts[1]


@dataclass
class Processor:  # pylint: disable=too-many-instance-attributes
    """
    Processor class for handling configuration processing and application setup.

    Attributes:
        lc (Logger): Logger instance for logging messages.
        flags (CommandLineParser): Parsed command line arguments.
        startup_timer (Timer): Timer instance for tracking startup time.
    """
    lc: Logger
    flags: CommandLineParser
    startup_timer: Optional[Timer]
    ctx_done: threading.Event
    wg: WaitGroup
    config_updated: Optional[queue.Queue]
    dic: Container
    overwrite_config: bool = False
    provider_has_config: bool = False
    common_config_client: Optional[ConfigurationClient] = None
    app_config_client: Optional[ConfigurationClient] = None
    config_client: Optional[ConfigurationClient] = None

    def __post_init__(self):
        """
        Post-initialization to set additional attributes after the initial setup.
        """
        self.overwrite_config = self.flags.overwrite()

    # pylint: disable=too-many-arguments, too-many-locals, too-many-statements, too-many-positional-arguments
    def process(self, service_key: str, config_stem: str,
                service_config: ConfigurationStruct,
                secret_provider: SecretProviderExt = None,
                jwt_secret_provider: Any = None):
        """
        Processes the configuration for a given service by loading and merging common and
        private configurations.

        Parameters:
            service_key (str): The key identifying the service.
            config_stem (str): The stem used for configuration files.
            service_config (ConfigurationStruct): The initial service configuration structure to
            be updated.
            secret_provider: The secret provider to use for retrieving secrets.
            jwt_secret_provider: The JWT secret provider to use for retrieving JWT secrets.

        Returns:
            None
        """
        try:
            self.overwrite_config = self.flags.overwrite()
            config_provider_url = self.flags.config_provider()
            remote_hosts = environment.get_remote_service_hosts(self.lc,
                                                                self.flags.remote_service_hosts())

            # Create new ProviderInfo and initialize it from command-line flag or Variables
            config_provider_info = ProviderInfo(self.lc, config_provider_url)

            config_provider_info.set_auth_injector(jwt_secret_provider)

            mode = DevRemoteMode(in_dev_mode=self.flags.dev_mode(),
                                 in_remote_mode=remote_hosts is not None)

            self.dic.update({
                DevRemoteModeName: lambda get: mode
            })

            use_provider = config_provider_info.use_provider()

            private_config_client = None

            if use_provider:
                if remote_hosts:
                    if len(remote_hosts) != 3:
                        raise ValueError("Invalid remote service hosts configuration")

                    self.lc.info(f"Setting config Provider host to {remote_hosts[1]}")
                    config_provider_info.set_host(remote_hosts[1])

                get_access_token = self.get_access_token_callback(service_key, secret_provider,
                                                                  config_provider_info)

                self.load_common_config(config_stem, get_access_token, config_provider_info,
                                        service_config, create_provider_client)

                self.lc.info("Common configuration loaded from the Configuration Provider. "
                             "No overrides applied")

                private_config_client = create_provider_client(
                    self.lc, service_key, config_stem,
                    get_access_token,
                    config_provider_info.service_config())

                self.dic.update({
                    ConfigClientInterfaceName: lambda get: private_config_client
                })

                self.provider_has_config = private_config_client.has_configuration()

                if self.provider_has_config and not self.overwrite_config:
                    private_service_config = ConfigurationStruct()
                    private_service_config.__dict__.update(service_config.__dict__)

                    load_config_from_provider(private_service_config, private_config_client)

                    config_keys = private_config_client.get_configuration_keys("")

                    # Must remove any settings in the config that are not actually present
                    # in the Config Provider
                    private_config_keys = utils.string_list_to_dict(config_keys)
                    private_config_map = utils.remove_unused_settings(
                        private_service_config,
                        utils.build_base_key(config_stem, service_key),
                        private_config_keys)

                    # Now merge only the actual present value with the existing configuration
                    # from common.
                    self.update_service_config(service_config, private_config_map)

                    self.lc.info("Private configuration loaded from the Configuration Provider. "
                                 "No overrides applied")
            else:
                # Now load common configuration from local file if not using config provider
                # and -cc/--commonConfig flag is used.
                # NOTE: Some security services don't use any common configuration and don't use
                # the configuration provider.
                common_config_location = (
                    environment.get_common_config_file_name(self.lc, self.flags.common_config()))
                if common_config_location != "":
                    common_config = self.load_common_config_from_file(common_config_location)
                    self.update_service_config(service_config, common_config)
                    override_count = environment.override_configuration(self.lc,
                                                                        service_config.__dict__)
                    self.lc.info(f"Common configuration loaded from file with {override_count} "
                                 f"overrides applied")

            # Now load the private config from a local file if any of these conditions are true
            if not use_provider or not self.provider_has_config or self.overwrite_config:
                file_path = get_config_file_location(self.lc, self.flags)
                config_map = environment.load_yaml_from_file(self.lc, file_path)

                # apply overrides - Now only done when loaded from file and values will
                # get pushed into Configuration Provider (if used)
                override_count = environment.override_configuration(self.lc, config_map)

                self.lc.info(f"Private configuration loaded from file with {override_count} "
                             f"overrides applied")

                cloned_config_map = copy.deepcopy(config_map)
                self.update_service_config(service_config, cloned_config_map)

                if use_provider:
                    private_config_client.put_configuration_map(config_map, self.overwrite_config)

                self.lc.info("Private configuration has been pushed to into "
                             "Configuration Provider with overrides applied")

                private_config = self.load_private_config()
                self.update_service_config(service_config, private_config)
                override_count = environment.override_configuration(self.lc,
                                                                    service_config.__dict__)
                self.lc.info(f"Private configuration loaded from file with {override_count} "
                             f"overrides applied")

            # listen for changes on Writable
            if use_provider:
                threading.Thread(target=self.listen_for_private_changes,
                                 args=(service_config, private_config_client,
                                       utils.build_base_key(config_stem, service_key),
                                       config_provider_info.service_config().type)).start()
                self.lc.info("listening for private config changes")
                threading.Thread(target=self.listen_for_common_changes,
                                 args=(service_config, self.common_config_client,
                                       private_config_client,
                                       utils.build_base_key(config_stem,
                                                            CORE_COMMON_CONFIG_SERVICE_KEY,
                                                            ALL_SERVICES_KEY),
                                       config_provider_info.service_config().type)).start()
                self.lc.info("listening for all services common config changes")

                if self.app_config_client is not None:
                    threading.Thread(target=self.listen_for_common_changes,
                                     args=(service_config, self.app_config_client,
                                           private_config_client,
                                           utils.build_base_key(config_stem,
                                                                CORE_COMMON_CONFIG_SERVICE_KEY,
                                                                APP_SERVICES_KEY),
                                           config_provider_info.service_config().type)).start()
                    self.lc.info("listening for application service common config changes")

            self.lc.set_log_level(service_config.Writable.LogLevel)
            self.adjust_for_dev_mode(service_config)

            if remote_hosts is not None:
                apply_remote_hosts(service_config, remote_hosts)
        except Exception as e:
            self.lc.error(f"Configuration processing error: {e}")
            raise

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def load_common_config(self, config_stem: str,
                           get_access_token: Optional[config.GetAccessTokenCallback],
                           config_provider_info: ProviderInfo, service_config: ConfigurationStruct,
                           create_provider: CreateProviderCallback):
        """
        Loads common configs from the config provider
        """
        try:
            self.common_config_client = (
                create_provider_client(self.lc,
                                       utils.build_base_key(CORE_COMMON_CONFIG_SERVICE_KEY,
                                                            ALL_SERVICES_KEY),
                                       config_stem, get_access_token,
                                       config_provider_info.service_config()
                                       )
            )
        except ValueError as e:
            raise RuntimeError(f"failed to create provider for {ALL_SERVICES_KEY}: {e}") from e

        # build the path for the common configuration ready value
        common_config_ready_path = (f"{config_stem}/{CORE_COMMON_CONFIG_SERVICE_KEY}/"
                                    f"{COMMON_CONFIG_DONE}")
        self.wait_for_common_config(self.common_config_client, common_config_ready_path)

        self.load_config_from_provider(service_config, self.common_config_client)

        service_type_section_key = utils.build_base_key(CORE_COMMON_CONFIG_SERVICE_KEY,
                                                        APP_SERVICES_KEY)
        self.lc.info("loading the common configuration for app service")
        service_type_config = copy.deepcopy(service_config)
        try:
            self.app_config_client = create_provider(self.lc, service_type_section_key,
                                                     config_stem, get_access_token,
                                                     config_provider_info.service_config())
        except ValueError as e:
            raise RuntimeError(f"failed to create provider for {APP_SERVICES_KEY}: {e}") from e
        self.load_config_from_provider(service_type_config, self.app_config_client)
        service_type_config_keys = self.app_config_client.get_configuration_keys("")

        # merge together the common config and the service type config
        if service_type_config is not None:
            # Must remove any settings in the config that are not actually present in
            # the Config Provider
            service_type_config_map = utils.remove_unused_settings(
                service_type_config,
                utils.build_base_key(config_stem, service_type_section_key),
                utils.string_list_to_dict(service_type_config_keys))

            # merge common config and the service type common config's actually used settings
            self.update_service_config(service_config, service_type_config_map)

    def load_private_config(self):
        """
        Loads the private configuration from a file specified by command line arguments or
        environment settings.
        TODO: Loads private configuration from Core Keeper.

        This method determines the location of the private configuration file using the command
        line arguments or environment settings provided. It then attempts to load this
        configuration file as a YAML and return its contents as a dictionary. The private
        configuration file is expected to contain settings specific to the instance of the
        application being run.

        Returns:
            dict: The loaded private configuration as a dictionary. If the file cannot be found
            or loaded, an empty dictionary is returned.
        """
        file_path = get_config_file_location(self.lc, self.flags)
        return environment.load_yaml_from_file(self.lc, file_path)

    def apply_overrides(self, config_dict):
        """
        Applies configuration overrides to the given configuration dictionary.

        This method uses the environment's override configuration function to apply any overrides
        specified through command line arguments or environment variables. It logs the number of
        overrides applied to the configuration.

        Parameters:
            config_dict (dict): The configuration dictionary to which overrides will be applied.

        Returns:
            None
        """
        override_count = environment.override_configuration(self.lc, config_dict)
        self.lc.info(f"Configuration loaded with {override_count} overrides applied")

    def update_service_config(self, service_config, config_dict):
        """
        Updates the service configuration with values from the provided configuration dictionary.

        This method first converts the keys in the provided configuration dictionary from camel
        case to snake case, applying any predefined key replacements. It then updates the service
        configuration object with the values from the modified configuration dictionary. Finally,
        it sets the log level in the service configuration based on the updated configuration
        values.

        Parameters:
            service_config (ConfigurationStruct): The initial service configuration structure
             to be updated.
            config_dict (dict): The configuration dictionary with potential camel case keys
             and new configuration values.

        Returns:
            None
        """
        update_object_from_data(service_config, config_dict)

    def adjust_for_dev_mode(self, service_config):
        """
        Adjusts the service configuration for development mode.

        In development mode, this method overrides the host configuration values with `localhost`
        to facilitate local testing and development. Specifically, it sets the host of the service,
        message bus, registry, and database configurations to `localhost`. Additionally, if the
        service is configured, it sets the service's host to the local IP address and the server
        bind address to `0.0.0.0` to allow connections from other devices in the network. This
        adjustment is applied to all clients as well.

        Parameters:
            service_config (ConfigurationStruct): The service configuration structure to be
            adjusted for development mode.

        Returns:
            None
        """
        if self.flags.dev_mode():
            host = "localhost"
            self.lc.info(f"Running in developer mode, overriding Host configuration values "
                         f"with `{host}`")
            if service_config.Service:
                service_config.Service.Host = get_local_ip()
                service_config.Service.ServerBindAddr = "0.0.0.0"
            for conf in [service_config.MessageBus, service_config.Registry,
                         service_config.Database]:
                if conf:
                    conf.Host = host
            if service_config.Clients:
                for client in service_config.Clients.values():
                    client.Host = host

    def load_common_config_from_file(self, config_file) -> dict:
        """
        Loads the common configuration from a specified file.

        Parameters:
            config_file (str): The path to the common configuration file.

        Returns:
            dict: The common configuration as a dictionary.
        """
        common_config = environment.load_yaml_from_file(self.lc, config_file)

        try:
            all_services_config = common_config[ALL_SERVICES_KEY]
        except KeyError:
            self.lc.error(f"could not find {ALL_SERVICES_KEY} section in common config "
                          f"{config_file}")
            raise

        try:
            self.lc.info("loading the common configuration for app service")
            service_type_config = common_config[APP_SERVICES_KEY]
        except KeyError:
            self.lc.error(f"could not find {APP_SERVICES_KEY} section in common config "
                          f"{config_file}")
            raise

        merge_dict(all_services_config, service_type_config)

        return all_services_config

    def get_access_token_callback(self, service_key: str, secret_provider: SecretProviderExt,
                                  config_provider_info: ProviderInfo) -> (
            Optional)[GetAccessTokenCallback]:
        """
        Returns a callback function that retrieves an access token.

        Returns:
            Callable[[], str]: A callback function that retrieves an access token.
        """
        # secret_provider will be None if not configured to be used.
        # In that case, no access token required.
        if secret_provider is not None:
            # Define the callback function to retrieve the Access Token
            def get_access_token() -> str:
                access_token = secret_provider.get_access_token(
                    config_provider_info.service_config().type, service_key)
                self.lc.debug("Using Configuration Provider access token of length %d",
                              len(access_token))
                return access_token

            return get_access_token

        self.lc.debug("Not configured to use Config Provider access token")
        return None

    def apply_writable_updates(self, service_config: ConfigurationStruct, raw: dict):
        """
        Applies the writable updates to the service configuration.

        This method updates the writable fields in the service configuration with the values from
        the provided configuration dictionary. It then checks for changes in the log level,
        insecure secrets, and telemetry interval, and applies the necessary updates to the service
        configuration. If the configuration updates exist, it signals the configuration updated
        queue.

        Parameters:
            service_config (ConfigurationStruct): The service configuration structure to be updated.
            raw (dict): The configuration dictionary with new writable values.

        Returns:
            None
        """
        lc = self.lc

        # Capture previous state for comparison
        previous_log_level = service_config.Writable.LogLevel
        previous_telemetry_interval = service_config.Writable.Telemetry.Interval

        previous_insecure_secrets = copy.deepcopy(service_config.Writable.InsecureSecrets)

        # Apply writable change to service configuration
        update_object_from_data(service_config.Writable, raw)

        current_insecure_secrets = service_config.Writable.InsecureSecrets
        current_log_level = service_config.Writable.LogLevel
        current_telemetry_interval = service_config.Writable.Telemetry.Interval

        lc.info("Writable configuration has been updated from the Configuration Provider")

        # Note: Updates occur one setting at a time so only have to look for single changes
        if current_log_level != previous_log_level:
            try:
                lc.set_log_level(service_config.Writable.LogLevel)
                lc.info(f"Logging level changed to {current_log_level}")
            except ValueError as e:
                lc.error(f"Failed to set new logging level: {e}")
            return

        # InsecureSecrets (map) will be nil if not in the original YAML used to seed the
        # Config Provider, so ignore it if this is the case.
        if current_insecure_secrets and DeepDiff(previous_insecure_secrets,
                                                 current_insecure_secrets):
            # lc.info("Insecure Secrets have been updated")
            # TODO: Implement secret provider in milestone E  # pylint: disable=fixme
            lc.info("TODO: Implement secret provider in milestone E")
            # secret_provider = get_secret_provider()
            # if secret_provider:
            #     updated_secrets = get_secret_names_changed(previous_insecure_secrets,
            #                                                current_insecure_secrets)
            #     for v in updated_secrets:
            #         secret_provider.secret_updated_at_secret_name(v)
            return

        if current_telemetry_interval != previous_telemetry_interval:
            lc.info("Telemetry interval has been updated. Processing new value...")
            try:
                interval = isodate.parse_duration(
                    "PT" + current_telemetry_interval.upper()).total_seconds() * 1e9
                if interval == 0:
                    lc.info(
                        "0 specified for metrics reporting interval. "
                        "Setting to max duration to effectively disable reporting.")
                    interval = (1 << 63) - 1
            except isodate.ISO8601Error as e:
                lc.error(f"Failed to update telemetry interval: {e}")
                return

            # TODO: Implement metrics manager in milestone D  # pylint: disable=fixme
            # if metrics_manager:
            #     metrics_manager.reset_interval(interval)
            # else:
            #     lc.error("Metrics manager not available while updating telemetry interval")
            return

        # Signal that configuration updates exist
        if self.config_updated is not None:
            self.config_updated.put(True)

    def wait_for_common_config(self, config_client: ConfigurationClient, config_ready_path: str):
        """
        Wait for the common configuration to be available from the configuration provider.
        """
        # Wait for configuration provider to be available
        is_alive = False
        while self.startup_timer.has_not_elapsed():
            if config_client.is_alive():
                is_alive = True
                break

            self.lc.warn("Waiting for configuration provider to be available")

            if self.ctx_done.is_set():
                raise RuntimeError("aborted waiting Configuration Provider to be available")

            self.startup_timer.sleep_for_interval()

        if not is_alive:
            raise RuntimeError("configuration provider is not available")

        # check to see if common config is loaded
        is_config_ready = False
        while self.startup_timer.has_not_elapsed():
            try:
                common_config_ready = config_client.get_configuration_value_by_full_path(
                    config_ready_path)
            except errors.EdgeX:
                self.lc.warn(
                    "waiting for Common Configuration to be available from config provider")
                self.startup_timer.sleep_for_interval()
                continue

            try:
                is_common_config_ready = parse_bool(common_config_ready.decode())
            except ValueError as e:
                self.lc.warn(
                    f"did not get boolean from config provider for {config_ready_path}: {e}")
                is_common_config_ready = False

            if is_common_config_ready:
                is_config_ready = True
                break

            self.lc.warn(
                "waiting for Common Configuration to be available from config provider")

            if self.ctx_done.is_set():
                raise RuntimeError("aborted waiting for Common Configuration to be available")

            self.startup_timer.sleep_for_interval()

        if not is_config_ready:
            raise RuntimeError("common config is not loaded - check to make sure "
                               "core-common-config-bootstrapper ran")

    def load_config_from_provider(self, service_config: ConfigurationStruct,
                                  config_client: ConfigurationClient):
        """
        Load the configuration from the provider.

        Parameters:
            service_config (ConfigurationStruct): The service configuration structure to be updated.
            config_client (ConfigurationClient): The configuration client to use for fetching
            the configuration.

        Returns:
            None
        """
        config_client.get_configuration(service_config)

    def listen_for_private_changes(self, service_config: ConfigurationStruct,
                                   config_client: ConfigurationClient,
                                   base_key: str, config_provider_type: str):
        """
        Listen for changes to the private configuration and apply them to the service configuration.
        """
        lc = self.lc

        self.wg.add(1)
        with FunctionExitCallback(self.wg.done):

            error_stream = queue.Queue()
            update_stream = queue.Queue()

            # get the MessageClient to be used in Keeper WatchForChanges method
            message_bus = None
            if config_provider_type.startswith(CONFIG_PROVIDER_TYPE_KEEPER):
                # there's no startupTimer for cp created by NewProcessorForCustomConfig
                # add a new startupTimer here
                if not self.startup_timer.has_not_elapsed():
                    self.startup_timer = timer.new_startup_timer(self.lc)

                while self.startup_timer.has_not_elapsed():
                    message_client = messaging_client_from(self.dic.get)
                    if message_client is not None:
                        message_bus = message_client
                        break
                    self.startup_timer.sleep_for_interval()

                if message_bus is None:
                    lc.error("unable to use MessageClient to watch for configuration changes")
                    return

            threading.Thread(target=config_client.watch_for_changes,
                             args=(update_stream, error_stream, empty_writable_ptr(),
                                   WRITABLE_KEY, message_bus)).start()

            while not self.ctx_done.is_set():
                try:
                    e = error_stream.get_nowait()
                    lc.error(f"error occurred during listening to the configuration changes: {e}")
                except queue.Empty:
                    pass

                try:
                    raw = update_stream.get_nowait()
                except queue.Empty:
                    continue

                used_keys = []
                try:
                    used_keys = config_client.get_configuration_keys(WRITABLE_KEY)
                except errors.EdgeX as e:
                    lc.error(
                        f"failed to get list of private configuration keys for {WRITABLE_KEY}: {e}")

                raw_map = utils.remove_unused_settings(raw,
                                                       utils.build_base_key(base_key,
                                                                            WRITABLE_KEY),
                                                       utils.string_list_to_dict(used_keys))

                self.apply_writable_updates(service_config, raw_map)

            config_client.stop_watching()
            lc.info("Watching for '%s' configuration changes has stopped", WRITABLE_KEY)

    def find_changed_key(self, previous: Any, updated: Any) -> (str, bool):
        """
        Find the changed key between the previous and updated configuration.
        """
        previous_map = utils.convert_any_to_dict(previous)
        updated_map = utils.convert_any_to_dict(updated)

        changed_key = walk_map_for_change(previous_map, updated_map, "")
        if changed_key == "":
            # look the other way around to see if an item was removed
            changed_key = walk_map_for_change(updated_map, previous_map, "")
            if changed_key == "":
                self.lc.error("could not find updated writable key or an error occurred")
                return "", False
        return changed_key, True

    def is_key_in_config(self, config_client: ConfigurationClient, config_stem: str,
                         changed_key: str) -> bool:
        """
        Check if the changed key is in the configuration.
        """
        try:
            keys = config_client.get_configuration_keys(config_stem)
        except errors.EdgeX as e:
            self.lc.error("could not get writable keys from configuration: %s", e)
            # return true because shouldn't change an overridden value
            # error means it is undetermined, so don't override to be safe
            return True
        changed_key = f"{WRITABLE_KEY}/{changed_key}"
        for key in keys:
            if changed_key in key:
                return True
        return False

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def process_common_config_change(self, full_service_config: ConfigurationStruct,
                                     previous_common_writable: Any,
                                     raw: Any,
                                     private_config_client: ConfigurationClient,
                                     config_client: ConfigurationClient):
        """
        Process the common configuration change.
        """
        changed_key, found = self.find_changed_key(previous_common_writable, raw)
        if found:
            # Only need to check App/Device writable if change was made to the all-services writable
            if config_client == self.common_config_client:
                # check if changed value (from all-services) is an App or Device common override
                other_config_client = self.app_config_client
                if other_config_client is not None:
                    if self.is_key_in_config(other_config_client, WRITABLE_KEY, changed_key):
                        self.lc.warn("ignoring changed writable key %s "
                                        "overwritten in App common writable", changed_key)
                        return

        # check if changed value is a private override
        if self.is_key_in_config(private_config_client, WRITABLE_KEY, changed_key):
            self.lc.warn("ignoring changed writable key %s overwritten in private writable",
                            changed_key)
            return

        self.apply_writable_updates(full_service_config, raw)
        return

    # pylint: disable=too-many-arguments, too-many-locals, too-many-positional-arguments
    def listen_for_common_changes(self, full_service_config: ConfigurationStruct,
                                  config_client: ConfigurationClient,
                                  private_config_client: ConfigurationClient,
                                  base_key: str,
                                  config_provider_type: str):
        """
        Leverages the Configuration Provider client's watch_for_changes() method to receive changes
        to and update the service's common configuration writable sub-struct.
        """
        lc = self.lc
        base_key = utils.build_base_key(base_key, WRITABLE_KEY)

        self.wg.add(1)
        with FunctionExitCallback(self.wg.done):

            error_stream = queue.Queue()
            update_stream = queue.Queue()
            # previous_common_writable represents the current state of the common writable config,
            # and is populated with the full_service_config common writable config values.
            previous_common_writable = empty_writable_ptr()
            previous_common_writable.__dict__.update(full_service_config.Writable.__dict__)

            # get the MessageClient to be used in Keeper WatchForChanges method
            message_bus = None
            if config_provider_type.startswith(CONFIG_PROVIDER_TYPE_KEEPER):
                while self.startup_timer.has_not_elapsed():
                    message_client = messaging_client_from(self.dic.get)
                    if message_client is not None:
                        message_bus = message_client
                        break
                    self.startup_timer.sleep_for_interval()

                if message_bus is None:
                    lc.error("unable to use MessageClient to watch for configuration changes")
                    return

            threading.Thread(target=config_client.watch_for_changes,
                             args=(update_stream, error_stream, empty_writable_ptr(),
                                   WRITABLE_KEY, message_bus)).start()

            while not self.ctx_done.is_set():
                try:
                    e = error_stream.get_nowait()
                    lc.error(f"error occurred during listening to the configuration changes: {e}")
                except queue.Empty:
                    pass

                try:
                    raw = update_stream.get_nowait()
                except queue.Empty:
                    continue

                used_keys = []
                try:
                    used_keys = config_client.get_configuration_keys(WRITABLE_KEY)
                except errors.EdgeX as e:
                    lc.error(
                        f"failed to get list of common configuration keys for {base_key}: {e}")

                raw_map = utils.remove_unused_settings(raw,
                                                       base_key,
                                                       utils.string_list_to_dict(used_keys))

                try:
                    self.process_common_config_change(full_service_config, previous_common_writable,
                                                      raw_map, private_config_client, config_client)
                except errors.EdgeX as e:
                    lc.error(e)

                # ensure that the local copy of the common writable gets updated no matter what
                previous_common_writable = raw_map

            config_client.stop_watching()
            lc.info("Watching for '%s' configuration changes has stopped", WRITABLE_KEY)

    def load_custom_config_section(self, updatable_config: Any, section_name: str):
        """
        load_custom_config_section loads the specified custom configuration section from file or
        Configuration provider. Section will be seed if Configuration provider does yet have it.
        This is used for structures custom configuration in App and Device services.
        """
        config_client = config_client_from(self.dic.get)
        if config_client is None:
            self.lc.info("Skipping use of Configuration Provider for custom configuration: "
                         "Provider not available")
            file_path = get_config_file_location(self.lc, self.flags)
            config_map = environment.load_yaml_from_file(self.lc, file_path)

            # only leave the section we are interested in
            config_map = {section_name: config_map.get(section_name)}
            update_object_from_data(updatable_config, config_map)
        else:
            self.lc.info(
                "Checking if custom configuration ('%s') exists in Configuration Provider",
                section_name)
            try:
                exists = config_client.has_sub_configuration(section_name)
            except errors.EdgeX as e:
                raise errors.new_common_edgex_wrapper(e)

            if exists and not self.flags.overwrite():
                try:
                    config_client.get_configuration(updatable_config)
                except errors.EdgeX as e:
                    raise errors.new_common_edgex_wrapper(e)

                self.lc.info("Loaded custom configuration from Configuration Provider, "
                             "no overrides applied")
            else:
                file_path = get_config_file_location(self.lc, self.flags)
                config_map = environment.load_yaml_from_file(self.lc, file_path)

                # only leave the section we are interested in
                config_map = {section_name: config_map.get(section_name)}

                update_object_from_data(updatable_config, config_map)

                # Must apply override before pushing into Configuration Provider
                override_count = environment.override_configuration(self.lc,
                                                                    updatable_config.__dict__)

                self.lc.info(
                    "Loaded custom configuration from File (%d envVars overrides applied)",
                    override_count)

                config_map = utils.convert_any_to_dict(updatable_config)

                config_client.put_configuration_map(config_map, True)

                overwrite_message = "(overwritten)" if exists and self.flags.overwrite() else ""

                self.lc.info(
                    "Custom Config loaded from file and pushed to Configuration Provider %s",
                    overwrite_message)

    def listen_for_custom_config_changes(self, config_to_watch: Any, section_name: str,
                                         changed_callback: Callable[[Any], None]):
        """
        listen_for_custom_config_changes listens for changes to the specified custom configuration
        section and applies them to the provided configuration object.
        """
        config_client = config_client_from(self.dic.get)
        if config_client is None:
            self.lc.warn("unable to watch custom configuration for changes: Configuration Provider"
                         " not enabled")
            return

        self.wg.add(1)
        with FunctionExitCallback(self.wg.done):

            error_stream = queue.Queue()
            update_stream = queue.Queue()

            config_provider_url = self.flags.config_provider()
            # get the MessageClient to be used in Keeper WatchForChanges method
            message_bus = None
            # check if the config provider type is keeper
            if config_provider_url.startswith(CONFIG_PROVIDER_TYPE_KEEPER):
                # there's no startupTimer for cp created by NewProcessorForCustomConfig
                # add a new startupTimer here
                if not self.startup_timer:
                    self.startup_timer = timer.new_startup_timer(self.lc)
                while self.startup_timer.has_not_elapsed():
                    message_client = messaging_client_from(self.dic.get)
                    if message_client is not None:
                        message_bus = message_client
                        break
                    self.startup_timer.sleep_for_interval()
                if message_bus is None:
                    self.lc.error("unable to use MessageClient to watch for custom configuration "
                                  "changes")
                    return

            threading.Thread(target=config_client.watch_for_changes,
                             args=(update_stream, error_stream, config_to_watch,
                                   section_name, message_bus)).start()

            while not self.ctx_done.is_set():
                try:
                    e = error_stream.get_nowait()
                    self.lc.error(e)
                except queue.Empty:
                    pass

                try:
                    raw = update_stream.get_nowait()
                except queue.Empty:
                    continue

                self.lc.info("Updated custom configuration '%s' has been received from the "
                             "Configuration Provider", section_name)
                changed_callback(raw)

            config_client.stop_watching()
            self.lc.info("Watching for '%s' configuration changes has stopped", section_name)


def create_provider_client(
        lc: Logger,
        service_key: str,
        config_stem: str,
        get_access_token: Optional[config.GetAccessTokenCallback],
        provider_config: config.ServiceConfig
) -> ConfigurationClient:
    """
    Creates and configures a client for interacting with a configuration provider.

    This function prepares a configuration client by setting its base path to a combination of
    the provided configuration stem and the service key. If an access token retrieval callback
    is provided, it is used to fetch an access token which is then set in the provider
    configuration. Finally, it logs the details of the configuration provider being used and
    returns a new instance of the configuration client.

    Parameters:
        lc (Logger): The logger instance for logging messages.
        service_key (str): The key identifying the service. Used as part of the base path.
        config_stem (str): The initial part of the base path for the configuration provider.
                           It is ensured to end with a '/'.
        get_access_token (Optional[config.get_access_token_callback]): An optional callback
                           function that returns an access token for authenticating with the
                           configuration provider.
        provider_config (config.ServiceConfig): The configuration settings for the configuration
                           provider client, including the type of provider and any necessary
                           authentication details.

    Returns:
        ConfigurationClient: An instance of the configuration client configured with the
                             specified provider settings.
    """
    if not config_stem.endswith('/'):
        config_stem += '/'

    provider_config.base_path = f"{config_stem}{service_key}"

    if get_access_token is not None:
        access_token = get_access_token()
        provider_config.access_token = access_token
        provider_config.get_access_token = get_access_token

    lc.info(
        f"Using Configuration provider ({provider_config.type}) from: {provider_config.get_url()} "
        f"with base path of {provider_config.base_path}")

    return new_configuration_client(provider_config)


def merge_dict(a: dict, b: dict):
    """ merge_dict merges two dict """
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dict(a[key], b[key])
            elif a[key] != b[key]:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


def get_insecure_secret_name_full_path(secret_name: str) -> str:
    """
    Returns the full configuration path of an InsecureSecret's SecretName field.
    example: Writable/InsecureSecrets/credentials001/SecretName
    """
    return f"{WRITABLE_KEY}/{INSECURE_SECRETS_KEY}/{secret_name}/{SECRET_NAME_KEY}"


def get_insecure_secret_data_full_path(secret_name: str, key: str) -> str:
    """
    Returns the full configuration path of an InsecureSecret's SecretData for a specific key.
    example: Writable/InsecureSecrets/credentials001/SecretData/username
    """
    return f"{WRITABLE_KEY}/{INSECURE_SECRETS_KEY}/{secret_name}/{SECRET_DATA_KEY}/{key}"


def walk_map_for_change(previous_map: dict, updated_map: dict, changed_key: str) -> str:
    """
    Walks through the map to find the changed key between the previous and updated maps.
    """
    for updated_key, updated_val in updated_map.items():
        previous_val = previous_map.get(updated_key)
        if previous_val is None:
            return build_new_key(changed_key, updated_key)

        if isinstance(updated_val, dict):
            if not isinstance(previous_val, dict):
                # handle the case where a new setting is added
                if previous_val is None and updated_val is not None:
                    sub_key = build_new_key(changed_key, updated_key)
                    for k in updated_val.keys():
                        return build_new_key(sub_key, k)
                return ""
            key = build_new_key(changed_key, updated_key)
            key = walk_map_for_change(previous_val, updated_val, key)
            if key:
                return key
        elif updated_val != previous_val:
            # if the value is not of type map[string]any, it should be a value to compare
            return build_new_key(changed_key, updated_key)

    return ""


def build_new_key(previous_key: str, current_key: str) -> str:
    """
    Builds a new key from the previous and current keys.
    """
    if previous_key != "":
        return utils.build_base_key(previous_key, current_key)
    return current_key


def new_processor_for_custom_config(
        flags: CommandLineParser,
        ctx_done: threading.Event,
        wg: WaitGroup,
        dic: Container):
    """
    new_processor_for_custom_config creates a new Processor instance for custom configuration.
    """
    return Processor(
        lc=logging_client_from(dic.get),
        flags=flags,
        ctx_done=ctx_done,
        wg=wg,
        dic=dic,
        startup_timer=None,
        config_updated=None
    )
