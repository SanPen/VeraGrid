# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEC Type 3 active-power controller."""

import math
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    _build_clipped_lookup_expression,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import delay, gradlim_const
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_wind_cont_p_type3_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dpmax: float = 999.0,
        dprefmax: float = 999.0,
        dprefmin: float = -999.0,
        dthetamax: float = 999.0,
        dthetamaxuvrt: float = 999.0,
        kdtd: float = 0.0,
        kip: float = 0.0,
        kpp: float = 0.0,
        mpuvrt: bool = False,
        omegaoffset: float = 0.0,
        pdtdmax: float = 0.0,
        tdvs: float = 0.0,
        thetaemin: float = 0.0,
        thetauscale: float = 0.0,
        tomegafiltp3: float = 0.0,
        tpfiltp3: float = 0.0,
        tpord: float = 0.0,
        tufiltp3: float = 0.0,
        tomegaref: float = 0.0,
        udvs: float = 0.0,
        updip: float = 0.0,
        omegadtd: float = 0.0,
        zeta: float = 0.0,
        omegap_curve: Sequence[tuple[float, float]] = (),
        initial_power: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC 61400-27-1 Type 3 P-control and torque-PI realization.

    :param vfactory: Factory allocating model symbols.
    :param name: Optional unique runtime model name.
    :param dpmax: Maximum power-order ramp rate in pu per second.
    :param dprefmax: Positive turbine reference ramp rate in pu per second.
    :param dprefmin: Negative turbine reference ramp rate in pu per second.
    :param dthetamax: Torque ramp-rate magnitude in pu per second (RDF spelling).
    :param dthetamaxuvrt: UVRT torque ramp-rate magnitude in pu per second.
    :param kdtd: Active drivetrain damping gain.
    :param kip: Torque PI integral gain.
    :param kpp: Torque PI proportional gain.
    :param mpuvrt: Select voltage-control torque reset during UVRT.
    :param omegaoffset: Offset added to the power-speed reference curve.
    :param pdtdmax: Absolute active drivetrain damping power limit.
    :param tdvs: Deep-voltage-sag hold delay in seconds.
    :param thetaemin: Minimum electrical torque (RDF spelling).
    :param thetauscale: Reset-torque voltage scale.
    :param tomegafiltp3: Generator-speed measurement filter time.
    :param tpfiltp3: Active-power measurement filter time.
    :param tpord: Power-order lag time.
    :param tufiltp3: Voltage measurement filter time.
    :param tomegaref: Speed-reference filter time.
    :param udvs: Deep-voltage-sag threshold.
    :param updip: P-control voltage-dip threshold.
    :param omegadtd: Active drivetrain damping frequency.
    :param zeta: Active drivetrain damping damping ratio.
    :param omegap_curve: Ordered `(power, speed)` values for `WindLookupTableFunctionKind.omegap`.
    :param initial_power: Solved initial turbine active power in pu.
    :return: Equation-backed controller with `IpCmdPu`, `OmegaRefPu`, and `PordPu` outputs.
    :raises ValueError: Invalid limits, time constants, damping, or lookup curve.
    """
    scalar_values: tuple[float, ...] = (
        dpmax, dprefmax, dprefmin, dthetamax, dthetamaxuvrt, kdtd, kip, kpp,
        omegaoffset, pdtdmax, tdvs, thetaemin, thetauscale, tomegafiltp3,
        tpfiltp3, tpord, tufiltp3, tomegaref, udvs, updip, omegadtd, zeta,
        initial_power,
    )
    if not all(math.isfinite(value) for value in scalar_values):
        raise ValueError('CGMES WindContPType3IEC values must be finite')
    elif min(dpmax, dprefmax, dthetamax, dthetamaxuvrt, pdtdmax, tdvs,
             tomegafiltp3, tpfiltp3, tpord, tufiltp3, tomegaref,
             omegadtd, zeta, initial_power) < 0.0:
        raise ValueError('CGMES WindContPType3IEC magnitudes and times must be nonnegative')
    elif dprefmin > 0.0:
        raise ValueError('CGMES WindContPType3IEC dprefmin must be nonpositive')
    elif not omegap_curve or len(omegap_curve) < 2:
        raise ValueError('CGMES WindContPType3IEC requires at least two omegap curve points')
    else:
        pass

    point_index: int
    for point_index in range(len(omegap_curve)):
        curve_power: float = float(omegap_curve[point_index][0])
        curve_speed: float = float(omegap_curve[point_index][1])
        if not math.isfinite(curve_power) or not math.isfinite(curve_speed):
            raise ValueError('CGMES WindContPType3IEC lookup values must be finite')
        elif point_index > 0 and curve_power <= float(omegap_curve[point_index - 1][0]):
            raise ValueError('CGMES WindContPType3IEC lookup power values must increase')
        else:
            pass

    template_name: str = 'WindContPType3IEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)

    # Declare the exact CGMES RDF properties so the parsed parameters remain visible.
    power_ramp_maximum: Var = model.parameter('WindContPType3IEC.dpmax', dpmax)
    reference_ramp_maximum: Var = model.parameter('WindContPType3IEC.dprefmax', dprefmax)
    reference_ramp_minimum: Var = model.parameter('WindContPType3IEC.dprefmin', dprefmin)
    torque_ramp_magnitude: Var = model.parameter('WindContPType3IEC.dthetamax', dthetamax)
    torque_uvrt_ramp_magnitude: Var = model.parameter(
        'WindContPType3IEC.dthetamaxuvrt', dthetamaxuvrt,
    )
    damping_gain: Var = model.parameter('WindContPType3IEC.kdtd', kdtd)
    integral_gain: Var = model.parameter('WindContPType3IEC.kip', kip)
    proportional_gain: Var = model.parameter('WindContPType3IEC.kpp', kpp)
    uvrt_voltage_mode: Var = model.parameter(
        'WindContPType3IEC.mpuvrt', 1.0 if mpuvrt else 0.0,
    )
    speed_offset: Var = model.parameter('WindContPType3IEC.omegaoffset', omegaoffset)
    damping_power_limit: Var = model.parameter('WindContPType3IEC.pdtdmax', pdtdmax)
    deep_sag_delay: Var = model.parameter('WindContPType3IEC.tdvs', tdvs)
    minimum_torque: Var = model.parameter('WindContPType3IEC.thetaemin', thetaemin)
    reset_torque_voltage_scale: Var = model.parameter(
        'WindContPType3IEC.thetauscale', thetauscale,
    )
    generator_speed_filter_time: Var = model.parameter(
        'WindContPType3IEC.tomegafiltp3', tomegafiltp3,
    )
    active_power_filter_time: Var = model.parameter(
        'WindContPType3IEC.tpfiltp3', tpfiltp3,
    )
    power_order_filter_time: Var = model.parameter('WindContPType3IEC.tpord', tpord)
    voltage_filter_time: Var = model.parameter('WindContPType3IEC.tufiltp3', tufiltp3)
    speed_reference_filter_time: Var = model.parameter(
        'WindContPType3IEC.tomegaref', tomegaref,
    )
    deep_sag_threshold: Var = model.parameter('WindContPType3IEC.udvs', udvs)
    voltage_dip_threshold: Var = model.parameter('WindContPType3IEC.updip', updip)
    damping_frequency: Var = model.parameter('WindContPType3IEC.omegadtd', omegadtd)
    damping_ratio: Var = model.parameter('WindContPType3IEC.zeta', zeta)

    # Expose the turbine-terminal signals as ports consumed by the composite model.
    power_reference: Var = model.input('PwtRefPu', Const(initial_power))
    measured_power: Var = model.input('PwtPu', Const(initial_power))
    generator_speed: Var = model.input('OmegaGenPu', Const(1.0))
    terminal_voltage: Var = model.input('UwtPu', Const(1.0))
    active_current_limit: Var = model.input('IpMaxPu', Const(1.0))

    # Preserve every lookup sample as a runtime parameter for exact RDF curve import.
    lookup_x_variables: list[Var] = list()
    lookup_y_variables: list[Var] = list()
    for point_index in range(len(omegap_curve)):
        lookup_x_variables.append(model.parameter(
            f'WindContPType3IEC.omegap_power_{point_index}',
            float(omegap_curve[point_index][0]),
        ))
        lookup_y_variables.append(model.parameter(
            f'WindContPType3IEC.omegap_speed_{point_index}',
            float(omegap_curve[point_index][1]),
        ))
    else:
        pass

    # IEC Annex G.3 rate limiters retain sampled outputs between solver boundaries.
    limited_reference: Var = vfactory.add_var(f'PwtRefLimitedPu_{template_name}')
    model.block.event_dict[limited_reference] = vfactory.add_const(value=initial_power)
    model.block.procedural_logic.append(gradlim_const(
        power_reference,
        reference_ramp_minimum,
        reference_ramp_maximum,
        limited_reference,
        name=f'WindContPType3IEC.ReferenceRamp_{template_name}',
    ))
    limited_power_order: Var = vfactory.add_var(f'PordRateLimitedPu_{template_name}')
    model.block.event_dict[limited_power_order] = vfactory.add_const(value=initial_power)

    # Filters precede the lookup and control errors as required by Figure 31.
    filtered_power: Var = model.lag(
        'FilteredPwtPu', measured_power, active_power_filter_time,
        tpfiltp3, Const(initial_power),
    )
    filtered_speed: Var = model.lag(
        'FilteredOmegaGenPu', generator_speed, generator_speed_filter_time,
        tomegafiltp3, Const(1.0),
    )
    filtered_voltage: Var = model.lag(
        'FilteredUwtPu', terminal_voltage, voltage_filter_time,
        tufiltp3, Const(1.0),
    )
    lookup_speed: Expr = _build_clipped_lookup_expression(
        filtered_power, lookup_x_variables, lookup_y_variables,
    )
    unfiltered_speed_reference: Expr = lookup_speed + speed_offset
    speed_reference: Var = model.lag(
        'OmegaRefPu', unfiltered_speed_reference, speed_reference_filter_time,
        tomegaref, Const(1.0),
    )
    speed_error: Expr = filtered_speed - speed_reference

    # Drivetrain damping uses the standard second-order high-pass transfer.
    if kdtd == 0.0 or pdtdmax == 0.0 or omegadtd == 0.0 or zeta == 0.0:
        damping_power: Var = model.algebraic(
            'DampingPowerPu', Const(0.0), Const(0.0),
        )
    else:
        damping_speed_state: Var = vfactory.add_var(f'PType3DampingSpeedState_{template_name}')
        damping_derivative_state: Var = vfactory.add_var(
            f'PType3DampingDerivativeState_{template_name}',
        )
        model.differential(
            damping_speed_state,
            damping_derivative_state,
            Const(0.0),
        )
        model.differential(
            damping_derivative_state,
            (filtered_speed - Const(1.0))
            - Const(2.0) * damping_ratio * damping_frequency * damping_derivative_state
            - damping_frequency * damping_frequency * damping_speed_state,
            Const(0.0),
        )
        damping_power = model.algebraic(
            'DampingPowerPu',
            sym.hard_sat(
                damping_gain * Const(2.0) * damping_ratio * damping_frequency
                * damping_derivative_state,
                -damping_power_limit,
                damping_power_limit,
            ),
            Const(0.0),
        )

    # The order follows the filtered reference with the IEC dpmax ramp and Tpord lag.
    power_order_source: Expr = limited_reference + damping_power
    model.block.procedural_logic.append(gradlim_const(
        power_order_source,
        -power_ramp_maximum,
        power_ramp_maximum,
        limited_power_order,
        name=f'WindContPType3IEC.PowerOrderRamp_{template_name}',
    ))
    power_order: Var = model.lag(
        'PordPu', limited_power_order, power_order_filter_time,
        tpord, Const(initial_power),
    )

    # The voltage dip detector holds torque PI memory after a deep sag.
    deep_sag_active: Var = vfactory.add_var(f'WindPType3DeepSag_{template_name}')
    model.block.mode_dict[deep_sag_active] = Const(0.0)
    model.block.procedural_logic.append(delay(
        sym.heaviside(deep_sag_threshold - filtered_voltage),
        deep_sag_delay,
        deep_sag_active,
        name=f'WindContPType3IEC.DeepSagDelay_{template_name}',
    ))
    voltage_dip_active: Expr = sym.max(
        sym.heaviside(voltage_dip_threshold - filtered_voltage), deep_sag_active,
    )
    uvrt_active: Expr = uvrt_voltage_mode * voltage_dip_active

    # Torque PI output is bounded by the current capability and minimum torque.
    maximum_torque: Expr = sym.max(
        minimum_torque,
        sym.safe_divide(
            active_current_limit * filtered_voltage,
            filtered_speed,
            Const(1.0),
        ),
    )
    torque_integral: Var = vfactory.add_var(f'PType3TorqueIntegralPu_{template_name}')
    torque_demand: Expr = proportional_gain * speed_error + torque_integral
    torque_limited: Expr = sym.hard_sat(torque_demand, minimum_torque, maximum_torque)
    torque_error_direction: Expr = sym.heaviside(integral_gain * speed_error)
    torque_upper_limited: Expr = sym.heaviside(torque_demand - maximum_torque)
    torque_lower_limited: Expr = sym.heaviside(minimum_torque - torque_demand)
    torque_integral_rate: Expr = integral_gain * speed_error * (
        torque_error_direction * (Const(1.0) - torque_upper_limited)
        + (Const(1.0) - torque_error_direction)
        * (Const(1.0) - torque_lower_limited)
    ) * (Const(1.0) - uvrt_active)
    model.differential(torque_integral, torque_integral_rate, Const(initial_power))

    # Reset-torque selection and the distinct normal/UVRT torque slew limits.
    reset_torque: Expr = sym.hard_sat(
        reset_torque_voltage_scale * filtered_voltage,
        minimum_torque,
        maximum_torque,
    )
    torque_command: Expr = (
        (Const(1.0) - uvrt_active) * torque_limited
        + uvrt_active * reset_torque
    )
    torque_ramp: Var = vfactory.add_var(f'Type3TorquePu_{template_name}')
    model.block.event_dict[torque_ramp] = vfactory.add_const(value=initial_power)
    torque_rate_limit: Expr = (
        (Const(1.0) - uvrt_active) * torque_ramp_magnitude
        + uvrt_active * torque_uvrt_ramp_magnitude
    )
    model.block.procedural_logic.append(gradlim_const(
        torque_command,
        -torque_rate_limit,
        torque_rate_limit,
        torque_ramp,
        name=f'WindContPType3IEC.TorqueRamp_{template_name}',
    ))

    # Generator current command converts electrical torque by filtered voltage.
    current_command: Var = model.algebraic(
        'IpCmdPu',
        sym.hard_sat(
            sym.safe_divide(
                torque_ramp * filtered_speed,
                sym.max(filtered_voltage, Const(0.01)),
                Const(1.0),
            ),
            Const(0.0),
            active_current_limit,
        ),
        Const(initial_power),
    )
    # PwtRefPu and unavailable voltage/current-limit sources remain host inputs; Type 3 composition binds IpCmdPu when the current-source model is present.
    return model.finish(
        (current_command, speed_reference, power_order),
        'IEC 61400-27-1 Type 3 P control: filtered power/speed/voltage, omega(p) lookup, '
        'sampled reference/order/torque rate limits, torque PI with voltage-sag handling, '
        'and second-order active drivetrain damping.',
    )
