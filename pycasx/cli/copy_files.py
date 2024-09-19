# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Copy scenarios to corresponding FG_ROOT folder."""


import os
import shutil
from pathlib import Path

import hydra
from hydra.core.config_store import ConfigStore
from loguru import logger

from pycasx.cli import FGFS_ASSETS_DATA_PATH
from pycasx.cli.utils.find_fgfs import find_fgfs
from pycasx.conf import CopyConfig

cs = ConfigStore.instance()
cs.store(name="copy_", node=CopyConfig)


@hydra.main(version_base=None, config_path="pkg://pycasx.conf", config_name="copy")
def copy_files(cfg: CopyConfig) -> None:
    """Copy FlightGear related files to the FlightGear data directory.

    Args:
        cfg (CopyConfig): The copy configuration.
    """
    _, fg_root = find_fgfs(with_root=True)
    fg_root = fg_root if cfg.fg_root is None else Path(cfg.fg_root)

    # Copy the assets to the FlightGear data directory.
    for f in FGFS_ASSETS_DATA_PATH.glob("**/*"):
        if f.is_file():
            dest = Path(fg_root, f.relative_to(FGFS_ASSETS_DATA_PATH))

            if dest.exists() and dest.is_file() and os.path.samefile(f, dest):
                logger.info("Skipping, file already exists.")
                continue

            logger.info(f"Copying {f} to {dest}")
            shutil.copyfile(f, dest)
