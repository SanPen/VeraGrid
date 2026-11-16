# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed IEC current ceilings for the CGMES wind limiter."""

import math
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    _build_clipped_lookup_expression,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def _interpolate_curve_value(curve: Sequence[tuple[float, float]], value: float) -> float:
    """Evaluate a clipped piecewise-linear lookup for an equilibrium seed.

    :param curve: Strictly increasing `(input, output)` points.
    :param value: Input coordinate at which to evaluate the curve.
    :return: Endpoint-clipped linearly interpolated curve value.
    """
    if value <= float(curve[0][0]):
        return float(curve[0][1])
    else:
        pass
    if value >= float(curve[-1][0]):
        return float(curve[-1][1])
    else:
        pass
    point_index: int
    for point_index in range(1, len(curve)):
        lower_x: float = float(curve[point_index - 1][0])
        upper_x: float = float(curve[point_index][0])
        if lower_x <= value <= upper_x:
            lower_y: float = float(curve[point_index - 1][1])
            upper_y: float = float(curve[point_index][1])
            fraction: float = (value - lower_x) / (upper_x - lower_x)
            return lower_y + fraction * (upper_y - lower_y)
        else:
            pass
    else:
        pass
    return float(curve[-1][1])


def build_wind_cont_curr_lim_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        imax: float = 1.0,
        imaxdip: float = 1.0,
        kpqu: float = 0.0,
        mdfslim: bool = True,
        mqpri: bool = False,
        tufiltcl: float = 0.0,
        upqumax: float = 1.0,
        ipmax_curve: Sequence[tuple[float, float]] = (),
        iqmax_curve: Sequence[tuple[float, float]] = (),
        initial_voltage: float = 1.0,
        initial_active_current: float = 0.0,
        initial_reactive_current: float = 0.0,
        initial_generator_speed: float = 1.0,
) -> RmsModelTemplate:
    """Build the IEC 61400-27-1 Figure 36 current limiter.

    :param vfactory: Factory allocating the equation graph symbols.
    :param name: Optional unique runtime model name.
    :param imax: Continuous terminal current ceiling in pu.
    :param imaxdip: Fault terminal current ceiling in pu.
    :param kpqu: Reactive-current ceiling slope against voltage in pu/pu.
    :param mdfslim: Selects stator-current mode; false scales Type 3 active-current limits by speed.
    :param mqpri: Enables reactive-current priority during fault ride through.
    :param tufiltcl: Terminal voltage filter time in seconds.
    :param upqumax: Voltage where the voltage-dependent reactive ceiling is zero.
    :param ipmax_curve: Voltage-dependent active current ceiling points.
    :param iqmax_curve: Voltage-dependent reactive current ceiling points.
    :param initial_voltage: Solved turbine terminal voltage in pu.
    :param initial_active_current: Solved active current command in pu.
    :param initial_reactive_current: Solved reactive current command in pu.
    :param initial_generator_speed: Solved generator speed in pu for total-current mode.
    :return: Open-loop current ceilings `IpMaxPu`, `IqMaxPu`, and `IqMinPu`.
    :raises ValueError: Invalid parameters or lookup curves.
    """
    scalar_values: tuple[float, ...] = (
        imax, imaxdip, kpqu, tufiltcl, upqumax, initial_voltage,
        initial_active_current, initial_reactive_current,
        initial_generator_speed,
    )
    if not all(math.isfinite(value) for value in scalar_values):
        raise ValueError('CGMES WindContCurrLimIEC values must be finite')
    elif min(imax, imaxdip, kpqu, tufiltcl, initial_voltage) < 0.0:
        raise ValueError('CGMES WindContCurrLimIEC magnitudes and time must be nonnegative')
    elif len(ipmax_curve) < 2 or len(iqmax_curve) < 2:
        raise ValueError('CGMES WindContCurrLimIEC requires ipmax and iqmax voltage curves')
    else:
        pass
    if initial_generator_speed < 0.0:
        raise ValueError('CGMES WindContCurrLimIEC generator speed must be nonnegative')
    else:
        pass

    curve: Sequence[tuple[float, float]]
    for curve in (ipmax_curve, iqmax_curve):
        point_index: int
        for point_index in range(len(curve)):
            input_value: float = float(curve[point_index][0])
            output_value: float = float(curve[point_index][1])
            if not math.isfinite(input_value) or not math.isfinite(output_value):
                raise ValueError('CGMES WindContCurrLimIEC lookup values must be finite')
            elif output_value < 0.0:
                raise ValueError('CGMES WindContCurrLimIEC current curves must be nonnegative')
            elif point_index > 0 and input_value <= float(curve[point_index - 1][0]):
                raise ValueError('CGMES WindContCurrLimIEC lookup voltages must increase')
            else:
                pass
        else:
            pass

    template_name: str = 'WindContCurrLimIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    continuous_current: Var = model.parameter('WindContCurrLimIEC.imax', imax)
    fault_current: Var = model.parameter('WindContCurrLimIEC.imaxdip', imaxdip)
    reactive_voltage_slope: Var = model.parameter('WindContCurrLimIEC.kpqu', kpqu)
    stator_current_mode: Var = model.parameter(
        'WindContCurrLimIEC.mdfslim', 1.0 if mdfslim else 0.0,
    )
    reactive_priority: Var = model.parameter(
        'WindContCurrLimIEC.mqpri', 1.0 if mqpri else 0.0,
    )
    voltage_filter_time: Var = model.parameter('WindContCurrLimIEC.tufiltcl', tufiltcl)
    zero_reactive_voltage: Var = model.parameter('WindContCurrLimIEC.upqumax', upqumax)

    active_curve_x: list[Var] = list()
    active_curve_y: list[Var] = list()
    reactive_curve_x: list[Var] = list()
    reactive_curve_y: list[Var] = list()
    for point_index in range(len(ipmax_curve)):
        active_curve_x.append(model.parameter(
            f'WindContCurrLimIEC.ipmax_voltage_{point_index}',
            float(ipmax_curve[point_index][0]),
        ))
        active_curve_y.append(model.parameter(
            f'WindContCurrLimIEC.ipmax_limit_{point_index}',
            float(ipmax_curve[point_index][1]),
        ))
    else:
        pass
    for point_index in range(len(iqmax_curve)):
        reactive_curve_x.append(model.parameter(
            f'WindContCurrLimIEC.iqmax_voltage_{point_index}',
            float(iqmax_curve[point_index][0]),
        ))
        reactive_curve_y.append(model.parameter(
            f'WindContCurrLimIEC.iqmax_limit_{point_index}',
            float(iqmax_curve[point_index][1]),
        ))
    else:
        pass

    # Type 3 scales active current capability by generator speed; Type 4 uses unity.
    active_current_command: Var = model.input('IpCmdPu', Const(initial_active_current))
    reactive_current_command: Var = model.input('IqCmdPu', Const(initial_reactive_current))
    terminal_voltage: Var = model.input('UwtPu', Const(initial_voltage))
    fault_flag: Var = model.input('FUVRTPu', Const(0.0))
    generator_speed: Expr = Const(1.0)
    if not mdfslim:
        generator_speed = model.input('OmegaGenPu', Const(initial_generator_speed))
    else:
        pass
    filtered_voltage: Var = model.lag(
        'FilteredUwtPu', terminal_voltage, voltage_filter_time, tufiltcl,
        Const(initial_voltage),
    )
    active_lookup: Expr = _build_clipped_lookup_expression(
        terminal_voltage, active_curve_x, active_curve_y,
    )
    reactive_lookup: Expr = _build_clipped_lookup_expression(
        terminal_voltage, reactive_curve_x, reactive_curve_y,
    )

    # The fault flag selects imaxdip and enables q-priority only during FRT.
    fault_active: Expr = sym.hard_sat(fault_flag, Const(0.0), Const(1.0))
    effective_current_limit: Expr = (
        (Const(1.0) - fault_active) * continuous_current
        + fault_active * fault_current
    )
    q_priority_active: Expr = reactive_priority * fault_active

    # Voltage and current-circle limits jointly bound each axis current ceiling.
    voltage_reactive_limit: Expr = sym.max(
        Const(0.0), reactive_voltage_slope * (zero_reactive_voltage - filtered_voltage),
    )
    physical_reactive_limit: Expr = sym.min(reactive_lookup, voltage_reactive_limit)
    active_circle_remainder: Expr = sym.sqrt(sym.max(
        Const(0.0), effective_current_limit ** 2 - reactive_current_command ** 2,
    ))
    reactive_circle_remainder: Expr = sym.sqrt(sym.max(
        Const(0.0), effective_current_limit ** 2 - active_current_command ** 2,
    ))
    active_priority_limit: Expr = (
        (Const(1.0) - q_priority_active) * effective_current_limit
        + q_priority_active * active_circle_remainder
    )
    reactive_priority_limit: Expr = (
        q_priority_active * effective_current_limit
        + (Const(1.0) - q_priority_active) * reactive_circle_remainder
    )
    active_current_scale: Expr = (
        stator_current_mode + (Const(1.0) - stator_current_mode) * generator_speed
    )
    active_current_maximum: Var = model.algebraic(
        'IpMaxPu', sym.min(active_lookup * active_current_scale, active_priority_limit),
        Const(min(
            _interpolate_curve_value(ipmax_curve, initial_voltage)
            * (1.0 if mdfslim else initial_generator_speed), imax,
        )),
    )
    reactive_current_maximum: Var = model.algebraic(
        'IqMaxPu', sym.min(physical_reactive_limit, reactive_priority_limit),
        Const(min(
            _interpolate_curve_value(iqmax_curve, initial_voltage),
            max(0.0, kpqu * (upqumax - initial_voltage)),
            imax,
        )),
    )
    reactive_current_minimum: Var = model.algebraic(
        'IqMinPu', -reactive_current_maximum,
        -reactive_current_maximum,
    )
    return model.finish(
        (active_current_maximum, reactive_current_maximum, reactive_current_minimum),
        'IEC 61400-27-1 Figure 36 speed-scaled type-3 and stator-current ceilings.',
    )
