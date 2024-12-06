# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from src.app_functions_sdk_py.contracts.dtos.tags import Tags


class TestTags(unittest.TestCase):
    def setUp(self):
        self.tags = Tags({"tag1": "value1", "tag2": "value2"})

    def test_tags_creation(self):
        self.assertEqual(self.tags, {"tag1": "value1", "tag2": "value2"})


if __name__ == '__main__':
    unittest.main()
