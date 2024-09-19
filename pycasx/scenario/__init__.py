# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Scenario generation module for pycasx."""
from __future__ import annotations

from dataclasses import dataclass
from typing import overload

import pyproj

from pycasx.acas import ureg

GEOD = pyproj.Geod(ellps="WGS84")


# REUSE-IgnoreStart
SPDX_FILE_COPYRIGHT_TEXT = (
    "SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>"
)
SPDX_LICENSE_IDENTIFIER = "SPDX-License-Identifier: MIT"
# REUSE-IgnoreStop

HEADLESS_OPTIONS = """# HEADLESS-START
--geometry=1x1
--disable-sound
--disable-terrasync
--disable-splash-screen
--fog-fastest
--disable-specular-highlight
--disable-random-objects
--disable-clouds
--disable-clouds3d
--disable-distance-attenuation
--disable-real-weather-fetch
--disable-random-vegetation
--disable-random-buildings
--disable-horizon-effect
--prop:/sim/rendering/particles=0
--prop:/sim/rendering/multi-sample-buffers=1
--prop:/sim/rendering/multi-samples=2
--prop:/sim/rendering/draw-mask/clouds=false
--prop:/sim/rendering/draw-mask/aircraft=false
--prop:/sim/rendering/draw-mask/models=false
--prop:/sim/rendering/draw-mask/terrain=false
--prop:/sim/rendering/random-vegetation=0
--prop:/sim/rendering/random-buildings=0
--prop:/sim/rendering/texture-compression=off
--prop:/sim/rendering/quality-level=0
--prop:/sim/rendering/shaders/quality-level=0
# HEADLESS-END
"""


@dataclass
class WayPointConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration of a single waypoint.

    Attributes:
        name (str): Name of the waypoint
        lat (float): The waypoint's latitude
        lon (float): The waypoint's longitude
        alt (float): The aircraft's **true altitude**
        ktas (float): The the aircraft's **true airspeed**
        on_ground (bool): Whether the aircraft in on the ground
        gear_down (bool): Whether the gear is down
        flaps_down (bool): Whether the flaps are down
    """

    name: str
    lat: float
    lon: float
    alt: float
    ktas: float
    on_ground: bool
    gear_down: bool
    flaps_down: bool


@dataclass
class GeographicCoordinates:
    """The latitude and longitude of an aircraft.

    Attributes:
        lat (float): the latitude of the aircraft.
        lon (float): the longitude of the aircraft.
    """

    lat: float
    lon: float


@overload
def convert(value: int | float) -> float: ...


@overload
def convert(value: int | float, unit: str) -> float: ...


@overload
def convert(value: str, unit: str) -> float: ...


def convert(value: int | float | str, unit: str = "") -> float:
    """Convert a value to a specific unit.

    This function takes a value and a unit and converts the value to the
    given unit. If the value is already a number (int | float), it is
    directly returned. If the value is a string, it is converted to a
    quantity and then to the given unit.
    This is useful to read values from the configuration file and
    convert them to the correct unit.

    Args:
        value (int | float | str): The value to convert
        unit (str): The unit to convert to

    Returns:
        float: The converted value
    """
    if isinstance(value, (int, float)):
        return float(value)
    else:
        return float(ureg.Quantity(value).to(unit).magnitude)  # type: ignore
