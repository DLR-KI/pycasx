# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Command line interface module for pycasx."""
from pathlib import Path

ASSETS_PATH = Path(Path(__file__).parent.parent, "assets")
FGFS_ASSETS_ROOT = Path(ASSETS_PATH, "flightgear")
FGFS_ASSETS_CONFIG_PATH = Path(FGFS_ASSETS_ROOT, "config")
FGFS_ASSETS_DATA_PATH = Path(FGFS_ASSETS_ROOT, "data")
