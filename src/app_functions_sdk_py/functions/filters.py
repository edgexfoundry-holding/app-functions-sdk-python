# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for Filter
"""
import re
from typing import List, Tuple, Any

from ..contracts.clients.logger import Logger
from ..contracts import errors
from ..contracts.dtos.event import Event
from ..interfaces import AppFunctionContext

PROFILE_NAMES = "profilenames"
DEVICE_NAMES = "devicenames"
SOURCE_NAMES = "sourcenames"
RESOURCE_NAMES = "resourcenames"
FILTER_OUT = "filterout"


class Filter:
    """ Filter houses various the parameters for which filter transforms filter on """
    def __init__(self,
                 filter_values:  List[str], filter_out: bool,
                 ctx: AppFunctionContext = None):
        self.filter_values = filter_values
        self.filter_out = filter_out
        self.ctx = ctx

    def setup_for_filtering(self,
                            func_name: str, filter_property: str, lc: Logger, data: Any) -> Event:
        """
        setup filter mode and check the data is valid event
        """
        mode = "For"
        if self.filter_out:
            mode = "Out"

        lc.debug(f"Filtering {mode} by {filter_property} in. "
                 f"FilterValues are: '[{self.filter_values}]'")

        if data is None:
            raise errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"{func_name}: no Event Received in pipeline '{self.ctx.pipeline_id()}'")

        if isinstance(data, Event) is False:
            raise errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"{func_name}: type received is not an Event "
                f"in pipeline '{self.ctx.pipeline_id()}'")

        return data

    def do_event_filter(self, filter_property: str, value: str) -> bool:
        """
        filer event by matching the value
        """
        # No names to filter for, so pass events through rather than filtering them all out.
        if len(self.filter_values) == 0:
            return True

        for name in self.filter_values:
            if re.match(name, value):
                if self.filter_out:
                    self.ctx.logger().debug(f"Event not accepted for {filter_property}={value} "
                                            f"in pipeline '{self.ctx.pipeline_id()}'")
                    return False

                self.ctx.logger().debug(f"Event accepted for {filter_property}={value} "
                                        f"in pipeline '{self.ctx.pipeline_id()}'")
                return True

        # Will only get here if Event's SourceName didn't match any names in FilterValues
        if self.filter_out:
            self.ctx.logger().debug(f"Event accepted for {filter_property}={value} "
                                    f"in pipeline {self.ctx.pipeline_id()}")
            return True

        self.ctx.logger().debug(f"Event not accepted for {filter_property}={value} "
                                f"in pipeline '{self.ctx.pipeline_id()}'")
        return False

    def filter_by_profile_name(self,
                               ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """
        filter_by_profile_name filters based on the specified Device Profile.
        If FilterOut is false, it filters out those Events
            not associated with the specified Device Profile listed in filter_values.
        If FilterOut is true, it out those Events
            that are associated with the specified Device Profile listed in filter_values.
        """
        self.ctx = ctx
        try:
            event = self.setup_for_filtering(
                "FilterByProfileName", "ProfileName", ctx.logger(), data)
            ok = self.do_event_filter("ProfileName", event.profileName)
            if ok:
                return True, event
        except errors.EdgeX as err:
            return False, err

        return False, None

    def filter_by_device_name(self,
                              ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """
        filter_by_device_name filters based on the specified Device Names, aka Instance of a Device.
        If FilterOut is false, it filters out those Events
                not associated with the specified Device Names listed in FilterValues.
        If FilterOut is true, it out those Events
                that are associated with the specified Device Names listed in FilterValues. """
        self.ctx = ctx
        try:
            event = self.setup_for_filtering(
                "FilterByDeviceName", "DeviceName", ctx.logger(), data)
            ok = self.do_event_filter("DeviceName", event.deviceName)
            if ok:
                return True, event
        except errors.EdgeX as err:
            return False, err

        return False, None

    def filter_by_source_name(self,
                              ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """
        filter_by_source_name filters based on the specified Source for the Event.
        If FilterOut is false, it filters out those Events
            not associated with the specified Source listed in FilterValues.
        If FilterOut is true, it out those Events
            that are associated with the specified Source listed in FilterValues.
        """
        self.ctx = ctx
        try:
            event = self.setup_for_filtering(
                "FilterBySourceName", "SourceName", ctx.logger(), data)
            ok = self.do_event_filter("SourceName", event.sourceName)
            if ok:
                return True, event
        except errors.EdgeX as err:
            return False, err

        return False, None

    def filter_by_resource_name(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        # pylint: disable=too-many-branches
        """
        filter_by_resource_name filters based on the specified Reading resource names.
        If FilterOut is false, it filters out those Event Readings
            not associated with the specified Resource Names listed in FilterValues.
        If FilterOut is true, it out those Event Readings
            that are associated with the specified Resource Names listed in FilterValues.
        This function will return an error
            and stop the pipeline if a non-edgex event is received or if no data is received.
        """
        self.ctx = ctx
        try:
            existing_event = self.setup_for_filtering(
                "FilterByResourceName", "ResourceName", ctx.logger(), data)

            # No filter values, so pass all event and all readings through,
            # rather than filtering them all out.
            if len(self.filter_values) == 0:
                return True, existing_event

            # Create copy of Event which will contain any Reading that are not filtered out
            aux_event = Event(
                id=existing_event.id,
                deviceName=existing_event.deviceName,
                profileName=existing_event.profileName,
                sourceName=existing_event.sourceName,
                origin=existing_event.origin)

            if self.filter_out:
                for reading in existing_event.readings:
                    reading_filtered_out = False
                    for name in self.filter_values:
                        item = re.compile(name)
                        if item.match(reading.resourceName):
                            reading_filtered_out = True
                            break

                    if not reading_filtered_out:
                        ctx.logger().debug(
                            f"Reading accepted in pipeline '{self.ctx.pipeline_id()}' "
                            f"for resource {reading.resourceName}")
                        aux_event.readings.append(reading)
                    else:
                        ctx.logger().debug(
                            f"Reading not accepted in pipeline '{self.ctx.pipeline_id()}' "
                            f"for resource {reading.resourceName}")
            else:
                for reading in existing_event.readings:
                    reading_filtered_for = False
                    for name in self.filter_values:
                        item = re.compile(name)
                        if item.match(reading.resourceName):
                            reading_filtered_for = True
                            break

                    if reading_filtered_for:
                        self.ctx.logger().debug(
                            f"Reading accepted in pipeline '{self.ctx.pipeline_id()}' "
                            f"for resource {reading.resourceName}")
                        aux_event.readings.append(reading)
                    else:
                        self.ctx.logger().debug(
                            f"Reading not accepted in pipeline '{self.ctx.pipeline_id()}' "
                            f"for resource {reading.resourceName}")

            if len(aux_event.readings) > 0:
                self.ctx.logger().debug(
                    f"Event accepted: {len(aux_event.readings)} remaining reading(s) "
                    f"in pipeline '{self.ctx.pipeline_id()}'")
                return True, aux_event

        except errors.EdgeX as err:
            return False, err

        self.ctx.logger().debug(
            f"Event not accepted: 0 remaining readings in pipeline '{self.ctx.pipeline_id()}'")
        return False, None


def new_filter_for(filter_values: List[str]) -> Filter:
    """ NewFilterFor creates, initializes and returns a new instance of Filter
    that defaults FilterOut to false, so it is filtering for specified values """
    return Filter(filter_values=filter_values, filter_out=False)


def new_filter_out(filter_values: List[str]) -> Filter:
    """ NewFilterOut creates, initializes and returns a new instance of Filter
    that defaults FilterOut to true, so it is filtering out specified values """
    return Filter(filter_values=filter_values, filter_out=True)
