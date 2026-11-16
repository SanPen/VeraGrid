# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE UEL2 table-characteristic limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class UnderexcLimIEEE2Parameters:
    """Canonical IEEE UEL2 scalar and eleven-point RDF parameters."""

    __slots__ = (
        'tuv', 'tup', 'tuq', 'kui', 'kul', 'vuimax', 'vuimin', 'kuf', 'kfb',
        'tul', 'tu1', 'tu2', 'tu3', 'tu4', 'vulmax', 'vulmin', 'points', 'k1', 'k2',
    )

    def __init__(
            self, tuv: float = 5.0, tup: float = 5.0, tuq: float = 0.0,
            kui: float = 0.5, kul: float = 0.8, vuimax: float = 0.25,
            vuimin: float = 0.0, kuf: float = 0.0, kfb: float = 0.0,
            tul: float = 0.0, tu1: float = 0.0, tu2: float = 0.0,
            tu3: float = 0.0, tu4: float = 0.0, vulmax: float = 0.25,
            vulmin: float = 0.0,
            points: tuple[tuple[float, float], ...] = (
                (0.0, -0.31), (0.3, -0.31), (0.6, -0.28), (0.9, -0.21), (1.02, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
            ), k1: float = 2.0, k2: float = 2.0,
    ) -> None:
        """Store all canonical parameters and table endpoints.

        :param tuv: Terminal-voltage measurement filter time.
        :param tup: Active-power measurement filter time.
        :param tuq: Reactive-power measurement filter time.
        :param kui: Integral gain.
        :param kul: Proportional gain.
        :param vuimax: PI integrator upper limit.
        :param vuimin: PI integrator lower limit.
        :param kuf: Excitation-system stabilizer gain.
        :param kfb: Optional integrator-feedback gain.
        :param tul: Optional integrator-feedback filter time.
        :param tu1: First lead time.
        :param tu2: First lag time.
        :param tu3: Second lead time.
        :param tu4: Second lag time.
        :param vulmax: Output upper limit.
        :param vulmin: Output lower limit.
        :param points: Ordered RDF P/Q endpoint pairs, preserving all eleven pairs.
        :param k1: Voltage exponent on the active-power table input.
        :param k2: Voltage exponent on the table reactive-power output.
        """
        self.tuv: float = tuv
        self.tup: float = tup
        self.tuq: float = tuq
        self.kui: float = kui
        self.kul: float = kul
        self.vuimax: float = vuimax
        self.vuimin: float = vuimin
        self.kuf: float = kuf
        self.kfb: float = kfb
        self.tul: float = tul
        self.tu1: float = tu1
        self.tu2: float = tu2
        self.tu3: float = tu3
        self.tu4: float = tu4
        self.vulmax: float = vulmax
        self.vulmin: float = vulmin
        self.points: tuple[tuple[float, float], ...] = points
        self.k1: float = k1
        self.k2: float = k2


def build_underexc_lim_i_e_e_e2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: UnderexcLimIEEE2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the IEEE UEL2 measurements, table, regulator, and output graph.

    :param vfactory: Factory allocating graph variables.
    :param name: Optional runtime model name.
    :param parameters: Canonical UnderexcLimIEEE2 settings and table values.
    :return: Limiter with machine P/Q/Vt inputs, stabilizer/feedback ports, and VUEL output.
    :raises ValueError: A parameter, limit, time stage, or lookup-table axis is invalid.
    """
    settings: UnderexcLimIEEE2Parameters = (
        UnderexcLimIEEE2Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.tuv, settings.tup, settings.tuq, settings.kui, settings.kul,
        settings.vuimax, settings.vuimin, settings.kuf, settings.kfb, settings.tul,
        settings.tu1, settings.tu2, settings.tu3, settings.tu4,
        settings.vulmax, settings.vulmin, settings.k1, settings.k2,
    ) + tuple(value for point in settings.points for value in point)
    if len(settings.points) != 11 or not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('UnderexcLimIEEE2 requires eleven finite points and finite parameters')
    elif min(settings.tuv, settings.tup, settings.tuq, settings.tul,
             settings.tu1, settings.tu2, settings.tu3, settings.tu4) < 0.0:
        raise ValueError('UnderexcLimIEEE2 time constants must be nonnegative')
    elif settings.vuimin >= settings.vuimax or settings.vulmin >= settings.vulmax:
        raise ValueError('UnderexcLimIEEE2 lower limits must be below upper limits')
    elif (settings.tu2 == 0.0 and settings.tu1 > 0.0) or (
            settings.tu4 == 0.0 and settings.tu3 > 0.0):
        raise ValueError('UnderexcLimIEEE2 zero lag requires a zero lead')
    elif len(tuple(point for point in settings.points if point != (0.0, 0.0))) < 2:
        raise ValueError('UnderexcLimIEEE2 requires at least two populated P/Q endpoints')
    else:
        pass

    template_name: str = 'UnderexcLimIEEE2' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    parameter_values: tuple[tuple[str, float], ...] = (
        ('tuv', settings.tuv), ('tup', settings.tup), ('tuq', settings.tuq),
        ('kui', settings.kui), ('kul', settings.kul), ('vuimax', settings.vuimax),
        ('vuimin', settings.vuimin), ('kuf', settings.kuf), ('kfb', settings.kfb),
        ('tul', settings.tul), ('tu1', settings.tu1), ('tu2', settings.tu2),
        ('tu3', settings.tu3), ('tu4', settings.tu4), ('vulmax', settings.vulmax),
        ('vulmin', settings.vulmin), ('k1', settings.k1), ('k2', settings.k2),
    )
    parameter_symbols: tuple[Var, ...] = tuple(
        model.parameter('UnderexcLimIEEE2.' + parameter_name, parameter_value)
        for parameter_name, parameter_value in parameter_values
    )
    point_symbols: tuple[tuple[Var, Var], ...] = tuple(
        (
            model.parameter('UnderexcLimIEEE2.p' + str(point_index), point[0]),
            model.parameter('UnderexcLimIEEE2.q' + str(point_index), point[1]),
        )
        for point_index, point in enumerate(settings.points)
    )
    measurement_voltage_time: Var = parameter_symbols[0]
    measurement_active_time: Var = parameter_symbols[1]
    measurement_reactive_time: Var = parameter_symbols[2]
    integral_gain: Var = parameter_symbols[3]
    proportional_gain: Var = parameter_symbols[4]
    integrator_upper: Var = parameter_symbols[5]
    integrator_lower: Var = parameter_symbols[6]
    stabilizer_gain: Var = parameter_symbols[7]
    feedback_gain: Var = parameter_symbols[8]
    feedback_time: Var = parameter_symbols[9]
    lead_one: Var = parameter_symbols[10]
    lag_one: Var = parameter_symbols[11]
    lead_two: Var = parameter_symbols[12]
    lag_two: Var = parameter_symbols[13]
    output_upper: Var = parameter_symbols[14]
    output_lower: Var = parameter_symbols[15]
    voltage_active_exponent: Var = parameter_symbols[16]
    voltage_reactive_exponent: Var = parameter_symbols[17]

    # The IEEE2 filters separate measured terminal conditions from the lookup control error.
    voltage_input: Var = model.input('VtPu', Const(1.0))
    active_input: Var = model.input('PPu', Const(0.0))
    reactive_input: Var = model.input('QPu', Const(0.0))
    # The importer binds Vf to the associated PSS output when that source is composed; otherwise it remains a root input.
    stabilizer_input: Var = model.input('VfPu', Const(0.0))
    feedback_input: Var = model.input('VfbPu', Const(0.0))
    voltage_filtered: Var = model.lag(
        'VtFilteredPu', voltage_input, measurement_voltage_time, settings.tuv,
        voltage_input,
    )
    active_filtered: Var = model.lag(
        'PFilteredPu', active_input, measurement_active_time, settings.tup,
        active_input,
    )
    reactive_filtered: Var = model.lag(
        'QFilteredPu', reactive_input, measurement_reactive_time, settings.tuq,
        reactive_input,
    )
    # TODO: The IEEE equation is singular at zero filtered voltage; preserve it literally until a source defines that boundary.
    active_table_input: Expr = active_filtered / (
        voltage_filtered ** voltage_active_exponent
    )
    # The RDF has no point count; canonical unused pairs are trailing zeros, so preserve interior (0, 0) endpoints.
    active_point_count: int = max(
        point_index + 1
        for point_index, point in enumerate(settings.points)
        if point != (0.0, 0.0)
    )
    active_points: tuple[tuple[float, float], ...] = settings.points[:active_point_count]
    active_point_symbols: tuple[tuple[Var, Var], ...] = point_symbols[:active_point_count]
    table_breakpoints: tuple[Var, ...] = tuple(point[0] for point in active_point_symbols)
    table_values: tuple[Var, ...] = tuple(point[1] for point in active_point_symbols)
    table_breakpoint_values: tuple[float, ...] = tuple(point[0] for point in active_points)
    table_value_values: tuple[float, ...] = tuple(point[1] for point in active_points)
    if any(table_breakpoint_values[index] >= table_breakpoint_values[index + 1]
           for index in range(len(table_breakpoint_values) - 1)):
        raise ValueError('UnderexcLimIEEE2 populated P endpoints must be strictly increasing')
    else:
        pass
    boundary_value: Expr = table_values[0]
    for point_index in range(len(table_breakpoints) - 1):
        x_left: Var = table_breakpoints[point_index]
        x_right: Var = table_breakpoints[point_index + 1]
        y_left: Var = table_values[point_index]
        y_right: Var = table_values[point_index + 1]
        segment_value: Expr = y_left + (active_table_input - x_left) * (
            (y_right - y_left) / (x_right - x_left)
        )
        active_segment: Expr = (active_table_input >= x_left).to_expression() * (
            Const(1.0) - (active_table_input >= x_right).to_expression()
        )
        boundary_value = active_segment * segment_value + (Const(1.0) - active_segment) * boundary_value
    else:
        pass
    final_slope: Expr = (
        (table_values[-1] - table_values[-2])
        / (table_breakpoints[-1] - table_breakpoints[-2])
    )
    final_segment: Expr = table_values[-1] + (active_table_input - table_breakpoints[-1]) * final_slope
    final_condition: Expr = (active_table_input >= table_breakpoints[-1]).to_expression()
    boundary_value = final_condition * final_segment + (Const(1.0) - final_condition) * boundary_value
    first_slope: Expr = (
        (table_values[1] - table_values[0]) / (table_breakpoints[1] - table_breakpoints[0])
    )
    first_segment: Expr = table_values[0] + (active_table_input - table_breakpoints[0]) * first_slope
    first_condition: Expr = (active_table_input < table_breakpoints[0]).to_expression()
    boundary_value = first_condition * first_segment + (Const(1.0) - first_condition) * boundary_value
    table_signal: Var = model.algebraic('QBoundaryTablePu', boundary_value, boundary_value)
    boundary_signal: Expr = table_signal * (voltage_filtered ** voltage_reactive_exponent)
    control_error: Expr = boundary_signal - reactive_filtered + stabilizer_gain * stabilizer_input
    if settings.tul > 0.0:
        feedback_signal: Var = model.lag(
            'IntegratorFeedbackPu', feedback_input, feedback_time, settings.tul,
            Const(0.0),
        )
    else:
        feedback_signal = model.algebraic('IntegratorFeedbackPu', feedback_input, Const(0.0))
    if settings.kui > 0.0:
        integral_state: Var = vfactory.add_var(f'PiIntegralPu_{template_name}')
        integral_initial: Expr = sym.hard_sat(
            -proportional_gain * control_error,
            integrator_lower - proportional_gain * control_error,
            integrator_upper - proportional_gain * control_error,
        )
        model.differential(
            integral_state,
            integral_gain * (control_error + feedback_gain * feedback_signal),
            integral_initial, integrator_lower - proportional_gain * control_error,
            integrator_upper - proportional_gain * control_error,
        )
        pi_signal: Expr = proportional_gain * control_error + integral_state
    else:
        pi_signal = proportional_gain * control_error
    pi_output_initial: Expr = sym.hard_sat(pi_signal, integrator_lower, integrator_upper)
    pi_limited: Var = model.algebraic(
        'PiOutputPu', sym.hard_sat(pi_signal, integrator_lower, integrator_upper), pi_output_initial,
    )
    first_compensation: Var = model.lead_lag(
        'LeadLag1Pu', pi_limited, lead_one, lag_one, settings.tu1, settings.tu2, pi_output_initial,
    )
    second_compensation: Var = model.lead_lag(
        'LeadLag2Pu', first_compensation, lead_two, lag_two,
        settings.tu3, settings.tu4, pi_output_initial,
    )
    output_initial: Expr = sym.hard_sat(second_compensation, output_lower, output_upper)
    output: Var = model.algebraic(
        'VuelPu', sym.hard_sat(second_compensation, output_lower, output_upper), output_initial,
    )
    template: RmsModelTemplate = model.finish(
        (output,), 'CGMES IEEE UEL2 multi-segment P/Q characteristic limiter',
    )
    template.comment = (
        'IEEE 421.5-2005 §10.2: filtered Vt/P/Q, Ptable=P/Vt^k1, '
        'Qboundary=Qtable(Ptable)*Vt^k2, bounded KUL+KUI/s, two lead-lags, '
        'KUF stabilizer input, KFB/TUL filtered feedback, and VUL output bounds. '
        'All eleven RDF pairs remain runtime parameters; trailing zero/zero unused slots are omitted from '
        'linear interpolation/extrapolation.'
    )
    enabled_name: str = f'UnderexcLimIEEE2.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    model.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
