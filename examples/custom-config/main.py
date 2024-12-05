# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
import asyncio
import copy
import os
from dataclasses import dataclass
from typing import Any

from app_functions_sdk_py.factory import new_app_service


@dataclass
class HostInfo:
    Host: str = ""
    Port: int = 0
    Protocol: str = ""


@dataclass
class AppCustomConfig:
    ResourceNames: str = ""
    SomeValue: int = 0
    SomeService: HostInfo = HostInfo()

    def validate(self):
        if self.SomeValue <= 0:
            raise ValueError("SomeValue must be greater than 0")

        if self.SomeService == HostInfo():
            raise ValueError("SomeService is not set")


@dataclass
class ServiceConfig:
    AppCustom: AppCustomConfig = AppCustomConfig()


class MyApp:
    def __init__(self):
        self.service_key = "app-new-service"
        self.service = None
        self.service_config = None
        self.previous_config = None

    def process_config_updates(self, updated_config: Any):
        if not isinstance(updated_config, AppCustomConfig):
            self.service.logger().error("unable to process config updates: Cannot cast raw config "
                                        "to type 'AppCustomConfig'")
            return

        if self.previous_config is None:
            self.previous_config = copy.deepcopy(self.service_config.AppCustom)
        self.service_config.AppCustom = updated_config

        if self.previous_config == updated_config:
            self.service.logger().info("No changes detected")
            return

        if self.previous_config.SomeValue != updated_config.SomeValue:
            self.service.logger().info(f"AppCustom.SomeValue changed to: {updated_config.SomeValue}")

        if self.previous_config.ResourceNames != updated_config.ResourceNames:
            self.service.logger().info(f"AppCustom.ResourceNames changed to: {updated_config.ResourceNames}")

        if self.previous_config.SomeService != updated_config.SomeService:
            self.service.logger().info(f"AppCustom.SomeService changed to: {updated_config.SomeService}")

        self.previous_config = copy.deepcopy(updated_config)

    def create_and_run_service(self) -> int:
        # create a new application service
        service, result = new_app_service(self.service_key)
        self.service = service
        self.service_config = ServiceConfig()

        # TODO: Change to use your service's custom configuration class
        #       or remove if not using custom configuration capability
        try:
            service.load_custom_config(self.service_config, "AppCustom")
        except Exception as e:
            service.logger().error(f"Failed to load custom config: {e}")
            return -1

        # Optionally validate the custom configuration after it is loaded.
        # TODO: remove if you don't have custom configuration or don't need to validate it
        try:
            self.service_config.AppCustom.validate()
        except Exception as e:
            service.logger().error(f"Custom config validation failed: {e}")
            return -1

        try:
            service.listen_for_custom_config_changes(self.service_config.AppCustom, "AppCustom", self.process_config_updates)
        except Exception as e:
            service.logger().error(f"Failed to listen for custom config changes: {e}")
            return -1

        # run the service
        asyncio.run(service.run())
        return 0


if __name__ == "__main__":
    app = MyApp()
    code = app.create_and_run_service()
    os._exit(code)
