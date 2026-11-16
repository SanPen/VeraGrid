# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E Brown-Boveri turbine governor and steam turbine."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Bbgov1Parameters:
    """PSS/E BBGOV1 constants in generator-MVA per unit."""

    __slots__ = (
        'fcut', 'ks', 'kls', 'kg', 'kp', 'tn', 'kd', 'td', 't4', 'k2',
        't5', 'k3', 't6', 't1', 'switch', 'pmax', 'pmin',
    )

    def __init__(self, fcut: float = 0.002, ks: float = 21.0,
                 kls: float = 0.1, kg: float = 1.0, kp: float = 1.0,
                 tn: float = 1.0, kd: float = 1.0, td: float = 1.0,
                 t4: float = 0.15, k2: float = 0.75, t5: float = 12.0,
                 k3: float = 0.5, t6: float = 0.75, t1: float = 0.05,
                 switch: float = 0.0, pmax: float = 1.0, pmin: float = 0.0) -> None:
        """Store the ordered physical source constants.

        :param fcut: Full width of the symmetric speed deadband, pu.
        :param ks: Speed feedback gain on generator MVA base.
        :param kls: Step limit of the step-gradient limiter, pu.
        :param kg: Gradient limit of the step-gradient limiter, pu/s.
        :param kp: PI controller gain.
        :param tn: PI controller integral time, seconds.
        :param kd: Valve-section gain.
        :param td: Valve-section time, seconds.
        :param t4: Steam-output time, seconds.
        :param k2: Intermediate-pressure turbine fraction.
        :param t5: Intermediate turbine time, seconds.
        :param k3: Low-pressure turbine fraction.
        :param t6: Low-pressure turbine time, seconds.
        :param t1: Electrical-power feedback filter time, seconds.
        :param switch: Zero selects electrical power; nonzero selects valve feedback.
        :param pmax: Maximum valve output, pu on generator MVA base.
        :param pmin: Minimum valve output, pu on generator MVA base.
        """
        self.fcut: float = fcut
        self.ks: float = ks
        self.kls: float = kls
        self.kg: float = kg
        self.kp: float = kp
        self.tn: float = tn
        self.kd: float = kd
        self.td: float = td
        self.t4: float = t4
        self.k2: float = k2
        self.t5: float = t5
        self.k3: float = k3
        self.t6: float = t6
        self.t1: float = t1
        self.switch: int = switch
        self.pmax: float = pmax
        self.pmin: float = pmin


def build_bbgov1_template(vf: VarFactory, name: str | None = None,
                          parameters: Bbgov1Parameters | None = None) -> RmsModelTemplate:
    """Build the seven-state PSS/E BBGOV1 realization.

    The governor uses the documented speed deadband, step-gradient limiter,
    PI/valve stages, power feedback selector, and three steam paths.

    :param vf: Factory that owns the native model symbols.
    :param name: Optional runtime instance name.
    :param parameters: PSS/E constants on generator MVA base.
    :return: Native governor template with speed, reference and power inputs.
    :raises ValueError: A source constant is outside the represented domain.
    """
    p: Bbgov1Parameters = Bbgov1Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        p.fcut, p.ks, p.kls, p.kg, p.kp, p.tn, p.kd, p.td, p.t4, p.k2,
        p.t5, p.k3, p.t6, p.t1, p.pmax, p.pmin,
    )
    if not all(math.isfinite(value) for value in values + (p.switch,)):
        raise ValueError('BBGOV1 constants must be finite')
    elif p.fcut < 0.0 or p.kls <= 0.0 or p.kg < 0.0:
        raise ValueError('BBGOV1 deadband and step-gradient limits are invalid')
    elif p.tn <= 0.0 or p.td <= 0.0 or p.t1 < 0.0 or min(p.t4, p.t5, p.t6) < 0.0:
        raise ValueError('BBGOV1 controller/transducer times are invalid')
    elif p.kp < 0.0 or p.kd < 0.0 or p.pmin >= p.pmax:
        raise ValueError('BBGOV1 valve gains and limits are invalid')
    elif not (0.0 <= p.k2 <= 1.0 and 0.0 <= p.k3 <= 1.0):
        raise ValueError('BBGOV1 turbine fractions must be in [0, 1]')
    else:
        pass

    model_name: str = 'BBGOV1' if name is None else name
    control: ControlRealization = ControlRealization(vf, model_name)
    speed: Var = control.input('OmegaPu', Const(1.0))
    reference: Var = control.input('GovernorReferencePu', Const(0.5))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.5))

    # Predeclare the valve state because SWITCH can route it into the feedback lag.
    valve: Var = vf.add_var(f'ValveOutputPu_{model_name}')
    feedback_source: Expr = electrical_power if p.switch == 0.0 else valve
    measured_feedback: Var = control.lag(
        'PowerFeedbackPu', feedback_source,
        control.parameter('T1', p.t1), p.t1, Const(0.5),
    )

    speed_deviation: Expr = Const(1.0) - speed
    deadbanded_speed: Expr = (
        sym.max(speed_deviation - p.fcut / 2.0, Const(0.0))
        + sym.min(speed_deviation + p.fcut / 2.0, Const(0.0))
    )
    limiter_demand: Expr = reference + p.ks * deadbanded_speed - measured_feedback
    limiter_state: Var = vf.add_var(f'StepGradientLimiterPu_{model_name}')
    control.differential(
        limiter_state,
        sym.hard_sat(limiter_demand - limiter_state, -p.kg, p.kg),
        Const(0.0), control.parameter('KLSMIN', -p.kls),
        control.parameter('KLSMAX', p.kls),
    )
    limiter_feedback: Var = control.algebraic(
        'StepGradientLimiterFeedbackPu', limiter_state, Const(0.0),
    )
    integral: Var = control.differential(
        vf.add_var(f'PIControllerIntegralPu_{model_name}'),
        limiter_feedback / control.parameter('TN', p.tn), Const(0.0),
    )
    pi_output: Var = control.algebraic(
        'PIControllerOutputPu', p.kp * (limiter_feedback + integral), Const(0.5),
    )
    control.lag(
        'ValveOutputPu', p.kd * pi_output,
        control.parameter('TD', p.td), p.td, Const(0.5),
        control.parameter('PMIN', p.pmin), control.parameter('PMAX', p.pmax),
        output=valve,
    )

    steam: Var = control.lag(
        'SteamOutputPu', valve, control.parameter('T4', p.t4), p.t4, Const(0.5),
    )
    turbine_t5: Var = control.lag(
        'IntermediateTurbinePowerPu', valve,
        control.parameter('T5', p.t5), p.t5, Const(0.5),
    )
    turbine_t6: Var = control.lag(
        'LowPressureTurbinePowerPu', valve,
        control.parameter('T6', p.t6), p.t6, Const(0.5),
    )
    mechanical_power: Var = control.algebraic(
        'MechanicalPowerPu',
        (1.0 - p.k2) * steam + p.k2 * (1.0 - p.k3) * turbine_t5
        + p.k2 * p.k3 * turbine_t6,
        Const(0.5),
    )
    return control.finish(
        (mechanical_power, valve),
        'PSS/E BBGOV1 Brown-Boveri governor and steam turbine',
    )
