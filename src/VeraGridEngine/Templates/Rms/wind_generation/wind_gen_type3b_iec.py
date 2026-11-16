# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC 61400-27-1 Figure 23 type-3B crowbar and current-source equations."""

import math
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    _build_clipped_lookup_expression,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import reset
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def build_wind_gen_type3b_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dipmax: float = 1.0,
        diqmax: float = 1.0,
        xs: float = 0.1,
        tg: float = 0.02,
        two: float = 0.01,
        mwtcwp: bool = False,
        tcwdu_curve: Sequence[tuple[float, float]] = (),
        initial_active_current: float = 0.0,
        initial_reactive_current: float = 0.0,
        initial_voltage_magnitude: float = 1.0,
        initial_voltage_angle: float = 0.0,
        initial_active_maximum: float = 999.0,
        initial_reactive_maximum: float = 999.0,
        initial_reactive_minimum: float = -999.0,
        use_terminal_voltage_frame: bool = False,
) -> RmsModelTemplate:
    """Build the IEC Type 3B current source and crowbar duration logic.

    :param vfactory: Factory allocating equation-graph symbols.
    :param name: Optional unique runtime model name.
    :param dipmax: Active-current order slew limit in pu/s.
    :param diqmax: Reactive-current order slew limit in pu/s.
    :param xs: Transient reactance in pu.
    :param tg: Current-generation lag time in seconds.
    :param two: Voltage-change washout time in seconds.
    :param mwtcwp: Whether the crowbar is enabled by the use case.
    :param tcwdu_curve: Ordered voltage-change/crowbar-duration curve.
    :param initial_active_current: Solved active current in controls coordinates.
    :param initial_reactive_current: Solved reactive current in controls coordinates.
    :param initial_voltage_magnitude: Solved terminal-voltage magnitude in pu.
    :param initial_voltage_angle: Solved terminal-voltage angle in radians.
    :param initial_active_maximum: Initial active-current maximum in pu.
    :param initial_reactive_maximum: Initial reactive-current maximum in pu.
    :param initial_reactive_minimum: Initial reactive-current minimum in pu.
    :param use_terminal_voltage_frame: Rotate current commands with terminal Va when the schema
        edition has no separate WindRefFrameRotIEC association.
    :return: Type 3B model with current-command and grid-current ports.
    :raises ValueError: Invalid parameters or malformed crowbar curve.
    """
    values: tuple[float, ...] = (
        dipmax, diqmax, xs, tg, two, initial_active_current,
        initial_reactive_current, initial_voltage_magnitude,
        initial_voltage_angle, initial_active_maximum,
        initial_reactive_maximum, initial_reactive_minimum,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindGenType3bIEC values must be finite')
    elif min(dipmax, diqmax, tg, two) < 0.0 or xs <= 0.0:
        raise ValueError('CGMES WindGenType3bIEC requires positive xs and nonnegative rates/times')
    elif initial_voltage_magnitude <= 0.0:
        raise ValueError('CGMES WindGenType3bIEC voltage magnitude must be positive')
    elif initial_active_maximum < 0.0 or initial_reactive_minimum > initial_reactive_maximum:
        raise ValueError('CGMES WindGenType3bIEC current bounds are inconsistent')
    elif not isinstance(mwtcwp, bool):
        raise ValueError('CGMES WindGenType3bIEC mwtcwp must be the canonical boolean')
    elif mwtcwp and len(tcwdu_curve) < 2:
        raise ValueError('CGMES WindGenType3bIEC requires tcwdu points when its crowbar is enabled')
    else:
        pass

    curve_inputs: list[float] = list()
    curve_outputs: list[float] = list()
    for point_index in range(len(tcwdu_curve)):
        curve_input: float = float(tcwdu_curve[point_index][0])
        curve_output: float = float(tcwdu_curve[point_index][1])
        if not math.isfinite(curve_input) or not math.isfinite(curve_output):
            raise ValueError('CGMES WindGenType3bIEC tcwdu values must be finite')
        elif curve_input < 0.0 or curve_output < 0.0:
            raise ValueError('CGMES WindGenType3bIEC tcwdu inputs and durations must be nonnegative')
        elif point_index > 0 and curve_input <= curve_inputs[point_index - 1]:
            raise ValueError('CGMES WindGenType3bIEC tcwdu inputs must be strictly increasing')
        else:
            curve_inputs.append(curve_input)
            curve_outputs.append(curve_output)

    template_name: str = 'WindGenType3bIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    active_slew: Var = model.parameter('WindGenType3IEC.dipmax', dipmax)
    reactive_slew: Var = model.parameter('WindGenType3IEC.diqmax', diqmax)
    transient_reactance: Var = model.parameter('WindGenType3IEC.xs', xs)
    current_generation_time: Var = model.parameter('WindGenType3bIEC.tg', tg)
    washout_time: Var = model.parameter('WindGenType3bIEC.two', two)

    # Commands and limits are supplied by the turbine active/reactive controls.
    initial_network_real: float = (
        initial_active_current * math.cos(initial_voltage_angle)
        - initial_reactive_current * math.sin(initial_voltage_angle)
    )
    initial_network_imaginary: float = (
        initial_active_current * math.sin(initial_voltage_angle)
        + initial_reactive_current * math.cos(initial_voltage_angle)
    )
    initial_voltage_real: float = initial_voltage_magnitude * math.cos(initial_voltage_angle)
    initial_voltage_imaginary: float = initial_voltage_magnitude * math.sin(initial_voltage_angle)
    initial_frame_real: float = initial_network_real + initial_voltage_imaginary / xs
    initial_frame_imaginary: float = initial_network_imaginary - initial_voltage_real / xs
    initial_active_order: float = (
        initial_frame_real * math.cos(initial_voltage_angle)
        + initial_frame_imaginary * math.sin(initial_voltage_angle)
    )
    initial_reactive_order: float = (
        -initial_frame_real * math.sin(initial_voltage_angle)
        + initial_frame_imaginary * math.cos(initial_voltage_angle)
    )
    initial_active: float = min(max(initial_active_order, 0.0), initial_active_maximum)
    initial_reactive: float = min(
        max(initial_reactive_order, initial_reactive_minimum),
        initial_reactive_maximum,
    )
    active_command: Var = model.input('IpCmdPu', Const(initial_active))
    reactive_command: Var = model.input('IqCmdPu', Const(initial_reactive))
    active_maximum: Var = model.input('IpMaxPu', Const(initial_active_maximum))
    reactive_maximum: Var = model.input('IqMaxPu', Const(initial_reactive_maximum))
    reactive_minimum: Var = model.input('IqMinPu', Const(initial_reactive_minimum))

    # A high-pass voltage-change signal starts the IEC crowbar hold timer.
    voltage_magnitude: Var = vfactory.add_var(
        name=f'Vm_{template_name}', reference=VarPowerFlowReferenceType.Vm,
    )
    voltage_angle: Var = vfactory.add_var(
        name=f'Va_{template_name}', reference=VarPowerFlowReferenceType.Va,
    )
    model.block.external_mapping[VarPowerFlowReferenceType.Vm] = voltage_magnitude
    model.block.external_mapping[VarPowerFlowReferenceType.Va] = voltage_angle
    voltage_deviation: Expr = sym.abs(voltage_magnitude - Const(initial_voltage_magnitude))
    filtered_deviation: Var = model.lag(
        'FilteredVoltageDeviationPu', voltage_deviation, washout_time, two,
        Const(0.0),
    )
    voltage_change: Expr = sym.abs(voltage_deviation - filtered_deviation)
    crowbar_duration: Expr
    crowbar_mode: float = 1.0 if mwtcwp else 0.0
    if mwtcwp:
        lookup_inputs: list[Var] = list()
        lookup_outputs: list[Var] = list()
        for point_index in range(len(curve_inputs)):
            lookup_inputs.append(model.parameter(
                f'WindGenType3bIEC.tcwdu_input_{point_index}', curve_inputs[point_index],
            ))
            lookup_outputs.append(model.parameter(
                f'WindGenType3bIEC.tcwdu_output_{point_index}', curve_outputs[point_index],
            ))
        crowbar_duration = _build_clipped_lookup_expression(
            voltage_change, lookup_inputs, lookup_outputs,
        )
        crowbar_expiry: Var = vfactory.add_var(name=f'CrowbarExpiryTime_{template_name}')
        model.differential(crowbar_expiry, Const(0.0), Const(0.0))
        simulation_time: Var = vfactory.add_var(name='glob_time')
        model.block.procedural_logic.append(reset(
            var=crowbar_expiry,
            rst=voltage_change > Const(1e-6),
            val=simulation_time + crowbar_duration,
            name=f'WindGenType3bIEC.CrowbarTimer_{template_name}',
        ))
        crowbar_active: Var = model.algebraic(
            'CrowbarActive',
            sym.heaviside(crowbar_expiry - simulation_time - Const(1e-9)),
            Const(0.0),
        )
    else:
        crowbar_duration = Const(0.0)
        crowbar_active = model.algebraic('CrowbarActive', Const(0.0), Const(0.0))
    crowbar_gate: Expr = Const(1.0) - Const(crowbar_mode) * crowbar_active

    # Slew-limited current orders are suppressed while the crowbar is active.
    limited_active_order: Expr = sym.hard_sat(
        crowbar_gate * active_command, Const(0.0), active_maximum,
    )
    active_ramp_state: Var = vfactory.add_var(name=f'IpRampStatePu_{template_name}')
    active_ramp_derivative: Expr = sym.hard_sat(
        limited_active_order - active_ramp_state, -active_slew, active_slew,
    )
    active_ramp: Var = model.differential(
        active_ramp_state, active_ramp_derivative, Const(initial_active),
        Const(0.0), active_maximum,
    )
    limited_reactive_order: Expr = sym.hard_sat(
        crowbar_gate * reactive_command, reactive_minimum, reactive_maximum,
    )
    reactive_ramp_state: Var = vfactory.add_var(name=f'IqRampStatePu_{template_name}')
    reactive_ramp_derivative: Expr = sym.hard_sat(
        limited_reactive_order - reactive_ramp_state, -reactive_slew, reactive_slew,
    )
    reactive_ramp: Var = model.differential(
        reactive_ramp_state, reactive_ramp_derivative, Const(initial_reactive),
        reactive_minimum, reactive_maximum,
    )
    active_control_current: Var = model.algebraic(
        'IpCtrlPu', active_ramp, Const(initial_active),
    )
    reactive_control_current: Var = model.algebraic(
        'IqCtrlPu', reactive_ramp, Const(initial_reactive),
    )

    # 2.4.15 has no rotation association, so its current orders use terminal Va directly.
    if use_terminal_voltage_frame:
        frame_current_real: Var = model.algebraic(
            'IreFramePu',
            active_control_current * sym.cos(voltage_angle)
            - reactive_control_current * sym.sin(voltage_angle),
            Const(initial_frame_real),
        )
        frame_current_imaginary: Var = model.algebraic(
            'IimFramePu',
            active_control_current * sym.sin(voltage_angle)
            + reactive_control_current * sym.cos(voltage_angle),
            Const(initial_frame_imaginary),
        )
    else:
        frame_current_real = model.input('IreFramePu', Const(initial_frame_real))
        frame_current_imaginary = model.input('IimFramePu', Const(initial_frame_imaginary))
    grid_current_real_lag: Var = model.lag(
        'IreGenerationLagPu', frame_current_real, current_generation_time, tg,
        Const(initial_frame_real),
    )
    grid_current_imaginary_lag: Var = model.lag(
        'IimGenerationLagPu', frame_current_imaginary, current_generation_time, tg,
        Const(initial_frame_imaginary),
    )
    voltage_real: Expr = voltage_magnitude * sym.cos(voltage_angle)
    voltage_imaginary: Expr = voltage_magnitude * sym.sin(voltage_angle)
    current_real: Var = model.algebraic(
        'IrePu', grid_current_real_lag - voltage_imaginary / transient_reactance,
        Const(initial_frame_real - initial_voltage_magnitude * math.sin(initial_voltage_angle) / xs),
    )
    current_imaginary: Var = model.algebraic(
        'IimPu', grid_current_imaginary_lag + voltage_real / transient_reactance,
        Const(initial_frame_imaginary + initial_voltage_magnitude * math.cos(initial_voltage_angle) / xs),
    )
    active_power: Var = model.algebraic(
        'PagPu', voltage_real * current_real + voltage_imaginary * current_imaginary,
        Const(initial_voltage_magnitude * initial_active_current),
    )
    reactive_power: Var = model.algebraic(
        'QagPu', voltage_imaginary * current_real - voltage_real * current_imaginary,
        Const(-initial_voltage_magnitude * initial_reactive_current),
    )
    return model.finish(
        (
            active_control_current, reactive_control_current, current_real,
            current_imaginary, active_power, reactive_power,
        ),
        'IEC 61400-27-1 Figure 23 crowbar timer, bounded current orders, Tg current generation, and transient-reactance source.',
    )
