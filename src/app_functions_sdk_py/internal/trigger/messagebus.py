# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module defines the `MessageBusTrigger` class, which represents a trigger for the message bus
in the application.

Classes:
    MessageBusTrigger: Handles the initialization and processing of messages from the message bus,
                       subscribing to topics, and managing the message processing pipeline.

Usage:
    The `MessageBusTrigger` class is used to set up and manage the message bus trigger, including
    subscribing to topics, processing incoming messages, and handling responses.

Example:
    service_binding = DefaultTriggerServiceBinding(logger, config, messaging_client, runtime)
    message_processor = DefaultTriggerMessageProcessor(service_binding)
    trigger = MessageBusTrigger(service_binding, message_processor)
    trigger.initialize(ctx_done, app_wg)
"""
import queue
import threading
from typing import Optional

from ...bootstrap.container.messaging import messaging_client_from
from ...bootstrap.di.container import Container
from ...contracts.common.constants import CONTENT_TYPE_JSON, CORRELATION_HEADER
from .messageprocessor import MessageProcessor
from .servicebinding import ServiceBinding
from ...constants import TOPIC_LEVEL_SEPERATOR, SPILT_COMMA
from ...interfaces import AppFunctionContext, FunctionPipeline, Deferred, Trigger
from ...interfaces.messaging import TopicMessageQueue, MessageEnvelope
from ...sync.waitgroup import WaitGroup
from ...utils.strconv import join_str


# pylint: disable=too-many-instance-attributes
class MessageBusTrigger(Trigger):
    """
    Represents a message bus trigger.
    """

    def __init__(self, service_binding: ServiceBinding, message_processor: MessageProcessor,
                 dic: Container):
        self.service_binding = service_binding
        self.message_processor = message_processor
        self.messaging_client = None
        self.topic_queues = list[TopicMessageQueue]()
        self.publish_topic = None
        self.done = None
        self.waiting_group = None
        self.dic = dic

    def initialize(self, ctx_done: threading.Event, app_wg: WaitGroup) -> Optional[Deferred]:
        """
        initialize the message bus trigger.
        """
        # pylint: disable=broad-exception-caught,too-many-locals,too-many-statements
        logger = self.service_binding.logger()
        config = self.service_binding.config()

        logger.info(f"Initializing EdgeX Message Bus Trigger for {config.MessageBus.Type}")

        self.messaging_client = messaging_client_from(self.dic.get)
        if self.messaging_client is None:
            raise ValueError("MessageBusTrigger requires a messaging client from the service "
                             "binding")

        if ctx_done is not None:
            self.done = ctx_done
        else:
            logger.error("MessageBus Trigger: Context done event is None")
            raise ValueError("MessageBus Trigger: Context done event is None")

        if app_wg is not None:
            self.waiting_group = app_wg
        else:
            logger.error("MessageBus Trigger: waiting group is None")
            raise ValueError("MessageBus Trigger: waiting group is None")

        subscribed_topics = config.Trigger.SubscribeTopics.strip()
        if not subscribed_topics:
            raise ValueError("SubscribeTopics cannot be empty in the configuration, must contain "
                             "one or more topic separated by commas")

        topics = subscribed_topics.split(SPILT_COMMA)

        # parse the topics and create a queue for each topic
        for topic in topics:
            topic = join_str([config.MessageBus.BaseTopicPrefix, topic],
                             TOPIC_LEVEL_SEPERATOR)
            topic_queue = TopicMessageQueue(topic, queue.Queue())
            self.topic_queues.append(topic_queue)
            logger.info(f"subscribing to topic '{topic}'")

        self.publish_topic = config.Trigger.PublishTopic.strip()
        if len(self.publish_topic) > 0:
            self.publish_topic = (
                join_str([config.MessageBus.BaseTopicPrefix, self.publish_topic],
                         TOPIC_LEVEL_SEPERATOR))
            logger.info(f"Publishing to topic: '{self.publish_topic}'")
        else:
            logger.info("Publish topic not set Trigger.  "
                        "Response data, if set, will not be published")

        def process_message(trigger_topic: TopicMessageQueue):
            logger.info(f"waiting for messages from the MessageBus on the topic: "
                        f"{trigger_topic.topic}")
            while True:
                # self.done will be set to true when the app service is shutting down or terminated
                if self.done.is_set():
                    self.waiting_group.done()
                    break
                message = trigger_topic.message_queue.get()
                if message is None:
                    continue
                app_context = self.service_binding.build_context(message)
                try:
                    self.message_processor.message_received(app_context, message,
                                                            self.response_handler)
                except Exception as e:
                    logger.error(f"MessageBus Trigger: Failed to process message on pipeline "
                                 f"received from topic {trigger_topic.topic}: {e}")

        # spawn threads to process the message for each individual subscribe topics
        for topic in self.topic_queues:
            self.waiting_group.add(1)
            threading.Thread(target=process_message, args=(topic,)).start()

        # create a message queue to handle error messages, note that the error message is expected
        # in str type, so ensure only put str error message into message_error_queue
        message_error_queue = queue.Queue()
        self.run_error_message_handler(message_error_queue)
        self.messaging_client.subscribe(self.topic_queues, message_error_queue)

        def deferred():
            self.messaging_client.disconnect()

        return deferred

    def run_error_message_handler(self, message_error_queue: queue.Queue):
        """
        run_error_message_handler spawn a thread to subscribe messages from message_error_queue
        """
        if message_error_queue is None:
            return

        logger = self.service_binding.logger()

        def process_message_error():
            logger.info("waiting for messages from the MessageBus on the error topic")
            while True:
                # self.done will be set to true when the app service is shutting down or terminated
                if self.done.is_set():
                    self.waiting_group.done()
                    break
                message = message_error_queue.get()
                if message is None:
                    continue
                logger.info(f"MessageBus Trigger: Received error message: {message}")
                self.message_processor.received_invalid_message()

        self.waiting_group.add(1)
        threading.Thread(target=process_message_error).start()

    def response_handler(self, ctx: AppFunctionContext, pipeline: FunctionPipeline):
        """
        response_handler provides a handler for the pipeline response
        """
        # pylint: disable=broad-exception-caught
        if ctx.response_data() is not None:
            publish_topic = ctx.apply_values(self.publish_topic)
            content_type = CONTENT_TYPE_JSON
            if ctx.response_content_type() is not None:
                content_type = ctx.response_content_type()
            message_envelope = MessageEnvelope(correlationID=ctx.correlation_id(),
                                               payload=ctx.response_data(),
                                               contentType=content_type)
            try:
                self.messaging_client.publish(message_envelope, publish_topic)
            except Exception as e:
                self.service_binding.logger().error(f"MessageBus trigger: Could not publish to "
                                                    f"topic '{publish_topic}' for pipeline "
                                                    f"'{pipeline.id}': {e}")
                return
            self.service_binding.logger().debug(f"MessageBus trigger: published response message "
                                                f"for pipeline '{pipeline.id}' on topic "
                                                f"'{publish_topic}' with {len(ctx.response_data())}"
                                                f" bytes")
            self.service_binding.logger().trace(f"MessageBus trigger published message: "
                                                f"{CORRELATION_HEADER}={ctx.correlation_id()}")
