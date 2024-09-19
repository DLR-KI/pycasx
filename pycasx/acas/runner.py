# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Runner class around ACAS X."""
import asyncio
import json
import math
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Literal, Union

from fastapi import HTTPException
from loguru import logger

import pycasx
from pycasx.acas import (
    HCAS_ACTIONS,
    VCAS_ACTIONS,
    AutoavoidInfo,
    ExtendedAircraft,
    ExtendedIntruder,
    HCASAdvisories,
    SystemInfo,
    VCASAdvisories,
    extend_intruder,
    ureg,
)
from pycasx.acas.acasx import ACASX
from pycasx.conf import AutoavoidConfig, LoggerConfig
from pycasx.connectors.protocols import PropsConnection


class Runner:
    """Run the ACAS X system in a continuous loop.

    Args:
        backend (str): The neural network backend to use for the CAS.
        rate (float): The update rate of the ACAS X.
        autoavoid_cfg (AutoavoidConfig): The autoavoid configuration.
        logger_cfg (LoggerConfig): The logger configuration.
    """

    def __init__(
        self,
        backend: str,
        rate: float,
        autoavoid_cfg: AutoavoidConfig,
        logger_cfg: LoggerConfig,
    ) -> None:
        self.rate = rate
        self.acasx = ACASX(backend=backend)  # type: ignore
        self.hcas_adv = HCASAdvisories.ACTIVE
        self.vcas_adv = VCASAdvisories.ACTIVE

        self.autoavoid_cfg = autoavoid_cfg
        self.action = None
        self.command = None
        self.heading_lock_set = False
        self.altitude_lock_set = False
        self.leveled_target_bank_angle_deg = 0
        self.hcas_reset = True
        self.leveled_vertical_speed_fpm = 0
        self.vcas_reset = True
        # Default gravitational acceleration. As an alternative, can be
        # queried at /environment/gravitational-acceleration-mps2
        self.g = 9.813179 * ureg.meter / ureg.second**2

        self.logger_cfg = logger_cfg
        self.logging_initialized = False

        self.max_width = (
            max(
                [len("HCAS"), len("VCAS")]
                + [len(a.name) for a in HCASAdvisories]
                + [len(a.name) for a in VCASAdvisories]
                + [len("Autoavoid"), len("Active"), len("Mode"), len("Command")]
                + [len(str(a)) for a in VCAS_ACTIONS.values()]
                + [len(str(a)) for a in HCAS_ACTIONS.values()]
            )
            + 2  # For the whitespace left and right of a string
        )

        logger.info("ACAS X initialized...")
        self.print_status()

    def register_connection(self, connection: PropsConnection) -> None:
        """Register a connection with the CAS.

        Args:
            connection (PropsConnection): The connection to register.
        """
        self.acasx.register_connection(connection)

    def autoavoid(self) -> None:
        """Execute the autoavoid action.

        This method will execute the autoavoid action based on the
        current autoavoid mode and advisory.

        Raises:
            ValueError: If the autoavoid mode is not/wrongly set.
        """
        if self.autoavoid_cfg.mode not in ("hcas", "vcas"):
            raise ValueError("Autoavoid mode not set")

        if self.autoavoid_cfg.mode == "hcas":
            self._hcas_autoavoid()
        elif self.autoavoid_cfg.mode == "vcas":
            self._vcas_autoavoid()

    def _hcas_autoavoid(self):
        """Execute the HCAS autoavoid action."""
        self.action = HCAS_ACTIONS[self.hcas_adv]
        self.command = self.action if not isinstance(self.action, str) else None

        if self.action is None or (self.action == "reset" and self.hcas_reset):
            return

        if self.action == "reset":
            self.acasx.conn.set_prop(
                "/autopilot/settings/target-bank-angle-deg",
                self.leveled_target_bank_angle_deg,
            )
            self.heading_lock_set = False
            self.hcas_reset = True
            return

        self.hcas_reset = False

        if not self.heading_lock_set:
            self.acasx.conn.set_prop("/autopilot/locks/heading", "wing-leveler")
            self.heading_lock_set = True

        v_tas = self.acasx.ownship.true_airspeed
        r = self.action * ureg.degree / ureg.second
        phi = (
            -math.atan(v_tas * r / self.g) * ureg.radian
        )  # a positive phi is a right turn but this is a negative turn rate

        self.acasx.conn.set_prop(
            "/autopilot/settings/target-bank-angle-deg",
            phi.to(ureg.degree).magnitude,
        )
        self.command = phi.to(ureg.degree).magnitude

    def _vcas_autoavoid(self):
        """Execute the VCAS autoavoid action."""
        self.action = VCAS_ACTIONS[self.vcas_adv]
        self.command = self.action if not isinstance(self.action, str) else None

        if self.action is None or (self.action == "reset" and self.vcas_reset):
            return

        if self.action == "reset":
            self.acasx.conn.set_prop(
                "/autopilot/settings/vertical-speed-fpm",
                self.leveled_vertical_speed_fpm,
            )
            self.altitude_lock_set = False
            self.vcas_reset = True
            return

        self.vcas_reset = False

        if not self.altitude_lock_set:
            self.acasx.conn.set_prop("/autopilot/locks/altitude", "vertical-speed-hold")
            self.altitude_lock_set = True

        self.acasx.conn.set_prop("/autopilot/settings/vertical-speed-fpm", self.action)

    def log(self) -> None:
        """Log the current state of the ACAS X.

        This method will log the current state of the ACAS X to log
        folder.

        Raises:
            ValueError: If the topic is not found.
        """
        if not self.logging_initialized:
            self.init_log()

        for topic, file in self.logger_cfg.files.items():
            try:
                if topic == "state":
                    resp = {
                        "hcas": self.get_system_info("hcas"),
                        "vcas": self.get_system_info("vcas"),
                        "timestamp": time.time(),
                    }

                elif topic == "autoavoid":
                    resp = asdict(self.get_autoavoid())
                elif topic == "ownship":
                    resp = asdict(self.get_ownship())
                elif topic == "intruders":
                    resp = {
                        k: v if isinstance(v, (float, int)) else asdict(v)
                        for k, v in self.get_intruders().items()
                    }
                else:
                    raise ValueError(f"Topic `{topic}` not found")
                with open(str(Path(self.log_folder, file).resolve())) as f:
                    lines = f.readlines()
                lines = lines[:-1]
                lines.append(json.dumps(resp, indent=2) + ",\n]")
                Path(self.log_folder, file).open("w").writelines(lines)

            except Exception as e:  # pylint: disable=broad-except
                logger.error(traceback.format_exc() + f"\nError in logging: {e}")

    def init_log(self):
        """Initialize the logging for the ACAS X."""
        self.log_folder = Path(
            Path(pycasx.__file__).parent.parent, self.logger_cfg.log_folder
        )
        if self.logger_cfg.include_date:
            date = time.strftime("%Y-%m-%d-%H-%M-%S")
            self.log_folder = Path(self.log_folder, date)
        self.log_folder.mkdir(parents=True, exist_ok=True)
        for _, file in self.logger_cfg.files.items():
            Path(self.log_folder, file).write_text("[\n]")
        self.logging_initialized = True

    def print_status(self) -> None:
        """Print the status of the ACAS X."""

        def format_title(title: str, max_width: int):
            whitespace = (2 * max_width + 1) - len(title)
            left_space = " " * math.floor(whitespace / 2)
            right_space = " " * math.ceil(whitespace / 2)
            return f"|{left_space}{title}{right_space}|\n"

        def format_line(label: str, value: Any, max_width: int):
            return (
                f"| {label}{' ' * (max_width - (len(label) + 1))}"
                f"| {value}{' ' * (max_width - (len(str(value)) + 1))}|\n"
            )

        top_rule = f"|{'-' * (2*self.max_width+1)}|\n"
        mid_rule = f"|{'-' * self.max_width}|{'-' * self.max_width}|\n"
        bot_rule = f"|{'-' * (2*self.max_width+1)}|"

        acasx_title = format_title("ACAS X", self.max_width)
        acasx_hcas_status = format_line("HCAS", self.hcas_adv.name, self.max_width)
        acasx_vcas_status = format_line("VCAS", self.vcas_adv.name, self.max_width)

        autoavoid_title = format_title("Autoavoid", self.max_width)
        autoavoid_active = format_line(
            "Active", self.autoavoid_cfg.active, self.max_width
        )
        autoavoid_mode = format_line("Mode", self.autoavoid_cfg.mode, self.max_width)
        autoavoid_action = format_line("Action", self.action, self.max_width)
        autoavoid_command = format_line("Command", self.command, self.max_width)

        info_str = (
            "\n"
            f"{top_rule}"
            f"{acasx_title}"
            f"{mid_rule}"
            f"{acasx_hcas_status}"
            f"{acasx_vcas_status}"
            f"{mid_rule}"
            f"{autoavoid_title}"
            f"{mid_rule}"
            f"{autoavoid_active}"
            f"{autoavoid_mode}"
            f"{autoavoid_action}"
            f"{autoavoid_command}"
            f"{bot_rule}"
        )

        logger.info(info_str)

    def get_system_info(self, system_type: Literal["hcas", "vcas"]) -> SystemInfo:
        """Get the information about a CAS system.

        Args:
            system_type (Literal["hcas", "vcas"]): The CAS system to get
                information about.

        Returns:
            SystemInfo: The information about the CAS system.

        Raises:
            HTTPException: If the system type is not found.
        """
        if system_type == "hcas":
            s_adv = self.hcas_adv  # type: ignore
        elif system_type == "vcas":
            s_adv = self.vcas_adv  # type: ignore
        else:
            raise HTTPException(
                status_code=404, detail=f"System `{system_type}` not found"
            )

        return {
            "advisory": {"value": s_adv.value, "name": s_adv.name},
            "connector": self.acasx.conn.__class__.__name__.lower(),  # type: ignore
            "timestamp": time.time(),
        }

    def get_ownship(self) -> ExtendedAircraft:
        """Get the ownship from the ACAS X system.

        Returns:
            ExtendedAircraft: the ownship representation.
        """
        return ExtendedAircraft(
            call_sign=self.acasx.ownship.call_sign,
            altitude=self.acasx.ownship.altitude.to(ureg.foot).magnitude,
            vertical_speed=self.acasx.ownship.vertical_speed.to(
                ureg.foot / ureg.second
            ).magnitude,
            true_airspeed=self.acasx.ownship.true_airspeed.to(ureg.knots).magnitude,
            heading=self.acasx.ownship.heading.to(ureg.degree).magnitude,
            latitude=self.acasx.ownship.latitude.to(ureg.degree).magnitude,
            longitude=self.acasx.ownship.longitude.to(ureg.degree).magnitude,
            timestamp=time.time(),
        )

    def get_intruder(self, call_sign: str) -> ExtendedIntruder:
        """Get an intruder from the ACAS X system.

        Args:
            call_sign (str): The callsign of the intruder.

        Returns:
            ExtendedIntruder: The intruder from the ACAS X system.

        Raises:
            HTTPException: If the intruder is not found.
        """
        if call_sign not in self.acasx.intruders:
            raise HTTPException(
                status_code=404, detail=f"Intruder `{call_sign}` not found"
            )
        return extend_intruder(self.acasx.intruders[call_sign])

    def get_intruders(self) -> Dict[str, Union[ExtendedIntruder, float]]:
        """Get the intruders from the ACAS X system.

        Returns:
            Dict[str, Union[ExtendedIntruder, float]]: The intruders from the
                ACAS X system.
        """
        if not self.acasx.intruders:
            return {}
        intruders: Dict[str, Union[ExtendedIntruder, float]] = {}
        for call_sign, intruder in self.acasx.intruders.items():
            intruders[call_sign] = extend_intruder(intruder)
        intruders["timestamp"] = time.time()
        return intruders

    def get_autoavoid(self) -> AutoavoidInfo:
        """Get the autoavoid status from the ACAS X system.

        Returns:
            AutoavoidInfo: the autoavoid representation.
        """
        return AutoavoidInfo(
            active=self.autoavoid_cfg.active,
            mode=self.autoavoid_cfg.mode,  # type: ignore
            action=self.action,
            command=self.command,
            timestamp=time.time(),
        )

    def single_run(self):
        """Runs a single ACAS X update."""
        try:
            hcas_adv, vcas_adv = self.acasx.advise()
        except Exception as e:  # pylint: disable=broad-except
            logger.error(traceback.format_exc() + f"\nError in ACAS X: {e}")
            hcas_adv = HCASAdvisories.INOP
            vcas_adv = VCASAdvisories.INOP

        self.hcas_adv = hcas_adv
        self.vcas_adv = vcas_adv

        if self.autoavoid_cfg.active:
            self.autoavoid()

        if self.logger_cfg.active:
            self.log()

        self.print_status()

    async def run(self) -> None:
        """Run the ACAS X in a continuous async loop.

        This method will run the ACAS X in a continuous loop, updating
        the advisory every `1/rate` seconds.
        """
        t = time.perf_counter()
        dt = 1 / self.rate
        while True:
            t += dt

            self.single_run()
            await asyncio.sleep(max(0, t - time.perf_counter()))
