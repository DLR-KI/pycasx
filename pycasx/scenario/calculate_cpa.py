# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Calculate the closest point of approach (CPA) given the time to CPA."""
from __future__ import annotations

from typing import Literal, overload

from pycasx.acas import ureg
from pycasx.conf import ScenarioConfig
from pycasx.scenario import GEOD, GeographicCoordinates, convert


@overload
def calculate_cpa(cfg: ScenarioConfig) -> GeographicCoordinates: ...


@overload
def calculate_cpa(
    cfg: ScenarioConfig,
    return_tuple: Literal[False],
) -> GeographicCoordinates: ...


@overload
def calculate_cpa(
    cfg: ScenarioConfig,
    return_tuple: Literal[True],
) -> tuple[float, float]: ...


@overload
def calculate_cpa(
    cfg: ScenarioConfig,
    return_tuple: Literal[False],
    order: Literal["lat,lon", "lon,lat"],
) -> GeographicCoordinates: ...


@overload
def calculate_cpa(
    cfg: ScenarioConfig,
    return_tuple: Literal[True],
    order: Literal["lat,lon", "lon,lat"],
) -> tuple[float, float]: ...


def calculate_cpa(
    cfg: ScenarioConfig,
    return_tuple: bool = False,
    order: Literal["lat,lon", "lon,lat"] = "lat,lon",
) -> GeographicCoordinates | tuple[float, float]:
    """Calculate the closest point of approach given the initial condition.

    Args:
        cfg (ScenarioConfig): The scenario configuration
        return_tuple (bool): If true, return the result as a tuple.
            Otherwise, return a GeographicCoordinates object.
        order (Literal["lat,lon", "lon,lat"]): The order of the returned
            tuple if `return_tuple` is true.

    Returns:
        GeographicCoordinates | tuple[float, float]: The closest point of
            approach as a GeographicCoordinates object if `return_tuple` is
            false, otherwise as a tuple of latitude and longitude in the
            specified order.
    """
    dist = (
        (convert(cfg.vc, "kt") * ureg.kt * convert(cfg.time_to_cpa, "s") * ureg.s)
        .to(ureg.meter)
        .magnitude
    )
    lon, lat, _ = GEOD.fwd(
        lons=convert(cfg.lon, "deg"),
        lats=convert(cfg.lat, "deg"),
        az=convert(cfg.heading, "deg"),
        dist=dist,
    )
    if not return_tuple:
        return GeographicCoordinates(lat=lat, lon=lon)
    if order == "lat,lon":
        return lat, lon
    return lon, lat
