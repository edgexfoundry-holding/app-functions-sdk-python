# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.app_functions_sdk_py.bootstrap.environment import StartupInfo
from src.app_functions_sdk_py.bootstrap.timer import Timer, new_startup_timer


class TimerTests(unittest.TestCase):

    def test_timer_initializes_correctly(self):
        start_time = datetime.now()
        duration = timedelta(seconds=60)
        interval = timedelta(seconds=10)
        timer = Timer(start_time=start_time, duration=duration, interval=interval)
        self.assertEqual(timer.start_time, start_time)
        self.assertEqual(timer.duration, duration)
        self.assertEqual(timer.interval, interval)

    def test_since_as_string_returns_correct_elapsed_time(self):
        start_time = datetime.now() - timedelta(seconds=30)
        timer = Timer(start_time=start_time, duration=timedelta(minutes=1), interval=timedelta(seconds=10))
        self.assertTrue("0:00:30" in timer.since_as_string())

    def test_remaining_as_string_returns_correct_remaining_time(self):
        start_time = datetime.now() - timedelta(seconds=30)
        timer = Timer(start_time=start_time, duration=timedelta(seconds=60), interval=timedelta(seconds=10))
        self.assertTrue("0:00:30" in timer.remaining_as_string())

    def test_remaining_as_string_returns_zero_when_past_duration(self):
        start_time = datetime.now() - timedelta(seconds=90)
        timer = Timer(start_time=start_time, duration=timedelta(seconds=60), interval=timedelta(seconds=10))
        self.assertEqual("0:00:00", timer.remaining_as_string())

    def test_has_not_elapsed_returns_false_after_duration(self):
        start_time = datetime.now() - timedelta(minutes=2)
        timer = Timer(start_time=start_time, duration=timedelta(minutes=1), interval=timedelta(seconds=10))
        self.assertFalse(timer.has_not_elapsed())

    def test_has_not_elapsed_returns_true_within_duration(self):
        start_time = datetime.now()
        timer = Timer(start_time=start_time, duration=timedelta(minutes=1), interval=timedelta(seconds=10))
        self.assertTrue(timer.has_not_elapsed())

    @patch('src.app_functions_sdk_py.bootstrap.timer.time.sleep')
    def test_sleep_for_interval_sleeps_for_correct_amount_of_time(self, mock_sleep):
        timer = Timer(start_time=datetime.now(), duration=timedelta(minutes=1), interval=timedelta(seconds=10))
        timer.sleep_for_interval()
        mock_sleep.assert_called_once_with(10)

    @patch('src.app_functions_sdk_py.bootstrap.timer.environment.get_startup_info')
    def test_new_startup_timer_creates_timer_with_correct_settings(self, mock_get_startup_info):
        mock_get_startup_info.return_value = StartupInfo(duration=60, interval=10)
        logger = MagicMock()
        timer = new_startup_timer(logger)
        self.assertEqual(timer.duration, timedelta(seconds=60))
        self.assertEqual(timer.interval, timedelta(seconds=10))


if __name__ == '__main__':
    unittest.main()
