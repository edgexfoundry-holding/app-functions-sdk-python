# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module defines the `MessageProcessor` abstract base class, which provides an interface for
processing messages within the application.

Classes:
    MessageProcessor: An abstract base class that defines the interface for a message processor,
                      including methods for handling received messages and invalid messages.

Usage:
    This class should be subclassed to create specific message processors that implement the
    abstract methods defined in the `MessageProcessor` class.

Example:
    class MyMessageProcessor(MessageProcessor):
        def message_received(self, ctx: AppFunctionContext, envelope: MessageEnvelope,
                             output_handler: PipelineResponseHandler):
            # Implementation here
            pass

        def received_invalid_message(self):
            # Implementation here
            pass
"""
from abc import ABC, abstractmethod
from typing import Callable

from ...interfaces import FunctionPipeline, AppFunctionContext
from ...interfaces.messaging import MessageEnvelope

PipelineResponseHandler = Callable[[AppFunctionContext, FunctionPipeline], None]


class MessageProcessor(ABC):
    """
    An abstract base class that defines the interface for a message processor.
    """

    @abstractmethod
    def message_received(self, ctx: AppFunctionContext,
                         envelope: MessageEnvelope,
                         output_handler: PipelineResponseHandler):
        """
        message_received provides runtime orchestration to pass the envelope to configured
        pipeline(s)
        """

    @abstractmethod
    def received_invalid_message(self):
        """
        ReceivedInvalidMessage is called when an invalid message is received so the metrics counter
        can be incremented.
        """
