# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Terminal-fed AC9C potential-source phasor magnitudes."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac9cPotentialSourceSettings:
    """Store AC9C terminal-fed source coefficients."""

    __slots__ = ('kp', 'ki1', 'ki2', 'xl', 'theta_p')

    def __init__(self, kp: float = 1.0, ki1: float = 0.0, ki2: float = 0.0,
                 xl: float = 0.0, theta_p: float = 0.0) -> None:
        """Store source gains and phase angle.

        :param kp: Potential-voltage gain.
        :param ki1: Compound current gain in the first source channel.
        :param ki2: Current gain in the second source channel.
        :param xl: Potential-source reactance.
        :param theta_p: Potential-circuit phase angle in degrees.
        """
        self.kp: float = kp
        self.ki1: float = ki1
        self.ki2: float = ki2
        self.xl: float = xl
        self.theta_p: float = theta_p


def build_ac9c_potential_source_template(
        vf: VarFactory,
        name: str = 'AC9C potential source',
        settings: Ac9cPotentialSourceSettings | None = None,
) -> RmsModelTemplate:
    """Build the two source magnitudes in PSS/E 35.2 Model Library §6.14.

    The first channel is ``|Kp*Vt + j*(KI1 + Kp*XL)*It|`` with
    ``Kp = KP*exp(j*theta_p)``. The second channel is ``|KI2*It|``.
    Terminal voltage and current are rectangular RMS phasors on one base.

    :param vf: Symbol factory owning the native equations.
    :param name: Unique component label.
    :param settings: Source gains, reactance and phase.
    :return: Stateless block exposing both potential-source magnitudes.
    :raises ValueError: Any source coefficient is nonfinite.
    """
    selected: Ac9cPotentialSourceSettings = (
        Ac9cPotentialSourceSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.kp, selected.ki1, selected.ki2, selected.xl, selected.theta_p,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC9C potential-source settings must be finite')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    kp: Var = control.parameter('KP', selected.kp)
    ki1: Var = control.parameter('KI1', selected.ki1)
    ki2: Var = control.parameter('KI2', selected.ki2)
    xl: Var = control.parameter('XL', selected.xl)
    theta: Var = control.parameter('THETAP', selected.theta_p)
    voltage_real: Var = control.input('TerminalVoltageRealPu', Const(1.0))
    voltage_imag: Var = control.input('TerminalVoltageImagPu', Const(0.0))
    current_real: Var = control.input('TerminalCurrentRealPu', Const(0.0))
    current_imag: Var = control.input('TerminalCurrentImagPu', Const(0.0))

    phase_radians: Expr = theta * Const(math.pi / 180.0)
    kp_real: Expr = kp * sym.cos(phase_radians)
    kp_imag: Expr = kp * sym.sin(phase_radians)
    compound_real: Expr = ki1 + kp_real * xl
    compound_imag: Expr = kp_imag * xl
    first_real: Expr = (
        kp_real * voltage_real - kp_imag * voltage_imag
        - compound_real * current_imag - compound_imag * current_real
    )
    first_imag: Expr = (
        kp_real * voltage_imag + kp_imag * voltage_real
        + compound_real * current_real - compound_imag * current_imag
    )
    first_voltage: Var = control.algebraic(
        'TerminalPotentialVoltagePu',
        sym.sqrt(first_real * first_real + first_imag * first_imag),
        Const(abs(selected.kp)),
    )
    second_voltage: Var = control.algebraic(
        'CurrentPotentialVoltagePu',
        sym.max(
            sym.sqrt(ki2 * ki2 * (current_real * current_real + current_imag * current_imag)),
            Const(0.001),
        ),
        Const(0.001),
    )
    return control.finish(
        (first_voltage, second_voltage),
        'AC9C terminal-fed potential-source phasor magnitudes',
    )
