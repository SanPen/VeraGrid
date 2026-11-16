# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 's^2K/(1+sT)^2'.

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

def build_typ_205__s_2k_1_st_2_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 's^2K/(1+sT)^2__205'

def build_typ_205__s_2k_1_st_2_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_205__s_2k_1_st_2_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    s_2K_1_sT_2_K: Var = vf.add_var('s^2K/(1+sT)^2__K_' + template_name)
    s_2K_1_sT_2_T: Var = vf.add_var('s^2K/(1+sT)^2__T_' + template_name)
    # Declare the state variables used by the template.
    s_2K_1_sT_2_x1: Var = vf.add_var('s^2K/(1+sT)^2__x1_' + template_name)
    s_2K_1_sT_2_x2: Var = vf.add_var('s^2K/(1+sT)^2__x2_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    s_2K_1_sT_2_dx1: Var = vf.add_var('s^2K/(1+sT)^2_dx1_' + template_name)
    s_2K_1_sT_2_dx2: Var = vf.add_var('s^2K/(1+sT)^2_dx2_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_s_2K_1_sT_2_x1: Var = vf.add_diff_var('d_s^2K/(1+sT)^2__x1_' + template_name, base_var=s_2K_1_sT_2_x1)
    d_s_2K_1_sT_2_x2: Var = vf.add_diff_var('d_s^2K/(1+sT)^2__x2_' + template_name, base_var=s_2K_1_sT_2_x2)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(s_2K_1_sT_2_dx1)
    state_equations.append(s_2K_1_sT_2_dx2)
    state_variables: list[Var] = list()
    state_variables.append(s_2K_1_sT_2_x1)
    state_variables.append(s_2K_1_sT_2_x2)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((s_2K_1_sT_2_dx1 - (((s_2K_1_sT_2_K * yi) - s_2K_1_sT_2_x1) / s_2K_1_sT_2_T)))
    algebraic_equations.append((s_2K_1_sT_2_dx2 - ((s_2K_1_sT_2_dx1 - s_2K_1_sT_2_x2) / s_2K_1_sT_2_T)))
    algebraic_equations.append((yo - s_2K_1_sT_2_dx2))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(s_2K_1_sT_2_dx1)
    algebraic_variables.append(s_2K_1_sT_2_dx2)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_s_2K_1_sT_2_x1)
    differential_variables.append(d_s_2K_1_sT_2_x2)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[s_2K_1_sT_2_K] = vf.add_const(None, name='K')
    event_parameters[s_2K_1_sT_2_T] = vf.add_const(None, name='T')
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

