# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module contains utility functions for handling environment variables and startup information.

Functions:
    log_env_variables_override(logger: Logger, name: str, key: str, value: str): Logs that an option
    or configuration has been overridden by an environment variable.
    get_env_var_as_bool(logger: Logger, var_name: str, default_value: bool): Retrieves the value of
    an environment variable as a boolean.
    use_registry(logger: Logger): Determines whether the EDGEX_USE_REGISTRY key is set to true.
    use_security_secret_store(logger: Logger): Determines whether the EDGEX_SECURITY_SECRET_STORE
    key is set to true.
    override_with_env_var(logger: Logger, name: str, env_key: str, default_value: str): Retrieves
    the value of a specified environment variable if it exists and is not blank, or uses the default
    value.
    get_common_config_file_name(logger: Logger, common_config_file_name: str): Retrieves the common
    configuration value from the environment variables or uses the passed in value.
    get_config_file_name(logger: Logger, config_file_name: str): Retrieves the configuration
    filename value from the environment variables or uses the passed in value.
    get_profile_directory(logger: Logger, default_profile_dir: str): Retrieves the profile directory
    value from the environment variables or uses the passed in value.
    get_remote_service_hosts(logger: Logger, remote_hosts: list[str]): Retrieves the Remote Service
    host name list from an environment variable or returns the passed in (default) value.
    get_config_directory(logger: Logger, config_dir: str): Retrieves the configuration directory
    value from the environment variables or uses the passed in value or default if previous value is
    in blank.
    get_request_timeout(logger: Logger, request_timeout: str): Retrieves the request timeout value
    from the environment variables or uses the default value.
    get_config_provider_url(logger: Logger, config_provider_url: str): Retrieves the configuration
    provider URL value from the environment variables or uses the default value.
    get_env_var_as_int(logger: Logger, var_name: str, default_value: int): Retrieves the value of an
    environment variable as an integer.
    get_startup_info(logger: Logger): Retrieves the startup duration and interval values from the
    environment variables or uses the default values.

Classes:
    StartupInfo: A data class that represents the startup information for an application.
