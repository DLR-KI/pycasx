# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Horizontal CAS (HCAS) mixin for the ACAS X."""

from __future__ import annotations

import math

import numpy as np

from pycasx.acas import (
    ACASXProtocol,
    HCASAdvisories,
    Intruder,
    check_for_loss_of_separation,
    ureg,
)


class HCASMixin:
    """Mixin class for the HCAS model.

    The mixin class provides the functionality to calculate the HCAS
    advisory for the pilot.
    """

    def advise_hcas(self: ACASXProtocol, intruder: Intruder) -> HCASAdvisories:
        """Calculate the advisory for the pilot.

        Args:
            intruder (Intruder): The intruder.

        Returns:
            HCASAdvisories: The advisory for the pilot.
        """
        state = intruder.hcas_state_variables
        tau = state.tau.to(ureg.second).magnitude

        # If tau is outside of the HCAS limits, simply return
        # an active state.
        if tau < 0.0 or tau > 60.0:
            return HCASAdvisories.ACTIVE

        # If the intruder is not on a collision course, return an active
        # state
        _, v_sep_loss = check_for_loss_of_separation(self.ownship, intruder.aircraft)
        if not v_sep_loss:
            return HCASAdvisories.ACTIVE

        # Choose correct model based on previous advisory
        # valid values for tau are [0, 5, 10, 15, 20, 30, 40, 60].
        # Limit previous advisory to values bigger than 0 as the values
        # lower than 0 are for internal purposes only and are not defined
        # for the underlying neural networks.
        valid_taus = [0, 5, 10, 15, 20, 30, 40, 60]
        tau = min(valid_taus, key=lambda x: abs(x - tau))
        model_name = (
            f"HCAS_rect_v6_pra{max(state.s_adv.value, 0)}_tau{tau:02d}_25HU_3000"
        )

        # Transform the state variables to the correct format
        # According to
        # https://github.com/sisl/HorizontalCAS/blob/master/GenerateNetworks/genTrainingData.py
        # the network was trained using rectangular coordinates and one
        # speed for both the ownship and intruder. If we want to use
        # different coordinates or a speed difference between the
        # ownship and intruder, we probably need to retrain the network.
        rho = state.rho.to(ureg.foot).magnitude
        theta = state.theta.to(ureg.radians).magnitude
        psi = state.psi.to(ureg.radians).magnitude
        values = [
            rho * math.cos(theta),
            rho * math.sin(theta),
            psi,
        ]
        inputs = np.array(values, dtype=np.float32)

        # Evaluate the model
        outputs = self.evaluate(model_name, inputs)

        # Convert the outputs to advisories
        advisory = HCASAdvisories(int(outputs.argmax()))

        return advisory
