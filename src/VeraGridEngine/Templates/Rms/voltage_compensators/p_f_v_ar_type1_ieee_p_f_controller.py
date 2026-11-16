# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed IEEE 421.5 Type I power-factor controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.procedural_logic import bool_and, pickup_dropoff


def build_p_f_v_ar_type1_i_e_e_e_p_f_controller_template(
        vfactory: VarFactory,
        name: str | None = None,
        ovex: bool = False,
        tpfc: float = 5.0,
        vitmin: float = 0.1,
        vpf: float = 1.0,
        vpfcbw: float = 0.02,
        vpfref: float = 0.95,
        vvtmax: float = 1.05,
        vvtmin: float = 0.95,
) -> RmsModelTemplate:
    """Build the IEEE 421.5-2005 §11.2 PF reference-adjuster controller.

    :param vfactory: Factory allocating equation and procedural output symbols.
    :param name: Optional runtime model name.
    :param ovex: Overexcitation selector used by PF normalization.
    :param tpfc: Delay before a raise/lower contact picks up, in seconds.
    :param vitmin: Minimum current magnitude enabling the controller.
    :param vpf: Initial measured power-factor estimate.
    :param vpfcbw: Power-factor error deadband half-width.
    :param vpfref: Normalized power-factor reference.
    :param vvtmax: Maximum terminal voltage enabling control.
    :param vvtmin: Minimum terminal voltage enabling control.
    :return: Controller with measured PF/current/voltage inputs and VCR/VCL outputs.
    :raises ValueError: Nonfinite values, invalid limits, or invalid timer/deadband.
    """
    values: tuple[float, ...] = (
        tpfc, vitmin, vpf, vpfcbw, vpfref, vvtmax, vvtmin,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('PFVArType1IEEEPFController parameters must be finite')
    elif tpfc < 0.0 or vitmin < 0.0 or vpfcbw < 0.0:
        raise ValueError('PF controller time, current threshold, and deadband must be nonnegative')
    elif vvtmin >= vvtmax:
        raise ValueError('PF controller VVTMIN must be below VVTMAX')
    else:
        pass

    template_name: str = 'PFVArType1IEEEPFController' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    overexcited: Var = model.parameter(
        'PFVArType1IEEEPFController.ovex', float(ovex),
    )
    measured_pf_initial: Var = model.parameter(
        'PFVArType1IEEEPFController.vpf', vpf,
    )
    reference: Var = model.parameter(
        'PFVArType1IEEEPFController.vpfref', vpfref,
    )
    measured_pf: Var = model.input('PFpu', measured_pf_initial)
    terminal_voltage: Var = model.input('VmPu', Const(1.0))
    terminal_current: Var = model.input('ItPu', Const(1.0))
    normalized_pf: Var = model.algebraic(
        'NormalizedPFpu',
        (Const(1.0) - overexcited) * measured_pf
        + overexcited * (Const(2.0) - measured_pf),
        Const(vpf if not ovex else 2.0 - vpf),
    )
    pf_error: Var = model.algebraic(
        'PFErrorPu', reference - normalized_pf, Const(0.0),
    )
    current_minimum: Var = model.parameter('PFVArType1IEEEPFController.vitmin', vitmin)
    voltage_maximum: Var = model.parameter('PFVArType1IEEEPFController.vvtmax', vvtmax)
    voltage_minimum: Var = model.parameter('PFVArType1IEEEPFController.vvtmin', vvtmin)
    deadband: Var = model.parameter('PFVArType1IEEEPFController.vpfcbw', vpfcbw)
    delay_time: Var = model.parameter('PFVArType1IEEEPFController.tpfc', tpfc)
    enable: Var = model.algebraic(
        'ControlEnabledPu',
        bool_and(
            terminal_current > current_minimum,
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
            boolexpr=bool_and(enable, pf_error > deadband),
            Tpick=delay_time,
            Tdrop=Const(0.0),
            name=f'PFVArType1.Raise_{template_name}',
        )
    )
    model.block.procedural_logic.append(
        pickup_dropoff(
            output=lower_contact,
            boolexpr=bool_and(enable, pf_error < -deadband),
            Tpick=delay_time,
            Tdrop=Const(0.0),
            name=f'PFVArType1.Lower_{template_name}',
        )
    )
    template: RmsModelTemplate = model.finish(
        (raise_contact, lower_contact),
        'CGMES PFVArType1IEEEPFController',
    )
    template.comment = (
        'IEEE 421.5-2005 §11.2: OVEX-normalized PF error, terminal current/voltage '
        'permissives, delayed deadband pickup, and retained VCR/VCL commands.'
    )
    return template
