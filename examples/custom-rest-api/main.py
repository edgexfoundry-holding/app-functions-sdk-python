# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
import asyncio

from app_functions_sdk_py.factory import new_app_service

from fastapi import Request, Response


class MyApp:
    def __init__(self):
        self.service_key = "app-new-service"

    def create_and_run_service(self):
        # create a new application service
        service, result = new_app_service(self.service_key)

        def my_handler(req: Request, resp: Response):
            service.logger().info("Hello from my_handler")
            resp.status_code = 200
            return {"message": "hello"}

        service.add_custom_route("/myroute", False, my_handler, methods=["GET"])

        # run the service
        asyncio.run(service.run())


if __name__ == "__main__":
    app = MyApp()
    app.create_and_run_service()
