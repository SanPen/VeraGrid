# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed IEEE 421.5 Type I reactive-power controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.procedural_logic import bool_and, pickup_dropoff


def build_p_f_v_ar_type1_i_e_e_e_v_ar_controller_template(
        vfactory: VarFactory,
        name: str | None = None,
        tvarc: float = 5.0,
        vvar: float = 0.0,
        vvarcbw: float = 0.02,
        vvarref: float = 0.0,
        vvtmax: float = 1.05,
        vvtmin: float = 0.95,
) -> RmsModelTemplate:
    """Build the IEEE 421.5-2005 §11.3 VAr reference-adjuster controller.

    :param vfactory: Factory allocating equation and procedural output symbols.
    :param name: Optional runtime model name.
    :param tvarc: Delay before a raise/lower contact picks up, in seconds.
    :param vvar: Initial measured reactive-power value.
    :param vvarcbw: Reactive-power error deadband half-width.
    :param vvarref: Reactive-power reference.
    :param vvtmax: Maximum terminal voltage enabling control.
    :param vvtmin: Minimum terminal voltage enabling control.
    :return: Controller with measured Q/voltage inputs and VCR/VCL outputs.
    :raises ValueError: Nonfinite values, invalid limits, or invalid timer/deadband.
    """
    values: tuple[float, ...] = (
        tvarc, vvar, vvarcbw, vvarref, vvtmax, vvtmin,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('PFVArType1IEEEVArController parameters must be finite')
    elif tvarc < 0.0 or vvarcbw < 0.0:
        raise ValueError('VAr controller delay and deadband must be nonnegative')
    elif vvtmin >= vvtmax:
        raise ValueError('VAr controller VVTMIN must be below VVTMAX')
    else:
        pass

    template_name: str = 'PFVArType1IEEEVArController' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    measured_var_initial: Var = model.parameter(
        'PFVArType1IEEEVArController.vvar', vvar,
    )
    reference: Var = model.parameter(
        'PFVArType1IEEEVArController.vvarref', vvarref,
    )
    measured_var: Var = model.input('QPu', measured_var_initial)
    terminal_voltage: Var = model.input('VmPu', Const(1.0))
    delay_time: Var = model.parameter('PFVArType1IEEEVArController.tvarc', tvarc)
    deadband: Var = model.parameter(
        'PFVArType1IEEEVArController.vvarcbw', vvarcbw,
    )
    voltage_maximum: Var = model.parameter(
        'PFVArType1IEEEVArController.vvtmax', vvtmax,
    )
    voltage_minimum: Var = model.parameter(
        'PFVArType1IEEEVArController.vvtmin', vvtmin,
    )
    var_error: Var = model.algebraic(
        'VArErrorPu', reference - measured_var, Const(0.0),
    )
    enable: Var = model.algebraic(
        'ControlEnabledPu',
        bool_and(
            terminal_voltage > voltage_minimum,
            terminal_voltage < voltage_maximum,
        ),
        Const(1.0),
    )
    raise_contact: Var = vfactory.add_var(f'VcrPu_{template_name}')
    lower_contact: Var = vfactory.add_var(f'VclPu_{template_name}')
    model.block.event_dict[raise_contact] = vfactory.add_const(value=0.0)
    model.block.event_dict[lower_contact] = vfactory.add_const(value=0.0)
    model.block.procedural_logic.append(
        pickup_dropoff(
            output=raise_contact,
            boolexpr=bool_and(enable, var_error > deadband),
            Tpick=delay_time,
            Tdrop=Const(0.0),
            name=f'PFVArType1.VArRaise_{template_name}',
        )
    )
    model.block.procedural_logic.append(
        pickup_dropoff(
            output=lower_contact,
            boolexpr=bool_and(enable, var_error < -deadband),
            Tpick=delay_time,
            Tdrop=Const(0.0),
            name=f'PFVArType1.VArLower_{template_name}',
        )
    )
    template: RmsModelTemplate = model.finish(
        (raise_contact, lower_contact),
        'CGMES PFVArType1IEEEVArController',
    )
    template.comment = (
        'IEEE 421.5-2005 §11.3: reactive-power error, terminal-voltage permissives, '
        'delayed deadband pickup, and retained VCR/VCL commands.'
    )
    return template
