# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Launch the ACAS X."""
import asyncio
import time
from typing import Dict, Literal, Union

import hydra
import uvicorn
from fastapi import FastAPI
from hydra.core.config_store import ConfigStore
from loguru import logger

from pycasx.acas import (
    AutoavoidInfo,
    ExtendedAircraft,
    ExtendedIntruder,
    RootInfo,
    SystemInfo,
)
from pycasx.acas.runner import Runner
from pycasx.conf import ACASXConfig
from pycasx.connectors.adsb import ADSB
from pycasx.connectors.protocols import PropsConnection

cs = ConfigStore.instance()
cs.store(name="acasx_", node=ACASXConfig)


@hydra.main(version_base=None, config_path="pkg://pycasx.conf", config_name="acasx")
def acasx(cfg: ACASXConfig) -> None:  # noqa: C901
    """Run both HCAS and VCAS in a continuous loop.

    Args:
        cfg (ACASXConfig): The ACAS X configuration.
    """
    adsb = ADSB(**cfg.adsb)  # type: ignore

    acasx_runner = Runner(
        backend=cfg.backend,
        rate=cfg.update_rate,
        autoavoid_cfg=cfg.autoavoid,
        logger_cfg=cfg.logger,
    )
    acasx_runner.register_connection(adsb)

    app = FastAPI(
        title="pyCASX API",
        docs_url=None,
    )

    async def startup_event() -> None:
        """Run the ACAS X systems in a continuous loop upon startup."""
        asyncio.create_task(acasx_runner.run())

    app.add_event_handler("startup", startup_event)

    @app.get("/ownship")
    async def get_ownship() -> ExtendedAircraft:
        """Get the ownship from the ACAS X system.

        Returns:
            ExtendedAircraft: the ownship representation.
        """
        return acasx_runner.get_ownship()

    @app.get("/autoavoid")
    async def autoavoid() -> AutoavoidInfo:
        """Get the autoavoid status from the ACAS X system.

        Returns:
            AutoavoidInfo: the ownship representation.
        """
        return acasx_runner.get_autoavoid()

    @app.get("/intruders")
    async def get_intruders() -> Dict[str, Union[ExtendedIntruder, float]]:
        """Get the intruders from the ACAS X system.

        Returns:
            Dict[str, Union[ExtendedIntruder, float]]: The intruders
                from the ACAS X system.
        """
        return acasx_runner.get_intruders()

    @app.get("/intruders/{call_sign}")
    async def get_intruder(call_sign: str) -> ExtendedIntruder:
        """Get an intruder from the ACAS X system.

        Args:
            call_sign (str): The callsign of the intruder.

        Returns:
            ExtendedIntruder: The intruder from the ACAS X system.
        """
        return acasx_runner.get_intruder(call_sign)

    @app.put("/connector")
    async def register_system_connection(connection: Literal["adsb"]) -> None:
        """Register a connection with the ACAS X system.

        Args:
            connection (Literal["adsb"]): The connection to register.
        """
        conn: PropsConnection = {"adsb": adsb}[connection]  # type: ignore
        acasx_runner.register_connection(conn)

    @app.get("/{system_type}")
    async def get_system(system_type: Literal["hcas", "vcas"]) -> SystemInfo:
        """Get the information about a CAS system.

        Args:
            system_type (Literal["hcas", "vcas"]): The CAS system to get
                information about.

        Returns:
            SystemInfo: The information about the CAS system.
        """
        return acasx_runner.get_system_info(system_type)

    @app.get("/")
    async def root() -> RootInfo:
        """Get the information about both CAS systems.

        Returns:
            RootInfo: The information about both CAS system aka the full ACAS X system.
        """
        return {
            "hcas": acasx_runner.get_system_info("hcas"),
            "vcas": acasx_runner.get_system_info("vcas"),
            "timestamp": time.time(),
        }

    logger.info(f"Starting API server at http://{cfg.api.host}:{cfg.api.port}")
    uvicorn.run(app, host=cfg.api.host, port=cfg.api.port, log_level="warning")
