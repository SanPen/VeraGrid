# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC 61400-27-1 Figure 38 reactive-power capability limiter."""

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
    """Evaluate an endpoint-clipped lookup for an operating-point seed.

    :param curve: Increasing input and output points.
    :param value: Curve input.
    :return: Linearly interpolated output.
    """
    if value <= curve[0][0]:
        return float(curve[0][1])
    else:
        pass
    if value >= curve[-1][0]:
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


def _validate_curve(curve: Sequence[tuple[float, float]], curve_name: str) -> None:
    """Reject missing, nonfinite, or unordered IEC capability curves.

    :param curve: Lookup coordinates from the CGMES lookup table.
    :param curve_name: Curve label used in any validation error.
    """
    if len(curve) < 2:
        raise ValueError('CGMES WindContQPQULimIEC requires two points for ' + curve_name)
    else:
        pass
    point_index: int
    for point_index in range(len(curve)):
        input_value: float = float(curve[point_index][0])
        output_value: float = float(curve[point_index][1])
        if not math.isfinite(input_value) or not math.isfinite(output_value):
            raise ValueError('CGMES WindContQPQULimIEC curve values must be finite')
        elif point_index > 0 and input_value <= float(curve[point_index - 1][0]):
            raise ValueError('CGMES WindContQPQULimIEC curve inputs must increase')
        else:
            pass
    else:
        pass


def _add_lookup_parameters(
        model: ControlRealization,
        curve: Sequence[tuple[float, float]],
        curve_name: str,
) -> tuple[list[Var], list[Var]]:
    """Declare one ordered curve as runtime parameters.

    :param model: Equation graph receiving the symbols.
    :param curve: Lookup coordinates.
    :param curve_name: Canonical IEC curve name.
    :return: Input and output parameter symbols in sequence order.
    """
    input_symbols: list[Var] = list()
    output_symbols: list[Var] = list()
    point_index: int
    for point_index in range(len(curve)):
        input_symbols.append(model.parameter(
            f'WindContQPQULimIEC.{curve_name}_input_{point_index}',
            float(curve[point_index][0]),
        ))
        output_symbols.append(model.parameter(
            f'WindContQPQULimIEC.{curve_name}_output_{point_index}',
            float(curve[point_index][1]),
        ))
    else:
        pass
    return input_symbols, output_symbols


def _add_measurement_filter(
        model: ControlRealization,
        signal_name: str,
        signal: Var,
        filter_time: Var,
        filter_time_value: float,
        freeze: Expr,
        initial_value: float,
) -> Var:
    """Add a zero-time pass-through or UVRT-frozen first-order measurement lag.

    :param model: Equation graph receiving the measurement equation.
    :param signal_name: Public filtered signal name.
    :param signal: Unfiltered host measurement.
    :param filter_time: Filter time-constant parameter.
    :param filter_time_value: Construction value selecting algebraic or dynamic form.
    :param freeze: Clipped UVRT flag that holds the filter state.
    :param initial_value: Solved measurement used for initialization.
    :return: Filtered measurement symbol.
    """
    if filter_time_value == 0.0:
        return model.algebraic(signal_name, signal, Const(initial_value))
    else:
        state: Var = model.vf.add_var(name=f'{signal_name}_{model.name}')
        derivative: Expr = (Const(1.0) - freeze) * (signal - state) / filter_time
        return model.differential(state, derivative, Const(initial_value))


