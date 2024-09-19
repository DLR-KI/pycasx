# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Module to generate the flightPlan XML string."""
from __future__ import annotations

from dataclasses import fields

from lxml import etree

from pycasx.scenario import (
    SPDX_FILE_COPYRIGHT_TEXT,
    SPDX_LICENSE_IDENTIFIER,
    WayPointConfig,
)


def create_flightplan_xml(waypoints: list[WayPointConfig]) -> str:
    """Create a flightplan XML file.

    Args:
        waypoints (list[WayPointConfig]): List of waypoints

    Returns:
        str: The XML file as a string
    """
    root = etree.Element("PropertyList")
    comment = etree.Comment(
        f"\n{SPDX_FILE_COPYRIGHT_TEXT}\n\n{SPDX_LICENSE_IDENTIFIER}\n"
    )
    root.addprevious(comment)

    flightplan = etree.SubElement(root, "flightplan")

    for wp in waypoints:
        wpt = etree.SubElement(flightplan, "wpt")

        for field in fields(WayPointConfig):
            etree.SubElement(wpt, field.name.replace("_", "-")).text = str(
                getattr(wp, field.name)
            )

    return etree.tostring(
        etree.ElementTree(root),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    ).decode("utf-8")
