# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Main module to calculate advisories."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, Literal, Protocol, Union

import numpy as np
import numpy.typing as npt
import pint
import pint.facets
import pyproj
from onnx.onnx_ml_pb2 import ModelProto
from torch.fx import GraphModule
from typing_extensions import TypeAlias, TypedDict

from pycasx.tools.NNet.nnet import NNet

ModelDict: TypeAlias = Union[
    Dict[str, NNet], Dict[str, ModelProto], Dict[str, GraphModule]
]
Quantity: TypeAlias = pint.facets.plain.PlainQuantity


DEFAULT_MODEL_PATH = Path(Path(__file__).parent.parent, "assets", "neural_networks")
DEFAULT_HCAS_MODEL_PATH = Path(DEFAULT_MODEL_PATH, "hcas")
DEFAULT_VCAS_MODEL_PATH = Path(DEFAULT_MODEL_PATH, "vcas")


ureg = pint.UnitRegistry(auto_reduce_dimensions=True, cache_folder=":auto:")
pint.set_application_registry(ureg)


def check_for_loss_of_separation(
    ac_1: Aircraft,
    ac_2: Aircraft,
    h_lim: Quantity = 500 * ureg.feet,
    v_lim: Quantity = 100 * ureg.feet,
) -> tuple[bool, bool]:
    """Checks whether two aircraft will lose separation.

    This function determines whether two aircraft will lose separation
    based on their current positions and speeds. The function assumes
    that the aircraft are flying in a straight line without changes in
    speed or direction.

    Args:
        ac_1 (Aircraft): The first aircraft.
        ac_2 (Aircraft): The second aircraft.
        h_lim (Quantity): The horizontal separation limit.
        v_lim (Quantity): The vertical separation limit.

    Returns:
        tuple[bool, bool]: A tuple of two booleans. The first boolean
            indicates whether the aircraft will lose horizontal
            separation, the second boolean indicates whether the
            aircraft will lose vertical separation (True if possible
            collision is detected).

    Raises:
        ValueError: Raised if the horizontal separation is not a length
            or the vertical separation is not a length.
    """
    if not h_lim.is_compatible_with(ureg.foot):
        raise ValueError("Horizontal separation must be a length.")
    if not v_lim.is_compatible_with(ureg.foot):
        raise ValueError("Vertical separation must be a length.")

    geodesic = pyproj.Geod(ellps="WGS84")
    fwd_azimuth, _, dist = geodesic.inv(
        ac_1.longitude.to(ureg.degree).magnitude,
        ac_1.latitude.to(ureg.degree).magnitude,
        ac_2.longitude.to(ureg.degree).magnitude,
        ac_2.latitude.to(ureg.degree).magnitude,
    )
    fwd_azimuth *= ureg.degree
    dist *= ureg.meter

    # Calculate tau according to https://doi.org/10.2514/6.2019-2832
    # Errico, A. and Di Vito, V. (2019): Methodology for Estimation of
    # Closest Point of Approach between Aircraft in ATM
    #
    # Ensure all units are in SI and all variable are magnitude only
    v_1 = ac_1.true_airspeed.to(ureg.meter / ureg.second).magnitude
    v_2 = ac_2.true_airspeed.to(ureg.meter / ureg.second).magnitude
    rho = dist.to(ureg.meter).magnitude
    u = np.array(
        [
            v_1 * math.sin(ac_1.heading.to(ureg.radian).magnitude),
            v_1 * math.cos(ac_1.heading.to(ureg.radian).magnitude),
        ]
    )
    v = np.array(
        [
            v_2 * math.sin(ac_2.heading.to(ureg.radian).magnitude),
            v_2 * math.cos(ac_2.heading.to(ureg.radian).magnitude),
        ]
    )
    w_0 = np.array(
        [
            rho * math.sin(fwd_azimuth.to(ureg.radian).magnitude),
            rho * math.cos(fwd_azimuth.to(ureg.radian).magnitude),
        ]
    )

    tau = float((np.dot(w_0, (u - v))) / (np.dot(u - v, u - v))) * ureg.second

    # Calculate the horizontal and vertical separation
    ac_1_lon, ac_1_lat, _ = geodesic.fwd(
        lons=ac_1.longitude.to(ureg.degree).magnitude,
        lats=ac_1.latitude.to(ureg.degree).magnitude,
        az=ac_1.heading.to(ureg.degree).magnitude,
        dist=v_1 * tau,
    )
    ac_2_lon, ac_2_lat, _ = geodesic.fwd(
        lons=ac_2.longitude.to(ureg.degree).magnitude,
        lats=ac_2.latitude.to(ureg.degree).magnitude,
        az=ac_2.heading.to(ureg.degree).magnitude,
        dist=v_2 * tau,
    )
    _, _, h_sep = geodesic.inv(
        lons1=ac_1_lon,
        lats1=ac_1_lat,
        lons2=ac_2_lon,
        lats2=ac_2_lat,
    )
    h_sep = h_sep * ureg.meter
    v_sep = (ac_1.altitude - ac_2.altitude) + (
        ac_1.vertical_speed - ac_2.vertical_speed
    ) * tau

    return h_sep <= h_lim, v_sep <= v_lim


