# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Vertical CAS (VCAS) mixin for the ACAS X."""

from __future__ import annotations

import numpy as np

from pycasx.acas import (
    ACASXProtocol,
    Intruder,
    VCASAdvisories,
    check_for_loss_of_separation,
    ureg,
)


class VCASMixin:
    """Mixin class for the VCAS model.

    The mixin class provides the functionality to calculate the VCAS
    advisory for the pilot.
    """

    def advise_vcas(self: ACASXProtocol, intruder: Intruder) -> VCASAdvisories:
        """Calculate the VCAS advisory for the pilot.

        Args:
            intruder (Intruder): The intruder.

        Returns:
            VCASAdvisories: The advisory for the pilot.
        """
        state = intruder.vcas_state_variables
        tau = state.tau.to(ureg.second).magnitude

        # If tau is outside of the VCAS limits, simply return
        # an active state.
        if tau < 0.0 or tau > 40.0:
            return VCASAdvisories.ACTIVE

        # If the intruder is not on a collision course, return an active
        # state
        h_sep_loss, _ = check_for_loss_of_separation(self.ownship, intruder.aircraft)
        if not h_sep_loss:
            return VCASAdvisories.ACTIVE

        # Choose correct model based on previous advisory. Limit to
        # values bigger than 0 as the values lower than 0 are for
        # internal purposes only and are not defined for the underlying
        # neural networks.
        model_name = f"VertCAS_pra{(max(state.s_adv.value, 0) + 1):02d}_v4_45HU_200"

        # Transform the state variables to the correct format
        # According to
        # https://github.com/sisl/VerticalCAS/blob/master/GenerateNetworks/genTrainingData.py
        # the inputs are [h, hdot_own, hdot_int, tau]
        # Also, it appears, that the network was trained using feet per
        # second instead of feet per minute.
        h = state.h.to(ureg.foot).magnitude
        hdot_own = state.hdot_own.to(ureg.foot / ureg.second).magnitude
        hdot_int = state.hdot_int.to(ureg.foot / ureg.second).magnitude
        values = [h, hdot_own, hdot_int, tau]
        inputs = np.array(values, dtype=np.float32)

        # Evaluate the model
        outputs = self.evaluate(model_name, inputs)

        # Convert the outputs to advisories
        advisory = VCASAdvisories(int(outputs.argmax()))

        return advisory
