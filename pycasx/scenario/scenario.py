# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Generate full sets of scenarios for FlightGear.

The scenarios consist of:
- A info file with general information about the flightplan
- A configuration file for the flight
- An AI scenario file
- The corresponding flight plan
"""
from __future__ import annotations

import random
import uuid
from pathlib import Path

from pycasx.cli import ASSETS_PATH
from pycasx.conf import ScenarioConfig
from pycasx.scenario import (
    SPDX_FILE_COPYRIGHT_TEXT,
    SPDX_LICENSE_IDENTIFIER,
    WayPointConfig,
    convert,
)
from pycasx.scenario.ai_scenario import create_ai_scenario_xml
from pycasx.scenario.calculate_cpa import calculate_cpa
from pycasx.scenario.fgfs_config import create_fgfs_config
from pycasx.scenario.flightplan import create_flightplan_xml
from pycasx.scenario.waypoint_generation import (
    generate_colliding_waypoints,
    generate_parallel_waypoints,
)


def create_intruders(
    cfg: ScenarioConfig,
    n_intruders: int,
    _uuid: uuid.UUID,
    fp_folder: Path,
    flightplan_files: list[Path],
    waypoints: dict[int, list[WayPointConfig]],
) -> None:
    """Create an intruder.

    Args:
        cfg (ScenarioConfig): The scenario configuration
        n_intruders (int): The number of intruders
        _uuid (uuid.UUID): The UUID of the scenario
        fp_folder (Path): The folder for the flight plans
        flightplan_files (list[Path]): The list of flight plan files
        waypoints (dict[int, list[WayPointConfig]]): The waypoints
    """
    for i in range(n_intruders):
        fp_file = Path(fp_folder, f"{_uuid}_fp_{i}.xml")
        fun_ = random.choices(
            population=[generate_colliding_waypoints, generate_parallel_waypoints],
            weights=[cfg.weights.colliding, cfg.weights.parallel],
            k=1,
        )[0]
        waypoints[i + 1] = fun_(cfg)
        fp_cfg = create_flightplan_xml(waypoints[i + 1])
        flightplan_files.append(fp_file)
        fp_file.write_text(fp_cfg, encoding="utf-8")


def create_scenario(cfg: ScenarioConfig) -> None:
    """Create a scenario.

    Args:
        cfg (ScenarioConfig): The scenario configuration
    """
    _uuid = uuid.uuid4()

    n_intruders = random.randint(cfg.min_intruders, cfg.max_intruders)

    folder = Path(ASSETS_PATH, "scenarios")
    if cfg.sort_by_uuid:
        folder = Path(folder, str(_uuid))
    ai_folder = Path(folder, "data", "AI")
    fp_folder = Path(ai_folder, "FlightPlans")
    fp_folder.mkdir(parents=True, exist_ok=True)

    fgfs_file = Path(folder, f"{_uuid}_fgfs.txt")
    info_file = Path(folder, f"{_uuid}_info.txt")

    fgfs_cfg = create_fgfs_config(cfg)
    info_cfg = (
        f"# {SPDX_FILE_COPYRIGHT_TEXT}\n#\n# {SPDX_LICENSE_IDENTIFIER}\n"
        + f"UUID: {_uuid}\n"
        + f"n_intruders: {n_intruders}\n"
        + f"cfg:\n{cfg}\n"
        + f"CPA: {calculate_cpa(cfg)}\n"
    )

    if n_intruders > 0:
        scenario_file = Path(ai_folder, f"{_uuid}_scenario.xml")
        fgfs_cfg += "--disable-ai-traffic\n"
        fgfs_cfg += f"--ai-scenario={scenario_file.stem}\n"
        flightplan_files: list[Path] = []
        waypoints: dict[int, list[WayPointConfig]] = {}

        create_intruders(
            cfg,
            n_intruders,
            _uuid,
            fp_folder,
            flightplan_files,
            waypoints,
        )

        info_cfg += f"waypoints:\n{waypoints}\n"
        info_cfg += (
            "Visualize the waypoints on:\n"
            + "<https://mobisoftinfotech.com/tools/plot-multiple-points-on-map/>\n"
        )
        info_cfg += (
            f'{convert(cfg.lat,"deg")},'
            f'{convert(cfg.lon,"deg")},'
            'red,marker,"Ownship Start"\n'
        )
        cpa = calculate_cpa(cfg)
        info_cfg += f'{cpa.lat},{cpa.lon},yellow,marker,"CPA"\n'
        for i, wp in waypoints.items():
            info_cfg += f'{wp[0].lat},{wp[0].lon},#0000FF,marker,"Int {i} START"\n'
            info_cfg += f'{wp[1].lat},{wp[1].lon},#AAAAFF,marker,"Int {i} END"\n'

        scenario_cfg = create_ai_scenario_xml(cfg, _uuid, flightplan_files)
        scenario_file.write_text(scenario_cfg, encoding="utf-8")

    fgfs_file.write_text(fgfs_cfg, encoding="utf-8")
    info_file.write_text(info_cfg, encoding="utf-8")


def create_scenarios(cfg: ScenarioConfig) -> None:
    """Generate full sets of scenarios for FlightGear.

    Args:
        cfg (ScenarioConfig): The scenario configuration.
    """
    for _ in range(cfg.n_scenarios):
        create_scenario(cfg)