class HCASAdvisories(IntEnum):
    """The advisories of the HCAS model.

    Attributes:
        INOP: inoperative
        OFF: off
        ACTIVE: active
        COC: clear of conflict
        WL: weak left
        WR: weak right
        SL: strong left
        SR: strong right
    """

    INOP = -3
    OFF = -2
    ACTIVE = -1
    COC = 0
    WL = 1
    WR = 2
    SL = 3
    SR = 4


class VCASAdvisories(IntEnum):
    """The advisories of the VCAS model.

    Attributes:
        INOP: inoperative
        OFF: off
        ACTIVE: active
        COC: clear of conflict
        DNC: do not climb
        DND: do not descend
        DES1500: descend >=1500 ft/min
        CL1500: climb >=1500 ft/min
        SDES1500: strengthen descend to >=1500 ft/min
        SCL1500: strengthen climb to >=1500 ft/min
        SDES2500: strengthen descend to >=2500 ft/min
        SCL2500: strengthen climb to >=2500 ft/min
    """

    INOP = -3
    OFF = -2
    ACTIVE = -1
    COC = 0
    DNC = 1
    DND = 2
    DES1500 = 3
    CL1500 = 4
    SDES1500 = 5
    SCL1500 = 6
    SDES2500 = 7
    SCL2500 = 8


@dataclass(frozen=True)
class HCASStateVariables:
    """The state variables of the HCAS model.

    Attributes:
        rho (Quantity): range to intruder, measured in feet.
        theta (Quantity): bearing angle to intruder, measured in
            degrees.
        psi (Quantity): relative heading angle of intruder, measured in
            degrees.
        v_own (Quantity): ownship speed, measured in feet per second.
        v_int (Quantity): intruder speed, measured in feet per second.
        tau (Quantity): time to loss of vertical separation, measured in
            seconds.
        s_adv (HCASAdvisories): previous advisory.
    """

    rho: Quantity
    theta: Quantity
    psi: Quantity
    v_own: Quantity
    v_int: Quantity
    tau: Quantity
    s_adv: HCASAdvisories


@dataclass(frozen=True)
class VCASStateVariables:
    """The state variables of the VCAS model.

    Attributes:
        h (Quantity): relative intruder altitude, measured in feet.
        hdot_own (Quantity): ownship vertical rate, measured in feet
            per minute.
        hdot_int (Quantity): intruder vertical rate, measured in feet
            per minute.
        tau (Quantity): time to loss of horizontal separation, measured
            in seconds.
        s_adv (VCASAdvisories): previous advisory.
    """

    h: Quantity
    hdot_own: Quantity
    hdot_int: Quantity
    tau: Quantity
    s_adv: VCASAdvisories


@dataclass
class Aircraft:
    """A generic aircraft class to save important state information.

    Although this dataclass relies on Pint for unit handling, default
    units are given in the docstring for each attribute.

    Attributes:
        call_sign (str): The call_sign of the aircraft.
        altitude (Quantity): The aircraft's current altitude, measured
            in feet.
        vertical_speed (Quantity): The aircraft's current vertical
            speed, measured in feet per second.
        true_airspeed (Quantity): The aircraft's current true airspeed,
            measured in knots.
        heading (Quantity): The aircraft's current heading, measured in
            degrees.
        latitude (Quantity): The aircraft's current latitude, measured
            in degrees.
        longitude (Quantity): The aircraft's current longitude, measured
            in degrees.
    """

    call_sign: str
    altitude: Quantity
    vertical_speed: Quantity
    true_airspeed: Quantity
    heading: Quantity
    latitude: Quantity
    longitude: Quantity


@dataclass
class Intruder:
    """An intruder representation relying also on advisory data.

    Attributes:
        aircraft (Aircraft): The aircraft data.
        hcas_advisory (HCASAdvisories): The HCAS advisory.
        vcas_advisory (VCASAdvisories): The VCAS advisory.
        hcas_state_variables (HCASStateVariables): The HCAS state with
            respect to the ownship.
        vcas_state_variables (VCASStateVariables): The VCAS state with
            respect to the ownship.
    """

    aircraft: Aircraft
    hcas_advisory: HCASAdvisories
    vcas_advisory: VCASAdvisories
    hcas_state_variables: HCASStateVariables
    vcas_state_variables: VCASStateVariables

    @property
    def triggers_nmac(self) -> bool:
        """Whether the intruder triggers a near mid-air collision for the
        ownship.

        A near mid-air collision (NMAC) is defined as a loss of
        separation between two aircraft that endangers the safety of the
        aircraft involved. The boundary for a NMAC is defined as 500 ft
        horizontally and 100 ft vertically.

        Returns:
            bool: Whether the intruder triggers a NMAC.
        """
        return (
            self.hcas_state_variables.rho < 500 * ureg.feet
            and abs(self.vcas_state_variables.h) < 100 * ureg.feet
        )


