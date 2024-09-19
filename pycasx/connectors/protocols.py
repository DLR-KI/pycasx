# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Protocols for connectors."""
from __future__ import annotations

from typing import Any, Protocol, TypedDict


class PropsDict(TypedDict):
    """A dictionary of properties returned.

    This dictionary is returned by the ``list_props`` method of the
    ``PropsConnection`` protocol.

    Attributes:
        directories (list[str]): the directories in the property tree.
        properties (dict[str, Any]): the properties in the property tree.
    """

    directories: list[str]
    properties: dict[str, Any]


class PropsConnection(Protocol):
    """Protocol for a connection to the FlightGear Property Tree."""

    def get_prop(self, prop_str: str) -> Any:
        """Get a property from FlightGear.

        For all general available properties, this works the same as
        :meth:`PropsConnection.get_prop`.
        But as we assume we do not have ADS-B data from the intruder
        aka the AI, we will use object detection to get the properties
        under ``/ai/models/aircraft/``.

        Args:
            prop_str (str): location of the property, should always be
                relative to the root (``/``)

        Returns:
            Any: the value of the property. If FG tells us what the type
                is we will pre-convert it (i.e. make an int from a string)
        """

    def set_prop(self, prop_str: str, value: Any) -> None:
        """Set a property in FlightGear.

        Args:
            prop_str (str): location of the property, should always be
                relative to the root (``/``)
            value (Any): value to set the property to. Must be convertible
                to ``str``
        """

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
        ...  # pylint: disable=W2301
