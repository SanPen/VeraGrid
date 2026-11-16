# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEC type-4B active-power controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.procedural_logic import gradlim_const
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_wind_cont_p_type4b_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dpmaxp4b: float = 999.0,
        tpaero: float = 0.0,
        tpordp4b: float = 0.0,
        tufiltp4b: float = 0.0,
        initial_power: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC 61400-27-1:2015 Figure 34 Type 4B P controller.

    :param vfactory: Factory allocating this controller's symbols.
    :param name: Optional unique runtime model name.
    :param dpmaxp4b: Symmetric active-power ramp limit in pu per second.
    :param tpaero: Aerodynamic-power response time in seconds.
    :param tpordp4b: Active-power order lag time in seconds.
    :param tufiltp4b: Terminal-voltage filter time in seconds.
    :param initial_power: Solved active power used to seed controller memories.
    :return: Controller with `IpCmdPu` and filtered aerodynamic-power outputs.
    :raises ValueError: Nonfinite, negative or infeasible parameter values.
    """
    values: tuple[float, ...] = (dpmaxp4b, tpaero, tpordp4b, tufiltp4b, initial_power)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindContPType4bIEC values must be finite')
    elif min(dpmaxp4b, tpaero, tpordp4b, tufiltp4b, initial_power) < 0.0:
        raise ValueError('CGMES WindContPType4bIEC rates, times and power must be nonnegative')
    else:
        pass

    template_name: str = 'WindContPType4bIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    ramp_limit: Var = model.parameter('WindContPType4bIEC.dpmaxp4b', dpmaxp4b)
    aerodynamic_time: Var = model.parameter('WindContPType4bIEC.tpaero', tpaero)
    power_order_time: Var = model.parameter('WindContPType4bIEC.tpordp4b', tpordp4b)
    voltage_filter_time: Var = model.parameter('WindContPType4bIEC.tufiltp4b', tufiltp4b)
    power_reference: Var = model.input('PwtRefPu', Const(initial_power))
    generator_speed: Var = model.input('OmegaGenPu', Const(1.0))
    aerodynamic_power: Var = model.input('PaeroPu', Const(initial_power))
    terminal_voltage: Var = model.input('UwtPu', Const(1.0))

    # The IEC ramp stage holds its previous output and limits both power directions.
    limited_power_reference: Var = vfactory.add_var(f'PType4bRampPu_{template_name}')
    model.block.event_dict[limited_power_reference] = vfactory.add_const(value=initial_power)
    model.block.procedural_logic.append(gradlim_const(
        power_reference,
        -ramp_limit,
        ramp_limit,
        limited_power_reference,
        name=f'WindContPType4bIEC.PowerRamp_{template_name}',
    ))

    # Voltage filtering and the standard floor prevent current-command blow-up at low voltage.
    filtered_voltage: Var = model.lag(
        'FilteredUwtPu', terminal_voltage, voltage_filter_time, tufiltp4b, Const(1.0),
    )
    filtered_power_order: Var = model.lag(
        'PordPu', limited_power_reference, power_order_time, tpordp4b,
        Const(initial_power),
    )
    filtered_aerodynamic_power: Var = model.lag(
        'PaeroFilteredPu', aerodynamic_power, aerodynamic_time, tpaero,
        Const(initial_power),
    )
    current_command: Var = model.algebraic(
        'IpCmdPu',
        filtered_power_order
        / (generator_speed * sym.max(filtered_voltage, Const(0.01))),
        Const(initial_power),
    )
    return model.finish(
        (current_command, filtered_aerodynamic_power),
        'IEC 61400-27-1:2015 Figure 34 type-4B active-power controller.',
    )
