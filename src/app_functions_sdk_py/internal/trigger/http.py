#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides the `HttpTrigger` class, which implements the `Trigger` abstract class for
allowing the pipeline to be triggered by a RESTful POST call to
http://[host]:[port]/api/v3/trigger/.

Classes:
    - HttpTrigger: Handles HTTP requests and processes messages using the provided service binding
    and message processor.
"""

import threading
from http import HTTPStatus
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

from .messageprocessor import MessageProcessor
from .servicebinding import ServiceBinding
from ..constants import API_TRIGGER_ROUTE
from ...contracts.clients.utils.request import HTTPMethod
from ...contracts.common.constants import CONTENT_TYPE, CORRELATION_HEADER
from ...interfaces import Trigger, Deferred, MessageEnvelope
from ...sync.waitgroup import WaitGroup


class HttpTrigger(Trigger):
    """
    Represents a HTTP trigger.
    """
    def __init__(self, service_binding: ServiceBinding,
                 message_processor: MessageProcessor, router: FastAPI):
        self.service_binding = service_binding
        self.message_processor = message_processor
        self.router = router
        self.done = None
        self.waiting_group = None

    def initialize(self, ctx_done: threading.Event, app_wg: WaitGroup) -> Optional[Deferred]:
        """
        Initializes the Trigger for logging and REST route.
        """
        lc = self.service_binding.logger()

        lc.info("Initializing HTTP trigger")
        self.router.add_api_route(API_TRIGGER_ROUTE, self.request_handler,
                                  methods=[HTTPMethod.POST.value])
        lc.info("HTTP trigger initialized")

    async def request_handler(self, request: Request) -> Response:
        """
        Handles incoming HTTP requests and processes the message using the provided service binding
        and message processor.
        """
        lc = self.service_binding.logger()

        body = await request.body()

        lc.debug(f"Request Body read, byte count: {len(body)}")

        content_type = request.headers.get(CONTENT_TYPE, "")
        correlation_id = request.headers.get(CORRELATION_HEADER, "")

        lc.trace(f"Received message from http, X-Correlation-ID: {correlation_id}")
        lc.debug(f"Received message from http, Content-Type: {content_type}")

        envelope = MessageEnvelope(
            correlationID=correlation_id,
            contentType=content_type,
            payload=body)

        app_context = self.service_binding.build_context(envelope)

        default_pipeline = self.service_binding.get_default_pipeline()
        try:
            target_data = self.service_binding.decode_message(app_context, envelope)
        except (ValueError, TypeError) as e:
            return PlainTextResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                     content=f"failed to decode message: {e}")

        message_error = self.service_binding.process_message(
            app_context, target_data, default_pipeline)
        if message_error is not None:
            return PlainTextResponse(status_code=message_error.code,
                                     content=f"failed to process message: {message_error.err}")

        response_content_type = app_context.response_content_type()
        response_data = app_context.response_data()

        response = Response(content=response_data)
        if response_content_type is not None and len(response_content_type) > 0:
            response.headers[CONTENT_TYPE] = response_content_type
        if response_data:
            lc.trace(f"Sent http response message, X-Correlation-ID: {correlation_id}")

        return response
