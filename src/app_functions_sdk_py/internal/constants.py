#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
Constants for the App Functions SDK.
"""

from ..contracts.common.constants import API_BASE

API_TRIGGER_ROUTE = API_BASE + "/trigger"

# Common Application Service Metrics constants
MESSAGES_RECEIVED_NAME = "MessagesReceived"
INVALID_MESSAGES_RECEIVED_NAME = "InvalidMessagesReceived"
PIPELINE_ID_TXT = "{PipelineId}"
PIPELINE_MESSAGES_PROCESSED_NAME = "PipelineMessagesProcessed-" + PIPELINE_ID_TXT
PIPELINE_MESSAGE_PROCESSING_TIME_NAME = "PipelineMessageProcessingTime-" + PIPELINE_ID_TXT
PIPELINE_PROCESSING_ERRORS_NAME = "PipelineProcessingErrors-" + PIPELINE_ID_TXT
HTTP_EXPORT_SIZE_NAME = "HttpExportSize"
HTTP_EXPORT_ERRORS_NAME = "HttpExportErrors"
MQTT_EXPORT_SIZE_NAME = "MqttExportSize"
MQTT_EXPORT_ERRORS_NAME = "MqttExportErrors"
STORE_FORWARD_QUEUE_SIZE_NAME = "StoreForwardQueueSize"

METRICS_RESERVOIR_SIZE = 1028  # The default Metrics Sample Reservoir size
