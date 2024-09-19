# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import unittest

from pycasx.acas.acasx import ACASX


class TestCAS(unittest.TestCase):
    def test_wrong_backend(self) -> None:
        with self.assertRaises(NotImplementedError):
            ACASX(backend="unsupported_backend")  # type: ignore
