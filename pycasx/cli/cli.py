# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Command line interface for pycasx.

Only import what's needed once a functions is called. Currently, torch
imports are slow (aka expensive), to speed up the CLI, we import and
call the functions only when really needed. This way, simple commands
like `pycasx --help` or `pycasx --version` print the information
immediately without needing to import torch and thus slowing down the
CLI.
"""
import sys
import warnings


def print_help():
    """Print the help message."""
    print(
        """
pycasx - Running ACAS X for FlightGear

Usage: pycasx --help <command> [<hydra args>...]

Commands:
    acasx:      Run the full ACAS X system (requires FlightGear)
    copy:       Copy the provided scenarios for FlightGear into the FG_ROOT
    launch:     Launch FlightGear
    onnx:       Convert the neural nets from NNet format into onnx format
    run:        Run the ACAS X test suite
    scenarios:  Generate full sets of scenarios for FlightGear

Hydra args:
    Manipulate the default configuration for each command via hydra cli commands.
"""
    )


def print_version():
    """Print the version of pyCASX."""
    import pycasx as c

    print(c.__version__)


def _acasx() -> None:
    """Run the full ACAS X system."""
    from pycasx.cli.acasx import acasx

    acasx()


def _copy_files() -> None:
    """Copy the provided scenarios for FlightGear into the FG_ROOT."""
    from pycasx.cli.copy_files import copy_files

    copy_files()


def _launch() -> None:
    """Launch FlightGear."""
    from pycasx.cli.launch import launch

    launch()


def _onnx() -> None:
    """Convert the neural nets from NNet format into onnx format."""
    from pycasx.cli.convert_to_onnx import convert_to_onnx

    convert_to_onnx()


def _run() -> None:
    """Run the ACAS X test suite."""
    from pycasx.cli.run import run

    run()


def _scenarios() -> None:
    """Generate full sets of scenarios for FlightGear."""
    from pycasx.cli.scenarios import create_scenarios

    create_scenarios()


def main() -> None:
    """Run the cli tools.

    Depending on the arguments, it will run the appropriate tool.

    Raises:
        ValueError: If the script name is unknown.
    """
    if sys.argv[0].endswith("cas"):
        warnings.warn(
            "The script name 'cas' is deprecated, please use 'pycasx' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    try:
        script_name = sys.argv[1]
        # Remove script name
        del sys.argv[1]
        # Execute known script
    except IndexError:
        script_name = "help"  # Default script if no script name is given
    known_scripts = {
        "acasx": _acasx,
        "copy": _copy_files,
        "launch": _launch,
        "onnx": _onnx,
        "run": _run,
        "scenarios": _scenarios,
        "help": print_help,
        "-h": print_help,
        "--help": print_help,
        "-v": print_version,
        "--version": print_version,
        "noop": lambda: None,  # Only used for testing
    }
    if script_name not in known_scripts:
        raise ValueError(
            f"The script {script_name} is unknown,"
            f" please use one of {known_scripts.keys()}"
        )
    known_scripts[script_name]()


if __name__ == "__main__":
    sys.argv.append("pycasx")
    main()
