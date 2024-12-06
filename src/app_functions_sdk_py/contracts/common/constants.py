# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Constants for the App Functions SDK Python package.

This module defines constants that are used throughout the App Functions SDK Python package.
"""
import os

API_VERSION = "v3"
API_BASE = "/api/v3"

CONFIG_STEM_APP = "edgex/v3"

APPLICATION_VERSION = os.getenv("APPLICATION_VERSION", "0.0.0")

# Constants related to the key of environment variables
ENV_ENCODE_ALL_EVENTS = "EDGEX_ENCODE_ALL_EVENTS_CBOR"

# Miscellaneous constants

# Defaults the interval at which a given service client will refresh its endpoint
# from the Registry, if used
CLIENT_MONITOR_DEFAULT = 15000

CORRELATION_HEADER = "X-Correlation-ID"  # Sets the key of the Correlation ID HTTP header

# Constants related to how services identify themselves in the Service Registry
CORE_COMMON_CONFIG_SERVICE_KEY = "core-common-config-bootstrapper"
CORE_DATA_SERVICE_KEY = "core-data"
CORE_METADATA_SERVICE_KEY = "core-metadata"
CORE_COMMAND_SERVICE_KEY = "core-command"

# Constants related to the possible content types supported by the APIs
ACCEPT = "Accept"
CONTENT_TYPE = "Content-Type"
CONTENT_LENGTH = "Content-Length"
CONTENT_TYPE_CBOR = "application/cbor"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_TOML = "application/toml"
CONTENT_TYPE_YAML = "application/x-yaml"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_XML = "application/xml"

# Constants related to defined url path names and parameters in the v3 service APIs
VALUE_TRUE = "true"
VALUE_FALSE = "false"
FLATTEN = "flatten"
KEY = "key"
PLAINTEXT = "plaintext"
KEY_ONLY = "keyOnly"
PREFIX_MATCH = "prefixMatch"
SERVICE_ID = "serviceId"
DEREGISTERED = "deregistered"
ALL = "all"
OFFSET = "offset"
LIMIT = "limit"
COUNT = "count"
DEVICE = "device"
NAME = "name"
START = "start"
END = "end"
AGE = "age"
ID = "id"
PUSH_EVENT = "ds-pushevent"
RETURN_EVENT = "ds-returnevent"
RESOURCE_NAME  = "resourceName"
RESOURCE_NAMES = "resourceNames"
DEVICE_COMMAND = "deviceCommand"
RESOURCE = "resource"
LABELS = "labels"
MODEL = "model"
MANUFACTURER = "manufacturer"
PROFILE = "profile"
DESCENDANTS_OF = "descendantsOf"
MAX_LEVELS = "maxLevels"
CHECK = "check"
SERVICE = "service"

# Constants for AdminState
LOCKED = "LOCKED"
UNLOCKED = "UNLOCKED"

# Constants for DeviceProfile
READ_WRITE_R = "R"
READ_WRITE_W = "W"
READ_WRITE_RW = "RW"
READ_WRITE_WR = "WR"

# Constants related to defined routes in the v3 service APIs
API_CONFIG_ROUTE = API_BASE + "/config"
API_PING_ROUTE = API_BASE + "/ping"
API_VERSION_ROUTE = API_BASE + "/version"
API_SECRET_ROUTE = API_BASE + "/secret"

API_KVS_ROUTE = API_BASE + "/kvs"
API_KVS_BY_KEY_ROUTE = API_KVS_ROUTE + "/" + KEY + "/{" + KEY + "}"
API_REGISTRY_ROUTE = API_BASE + "/registry"
API_ALL_REGISTRY_ROUTE = API_REGISTRY_ROUTE + "/" + ALL

API_EVENT_ROUTE = API_BASE + "/event"
API_ALL_EVENT_ROUTE = API_EVENT_ROUTE + "/" + ALL
API_EVENT_COUNT_ROUTE = API_EVENT_ROUTE + "/" + COUNT

API_READING_ROUTE = API_BASE + "/reading"
API_ALL_READING_ROUTE = API_READING_ROUTE + "/" + ALL
API_READING_COUNT_ROUTE = API_READING_ROUTE + "/" + COUNT

API_DEVICE_ROUTE = API_BASE + "/device"
API_ALL_DEVICE_ROUTE = API_DEVICE_ROUTE + "/" + ALL

API_DEVICE_SERVICE_ROUTE = API_BASE + "/deviceservice"
API_ALL_DEVICE_SERVICE_ROUTE = API_DEVICE_SERVICE_ROUTE + "/" + ALL

API_DEVICE_PROFILE_ROUTE = API_BASE + "/deviceprofile"
API_DEVICE_PROFILE_BASIC_INFO_ROUTE = API_DEVICE_PROFILE_ROUTE + "/basicinfo"
API_ALL_DEVICE_PROFILE_BASIC_INFO_ROUTE = API_DEVICE_PROFILE_BASIC_INFO_ROUTE + "/" + ALL
API_DEVICE_PROFILE_DEVICE_COMMAND_ROUTE = API_DEVICE_PROFILE_ROUTE + "/" + DEVICE_COMMAND
API_DEVICE_PROFILE_RESOURCE_ROUTE = API_DEVICE_PROFILE_ROUTE + "/" + RESOURCE
API_DEVICE_PROFILE_UPLOAD_FILE_ROUTE = API_DEVICE_PROFILE_ROUTE + "/uploadfile"
API_DEVICE_PROFILE_BY_NAME_ROUTE = API_DEVICE_PROFILE_ROUTE + "/" + NAME + "/{" + NAME + "}"
API_ALL_DEVICE_PROFILE_ROUTE = API_DEVICE_PROFILE_ROUTE + "/" + ALL

API_DEVICE_RESOURCE_ROUTE = API_BASE + "/deviceresource"

# Constants related to Reading ValueTypes
VALUE_TYPE_BOOL = "Bool"
VALUE_TYPE_STRING = "String"
VALUE_TYPE_UINT8 = "Uint8"
VALUE_TYPE_UINT16 = "Uint16"
VALUE_TYPE_UINT32 = "Uint32"
VALUE_TYPE_UINT64 = "Uint64"
VALUE_TYPE_INT8 = "Int8"
VALUE_TYPE_INT16 = "Int16"
VALUE_TYPE_INT32 = "Int32"
VALUE_TYPE_INT64 = "Int64"
VALUE_TYPE_FLOAT32 = "Float32"
VALUE_TYPE_FLOAT64 = "Float64"
VALUE_TYPE_BINARY = "Binary"
VALUE_TYPE_BOOL_ARRAY = "BoolArray"
VALUE_TYPE_STRING_ARRAY = "StringArray"
VALUE_TYPE_UINT8_ARRAY = "Uint8Array"
VALUE_TYPE_UINT16_ARRAY = "Uint16Array"
VALUE_TYPE_UINT32_ARRAY = "Uint32Array"
VALUE_TYPE_UINT64_ARRAY = "Uint64Array"
VALUE_TYPE_INT8_ARRAY = "Int8Array"
VALUE_TYPE_INT16_ARRAY = "Int16Array"
VALUE_TYPE_INT32_ARRAY = "Int32Array"
VALUE_TYPE_INT64_ARRAY = "Int64Array"
VALUE_TYPE_FLOAT32_ARRAY = "Float32Array"
VALUE_TYPE_FLOAT64_ARRAY = "Float64Array"
VALUE_TYPE_OBJECT = "Object"
VALUE_TYPE_OBJECT_ARRAY = "ObjectArray"

CONFIG_KEYS_REPLACEMENTS = {
    "EnableCORS": "enable_cors",
    "CORSAllowCredentials": "cors_allow_credentials",
    "CORSAllowedOrigins": "cors_allowed_origins",
    "CORSAllowedHeaders": "cors_allowed_headers",
    "CORSAllowedMethods": "cors_allowed_methods",
    "CORSExposedHeaders": "cors_exposed_headers",
    "CORSMaxAge": "cors_max_age",
    "CORSConfiguration": "cors_configuration",
    "QoS": "qos"
}

FUNCTION_KEYS_REPLACEMENTS = {
    "MQTTExport": "mqtt_export",
    "HTTPExport": "http_export",
    "JSONLogic": "json_logic"
}

# MessageBus Topics

# Common Topics
DEFAULT_BASE_TOPIC = "edgex"
METRICS_PUBLISH_TOPIC = "telemetry"
