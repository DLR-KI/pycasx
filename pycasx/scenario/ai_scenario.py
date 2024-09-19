# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Module to generate the AI Scenario XML string."""
from __future__ import annotations

import uuid
from pathlib import Path

from lxml import etree

from pycasx.conf import ScenarioConfig
from pycasx.scenario import SPDX_FILE_COPYRIGHT_TEXT, SPDX_LICENSE_IDENTIFIER


def create_ai_scenario_xml(
    cfg: ScenarioConfig, _uuid: uuid.UUID, flightplans: list[Path]
) -> str:
    """Create the scenario file.

    Args:
        cfg (ScenarioConfig): The scenario configuration
        _uuid (uuid.UUID): The UUID of the scenario
        flightplans (list[Path]): The flightplan files of the intruders

    Returns:
        str: The XML file as a string
    """
    root = etree.Element("PropertyList")
    comment = etree.Comment(
        f"\n{SPDX_FILE_COPYRIGHT_TEXT}\n\n{SPDX_LICENSE_IDENTIFIER}\n"
    )
    root.addprevious(comment)

    scenario = etree.SubElement(root, "scenario")

    etree.SubElement(scenario, "name").text = str(_uuid)
    etree.SubElement(scenario, "description").text = (
        f"UUID: {_uuid}, n_intruders: {len(flightplans)}"
    )

    for i, fp in enumerate(flightplans):
        entry = etree.SubElement(scenario, "entry")
        etree.SubElement(entry, "callsign").text = f"INTRUDER_{i+1}"
        etree.SubElement(entry, "type").text = cfg.intruder.type_
        etree.SubElement(entry, "class").text = cfg.intruder.class_
        etree.SubElement(entry, "model").text = cfg.intruder.model
        etree.SubElement(entry, "flightplan").text = f"{fp.stem}{fp.suffix}"
        etree.SubElement(entry, "repeat").text = "0"

    return etree.tostring(
        etree.ElementTree(root),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    ).decode("utf-8")