"""

import os
import re
from typing import Any
from dataclasses import dataclass
import yaml
from ..contracts.clients.logger import Logger
from ..configuration import ServiceConfig

ENV_KEY_SECURITY_SECRET_STORE = "EDGEX_SECURITY_SECRET_STORE"
ENV_KEY_DISABLE_JWT_VALIDATION = "EDGEX_DISABLE_JWT_VALIDATION"
ENV_KEY_CONFIG_PROVIDER_URL = "EDGEX_CONFIG_PROVIDER"
ENV_KEY_COMMON_CONFIG = "EDGEX_COMMON_CONFIG"
ENV_KEY_USE_REGISTRY = "EDGEX_USE_REGISTRY"
ENV_KEY_STARTUP_DURATION = "EDGEX_STARTUP_DURATION"
ENV_KEY_STARTUP_INTERVAL = "EDGEX_STARTUP_INTERVAL"
ENV_KEY_CONFIG_DIR = "EDGEX_CONFIG_DIR"
ENV_KEY_PROFILE = "EDGEX_PROFILE"
ENV_KEY_CONFIG_FILE = "EDGEX_CONFIG_FILE"
ENV_KEY_FILE_URI_TIMEOUT = "EDGEX_FILE_URI_TIMEOUT"
ENV_KEY_REMOTE_SERVICE_HOSTS = "EDGEX_REMOTE_SERVICE_HOSTS"
REDACTED_STRING = "<redacted>"
INSECURE_SECRETS_REGEX = r"^Writable\.InsecureSecrets\.[^.]+\.Secrets\..+$"
DEFAULT_CONFIG_DIR = "./res"
DEFAULT_FILE_URI_TIMEOUT = "15s"
NO_CONFIG_PROVIDER = "none"
DEFAULT_STARTUP_DURATION = 60
DEFAULT_STARTUP_INTERVAL = 1

CONFIG_PATH_SEPARATOR = r"/"
CONFIG_NAME_SEPARATOR = r"-"
ENV_NAME_SEPARATOR = r"_"


def log_env_variables_override(logger: Logger, name: str, key: str, value: str):
    """
    Logs that an option or configuration has been override by an environment variable. If the key
    belongs to a Secret within Writable.InsecureSecrets, the value is redacted when printing it.
    """
    value_str = value
    if bool(re.match(INSECURE_SECRETS_REGEX, name)):
        value_str = REDACTED_STRING

    logger.info(f"Variables override of '{name}' by environment variable: {key}={value_str}")


def get_env_var_as_bool(logger: Logger, var_name: str, default_value: bool) -> (bool, bool):
    """
    Helper function to get the value of an environment variable as a boolean.
    If the environment variable is not set or contains an invalid value, the default value is
    returned.
    """
    env_value = os.environ.get(var_name)
    if env_value is not None:
        if env_value.lower() == "true":
            return True, True
        if env_value.lower() == "false":
            return False, True
        logger.warn(f"Invalid value for environment variable {var_name}: {env_value}. Using "
                       f"default value {default_value}")
    return default_value, False


def use_registry(logger: Logger) -> (bool, bool):
    """
    Returns whether the EDGEX_USE_REGISTRY key is set to true (case-insensitive) and whether the
    override was used
    """
    result, overrode = get_env_var_as_bool(logger, ENV_KEY_USE_REGISTRY, False)
    if overrode:
        log_env_variables_override(logger, "-r/--registry", ENV_KEY_USE_REGISTRY, result)
    return result, overrode


def use_security_secret_store(logger: Logger) -> bool:
    """
    Returns whether the EDGEX_SECURITY_SECRET_STORE key is set to true (case-insensitive) or not
    """
    result, overrode = get_env_var_as_bool(logger, ENV_KEY_SECURITY_SECRET_STORE, False)
    if overrode:
        log_env_variables_override(logger, ENV_KEY_SECURITY_SECRET_STORE,
                                   ENV_KEY_SECURITY_SECRET_STORE, result)
    return result


def get_env_var_as_str(logger: Logger, name: str, env_key: str, default_value: str) -> str:
    """
    gets the value of specified environment variable (env_key) if it exists and is not in blank, or
    uses the passed in default value.
    """
    if env_key in os.environ:
        env_value = os.environ[env_key]
        if len(env_value) > 0:  # only override if the value is not blank
            log_env_variables_override(logger, name, env_key, env_value)
            return env_value

    return default_value


def get_common_config_file_name(logger: Logger, common_config_file_name: str) -> str:
    """
    gets the common configuration value from the environment variables (if it exists) or uses
    passed in value.
    """
    return get_env_var_as_str(logger, "-cc/--commonConfig", ENV_KEY_COMMON_CONFIG,
                              common_config_file_name)


def get_config_file_name(logger: Logger, config_file_name: str) -> str:
    """
    gets the configuration filename value from the environment variables (if it exists) or uses
    passed in value.
    """
    return get_env_var_as_str(logger, "-cf/--configFile", ENV_KEY_CONFIG_FILE,
                              config_file_name)


def get_profile_directory(logger: Logger, default_profile_dir: str) -> str:
    """
    gets the profile directory value from the environment variables (if it exists) or uses
    passed in value.
    """
    profile_dir = get_env_var_as_str(logger, "-p/--profile", ENV_KEY_PROFILE,
                                     default_profile_dir)
    if len(profile_dir) > 0:
        profile_dir = f"{profile_dir}/"
    return profile_dir


def get_remote_service_hosts(logger: Logger, remote_hosts: list[str]) -> list[str]:
    """
    gets the Remote Service host name list from an environment variable (if it exists), if not
    returns the passed in (default) value
    """
    if ENV_KEY_REMOTE_SERVICE_HOSTS in os.environ:
        env_value = os.environ[ENV_KEY_REMOTE_SERVICE_HOSTS]
        if len(env_value) > 0:  # only override if the value is not blank
            log_env_variables_override(logger, "-rsh/--remoteServiceHosts",
                                       ENV_KEY_REMOTE_SERVICE_HOSTS, env_value)
            return env_value.split(",")
    return remote_hosts


def get_config_directory(logger: Logger, config_dir: str) -> str:
    """
    gets the configuration directory value from the environment variables (if it exists) or uses
    passed in value or default if previous value is in blank.
    """
    config_dir = get_env_var_as_str(logger, "-cd/-configDir", ENV_KEY_CONFIG_DIR,
                                    config_dir)
    if len(config_dir) == 0:
        return DEFAULT_CONFIG_DIR
    return config_dir


def get_request_timeout(logger: Logger, request_timeout: str) -> str:
    """
    gets the request timeout value from the environment variables (if it exists) or uses the
    default value.
    """
    request_timeout = get_env_var_as_str(logger, "URI Request Timeout",
                                         ENV_KEY_FILE_URI_TIMEOUT, request_timeout)
    if len(request_timeout) == 0:
        return DEFAULT_FILE_URI_TIMEOUT
    return request_timeout


def get_config_provider_url(logger: Logger, config_provider_url: str) -> str:
    """
    gets the configuration provider URL value from the environment variables (if it exists) or
    uses the default value.
    """
    config_provider_url = get_env_var_as_str(logger, "-cp/--configProvider",
                                             ENV_KEY_CONFIG_PROVIDER_URL, config_provider_url)
    if config_provider_url == NO_CONFIG_PROVIDER:
        return ""
    return config_provider_url


@dataclass
class StartupInfo:
    """
    A data class that represents the startup information for an application.

    Attributes:
        duration (int): The startup duration in seconds. This is the maximum amount of time the
                        application will wait for all the necessary services to become available.
        interval (int): The interval in seconds between each check for the availability of the
                        necessary services.
    """
    duration: int
    interval: int


def get_env_var_as_int(logger: Logger, var_name: str, default_value: int) -> int:
    """
    Helper function to get the value of an environment variable as an integer.
    If the environment variable is not set or contains an invalid value, the default value is
    returned.
    """
    env_value = os.environ.get(var_name)
    if env_value is not None:
        try:
            return int(env_value)
        except ValueError:
            logger.warn(f"Invalid value for environment variable {var_name}: {env_value}. "
                           f"Using default value {default_value}")
    return default_value


def get_startup_info(logger: Logger) -> StartupInfo:
    """
    Gets the startup duration and interval values from the environment variables (if they exist) or
    uses the default values.
    """
    duration = get_env_var_as_int(logger, ENV_KEY_STARTUP_DURATION, DEFAULT_STARTUP_DURATION)
    interval = get_env_var_as_int(logger, ENV_KEY_STARTUP_INTERVAL, DEFAULT_STARTUP_INTERVAL)
    return StartupInfo(duration, interval)


def load_yaml_from_file(logger: Logger, file_path: str) -> dict:
    """
    Load a yaml file from the specified path and return the parsed yaml object.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing yaml file: {file_path}")
        raise e


