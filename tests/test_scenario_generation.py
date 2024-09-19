# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import unittest
import unittest.mock
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pyproj
import pytest
from lxml import etree
from parameterized import parameterized
from shapely.geometry import LineString

from pycasx.acas import ureg
from pycasx.cli import ASSETS_PATH
from pycasx.cli.scenarios import create_scenarios as cli_create_scenarios
from pycasx.conf import (
    BetaDistributionConfig,
    CollidingConfig,
    IntruderConfig,
    MinMaxConfig,
    ParallelConfig,
    ScenarioConfig,
    TelnetConfig,
    WeightsConfig,
)
from pycasx.scenario import (
    GEOD,
    HEADLESS_OPTIONS,
    SPDX_FILE_COPYRIGHT_TEXT,
    SPDX_LICENSE_IDENTIFIER,
    GeographicCoordinates,
    WayPointConfig,
    convert,
)
from pycasx.scenario.ai_scenario import create_ai_scenario_xml
from pycasx.scenario.calculate_cpa import calculate_cpa
from pycasx.scenario.fgfs_config import create_fgfs_config
from pycasx.scenario.flightplan import create_flightplan_xml
from pycasx.scenario.scenario import create_scenario, create_scenarios
from pycasx.scenario.waypoint_generation import (
    generate_colliding_waypoints,
    generate_parallel_waypoints,
)


def line_intersection(
    lon01: float,
    lat01: float,
    lon02: float,
    lat02: float,
    lon11: float,
    lat11: float,
    lon12: float,
    lat12: float,
) -> tuple[float, float] | None:
    """Test whether two lines intersect.

    Args:
        lon01 (float): Longitude of the first point of the first line
        lat01 (float): Latitude of the first point of the first line
        lon02 (float): Longitude of the second point of the first line
        lat02 (float): Latitude of the second point of the first line
        lon11 (float): Longitude of the first point of the second line
        lat11 (float): Latitude of the first point of the second line
        lon12 (float): Longitude of the second point of the second line
        lat12 (float): Latitude of the second point of the second line

    Returns:
        tuple[float, float] | None: The intersection point (lon, lat)
            if the lines intersect, else None
    """

    # Define the coordinate system
    crs = pyproj.CRS("WGS84")

    # Create a transformer to convert from geographic to cartesian coordinates
    transformer_to_cartesian = pyproj.Transformer.from_crs(
        crs, crs.geodetic_crs, always_xy=True
    )

    # Convert the lines to cartesian coordinates
    line1_cartesian = LineString(
        transformer_to_cartesian.transform(*point)
        for point in [(lon01, lat01), (lon02, lat02)]
    )
    line2_cartesian = LineString(
        transformer_to_cartesian.transform(*point)
        for point in [(lon11, lat11), (lon12, lat12)]
    )

    # Calculate the intersection of the lines
    intersection = line1_cartesian.intersection(line2_cartesian)

    if intersection.is_empty:
        # The lines do not intersect
        return None

    # Create a transformer to convert from cartesian to geographic coordinates
    transformer_to_geographic = pyproj.Transformer.from_crs(
        crs.geodetic_crs, crs, always_xy=True
    )

    # Convert the intersection point to geographic coordinates
    intersection_geographic = transformer_to_geographic.transform(
        *intersection.coords[0]
    )

    return intersection_geographic


