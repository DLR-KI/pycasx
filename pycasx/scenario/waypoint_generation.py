# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Module to generate different waypoints."""
from __future__ import annotations

import random

from pycasx.acas import ureg
from pycasx.conf import ScenarioConfig
from pycasx.scenario import GEOD, GeographicCoordinates, WayPointConfig, convert
from pycasx.scenario.calculate_cpa import calculate_cpa


def generate_colliding_waypoints(cfg: ScenarioConfig) -> list[WayPointConfig]:
    """Generate intruder waypoints for a collision course.

    For an easy visualization of the beta distribution, see:
    https://eurekastatistics.com/beta-distribution-pdf-grapher/

    Args:
        cfg (ScenarioConfig): The scenario configuration

    Returns:
        list[WayPointConfig]: The generated waypoints
    """
    cpa = calculate_cpa(cfg)

    altitude = convert(cfg.altitude, "ft") + convert(
        cfg.colliding.altitude.spread, "ft"
    ) * (
        random.betavariate(
            cfg.colliding.altitude.alpha,
            cfg.colliding.altitude.beta,
        )
        - 0.5
    )
    heading = convert(cfg.heading, "deg") + random.uniform(
        convert(cfg.colliding.heading.min_, "deg"),
        convert(cfg.colliding.heading.max_, "deg"),
    )
    speed = random.uniform(
        convert(cfg.colliding.speed.min_, "kt"),
        convert(cfg.colliding.speed.max_, "kt"),
    )

    # We have to cheat here a little bit, because we don't know the
    # exact true airspeed of the ownship as the control algorithm
    # uses the indicated airspeed. That's why we still use the defined
    # airspeed of the ownship but try to sync that up with the
    # randomized airspeed of the intruder.
    dist = (
        (convert(cfg.vc, "kt") * ureg.kt * convert(cfg.time_to_cpa, "s") * ureg.s)
        .to(ureg.meter)
        .magnitude
    )

    lon_start, lat_start, _ = GEOD.fwd(
        lons=cpa.lon,
        lats=cpa.lat,
        az=heading + 180,
        dist=dist,
    )
    start = GeographicCoordinates(lat=lat_start, lon=lon_start)
    lon_end, lat_end, _ = GEOD.fwd(
        lons=cpa.lon,
        lats=cpa.lat,
        az=heading,
        dist=dist,
    )
    end = GeographicCoordinates(lat=lat_end, lon=lon_end)

    waypoints = [
        WayPointConfig(
            name="START",
            lat=start.lat,
            lon=start.lon,
            alt=altitude,
            ktas=speed,
            on_ground=False,
            gear_down=False,
            flaps_down=False,
        ),
        WayPointConfig(
            name="END",
            lat=end.lat,
            lon=end.lon,
            alt=altitude,
            ktas=speed,
            on_ground=False,
            gear_down=False,
            flaps_down=False,
        ),
    ]

    return waypoints


def generate_parallel_waypoints(
    cfg: ScenarioConfig,
) -> list[WayPointConfig]:  # pylint: disable=too-many-locals
    """Generate intruder waypoints that are on a parallel course.

    For an easy visualization of the beta distribution, see:
    https://eurekastatistics.com/beta-distribution-pdf-grapher/

    Args:
        cfg (ScenarioConfig): The scenario configuration

    Returns:
        list[WayPointConfig]: The generated waypoints
    """
    cpa = calculate_cpa(cfg)

    altitude = convert(cfg.altitude, "ft") + convert(
        cfg.colliding.altitude.spread, "ft"
    ) * (
        random.betavariate(
            cfg.parallel.altitude.alpha,
            cfg.parallel.altitude.beta,
        )
        - 0.5
    )
    heading = convert(cfg.heading, "deg") + 180
    speed = random.uniform(
        convert(cfg.parallel.speed.min_, "kt"),
        convert(cfg.parallel.speed.max_, "kt"),
    )

    horizontal_offset = convert(cfg.parallel.horizontal.spread, "m") * (
        random.betavariate(
            cfg.parallel.horizontal.alpha,
            cfg.parallel.horizontal.beta,
        )
        - 0.5
    )

    dist = (
        (speed * ureg.kt * convert(cfg.time_to_cpa, "s") * ureg.s)
        .to(ureg.meter)
        .magnitude
    )

    lon_offset, lat_offset, _ = GEOD.fwd(
        lons=cpa.lon,
        lats=cpa.lat,
        az=convert(cfg.heading, "deg") + 90,
        dist=horizontal_offset,
    )
    offset_cpa = GeographicCoordinates(lat=lat_offset, lon=lon_offset)

    lon_start, lat_start, _ = GEOD.fwd(
        lons=offset_cpa.lon,
        lats=offset_cpa.lat,
        az=heading + 180,
        dist=dist,
    )
    start = GeographicCoordinates(lat=lat_start, lon=lon_start)
    lon_end, lat_end, _ = GEOD.fwd(
        lons=offset_cpa.lon,
        lats=offset_cpa.lat,
        az=heading,
        dist=dist,
    )
    end = GeographicCoordinates(lat=lat_end, lon=lon_end)

    waypoints = [
        WayPointConfig(
            name="START",
            lat=start.lat,
            lon=start.lon,
            alt=altitude,
            ktas=speed,
            on_ground=False,
            gear_down=False,
            flaps_down=False,
        ),
        WayPointConfig(
            name="END",
            lat=end.lat,
            lon=end.lon,
            alt=altitude,
            ktas=speed,
            on_ground=False,
            gear_down=False,
            flaps_down=False,
        ),
    ]

    return waypoints
