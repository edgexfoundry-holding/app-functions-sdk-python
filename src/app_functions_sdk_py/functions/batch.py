# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for Batch
"""
import threading
import time
from datetime import timedelta
from enum import Enum
from queue import Queue
from typing import Tuple, Any, Optional

import isodate
from isodate import ISO8601Error

from ..contracts.common.constants import CORRELATION_HEADER
from ..interfaces import AppFunctionContext
from ..contracts import errors
from ..utils.helper import coerce_type
from ..contracts.dtos.event import Event, unmarshal_event

MODE = "mode"
BATCH_BY_COUNT = "bycount"
BATCH_BY_TIME = "bytime"
BATCH_BY_TIME_COUNT = "bytimecount"
IS_EVENT_DATA = "iseventdata"
MERGE_ON_SEND = "mergeonsend"
BATCH_THRESHOLD = "batchthreshold"
TIME_INTERVAL = "timeinterval"


class BatchMode(Enum):
    # pylint: disable=too-few-public-methods
    """ BatchMode is used to specify the mode value. """
    BATCH_BY_COUNT_ONLY = 0
    BATCH_BY_TIME_ONLY = 1
    BATCH_BY_TIME_AND_COUNT = 2


class AtomicBool:
    # pylint: disable=too-few-public-methods
    """ BatchConfig is used to hold boolean data with mutex lock. """
    def __init__(self):
        self._mutex = threading.Lock()
        self._value = False

    def value(self) -> bool:
        """ return bool value """
        with self._mutex:
            return self._value

    def set(self, v: bool):
        """ set bool value """
        with self._mutex:
            self._value = v


class AtomicBatchData:
    """ BatchConfig is used to hold the batch data """
    def __init__(self):
        self._mutex = threading.Lock()
        self._data = []

    def append(self, to_be_added: bytes) -> list[bytes]:
        """ append batch data """
        with self._mutex:
            self._data.append(to_be_added)
            return self._data.copy()

    def all(self) -> list[bytes]:
        """ return all batch data """
        with self._mutex:
            return self._data.copy()

    def remove_all(self):
        """ remove all batch data """
        with self._mutex:
            self._data.clear()

    def length(self) -> int:
        """ return the length of batch data """
        with self._mutex:
            return len(self._data)


class BatchConfig:
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-positional-arguments
    """ BatchConfig is used to bach the events """
    def __init__(
            self,
            is_event_data: bool = False, merge_on_send: bool = False,
            time_interval: str = "", parsed_duration: timedelta = None,
            batch_threshold: int = 0, batch_mode: BatchMode = BatchMode.BATCH_BY_TIME_AND_COUNT,
            done: Queue = None, done_mutex: threading.Lock = threading.Lock()


    ):
        self.is_event_data = is_event_data
        self.merge_on_send = merge_on_send
        self.time_interval = time_interval
        self.parsed_duration = parsed_duration
        self.batch_threshold = batch_threshold
        self.batch_mode = batch_mode
        self.batch_data = AtomicBatchData()
        self.timer_active = AtomicBool()
        self.done = done
        self.done_mutex = done_mutex

    def batch(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        """ batch the events with the specified mode"""
        if data is None:
            # We didn't receive a result
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"function Batch in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug("Batching Data in pipeline '%s'", ctx.pipeline_id())
        byte_data, err = coerce_type(data)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        # always append data
        self.batch_data.append(byte_data)

        # If its time only or time and count
        if self.batch_mode != BatchMode.BATCH_BY_COUNT_ONLY:
            if not self.timer_active.value():
                self.timer_active.set(True)
                ctx.logger().debug("Timer active in pipeline '%s'", ctx.pipeline_id())
                start = time.perf_counter()
                while True:
                    with self.done_mutex:
                        if self.done.full():
                            self.done.get()
                            ctx.logger().debug(
                                "Batch count has been reached in pipeline '%s'", ctx.pipeline_id())
                            break

                    duration = time.perf_counter() - start
                    if duration > self.parsed_duration.total_seconds():
                        ctx.logger().debug("Timer has elapsed in pipeline '%s'", ctx.pipeline_id())
                        break
                self.timer_active.set(False)
            else:
                if self.batch_mode == BatchMode.BATCH_BY_TIME_ONLY:
                    return False, None

        if self.batch_mode != BatchMode.BATCH_BY_TIME_ONLY:
            # Only want to check the threshold if the timer is running and in TimeAndCount mode
            # OR if we are in CountOnly mode
            if (self.batch_mode == BatchMode.BATCH_BY_COUNT_ONLY or
                    (self.timer_active.value() and
                     self.batch_mode == BatchMode.BATCH_BY_TIME_AND_COUNT)):
                # if we have not reached the threshold,
                # then stop pipeline and continue batching
                if self.batch_data.length() < self.batch_threshold:
                    return False, None
                # if in BatchByCountOnly mode, there are no listeners
                # so this would hang indefinitely
                ctx.logger().debug(
                    "Batch count has been reached the threshold '%s' in pipeline '%s'",
                    self.batch_threshold, ctx.pipeline_id())
                if self.done is not None:
                    with self.done_mutex:
                        self.done.put(True)

        ctx.logger().debug(
            "Forwarding Batched Data in pipeline '%s' (%s=%s)",
            ctx.pipeline_id(), CORRELATION_HEADER, ctx.correlation_id())
        # we've met the threshold, lets clear out the buffer and send it forward in the pipeline
        if self.batch_data.length() > 0:
            copy_of_data = self.batch_data.all()
            result_data = copy_of_data.copy()
            if self.is_event_data:
                ctx.logger().debug("Marshaling batched data to []Event")
                events: list[Event] = []
                for d in copy_of_data:
                    event, err = unmarshal_event(d)
                    if err is not None:
                        return False, errors.new_common_edgex(
                                    errors.ErrKind.SERVER_ERROR,
                                    "unable to unmarshal batched data to slice of Events "
                                    f"in pipeline '{ctx.pipeline_id()}': {err}")

                    events.append(event)

                result_data = events
            elif self.merge_on_send:
                merged_data = bytes()
                for d in copy_of_data:
                    merged_data += d

                result_data = merged_data

            self.batch_data.remove_all()
            return True, result_data

        return False, None


def new_batch_by_count(batch_threshold: int) -> BatchConfig:
    """ new_batch_by_count create, initializes  and returns a new instance for BatchConfig """
    return BatchConfig(batch_threshold=batch_threshold, batch_mode=BatchMode.BATCH_BY_COUNT_ONLY)


def new_batch_by_time(time_interval: str) -> Tuple[BatchConfig, Optional[errors.EdgeX]]:
    """ new_batch_by_time create, initializes  and returns a new instance for BatchConfig """
    config = BatchConfig(
        time_interval=time_interval,
        batch_mode=BatchMode.BATCH_BY_TIME_ONLY
    )
    try:
        config.parsed_duration = isodate.parse_duration("PT" + time_interval.upper())
    except ISO8601Error as e:
        return config, errors.new_common_edgex_wrapper(e)

    config.done = Queue(maxsize=1)
    return config, None


def new_batch_by_time_and_count(
        time_interval:str, batch_threshold: int) -> Tuple[BatchConfig, Optional[errors.EdgeX]]:
    """ new_batch_by_time_and_count create, initializes
    and returns a new instance for BatchConfig """
    config = BatchConfig(
        time_interval=time_interval,
        batch_threshold=batch_threshold,
        batch_mode=BatchMode.BATCH_BY_TIME_AND_COUNT
    )
    try:
        config.parsed_duration = isodate.parse_duration("PT" + time_interval.upper())
    except ISO8601Error as e:
        return config, errors.new_common_edgex_wrapper(e)

    config.done = Queue(maxsize=1)
    return config, None
