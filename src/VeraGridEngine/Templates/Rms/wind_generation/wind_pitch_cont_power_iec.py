# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed IEC 61400-27-1:2015 wind pitch-power controller."""

import math
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import pickup_dropoff
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_wind_pitch_cont_power_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dpmax: float = 999.0,
        dpmin: float = -999.0,
        pmin: float = 0.0,
        pset: float = 0.0,
        t1: float = 0.0,
        tr: float = 0.0,
        uuvrt: float = 0.0,
        tduwt_curve: Sequence[tuple[float, float]] = (),
        initial_power: float = 0.0,
        initial_voltage: float = 1.0,
) -> RmsModelTemplate:
    """Build IEC Figure 28 filtered dip, delay, ramp and aerodynamic-power lag.

    :param vfactory: Factory allocating model symbols.
    :param name: Optional unique runtime name.
    :param dpmax: Maximum power increase rate in pu/s.
    :param dpmin: Maximum power decrease rate in pu/s, encoded nonpositive.
    :param pmin: Minimum aerodynamic-power target during a qualifying voltage dip.
    :param pset: Power threshold; reduction applies when initial power is below it.
    :param t1: Aerodynamic-power output lag time in seconds.
    :param tr: Turbine-voltage measurement lag time in seconds.
    :param uuvrt: Voltage threshold that detects a dip.
    :param tduwt_curve: Ordered `(voltage, delay_seconds)` lookup points.
    :param initial_power: Solved load-flow generator power in pu.
    :param initial_voltage: Solved terminal voltage in pu.
    :return: Equation-backed `PaeroPu` output.
    :raises ValueError: Invalid parameters or lookup points.
    """
    values: tuple[float, ...] = (
        dpmax, dpmin, pmin, pset, t1, tr, uuvrt, initial_power, initial_voltage,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindPitchContPowerIEC values must be finite')
    elif min(dpmax, t1, tr, uuvrt, initial_power, initial_voltage) < 0.0:
        raise ValueError('CGMES WindPitchContPowerIEC rates, times and magnitudes must be nonnegative')
    elif dpmin > 0.0 or pmin > pset:
        raise ValueError('CGMES WindPitchContPowerIEC requires dpmin <= 0 and pmin <= pset')
    elif len(tduwt_curve) < 2:
        raise ValueError('CGMES WindPitchContPowerIEC requires at least two tduwt points')
    else:
        pass

    point_index: int
    for point_index in range(len(tduwt_curve)):
        voltage_point: float = float(tduwt_curve[point_index][0])
        delay_point: float = float(tduwt_curve[point_index][1])
        if not math.isfinite(voltage_point) or not math.isfinite(delay_point) or delay_point < 0.0:
            raise ValueError('CGMES WindPitchContPowerIEC lookup values must be finite and delays nonnegative')
        elif point_index > 0 and voltage_point <= float(tduwt_curve[point_index - 1][0]):
            raise ValueError('CGMES WindPitchContPowerIEC lookup voltages must increase')
        else:
            pass
    else:
        pass

    template_name: str = 'WindPitchContPowerIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    increasing_rate: Var = model.parameter('WindPitchContPowerIEC.dpmax', dpmax)
    decreasing_rate: Var = model.parameter('WindPitchContPowerIEC.dpmin', dpmin)
    minimum_power: Var = model.parameter('WindPitchContPowerIEC.pmin', pmin)
    power_threshold: Var = model.parameter('WindPitchContPowerIEC.pset', pset)
    power_lag_time: Var = model.parameter('WindPitchContPowerIEC.t1', t1)
    voltage_lag_time: Var = model.parameter('WindPitchContPowerIEC.tr', tr)
    dip_threshold: Var = model.parameter('WindPitchContPowerIEC.uuvrt', uuvrt)

    voltage_input: Var = model.input('UwtPu', Const(initial_voltage))
    filtered_voltage: Var = model.lag(
        'FilteredUwtPu', voltage_input, voltage_lag_time, tr, Const(initial_voltage),
    )
    initial_power_input: Var = model.input('PinitPu', Const(initial_power))

    # IEC notes define tduwt as a step curve, so accumulate threshold crossings
    # instead of interpolating between delay values.
    delay_curve_x: list[Var] = list()
    delay_curve_y: list[Var] = list()
    delay_lookup: Expr = Const(0.0)
    for point_index in range(len(tduwt_curve)):
        delay_curve_x.append(model.parameter(
            f'WindPitchContPowerIEC.tduwt_voltage_{point_index}',
            float(tduwt_curve[point_index][0]),
        ))
        delay_curve_y.append(model.parameter(
            f'WindPitchContPowerIEC.tduwt_delay_{point_index}',
            float(tduwt_curve[point_index][1]),
        ))
        if point_index == 0:
            delay_lookup = delay_curve_y[point_index]
        else:
            delay_lookup = delay_lookup + (
                delay_curve_y[point_index] - delay_curve_y[point_index - 1]
            ) * sym.heaviside(filtered_voltage - delay_curve_x[point_index])
    else:
        pass

    voltage_dip: Expr = sym.heaviside(dip_threshold - filtered_voltage)
    initial_power_below_setpoint: Expr = sym.heaviside(power_threshold - initial_power_input)
    reduction_condition: Expr = voltage_dip * initial_power_below_setpoint
    delay_flag_hold: Var = vfactory.add_var(f'WindPitchPowerDelayFlagHold_{template_name}')
    model.block.mode_dict[delay_flag_hold] = Const(0.0)
    model.block.procedural_logic.append(pickup_dropoff(
        output=delay_flag_hold,
        boolexpr=reduction_condition,
        Tpick=Const(0.0),
        Tdrop=delay_lookup,
        name=f'WindPitchContPowerIEC.DelayFlagTimer_{template_name}',
    ))

    # IEC Annex G.11 encodes the relay as 1 while faulted, 2 during delayed
    # post-fault recovery, and 0 after the variable post-fault timer expires.
    delay_flag: Var = model.algebraic(
        'DelayFlag',
        reduction_condition + Const(2.0) * (delay_flag_hold - reduction_condition),
        Const(0.0),
    )
    selected_power: Expr = (
        (Const(1.0) - delay_flag_hold) * initial_power_input
        + reduction_condition * minimum_power
    )
    ramp_state: Var = vfactory.add_var(f'WindPitchPowerRampStatePu_{template_name}')
    model.differential(
        ramp_state,
        sym.hard_sat(selected_power - ramp_state, decreasing_rate, increasing_rate),
        Const(initial_power),
    )
    aerodynamic_power: Var = model.lag(
        'PaeroPu', ramp_state, power_lag_time, t1, Const(initial_power),
    )
    return model.finish(
        (aerodynamic_power, delay_flag),
        'IEC 61400-27-1:2015 Figure 28 pitch-power model; tduwt is a step delay lookup.',
    )
