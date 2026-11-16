# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed IEEE 421.5 Type I voltage-reference adjuster."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.procedural_logic import bool_and, bool_not, pickup_dropoff


def build_v_adj_i_e_e_e_template(
        vfactory: VarFactory,
        name: str | None = None,
        vadjf: float = 0.0,
        adjslew: float = 300.0,
        vadjmax: float = 1.1,
        vadjmin: float = 0.9,
        taon: float = 0.1,
        taoff: float = 0.5,
) -> RmsModelTemplate:
    """Build the IEEE 421.5-2005 Figure 11-1 reference adjuster.

    :param vfactory: Factory allocating equation and event variables.
    :param name: Optional runtime model name.
    :param vadjf: Bypass flag for the contact pulse generator.
    :param adjslew: Time to move across the full reference range in seconds.
    :param vadjmax: Maximum voltage reference.
    :param vadjmin: Minimum voltage reference.
    :param taon: Contact closed time in seconds.
    :param taoff: Contact open time in seconds.
    :return: Bounded voltage-reference state driven by VCR and VCL.
    :raises ValueError: Invalid limits or non-realizable pulse/slew times.
    """
    values: tuple[float, ...] = (vadjf, adjslew, vadjmax, vadjmin, taon, taoff)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('VAdjIEEE parameters must be finite')
    elif adjslew <= 0.0 or taon <= 0.0 or taoff <= 0.0:
        raise ValueError('VAdjIEEE slew and pulse times must be positive')
    elif vadjmin >= vadjmax or vadjf not in (0.0, 1.0):
        raise ValueError('VAdjIEEE requires ordered limits and a binary VADJF')
    else:
        pass

    template_name: str = 'VAdjIEEE' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    raise_command: Var = model.input('VcrPu', Const(0.0))
    lower_command: Var = model.input('VclPu', Const(0.0))
    bypass: Var = model.parameter('VAdjIEEE.vadjf', vadjf)
    travel_time: Var = model.parameter('VAdjIEEE.adjslew', adjslew)
    maximum: Var = model.parameter('VAdjIEEE.vadjmax', vadjmax)
    minimum: Var = model.parameter('VAdjIEEE.vadjmin', vadjmin)
    on_time: Var = model.parameter('VAdjIEEE.taon', taon)
    off_time: Var = model.parameter('VAdjIEEE.taoff', taoff)

    # Each contact repeats its ON/OFF cycle while its command remains asserted.
    raise_pulse: Var = vfactory.add_var(f'RaisePulse_{template_name}')
    lower_pulse: Var = vfactory.add_var(f'LowerPulse_{template_name}')
    model.block.event_dict[raise_pulse] = vfactory.add_const(value=0.0)
    model.block.event_dict[lower_pulse] = vfactory.add_const(value=0.0)
    model.block.procedural_logic.append(
        pickup_dropoff(
            output=raise_pulse,
            boolexpr=bool_and(raise_command, bool_not(raise_pulse)),
            Tpick=off_time,
            Tdrop=on_time,
            name=f'VAdjIEEE.RaisePulse_{template_name}',
        )
    )
    model.block.procedural_logic.append(
        pickup_dropoff(
            output=lower_pulse,
            boolexpr=bool_and(lower_command, bool_not(lower_pulse)),
            Tpick=off_time,
            Tdrop=on_time,
            name=f'VAdjIEEE.LowerPulse_{template_name}',
        )
    )
    raise_contact: Var = model.algebraic(
        'RaiseContactPu',
        raise_command * (bypass + (Const(1.0) - bypass) * raise_pulse),
        Const(0.0),
    )
    lower_contact: Var = model.algebraic(
        'LowerContactPu',
        lower_command * (bypass + (Const(1.0) - bypass) * lower_pulse),
        Const(0.0),
    )
    reference: Var = vfactory.add_var(f'VAdjPu_{template_name}')
    model.differential(
        reference,
        (maximum - minimum) / travel_time * (raise_contact - lower_contact),
        Const(1.0),
        minimum,
        maximum,
    )
    template: RmsModelTemplate = model.finish((reference,), 'CGMES VAdjIEEE voltage adjuster')
    template.comment = (
        'IEEE 421.5-2005 Figure 11-1: bounded reference slew with bypassable '
        'periodic raise/lower contacts.'
    )
    return template
