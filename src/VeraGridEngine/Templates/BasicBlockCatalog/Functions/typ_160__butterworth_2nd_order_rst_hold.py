# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Butterworth 2nd order _rst_hold'.

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

def build_typ_160__butterworth_2nd_order_rst_hold_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Butterworth 2nd order _rst_hold__160'

def build_typ_160__butterworth_2nd_order_rst_hold_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_160__butterworth_2nd_order_rst_hold_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Butterworth_2nd_order_rst_hold_wc: Var = vf.add_var('Butterworth 2nd order _rst_hold__wc_' + template_name)
    # Declare the state variables used by the template.
    Butterworth_2nd_order_rst_hold_x1: Var = vf.add_var('Butterworth 2nd order _rst_hold__x1_' + template_name)
    Butterworth_2nd_order_rst_hold_x2: Var = vf.add_var('Butterworth 2nd order _rst_hold__x2_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Butterworth_2nd_order_rst_hold_proc_lastvalue_2: Var = vf.add_var('Butterworth 2nd order _rst_hold__proc_lastvalue_2_' + template_name)
    Butterworth_2nd_order_rst_hold_proc_select_0: Var = vf.add_var('Butterworth 2nd order _rst_hold__proc_select_0_' + template_name)
    Butterworth_2nd_order_rst_hold_proc_select_1: Var = vf.add_var('Butterworth 2nd order _rst_hold__proc_select_1_' + template_name)
    Butterworth_2nd_order_rst_hold_proc_select_3: Var = vf.add_var('Butterworth 2nd order _rst_hold__proc_select_3_' + template_name)
    Butterworth_2nd_order_rst_hold_wc_2: Var = vf.add_var('Butterworth 2nd order _rst_hold_wc_2_' + template_name)
    Butterworth_2nd_order_rst_hold_x1_init: Var = vf.add_var('Butterworth 2nd order _rst_hold_x1_init_' + template_name)
    hold: Var = vf.add_var('hold_' + template_name)
    rst: Var = vf.add_var('rst_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_Butterworth_2nd_order_rst_hold_x1: Var = vf.add_diff_var('d_Butterworth 2nd order _rst_hold__x1_' + template_name, base_var=Butterworth_2nd_order_rst_hold_x1)
    d_Butterworth_2nd_order_rst_hold_x2: Var = vf.add_diff_var('d_Butterworth 2nd order _rst_hold__x2_' + template_name, base_var=Butterworth_2nd_order_rst_hold_x2)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((Butterworth_2nd_order_rst_hold_proc_select_0 * sym.Const(0.0)) + ((sym.Const(1.0) - Butterworth_2nd_order_rst_hold_proc_select_0) * Butterworth_2nd_order_rst_hold_x2)))
    state_equations.append(((Butterworth_2nd_order_rst_hold_proc_select_1 * sym.Const(0.0)) + ((sym.Const(1.0) - Butterworth_2nd_order_rst_hold_proc_select_1) * ((((-Butterworth_2nd_order_rst_hold_wc_2) * Butterworth_2nd_order_rst_hold_x1) - ((sym.Const(1.414) * Butterworth_2nd_order_rst_hold_wc) * Butterworth_2nd_order_rst_hold_x2)) + yi))))
    state_variables: list[Var] = list()
    state_variables.append(Butterworth_2nd_order_rst_hold_x1)
    state_variables.append(Butterworth_2nd_order_rst_hold_x2)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo - ((Butterworth_2nd_order_rst_hold_proc_select_3 * Butterworth_2nd_order_rst_hold_proc_lastvalue_2) + ((sym.Const(1.0) - Butterworth_2nd_order_rst_hold_proc_select_3) * (Butterworth_2nd_order_rst_hold_wc_2 * Butterworth_2nd_order_rst_hold_x1)))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Butterworth_2nd_order_rst_hold_x1)
    differential_variables.append(d_Butterworth_2nd_order_rst_hold_x2)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    input_variables.append(hold)
    input_variables.append(rst)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Butterworth_2nd_order_rst_hold_wc] = vf.add_const(None, name='wc')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Butterworth_2nd_order_rst_hold_proc_select_0] = vf.add_const(0.0, name='')
    mode_parameters[Butterworth_2nd_order_rst_hold_proc_select_1] = vf.add_const(0.0, name='')
    mode_parameters[Butterworth_2nd_order_rst_hold_proc_lastvalue_2] = vf.add_const(0.0, name='')
    mode_parameters[Butterworth_2nd_order_rst_hold_proc_select_3] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Butterworth_2nd_order_rst_hold_wc_2] = (Butterworth_2nd_order_rst_hold_wc * Butterworth_2nd_order_rst_hold_wc)
    initial_equations[Butterworth_2nd_order_rst_hold_x1] = (yi / Butterworth_2nd_order_rst_hold_wc_2)
    initial_equations[Butterworth_2nd_order_rst_hold_x2] = vf.add_const(0.0, name='')
    initial_equations[Butterworth_2nd_order_rst_hold_x1_init] = Butterworth_2nd_order_rst_hold_x1
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=Butterworth_2nd_order_rst_hold_proc_select_0, source=hold))
    procedural_logic_entries.append(sampled_value(output=Butterworth_2nd_order_rst_hold_proc_select_1, source=hold))
    procedural_logic_entries.append(lastvalue(yo, output=Butterworth_2nd_order_rst_hold_proc_lastvalue_2))
    procedural_logic_entries.append(sampled_value(output=Butterworth_2nd_order_rst_hold_proc_select_3, source=hold))
    procedural_logic_entries.append(reset(Butterworth_2nd_order_rst_hold_x1, rst, Butterworth_2nd_order_rst_hold_x1_init))
    procedural_logic_entries.append(reset(Butterworth_2nd_order_rst_hold_x2, rst, 0.0))

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

