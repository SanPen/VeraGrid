# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block '(1+ATs)/(1+BTs)'.

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

def build_typ_293__1_ats_1_bts_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return '(1+ATs)/(1+BTs)__293'

def build_typ_293__1_ats_1_bts_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_293__1_ats_1_bts_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    v_1_ATs_1_BTs_A: Var = vf.add_var('(1+ATs)/(1+BTs)__A_' + template_name)
    v_1_ATs_1_BTs_B: Var = vf.add_var('(1+ATs)/(1+BTs)__B_' + template_name)
    v_1_ATs_1_BTs_T: Var = vf.add_var('(1+ATs)/(1+BTs)__T_' + template_name)
    # Declare the state variables used by the template.
    v_1_ATs_1_BTs_x: Var = vf.add_var('(1+ATs)/(1+BTs)__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    v_1_ATs_1_BTs_dx: Var = vf.add_var('(1+ATs)/(1+BTs)_dx_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_1_ATs_1_BTs_x: Var = vf.add_diff_var('d_(1+ATs)/(1+BTs)__x_' + template_name, base_var=v_1_ATs_1_BTs_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(v_1_ATs_1_BTs_dx)
    state_variables: list[Var] = list()
    state_variables.append(v_1_ATs_1_BTs_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((v_1_ATs_1_BTs_dx - ((yi - v_1_ATs_1_BTs_x) / (v_1_ATs_1_BTs_B * v_1_ATs_1_BTs_T))))
    algebraic_equations.append((yo - (v_1_ATs_1_BTs_x + ((v_1_ATs_1_BTs_dx * v_1_ATs_1_BTs_A) * v_1_ATs_1_BTs_T))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(v_1_ATs_1_BTs_dx)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_1_ATs_1_BTs_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[v_1_ATs_1_BTs_A] = vf.add_const(None, name='A')
    event_parameters[v_1_ATs_1_BTs_B] = vf.add_const(None, name='B')
    event_parameters[v_1_ATs_1_BTs_T] = vf.add_const(None, name='T')
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

