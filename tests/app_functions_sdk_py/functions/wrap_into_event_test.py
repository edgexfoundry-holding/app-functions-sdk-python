#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import unittest
import uuid
from typing import Any
from unittest.mock import Mock

from src.app_functions_sdk_py.bootstrap.container.logging import LoggingClientInterfaceName
from src.app_functions_sdk_py.bootstrap.di.container import Container
from src.app_functions_sdk_py.contracts.common import constants
from src.app_functions_sdk_py.utils.strconv import parse_bool
from src.app_functions_sdk_py.functions import wrap_into_event
from src.app_functions_sdk_py.contracts.clients.logger import EdgeXLogger, DEBUG
from src.app_functions_sdk_py.functions.configurable import Configurable
from src.app_functions_sdk_py.functions.context import Context


class TestWrapIntoEvent(unittest.TestCase):

	def setUp(self):
		self.logger = EdgeXLogger('test_service', DEBUG)
		self.dic = Container()
		self.dic.update({
			LoggingClientInterfaceName: lambda get: self.logger
		})
		self.ctx = Context(str(uuid.uuid4()), self.dic, "")

	def test_configurable(self):
		configurable = Configurable(logger=self.ctx.logger(), sp=Mock())

		profile_name = "MyProfile"
		device_name = "MyDevice"
		resource_name = "MyResource"
		simple_value_type = "int64"
		binary_value_type = "binary"
		object_value_type = "object"
		bad_value_type = "bogus"
		media_type = "application/mxl"
		empty_media_type = ""

		class TestData:
			def __init__(
					self,
					name: str, profile_name: str, device_name: str,
					resource_name: str, value_type: str,
					media_type: str, expect_none: bool):
				self.name = name
				self.profile_name = profile_name
				self.device_name = device_name
				self.resource_name = resource_name
				self.value_type = value_type
				self.media_type = media_type
				self.expect_none = expect_none

		tests = [
			TestData("Valid simple", profile_name, device_name, resource_name, simple_value_type, "", False),
			TestData("Invalid simple - missing profile", "", device_name, resource_name, simple_value_type, "", True),
			TestData("Invalid simple - missing device", profile_name, "", resource_name, simple_value_type, "", True),
			TestData("Invalid simple - missing resource", profile_name, device_name, "", simple_value_type, "", True),
			TestData("Invalid simple - missing value type", profile_name, device_name, resource_name, "", "", True),
			TestData("Invalid - bad value type", profile_name, device_name, resource_name, bad_value_type, "", True),
			TestData("Valid binary", profile_name, device_name, resource_name, binary_value_type, media_type, False),
			TestData("Invalid binary - empty MediaType", profile_name, device_name, resource_name, binary_value_type, empty_media_type, True),
			TestData("Invalid binary - missing MediaType", profile_name, device_name, resource_name, binary_value_type, "", True),
			TestData("Valid object", profile_name, device_name, resource_name, object_value_type, "", False),
		]

		for test_case in tests:
			with self.subTest(msg=test_case.name):
				params = {}
				if len(test_case.profile_name) > 0:
					params[wrap_into_event.PROFILE_NAME] = test_case.profile_name
				if len(test_case.device_name) > 0:
					params[wrap_into_event.DEVICE_NAME] = test_case.device_name
				if len(test_case.resource_name) > 0:
					params[wrap_into_event.RESOURCE_NAME] = test_case.resource_name
				if len(test_case.value_type) > 0:
					params[wrap_into_event.VALUE_TYPE] = test_case.value_type
				if len(test_case.media_type) > 0:
					params[wrap_into_event.MEDIA_TYPE] = test_case.media_type

				transform = configurable.wrap_into_event(params)
				self.assertEqual(test_case.expect_none, transform is None)

	def test_wrap(self):
		class TestObject:
			def __init__(self, my_int: int, my_str: str):
				self.my_int = my_int
				self.my_str = my_str
		obj = TestObject(3, "hello world")

		class TestData:
			def __init__(
					self,
					name: str, profile_name: str, device_name: str,
					resource_name: str, value_type: str,
					media_type: str, data: Any):
				self.name = name
				self.profile_name = profile_name
				self.device_name = device_name
				self.resource_name = resource_name
				self.value_type = value_type
				self.media_type = media_type
				self.data= data

		tests = [
			TestData("Successful Binary Reading", "MyProfile", "MyDevice", "BinaryEvent", constants.VALUE_TYPE_BINARY, "stuff", True),
			TestData("Successful Object Reading", "MyProfile", "MyDevice", "ObjectEvent", constants.VALUE_TYPE_OBJECT, "", obj),
			TestData("Successful Simple Reading", "MyProfile", "MyDevice", "ObjectEvent", constants.VALUE_TYPE_STRING, "", "hello there"),
		]

		for test in tests:
			with self.subTest(msg=test.name):
				match test.value_type:
					case constants.VALUE_TYPE_BINARY:
						transform = wrap_into_event.new_event_wrapper_binary_reading(
							test.profile_name, test.device_name, test.resource_name, test.media_type)
					case constants.VALUE_TYPE_OBJECT:
						transform = wrap_into_event.new_event_wrapper_object_reading(
							test.profile_name, test.device_name, test.resource_name)
					case _:
						transform = wrap_into_event.new_event_wrapper_simple_reading(
							test.profile_name, test.device_name, test.resource_name, test.media_type)

				actual_bool, event_request = transform.wrap(self.ctx, test.data)

				self.assertTrue(actual_bool)
				self.assertEqual("", self.ctx.response_content_type())

				ctx_values = self.ctx.get_values()
				self.assertEqual(test.profile_name, ctx_values[wrap_into_event.PROFILE_NAME])
				self.assertEqual(test.device_name, ctx_values[wrap_into_event.DEVICE_NAME])
				self.assertEqual(test.resource_name, ctx_values[wrap_into_event.SOURCE_NAME])

				self.assertEqual(test.device_name, event_request.event.deviceName)
				self.assertEqual(test.profile_name, event_request.event.profileName)
				self.assertEqual(test.resource_name, event_request.event.sourceName)
				self.assertEqual(test.device_name, event_request.event.readings[0].deviceName)
				self.assertEqual(test.profile_name, event_request.event.readings[0].profileName)
				self.assertEqual(test.resource_name, event_request.event.readings[0].resourceName)
				match test.value_type:
					case constants.VALUE_TYPE_BINARY:
						value = parse_bool(event_request.event.readings[0].binaryValue.decode())
						self.assertEqual(test.data, value)
					case constants.VALUE_TYPE_OBJECT:
						self.assertEqual(test.data, event_request.event.readings[0].objectValue)
					case _:
						self.assertEqual(test.data, event_request.event.readings[0].value)
