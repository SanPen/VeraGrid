# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEC type-4A active-power controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.procedural_logic import gradlim_const
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_wind_cont_p_type4a_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dpmaxp4a: float = 999.0,
        tpordp4a: float = 0.0,
        tufiltp4a: float = 0.0,
        initial_power: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC 61400-27-1:2015 Figure 33 Type 4A P controller.

    :param vfactory: Factory allocating this controller's symbols.
    :param name: Optional unique runtime model name.
    :param dpmaxp4a: Symmetric active-power ramp limit in pu per second.
    :param tpordp4a: Active-power order lag time in seconds.
    :param tufiltp4a: Terminal-voltage filter time in seconds.
    :param initial_power: Solved active power used to seed controller memories.
    :return: Controller with an `IpCmdPu` output and two open signal inputs.
    :raises ValueError: Nonfinite, negative or infeasible parameter values.
    """
    values: tuple[float, ...] = (dpmaxp4a, tpordp4a, tufiltp4a, initial_power)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindContPType4aIEC values must be finite')
    elif min(dpmaxp4a, tpordp4a, tufiltp4a, initial_power) < 0.0:
        raise ValueError('CGMES WindContPType4aIEC rates, times and power must be nonnegative')
    else:
        pass

    template_name: str = 'WindContPType4aIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    ramp_limit: Var = model.parameter('WindContPType4aIEC.dpmaxp4a', dpmaxp4a)
    power_order_time: Var = model.parameter('WindContPType4aIEC.tpordp4a', tpordp4a)
    voltage_filter_time: Var = model.parameter('WindContPType4aIEC.tufiltp4a', tufiltp4a)
    power_reference: Var = model.input('PwtRefPu', Const(initial_power))
    terminal_voltage: Var = model.input('UwtPu', Const(1.0))

    # The IEC ramp stage holds its previous output and limits both power directions.
    limited_power_reference: Var = vfactory.add_var(f'PType4aRampPu_{template_name}')
    model.block.event_dict[limited_power_reference] = vfactory.add_const(value=initial_power)
    model.block.procedural_logic.append(gradlim_const(
        power_reference,
        -ramp_limit,
        ramp_limit,
        limited_power_reference,
        name=f'WindContPType4aIEC.PowerRamp_{template_name}',
    ))

    # Filter voltage before division and keep the IEC 0.01 pu denominator floor.
    filtered_voltage: Var = model.lag(
        'FilteredUwtPu', terminal_voltage, voltage_filter_time, tufiltp4a, Const(1.0),
    )
    power_order: Var = model.lag(
        'PordPu', limited_power_reference, power_order_time, tpordp4a,
        Const(initial_power),
    )
    current_command: Var = model.algebraic(
        'IpCmdPu',
        power_order / sym.max(filtered_voltage, Const(0.01)),
        Const(initial_power),
    )
    return model.finish(
        (current_command,),
        'IEC 61400-27-1:2015 Figure 33 type-4A active-power controller.',
    )
