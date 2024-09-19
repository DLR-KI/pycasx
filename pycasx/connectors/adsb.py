# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""ADS-B Sensor Connector."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from flightgear_python.fg_if import HTTPConnection

from pycasx.connectors.protocols import PropsDict


@dataclass
class ADSB:
    """ADS-B Sensor Connector.

    Args:
        host (str): The http host of the FlightGear instance.
        port (int): The http port of the FlightGear instance.

    Attributes:
        host (str): The http host of the FlightGear instance.
        port (int): The http port of the FlightGear instance.
        conn (HTTPConnection): The connection to the FlightGear instance.
    """

    host: str
    port: int
    conn: HTTPConnection = field(init=False)

    def __post_init__(self) -> None:
        """Run post init steps required to finalize the initialization."""
        self.conn = HTTPConnection(self.host, self.port)

    def get_prop(self, prop_str: str) -> Any:
        """Get a property from FlightGear.

        Args:
            prop_str (str): location of the property, should always be
                relative to the root (``/``)

        Returns:
            Any: the value of the property. If FG tells us what the type
                is we will pre-convert it (i.e. make an int from a string)
        """
        return self.conn.get_prop(prop_str)

    def set_prop(self, prop_str: str, value: Any) -> None:
        """Set a property in FlightGear.

        Args:
            prop_str (str): location of the property, should always be
                relative to the root (``/``)
            value (Any): value to set the property to. Must be convertible
                to ``str``
        """
        self.conn.set_prop(prop_str, value)

    def list_props(self, path: str = "/", recurse_limit: int | None = 0) -> PropsDict:
        r"""List properties in the FlightGear property tree.

        Args:
            path (str): directory to list from, should always be
                relative to the root (``/``)
            recurse_limit (int | None): how many times to recurse into
                subdirectories. 1 (default) is no recursion, 2 is 1
                level deep, etc. Passing in ``None`` disables the
                recursion limit. Be warned that enabling any kind of
                recursion will take a long time!

        Returns:
            PropsDict: dictionary with keys:

            * ``directories``: List of directories, absolute path
            * ``properties``: Dictionary with property name as the key
                (absolute path), value as their value.

        Example for ``list_props('/position', recurse_limit=0)``:

        .. code-block:: python

            {
                'directories': [
                    '/position/model'
                ],
                'properties': {
                    '/position/altitude-agl-ft': 3.148566963,
                    '/position/altitude-agl-m': 0.9596832103,
                    '/position/altitude-ft': 3491.986254,
                    '/position/ground-elev-ft': 3488.469757,
                    '/position/ground-elev-m': 1063.285582,
                    '/position/latitude-deg': 0.104476136,
                    '/position/latitude-string': '0*06\\'16.1"N',
                    '/position/longitude-deg': 100.023135,
                    '/position/longitude-string': '100*01\\'23.3"E',
                    '/position/sea-level-radius-ft': 20925646.09
                }
            }
        """
        return self.conn.list_props(path, recurse_limit)  # type: ignore
