# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The commandline module of the App Functions SDK Python package.

This module provides a command line parser for the App Functions SDK. It uses argparse to parse
command line arguments and provides methods to access these arguments.

Classes:
    CommandLineParser: A command line parser for the App Functions SDK.

Functions:
    config_directory() -> str: Returns the configuration directory argument.
    config_file() -> str: Returns the configuration file argument.
    config_provider() -> str: Returns the configuration provider argument.
    common_config() -> str: Returns the common configuration argument.
    profile() -> str: Returns the profile argument.
    registry() -> bool: Returns the registry argument.
    overwrite() -> bool: Returns the overwrite argument.
    skip_version_check() -> bool: Returns the skip version check argument.
    service_key() -> str: Returns the service key argument.
    dev_mode() -> bool: Returns the dev mode argument.
    remote_service_hosts() -> [str]: Returns the remote service hosts argument.
"""

import argparse

DEFAULT_CONFIG_PROVIDER = "keeper.http://localhost:59890"
DEFAULT_CONFIG_FILE = "configuration.yaml"


class CommandLineParser:
    """
    A command line parser for the App Functions SDK.

    This class uses argparse to parse command line arguments and provides methods to access these
    arguments.

    Attributes:
        args: The parsed command line arguments.

    Methods:
        config_directory() -> str:
            Returns the configuration directory argument.

        config_file() -> str:
            Returns the configuration file argument.

        config_provider() -> str:
            Returns the configuration provider argument.

        common_config() -> str:
            Returns the common configuration argument.

        profile() -> str:
            Returns the profile argument.

        registry() -> bool:
            Returns the registry argument.

        overwrite() -> bool:
            Returns the overwrite argument.

        skip_version_check() -> bool:
            Returns the skip version check argument.

        service_key() -> str:
            Returns the service key argument.

        dev_mode() -> bool:
            Returns the dev mode argument.

        remote_service_hosts() -> [str]:
            Returns the remote service hosts argument.
    """
    def __init__(self):
        parser = argparse.ArgumentParser(description='App Functions SDK Command Line Parser')
        parser.add_argument('-c', '--configDir', dest='configDir',
                            action='store', type=str, required=False, default='res',
                            help='Specify local configuration directory')
        parser.add_argument('-cf', '--configFile', dest='configFile',
                            action='store', type=str, required=False, default=DEFAULT_CONFIG_FILE,
                            help='Indicates the name of the local configuration file or the URI of '
                                 'the private configuration.')
        parser.add_argument('-cp', '--configProvider', dest='configProvider',
                            action='store', type=str, required=False,
                            default="",
                            help='Indicates to use Configuration Provider service at specified '
                                 'URL.')
        parser.add_argument('-cc', '--commonConfig', dest='commonConfig',
                            action='store', type=str, required=False, default='',
                            help='Takes the location where the common configuration is loaded from '
                                 '- either a local file path or a URI when not using the '
                                 'Configuration Provider')
        parser.add_argument('-p', '--profile', dest='profile',
                            action='store', type=str, required=False, default='',
                            help='Indicates configuration profile other than default. Default is no'
                                 ' profile name resulting in using ./res/configuration.yaml.')
        parser.add_argument('-r', '--registry', dest='registry',
                            action='store_true', required=False,
                            help='Indicates service should use the Registry. Connection information'
                                 ' is pulled from the [Registry] configuration section.')
        parser.add_argument('-o', '--overwrite', dest='overwrite',
                            action='store_true', required=False,
                            help='Overwrite configuration in provider with local configuration.')
        parser.add_argument('-s', '--skipVersionCheck', dest='skipVersionCheck',
                            action='store_true', required=False,
                            help="Indicates the service should skip the Core Service's version "
                                 "compatibility check.")
        parser.add_argument('-sk', '--serviceKey', dest='serviceKey',
                            action='store', type=str, required=False, default=None,
                            help="Overrides the service service key used with Registry and/or "
                                 "Configuration Providers.If the name provided contains the text "
                                 "`<profile>`, this text will be replaced with the name of the "
                                 "profile used.")
        parser.add_argument('-d', '--dev', dest='dev',
                            action='store_true', required=False,
                            help='Indicates service to run in developer mode which causes Host '
                                 'configuration values to be overridden with `localhost`. This is '
                                 'so that it will run with other services running in Docker '
                                 '(aka hybrid mode)')
        parser.add_argument('-rsh', '--remoteServiceHosts', dest='remoteServiceHosts',
                            action='store', type=str, required=False, default=None,
                            help='Indicates that the service is running remote from the core EdgeX '
                                 'services and to use the listed host names to connect remotely. '
                                 '<host names> contains 3 comma separated host names separated by '
                                 '\',\'. 1st is the local system host name, 2nd is the remote '
                                 'system host name and 3rd is the WebServer bind host name.'
                                 'example: -rsh=192.0.1.20,192.0.1.5,localhost')
        self.args = parser.parse_args()

    def config_directory(self) -> str:
        """
        Returns the configuration directory argument.

        Returns:
            str: The configuration directory argument.
        """
        return self.args.configDir

    def config_file(self) -> str:
        """
        Returns the configuration file argument.

        Returns:
            str: The configuration file argument.
        """
        return self.args.configFile

    def config_provider(self) -> str:
        """
        Returns the configuration provider argument.

        Returns:
            str: The configuration provider argument.
        """
        return self.args.configProvider

    def common_config(self) -> str:
        """
        Returns the common configuration argument.

        Returns:
            str: The common configuration argument.
        """
        return self.args.commonConfig

    def profile(self) -> str:
        """
        Returns the profile argument.

        Returns:
            str: The profile argument.
        """
        return self.args.profile

    def registry(self) -> bool:
        """
        Returns the registry argument.

        Returns:
            bool: The registry argument.
        """
        return self.args.registry

    def overwrite(self) -> bool:
        """
        Returns the overwrite argument.

        Returns:
            bool: The overwrite argument.
        """
        return self.args.overwrite

    def skip_version_check(self) -> bool:
        """
        Returns the skip version check argument.

        Returns:
            bool: The skip version check argument.
        """
        return self.args.skipVersionCheck

    def service_key(self) -> str:
        """
        Returns the service key argument.

        Returns:
            str: The service key argument.
        """
        return self.args.serviceKey

    def dev_mode(self) -> bool:
        """
        Returns the dev mode argument.

        Returns:
            bool: The dev mode argument.
        """
        return self.args.dev

    def remote_service_hosts(self) -> [str]:
        """
        Returns the remote service hosts argument.

        Returns:
            [str]: The remote service hosts argument.
        """
        return self.args.remoteServiceHosts.split(',') if self.args.remoteServiceHosts else None
