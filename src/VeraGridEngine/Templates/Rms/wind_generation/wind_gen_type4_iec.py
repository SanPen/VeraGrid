# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC type-4 wind generator current-order and air-gap power equations."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def build_wind_gen_type4_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dipmax: float = 1.0,
        diqmax: float = 1.0,
        diqmin: float = -1.0,
        tg: float = 0.02,
        initial_active_current: float = 0.0,
        initial_reactive_current: float = 0.0,
        initial_voltage_magnitude: float = 1.0,
        initial_voltage_angle: float = 0.0,
        initial_active_maximum: float = 1.0,
        initial_reactive_maximum: float = 1.0,
        initial_reactive_minimum: float = -1.0,
) -> RmsModelTemplate:
    """Build IEC 61400-27-1:2020 Figure 24 type-4 generator equations.

    :param vfactory: Factory allocating model symbols.
    :param name: Optional unique runtime model name.
    :param dipmax: Symmetric active-current order slew limit in pu/s.
    :param diqmax: Positive reactive-current order slew limit in pu/s.
    :param diqmin: Negative reactive-current order slew limit in pu/s.
    :param tg: Current-order first-order time constant in seconds.
    :param initial_active_current: Load-flow active current in controls frame.
    :param initial_reactive_current: Load-flow reactive current in controls frame.
    :param initial_voltage_magnitude: Load-flow terminal voltage magnitude in pu.
    :param initial_voltage_angle: Load-flow terminal voltage angle in radians.
    :param initial_active_maximum: Seed for the active current maximum input.
    :param initial_reactive_maximum: Seed for the reactive current maximum input.
    :param initial_reactive_minimum: Seed for the reactive current minimum input.
    :return: Current-order lags with current outputs and air-gap power output.
    :raises ValueError: Nonfinite values or invalid time/rate settings.
    """
    values: tuple[float, ...] = (
        dipmax, diqmax, diqmin, tg, initial_active_current,
        initial_reactive_current, initial_voltage_magnitude,
        initial_voltage_angle,
        initial_active_maximum, initial_reactive_maximum, initial_reactive_minimum,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindGenType4IEC values must be finite')
    elif min(
            dipmax, diqmax, tg, initial_voltage_magnitude,
            initial_active_maximum, initial_reactive_maximum,
    ) < 0.0:
        raise ValueError('CGMES WindGenType4IEC rates, time, and voltage must be nonnegative')
    elif diqmin > 0.0 or diqmin > diqmax or initial_reactive_minimum > initial_reactive_maximum:
        raise ValueError('CGMES WindGenType4IEC reactive minima must not exceed maxima')
    else:
        pass

    template_name: str = 'WindGenType4IEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    active_rate: Var = model.parameter('WindGenType4IEC.dipmax', dipmax)
    reactive_rise_rate: Var = model.parameter('WindGenType4IEC.diqmax', diqmax)
    reactive_fall_rate: Var = model.parameter('WindGenType4IEC.diqmin', diqmin)
    current_time: Var = model.parameter('WindGenType4IEC.tg', tg)

    initial_active: float = min(max(initial_active_current, 0.0), initial_active_maximum)
    initial_reactive: float = min(
        max(initial_reactive_current, initial_reactive_minimum), initial_reactive_maximum,
    )
    active_command: Var = model.input('IpCmdPu', Const(initial_active))
    reactive_command: Var = model.input('IqCmdPu', Const(initial_reactive))
    active_maximum: Var = model.input('IpMaxPu', Const(initial_active_maximum))
    reactive_maximum: Var = model.input('IqMaxPu', Const(initial_reactive_maximum))
    reactive_minimum: Var = model.input('IqMinPu', Const(initial_reactive_minimum))
    voltage_magnitude: Var = vfactory.add_var(
        name=f'Vm_{template_name}', reference=VarPowerFlowReferenceType.Vm,
    )
    voltage_angle: Var = vfactory.add_var(
        name=f'Va_{template_name}', reference=VarPowerFlowReferenceType.Va,
    )
    model.block.external_mapping[VarPowerFlowReferenceType.Vm] = voltage_magnitude
    model.block.external_mapping[VarPowerFlowReferenceType.Va] = voltage_angle
    initial_current_angle: float = initial_voltage_angle
    initial_current_real: float = (
        initial_active * math.cos(initial_current_angle)
        - initial_reactive * math.sin(initial_current_angle)
    )
    initial_current_imaginary: float = (
        initial_active * math.sin(initial_current_angle)
        + initial_reactive * math.cos(initial_current_angle)
    )
    current_real: Var = model.input('IrePu', Const(initial_current_real))
    current_imaginary: Var = model.input('IimPu', Const(initial_current_imaginary))

    limited_active_command: Expr = sym.hard_sat(
        active_command, Const(0.0), active_maximum,
    )
    limited_reactive_command: Expr = sym.hard_sat(
        reactive_command, reactive_minimum, reactive_maximum,
    )
    active_state: Var = vfactory.add_var(name=f'IpGenStatePu_{template_name}')
    reactive_state: Var = vfactory.add_var(name=f'IqGenStatePu_{template_name}')

    if tg > 0.0:
        active_demand_rate: Expr = (
            limited_active_command - active_state
        ) / current_time
        reactive_demand_rate: Expr = (
            limited_reactive_command - reactive_state
        ) / current_time
    else:
        active_demand_rate = (
            sym.heaviside(limited_active_command - active_state)
            - sym.heaviside(active_state - limited_active_command)
        ) * active_rate
        reactive_error: Expr = limited_reactive_command - reactive_state
        reactive_demand_rate = (
            sym.heaviside(reactive_error) * reactive_rise_rate
            + sym.heaviside(-reactive_error) * reactive_fall_rate
        )
    active_rate_limited: Expr = sym.hard_sat(
        active_demand_rate, -active_rate, active_rate,
    )
    reactive_rate_limited: Expr = sym.hard_sat(
        reactive_demand_rate, reactive_fall_rate, reactive_rise_rate,
    )
    active_current: Var = model.differential(
        active_state,
        active_rate_limited,
        Const(initial_active),
        Const(0.0),
        active_maximum,
    )
    reactive_current: Var = model.differential(
        reactive_state,
        reactive_rate_limited,
        Const(initial_reactive),
        reactive_minimum,
        reactive_maximum,
    )
    active_power: Var = model.algebraic(
        'PagPu',
        voltage_magnitude * (
            current_real * sym.cos(voltage_angle)
            + current_imaginary * sym.sin(voltage_angle)
        ),
        Const(initial_voltage_magnitude * initial_active),
    )
    reactive_power: Var = model.algebraic(
        'QagPu',
        voltage_magnitude * (
            current_real * sym.sin(voltage_angle)
            - current_imaginary * sym.cos(voltage_angle)
        ),
        Const(-initial_voltage_magnitude * initial_reactive),
    )
    return model.finish(
        (active_current, reactive_current, active_power, reactive_power),
        'IEC 61400-27-1 Figure 24 type-4 generator current dynamics and air-gap power.',
    )
