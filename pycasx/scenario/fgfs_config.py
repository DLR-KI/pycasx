# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Create the FlightGear (FGFS) configuration file."""
from __future__ import annotations

from pycasx.conf import ScenarioConfig
from pycasx.scenario import (
    HEADLESS_OPTIONS,
    SPDX_FILE_COPYRIGHT_TEXT,
    SPDX_LICENSE_IDENTIFIER,
    convert,
)


def create_fgfs_config(cfg: ScenarioConfig) -> str:
    """Create a FlightGear configuration file.

    Args:
        cfg (ScenarioConfig): The scenario configuration

    Returns:
        str: The configuration file as a string
    """
    fgfs_cfg = f"""# {SPDX_FILE_COPYRIGHT_TEXT}
#
# {SPDX_LICENSE_IDENTIFIER}
--aircraft={cfg.aircraft}
--lat={convert(cfg.lat,"deg")}
--lon={convert(cfg.lon,"deg")}
--altitude={convert(cfg.altitude,"ft")}
--heading={convert(cfg.heading,"deg")}
--vc={convert(cfg.vc,"kt")}
--roll={convert(cfg.roll,"deg")}
--pitch={convert(cfg.pitch,"deg")}
--timeofday={cfg.timeofday}
--wind={cfg.wind}
"""

    if cfg.disable_sound:
        fgfs_cfg += "--disable-sound\n"
    else:
        fgfs_cfg += "--enable-sound\n"

    if cfg.httpd:
        fgfs_cfg += f"--httpd={cfg.httpd}\n"
    if cfg.telnet:
        fgfs_cfg += f"--telnet=,,{cfg.telnet.rate},,{cfg.telnet.port},\n"

    if cfg.config is not None:
        for config in cfg.config:
            fgfs_cfg += f"--config={config}"

    for prop_name in cfg.prop:
        fgfs_cfg += f"--prop:{prop_name}={cfg.prop[prop_name]}\n"

    if cfg.headless:
        fgfs_cfg += HEADLESS_OPTIONS

    return fgfs_cfg
