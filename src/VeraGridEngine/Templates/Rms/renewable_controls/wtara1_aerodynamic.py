# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native pitch-to-mechanical-power stage for the wind aerodynamic family."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class Wtara1AerodynamicSettings:
    """Store pitch sensitivity and the equilibrium blade angle."""

    __slots__ = ('ka', 'theta0')

    def __init__(self, ka: float = .007, theta0: float = 0.) -> None:
        """Store the two source constants.

        :param ka: Aerodynamic pitch gain on generator MVA base.
        :param theta0: Initial pitch angle in degrees.
        :return: None.
        """
        self.ka: float = ka
        self.theta0: float = theta0


def build_wtara1_aerodynamic_template(
        vf: VarFactory,
        name: str = 'WTARA1 aerodynamic',
        settings: Wtara1AerodynamicSettings | None = None,
) -> RmsModelTemplate:
    """Convert blade pitch into mechanical power on the machine base.

    The pitch input is in degrees. The second input is the mechanical-power
    operating point. Source binding still requires a complete Type 3 wind
    assembly and its pitch-controller connection.

    :param vf: Shared symbolic variable factory.
    :param name: Unique aerodynamic instance name.
    :param settings: Pitch gain and initial blade angle.
    :return: Stand-alone algebraic aerodynamic controller.
    :raises ValueError: Invalid pitch gain or initial angle.
    """
    selected: Wtara1AerodynamicSettings = Wtara1AerodynamicSettings() if settings is None else settings
    if not math.isfinite(selected.ka) or not math.isfinite(selected.theta0):
        raise ValueError('WTARA1 settings must be finite')
    elif selected.ka <= 0 or selected.theta0 < 0:
        raise ValueError('WTARA1 pitch gain and initial angle are invalid')
    else:
        pass
    control: ControlRealization = ControlRealization(vf, name)
    pitch: Var = control.input('PitchAngleDeg', Const(selected.theta0))
    initial_power: Var = control.input('InitialMechanicalPowerPu', Const(0.))
    ka: Var = control.parameter('KA', selected.ka)
    theta0: Var = control.parameter('THETA0', selected.theta0)
    # All three published block diagrams multiply the live pitch by its
    # change from the initial angle before applying the aerodynamic gain.
    mechanical_power: Var = control.algebraic(
        'MechanicalPowerPu', initial_power - ka * pitch * (pitch - theta0), initial_power,
    )
    return control.finish((mechanical_power,), 'Wind pitch-to-mechanical-power response')
