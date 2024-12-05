#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

import asyncio
from typing import Any, Tuple

from app_functions_sdk_py.factory import new_app_service
from app_functions_sdk_py.interfaces import AppFunctionContext


class Person:
    def __init__(self):
        self.FirstName = ""
        self.LastName = ""


def my_person_function(ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
    ctx.logger().debug("my_person_function executing")
    if data is None:
        return False, ValueError("no data received to my_person_function")
    if not isinstance(data, Person):
        return False, ValueError("data is not of type Person")
    # do something with the data
    ctx.logger().info(f"Person data received: {vars(data)}")
    return True, data


class MyApp:
    def __init__(self):
        self.service_key = "app-new-service"

    def create_and_run_service(self):
        # create a new application service
        service, result = new_app_service(self.service_key, Person())

        service.add_functions_pipeline_for_topics(
            "pipeline1",
            ["events/pipeline1/#"],
            my_person_function
        )

        # run the service
        asyncio.run(service.run())


if __name__ == "__main__":
    app = MyApp()
    app.create_and_run_service()