def _build_config_paths(parsed_yaml) -> list[str]:
    """
    Builds the configuration paths from parsed yaml object.
    """
    config_paths = []
    for key, value in parsed_yaml.items():
        if value is None or not isinstance(value, dict):
            config_paths.append(key)
            continue

        sub_map = _build_config_paths(value)
        for path in sub_map:
            config_paths.append(f"{key}/{path}")
    return config_paths


def _build_override_names(paths: list[str]) -> dict[str, str]:
    """
    Builds the override names from the configuration paths.
    """
    override_names = {}
    for p in paths:
        override_names[_get_override_names(p)] = p
    return override_names


def _get_override_names(path: str) -> str:
    """
    Get the override names from the configuration file.
    """
    override = path.replace(CONFIG_PATH_SEPARATOR, ENV_NAME_SEPARATOR)
    override = override.replace(CONFIG_NAME_SEPARATOR, ENV_NAME_SEPARATOR)
    return override.upper()


def _get_configuration_value(path: str, configuration: dict) -> Any:
    """
    Get the configuration value from the configuration dictionary.
    """
    # First check the case of flattened configuration where the path is the key
    if path in configuration:
        return configuration[path]

    # Deal with the case of not flattened configuration where the path is individual keys
    keys = path.split(CONFIG_PATH_SEPARATOR)

    current_config = configuration

    for key in keys:
        if key not in current_config:
            return None

        item = current_config[key]
        if not isinstance(item, dict):
            return item

        current_config = item

    return None


def _set_configuration_value(path: str, value: Any, configuration: dict):
    """
    Set the configuration value in the configuration dictionary.
    """
    # First check the case of flattened configuration where the path is the key
    if path in configuration:
        configuration[path] = value
        return

    # Deal with the case of not flattened configuration where the path is individual keys
    keys = path.split(CONFIG_PATH_SEPARATOR)

    current_config = configuration

    for key in keys:
        # note that we are not checking if the key exists in the current_config as private
        # _set_configuration_value function is called only after _get_configuration_value function
        # so that the path is valid
        item = current_config[key]
        if not isinstance(item, dict):
            current_config[key] = value
            return

        current_config = item


def _parse_comma_separated_string(value: str) -> list[str]:
    """
    Parse a comma-separated string and return a list of strings.
    """
    return [item.strip() for item in value.split(",")]


def _convert_to_type(old_value: Any, new_value: str) -> Any:
    """
    Convert the new_value to the type of old_value.
    If the conversion is not possible, return the original new_value.
    """
    old_type = type(old_value)

    try:
        if old_type is bool:
            return new_value.lower() in ['true', '1', 'yes']
        if old_type is list:
            return _parse_comma_separated_string(new_value)
        return old_type(new_value)
    except ValueError:
        return new_value


def override_configuration(logger: Logger, configuration: dict) -> int:
    """
    Override the configuration with the environment variables.
    """
    override_count = 0  # count of overridden values
    paths = _build_config_paths(configuration)
    override_names = _build_override_names(paths)

    for env_key, env_value in os.environ.items():
        if env_key not in override_names:
            continue
        old_value = _get_configuration_value(override_names[env_key], configuration)
        if old_value is None:
            logger.warn(f"Configuration value not found for {override_names[env_key]}")
            continue
        new_value = _convert_to_type(old_value, env_value)
        _set_configuration_value(override_names[env_key], new_value, configuration)
        override_count += 1
        log_env_variables_override(logger, override_names[env_key], env_key, env_value)

    return override_count


def override_config_provider_info(logger: Logger, configuration: ServiceConfig) -> ServiceConfig:
    """
    Override the configuration with the environment variables.
    """
    url = get_config_provider_url(logger, "")
    if len(url) > 0:
        log_env_variables_override(logger, "Configuration Provider URL",
                                   ENV_KEY_CONFIG_PROVIDER_URL, url)

        if url == NO_CONFIG_PROVIDER:
            return ServiceConfig()

        configuration.populate_from_url(url)

    return configuration
