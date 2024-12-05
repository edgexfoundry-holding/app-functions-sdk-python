# Copyright (C) 2024 IOTech Ltd
# SPDX-License-Identifier: Apache-2.0

import unittest
from src.app_functions_sdk_py.contracts.errors import (new_common_edgex, new_common_edgex_wrapper,
                                                       ErrKind, kind)


class TestErrorHandling(unittest.TestCase):

    def setUp(self):
        self.L0Error = new_common_edgex(ErrKind.UNKNOWN, "", None)
        self.L1Error = Exception("nothing")
        self.L1ErrorWrapper = new_common_edgex_wrapper(self.L1Error)
        self.L2ErrorWrapper = new_common_edgex_wrapper(self.L1ErrorWrapper)
        self.L2Error = new_common_edgex(ErrKind.DATABASE_ERROR, "database failed", self.L1Error)
        self.L3Error = new_common_edgex_wrapper(self.L2Error)
        self.L4Error = new_common_edgex(ErrKind.UNKNOWN, "don't know", self.L3Error)
        self.L5Error = new_common_edgex(ErrKind.COMMUNICATION_ERROR, "network disconnected",
                                        self.L4Error)

    def test_kind(self):
        tests = [
            ("Check the empty CommonEdgeX", self.L0Error, ErrKind.UNKNOWN),
            ("Check the non-CommonEdgeX", self.L1Error, ErrKind.UNKNOWN),
            ("Get the first error kind with 1 error wrapped", self.L2Error, ErrKind.DATABASE_ERROR),
            ("Get the first error kind with 2 error wrapped", self.L3Error, ErrKind.DATABASE_ERROR),
            ("Get the first non-unknown error kind with 3 error wrapped", self.L4Error,
             ErrKind.DATABASE_ERROR),
            ("Get the first error kind with 4 error wrapped", self.L5Error,
             ErrKind.COMMUNICATION_ERROR),
        ]

        for name, err, expected_kind in tests:
            with self.subTest(name=name):
                self.assertEqual(kind(err), expected_kind, f"Retrieved Error Kind {kind(err)} "
                                                           f"is not equal to {expected_kind}.")

    def test_message(self):
        tests = [
            ("Get the first level error message from an empty error", self.L0Error, ""),
            ("Get the first level error message from an empty EdgeXError with 1 error wrapped",
             self.L1ErrorWrapper, str(self.L1Error)),
            ("Get the first level error message from an empty EdgeXError with 1 empty error wrapped",
             self.L2ErrorWrapper, str(self.L1Error)),
            ("Get the first level error message from an EdgeXError with 1 error wrapped",
             self.L2Error, self.L2Error.message),
            ("Get the first level error message from an empty EdgeXError with 2 error wrapped",
             self.L3Error, self.L2Error.message),
            ("Get the first level error message from an EdgeXError with 3 error wrapped",
             self.L4Error, self.L4Error.message),
            ("Get the first level error message from an EdgeXError with 4 error wrapped",
             self.L5Error, self.L5Error.message),
        ]

        for name, err, expected_msg in tests:
            with self.subTest(name=name):
                self.assertEqual(err.first_level_message(), expected_msg,
                                 f"Returned error message {err.first_level_message()} "
                                 f"is not equal to {expected_msg}.")


if __name__ == '__main__':
    unittest.main()
