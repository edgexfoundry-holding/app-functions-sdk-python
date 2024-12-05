#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import unittest

from src.app_functions_sdk_py.bootstrap.di.container import Container, Get

_service_name = "service"


class TestContainer(unittest.TestCase):
    def test_get_unknown_service(self):
        container = Container()
        result = container.get("unknownService")
        self.assertIsNone(result)

    def test_get_known_service_returns_expected_constructor_result(self):
        class ServiceType:
            pass
        service = ServiceType()

        def service_constructor(get: Get):
            return service
        container = Container({_service_name: service_constructor})
        result = container.get(_service_name)
        self.assertEqual(service, result)

    def test_get_known_service_implements_singleton(self):
        class ServiceType:
            def __init__(self, value: int):
                self.value = value
        instance_count = 0

        def service_constructor(get: Get):
            nonlocal instance_count
            instance_count += 1
            return ServiceType(instance_count)

        container = Container({_service_name: service_constructor})
        first = container.get(_service_name)
        second = container.get(_service_name)
        self.assertEqual(first, second)

    def test_update_of_non_existent_service_adds(self):
        class ServiceType:
            pass
        service = ServiceType()

        def service_constructor(get: Get):
            return service
        container = Container()
        container.update({_service_name: service_constructor})
        result = container.get(_service_name)
        self.assertEqual(service, result)

    def test_update_of_existing_service_replaces(self):
        original = "original"
        replacement = "replacement"

        class ServiceType:
            def __init__(self, value):
                self.value = value

        def original_constructor(get: Get):
            return ServiceType(original)
        container = Container({_service_name: original_constructor})

        def replacement_constructor(get: Get):
            return ServiceType(replacement)
        container.update({_service_name: replacement_constructor})

        result = container.get(_service_name)
        self.assertEqual(replacement, result.value)

    def test_get_inside_get_returns_as_expected(self):
        foo_name = "foo"
        bar_name = "bar"

        class Foo:
            def __init__(self, foo_message: str):
                self.foo_message = foo_message

        class Bar:
            def __init__(self, bar_message: str, foo: Foo):
                self.bar_message = bar_message
                self.foo = foo

        container = Container({
            foo_name: lambda get: Foo(foo_message=foo_name),
            bar_name: lambda get: Bar(bar_message=bar_name, foo=get(foo_name))
        })

        result = container.get(bar_name)
        self.assertEqual(bar_name, result.bar_message)
        self.assertIsNotNone(result.foo)
        self.assertEqual(foo_name, result.foo.foo_message)


if __name__ == '__main__':
    unittest.main()
