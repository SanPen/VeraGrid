# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC 61400-27-1 Annex D.1 wind-plant reactive controller."""

import math
from enum import Enum
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    _build_clipped_lookup_expression,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class WindPlantReactiveControlMode(Enum):
    """Build-time selectors defined by the CGMES WindPlantQcontrolModeKind RDF enum."""

    reactive_power = 'reactivePower'
    power_factor = 'powerFactor'
    uq_static = 'uqStatic'
    voltage_control = 'voltageControl'


def build_wind_plant_reactive_control_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dxrefmax: float = 1.0,
        dxrefmin: float = -1.0,
        kiwpx: float = 0.0,
        kiwpxmax: float = 999.0,
        kiwpxmin: float = -999.0,
        kpwpx: float = 0.0,
        kwpqref: float = 1.0,
        kwpqu: float = 0.0,
        tuqfilt: float = 0.0,
        twppfiltq: float = 0.0,
        twpqfiltq: float = 0.0,
        twpufiltq: float = 0.0,
        txft: float = 0.0,
        txfv: float = 0.0,
        uwpqdip: float = 0.0,
        mode: WindPlantReactiveControlMode = WindPlantReactiveControlMode.reactive_power,
        xrefmax: float = 999.0,
        xrefmin: float = -999.0,
        uq_curve: Sequence[tuple[float, float]] = (),
        initial_active_power: float = 0.0,
        initial_reactive_power: float = 0.0,
        initial_voltage: float = 1.0,
        initial_tan_phi: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC Annex D.1 plant Q/voltage controller equations.

    :param vfactory: Factory allocating equation-graph symbols.
    :param name: Optional unique runtime model name.
    :param dxrefmax: Maximum positive output-reference ramp in pu/s.
    :param dxrefmin: Minimum negative output-reference ramp in pu/s.
    :param kiwpx: PI integral gain in 1/s.
    :param kiwpxmax: Maximum PI integral contribution in pu.
    :param kiwpxmin: Minimum PI integral contribution in pu.
    :param kpwpx: PI proportional gain.
    :param kwpqref: Gain on the plant reactive-power reference.
    :param kwpqu: Voltage-control reactive-power droop gain.
    :param tuqfilt: UQ-static lookup-output filter time in seconds.
    :param twppfiltq: Active-power measurement filter time in seconds.
    :param twpqfiltq: Reactive-power measurement filter time in seconds.
    :param twpufiltq: Voltage measurement filter time in seconds.
    :param txft: Lead time in the reference transfer function, in seconds.
    :param txfv: Lag time in the reference transfer function, in seconds.
    :param uwpqdip: Voltage threshold that freezes Q-controller integration.
    :param mode: Canonical reactive-power, power-factor, UQ-static, or voltage mode.
    :param xrefmax: Maximum WT reactive-power/voltage reference in pu.
    :param xrefmin: Minimum WT reactive-power/voltage reference in pu.
    :param uq_curve: Ordered voltage-error/reactive-power UQ-static curve.
    :param initial_active_power: Solved plant active power in pu.
    :param initial_reactive_power: Solved plant reactive power in pu.
    :param initial_voltage: Solved plant voltage in pu.
    :param initial_tan_phi: Load-flow tangent of the power-factor angle.
    :return: Equation-backed `XwtRefPu` plant controller.
    :raises ValueError: Invalid parameters, selector, or UQ lookup data.
    """
    values: tuple[float, ...] = (
        dxrefmax, dxrefmin, kiwpx, kiwpxmax, kiwpxmin, kpwpx,
        kwpqref, kwpqu, tuqfilt, twppfiltq, twpqfiltq, twpufiltq,
        txft, txfv, uwpqdip, xrefmax, xrefmin, initial_active_power,
        initial_reactive_power, initial_voltage, initial_tan_phi,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindPlantReactiveControlIEC values must be finite')
    elif min(kiwpx, tuqfilt, twppfiltq, twpqfiltq, twpufiltq, txft, txfv, uwpqdip) < 0.0:
        raise ValueError('CGMES WindPlantReactiveControlIEC gains, times, and threshold must be nonnegative')
    elif kiwpxmin > kiwpxmax or xrefmin > xrefmax:
        raise ValueError('CGMES WindPlantReactiveControlIEC limits are reversed')
    elif dxrefmin > 0.0 or dxrefmax < 0.0 or txft > txfv:
        raise ValueError('CGMES WindPlantReactiveControlIEC ramp or transfer limits are invalid')
    elif not isinstance(mode, WindPlantReactiveControlMode):
        raise ValueError('CGMES WindPlantReactiveControlIEC selector is invalid')
    elif mode is WindPlantReactiveControlMode.uq_static and len(uq_curve) < 2:
        raise ValueError('CGMES WindPlantReactiveControlIEC UQ-static mode requires its qwp curve')
    else:
        pass

    for point_index in range(len(uq_curve)):
        curve_voltage: float = float(uq_curve[point_index][0])
        curve_reactive_power: float = float(uq_curve[point_index][1])
        if not math.isfinite(curve_voltage) or not math.isfinite(curve_reactive_power):
            raise ValueError('CGMES WindPlantReactiveControlIEC lookup values must be finite')
        elif point_index > 0 and curve_voltage <= float(uq_curve[point_index - 1][0]):
            raise ValueError('CGMES WindPlantReactiveControlIEC UQ lookup inputs must increase')
        else:
            pass

    template_name: str = 'WindPlantReactiveControlIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    integral_gain: Var = model.parameter('WindPlantReactiveControlIEC.kiwpx', kiwpx)
    integral_maximum: Var = model.parameter('WindPlantReactiveControlIEC.kiwpxmax', kiwpxmax)
    integral_minimum: Var = model.parameter('WindPlantReactiveControlIEC.kiwpxmin', kiwpxmin)
    proportional_gain: Var = model.parameter('WindPlantReactiveControlIEC.kpwpx', kpwpx)
    reactive_reference_gain: Var = model.parameter('WindPlantReactiveControlIEC.kwpqref', kwpqref)
    voltage_droop_gain: Var = model.parameter('WindPlantReactiveControlIEC.kwpqu', kwpqu)
    uq_filter_time: Var = model.parameter('WindPlantReactiveControlIEC.tuqfilt', tuqfilt)
    power_filter_time: Var = model.parameter('WindPlantReactiveControlIEC.twppfiltq', twppfiltq)
    reactive_filter_time: Var = model.parameter('WindPlantReactiveControlIEC.twpqfiltq', twpqfiltq)
    voltage_filter_time: Var = model.parameter('WindPlantReactiveControlIEC.twpufiltq', twpufiltq)
    lead_time: Var = model.parameter('WindPlantReactiveControlIEC.txft', txft)
    lag_time: Var = model.parameter('WindPlantReactiveControlIEC.txfv', txfv)
    voltage_dip_threshold: Var = model.parameter('WindPlantReactiveControlIEC.uwpqdip', uwpqdip)
    reference_maximum: Var = model.parameter('WindPlantReactiveControlIEC.xrefmax', xrefmax)
    reference_minimum: Var = model.parameter('WindPlantReactiveControlIEC.xrefmin', xrefmin)
    reference_ramp_up: Var = model.parameter('WindPlantReactiveControlIEC.dxrefmax', dxrefmax)
    reference_ramp_down: Var = model.parameter('WindPlantReactiveControlIEC.dxrefmin', dxrefmin)
    initial_reference: float = (
        initial_voltage
        if mode is WindPlantReactiveControlMode.voltage_control
        else initial_reactive_power
    )
    initial_q_reference: float = (
        initial_reactive_power / kwpqref
        if kwpqref != 0.0
        else initial_reactive_power
    )
    initial_u_reference: float = initial_voltage + kwpqu * initial_reactive_power

    # These plant measurements/references remain host-owned ports until an
    # aggregate plant signal source is available in the CGMES graph.
    active_power_input: Var = model.input('PwpPu', Const(initial_active_power))
    reactive_power_input: Var = model.input('QwpPu', Const(initial_reactive_power))
    voltage_input: Var = model.input('UwpPu', Const(initial_voltage))
    reactive_reference_input: Var = model.input('QwpRefPu', Const(initial_q_reference))
    voltage_reference_input: Var = model.input('UwpRefPu', Const(initial_u_reference))
    filtered_active_power: Var = model.lag(
        'FilteredPwpPu', active_power_input, power_filter_time, twppfiltq,
        Const(initial_active_power),
    )
    filtered_reactive_power: Var = model.lag(
        'FilteredQwpPu', reactive_power_input, reactive_filter_time, twpqfiltq,
        Const(initial_reactive_power),
    )
    filtered_voltage: Var = model.lag(
        'FilteredUwpPu', voltage_input, voltage_filter_time, twpufiltq,
        Const(initial_voltage),
    )
    voltage_error: Expr = voltage_reference_input - filtered_voltage
    q_reference: Expr
    control_error: Expr
    reference_base: Expr
    if mode is WindPlantReactiveControlMode.reactive_power:
        q_reference = reactive_reference_gain * reactive_reference_input
        control_error = q_reference - filtered_reactive_power
        reference_base = q_reference
    elif mode is WindPlantReactiveControlMode.power_factor:
        initial_power_factor_tangent: Var = model.parameter(
            'WindPlantReactiveControlIEC.tanPhiWPinit', initial_tan_phi,
        )
        q_reference = initial_power_factor_tangent * filtered_active_power
        control_error = q_reference - filtered_reactive_power
        reference_base = q_reference
    elif mode is WindPlantReactiveControlMode.uq_static:
        uq_curve_inputs: list[Var] = list()
        uq_curve_outputs: list[Var] = list()
        for point_index in range(len(uq_curve)):
            uq_curve_inputs.append(model.parameter(
                f'WindPlantReactiveControlIEC.qwp_voltage_error_{point_index}',
                float(uq_curve[point_index][0]),
            ))
            uq_curve_outputs.append(model.parameter(
                f'WindPlantReactiveControlIEC.qwp_reactive_power_{point_index}',
                float(uq_curve[point_index][1]),
            ))
        else:
            pass
        uq_reactive_power: Expr = _build_clipped_lookup_expression(
            voltage_error, uq_curve_inputs, uq_curve_outputs,
        )
        filtered_uq_reactive_power: Var = model.lag(
            'FilteredUQReactivePowerPu', uq_reactive_power, uq_filter_time,
            tuqfilt, Const(initial_reactive_power),
        )
        q_reference = filtered_uq_reactive_power
        control_error = q_reference - filtered_reactive_power
        reference_base = q_reference
    else:
        q_reference = reactive_reference_input
        control_error = voltage_error - voltage_droop_gain * filtered_reactive_power
        reference_base = voltage_reference_input

    # Integrate the PI correction only while the controller is outside UVRT.
    integral_state: Var = vfactory.add_var(name=f'PlantQPIIntegralPu_{template_name}')
    provisional_pi_output: Expr = proportional_gain * control_error + integral_state
    provisional_reference: Expr = reference_base + provisional_pi_output
    limited_reference: Var = model.algebraic(
        'LimitedXwtRefPu',
        sym.hard_sat(provisional_reference, reference_minimum, reference_maximum),
        Const(min(max(initial_reference, xrefmin), xrefmax)),
    )
    reference_lag_output: Var = model.lead_lag(
        'ReferenceTransfer', limited_reference, lead_time, lag_time,
        txft, txfv, Const(min(max(initial_reference, xrefmin), xrefmax)),
    )
    reference_state: Var = vfactory.add_var(name=f'XwtRefRampStatePu_{template_name}')
    ramp_delta: Expr = reference_lag_output - reference_state
    ramp_derivative: Expr = (
        sym.heaviside(ramp_delta) * reference_ramp_up
        + sym.heaviside(-ramp_delta) * reference_ramp_down
    )
    xwt_reference: Var = model.differential(
        reference_state,
        ramp_derivative,
        Const(min(max(initial_reference, xrefmin), xrefmax)),
        reference_minimum,
        reference_maximum,
    )

    # Freeze the PI when UVRT is active or a hard/rate limit blocks further motion.
    pi_drive: Expr = integral_gain * control_error
    uvrt_freeze: Expr = sym.heaviside(voltage_dip_threshold - filtered_voltage)
    upper_freeze: Expr = sym.heaviside(
        provisional_reference - reference_maximum,
    ) * sym.heaviside(pi_drive)
    lower_freeze: Expr = sym.heaviside(
        reference_minimum - provisional_reference,
    ) * sym.heaviside(-pi_drive)
    ramp_up_freeze: Expr = sym.heaviside(
        reference_lag_output - xwt_reference,
    ) * sym.heaviside(pi_drive)
    ramp_down_freeze: Expr = sym.heaviside(
        xwt_reference - reference_lag_output,
    ) * sym.heaviside(-pi_drive)
    limitation_freeze: Expr = sym.max(
        sym.max(upper_freeze, lower_freeze),
        sym.max(ramp_up_freeze, ramp_down_freeze),
    )
    freeze_signal: Expr = sym.max(uvrt_freeze, limitation_freeze)
    model.differential(
        integral_state,
        pi_drive * (Const(1.0) - freeze_signal),
        Const(0.0),
        integral_minimum,
        integral_maximum,
    )
    return model.finish(
        (xwt_reference,),
        'IEC 61400-27-1 Annex D.1 WP reactive/voltage PI control, mode selection, limits, and UVRT freeze.',
    )
