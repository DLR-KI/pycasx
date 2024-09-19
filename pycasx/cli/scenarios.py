# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Run the scenario generation via CLI."""
from __future__ import annotations

import hydra
from hydra.core.config_store import ConfigStore

from pycasx.conf import ScenarioConfig
from pycasx.scenario.scenario import create_scenarios as create_scenarios_

cs = ConfigStore.instance()
cs.store(name="scenario_", node=ScenarioConfig)


@hydra.main(version_base=None, config_path="pkg://pycasx.conf", config_name="scenario")
def create_scenarios(cfg: ScenarioConfig) -> None:
    """Generate full sets of scenarios for FlightGear.

    Args:
        cfg (ScenarioConfig): The scenario configuration.
    """
    create_scenarios_(cfg)
