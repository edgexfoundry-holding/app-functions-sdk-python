# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Constants for the App Functions SDK.

This module defines constants that are used throughout the App Functions SDK.
"""

DEFAULT_PROFILE_SUFFIX_PLACEHOLDER = "<profile>"

DEFAULT_PIPELINE_ID = "default-pipeline"

TRIGGER_TYPE_MESSAGEBUS = "EDGEX-MESSAGEBUS"
TRIGGER_TYPE_MQTT = "EXTERNAL-MQTT"
TRIGGER_TYPE_HTTP = "HTTP"

DEFAULT_TRIGGER_TYPE = TRIGGER_TYPE_MESSAGEBUS

TOPIC_WILDCARD = "#"
TOPIC_SINGLE_LEVEL_WILDCARD = "+"
TOPIC_LEVEL_SEPERATOR = "/"
TARGET_TYPE_RAW = "raw"
TARGET_TYPE_EVENT = "event"
TARGET_TYPE_METRIC = "metric"
TARGET_TYPE_EMPTY = ""

KEY_DEVICE_NAME = "devicename"
KEY_PROFILE_NAME = "profilename"
KEY_SOURCE_NAME = "sourcename"
KEY_RECEIVEDTOPIC = "receivedtopic"
KEY_PIPELINEID = "pipelineid"

SPILT_COMMA = ","

SECRET_USERNAME_KEY = "username"
SECRET_PASSWORD_KEY = "password"
SECRET_CLIENT_KEY = "clientkey"
SECRET_CLIENT_CERT = "clientcert"
SECRET_CA_CERT = "cacert"

DB_SQLITE = "sqlite"
