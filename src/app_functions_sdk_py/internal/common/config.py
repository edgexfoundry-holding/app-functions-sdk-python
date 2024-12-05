# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the data structures for the configuration of
an EdgeX Foundry application service.

Classes:
    TopicPipeline: Configuration for function pipelines based on topics.
    PipelineFunction: Configuration for individual pipeline functions.
    PipelineInfo: Top-level configuration for all pipelines.
    StoreAndForwardInfo: Configuration for the store and forward mechanism.
    InsecureSecretsInfo: Configuration for insecure secrets.
    TelemetryInfo: Configuration for telemetry data collection.
    WritableInfo: Configuration that can be modified at runtime.
    RegistryInfo: Configuration for service registry.
    CORSConfigurationInfo: Configuration for CORS headers.
    ServiceInfo: General service configuration.
    HttpConfig: HTTP server configuration.
    MessageBusInfo: Configuration for the message bus.
    WillConfig: Configuration for MQTT Last Will and Testament.
    ExternalMqttConfig: Configuration for external MQTT brokers.
    TriggerInfo: Configuration for triggers initiating actions.
    ClientInfo: Configuration for external clients interacting with the service.
    DatabaseInfo: Configuration for the database used by the service.
    ConfigurationStruct: Main configuration structure containing all configurable components.
