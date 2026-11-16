# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block '(1+sTb)(sTa)^2/(1+sTa)^4'.

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

def build_typ_195__1_stb_sta_2_1_sta_4_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return '(1+sTb)(sTa)^2/(1+sTa)^4__195'

def build_typ_195__1_stb_sta_2_1_sta_4_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_195__1_stb_sta_2_1_sta_4_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    v_1_sTb_sTa_2_1_sTa_4_Ta: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4__Ta_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_Tb: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4__Tb_' + template_name)
    # Declare the state variables used by the template.
    v_1_sTb_sTa_2_1_sTa_4_x1: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4__x1_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_x2: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4__x2_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_x3: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4__x3_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_x4: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4__x4_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    v_1_sTb_sTa_2_1_sTa_4_dx1: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4_dx1_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_dx2: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4_dx2_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_dx3: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4_dx3_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_yo1: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4_yo1_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_yo2: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4_yo2_' + template_name)
    v_1_sTb_sTa_2_1_sTa_4_yo3: Var = vf.add_var('(1+sTb)(sTa)^2/(1+sTa)^4_yo3_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_1_sTb_sTa_2_1_sTa_4_x1: Var = vf.add_diff_var('d_(1+sTb)(sTa)^2/(1+sTa)^4__x1_' + template_name, base_var=v_1_sTb_sTa_2_1_sTa_4_x1)
    d_1_sTb_sTa_2_1_sTa_4_x2: Var = vf.add_diff_var('d_(1+sTb)(sTa)^2/(1+sTa)^4__x2_' + template_name, base_var=v_1_sTb_sTa_2_1_sTa_4_x2)
    d_1_sTb_sTa_2_1_sTa_4_x3: Var = vf.add_diff_var('d_(1+sTb)(sTa)^2/(1+sTa)^4__x3_' + template_name, base_var=v_1_sTb_sTa_2_1_sTa_4_x3)
    d_1_sTb_sTa_2_1_sTa_4_x4: Var = vf.add_diff_var('d_(1+sTb)(sTa)^2/(1+sTa)^4__x4_' + template_name, base_var=v_1_sTb_sTa_2_1_sTa_4_x4)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(v_1_sTb_sTa_2_1_sTa_4_dx1)
    state_equations.append(v_1_sTb_sTa_2_1_sTa_4_dx2)
    state_equations.append(v_1_sTb_sTa_2_1_sTa_4_dx3)
    state_equations.append(((v_1_sTb_sTa_2_1_sTa_4_yo3 - v_1_sTb_sTa_2_1_sTa_4_x4) / v_1_sTb_sTa_2_1_sTa_4_Ta))
    state_variables: list[Var] = list()
    state_variables.append(v_1_sTb_sTa_2_1_sTa_4_x1)
    state_variables.append(v_1_sTb_sTa_2_1_sTa_4_x2)
    state_variables.append(v_1_sTb_sTa_2_1_sTa_4_x3)
    state_variables.append(v_1_sTb_sTa_2_1_sTa_4_x4)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((v_1_sTb_sTa_2_1_sTa_4_dx1 - ((yi - v_1_sTb_sTa_2_1_sTa_4_x1) / v_1_sTb_sTa_2_1_sTa_4_Ta)))
    algebraic_equations.append((v_1_sTb_sTa_2_1_sTa_4_yo1 - (v_1_sTb_sTa_2_1_sTa_4_x1 + (v_1_sTb_sTa_2_1_sTa_4_Tb * v_1_sTb_sTa_2_1_sTa_4_dx1))))
    algebraic_equations.append((v_1_sTb_sTa_2_1_sTa_4_dx2 - ((v_1_sTb_sTa_2_1_sTa_4_yo1 - v_1_sTb_sTa_2_1_sTa_4_x2) / v_1_sTb_sTa_2_1_sTa_4_Ta)))
    algebraic_equations.append((v_1_sTb_sTa_2_1_sTa_4_yo2 - (v_1_sTb_sTa_2_1_sTa_4_Ta * v_1_sTb_sTa_2_1_sTa_4_dx2)))
    algebraic_equations.append((v_1_sTb_sTa_2_1_sTa_4_dx3 - ((v_1_sTb_sTa_2_1_sTa_4_yo2 - v_1_sTb_sTa_2_1_sTa_4_x3) / v_1_sTb_sTa_2_1_sTa_4_Ta)))
    algebraic_equations.append((v_1_sTb_sTa_2_1_sTa_4_yo3 - (v_1_sTb_sTa_2_1_sTa_4_Ta * v_1_sTb_sTa_2_1_sTa_4_dx3)))
    algebraic_equations.append((yo - v_1_sTb_sTa_2_1_sTa_4_x4))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(v_1_sTb_sTa_2_1_sTa_4_dx1)
    algebraic_variables.append(v_1_sTb_sTa_2_1_sTa_4_yo1)
    algebraic_variables.append(v_1_sTb_sTa_2_1_sTa_4_dx2)
    algebraic_variables.append(v_1_sTb_sTa_2_1_sTa_4_yo2)
    algebraic_variables.append(v_1_sTb_sTa_2_1_sTa_4_dx3)
    algebraic_variables.append(v_1_sTb_sTa_2_1_sTa_4_yo3)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_1_sTb_sTa_2_1_sTa_4_x1)
    differential_variables.append(d_1_sTb_sTa_2_1_sTa_4_x2)
    differential_variables.append(d_1_sTb_sTa_2_1_sTa_4_x3)
    differential_variables.append(d_1_sTb_sTa_2_1_sTa_4_x4)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[v_1_sTb_sTa_2_1_sTa_4_Tb] = vf.add_const(None, name='Tb')
    event_parameters[v_1_sTb_sTa_2_1_sTa_4_Ta] = vf.add_const(None, name='Ta')
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

