#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for JSONLogic
"""
import json
from json import JSONDecodeError
from typing import Any, Tuple, Optional

from json_logic import jsonLogic

from ..contracts import errors
from ..interfaces import AppFunctionContext
from ..utils.helper import coerce_type

RULE = "rule"


class JSONLogic:
    # pylint: disable=too-few-public-methods
    """ JSONLogic parser accepts JsonLogic rules and executes them """

    def __init__(self, rule: dict):
        self.rule = rule

    def evaluate(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ Evaluate the JSON logic """
        if data is None:
            return False, errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID,
                f"function JSONLogic in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug("Evaluate JSON Logic in pipeline '%s'", ctx.pipeline_id())

        byte_data, err = coerce_type(data)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        try:
            # https://github.com/nadirizr/json-logic-py no longer maintain and not support Python3
            # use https://github.com/panzi/panzi-json-logic instead
            input_data = json.loads(byte_data)
            result = jsonLogic(self.rule, input_data)
        except JSONDecodeError as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                "JSONLogic input data should be JSON format",
                e
            )
        except ReferenceError as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                "unable to apply JSONLogic rule",
                e
            )

        ctx.logger().debug("Condition met in pipeline '%s': %s", ctx.pipeline_id(), result)
        return result, data


def new_json_logic(rule: str) -> Tuple[JSONLogic, Optional[errors.EdgeX]]:
    """ new_json_logic creates, initializes and returns a new instance of json_logic """
    try:
        return JSONLogic(json.loads(rule)), None
    except JSONDecodeError as e:
        return JSONLogic({}), errors.new_common_edgex(
            errors.ErrKind.CONTRACT_INVALID,
            "unable to decode the JSON logic rule",
            e
        )
