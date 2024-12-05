#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the MQTTFactory class that creates a new MQTT client instance.
"""
from dataclasses import dataclass
from typing import Optional

import paho.mqtt.client as pahomqtt

from ..secret import get_secret_data, validate_secret_data
from ...bootstrap.interface.secret import SecretProvider
from ...bootstrap.secret.secret import SecretData
from ...contracts.clients.logger import Logger
from ...contracts.errors import EdgeX
from ...interfaces.messaging import AUTH_MODE_NONE, AUTH_MODE_USERNAME_PASSWORD, \
    AUTH_MODE_CLIENT_CERT, AUTH_MODE_CACERT
from ...internal.common.config import WillConfig


@dataclass
class MQTTClientConfig:
    # pylint: disable=too-many-instance-attributes
    """
    MQTTClientConfig is a data class that holds the configuration for an MQTT client.
    """
    # broker_address is the address of the MQTT broker i.e. "test.mosquitto.org"
    broker_address: str
    # topic is the MQTT topic to publish messages to
    topic: str
    # secret_name is the name of the secret in secret provider to retrieve the MQTT credentials
    secret_name: str
    # auth_mode indicates what to use when connecting to the broker. Options are "none", "cacert" ,
    # "usernamepassword", "clientcert". If a CA Cert exists in the secret_name data then it will be
    # used for all modes except "none".
    auth_mode: str
    # client_id is the client id to use when connecting to the broker
    client_id: str
    # qos is the quality of service to use when publishing messages
    qos: int = 0
    # retain indicates whether the broker should retain messages
    retain: bool = False
    # auto_reconnect indicates whether the client should automatically reconnect to the broker
    auto_reconnect: bool = False
    # skip_verify indicates whether to skip verifying the server's certificate
    skip_verify: bool = False
    # keep_alive is the time in seconds to keep the connection alive
    keep_alive: int = 60  # default keep alive time is 60 seconds in paho mqtt
    # connect_timeout is the time in seconds to wait for the connection to be established
    connect_timeout: float = 5.0  # default connect timeout is 5 seconds in paho mqtt
    # max_reconnect_interval is the maximum time in seconds to wait between reconnections
    max_reconnect_interval: int = 120  # default max reconnect interval is 120 seconds in paho mqtt
    # will is the last will and testament configuration
    will: Optional[WillConfig] = None


class MQTTFactory:
    """
    MQTTFactory is a factory class that creates a new MQTT client instance.
    """
    # pylint: disable=too-many-arguments, too-few-public-methods, too-many-positional-arguments
    def __init__(self, secret_data_provider: SecretProvider, logger: Logger, auth_mode: str,
                 secret_name: str, skip_cert_verify: bool):
        self._secret_data_provider = secret_data_provider
        self._logger = logger
        self._auth_mode = auth_mode
        self._secret_name = secret_name
        self._skip_cert_verify = skip_cert_verify
        self._client_config = None

    def create(self, client_config: MQTTClientConfig) -> (pahomqtt.Client, EdgeX):
        """
        Create a new MQTT client instance.
        """
        if len(self._auth_mode) == 0:
            self._auth_mode = AUTH_MODE_NONE
            self._logger.warn(f"auth_mode is not set, defaulting to '{AUTH_MODE_NONE}'")

        secret_data, err = get_secret_data(self._auth_mode, self._secret_name,
                                           self._secret_data_provider)
        if err is not None:
            return None, err

        if secret_data is not None:
            err = validate_secret_data(self._auth_mode, self._secret_name, secret_data)
            if err is not None:
                return None, err

        client = self._new_client(client_config, secret_data)
        return client, None

    def _new_client(self, client_config: MQTTClientConfig,
                    secret_data: SecretData) -> pahomqtt.Client:
        # pylint: disable=no-value-for-parameter
        client = pahomqtt.Client(callback_api_version=pahomqtt.CallbackAPIVersion.VERSION2,
                                 reconnect_on_failure=client_config.auto_reconnect)
        client.client_id = client_config.client_id
        client.keepalive = client_config.keep_alive
        client.connect_timeout = client_config.connect_timeout
        if client_config.will and client_config.will.Enabled:
            client.will_set(
                client_config.will.Topic,
                client_config.will.Payload,
                int(client_config.will.Qos),
                client_config.will.Retained
            )
        if secret_data is not None:
            if client_config.auth_mode == AUTH_MODE_USERNAME_PASSWORD:
                client.username_pw_set(secret_data.username, secret_data.password)
            elif client_config.auth_mode == AUTH_MODE_CLIENT_CERT:
                client.tls_set(certfile=str(secret_data.cert_pem_block),
                               keyfile=str(secret_data.key_pem_block))
            elif client_config.auth_mode == AUTH_MODE_CACERT:
                client.tls_set(ca_certs=str(secret_data.ca_pem_block))
        return client