def build_wind_cont_q_p_q_u_lim_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        tpfiltql: float = 0.0,
        tufiltql: float = 0.0,
        qmaxp_curve: Sequence[tuple[float, float]] = (),
        qminp_curve: Sequence[tuple[float, float]] = (),
        qmaxu_curve: Sequence[tuple[float, float]] = (),
        qminu_curve: Sequence[tuple[float, float]] = (),
        initial_active_power: float = 0.0,
        initial_voltage: float = 1.0,
        initial_uvrt: float = 0.0,
) -> RmsModelTemplate:
    """Build IEC 61400-27-1:2015 §5.6.5.10 Figure 38 QP/QU limits.

    :param vfactory: Factory allocating equation graph symbols.
    :param name: Optional unique runtime model name.
    :param tpfiltql: Active-power measurement filter time constant in seconds.
    :param tufiltql: Voltage measurement filter time constant in seconds.
    :param qmaxp_curve: Maximum-Q curve against active power.
    :param qminp_curve: Minimum-Q curve against active power.
    :param qmaxu_curve: Maximum-Q curve against terminal voltage.
    :param qminu_curve: Minimum-Q curve against terminal voltage.
    :param initial_active_power: Solved active power in pu.
    :param initial_voltage: Solved terminal voltage in pu.
    :param initial_uvrt: Initial voltage-ride-through freeze flag.
    :return: Maximum and minimum reactive power limits in pu.
    :raises ValueError: Invalid filter constants, seeds, or lookup curves.
    """
    scalar_values: tuple[float, ...] = (
        tpfiltql, tufiltql, initial_active_power, initial_voltage, initial_uvrt,
    )
    if not all(math.isfinite(value) for value in scalar_values):
        raise ValueError('CGMES WindContQPQULimIEC values must be finite')
    elif min(tpfiltql, tufiltql) < 0.0:
        raise ValueError('CGMES WindContQPQULimIEC filter times must be nonnegative')
    else:
        pass
    _validate_curve(qmaxp_curve, 'qmaxp')
    _validate_curve(qminp_curve, 'qminp')
    _validate_curve(qmaxu_curve, 'qmaxu')
    _validate_curve(qminu_curve, 'qminu')

    template_name: str = 'WindContQPQULimIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    power_filter_time: Var = model.parameter('WindContQPQULimIEC.tpfiltql', tpfiltql)
    voltage_filter_time: Var = model.parameter('WindContQPQULimIEC.tufiltql', tufiltql)
    active_power: Var = model.input('PwtPu', Const(initial_active_power))
    voltage: Var = model.input('UwtPu', Const(initial_voltage))
    uvrt_flag: Var = model.input('FUVRTPu', Const(initial_uvrt))
    freeze: Expr = sym.hard_sat(uvrt_flag, Const(0.0), Const(1.0))

    # IEC Figure 38 freezes both measured quantities while UVRT is active.
    filtered_power: Var = _add_measurement_filter(
        model, 'FilteredPwtPu', active_power, power_filter_time,
        tpfiltql, freeze, initial_active_power,
    )
    filtered_voltage: Var = _add_measurement_filter(
        model, 'FilteredUwtPu', voltage, voltage_filter_time,
        tufiltql, freeze, initial_voltage,
    )
    qmaxp_symbols: tuple[list[Var], list[Var]] = _add_lookup_parameters(
        model, qmaxp_curve, 'qmaxp',
    )
    qminp_symbols: tuple[list[Var], list[Var]] = _add_lookup_parameters(
        model, qminp_curve, 'qminp',
    )
    qmaxu_symbols: tuple[list[Var], list[Var]] = _add_lookup_parameters(
        model, qmaxu_curve, 'qmaxu',
    )
    qminu_symbols: tuple[list[Var], list[Var]] = _add_lookup_parameters(
        model, qminu_curve, 'qminu',
    )
    qmax_from_power: Expr = _build_clipped_lookup_expression(
        filtered_power, qmaxp_symbols[0], qmaxp_symbols[1],
    )
    qmin_from_power: Expr = _build_clipped_lookup_expression(
        filtered_power, qminp_symbols[0], qminp_symbols[1],
    )
    qmax_from_voltage: Expr = _build_clipped_lookup_expression(
        filtered_voltage, qmaxu_symbols[0], qmaxu_symbols[1],
    )
    qmin_from_voltage: Expr = _build_clipped_lookup_expression(
        filtered_voltage, qminu_symbols[0], qminu_symbols[1],
    )
    q_max_initial: float = min(
        _interpolate_curve_value(qmaxp_curve, initial_active_power),
        _interpolate_curve_value(qmaxu_curve, initial_voltage),
    )
    q_min_initial: float = max(
        _interpolate_curve_value(qminp_curve, initial_active_power),
        _interpolate_curve_value(qminu_curve, initial_voltage),
    )
    q_max: Var = model.algebraic(
        'QwtMaxPu', sym.min(qmax_from_power, qmax_from_voltage), Const(q_max_initial),
    )
    q_min: Var = model.algebraic(
        'QwtMinPu', sym.max(qmin_from_power, qmin_from_voltage), Const(q_min_initial),
    )
    return model.finish(
        (q_max, q_min),
        'IEC 61400-27-1 Figure 38 QP/QU capability limits with UVRT-frozen measurements.',
    )
