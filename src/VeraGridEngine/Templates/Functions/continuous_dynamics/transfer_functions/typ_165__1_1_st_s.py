# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block '1/(1+sT) (s'.

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
from VeraGridEngine.Utils.procedural_logic import lastvalue, reset, sampled_value
from VeraGridEngine.enumerations import DeviceType

def build_typ_165__1_1_st_s_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return '1/(1+sT) (s__165'

def build_typ_165__1_1_st_s_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_165__1_1_st_s_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    v_1_1_sT_s_T: Var = vf.add_var('1/(1+sT) (s__T_' + template_name)
    # Declare the state variables used by the template.
    v_1_1_sT_s_x: Var = vf.add_var('1/(1+sT) (s__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    v_1_1_sT_s_proc_lastvalue_1: Var = vf.add_var('1/(1+sT) (s__proc_lastvalue_1_' + template_name)
    v_1_1_sT_s_proc_select_0: Var = vf.add_var('1/(1+sT) (s__proc_select_0_' + template_name)
    v_1_1_sT_s_proc_select_2: Var = vf.add_var('1/(1+sT) (s__proc_select_2_' + template_name)
    hold: Var = vf.add_var('hold_' + template_name)
    rst: Var = vf.add_var('rst_' + template_name)
    x_rst: Var = vf.add_var('x_rst_' + template_name)
    y_max: Var = vf.add_var('y_max_' + template_name)
    y_min: Var = vf.add_var('y_min_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_1_1_sT_s_x: Var = vf.add_diff_var('d_1/(1+sT) (s__x_' + template_name, base_var=v_1_1_sT_s_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((v_1_1_sT_s_proc_select_0 * sym.Const(0.0)) + ((sym.Const(1.0) - v_1_1_sT_s_proc_select_0) * ((yi - yo) / v_1_1_sT_s_T))))
    state_variables: list[Var] = list()
    state_variables.append(v_1_1_sT_s_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo - ((v_1_1_sT_s_proc_select_2 * v_1_1_sT_s_proc_lastvalue_1) + ((sym.Const(1.0) - v_1_1_sT_s_proc_select_2) * ((y_min + ((v_1_1_sT_s_x - y_min) * sym.heaviside((v_1_1_sT_s_x - y_min)))) - ((v_1_1_sT_s_x - y_max) * sym.heaviside((v_1_1_sT_s_x - y_max))))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_1_1_sT_s_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    input_variables.append(hold)
    input_variables.append(x_rst)
    input_variables.append(y_max)
    input_variables.append(rst)
    input_variables.append(y_min)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[v_1_1_sT_s_T] = vf.add_const(None, name='T')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[v_1_1_sT_s_proc_select_0] = vf.add_const(0.0, name='')
    mode_parameters[v_1_1_sT_s_proc_lastvalue_1] = vf.add_const(0.0, name='')
    mode_parameters[v_1_1_sT_s_proc_select_2] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=v_1_1_sT_s_proc_select_0, source=hold))
    procedural_logic_entries.append(lastvalue(yo, output=v_1_1_sT_s_proc_lastvalue_1))
    procedural_logic_entries.append(sampled_value(output=v_1_1_sT_s_proc_select_2, source=hold))
    procedural_logic_entries.append(reset(v_1_1_sT_s_x, rst, x_rst))

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

