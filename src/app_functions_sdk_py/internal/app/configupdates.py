#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0

"""
This module provides a ConfigUpdateProcessor that can be used to process configuration updates
triggered from the configuration provider.
"""

from ...internal.common.config import PipelineFunction


# TODO: Implement ConfigUpdateProcessor in milestone F  # pylint: disable=fixme

def set_pipeline_function_parameter_names_lowercase(functions: dict[str, PipelineFunction]):
    """
    set_pipeline_function_parameter_names_lowercase sets the parameter names of all functions in
    the pipeline to lowercase.
    """
    for function in functions.values():
        keys_to_update = list(function.Parameters.keys())
        for key in keys_to_update:
            value = function.Parameters[key]
            # Make sure the old key has been removed so don't have multiples
            del function.Parameters[key]
            function.Parameters[key.lower()] = value
