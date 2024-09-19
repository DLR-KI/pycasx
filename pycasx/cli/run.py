# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Run the ACAS X test suite.

Not to be confused with software tests, this command runs multiple
scenarios and logs the data to a file.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import hydra
import libtmux
from hydra.core.config_store import ConfigStore
from tqdm.rich import tqdm

import pycasx
from pycasx.conf import RunConfig

cs = ConfigStore.instance()
cs.store(name="run_", node=RunConfig)

SCENARIO_FOLDER = Path(Path(pycasx.__file__).parent, "assets", "scenarios").resolve()

FGFS_BASE_CMD = " ".join(
    [
        "pycasx",
        "launch",
        "background=false",
        "httpd=null",
        "telnet=null",
        "disable_sound=false",
        "aircraft=null",
        "altitude=null",
        "heading=null",
        "lat=null",
        "lon=null",
        "pitch=null",
        "roll=null",
        "vc=null",
        "config=null",
        "prop=null",
        "timeofday=null",
        "wind=null",
        "ai_scenario=null",
    ]
)
PYCASX_BASE_CMD = " ".join(
    [
        "pycasx",
        "acasx",
        "logger.log_folder=logs/{uuids[_idx]}/{run_}",
        "logger.include_date=false",
    ]
)


@hydra.main(version_base=None, config_path="pkg://pycasx.conf", config_name="run")
def run(cfg: RunConfig) -> None:
    """Run the ACAS X test suite.

    Not to be confused with software tests, this command runs multiple
    scenarios and logs the data to a file.

    Args:
        cfg (RunConfig): The configuration for the run command.

    Raises:
        RuntimeError: If the command is run on Windows.
    """
    if sys.platform == "win32":
        raise RuntimeError("This command is not supported on Windows.")

    srv = libtmux.server.Server()
    session = srv.new_session("pycasx", attach=False, kill_session=True)
    fgfs_window = session.active_window.rename_window("FlightGear")
    acasx_window = session.new_window("ACAS X", attach=False)

    fgfs_pane: libtmux.pane.Pane = fgfs_window.active_pane  # type: ignore
    acasx_pane: libtmux.pane.Pane = acasx_window.active_pane  # type: ignore

    time.sleep(5)  # Wait for the windows to be created

    if cfg.venv_path is not None:
        fgfs_pane.send_keys(f"source {cfg.venv_path}/bin/activate", enter=True)
        acasx_pane.send_keys(f"source {cfg.venv_path}/bin/activate", enter=True)

    # Get all valid scenarios
    scenarios = list(SCENARIO_FOLDER.glob("*_fgfs.txt"))
    uuids = [s.stem[:-5] for s in scenarios]  # noqa: F841

    for _idx, scenario in enumerate(tqdm(scenarios)):
        for run_ in range(3):
            cmd_ = eval(f'f"{PYCASX_BASE_CMD}"')
            if run_ == 0:
                acasx_pane.send_keys(f"{cmd_} autoavoid.active=False", enter=True)
            elif run_ == 1:
                acasx_pane.send_keys(
                    f"{cmd_} autoavoid.active=True autoavoid.mode=hcas", enter=True
                )
            elif run_ == 2:
                acasx_pane.send_keys(
                    f"{cmd_} autoavoid.active=True autoavoid.mode=vcas", enter=True
                )

            # Start FlightGear
            fgfs_pane.send_keys(
                f"{FGFS_BASE_CMD} timeout={cfg.timeout} fgfsrc={scenario.resolve()}",
                enter=True,
            )

            # Wait for the scenario to finish
            time.sleep(cfg.timeout + 5)

            # Cleanup
            acasx_pane.send_keys("C-c", enter=False, suppress_history=False)
