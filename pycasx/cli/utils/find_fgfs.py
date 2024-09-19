# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Find FlightGear and the corresponding root data directory."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal, overload


@overload
def find_fgfs() -> Path: ...


@overload
def find_fgfs(with_root: Literal[False]) -> Path: ...


@overload
def find_fgfs(with_root: Literal[True]) -> tuple[Path, Path]: ...


def find_fgfs(with_root: bool = False) -> Path | tuple[Path, Path]:
    """Find the fully resolved path to the FlightGear executable.

    Args:
        with_root (bool): If true, return the root data directory as well.

    Returns:
        Path | tuple[Path, Path]: The fully resolved path to the FlightGear
            executable and the root data directory if `with_root` is
            true.

    Raises:
        NotImplementedError: If the platform is not supported.
    """
    if sys.platform == "win32":
        fgfs = Path("C:/Program Files/FlightGear 2020.3/bin/fgfs.exe")
        root = Path("C:/Program Files/FlightGear 2020.3/data")
    elif sys.platform == "darwin":
        fgfs = Path("/Applications/FlightGear.app/Contents/MacOS/fgfs")
        root = Path("/Applications/FlightGear.app/Contents/Resources/data")
    elif sys.platform == "linux":
        fgfs = Path("/usr/games/fgfs")
        root = Path("/usr/share/games/flightgear")
    else:
        raise NotImplementedError(
            f"FlightGear is not supported on {sys.platform}."
            " Please ensure FlightGear is installed and provide a custom path."
        )

    if with_root:
        return fgfs.resolve(), root.resolve()
    return fgfs.resolve()
