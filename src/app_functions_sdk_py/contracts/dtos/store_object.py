#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for StoredObject
"""
import uuid
from dataclasses import dataclass, field
from typing import Optional, Any

from ...contracts import errors


@dataclass
class StoredObject:
    # pylint: disable=invalid-name
    # pylint: disable=too-many-instance-attributes
    """ StoredObject is the atomic and most abstract description
    of what is collected by the export store system. """

    # retryCount is how many times this has tried to be exported
    retryCount: int
    # pipelineId is the ID of the pipeline that needs to be restarted.
    pipelineId: str = ""
    # pipelinePosition is where to pickup in the pipeline
    pipelinePosition: int = 0
    # version is a hash of the functions to know if the pipeline has changed.
    version: str = ""
    # correlationID is an identifier provided by EdgeX to track this record as it moves
    correlationID: str = ""
    # id uniquely identifies this StoredObject
    id: str = ""
    # appServiceKey identifies the app to which this data belongs.
    appServiceKey: str = ""
    # payload is the data to be exported
    payload: Any = None
    # contextData is a snapshot of data used by the pipeline at runtime
    contextData: dict = field(default_factory=dict)

    def validate_contract(self, id_required: bool) -> Optional[errors.EdgeX]:
        """ validate_contract ensures that the required fields are present on the object. """
        if id_required:
            if self.id == "":
                return errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    "invalid contract, ID cannot be empty")
        else:
            if self.id == "":
                self.id = str(uuid.uuid4())

        if self.appServiceKey == "":
            return errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                "invalid contract, app service key cannot be empty")
        if len(self.payload) == 0:
            return errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                "invalid contract, payload cannot be empty")
        if self.version == "":
            return errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                "invalid contract, version cannot be empty")

        return None


# pylint: disable=too-many-arguments, too-many-positional-arguments
def new_stored_object(
        app_service_key: str, payload: Any, pipeline_id: str, pipeline_position: int,
        version: str, context_data: dict) -> StoredObject:
    """ NewStoredObject creates a new instance of StoredObject
            and is the preferred way to create one. """
    return StoredObject(
        appServiceKey=app_service_key,
        payload=payload,
        retryCount=0,
        pipelineId=pipeline_id,
        pipelinePosition=pipeline_position,
        version=version,
        contextData=context_data)