class ACASXProtocol(Protocol):
    """Protocol for an ACAS X model.

    Provides crucial typing info for the mixin classes.
    """

    @property
    def model_dict(self) -> dict[str, Any]:
        """The dictionary of models."""
        ...  # pylint: disable=W2301

    @property
    def ownship(self) -> Aircraft:
        """The ownship's state."""
        ...  # pylint: disable=W2301

    def evaluate(
        self, model_name: str, inputs: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        """Evaluate a CAS model.

        Args:
            model_name (str): Name of the model to evaluate from the
                model dictionary.
            inputs (npt.NDArray[np.float32]): The inputs to the model.

        Returns:
            npt.NDArray[np.float32]: The outputs of the model.

        Raises:
            NotImplementedError: Raised if the requested backend is not
                implemented.
        """
        ...  # pylint: disable=W2301


HCAS_ACTIONS: dict[HCASAdvisories, float | str | None] = {
    HCASAdvisories.INOP: None,
    HCASAdvisories.OFF: None,
    HCASAdvisories.ACTIVE: "reset",
    HCASAdvisories.COC: None,
    HCASAdvisories.WL: 1.5,
    HCASAdvisories.WR: -1.5,
    HCASAdvisories.SL: 3.0,
    HCASAdvisories.SR: -3.0,
}

VCAS_ACTIONS: dict[VCASAdvisories, float | str | None] = {
    VCASAdvisories.INOP: None,
    VCASAdvisories.OFF: None,
    VCASAdvisories.ACTIVE: "reset",
    VCASAdvisories.COC: None,
    VCASAdvisories.DNC: 0.0,
    VCASAdvisories.DND: 0.0,
    VCASAdvisories.DES1500: -1500.0,
    VCASAdvisories.CL1500: 1500.0,
    VCASAdvisories.SDES1500: -2000.0,
    VCASAdvisories.SCL1500: 2000.0,
    VCASAdvisories.SDES2500: -2500.0,
    VCASAdvisories.SCL2500: 2500.0,
}


class AdvisoryDict(TypedDict):
    """The advisory dictionary.

    Attributes:
        value (int): The advisory value.
        name (str): The advisory name.
    """

    value: int
    name: str


class SystemInfo(TypedDict):
    """The information about a CAS system.

    Attributes:
        advisory (AdvisoryDict): The advisory information.
        connector (str): The connector name.
        timestamp (float): The timestamp of the information.
    """

    advisory: AdvisoryDict
    connector: Literal["adsb"]
    timestamp: float


class RootInfo(TypedDict):
    """The information all CAS systems.

    Attributes:
        hcas (SystemInfo): The HCAS information.
        vcas (SystemInfo): The VCAS information.
        timestamp (float): The timestamp of the information.
    """

    hcas: SystemInfo
    vcas: SystemInfo
    timestamp: float


@dataclass(frozen=True)
class APIHCASStateVariables:
    """The state variables of the HCAS model.

    Attributes:
        rho (float): range to intruder, measured in feet.
        theta (float): bearing angle to intruder, measured in degrees.
        psi (float): relative heading angle of intruder, measured in
            degrees.
        v_own (float): ownship speed, measured in feet per second.
        v_int (float): intruder speed, measured in feet per second.
        tau (float): time to loss of vertical separation, measured in
            seconds.
        s_adv (HCASAdvisories): previous advisory.
    """

    rho: float
    theta: float
    psi: float
    v_own: float
    v_int: float
    tau: float
    s_adv: HCASAdvisories


@dataclass(frozen=True)
class APIVCASStateVariables:
    """The state variables of the VCAS model.

    Attributes:
        h (float): relative intruder altitude, measured in feet.
        hdot_own (float): ownship vertical rate, measured in feet per
            minute.
        hdot_int (float): intruder vertical rate, measured in feet per
            minute.
        tau (float): time to loss of horizontal separation, measured in
            seconds.
        s_adv (VCASAdvisories): previous advisory.
    """

    h: float
    hdot_own: float
    hdot_int: float
    tau: float
    s_adv: VCASAdvisories


@dataclass
class AutoavoidInfo:  # pylint: disable=too-many-instance-attributes
    """An extended aircraft representation including the current timestamp.

    Attributes:
        active (bool): Whether autoavoid is active.
        mode (Optional[Literal["hcas", "vcas"]]): The autoavoid mode to
            use.
        action (Optional[float]): The action to take.
        command (Optional[float]): The command issued to FlightGear.
        timestamp (float): The timestamp of the information.
    """

    active: bool
    mode: Literal["hcas", "vcas"] | None
    action: float | None
    command: float | None
    timestamp: float


@dataclass
class ExtendedAircraft:  # pylint: disable=too-many-instance-attributes
    """An extended aircraft representation including the current timestamp.

    Attributes:
        call_sign (str): The call_sign of the aircraft.
        altitude (float): The aircraft's current altitude, measured
            in feet.
        vertical_speed (float): The aircraft's current vertical
            speed, measured in feet per second.
        true_airspeed (float): The aircraft's current true airspeed,
            measured in knots.
        heading (float): The aircraft's current heading, measured in
            degrees.
        latitude (float): The aircraft's current latitude, measured
            in degrees.
        longitude (float): The aircraft's current longitude, measured
            in degrees.
        timestamp (float): The timestamp of the information.
    """

    call_sign: str
    altitude: float
    vertical_speed: float
    true_airspeed: float
    heading: float
    latitude: float
    longitude: float
    timestamp: float


@dataclass
class ExtendedIntruder:
    """An extended intruder representation relying also on advisory data.

    Attributes:
        aircraft (Aircraft): The aircraft data.
        triggers_nmac (bool): Whether the intruder triggers a near
            mid-air collision for the ownship.
        hcas_advisory (HCASAdvisories): The HCAS advisory.
        vcas_advisory (VCASAdvisories): The VCAS advisory.
        hcas_state_variables (HCASStateVariables): The HCAS state with
            respect to the ownship.
        vcas_state_variables (VCASStateVariables): The VCAS state with
            respect to the ownship.
        timestamp (float): The timestamp of the information.
    """

    aircraft: ExtendedAircraft
    triggers_nmac: bool
    hcas_advisory: HCASAdvisories
    vcas_advisory: VCASAdvisories
    hcas_state_variables: APIHCASStateVariables
    vcas_state_variables: APIVCASStateVariables
    timestamp: float


def extend_intruder(intruder: Intruder) -> ExtendedIntruder:
    """Extend the intruder with additional information.

    This will make the intruder JSON serializable and add the
    `triggers_nmac` attribute.

    Args:
        intruder (Intruder): The intruder to extend.

    Returns:
        ExtendedIntruder: The extended intruder.
    """
    return ExtendedIntruder(
        aircraft=ExtendedAircraft(
            call_sign=intruder.aircraft.call_sign,
            altitude=intruder.aircraft.altitude.to(ureg.foot).magnitude,
            vertical_speed=intruder.aircraft.vertical_speed.to(
                ureg.foot / ureg.second
            ).magnitude,
            true_airspeed=intruder.aircraft.true_airspeed.to(ureg.knots).magnitude,
            heading=intruder.aircraft.heading.to(ureg.degree).magnitude,
            latitude=intruder.aircraft.latitude.to(ureg.degree).magnitude,
            longitude=intruder.aircraft.longitude.to(ureg.degree).magnitude,
            timestamp=time.time(),
        ),
        triggers_nmac=intruder.triggers_nmac,
        hcas_advisory=intruder.hcas_advisory,
        vcas_advisory=intruder.vcas_advisory,
        hcas_state_variables=APIHCASStateVariables(
            rho=intruder.hcas_state_variables.rho.to(ureg.foot).magnitude,
            theta=intruder.hcas_state_variables.theta.to(ureg.degree).magnitude,
            psi=intruder.hcas_state_variables.psi.to(ureg.degree).magnitude,
            v_own=intruder.hcas_state_variables.v_own.to(
                ureg.foot / ureg.second
            ).magnitude,
            v_int=intruder.hcas_state_variables.v_int.to(
                ureg.foot / ureg.second
            ).magnitude,
            tau=intruder.hcas_state_variables.tau.to(ureg.second).magnitude,
            s_adv=intruder.hcas_state_variables.s_adv,
        ),
        vcas_state_variables=APIVCASStateVariables(
            h=intruder.vcas_state_variables.h.to(ureg.foot).magnitude,
            hdot_own=intruder.vcas_state_variables.hdot_own.to(
                ureg.foot / ureg.minute
            ).magnitude,
            hdot_int=intruder.vcas_state_variables.hdot_int.to(
                ureg.foot / ureg.minute
            ).magnitude,
            tau=intruder.vcas_state_variables.tau.to(ureg.second).magnitude,
            s_adv=intruder.vcas_state_variables.s_adv,
        ),
        timestamp=time.time(),
    )
