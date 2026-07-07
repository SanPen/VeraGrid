# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Kp+Ki/s _rst_hold'.

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

def build_typ_461__kp_ki_s_rst_hold_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Kp+Ki/s _rst_hold__461'

def build_typ_461__kp_ki_s_rst_hold_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_461__kp_ki_s_rst_hold_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Kp_Ki_s_rst_hold_Ki: Var = vf.add_var('Kp+Ki/s _rst_hold__Ki_' + template_name)
    Kp_Ki_s_rst_hold_Kp: Var = vf.add_var('Kp+Ki/s _rst_hold__Kp_' + template_name)
    # Declare the state variables used by the template.
    Kp_Ki_s_rst_hold_x: Var = vf.add_var('Kp+Ki/s _rst_hold__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Kp_Ki_s_rst_hold_proc_lastvalue_1: Var = vf.add_var('Kp+Ki/s _rst_hold__proc_lastvalue_1_' + template_name)
    Kp_Ki_s_rst_hold_proc_select_0: Var = vf.add_var('Kp+Ki/s _rst_hold__proc_select_0_' + template_name)
    Kp_Ki_s_rst_hold_proc_select_2: Var = vf.add_var('Kp+Ki/s _rst_hold__proc_select_2_' + template_name)
    Kp_Ki_s_rst_hold_x_init: Var = vf.add_var('Kp+Ki/s _rst_hold_x_init_' + template_name)
    hold: Var = vf.add_var('hold_' + template_name)
    rst: Var = vf.add_var('rst_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_Kp_Ki_s_rst_hold_x: Var = vf.add_diff_var('d_Kp+Ki/s _rst_hold__x_' + template_name, base_var=Kp_Ki_s_rst_hold_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((Kp_Ki_s_rst_hold_proc_select_0 * sym.Const(0.0)) + ((sym.Const(1.0) - Kp_Ki_s_rst_hold_proc_select_0) * (Kp_Ki_s_rst_hold_Ki * yi))))
    state_variables: list[Var] = list()
    state_variables.append(Kp_Ki_s_rst_hold_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo - ((Kp_Ki_s_rst_hold_proc_select_2 * Kp_Ki_s_rst_hold_proc_lastvalue_1) + ((sym.Const(1.0) - Kp_Ki_s_rst_hold_proc_select_2) * ((Kp_Ki_s_rst_hold_Kp * yi) + Kp_Ki_s_rst_hold_x)))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Kp_Ki_s_rst_hold_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    input_variables.append(hold)
    input_variables.append(rst)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Kp_Ki_s_rst_hold_Kp] = vf.add_const(None, name='Kp')
    event_parameters[Kp_Ki_s_rst_hold_Ki] = vf.add_const(None, name='Ki')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Kp_Ki_s_rst_hold_proc_select_0] = vf.add_const(0.0, name='')
    mode_parameters[Kp_Ki_s_rst_hold_proc_lastvalue_1] = vf.add_const(0.0, name='')
    mode_parameters[Kp_Ki_s_rst_hold_proc_select_2] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Kp_Ki_s_rst_hold_x_init] = Kp_Ki_s_rst_hold_x
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=Kp_Ki_s_rst_hold_proc_select_0, source=hold))
    procedural_logic_entries.append(lastvalue(yo, output=Kp_Ki_s_rst_hold_proc_lastvalue_1))
    procedural_logic_entries.append(sampled_value(output=Kp_Ki_s_rst_hold_proc_select_2, source=hold))
    procedural_logic_entries.append(reset(Kp_Ki_s_rst_hold_x, rst, Kp_Ki_s_rst_hold_x_init))

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

