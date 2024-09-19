# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""ACAS X implementation for pyCASX."""

from __future__ import annotations

import math
import threading
from pathlib import Path
from typing import Final, Literal

import numpy as np
import numpy.typing as npt
import onnxruntime as ort
import pyproj
import torch as th
from loguru import logger
from onnx.onnx_ml_pb2 import ModelProto
from torch.fx import GraphModule

from pycasx.acas import (
    DEFAULT_MODEL_PATH,
    Aircraft,
    HCASAdvisories,
    HCASStateVariables,
    Intruder,
    ModelDict,
    VCASAdvisories,
    VCASStateVariables,
    ureg,
)
from pycasx.acas.hcas import HCASMixin
from pycasx.acas.vcas import VCASMixin
from pycasx.connectors.protocols import PropsConnection
from pycasx.tools.nn_load import (
    load_nnet_from_path,
    load_onnx_from_path,
    load_torch_from_path,
)
from pycasx.tools.NNet.nnet import NNet

RHO_INA = 1.225 * ureg.kilogram / ureg.meter**3  # Density of air at sea level


class ACASX(HCASMixin, VCASMixin):
    """The brain behind pyCASX.

    This class contains all the logic for the ACAS X implementation.
    Well, almost, some logic is provided by the mixin classes

    Args:
        model_path (Path | str | None): Path to the ACAS model folder.
        backend (Literal["nnet", "onnx", "torch"], optional): The runtime
            backend to use. Defaults to "nnet".
    """

    def __init__(
        self,
        model_path: Path | str | None = None,
        backend: Literal["nnet", "onnx", "torch"] = "nnet",
    ) -> None:
        self.backend: Final[str] = backend.lower()

        if model_path is None:
            model_path = DEFAULT_MODEL_PATH
            logger.info(
                f"No `model_path` provided, using default path at {model_path}."
            )

        hcas_models = self.load_models(Path(model_path, "hcas"))
        vcas_models = self.load_models(Path(model_path, "vcas"))

        self.model_dict: ModelDict = {**hcas_models, **vcas_models}  # type: ignore

        self.conn: PropsConnection

        self.ownship: Aircraft
        self.intruders: dict[str, Intruder] = {}

        self.geodesic = pyproj.Geod(ellps="WGS84")

        self.hcas_adv = HCASAdvisories.ACTIVE
        self.vcas_adv = VCASAdvisories.ACTIVE

    def advise(self) -> tuple[HCASAdvisories, VCASAdvisories]:  # noqa: C901
        """Advise the pilot on the current situation.

        Returns:
            tuple[HCASAdvisories, VCASAdvisories]: The HCAS and VCAS
                advisories.
        """
        self.fetch_data()

        # Calculate HCAS advisory, abort if colliding advisories are
        # detected.
        self.hcas_adv = HCASAdvisories.ACTIVE
        for intruder in self.intruders.values():
            intruder.hcas_advisory = self.advise_hcas(intruder)

            if len(self.intruders) < 2:
                self.hcas_adv = intruder.hcas_advisory
                break

            # Simple check for incompatible advisories. With the current
            # structure in the HCASAdvisories enum, higher numbers are
            # stronger advisories and two advisories are only compatible
            # if both are even or both are odd.
            if self.hcas_adv in (HCASAdvisories.ACTIVE, HCASAdvisories.COC):
                self.hcas_adv = intruder.hcas_advisory
            elif intruder.hcas_advisory in (
                HCASAdvisories.ACTIVE,
                HCASAdvisories.COC,
            ):
                pass
            elif not self.hcas_adv.value + intruder.hcas_advisory.value & 1:
                self.hcas_adv = HCASAdvisories(
                    max(self.hcas_adv.value, intruder.hcas_advisory.value)
                )
            else:
                self.hcas_adv = HCASAdvisories.INOP
                break

        # Calculate VCAS advisory, abort if colliding advisories are
        # detected.
        self.vcas_adv = VCASAdvisories.ACTIVE
        for intruder in self.intruders.values():
            intruder.vcas_advisory = self.advise_vcas(intruder)

            if len(self.intruders) < 2:
                self.vcas_adv = intruder.vcas_advisory
                break

            # Simple check for incompatible advisories. With the current
            # structure in the VCASAdvisories enum, higher numbers are
            # stronger advisories and two advisories are only compatible
            # if both are even or both are odd.
            if self.vcas_adv in (VCASAdvisories.ACTIVE, VCASAdvisories.COC):
                self.vcas_adv = intruder.vcas_advisory
            elif intruder.vcas_advisory in (
                VCASAdvisories.ACTIVE,
                VCASAdvisories.COC,
            ):
                pass
            elif not self.vcas_adv.value + intruder.vcas_advisory.value & 1:
                self.vcas_adv = VCASAdvisories(
                    max(self.vcas_adv.value, intruder.vcas_advisory.value)
                )
            else:
                self.vcas_adv = VCASAdvisories.INOP
                break

        return (self.hcas_adv, self.vcas_adv)

    def fetch_data(self) -> None:
        """Fetch the required data from FlightGear.

        Fetches data of ownship and all intruders from FlightGear and
        post-processes the data to the required format for the ACAS X.

        Note: a single get_prop or list_props (without recursion) call
            via the HTTP API takes roughly 20 ms. Therefore, accessing
            the properties of a single aircraft in our current setup
            takes roughly 100 ms. This is a lot of time, especially
            when we have a lot of intruders. Therefore, not only should
            we try to eliminate unnecessary calls to intruders far away
            from the ownship, but we should also try to refactor this
            function to use concurrency.

        Raises:
            RuntimeError: If no connection is registered.
        """
        if self.conn is None:
            raise RuntimeError(
                "No connection to FlightGear established. Please register a connection."
            )

        # Fetch data of ownship
        self.ownship = self.fetch_ownship_data()

        # Get a list of all ai aircraft which are possible intruders
        aircraft = [
            ai
            for ai in self.conn.list_props("/ai/models")["directories"]
            if "/aircraft" in ai
        ]

        # Fetch data of intruders
        for model in aircraft:
            ac_int = self.fetch_intruder_data(model)

            fwd_azimuth, _, dist = self.geodesic.inv(
                self.ownship.longitude.to(ureg.degree).magnitude,
                self.ownship.latitude.to(ureg.degree).magnitude,
                ac_int.longitude.to(ureg.degree).magnitude,
                ac_int.latitude.to(ureg.degree).magnitude,
            )
            fwd_azimuth *= ureg.degree
            dist *= ureg.meter

            psi = self.ownship.heading - ac_int.heading
            # Wrap psi to [-180°, 180°]
            if psi > 180 * ureg.degree:
                psi -= 360 * ureg.degree
            elif psi < -180 * ureg.degree:
                psi += 360 * ureg.degree

            theta = 360 * ureg.degree - (fwd_azimuth - self.ownship.heading)
            # Wrap theta to [-180°, 180°]
            if theta > 180 * ureg.degree:
                theta -= 360 * ureg.degree
            elif theta < -180 * ureg.degree:
                theta += 360 * ureg.degree

            # Calculate tau according to https://doi.org/10.2514/6.2019-2832
            # Errico, A. and Di Vito, V. (2019): Methodology for Estimation
            # of Closest Point of Approach between Aircraft in ATM
            #
            # Ensure all units are in SI and all variable are magnitude only
            _v_own = self.ownship.true_airspeed.to(ureg.meter / ureg.second).magnitude
            _v_int = ac_int.true_airspeed.to(ureg.meter / ureg.second).magnitude
            _rho = dist.to(ureg.meter).magnitude
            u = np.array(
                [
                    _v_own * math.sin(self.ownship.heading.to(ureg.radian).magnitude),
                    _v_own * math.cos(self.ownship.heading.to(ureg.radian).magnitude),
                ]
            )
            v = np.array(
                [
                    _v_int * math.sin(ac_int.heading.to(ureg.radian).magnitude),
                    _v_int * math.cos(ac_int.heading.to(ureg.radian).magnitude),
                ]
            )
            w_0 = np.array(
                [
                    _rho * math.sin(fwd_azimuth.to(ureg.radian).magnitude),
                    _rho * math.cos(fwd_azimuth.to(ureg.radian).magnitude),
                ]
            )

            tau = float((np.dot(w_0, (u - v))) / (np.dot(u - v, u - v))) * ureg.second

            hcas_state = HCASStateVariables(
                rho=dist.to(ureg.foot),
                theta=theta.to(ureg.degree),
                psi=psi.to(ureg.degree),
                v_own=self.ownship.true_airspeed.to(ureg.foot / ureg.second),
                v_int=ac_int.true_airspeed.to(ureg.foot / ureg.second),
                tau=tau,
                s_adv=(
                    self.intruders[ac_int.call_sign].hcas_advisory
                    if ac_int.call_sign in self.intruders
                    else HCASAdvisories.ACTIVE
                ),
            )

            vcas_state = VCASStateVariables(
                h=(ac_int.altitude - self.ownship.altitude).to(ureg.foot),
                hdot_own=self.ownship.vertical_speed.to(ureg.foot / ureg.minute),
                hdot_int=ac_int.vertical_speed.to(ureg.foot / ureg.minute),
                tau=tau,
                s_adv=(
                    self.intruders[ac_int.call_sign].vcas_advisory
                    if ac_int.call_sign in self.intruders
                    else VCASAdvisories.ACTIVE
                ),
            )

            if ac_int.call_sign in self.intruders:
                self.intruders[ac_int.call_sign].aircraft = ac_int
                self.intruders[ac_int.call_sign].hcas_state_variables = hcas_state
                self.intruders[ac_int.call_sign].vcas_state_variables = vcas_state
            else:
                self.intruders[ac_int.call_sign] = Intruder(
                    aircraft=ac_int,
                    hcas_advisory=HCASAdvisories.ACTIVE,
                    vcas_advisory=VCASAdvisories.ACTIVE,
                    hcas_state_variables=hcas_state,
                    vcas_state_variables=vcas_state,
                )

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
        if self.backend == "nnet":
            return self._evaluate_nnet(model_name, inputs)
        if self.backend == "onnx":
            return self._evaluate_onnx(model_name, inputs)
        if self.backend == "torch":
            return self._evaluate_torch(model_name, inputs)

        raise NotImplementedError(f"Backend {self.backend} not implemented.")

    def _evaluate_nnet(
        self, model_name: str, inputs: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        """Evaluate a CAS model with the NNet runtime.

        Args:
            model_name (str): Name of the model to evaluate from the
                model dictionary.
            inputs (npt.NDArray[np.float32]): The inputs to the model.

        Returns:
            npt.NDArray[np.float32]: The outputs of the model.
        """
        model: NNet = self.model_dict[model_name]  # type: ignore
        return model.evaluate_network(inputs)

    def _evaluate_onnx(
        self, model_name: str, inputs: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        """Evaluate a CAS model with the onnx runtime.

        Args:
            model_name (str): Name of the model to evaluate from the
                model dictionary.
            inputs (npt.NDArray[np.float32]): The inputs to the model.

        Returns:
            npt.NDArray[np.float32]: The outputs of the model.

        Raises:
            KeyError: Raised if the requested model is not found.
        """
        try:
            model: ModelProto = self.model_dict[model_name]  # type: ignore
        except KeyError:
            raise KeyError(
                "Please run `pycasx onnx` to convert the provided NNet models to onnx.",
            )
        session = ort.InferenceSession(model.SerializeToString())
        return session.run(None, {"X": inputs})[0]

    def _evaluate_torch(
        self, model_name: str, inputs: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        """Evaluate a CAS model with the PyTorch runtime.

        Args:
            model_name (str): Name of the model to evaluate from the
                model dictionary.
            inputs (npt.NDArray[np.float32]): The inputs to the model.

        Returns:
            npt.NDArray[np.float32]: The outputs of the model.

        Raises:
            KeyError: Raised if the requested model is not found.
        """
        try:
            model: GraphModule = self.model_dict[model_name]  # type: ignore
        except KeyError:
            raise KeyError(
                "Please run `pycasx onnx` to convert the provided NNet models to onnx.",
            )
        with th.no_grad():
            return model.forward(th.from_numpy(inputs)).numpy()

    def register_connection(self, connection: PropsConnection) -> None:
        """Register a new connection to a connection provider.

        The newly registered connection will be used to fetch data for
        the ACAS X model. If a connection is already registered, it will
        be overwritten.

        Args:
            connection (PropsConnection): The connection provider.
        """
        self.conn = connection

    def load_models(self, model_path: Path | str) -> ModelDict:
        """Load the CAS models from the provided path.

        Args:
            model_path (Path | str): Path to the CAS models.

        Returns:
            ModelDict: The loaded CAS models.

        Raises:
            NotImplementedError: Raised if the requested backend is not
                implemented.
            FileNotFoundError: Raised if no models are found at the
                provided path.
        """
        model_dict: ModelDict
        if self.backend == "nnet":
            model_dict = load_nnet_from_path(model_path)
        elif self.backend == "onnx":
            model_dict = load_onnx_from_path(model_path)
        elif self.backend == "torch":
            model_dict = load_torch_from_path(model_path)
        else:
            raise NotImplementedError(f"Backend `{self.backend}` not implemented.")

        if model_dict == {}:
            msg = (
                f"Could not find CAS models at {model_path}. "
                "Please provide correct `model_path` or use `pycasx onnx` "
                "to convert the provided NNet models to onnx. "
                "Also, make sure, in case you provide a custom `model_path`, "
                "that the path contains two subdirectories `hcas` and `vcas` "
                "containing the respective models."
            )
            logger.error(msg)
            raise FileNotFoundError(msg)

        return model_dict

    def fetch_ownship_data(
        self,
    ) -> Aircraft:
        """Fetches the data of the ownship.

        The ownship uses the following properties:
            - /sim/multiplay/callsign
            - /position/altitude-ft
            - /velocities/vertical-speed-fps
            - /velocities/equivalent-kt
            - /environment/density-slugft3
            - /orientation/true-heading-deg
            - /position/latitude-deg
            - /position/longitude-deg

        Returns:
            Aircraft: The ownship with the data fetched from FlightGear.
        """
        return self.fetch_aircraft_data(
            call_sign="/sim/multiplay/callsign",
            altitude_ft="/position/altitude-ft",
            vertical_speed_fps="/velocities/vertical-speed-fps",
            equivalent_airspeed_kt="/velocities/equivalent-kt",
            density_slugft3="/environment/density-slugft3",
            heading_deg="/orientation/true-heading-deg",
            latitude_deg="/position/latitude-deg",
            longitude_deg="/position/longitude-deg",
        )

    def fetch_intruder_data(
        self,
        intruder: str,
    ) -> Aircraft:
        """Fetches the data of a single intruder.

        Args:
            intruder (str): The intruder to fetch the data for. This
                refers to the full path of the intruder in the
                property tree until the aircraft directory. E.g.
                ``/ai/models/aircraft`` for the zeroth intruder and
                ``/ai/models/aircraft[1]`` for the first intruder.

        Returns:
            Aircraft: The intruder with the data fetched from FlightGear.
        """
        return self.fetch_aircraft_data(
            call_sign=f"{intruder}/callsign",
            altitude_ft=f"{intruder}/position/altitude-ft",
            vertical_speed_fps=f"{intruder}/velocities/vertical-speed-fps",
            true_airspeed_kt=f"{intruder}/velocities/true-airspeed-kt",
            heading_deg=f"{intruder}/orientation/true-heading-deg",
            latitude_deg=f"{intruder}/position/latitude-deg",
            longitude_deg=f"{intruder}/position/longitude-deg",
        )

    def fetch_aircraft_data(
        self,
        call_sign: str,
        altitude_ft: str,
        vertical_speed_fps: str,
        heading_deg: str,
        latitude_deg: str,
        longitude_deg: str,
        true_airspeed_kt: str | None = None,
        equivalent_airspeed_kt: str | None = None,
        density_slugft3: str | None = None,
    ) -> Aircraft:
        """Fetches the data of a single aircraft.

        Fetch the required data to fully describe an aircraft from
        FlightGear.
        Some properties are optional, depending on the model used.
        For example, for AI aircraft, FlightGear directly provides the
        true airspeed, but for the ownship, we have to calculate it
        ourselves.
        Thus, one either has to provide the true airspeed or the
        equivalent airspeed and the density.

        This method uses threading to improve performance.

        Args:
            call_sign (str): The property string of the call sign.
            altitude_ft (str): The property string of the altitude.
            vertical_speed_fps (str): The property string of the
                vertical speed.
            heading_deg (str): The property string of the heading.
            latitude_deg (str): The property string of the latitude.
            longitude_deg (str): The property string of the longitude.
            true_airspeed_kt (str | None): The property string of the
                true airspeed.
            equivalent_airspeed_kt (str | None): The property string of
                the equivalent airspeed.
            density_slugft3 (str | None): The property string of the
                density.

        Returns:
            Aircraft: The aircraft with the data fetched from FlightGear.

        Raises:
            ValueError: Raised if neither the true airspeed nor the
                equivalent airspeed and density are provided.
            RuntimeError: Raised if internal logic fails. Please report
                this as a bug.
        """
        if true_airspeed_kt is None and (
            equivalent_airspeed_kt is None or density_slugft3 is None
        ):
            raise ValueError(
                "Please provide either the true airspeed or"
                + " the equivalent airspeed and density."
            )

        properties = [
            call_sign,
            altitude_ft,
            vertical_speed_fps,
            true_airspeed_kt,
            equivalent_airspeed_kt,
            density_slugft3,
            heading_deg,
            latitude_deg,
            longitude_deg,
        ]

        results = {k: None for k in properties if k is not None}

        def get_prop(prop_str: str, results: dict) -> None:
            results[prop_str] = self.conn.get_prop(prop_str)

        threads = []
        for prop in properties:
            if prop is None:
                continue
            t = threading.Thread(
                target=get_prop,
                args=(prop, results),
            )
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()

        if true_airspeed_kt is not None:
            true_airspeed = results[true_airspeed_kt] * ureg.knot
        elif equivalent_airspeed_kt is not None and density_slugft3 is not None:
            v_eas = results[equivalent_airspeed_kt] * ureg.knot
            rho = results[density_slugft3] * ureg.slug / ureg.foot**3
            true_airspeed = v_eas * math.sqrt(RHO_INA / rho)
        else:
            raise RuntimeError("This should never happen. Please report this as a bug.")

        return Aircraft(
            call_sign=str(results[call_sign]),
            altitude=results[altitude_ft] * ureg.foot,
            vertical_speed=results[vertical_speed_fps] * (ureg.foot / ureg.second),
            true_airspeed=true_airspeed,
            heading=results[heading_deg] * ureg.degree,
            latitude=results[latitude_deg] * ureg.degree,
            longitude=results[longitude_deg] * ureg.degree,
        )
