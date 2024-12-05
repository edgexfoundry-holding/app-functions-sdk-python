# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

"""
The event module of the App Functions SDK Python package.

This module defines the Event class which represents an event in the context of the App Functions
SDK. An event is a collection of readings from a device.

Classes:
    Event: Represents an event. It has attributes like event_id, device_name, profile_name,
    source_name, origin, readings, and tags.
"""
import base64
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

import xmltodict
from dataclasses_json import dataclass_json

from .common.base import Versionable
from .tags import Tags
from .reading import BaseReading, new_base_reading
from .. import errors
from ..clients.utils.common import convert_any_to_dict
from ..common import constants
from ..common.constants import API_VERSION

@dataclass_json
@dataclass
class Event(Versionable):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=invalid-name
    """
        Represents an event.

        An event is a collection of readings from a device. It has attributes like event_id,
        device_name, profile_name, source_name, origin, readings, and tags.

        Attributes:
            id (str): The ID of the event.
            deviceName (str): The name of the device that generated the event.
            profileName (str): The name of the profile associated with the device.
            sourceName (str): The name of the source that generated the event.
            origin (int): The time the event was generated.
            readings (list[BaseReading]): The readings associated with the event.
            tags (Tags): The tags associated with the event.

        Methods:
            __post_init__(): Initializes the API version of the event.
        """
    id: str = ""
    deviceName: str = ""
    profileName: str = ""
    sourceName: str = ""
    origin: int = 0
    readings: list[BaseReading] = field(default_factory=lambda: [], init=True)
    tags: Tags = field(default_factory=lambda: {}, init=True)
    apiVersion: str = field(default=API_VERSION, init=False)

    def add_base_reading(self, resource_name: str, value_type: str, value: Any):
        """ add_base_reading creates the reading and append to the event """
        self.readings.append(
            new_base_reading(
                self.profileName, self.deviceName, resource_name, value_type, value))

    def to_xml(self) -> Tuple[str, Optional[errors.EdgeX]]:
        """ convert event to XML """
        try:
            d = {"Event": convert_dict_keys_to_upper_camelcase(convert_any_to_dict(self))}
            return xmltodict.unparse(d), None
        except (ValueError, KeyError, AttributeError) as e:
            return "", errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                "failed to convert event to XML", e)

    def add_binary_reading(
            self, resource_name: str, binary_value: bytes, media_type: str):
        """ add_binary_reading adds a binary reading to the Event  """
        reading = new_base_reading(
            self.profileName, self.deviceName, resource_name,
            constants.VALUE_TYPE_BINARY, "")
        reading.mediaType = media_type
        reading.binaryValue = binary_value
        self.readings.append(reading)

    def add_object_reading(self, resource_name: str, object_value: Any):
        """ add_object_reading adds a object reading to the Event """
        reading = new_base_reading(
            self.profileName, self.deviceName, resource_name,
            constants.VALUE_TYPE_OBJECT, "")
        reading.objectValue = object_value
        self.readings.append(reading)


def new_event(profile_name: str, device_name: str, source_name: str) -> Event:
    """ new_event creates and returns an initialized Event with no Readings """
    return Event(
        id=str(uuid.uuid4()),
        deviceName=device_name,
        profileName=profile_name,
        sourceName=source_name,
        origin=time.time_ns(),
        readings=[]
    )


def convert_dict_keys_to_upper_camelcase(obj: dict) -> Any:
    """ convert the dictionary key to upper camelcase """
    if isinstance(obj, dict):
        return {
            k[0].upper() + k[1:]: convert_dict_keys_to_upper_camelcase(v) for k, v in obj.items()}
    if hasattr(obj, '__dict__'):
        return {
            k[0].upper() + k[1:]: convert_dict_keys_to_upper_camelcase(v)
            for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [convert_dict_keys_to_upper_camelcase(e) for e in obj]
    return obj


def unmarshal_event(data: bytes) -> Tuple[Event, Optional[errors.EdgeX]]:
    """ unmarshal_event encode """
    d = json.loads(data)
    event = Event(**d)
    # convert readings from dict to BaseReading object
    event.readings = list(map(lambda r: BaseReading(**r), event.readings))
    try:
        for r in event.readings:
            if r.valueType == constants.VALUE_TYPE_BINARY:
                r.binaryValue = base64.b64decode(r.binaryValue)
    except (TypeError, ValueError) as e:
        return event, errors.new_common_edgex(
            errors.ErrKind.SERVER_ERROR,
            "failed to decode base64 str to bytes", e)
    return event, None
