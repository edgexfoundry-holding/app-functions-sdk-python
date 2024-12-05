# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
import asyncio
import threading
from queue import Queue
from typing import Optional, Any, Tuple

from app_functions_sdk_py.factory import new_app_service

from app_functions_sdk_py.constants import TARGET_TYPE_BYTES
from app_functions_sdk_py.interfaces import TriggerConfig, Trigger, Deferred, AppFunctionContext, FunctionPipeline, \
    MessageEnvelope
from app_functions_sdk_py.sync.waitgroup import WaitGroup
from app_functions_sdk_py.utils.helper import coerce_type


class CustomTrigger(Trigger):
    def __init__(self, tc: TriggerConfig):
        self.tc = tc

    def initialize(self, ctx_done: threading.Event, app_wg: WaitGroup,
                   background_publish_queue: Queue) -> Optional[Deferred]:

        def loop():
            while not ctx_done.is_set():
                ctx_done.wait(3)  # wait for 3 seconds

                event = MessageEnvelope(
                    payload="Hello, World!".encode(),
                    received_topic="CustomTrigger"
                )

                try:
                    self.tc.message_received(None, event, self.response_handler)
                except Exception as e:
                    self.tc.logger.error("Error processing message: %s", str(e))

        threading.Thread(target=loop).start()

        return None

    def response_handler(self, ctx: AppFunctionContext, pipeline: FunctionPipeline):
        self.tc.logger.info("Responding to pipeline %s with '%s'", pipeline.id, str(ctx.response_data()))


def PrintDataToConsole(app_context: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
    input_data, err = coerce_type(data)
    if err is not None:
        app_context.logger().error("Failed to coerce data: %s", err)
        return False, None

    app_context.logger().info("Received data: %s", input_data)
    print("Received data: %s", input_data)

    app_context.set_response_data(input_data)
    return True, None


class MyApp:
    def __init__(self):
        self.service_key = "app-new-service"

    def create_and_run_service(self):
        service, result = new_app_service(self.service_key, target_type=TARGET_TYPE_BYTES)
        print(f"service: {service}, result: {result}")
        if not result:
            raise RuntimeError("failed to create a new ApplicationService instance and initialize it.")

        def trigger_factory(tc: TriggerConfig) -> Trigger:
            return CustomTrigger(tc)

        service.register_custom_trigger_factory("CustomTrigger", trigger_factory)

        service.set_default_functions_pipeline([PrintDataToConsole])

        asyncio.run(service.run())


if __name__ == "__main__":
    app = MyApp()
    app.create_and_run_service()
