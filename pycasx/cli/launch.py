# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Launch FlightGear with our custom options."""

import subprocess
import sys
from pathlib import Path

import hydra
from hydra.core.config_store import ConfigStore

from pycasx.cli import FGFS_ASSETS_CONFIG_PATH, FGFS_ASSETS_DATA_PATH
from pycasx.cli.utils.find_fgfs import find_fgfs
from pycasx.conf import LaunchConfig

cs = ConfigStore.instance()
cs.store(name="launch_", node=LaunchConfig)


@hydra.main(version_base=None, config_path="pkg://pycasx.conf", config_name="launch")
def launch(cfg: LaunchConfig) -> None:  # noqa: C901
    """Launches FlightGear with our custom options.

    Args:
        cfg (LaunchConfig): The configuration to use.

    Raises:
        ValueError: If the timeout together with the background flag is
            set.
    """
    fgfs, fg_root = find_fgfs(with_root=True)
    fgfs = fgfs if cfg.fgfs is None else Path(cfg.fgfs)
    fg_root = fg_root if cfg.fg_root is None else Path(cfg.fg_root)

    command = [str(fgfs.resolve())]

    if cfg.httpd is not None:
        command += [f"--httpd={cfg.httpd}"]

    if cfg.telnet is not None:
        command += [f"--telnet=,,{cfg.telnet.rate},,{cfg.telnet.port},"]

    if cfg.aircraft is not None:
        command += [f"--aircraft={cfg.aircraft}"]

    if cfg.altitude is not None:
        command += [f"--altitude={cfg.altitude}"]

    if cfg.heading is not None:
        command += [f"--heading={cfg.heading}"]

    if cfg.lat is not None:
        command += [f"--lat={cfg.lat}"]

    if cfg.lon is not None:
        command += [f"--lon={cfg.lon}"]

    if cfg.pitch is not None:
        command += [f"--pitch={cfg.pitch}"]

    if cfg.roll is not None:
        command += [f"--roll={cfg.roll}"]

    if cfg.vc is not None:
        command += [f"--vc={cfg.vc}"]

    if cfg.timeofday is not None:
        command += [f"--timeofday={cfg.timeofday}"]

    if cfg.wind is not None:
        command += [f"--wind={cfg.wind}"]

    if cfg.ai_scenario is not None:
        command += [f"--ai-scenario={cfg.ai_scenario}"]

    if cfg.disable_sound:
        command += ["--disable-sound"]

    if cfg.config is not None:
        for config in cfg.config:
            command += [f"--config={FGFS_ASSETS_CONFIG_PATH.resolve()}/{config}"]

    if cfg.prop is not None:
        for prop, value in cfg.prop.items():
            command += [f"--prop:{prop}={value}"]

    # Under Windows, FlightGear sometimes fails to find the data directory.
    if sys.platform == "win32":
        command.append(f"--fg-root={fg_root.resolve()}")

    # Will work in 2020.4
    command += [f"--data={FGFS_ASSETS_DATA_PATH.resolve()}"]

    # Manually parse the fgfsrc file
    # fgfs will ignore duplicate options, so we can safely append them.
    # In any case, CLI options take priority over the fgfsrc file.
    if cfg.fgfsrc is not None:
        with open(cfg.fgfsrc, encoding="utf-8") as f:
            line = f.readline()
            while line:
                if line[0] != "#":
                    command += line.split()
                line = f.readline()

    timeout = cfg.timeout if cfg.timeout > 0 else None
    if timeout is not None and cfg.background:
        raise ValueError("Cannot run in background with a timeout")

    if cfg.background:
        subprocess.Popen(command)
    else:
        subprocess.run(command, check=True, timeout=timeout)
