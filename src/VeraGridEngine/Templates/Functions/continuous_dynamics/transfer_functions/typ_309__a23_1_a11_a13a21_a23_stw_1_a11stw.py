# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)'.

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

def build_typ_309__a23_1_a11_a13a21_a23_stw_1_a11stw_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)__309'

def build_typ_309__a23_1_a11_a13a21_a23_stw_1_a11stw_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_309__a23_1_a11_a13a21_a23_stw_1_a11stw_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_Tw: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)__Tw_' + template_name)
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_a11: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)__a11_' + template_name)
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_a13: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)__a13_' + template_name)
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_a21: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)__a21_' + template_name)
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_a23: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)__a23_' + template_name)
    # Declare the state variables used by the template.
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_x: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_Ta: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)_Ta_' + template_name)
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_Tb: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)_Tb_' + template_name)
    a23_1_a11_a13a21_a23_sTw_1_a11sTw_dx: Var = vf.add_var('a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)_dx_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_a23_1_a11_a13a21_a23_sTw_1_a11sTw_x: Var = vf.add_diff_var('d_a23(1+(a11-a13a21/a23)sTw)/(1+a11sTw)__x_' + template_name, base_var=a23_1_a11_a13a21_a23_sTw_1_a11sTw_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(a23_1_a11_a13a21_a23_sTw_1_a11sTw_dx)
    state_variables: list[Var] = list()
    state_variables.append(a23_1_a11_a13a21_a23_sTw_1_a11sTw_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((a23_1_a11_a13a21_a23_sTw_1_a11sTw_dx - ((yi - a23_1_a11_a13a21_a23_sTw_1_a11sTw_x) / a23_1_a11_a13a21_a23_sTw_1_a11sTw_Ta)))
    algebraic_equations.append((yo - (a23_1_a11_a13a21_a23_sTw_1_a11sTw_a23 * (a23_1_a11_a13a21_a23_sTw_1_a11sTw_x + (a23_1_a11_a13a21_a23_sTw_1_a11sTw_Tb * a23_1_a11_a13a21_a23_sTw_1_a11sTw_dx)))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(a23_1_a11_a13a21_a23_sTw_1_a11sTw_dx)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_a23_1_a11_a13a21_a23_sTw_1_a11sTw_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[a23_1_a11_a13a21_a23_sTw_1_a11sTw_a11] = vf.add_const(None, name='a11')
    event_parameters[a23_1_a11_a13a21_a23_sTw_1_a11sTw_a13] = vf.add_const(None, name='a13')
    event_parameters[a23_1_a11_a13a21_a23_sTw_1_a11sTw_a21] = vf.add_const(None, name='a21')
    event_parameters[a23_1_a11_a13a21_a23_sTw_1_a11sTw_a23] = vf.add_const(None, name='a23')
    event_parameters[a23_1_a11_a13a21_a23_sTw_1_a11sTw_Tw] = vf.add_const(None, name='Tw')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[a23_1_a11_a13a21_a23_sTw_1_a11sTw_Tb] = ((a23_1_a11_a13a21_a23_sTw_1_a11sTw_a11 - ((a23_1_a11_a13a21_a23_sTw_1_a11sTw_a13 * a23_1_a11_a13a21_a23_sTw_1_a11sTw_a21) / a23_1_a11_a13a21_a23_sTw_1_a11sTw_a23)) * a23_1_a11_a13a21_a23_sTw_1_a11sTw_Tw)
    initial_equations[a23_1_a11_a13a21_a23_sTw_1_a11sTw_Ta] = (a23_1_a11_a13a21_a23_sTw_1_a11sTw_a11 * a23_1_a11_a13a21_a23_sTw_1_a11sTw_Tw)
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