"""

from dataclasses import dataclass, field
from typing import Optional

from ...contracts.common.constants import DEFAULT_BASE_TOPIC

# pylint: disable=invalid-name
# For the ConfigurationStruct and related configuration classes as defined in this module, we
# intentionally name their fields with the same upper-camel-case naming style as the fields in the
# corresponding Go SDK, so that the configuration key as stored in the Configuration Provider,
# core-keeper, can be consistent between the Python and Go SDKs.

@dataclass
class TopicPipeline:
    """
    Represents a pipeline configuration for a Per Topics function pipeline.

    Attributes:
        Id (str): Unique identifier for the pipeline.
        Topics (str): Comma-separated topics matched against the incoming to determine if pipeline
                      should execute.
        ExecutionOrder (str): Defines the order of execution for functions within this pipeline.
    """
    Id: str = field(default_factory=str)
    Topics: str = field(default_factory=str)
    ExecutionOrder: str = field(default_factory=str)


@dataclass
class PipelineFunction:
    """
    A collection of built-in pipeline functions configurations.

    Attributes:
        Parameters (dict[str, str]): Key-value pairs representing function parameters.
    """
    Parameters: dict[str, str] = field(default_factory=dict[str, str])


@dataclass
class PipelineInfo:
    """
    Defines the top level data for configurable pipelines.

    Attributes:
        ExecutionOrder (str): Comma separated list of pipeline function names to execute
         in order as the default functions pipeline.
        PerTopicPipelines (dict[str, TopicPipeline]): Defines and configures the collection of
         function pipelines that are triggered based on the topic the data is received on.
        TargetType (str): The object type that all configurable pipelines will receive.
        Functions (dict[str, PipelineFunction]): Defines and configures the collection of
         available pipeline functions to be used in the above functions pipelines.
    """
    ExecutionOrder: str = field(default_factory=str)
    PerTopicPipelines: dict[str, TopicPipeline] = field(default_factory=dict[str, TopicPipeline])
    TargetType: str = field(default_factory=str)
    Functions: dict[str, PipelineFunction] = field(default_factory=dict[str, PipelineFunction])


@dataclass
class StoreAndForwardInfo:
    """
    Configuration for the Store and Forward mechanism.

    Attributes:
        Enabled (bool): Indicates whether the Store and Forward capability enabled or disabled.
        RetryInterval (str): Indicates the duration of time to wait before retries, aka Forward.
        MaxRetryCount (int): The maximum number of retry attempts for forwarding a message.
    """
    Enabled: bool = field(default_factory=bool)
    RetryInterval: str = field(default_factory=str)
    MaxRetryCount: int = field(default_factory=int)


@dataclass
class InsecureSecretsInfo:
    """
    This section defines a block of insecure secrets for some service specific needs.

    Attributes:
        SecretName (str): The name of the secret in the secret store.
        SecretData (dict[str, str]): Key-value pairs representing the secret data.
    """
    SecretName: str = field(default_factory=str)
    SecretData: dict[str, str] = field(default_factory=dict[str, str])


@dataclass
class TelemetryInfo:
    """
    Configuration for a service's metrics collection.

    Attributes:
        Interval (str): The interval in seconds at which to report the metrics currently being
         collected and enabled.
        Metrics (dict[str, bool]): Key-value pairs indicating which metrics are enabled
         for reporting.
        Tags (dict[str, str]): Key-value pairs representing tags to be added to telemetry data.
    """
    Interval: str = field(default_factory=str)
    Metrics: dict[str, bool] = field(default_factory=dict[str, bool])
    Tags: Optional[dict[str, str]] = field(default_factory=dict[str, str])

    def get_enabled_metric_name(self, metric_name: str) -> tuple[str, bool]:
        """
        Returns the matching configured Metric name and if it is enabled.
        """
        # Match on config metric name as prefix of passed in metric name
        # (service's metric item name) This allows for a class of Metrics to be enabled with one
        # configured metric name. App SDK uses this for PipelineMetrics by appending the
        # pipeline ID to the name of the metric(s) it is collecting for multiple function
        # pipelines.
        for config_metric_name, enabled in self.Metrics.items():
            if not metric_name.startswith(config_metric_name):
                continue
            return config_metric_name, enabled
        return "", False


@dataclass
class WritableInfo:
    """
    Entries in the Writable section of the configuration can be changed on the fly while the
    service is running if the service is running with the -cp/--configProvider flag

    Attributes:
        LogLevel (str): The logging level.
        Pipeline (PipelineInfo): Configuration for the processing pipeline.
        StoreAndForward (StoreAndForwardInfo): Configuration for the store and forward mechanism.
        InsecureSecrets (InsecureSecretsInfo): Configuration for insecure secrets.
        Telemetry (TelemetryInfo): Configuration for telemetry.
    """
    LogLevel: str = field(default_factory=str)
    Pipeline: PipelineInfo = field(default_factory=PipelineInfo)
    StoreAndForward: StoreAndForwardInfo = field(default=StoreAndForwardInfo())
    InsecureSecrets: dict[str, InsecureSecretsInfo] = field(default_factory=dict[str, InsecureSecretsInfo])
    Telemetry: TelemetryInfo = field(default_factory=TelemetryInfo)


@dataclass
class RegistryInfo:
    """
    Configuration for service registry.

    Attributes:
        Host (str): Registry host name.
        Port (int): Registry port number.
        Type (str): Registry implementation type.
    """
    Host: str = field(default_factory=str)
    Port: int = field(default_factory=int)
    Type: str = field(default_factory=str)


@dataclass
class CORSConfigurationInfo:
    """
    The settings of controlling CORS http headers.

    Attributes:
        EnableCORS (bool): Enable or disable CORS support.
        CORSAllowCredentials (bool): The value of Access-Control-Allow-Credentials http header.
        CORSAllowedOrigin (str): The value of Access-Control-Allow-Origin http header.
        CORSAllowedMethods (str): The value of Access-Control-Allow-Methods http header.
        CORSAllowedHeaders (str): The value of Access-Control-Allow-Headers http header.
        CORSExposeHeaders (str): The value of Access-Control-Expose-Headers http header.
        CORSMaxAge (int): The value of Access-Control-Max-Age http header.
    """
    EnableCORS: bool = field(default_factory=bool)
    CORSAllowCredentials: bool = field(default_factory=bool)
    CORSAllowedOrigin: str = field(default_factory=str)
    CORSAllowedMethods: str = field(default_factory=str)
    CORSAllowedHeaders: str = field(default_factory=str)
    CORSExposeHeaders: str = field(default_factory=str)
    CORSMaxAge: int = field(default_factory=int)


@dataclass
class ServiceInfo:  # pylint: disable=too-many-instance-attributes
    """
    General service configuration.

    Attributes:
        HealthCheckInterval (str): The interval in seconds at which the registry service will
         conduct a health check of this service.
        Host (str): The host name of the service.
        Port (int): The port number on which the service listens.
        ServerBindAddr (str): The interface on which the service's REST server should listen.
        StartupMsg (str): Message logged when service completes bootstrap start-up.
        MaxResultCount (int): Read data limit per invocation. Application and Device services do
         not implement this setting.
        MaxRequestSize (int): Defines the maximum size of http request body in kilobytes.
        RequestTimeout (str): Specifies a timeout duration for handling requests.
        EnableNameFieldEscape (bool): The name field escape could allow the system to use
         special or Chinese characters in the different name fields, including device, profile,
         and so on.
        CORSConfiguration (CORSConfigurationInfo): CORS configuration.
        SecurityOptions (dict[str, str]): SecurityOptions is a key/value map, used for configuring
         hosted services. Currently used for zero trust but could be for other options additional
         security related configuration.
    """
    HealthCheckInterval: str = field(default_factory=str)
    Host: str = field(default_factory=str)
    Port: int = field(default_factory=int)
    ServerBindAddr: str = field(default_factory=str)
    StartupMsg: str = field(default_factory=str)
    MaxResultCount: int = field(default_factory=int)
    MaxRequestSize: int = field(default_factory=int)
    RequestTimeout: str = field(default_factory=str)
    EnableNameFieldEscape: bool = field(default_factory=bool)
    CORSConfiguration: CORSConfigurationInfo = field(default_factory=CORSConfigurationInfo)
    SecurityOptions: dict[str, str] = field(default_factory=dict[str, str])


@dataclass
class HttpConfig:
    """
    HTTP server configuration.

    Attributes:
        Protocol (str): The protocol used by the server.
        SecretName (str): The name in the secret store for the HTTPS cert and key.
        HTTPSCertName (str): The name of the HTTPS cert in the secret store.
        HTTPSKeyName (str): The name of the HTTPS key in the secret store.
    """
    Protocol: str = field(default_factory=str)
    SecretName: str = field(default_factory=str)
    HTTPSCertName: str = field(default_factory=str)
    HTTPSKeyName: str = field(default_factory=str)


@dataclass
class MessageBusInfo:  # pylint: disable=too-many-instance-attributes
    """
    Configuration for the message bus.

    Attributes:
        Disabled (bool): Indicates if the use of the EdgeX MessageBus is disabled.
        Type (str): The type of message bus (e.g., 'mqtt', 'redis').
        Protocol (str): The protocol used by the message bus.
        Host (str): The host name or IP address of the message bus.
        Port (int): The port number of the message bus.
        AuthMode (str): The authentication mode for the message bus.
        SecretName (str): The name of the secret in the SecretStore that contains the
         Auth Credentials.
        BaseTopicPrefix (str): The base topic prefix that all topics start with.
        Optional (dict[str, str]): Provides additional configuration properties which do not fit
         within the existing field.
    """
    Disabled: bool = field(default_factory=bool)
    Type: str = field(default_factory=str)
    Protocol: str = field(default_factory=str)
    Host: str = field(default_factory=str)
    Port: int = field(default_factory=int)
    AuthMode: str = field(default_factory=str)
    SecretName: str = field(default_factory=str)
    BaseTopicPrefix: str = field(default_factory=str)
    Optional: dict[str, str] = field(default_factory=dict[str, str])

    def get_base_topic_prefix(self) -> str:
        """
        Returns the base topic prefix.
        """
        if len(self.BaseTopicPrefix) == 0:
            return DEFAULT_BASE_TOPIC
        return self.BaseTopicPrefix


@dataclass
class WillConfig:
    """
    Configuration for the Last Will message in MQTT.

    Attributes:
        Enabled (bool): Enables Last Will capability.
        Payload (str): Will message to be sent to the Will Topic.
        Qos (bytes): QOS level for Will Topic.
        Retained (bool): Retained setting for Will Topic.
        Topic (str): Topic to publish the Last Will Payload when service disconnects from
         MQTT Broker.
    """
    Enabled: bool = field(default_factory=bool)
    Payload: str = field(default_factory=str)
    Qos: bytes = field(default_factory=lambda: b'')
    Retained: bool = field(default_factory=bool)
    Topic: str = field(default_factory=str)


@dataclass
class ExternalMqttConfig:  # pylint: disable=too-many-instance-attributes
    """
    Configuration for an external MQTT broker.

    Attributes:
        Url (str): The URL of the MQTT broker.
        ClientId (str): The client ID for the MQTT connection.
        ConnectTimeout (str): Time duration indicating how long to wait before
         timing out broker connection.
        AutoReconnect (bool): Indicates whether to retry connection if disconnected.
        KeepAlive (int): Seconds between client ping when no active data flowing to avoid client
         being disconnected. Must be greater than 2.
        Qos (str): Quality of Service.
        Retain (bool): Whether messages are retained by default.
        SkipCertVerify (bool): Indicates if the certificate verification should be skipped
        SecretName (str): The name of the secret in secret provider to retrieve your secrets.
        AuthMode (str): The authentication mode.
        RetryDuration (int): Indicates how long (in seconds) to wait timing out on the
         MQTT client creation.
        RetryInterval (int): Indicates the time (in seconds) that will be waited between attempts
         to create MQTT client.
        Will (WillConfig): Configuration for the Last Will message.
    """
    Url: str = field(default_factory=str)
    ClientId: str = field(default_factory=str)
    ConnectTimeout: str = field(default_factory=str)
    AutoReconnect: bool = field(default_factory=bool)
    KeepAlive: int = field(default_factory=int)
    Qos: str = field(default_factory=str)
    Retain: bool = field(default_factory=bool)
    SkipCertVerify: bool = field(default_factory=bool)
    SecretName: str = field(default_factory=str)
    AuthMode: str = field(default_factory=str)
    RetryDuration: int = field(default_factory=int)
    RetryInterval: int = field(default_factory=int)
    Will: WillConfig = field(default_factory=WillConfig)


@dataclass
class TriggerInfo:
    """
    Configuration for triggers, which initiate actions in response to events.

    Attributes:
        Type (str): The type of trigger.
        SubscribeTopics (str): Topic(s) to subscribe to. This is a comma separated list of topics.
         Supports filtering by subscribe topics.
        PublishTopic (str): Indicates the topic in which to publish the function pipeline response
         data, if any. Supports dynamic topic places holders.
        ExternalMqtt (ExternalMqttConfig): Configuration for an external MQTT trigger, if used.
    """
    Type: str = field(default_factory=str)
    SubscribeTopics: str = field(default_factory=str)
    PublishTopic: str = field(default_factory=str)
    ExternalMqtt: ExternalMqttConfig = field(default_factory=ExternalMqttConfig)


@dataclass
class ClientInfo:
    """
    Configuration for external clients that interact with the service.

    Attributes:
        Host (str): The host name of the client.
        Port (int): The port number of the client.
        Protocol (str): The protocol used for communication with the client.
        UseMessageBus (bool): Whether to use the EdgeX message bus for communication with
         the client.
        SecurityOptions (dict[str, str]): Security-related options for the client.
    """
    Host: str = field(default_factory=str)
    Port: int = field(default_factory=int)
    Protocol: str = field(default_factory=str)
    UseMessageBus: bool = field(default_factory=bool)
    SecurityOptions: dict[str, str] = field(default_factory=dict[str, str])

    def url(self) -> str:
        """
        Returns the URL of the client.
        """
        return f"{self.Protocol}://{self.Host}:{self.Port}"


@dataclass
class DatabaseInfo:
    """
    Configuration for the database used by the service.

    Attributes:
        Type (str): The type of database.
        Timeout (str): The timeout for database connections.
        Host (str): The host name of the database.
        Port (int): The port number of the database.
        Name (str): Database or document store name (Specific to the service).
    """
    Type: str = field(default_factory=str)
    Timeout: str = field(default_factory=str)
    Host: str = field(default_factory=str)
    Port: int = field(default_factory=int)
    Name: str = field(default_factory=str)


@dataclass
class Credentials:
    """ Credentials encapsulates username-password attributes. """
    Username: str
    Password: str


def empty_writable_ptr() -> WritableInfo:
    """
    Returns an empty WritableInfo object.
    """
    return WritableInfo()


@dataclass
class ConfigurationStruct:  # pylint: disable=too-many-instance-attributes
    """
    The main configuration structure for the application, containing all configurable components.

    Attributes:
        Writable (WritableInfo): Configuration that can be modified at runtime.
        Registry (RegistryInfo): Configuration for service registry.
        Service (ServiceInfo): General service configuration.
        HttpServer (HttpConfig): HTTP server configuration.
        MessageBus (MessageBusInfo): Configuration for the EdgeX message bus.
        Trigger (TriggerInfo): Configuration for the Function Pipeline Trigger.
        ApplicationSettings (dict[str, str]): Custom configuration for the Application service.
        Clients (dict[str, ClientInfo]): Configuration for the dependent EdgeX clients.
        Database (DatabaseInfo): Configuration for the database.
    """
    Writable: WritableInfo = field(default_factory=WritableInfo)
    Registry: RegistryInfo = field(default_factory=RegistryInfo)
    Service: ServiceInfo = field(default_factory=ServiceInfo)
    HttpServer: HttpConfig = field(default_factory=HttpConfig)
    MessageBus: MessageBusInfo = field(default_factory=MessageBusInfo)
    Trigger: TriggerInfo = field(default_factory=TriggerInfo)
    ApplicationSettings: dict[str, str] = field(default_factory=dict[str, str])
    Clients: dict[str, ClientInfo] = field(default_factory=dict[str, ClientInfo])
    Database: DatabaseInfo = field(default_factory=DatabaseInfo)
