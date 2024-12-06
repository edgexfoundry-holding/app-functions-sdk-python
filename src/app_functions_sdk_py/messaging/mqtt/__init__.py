# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines constants for configuring MQTT message bus options. These constants are used to
set up the MQTT client with specific configurations such as authentication credentials, connection
timeout, quality of service (QoS), and more.

Constants:
    USERNAME (str): Key for specifying the username for MQTT broker authentication.
    PASSWORD (str): Key for specifying the password for MQTT broker authentication.
    CLIENT_ID (str): Key for specifying a unique client identifier for the MQTT session.
    CONNECT_TIMEOUT (str): Key for specifying the maximum time in seconds to wait for a connection
    to the MQTT broker.
    AUTO_RECONNECT (str): Key for enabling or disabling automatic reconnection to the MQTT broker.
    SKIP_CERT_VERIFY (str): Key for enabling or disabling SSL/TLS certificate verification.
    CERT_FILE (str): Key for specifying the path to the client's certificate file for SSL/TLS.
    KEY_FILE (str): Key for specifying the path to the client's private key file for SSL/TLS.
    CA_FILE (str): Key for specifying the path to the CA certificate file for SSL/TLS.
    KEY_PEM_BLOCK (str): Key for specifying the client's private key PEM block as a string.
    CERT_PEM_BLOCK (str): Key for specifying the client's certificate PEM block as a string.
    CA_PEM_BLOCK (str): Key for specifying the CA certificate PEM block as a string.
    QOS (str): Key for specifying the Quality of Service level for message delivery.
    KEEP_ALIVE (str): Key for specifying the maximum period in seconds allowed between
    communications with the broker.
    RETAINED (str): Key for specifying if messages are retained by the broker for new subscribers.
    CLEAN_SESSION (str): Key for specifying if the broker removes all information about the client
    when it disconnects.
"""
# common constants for messagebus.Optional properties
USERNAME = "Username"
PASSWORD = "Password"
CLIENT_ID = "ClientId"
CONNECT_TIMEOUT = "ConnectTimeout"
AUTO_RECONNECT = "AutoReconnect"
QOS = "Qos"
KEEP_ALIVE = "KeepAlive"
RETAINED = "Retained"
CLEAN_SESSION = "CleanSession"
AUTH_MODE = "AuthMode"
