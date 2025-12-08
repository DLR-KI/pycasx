# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT

import io
import sys
import unittest
import unittest.mock

import pytest

from pycasx import __version__ as pycasx_version
from pycasx.cli.cli import main as cli_main


class TestCLI(unittest.TestCase):
    def test_wrong_script(self):
        sys.argv = ["pycasx", "wrong_script"]
        with pytest.raises(ValueError):
            cli_main()

    def test_warns_with_old_script_name(self):
        sys.argv = ["cas", "noop"]
        with self.assertWarns(DeprecationWarning):
            cli_main()

    def test_noop_arg(self):
        sys.argv = ["pycasx", "noop"]
        cli_main()

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_defaults_to_help(self, stdout):
        sys.argv = ["pycasx"]
        cli_main()
        default_response = stdout.getvalue()
        stdout.seek(0)  # Reset the StringIO object
        sys.argv = ["pycasx", "--help"]
        cli_main()
        help_response = stdout.getvalue()
        assert default_response == help_response

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_version_arg(self, stdout):
        version_args = ["-v", "--version"]
        for arg in version_args:
            sys.argv = ["pycasx", arg]
            cli_main()
            assert stdout.getvalue() == f"{pycasx_version}\n"
            stdout.seek(0)  # Reset the StringIO object

    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_help_arg_returns_text(self, stdout):
        help_args = ["-h", "--help", "help"]
        for arg in help_args:
            sys.argv = ["pycasx", arg]
            cli_main()
            help_text = stdout.getvalue()
            # Check that the help text is not empty
            assert len(help_text) > 10
            # Check that the help text contains the CLI name
            assert "pycasx" in help_text
            # Check that the help text contains the word "Usage"
            assert "Usage" in help_text
            # Check that the help text contains the word "Commands"
            assert "Commands" in help_text
            # Check that the help text contains the registered commands
            commands = ["acasx", "launch", "onnx", "copy", "scenarios"]
            for command in commands:
                assert command in help_text
            # Check that the help text contains the word "Hydra"
            assert "Hydra" in help_text
            stdout.seek(0)  # Reset the StringIO object
