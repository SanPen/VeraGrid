# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://www.mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcDC3A1 potential-source exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcDC3A1Parameters:
    """Parameters declared by the canonical CGMES ExcDC3A1 class."""

    __slots__ = (
        'ka', 'ta', 'vrmax', 'vrmin', 'te', 'kf', 'tf', 'kp', 'ki', 'vbmax',
        'exclim', 'ke', 'vb1max', 'vblim',
    )

    def __init__(
            self,
            ka: float = 300.0,
            ta: float = 0.01,
            vrmax: float = 5.0,
            vrmin: float = 0.0,
            te: float = 1.83,
            kf: float = 0.1,
            tf: float = 0.675,
            kp: float = 4.37,
            ki: float = 4.83,
            vbmax: float = 11.63,
            exclim: bool = True,
            ke: float = 1.0,
            vb1max: float = 11.63,
            vblim: bool = True,
    ) -> None:
        """Store EA typical settings and Boolean limiter selections.

        :param ka: Voltage-regulator gain.
        :param ta: Voltage-regulator time constant in seconds.
        :param vrmax: Upper regulator output limit.
        :param vrmin: Lower regulator output limit.
        :param te: Exciter time constant in seconds.
        :param kf: Exciter stabilizer gain.
        :param tf: Exciter stabilizer time constant in seconds.
        :param kp: Potential-circuit voltage gain.
        :param ki: Potential-circuit current gain.
        :param vbmax: Exciter input upper limit.
        :param exclim: Apply the zero lower stop to the exciter state.
        :param ke: Exciter field constant.
        :param vb1max: Potential-source upper limit.
        :param vblim: Select Vbmax (true) or Vb1max (false) as the active exciter-input limit.
        """
        self.ka: float = ka
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.te: float = te
        self.kf: float = kf
        self.tf: float = tf
        self.kp: float = kp
        self.ki: float = ki
        self.vbmax: float = vbmax
        self.exclim: bool = exclim
        self.ke: float = ke
        self.vb1max: float = vb1max
        self.vblim: bool = vblim


def build_exc_d_c3_a1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcDC3A1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the potential-source bridge, voltage regulator, and exciter.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Equation-backed model with voltage, current, field-current, reference,
        stabilizer, and Efd signals.
    :raises ValueError: Invalid time constants or limiter/signal gain settings.
    """
    settings: ExcDC3A1Parameters = ExcDC3A1Parameters() if parameters is None else parameters
    template_name: str = 'ExcDC3A1' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.ta, settings.vrmax, settings.vrmin, settings.te,
        settings.kf, settings.tf, settings.kp, settings.ki, settings.vbmax,
        settings.ke, settings.vb1max,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcDC3A1 parameters must be finite')
    elif settings.ta < 0.0 or settings.te <= 0.0 or settings.tf < 0.0:
        raise ValueError('ExcDC3A1 times must be nonnegative and TE positive')
    elif settings.vrmin >= settings.vrmax or settings.vbmax <= 0.0 or settings.vb1max <= 0.0:
        raise ValueError('ExcDC3A1 regulator and bridge limits must be positive and ordered')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    te: Var = builder.parameter('TE', settings.te)
    kf: Var = builder.parameter('KF', settings.kf)
    tf: Var = builder.parameter('TF', settings.tf)
    kp: Var = builder.parameter('KP', settings.kp)
    ki: Var = builder.parameter('KI', settings.ki)
    vbmax: Var = builder.parameter('VBMAX', settings.vbmax)
    ke: Var = builder.parameter('KE', settings.ke)
    vb1max: Var = builder.parameter('VB1MAX', settings.vb1max)
    builder.parameter('EXCLIM', 1.0 if settings.exclim else 0.0)
    builder.parameter('VBLIM', 1.0 if settings.vblim else 0.0)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    terminal_current: Var = builder.input('ItPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))

    # The source diagram places voltage and j-scaled current in quadrature.
    potential_magnitude: Expr = sym.sqrt(
        (kp * terminal_voltage) ** Const(2.0)
        + (ki * terminal_current) ** Const(2.0),
    )
    bridge_radicand: Expr = potential_magnitude ** Const(2.0) - (
        Const(0.78) * field_current
    ) ** Const(2.0)
    bridge_voltage: Expr = sym.hard_sat(
        sym.sqrt(sym.max(bridge_radicand, Const(0.0))), Const(0.0), vb1max,
    )
    exciter_state: Var = vfactory.add_var(f'EfdPu_{template_name}')
    if settings.kf == 0.0:
        stabilizing_feedback: Expr = Const(0.0)
    else:
        feedback_state: Var = builder.lag(
            'FeedbackPu', exciter_state, tf, settings.tf, Const(1.0),
        )
        stabilizing_feedback = kf * feedback_state
    regulator_demand: Expr = ka * (reference - terminal_voltage + supplementary + stabilizing_feedback)
    if settings.ka == 0.0:
        regulator_initial: Expr = sym.hard_sat(Const(0.0), vrmin, vrmax)
    else:
        regulator_initial = sym.hard_sat(ke - bridge_voltage, vrmin, vrmax)
        builder.block.init_eqs[reference] = (
            terminal_voltage + regulator_initial / ka - supplementary - stabilizing_feedback
        )
    regulator_output: Var = builder.lag(
        'RegulatorOutputPu', regulator_demand, ta, settings.ta, regulator_initial,
        vrmin, vrmax,
    )
    exciter_input: Expr = regulator_output + bridge_voltage
    if settings.vblim:
        exciter_input = sym.hard_sat(exciter_input, Const(0.0), vbmax)
    else:
        exciter_input = sym.hard_sat(exciter_input, Const(0.0), vb1max)
    exciter_derivative: Expr = (exciter_input - ke * exciter_state) / te
    if settings.exclim:
        lower_stop: Expr = Const(1.0) - sym.heaviside(exciter_state)
        outward_motion: Expr = sym.heaviside(-exciter_derivative)
        exciter_derivative = exciter_derivative * (Const(1.0) - lower_stop * outward_motion)
    else:
        pass
    builder.differential(exciter_state, exciter_derivative, Const(1.0))
    field_voltage: Var = builder.algebraic('EfdPu', exciter_state, Const(1.0))
    return builder.finish((field_voltage,), 'CGMES ExcDC3A1 potential-source exciter')