class TestScenarioGeneration(unittest.TestCase):
    def setUp(self) -> None:
        self._uuid = uuid.uuid4()
        self.flightplans = [Path(f"flightplan_{i}.xml") for i in range(3)]
        self.cfg = ScenarioConfig(
            dest_folder=".",
            n_scenarios=3,
            sort_by_uuid=True,
            time_to_cpa=60.0,
            weights=WeightsConfig(
                colliding=1,
                parallel=1,
                skewed=0,
            ),
            colliding=CollidingConfig(
                altitude=BetaDistributionConfig(
                    spread=1000,
                    alpha=5,
                    beta=5,
                ),
                heading=MinMaxConfig(
                    min_=45,
                    max_=135,
                ),
                speed=MinMaxConfig(
                    min_=200,
                    max_=300,
                ),
            ),
            parallel=ParallelConfig(
                altitude=BetaDistributionConfig(
                    spread=1000,
                    alpha=5,
                    beta=5,
                ),
                horizontal=BetaDistributionConfig(
                    spread=1000,
                    alpha=5,
                    beta=5,
                ),
                speed=MinMaxConfig(
                    min_=200,
                    max_=300,
                ),
            ),
            headless=True,
            disable_sound=False,
            httpd=8080,
            telnet=TelnetConfig(
                port=1337,
                rate=150,
            ),
            aircraft="test_aircraft",
            altitude=1000.0,
            heading=90.0,
            lat=50.0,
            lon=10.0,
            pitch=0.0,
            roll=0.0,
            vc=200.0,
            config=["config1", "config2"],
            prop={"test_prop": "test_value", "test_prop2": 100.0},
            timeofday="noon",
            wind="0@0",
            min_intruders=2,
            max_intruders=10,
            intruder=IntruderConfig(
                type_="aircraft",
                class_="jet",
                model="Aircraft/737-200/Models/737-200.xml",
            ),
        )
        self.waypoints = [
            WayPointConfig(
                name="START",
                lat=10.0,
                lon=11.0,
                alt=30000.0,
                ktas=500.0,
                on_ground=False,
                gear_down=False,
                flaps_down=False,
            ),
            WayPointConfig(
                name="END",
                lat=20.0,
                lon=42.0,
                alt=25000.0,
                ktas=200.0,
                on_ground=False,
                gear_down=False,
                flaps_down=False,
            ),
        ]

    def test_calculate_cpa_return_geographic_coordinates(self):
        result = calculate_cpa(self.cfg)
        self.assertIsInstance(result, GeographicCoordinates)

    def test_calculate_cpa_return_tuple_lat_lon(self):
        result = calculate_cpa(self.cfg, return_tuple=True, order="lat,lon")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        for value in result:
            self.assertIsInstance(value, float)

    def test_calculate_cpa_return_tuple_lon_lat(self):
        result = calculate_cpa(self.cfg, return_tuple=True, order="lon,lat")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        for value in result:
            self.assertIsInstance(value, float)

    def test_calculate_cpa_return_tuple_default_lat_lon(self):
        result = calculate_cpa(self.cfg)
        result_tuple_lat_lon = calculate_cpa(self.cfg, return_tuple=True)
        self.assertEqual(result.lat, result_tuple_lat_lon[0])
        self.assertNotEqual(result.lon, result_tuple_lat_lon[0])
        self.assertEqual(result.lon, result_tuple_lat_lon[1])
        self.assertNotEqual(result.lat, result_tuple_lat_lon[1])

    def test_calculate_cpa_return_values_equal(self):
        result = calculate_cpa(self.cfg)
        result_tuple_lat_lon = calculate_cpa(
            self.cfg, return_tuple=True, order="lat,lon"
        )
        result_tuple_lon_lat = calculate_cpa(
            self.cfg, return_tuple=True, order="lon,lat"
        )
        self.assertEqual(result.lat, result_tuple_lat_lon[0])
        self.assertEqual(result.lon, result_tuple_lat_lon[1])
        self.assertEqual(result.lat, result_tuple_lon_lat[1])
        self.assertEqual(result.lon, result_tuple_lon_lat[0])

    def test_create_fgfs_config_license_info(self):
        result = create_fgfs_config(self.cfg)
        self.assertIn("SPDX-FileCopyrightText:", result)
        self.assertIn(SPDX_FILE_COPYRIGHT_TEXT, result)
        self.assertIn("SPDX-License-Identifier:", result)
        self.assertIn(SPDX_LICENSE_IDENTIFIER, result)

    def test_create_fgfs_config_ownship_info(self):
        result = create_fgfs_config(self.cfg)
        self.assertIn(f"--aircraft={self.cfg.aircraft}", result)
        self.assertIn(f"--lat={self.cfg.lat}", result)
        self.assertIn(f"--lon={self.cfg.lon}", result)
        self.assertIn(f"--altitude={self.cfg.altitude}", result)
        self.assertIn(f"--heading={self.cfg.heading}", result)
        self.assertIn(f"--vc={self.cfg.vc}", result)
        self.assertIn(f"--roll={self.cfg.roll}", result)
        self.assertIn(f"--pitch={self.cfg.pitch}", result)

    def test_create_fgfs_config_fgfs_info(self):
        result = create_fgfs_config(self.cfg)
        self.assertIn(f"--timeofday={self.cfg.timeofday}", result)
        self.assertIn(f"--wind={self.cfg.wind}", result)
        self.assertIn(f"--httpd={self.cfg.httpd}", result)

    def test_create_fgfs_config_options(self):
        result = create_fgfs_config(self.cfg)
        for config_option in self.cfg.config:
            self.assertIn(f"--config={config_option}", result)

    def test_create_fgfs_config_props(self):
        result = create_fgfs_config(self.cfg)
        for prop_key, prop_value in self.cfg.prop.items():
            self.assertIn(f"--prop:{prop_key}={prop_value}", result)

    @parameterized.expand(
        (
            (None,),
            ((1234, 5678),),
        )
    )
    def test_create_fgfs_config_fgfs_optional_telnet(
        self,
        telnet_tuple: tuple[int, int] | None,
    ):
        if telnet_tuple is not None:
            port, rate = telnet_tuple
            self.cfg.telnet = TelnetConfig(port=port, rate=rate)
        else:
            self.cfg.telnet = None
        result = create_fgfs_config(self.cfg)
        if telnet_tuple is not None:
            self.assertIn(f"--telnet=,,{telnet_tuple[1]},,{telnet_tuple[0]},", result)
        else:
            self.assertNotIn("--telnet", result)

    @parameterized.expand(((True,), (False,)))
    def test_create_fgfs_config_headless(self, headless: bool):
        self.cfg.headless = headless
        result = create_fgfs_config(self.cfg)

        if self.cfg.headless:
            self.assertIn(HEADLESS_OPTIONS, result)
        else:
            self.assertNotIn(HEADLESS_OPTIONS, result)

    @parameterized.expand(((True,), (False,)))
    def test_create_fgfs_config_disable_sound(self, disable_sound: bool):
        self.cfg.disable_sound = disable_sound
        self.cfg.headless = False  # Headless overwrites disable_sound
        result = create_fgfs_config(self.cfg)

        if self.cfg.disable_sound:
            self.assertNotIn("--enable-sound", result)
            self.assertIn("--disable-sound", result)
        else:
            self.assertIn("--enable-sound", result)
            self.assertNotIn("--disable-sound", result)

    def test_create_flightplan_xml_xml_header(self):
        result = create_flightplan_xml(self.waypoints)
        self.assertIn("<?xml version='1.0' encoding='UTF-8'?>", result)

    def test_create_flightplan_xml_license_info(self):
        result = create_flightplan_xml(self.waypoints)
        self.assertIn("SPDX-FileCopyrightText:", result)
        self.assertIn(SPDX_FILE_COPYRIGHT_TEXT, result)
        self.assertIn("SPDX-License-Identifier:", result)
        self.assertIn(SPDX_LICENSE_IDENTIFIER, result)

    def test_create_flightplan_xml_is_valid(self):
        result = create_flightplan_xml(self.waypoints)

        # Check that the root element is "PropertyList"
        root = etree.fromstring(str.encode(result))
        self.assertEqual(root.tag, "PropertyList")

        # Check that the first child of the root is "flightplan"
        flightplan = root.find("flightplan")
        self.assertIsNotNone(flightplan)

        # Check that the flightplan contains the correct number of waypoints
        waypoints = flightplan.findall("wpt")
        self.assertEqual(len(waypoints), len(self.waypoints))

        # Check that each waypoint has the correct attributes
        for i, waypoint in enumerate(waypoints):
            self.assertIsNotNone(waypoint)
            self.assertEqual(waypoint.find("name").text, self.waypoints[i].name)
            self.assertEqual(float(waypoint.find("lat").text), self.waypoints[i].lat)
            self.assertEqual(float(waypoint.find("lon").text), self.waypoints[i].lon)
            self.assertEqual(float(waypoint.find("alt").text), self.waypoints[i].alt)
            self.assertEqual(float(waypoint.find("ktas").text), self.waypoints[i].ktas)
            self.assertEqual(
                waypoint.find("on-ground").text.lower(),
                str(self.waypoints[i].on_ground).lower(),
            )
            self.assertEqual(
                waypoint.find("gear-down").text.lower(),
                str(self.waypoints[i].gear_down).lower(),
            )
            self.assertEqual(
                waypoint.find("flaps-down").text.lower(),
                str(self.waypoints[i].flaps_down).lower(),
            )

    def test_create_ai_scenario_xml_header(self):
        result = create_ai_scenario_xml(self.cfg, self._uuid, self.flightplans)
        self.assertIn("<?xml version='1.0' encoding='UTF-8'?>", result)

    def test_create_ai_scenario_license_info(self):
        result = create_ai_scenario_xml(self.cfg, self._uuid, self.flightplans)
        self.assertIn("SPDX-FileCopyrightText:", result)
        self.assertIn(SPDX_FILE_COPYRIGHT_TEXT, result)
        self.assertIn("SPDX-License-Identifier:", result)
        self.assertIn(SPDX_LICENSE_IDENTIFIER, result)

    def test_create_ai_scenario_is_valid(self):
        result = create_ai_scenario_xml(self.cfg, self._uuid, self.flightplans)
        root = etree.fromstring(str.encode(result))

        # Check that the root element is "PropertyList"
        self.assertEqual(root.tag, "PropertyList")

        # Check that the first child of the root is "scenario"
        scenario = root.find("scenario")
        self.assertIsNotNone(scenario)

        # Check that the scenario contains the correct number of entries
        entries = scenario.findall("entry")
        self.assertEqual(len(entries), len(self.flightplans))

        # Check that each entry has the correct attributes
        for i, entry in enumerate(entries):
            self.assertEqual(entry.find("callsign").text, f"INTRUDER_{i+1}")
            self.assertEqual(entry.find("type").text, self.cfg.intruder.type_)
            self.assertEqual(entry.find("class").text, self.cfg.intruder.class_)
            self.assertEqual(entry.find("model").text, self.cfg.intruder.model)
            self.assertEqual(
                entry.find("flightplan").text,
                f"{self.flightplans[i].stem}{self.flightplans[i].suffix}",
            )
            self.assertEqual(entry.find("repeat").text, "0")

    def test_generate_colliding_waypoints_returns_waypoints(self):
        waypoints = generate_colliding_waypoints(self.cfg)
        self.assertIsInstance(waypoints, list)
        self.assertTrue(all(isinstance(wp, WayPointConfig) for wp in waypoints))

    def test_generate_colliding_waypoints_returns_two_waypoints(self):
        waypoints = generate_colliding_waypoints(self.cfg)
        self.assertEqual(len(waypoints), 2)

    def test_generate_colliding_waypoints_correct_names(self):
        waypoints = generate_colliding_waypoints(self.cfg)
        self.assertEqual(waypoints[0].name, "START")
        self.assertEqual(waypoints[1].name, "END")

    def test_generate_colliding_waypoints_correct_ktas(self):
        waypoints = generate_colliding_waypoints(self.cfg)
        self.assertTrue(
            convert(self.cfg.colliding.speed.min_, "kt") <= waypoints[0].ktas
            and waypoints[0].ktas <= convert(self.cfg.colliding.speed.max_, "kt")
        )
        self.assertTrue(
            convert(self.cfg.colliding.speed.min_, "kt") <= waypoints[1].ktas
            and waypoints[1].ktas <= convert(self.cfg.colliding.speed.max_, "kt")
        )
        self.assertEqual(waypoints[0].ktas, waypoints[1].ktas)

    def test_generate_colliding_waypoints_constant_altitude(self):
        waypoints = generate_colliding_waypoints(self.cfg)
        self.assertEqual(waypoints[0].alt, waypoints[1].alt)

    def test_generate_colliding_waypoints_correct_heading(self):
        waypoints = generate_parallel_waypoints(self.cfg)
        az, _, _ = GEOD.inv(
            waypoints[0].lon,
            waypoints[0].lat,
            waypoints[1].lon,
            waypoints[1].lat,
        )
        az = az % 360
        heading = self.cfg.heading % 360
        self.assertGreaterEqual(az, heading - self.cfg.parallel.horizontal.spread / 2)
        self.assertLessEqual(az, heading + self.cfg.parallel.horizontal.spread / 2)

    def test_generate_colliding_waypoints_altitude_in_range(self):
        waypoints = generate_colliding_waypoints(self.cfg)
        self.assertGreaterEqual(
            waypoints[0].alt, self.cfg.altitude - self.cfg.colliding.altitude.spread / 2
        )
        self.assertLessEqual(
            waypoints[0].alt, self.cfg.altitude + self.cfg.colliding.altitude.spread / 2
        )
        self.assertGreaterEqual(
            waypoints[1].alt, self.cfg.altitude - self.cfg.colliding.altitude.spread / 2
        )
        self.assertLessEqual(
            waypoints[1].alt, self.cfg.altitude + self.cfg.colliding.altitude.spread / 2
        )

    def test_generate_colliding_waypoints_correct_properties(self):
        waypoints = generate_colliding_waypoints(self.cfg)
        self.assertFalse(waypoints[0].on_ground)
        self.assertFalse(waypoints[0].gear_down)
        self.assertFalse(waypoints[0].flaps_down)
        self.assertFalse(waypoints[1].on_ground)
        self.assertFalse(waypoints[1].gear_down)
        self.assertFalse(waypoints[1].flaps_down)

    def test_generate_colliding_waypoints_waypoints_intersects_ownship_at_cpa(self):
        for _ in range(100):
            waypoints = generate_colliding_waypoints(self.cfg)

            intruder_start = (waypoints[0].lon, waypoints[0].lat)
            intruder_end = (waypoints[1].lon, waypoints[1].lat)
            ownship_start = (self.cfg.lon, self.cfg.lat)
            cpa = calculate_cpa(self.cfg)
            lon_, lat_, _ = GEOD.fwd(
                lons=cpa.lon,
                lats=cpa.lat,
                az=self.cfg.heading,
                dist=(self.cfg.vc * ureg.kt * self.cfg.time_to_cpa * ureg.s)
                .to(ureg.meter)
                .magnitude,
            )
            ownship_end = (lon_, lat_)
            intersection = line_intersection(
                ownship_start[0],
                ownship_start[1],
                ownship_end[0],
                ownship_end[1],
                intruder_start[0],
                intruder_start[1],
                intruder_end[0],
                intruder_end[1],
            )
            self.assertIsNotNone(intersection)
            self.assertAlmostEqual(intersection[0], cpa.lon, places=3)
            self.assertAlmostEqual(intersection[1], cpa.lat, places=3)

    def test_generate_parallel_waypoints_returns_waypoints(self):
        waypoints = generate_parallel_waypoints(self.cfg)
        self.assertIsInstance(waypoints, list)
        self.assertTrue(all(isinstance(wp, WayPointConfig) for wp in waypoints))

    def test_generate_parallel_waypoints_returns_two_waypoints(self):
        waypoints = generate_parallel_waypoints(self.cfg)
        self.assertEqual(len(waypoints), 2)

    def test_generate_parallel_waypoints_correct_names(self):
        waypoints = generate_parallel_waypoints(self.cfg)
        self.assertEqual(waypoints[0].name, "START")
        self.assertEqual(waypoints[1].name, "END")

    def test_generate_parallel_waypoints_correct_ktas(self):
        waypoints = generate_parallel_waypoints(self.cfg)
        self.assertTrue(
            convert(self.cfg.parallel.speed.min_, "kt") <= waypoints[0].ktas
            and waypoints[0].ktas <= convert(self.cfg.parallel.speed.max_, "kt")
        )
        self.assertTrue(
            convert(self.cfg.parallel.speed.min_, "kt") <= waypoints[1].ktas
            and waypoints[1].ktas <= convert(self.cfg.parallel.speed.max_, "kt")
        )
        self.assertEqual(waypoints[0].ktas, waypoints[1].ktas)

    def test_generate_parallel_waypoints_constant_altitude(self):
        waypoints = generate_parallel_waypoints(self.cfg)
        self.assertEqual(waypoints[0].alt, waypoints[1].alt)

    def test_generate_parallel_waypoints_correct_heading(self):
        waypoints = generate_parallel_waypoints(self.cfg)
        az, _, _ = GEOD.inv(
            waypoints[0].lon,
            waypoints[0].lat,
            waypoints[1].lon,
            waypoints[1].lat,
        )
        az = az % 360
        self.assertAlmostEqual(az, self.cfg.heading + 180, delta=0.1)

    def test_generate_parallel_waypoints_correct_properties(self):
        waypoints = generate_parallel_waypoints(self.cfg)
        self.assertFalse(waypoints[0].on_ground)
        self.assertFalse(waypoints[0].gear_down)
        self.assertFalse(waypoints[0].flaps_down)
        self.assertFalse(waypoints[1].on_ground)
        self.assertFalse(waypoints[1].gear_down)
        self.assertFalse(waypoints[1].flaps_down)

    @pytest.mark.skip(
        reason="Currently not working due to problem with different speeds"
    )
    def test_generate_parallel_waypoints_no_intersection(self):
        for _ in range(100):
            waypoints = generate_parallel_waypoints(self.cfg)
            # Ensure no intersection between ownship start -> ownship
            # end and intruder start -> intruder end
            intruder_start = (waypoints[0].lon, waypoints[0].lat)
            intruder_end = (waypoints[1].lon, waypoints[1].lat)
            ownship_start = (self.cfg.lon, self.cfg.lat)
            lon_, lat_, _ = GEOD.fwd(
                lons=self.cfg.lon,
                lats=self.cfg.lat,
                az=self.cfg.heading,
                dist=2
                * (self.cfg.vc * ureg.kt * self.cfg.time_to_cpa * ureg.s)
                .to(ureg.meter)
                .magnitude,
            )
            ownship_end = (lon_, lat_)

            # If the distance between the ownship start/end and the
            # intruder end/start is less than 10m, the lines might
            # intersect due to numerical errors
            _, _, dist1 = GEOD.inv(
                ownship_start[0], ownship_start[1], intruder_end[0], intruder_end[1]
            )
            _, _, dist2 = GEOD.inv(
                ownship_end[0], ownship_end[1], intruder_start[0], intruder_start[1]
            )
            if dist1 < 10 or dist2 < 10:
                continue

            self.assertIsNone(
                line_intersection(
                    ownship_start[0],
                    ownship_start[1],
                    ownship_end[0],
                    ownship_end[1],
                    intruder_start[0],
                    intruder_start[1],
                    intruder_end[0],
                    intruder_end[1],
                )
            )

    @patch("pycasx.scenario.scenario.uuid.uuid4")
    @patch("pycasx.scenario.scenario.random.randint")
    @patch("pycasx.scenario.scenario.random.choices")
    @patch("pycasx.scenario.scenario.create_fgfs_config")
    @patch("pycasx.scenario.scenario.calculate_cpa")
    @patch("pycasx.scenario.scenario.create_flightplan_xml")
    @patch("pycasx.scenario.scenario.create_ai_scenario_xml")
    @patch("pathlib.Path.write_text", new_callable=unittest.mock.mock_open)
    @patch("pathlib.Path.mkdir")
    def test_create_scenario(
        self,
        mock_mkdir: MagicMock,
        mock_write_text: MagicMock,
        mock_create_ai_scenario_xml: MagicMock,
        mock_create_flightplan_xml: MagicMock,
        mock_calculate_cpa: MagicMock,
        mock_create_fgfs_config: MagicMock,
        mock_choices: MagicMock,
        mock_randint: MagicMock,
        mock_uuid: MagicMock,
    ):
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        mock_randint.return_value = 5
        self.cfg.min_intruders = mock_randint.return_value
        self.cfg.max_intruders = mock_randint.return_value
        mock_create_fgfs_config.return_value = "fgfs_config"
        mock_calculate_cpa.return_value = MagicMock(lat=50.0, lon=10.0)
        mock_choices.return_value = [MagicMock()]
        mock_create_flightplan_xml.return_value = "flightplan_xml"
        mock_create_ai_scenario_xml.return_value = "ai_scenario_xml"

        create_scenario(self.cfg)

        # Check that the mock functions were called with the expected arguments
        mock_uuid.assert_called_once()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_randint.assert_called_once_with(
            self.cfg.min_intruders, self.cfg.max_intruders
        )
        mock_create_fgfs_config.assert_called_once_with(self.cfg)
        mock_calculate_cpa.assert_called_with(self.cfg)
        mock_choices.assert_called_with(
            population=[generate_colliding_waypoints, generate_parallel_waypoints],
            weights=[self.cfg.weights.colliding, self.cfg.weights.parallel],
            k=1,
        )
        mock_create_flightplan_xml.assert_called()
        mock_create_ai_scenario_xml.assert_called()
        mock_create_ai_scenario_xml.assert_called_once_with(
            self.cfg,
            mock_uuid.return_value,
            [
                Path(
                    ASSETS_PATH,
                    "scenarios",
                    str(mock_uuid.return_value),
                    "data",
                    "AI",
                    "FlightPlans",
                    f"{mock_uuid.return_value}_fp_{i}.xml",
                )
                for i in range(mock_randint.return_value)
            ],
        )

        # Check that the files were written with the expected content
        mock_write_text.assert_called()

    @patch("pycasx.scenario.scenario.create_scenario")
    def test_create_scenarios(self, mock_create_scenario: MagicMock):
        create_scenarios(self.cfg)
        self.assertEqual(mock_create_scenario.call_count, self.cfg.n_scenarios)
        mock_create_scenario.assert_called_with(self.cfg)

    @patch("pycasx.cli.scenarios.create_scenarios_")
    def test_cli_create_scenarios(self, mock_create_scenarios_: MagicMock):
        cli_create_scenarios(self.cfg)
        mock_create_scenarios_.assert_called_once_with(self.cfg)

    def test_convert_int_to_float(self):
        result = convert(1)
        self.assertIsInstance(result, float)
        self.assertEqual(result, 1.0)

    def test_convert_float_to_float(self):
        result = convert(1.0)
        self.assertIsInstance(result, float)
        self.assertEqual(result, 1.0)

    def test_convert_unit_to_float(self):
        result = convert("1ft", "ft")
        self.assertIsInstance(result, float)
        self.assertEqual(result, 1.0)

    def test_convert_convert_unit(self):
        result = convert("1ft", "m")
        self.assertIsInstance(result, float)
        self.assertEqual(result, ureg.Quantity(1, "foot").to("meter").magnitude)


if __name__ == "__main__":
    unittest.main()
