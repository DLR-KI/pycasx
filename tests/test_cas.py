# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT


import unittest

import pytest

from pycasx.acas.acasx import ACASX


class TestCAS(unittest.TestCase):
    def test_wrong_backend(self) -> None:
        with pytest.raises(NotImplementedError):
            ACASX(backend="unsupported_backend")  # type: ignore
