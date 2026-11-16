# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC 61400-27-1:2015 Figure 35 wind-turbine reactive current control."""

from enum import Enum
import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import pickup_dropoff, sampled_value
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class WindQControlMode(Enum):
    """IEC Table 22 general reactive-power controller modes."""

    voltage = 0
    reactive_power = 1
    open_loop_reactive_power = 2
    power_factor = 3
    open_loop_power_factor = 4


class WindUVRTQControlMode(Enum):
    """IEC Table 23 reactive current response modes during voltage dips."""

    voltage_dependent = 0
    prefault_plus_voltage_dependent = 1
    prefault_plus_voltage_and_postfault = 2


def _deadband(value: Expr, lower: Var, upper: Var) -> Expr:
    """Apply the IEC voltage-error deadband with continuous outside branches.

    :param value: Voltage error before the deadband.
    :param lower: Lower deadband edge.
    :param upper: Upper deadband edge.
    :return: Zero inside the deadband and edge-referenced error outside it.
    """
    below: Expr = sym.min(value - lower, Const(0.0))
    above: Expr = sym.max(value - upper, Const(0.0))
    return below + above


def build_wind_cont_q_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        iqh1: float = 1.0,
        iqmax: float = 1.0,
        iqmin: float = -1.0,
        iqpost: float = 0.0,
        kiq: float = 0.0,
        kiu: float = 0.0,
        kpq: float = 0.0,
        kpu: float = 0.0,
        kqv: float = 0.0,
        tiq: float = 0.0,
        tpfiltq: float = 0.0,
        rdroop: float = 0.0,
        tufiltq: float = 0.0,
        tpost: float = 0.0,
        tqord: float = 0.0,
        udb1: float = 0.0,
        udb2: float = 0.0,
        umax: float = 2.0,
        umin: float = 0.0,
        uqdip: float = 0.9,
        uref0: float = 1.0,
        xdroop: float = 0.0,
        q_control_mode: WindQControlMode = WindQControlMode.voltage,
        uvrt_q_control_mode: WindUVRTQControlMode = WindUVRTQControlMode.voltage_dependent,
        qmax: float | None = 1.0,
        qmin: float | None = -1.0,
        initial_active_power: float = 0.0,
        initial_reactive_power: float = 0.0,
        initial_voltage: float = 1.0,
        initial_reactive_current: float = 0.0,
        initial_tan_phi: float = 0.0,
        initial_external_reference: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC Figure 35 Q controller, voltage droop, and UVRT response.

    :param vfactory: Factory allocating equation graph symbols.
    :param name: Optional unique runtime model name.
    :param iqh1: Maximum additional reactive current during a dip.
    :param iqmax: Maximum normal reactive current.
    :param iqmin: Minimum normal reactive current.
    :param iqpost: Additional post-fault reactive current.
    :param kiq: Reactive-power PI integration gain.
    :param kiu: Voltage PI integration gain.
    :param kpq: Reactive-power PI proportional gain.
    :param kpu: Voltage PI proportional gain.
    :param kqv: Voltage-dependent reactive-current gain.
    :param tiq: Reactive-current output lag time in seconds (zero bypasses the lag).
    :param tpfiltq: Active-power filter time constant in seconds.
    :param rdroop: Resistive voltage-droop impedance in pu.
    :param tufiltq: Voltage filter time constant in seconds.
    :param tpost: Post-fault reactive-current duration in seconds.
    :param tqord: Reactive-current order lag in seconds.
    :param udb1: Lower voltage-error deadband edge.
    :param udb2: Upper voltage-error deadband edge.
    :param umax: Upper voltage PI integrator limit.
    :param umin: Lower voltage PI integrator limit.
    :param uqdip: Voltage threshold starting UVRT response.
    :param uref0: Load-flow voltage reference bias.
    :param xdroop: Inductive voltage-droop impedance in pu.
    :param q_control_mode: IEC general Q-control mode.
    :param uvrt_q_control_mode: IEC UVRT reactive-current mode.
    :param qmax: Constant reactive-power maximum; ``None`` exposes the IEC Q-limit input.
    :param qmin: Constant reactive-power minimum; ``None`` exposes the IEC Q-limit input.
    :param initial_active_power: Solved active power in pu.
    :param initial_reactive_power: Solved reactive power in pu.
    :param initial_voltage: Solved terminal voltage in pu.
    :param initial_reactive_current: Solved reactive current in pu.
    :param initial_tan_phi: Load-flow tangent of the initial power-factor angle.
    :param initial_external_reference: Solved Q or voltage reference for the selected mode.
    :return: `IqCmdPu` and the IEC three-stage `FUVRTPu` signal.
    :raises ValueError: Invalid mode values, time constants, limits or seeds.
    """
    values: tuple[float, ...] = (
        iqh1, iqmax, iqmin, iqpost, kiq, kiu, kpq, kpu, kqv, tiq, tpfiltq,
        rdroop, tufiltq, tpost, tqord, udb1, udb2, umax, umin, uqdip,
        uref0, xdroop, initial_active_power, initial_reactive_power,
        initial_voltage, initial_reactive_current, initial_tan_phi,
        initial_external_reference,
    )
    if qmax is not None:
        values += (qmax,)
    else:
        pass
    if qmin is not None:
        values += (qmin,)
    else:
        pass
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindContQIEC values must be finite')
    elif min(iqh1, iqmax, kqv, tiq, tpfiltq, rdroop, tufiltq, tpost, tqord, xdroop) < 0.0:
        raise ValueError('CGMES WindContQIEC magnitudes, impedances and times must be nonnegative')
    elif iqmin > iqmax or umin > umax or udb1 > udb2 or initial_voltage <= 0.0:
        raise ValueError('CGMES WindContQIEC limits or initial voltage are inconsistent')
    elif qmax is not None and qmin is not None and qmin > qmax:
        raise ValueError('CGMES WindContQIEC reactive-power limits are inconsistent')
    elif not isinstance(q_control_mode, WindQControlMode):
        raise ValueError('CGMES WindContQIEC general mode must use WindQControlMode')
    elif not isinstance(uvrt_q_control_mode, WindUVRTQControlMode):
        raise ValueError('CGMES WindContQIEC UVRT mode must use WindUVRTQControlMode')
    else:
        pass

    template_name: str = 'WindContQIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    reactive_dip_limit: Var = model.parameter('WindContQIEC.iqh1', iqh1)
    reactive_current_maximum: Var = model.parameter('WindContQIEC.iqmax', iqmax)
    reactive_current_minimum: Var = model.parameter('WindContQIEC.iqmin', iqmin)
    postfault_reactive_current: Var = model.parameter('WindContQIEC.iqpost', iqpost)
    reactive_power_integral_gain: Var = model.parameter('WindContQIEC.kiq', kiq)
    voltage_integral_gain: Var = model.parameter('WindContQIEC.kiu', kiu)
    reactive_power_proportional_gain: Var = model.parameter('WindContQIEC.kpq', kpq)
    voltage_proportional_gain: Var = model.parameter('WindContQIEC.kpu', kpu)
    uvrt_reactive_gain: Var = model.parameter('WindContQIEC.kqv', kqv)
    reactive_current_lag_time: Var = model.parameter('WindContQIEC.tiq', tiq)
    active_power_filter_time: Var = model.parameter('WindContQIEC.tpfiltq', tpfiltq)
    resistive_droop: Var = model.parameter('WindContQIEC.rdroop', rdroop)
    voltage_filter_time: Var = model.parameter('WindContQIEC.tufiltq', tufiltq)
    postfault_time: Var = model.parameter('WindContQIEC.tpost', tpost)
    reactive_order_time: Var = model.parameter('WindContQIEC.tqord', tqord)
    voltage_deadband_lower: Var = model.parameter('WindContQIEC.udb1', udb1)
    voltage_deadband_upper: Var = model.parameter('WindContQIEC.udb2', udb2)
    voltage_integral_maximum: Var = model.parameter('WindContQIEC.umax', umax)
    voltage_integral_minimum: Var = model.parameter('WindContQIEC.umin', umin)
    dip_voltage: Var = model.parameter('WindContQIEC.uqdip', uqdip)
    voltage_reference_bias: Var = model.parameter('WindContQIEC.uref0', uref0)
    inductive_droop: Var = model.parameter('WindContQIEC.xdroop', xdroop)

    active_power_input: Var = model.input('PwtPu', Const(initial_active_power))
    reactive_power_input: Var = model.input('QwtPu', Const(initial_reactive_power))
    terminal_voltage_input: Var = model.input('UwtPu', Const(initial_voltage))
    external_reference: Var = model.input('XwtRefPu', Const(initial_external_reference))
    freeze_input: Var = model.input('FreezePu', Const(0.0))
    initial_power_factor: Var = model.parameter('WindContQIEC.tanPhiInit', initial_tan_phi)
    if qmax is None and qmin is None:
        reactive_power_maximum: Var = model.input('QwtMaxPu', Const(1.0))
        reactive_power_minimum: Var = model.input('QwtMinPu', Const(-1.0))
    elif qmax is not None and qmin is not None:
        reactive_power_maximum = model.parameter('WindContQLimIEC.qmax', qmax)
        reactive_power_minimum = model.parameter('WindContQLimIEC.qmin', qmin)
    else:
        raise ValueError('CGMES WindContQIEC dynamic Q limits must be supplied as a pair')

    filtered_active_power: Var
    if tpfiltq > 0.0:
        # Annex G.4 holds a positive-time filter's state when the freeze flag is raised.
        filtered_active_power = vfactory.add_var(f'FilteredPwtPu_{template_name}')
        model.differential(
            filtered_active_power,
            (active_power_input - filtered_active_power) * (Const(1.0) - freeze_input)
            / active_power_filter_time,
            Const(initial_active_power),
        )
    else:
        # Figure G.6 replaces a zero-time filter with a freeze-controlled sample-and-hold.
        filtered_active_power = vfactory.add_var(f'FilteredPwtPu_{template_name}')
        model.block.mode_dict[filtered_active_power] = Const(initial_active_power)
        model.block.procedural_logic.append(sampled_value(
            output=filtered_active_power,
            source=(
                (Const(1.0) - freeze_input) * active_power_input
                + freeze_input * filtered_active_power
            ),
            name=f'WindContQIEC.ActivePowerSample_{template_name}',
        ))
    filtered_voltage: Var
    if tufiltq > 0.0:
        filtered_voltage = vfactory.add_var(f'FilteredUwtPu_{template_name}')
        model.differential(
            filtered_voltage,
            (terminal_voltage_input - filtered_voltage) * (Const(1.0) - freeze_input)
            / voltage_filter_time,
            Const(initial_voltage),
        )
    else:
        # The zero-time voltage path uses the same accepted-step freeze state as the P path.
        filtered_voltage = vfactory.add_var(f'FilteredUwtPu_{template_name}')
        model.block.mode_dict[filtered_voltage] = Const(initial_voltage)
        model.block.procedural_logic.append(sampled_value(
            output=filtered_voltage,
            source=(
                (Const(1.0) - freeze_input) * terminal_voltage_input
                + freeze_input * filtered_voltage
            ),
            name=f'WindContQIEC.VoltageSample_{template_name}',
        ))
    voltage_denominator: Expr = sym.max(filtered_voltage, Const(0.01))
    voltage_drop_real: Expr = (
        filtered_voltage
        - resistive_droop * active_power_input / voltage_denominator
        - inductive_droop * reactive_power_input / voltage_denominator
    )
    voltage_drop_imaginary: Expr = (
        inductive_droop * active_power_input / voltage_denominator
        - resistive_droop * reactive_power_input / voltage_denominator
    )
    droop_voltage: Var = model.algebraic(
        'UdroopPu',
        sym.sqrt(voltage_drop_real ** 2 + voltage_drop_imaginary ** 2),
        Const(initial_voltage),
    )
    initial_voltage_denominator: float = max(initial_voltage, 0.01)
    initial_droop_real: float = (
        initial_voltage
        - rdroop * initial_active_power / initial_voltage_denominator
        - xdroop * initial_reactive_power / initial_voltage_denominator
    )
    initial_droop_imaginary: float = (
        xdroop * initial_active_power / initial_voltage_denominator
        - rdroop * initial_reactive_power / initial_voltage_denominator
    )
    initial_droop_voltage: float = math.hypot(initial_droop_real, initial_droop_imaginary)
    initial_reactive_voltage_offset: float = initial_droop_voltage - uref0

    # General mode selection chooses voltage, closed-loop Q/PF, or open-loop Q/PF.
    q_reference: Expr = external_reference
    if q_control_mode == WindQControlMode.power_factor:
        q_reference = filtered_active_power * initial_power_factor
    elif q_control_mode == WindQControlMode.open_loop_power_factor:
        q_reference = filtered_active_power * initial_power_factor
    else:
        pass
    limited_q_reference: Expr = sym.hard_sat(
        q_reference, reactive_power_minimum, reactive_power_maximum,
    )
    filtered_q_reference: Var = model.lag(
        'QorderPu', limited_q_reference, reactive_order_time,
        tqord, Const(initial_reactive_power),
    )
    q_error: Expr = filtered_q_reference - reactive_power_input
    q_integral: Var = vfactory.add_var(f'WindContQIEC.QIntegralPu_{template_name}')
    q_loop_enabled: float = 1.0 if q_control_mode in (
        WindQControlMode.reactive_power, WindQControlMode.power_factor,
    ) else 0.0
    q_integral_state: Var = model.differential(
        q_integral,
        Const(q_loop_enabled) * reactive_power_integral_gain * q_error,
        Const(initial_reactive_voltage_offset),
    )
    q_controller_voltage: Expr = (
        reactive_power_proportional_gain * q_error + q_integral_state
    )
    if q_control_mode == WindQControlMode.voltage:
        voltage_reference: Expr = voltage_reference_bias + external_reference
    elif q_control_mode == WindQControlMode.reactive_power:
        voltage_reference = voltage_reference_bias + q_controller_voltage
    elif q_control_mode == WindQControlMode.power_factor:
        voltage_reference = voltage_reference_bias + q_controller_voltage
    else:
        voltage_reference = voltage_reference_bias
    voltage_error: Expr = _deadband(voltage_reference - droop_voltage, voltage_deadband_lower, voltage_deadband_upper)
    voltage_integral: Var = vfactory.add_var(f'WindContQIEC.UIntegralPu_{template_name}')
    voltage_loop_enabled: float = 1.0 if q_control_mode in (
        WindQControlMode.voltage,
        WindQControlMode.reactive_power,
        WindQControlMode.power_factor,
    ) else 0.0
    voltage_integral_state: Var = model.differential(
        voltage_integral,
        Const(voltage_loop_enabled) * voltage_integral_gain * voltage_error,
        Const(initial_reactive_current),
        voltage_integral_minimum,
        voltage_integral_maximum,
    )
    closed_loop_current: Expr = (
        voltage_proportional_gain * voltage_error + voltage_integral_state
    )
    open_loop_q_current: Expr = filtered_q_reference / voltage_denominator
    normal_current: Expr = closed_loop_current
    if q_control_mode == WindQControlMode.open_loop_reactive_power:
        normal_current = open_loop_q_current
    elif q_control_mode == WindQControlMode.open_loop_power_factor:
        normal_current = open_loop_q_current
    else:
        pass
    # The IEC delay flag is 1 in a dip, 2 for the post-dip timer, and 0 otherwise.
    voltage_dip: Expr = sym.heaviside(dip_voltage - filtered_voltage)
    delay_hold: Var = vfactory.add_var(f'WindContQIEC.DelayHold_{template_name}')
    model.block.mode_dict[delay_hold] = Const(0.0)
    model.block.procedural_logic.append(pickup_dropoff(
        output=delay_hold,
        boolexpr=voltage_dip,
        Tpick=Const(0.0),
        Tdrop=postfault_time,
        name=f'WindContQIEC.DelayFlagTimer_{template_name}',
    ))
    fault_stage: Var = model.algebraic('FUVRTPu', voltage_dip + Const(2.0) * (delay_hold - voltage_dip), Const(0.0))
    voltage_dependent_current: Expr = sym.hard_sat(
        uvrt_reactive_gain * (voltage_deadband_lower - filtered_voltage),
        Const(0.0), reactive_dip_limit,
    )
    prefault_current: Expr = normal_current
    fault_current: Expr = voltage_dependent_current
    if uvrt_q_control_mode == WindUVRTQControlMode.prefault_plus_voltage_dependent:
        fault_current = prefault_current + voltage_dependent_current
    elif uvrt_q_control_mode == WindUVRTQControlMode.prefault_plus_voltage_and_postfault:
        fault_current = prefault_current + voltage_dependent_current
    else:
        pass
    postfault_current: Expr = prefault_current
    if uvrt_q_control_mode == WindUVRTQControlMode.prefault_plus_voltage_and_postfault:
        postfault_current = prefault_current + postfault_reactive_current
    else:
        pass
    current_command: Expr = (
        (Const(1.0) - voltage_dip) * (Const(1.0) - delay_hold) * normal_current
        + voltage_dip * fault_current
        + (delay_hold - voltage_dip) * postfault_current
    )
    limited_current: Expr = sym.hard_sat(
        current_command, reactive_current_minimum, reactive_current_maximum,
    )
    if tiq > 0.0:
        # IEC 61400-27-1:2015 retains this fast current state and freezes it during LVRT.
        reactive_current_state: Var = vfactory.add_var(f'WindContQIEC.IqLagPu_{template_name}')
        reactive_current_output: Var = model.differential(
            reactive_current_state,
            (Const(1.0) - voltage_dip)
            * (limited_current - reactive_current_state)
            / reactive_current_lag_time,
            Const(initial_reactive_current),
        )
    else:
        reactive_current_output = limited_current
    reactive_current_command: Var = model.algebraic(
        'IqCmdPu', reactive_current_output, Const(initial_reactive_current),
    )
    template: RmsModelTemplate = model.finish(
        (reactive_current_command, fault_stage),
    'IEC 61400-27-1:2015 Figure 35 Q modes, Annex G.4 freeze-aware P/U filters, '
        'droop, UVRT delay flag and current injection.',
    )
    template.comment += (
        ' Annex G.4 Figure G.6 zero-time P/U filters use accepted-step freeze-controlled '
        'sample-and-hold logic; the `FreezePu` driver remains a host signal.'
    )
    return template
