# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC 61400-27-1 type-3A current-source generator realization."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def build_wind_gen_type3a_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dipmax: float = 1.0,
        diqmax: float = 1.0,
        xs: float = 0.1,
        kpc: float = 1.0,
        tic: float = 0.1,
        initial_active_current: float = 0.0,
        initial_reactive_current: float = 0.0,
        initial_voltage_magnitude: float = 1.0,
        initial_voltage_angle: float = 0.0,
        initial_active_maximum: float = 1.0,
        initial_reactive_maximum: float = 1.0,
        initial_reactive_minimum: float = -1.0,
        parent_parameter_class_name: str = 'WindGenType3IEC',
        local_parameter_class_name: str = 'WindGenType3aIEC',
        reactance_parameter_class_name: str | None = None,
) -> RmsModelTemplate:
    """Build the type-3A PI-controlled transient-reactance current source.

    :param vfactory: Factory allocating model symbols.
    :param name: Optional unique runtime model name.
    :param dipmax: Active-current reference slew limit in pu/s.
    :param diqmax: Symmetric reactive-current reference slew limit in pu/s.
    :param xs: Transient reactance in pu.
    :param kpc: Current-controller proportional gain.
    :param tic: Current-controller integral time in seconds.
    :param initial_active_current: Solved active current in the controls frame.
    :param initial_reactive_current: Solved reactive current in the controls frame.
    :param initial_voltage_magnitude: Solved terminal-voltage magnitude in pu.
    :param initial_voltage_angle: Solved terminal-voltage angle in radians.
    :param initial_active_maximum: Initial active-current upper bound in pu.
    :param initial_reactive_maximum: Initial reactive-current upper bound in pu.
    :param initial_reactive_minimum: Initial reactive-current lower bound in pu.
    :param parent_parameter_class_name: RDF class declaring ``dipmax`` and ``diqmax``.
    :param local_parameter_class_name: RDF class declaring ``kpc`` and ``tic``.
    :param reactance_parameter_class_name: RDF class declaring ``xs``; defaults to the parent.
    :return: Equation-backed generator model with network-frame current injection.
    :raises ValueError: Nonfinite values or physically invalid current/reactance data.
    """
    values: tuple[float, ...] = (
        dipmax, diqmax, xs, kpc, tic, initial_active_current,
        initial_reactive_current, initial_voltage_magnitude,
        initial_voltage_angle, initial_active_maximum,
        initial_reactive_maximum, initial_reactive_minimum,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindGenType3aIEC values must be finite')
    elif min(dipmax, diqmax, kpc) < 0.0 or xs <= 0.0 or tic <= 0.0:
        raise ValueError('CGMES WindGenType3aIEC requires positive xs/tic and nonnegative gains/rates')
    elif initial_voltage_magnitude <= 0.0:
        raise ValueError('CGMES WindGenType3aIEC terminal voltage must be positive')
    elif initial_active_maximum < 0.0 or initial_reactive_minimum > initial_reactive_maximum:
        raise ValueError('CGMES WindGenType3aIEC current bounds are inconsistent')
    else:
        pass

    template_name: str = 'WindGenType3aIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    reactance_class_name: str = (
        parent_parameter_class_name
        if reactance_parameter_class_name is None
        else reactance_parameter_class_name
    )
    active_slew: Var = model.parameter(f'{parent_parameter_class_name}.dipmax', dipmax)
    reactive_slew: Var = model.parameter(f'{parent_parameter_class_name}.diqmax', diqmax)
    transient_reactance: Var = model.parameter(f'{reactance_class_name}.xs', xs)
    current_gain: Var = model.parameter(f'{local_parameter_class_name}.kpc', kpc)
    current_integral_time: Var = model.parameter(f'{local_parameter_class_name}.tic', tic)

    # Seed the current-order states directly at the imported power-flow point.
    initial_active: float = min(max(initial_active_current, 0.0), initial_active_maximum)
    initial_reactive: float = min(
        max(initial_reactive_current, initial_reactive_minimum),
        initial_reactive_maximum,
    )
    active_command: Var = model.input('IpCmdPu', Const(initial_active))
    reactive_command: Var = model.input('IqCmdPu', Const(initial_reactive))
    active_maximum: Var = model.input('IpMaxPu', Const(initial_active_maximum))
    reactive_maximum: Var = model.input('IqMaxPu', Const(initial_reactive_maximum))
    reactive_minimum: Var = model.input('IqMinPu', Const(initial_reactive_minimum))
    active_reference_state: Var = vfactory.add_var(name=f'IpGenStatePu_{template_name}')
    reactive_reference_state: Var = vfactory.add_var(name=f'IqGenStatePu_{template_name}')
    active_reference_derivative: Expr = sym.hard_sat(
        sym.heaviside(active_command - active_reference_state)
        - sym.heaviside(active_reference_state - active_command),
        Const(-1.0), Const(1.0),
    ) * active_slew
    reactive_reference_derivative: Expr = sym.hard_sat(
        sym.heaviside(reactive_command - reactive_reference_state)
        - sym.heaviside(reactive_reference_state - reactive_command),
        Const(-1.0), Const(1.0),
    ) * reactive_slew
    active_reference: Var = model.differential(
        active_reference_state,
        active_reference_derivative,
        Const(initial_active),
        Const(0.0),
        active_maximum,
    )
    reactive_reference: Var = model.differential(
        reactive_reference_state,
        reactive_reference_derivative,
        Const(initial_reactive),
        reactive_minimum,
        reactive_maximum,
    )

    # Terminal voltage is the network-frame phasor used by both current feedback
    # rotation and the transient-reactance source equation.
    voltage_magnitude: Var = vfactory.add_var(
        name=f'Vm_{template_name}', reference=VarPowerFlowReferenceType.Vm,
    )
    voltage_angle: Var = vfactory.add_var(
        name=f'Va_{template_name}', reference=VarPowerFlowReferenceType.Va,
    )
    model.block.external_mapping[VarPowerFlowReferenceType.Vm] = voltage_magnitude
    model.block.external_mapping[VarPowerFlowReferenceType.Va] = voltage_angle
    controller_angle: Var = model.input('VoltageAngleRad', Const(initial_voltage_angle))
    voltage_real: Expr = voltage_magnitude * sym.cos(voltage_angle)
    voltage_imaginary: Expr = voltage_magnitude * sym.sin(voltage_angle)
    initial_current_real: float = (
        initial_active * math.cos(initial_voltage_angle)
        - initial_reactive * math.sin(initial_voltage_angle)
    )
    initial_current_imaginary: float = (
        initial_active * math.sin(initial_voltage_angle)
        + initial_reactive * math.cos(initial_voltage_angle)
    )
    internal_voltage_real_initial: float = (
        initial_voltage_magnitude * math.cos(initial_voltage_angle)
        - xs * initial_current_imaginary
    )
    internal_voltage_imaginary_initial: float = (
        initial_voltage_magnitude * math.sin(initial_voltage_angle)
        + xs * initial_current_real
    )
    internal_voltage_real: Var = vfactory.add_var(name=f'EreStatePu_{template_name}')
    internal_voltage_imaginary: Var = vfactory.add_var(name=f'EimStatePu_{template_name}')
    current_real: Var = model.algebraic(
        'IrePu',
        (internal_voltage_imaginary - voltage_imaginary) / transient_reactance,
        Const(initial_current_real),
    )
    current_imaginary: Var = model.algebraic(
        'IimPu',
        (voltage_real - internal_voltage_real) / transient_reactance,
        Const(initial_current_imaginary),
    )
    current_control_active_expression: Expr = (
        current_real * sym.cos(controller_angle)
        + current_imaginary * sym.sin(controller_angle)
    )
    current_control_reactive_expression: Expr = (
        current_imaginary * sym.cos(controller_angle)
        - current_real * sym.sin(controller_angle)
    )
    current_control_active: Var = model.algebraic(
        'IpCtrlPu', current_control_active_expression, Const(initial_active),
    )
    current_control_reactive: Var = model.algebraic(
        'IqCtrlPu', current_control_reactive_expression, Const(initial_reactive),
    )
    active_error: Expr = active_reference - current_control_active
    reactive_error: Expr = reactive_reference - current_control_reactive
    active_integral: Var = vfactory.add_var(name=f'IpErrorIntegral_{template_name}')
    reactive_integral: Var = vfactory.add_var(name=f'IqErrorIntegral_{template_name}')
    active_integral_state: Var = model.differential(
        active_integral, active_error, Const(0.0),
    )
    reactive_integral_state: Var = model.differential(
        reactive_integral, reactive_error, Const(0.0),
    )
    active_voltage_control: Expr = current_gain * (
        active_error + active_integral_state / current_integral_time
    )
    reactive_voltage_control: Expr = current_gain * (
        reactive_error + reactive_integral_state / current_integral_time
    )
    active_voltage_grid: Expr = (
        active_voltage_control * sym.cos(controller_angle)
        - reactive_voltage_control * sym.sin(controller_angle)
    )
    reactive_voltage_grid: Expr = (
        active_voltage_control * sym.sin(controller_angle)
        + reactive_voltage_control * sym.cos(controller_angle)
    )
    model.differential(
        internal_voltage_real,
        active_voltage_grid,
        Const(internal_voltage_real_initial),
    )
    model.differential(
        internal_voltage_imaginary,
        reactive_voltage_grid,
        Const(internal_voltage_imaginary_initial),
    )
    active_power: Var = model.algebraic(
        'PagPu', voltage_real * current_real + voltage_imaginary * current_imaginary,
        Const(initial_voltage_magnitude * initial_active),
    )
    reactive_power: Var = model.algebraic(
        'QagPu', voltage_imaginary * current_real - voltage_real * current_imaginary,
        Const(-initial_voltage_magnitude * initial_reactive),
    )
    return model.finish(
        (
            active_reference, reactive_reference, current_real, current_imaginary,
            current_control_active, current_control_reactive, active_power, reactive_power,
        ),
        'IEC 61400-27-1:2020 Figure 22 PI current control, slew limits, transient-reactance source, and air-gap power.',
    )
