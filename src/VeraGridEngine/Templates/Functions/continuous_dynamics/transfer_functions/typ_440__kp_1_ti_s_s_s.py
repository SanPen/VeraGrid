# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Kp(1/Ti+s)/s (s)'.

This module is generated from the shipped VeraGrid catalog artifacts and keeps the
symbolic surface explicit so both humans and tools can inspect it directly.
"""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType

def build_typ_440__kp_1_ti_s_s_s_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Kp(1/Ti+s)/s (s)__440'

def build_typ_440__kp_1_ti_s_s_s_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_440__kp_1_ti_s_s_s_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Kp_1_Ti_s_s_s_Kp: Var = vf.add_var('Kp(1/Ti+s)/s (s)__Kp_' + template_name)
    Kp_1_Ti_s_s_s_Ti: Var = vf.add_var('Kp(1/Ti+s)/s (s)__Ti_' + template_name)
    Kp_1_Ti_s_s_s_Tt: Var = vf.add_var('Kp(1/Ti+s)/s (s)__Tt_' + template_name)
    # Declare the state variables used by the template.
    Kp_1_Ti_s_s_s_x: Var = vf.add_var('Kp(1/Ti+s)/s (s)__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    yo_lim: Var = vf.add_var('yo_lim_' + template_name)
    # Declare the differential variables used by the template.
    d_Kp_1_Ti_s_s_s_x: Var = vf.add_diff_var('d_Kp(1/Ti+s)/s (s)__x_' + template_name, base_var=Kp_1_Ti_s_s_s_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((Kp_1_Ti_s_s_s_Kp / Kp_1_Ti_s_s_s_Ti) * yi) + ((yo_lim - yo) / Kp_1_Ti_s_s_s_Tt)))
    state_variables: list[Var] = list()
    state_variables.append(Kp_1_Ti_s_s_s_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo - ((Kp_1_Ti_s_s_s_Kp * yi) + Kp_1_Ti_s_s_s_x)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Kp_1_Ti_s_s_s_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    input_variables.append(yo_lim)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Kp_1_Ti_s_s_s_Kp] = vf.add_const(None, name='Kp')
    event_parameters[Kp_1_Ti_s_s_s_Ti] = vf.add_const(None, name='Ti')
    event_parameters[Kp_1_Ti_s_s_s_Tt] = vf.add_const(None, name='Tt')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()

    # Assemble the final block from the explicit typed collections above.
    template.block = Block(
        state_vars=state_variables,
        state_eqs=state_equations,
        algebraic_vars=algebraic_variables,
        algebraic_eqs=algebraic_equations,
        diff_vars=differential_variables,
        init_eqs=initial_equations,
        diff_init_eqs=differential_initial_equations,
        in_vars=input_variables,
        out_vars=output_variables,
        event_dict=event_parameters,
        mode_dict=mode_parameters,
        procedural_logic=procedural_logic_entries,
        name=template_name,
    )

    return template

