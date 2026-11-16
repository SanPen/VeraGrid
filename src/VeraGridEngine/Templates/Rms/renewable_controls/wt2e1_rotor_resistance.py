# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""WT2E1 Type 2 wind external rotor-resistance controller."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Wt2e1Settings:
    """Hold six WT2E1 CONs, WT2G1 curve points and host initial values."""

    __slots__ = ('tsp', 'tpe', 'ti', 'kp', 'rotrv_max', 'rotrv_min', 'curve',
                 'initial_speed', 'initial_power', 'initial_fraction')

    def __init__(self, tsp: float = .05, tpe: float = .05, ti: float = 1.,
                 kp: float = 1., rotrv_max: float = 1., rotrv_min: float = 0.,
                 curve: tuple[tuple[float, float], ...] = ((0., 0.), (.0054, .0217),
                                                          (.02, .8988), (.04, .9), (.1, .905)),
                 initial_speed: float = 1., initial_power: float = 0.,
                 initial_fraction: float = 0.) -> None:
        """Store source controls and the machine-owned operating point.

        :param tsp: Generator-speed filter time, seconds.
        :param tpe: Electrical-power filter time, seconds.
        :param ti: PI integral time, seconds.
        :param kp: PI proportional gain.
        :param rotrv_max: Maximum available external-resistance fraction.
        :param rotrv_min: Minimum available external-resistance fraction.
        :param curve: Five ordered (positive generator slip, power) WT2G1 pairs.
        :param initial_speed: Initial generator speed, per unit.
        :param initial_power: Initial electrical power, per unit.
        :param initial_fraction: Initial share of available external resistance.
        :return: None.
        """
        self.tsp: float = tsp
        self.tpe: float = tpe
        self.ti: float = ti
        self.kp: float = kp
        self.rotrv_max: float = rotrv_max
        self.rotrv_min: float = rotrv_min
        self.curve: tuple[tuple[float, float], ...] = curve
        self.initial_speed: float = initial_speed
        self.initial_power: float = initial_power
        self.initial_fraction: float = initial_fraction


def _wt2e1_power_slip_curve(
        control: ControlRealization, slip: Expr,
        curve: tuple[tuple[float, float], ...],
) -> Expr:
    """Interpolate WT2G1's five points with held ends and odd slip symmetry.

    :param control: Controller that owns named source parameters.
    :param slip: Filtered generator speed minus synchronous speed.
    :param curve: Validated five-point nonnegative-slip curve.
    :return: Signed reference electrical power.
    """
    magnitude: Expr = sym.abs(slip)
    previous_slip: Var = control.parameter('SLIP_1', curve[0][0])
    previous_power: Var = control.parameter('POWER_REF_1', curve[0][1])
    result: Expr = previous_power
    index: int
    for index in range(1, 5):
        next_slip: Var = control.parameter('SLIP_' + str(index + 1), curve[index][0])
        next_power: Var = control.parameter('POWER_REF_' + str(index + 1), curve[index][1])
        span: Expr = sym.hard_sat(magnitude - previous_slip, Const(0.),
                                  next_slip - previous_slip)
        result = result + (next_power - previous_power) * span / (next_slip - previous_slip)
        previous_slip = next_slip
        previous_power = next_power
    sign: Expr = sym.heaviside(slip) - sym.heaviside(-slip)
    return sign * result


def build_wt2e1_rotor_resistance_template(
        vf: VarFactory, name: str = 'WT2E1 rotor resistance',
        settings: Wt2e1Settings | None = None,
) -> RmsModelTemplate:
    """Build the WT2E1 filtered power-slip error and bounded resistance PI.

    WT2G1 supplies the five-point curve and initial resistance fraction.
    The host also owns the power-curve offset that balances the initial point.
    No WT2G1 source binding is implied by this stand-alone component.

    :param vf: Shared symbolic variable factory.
    :param name: Unique model name.
    :param settings: WT2E1 controls, WT2G1 curve and host initial values.
    :return: Native WT2E1 controller with open machine inputs.
    :raises ValueError: Invalid times, stops, operating point or curve order.
    """
    selected: Wt2e1Settings = Wt2e1Settings() if settings is None else settings
    values: tuple[float, ...] = (selected.tsp, selected.tpe, selected.ti,
                                 selected.kp, selected.rotrv_max, selected.rotrv_min,
                                 selected.initial_speed, selected.initial_power,
                                 selected.initial_fraction)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('WT2E1 settings must be finite')
    elif min(selected.tsp, selected.tpe) < 0 or selected.ti <= 0:
        raise ValueError('WT2E1 time constants are invalid')
    elif (selected.rotrv_min < 0 or selected.rotrv_max > 1
          or selected.rotrv_max <= selected.rotrv_min
          or not selected.rotrv_min <= selected.initial_fraction <= selected.rotrv_max):
        raise ValueError('WT2E1 external-resistance stops or initial value are invalid')
    elif selected.initial_speed <= 0 or len(selected.curve) != 5:
        raise ValueError('WT2E1 initial speed or five-point curve is invalid')
    elif selected.curve[0] != (0., 0.):
        raise ValueError('WT2E1 odd power-slip curve must pass through the origin')
    else:
        pass
    previous_slip: float = -math.inf
    slip: float
    power: float
    for slip, power in selected.curve:
        if (not math.isfinite(slip) or not math.isfinite(power)
                or slip < 0 or slip <= previous_slip):
            raise ValueError('WT2E1 curve requires increasing nonnegative slip')
        else:
            previous_slip = slip

    control: ControlRealization = ControlRealization(vf, name)
    speed: Var = control.input('GeneratorSpeedPu', Const(selected.initial_speed))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(selected.initial_power))
    tsp: Var = control.parameter('TSP', selected.tsp)
    tpe: Var = control.parameter('TPE', selected.tpe)
    ti: Var = control.parameter('TI', selected.ti)
    kp: Var = control.parameter('KP', selected.kp)
    upper: Var = control.parameter('ROTRV_MAX', selected.rotrv_max)
    lower: Var = control.parameter('ROTRV_MIN', selected.rotrv_min)
    filtered_speed: Var = control.lag('FilteredGeneratorSpeedPu', speed, tsp,
                                      selected.tsp, Const(selected.initial_speed))
    filtered_power: Var = control.lag('FilteredElectricalPowerPu', electrical_power, tpe,
                                      selected.tpe, Const(selected.initial_power))
    curve_power: Expr = _wt2e1_power_slip_curve(control, filtered_speed - Const(1.),
                                                 selected.curve)
    curve_initial: Expr = curve_power.subs({filtered_speed: Const(selected.initial_speed)})
    offset: Var = control.input('PowerCurveOffsetPu', Const(selected.initial_power) - curve_initial)
    error: Expr = filtered_power - curve_power - offset
    integral: Var = vf.add_var('ResistanceIntegral_' + name)
    control.differential(integral, error / ti, Const(selected.initial_fraction),
                         lower - kp * error, upper - kp * error)
    resistance: Var = control.algebraic('RotorResistanceFraction',
                                        sym.hard_sat(kp * error + integral, lower, upper),
                                        Const(selected.initial_fraction))
    return control.finish((resistance, filtered_speed, filtered_power),
                          'Type 2 wind power-slip external rotor-resistance controller')
