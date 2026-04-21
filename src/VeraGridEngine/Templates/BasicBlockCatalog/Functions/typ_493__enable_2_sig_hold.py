# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Enable 2 sig _hold'.

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
from VeraGridEngine.Utils.procedural_logic import lastvalue, sampled_value
from VeraGridEngine.enumerations import DeviceType

def build_typ_493__enable_2_sig_hold_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Enable 2 sig _hold__493'

def build_typ_493__enable_2_sig_hold_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_493__enable_2_sig_hold_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Enable: Var = vf.add_var('Enable_' + template_name)
    Enable_2_sig_hold_proc_lastvalue_0: Var = vf.add_var('Enable 2 sig _hold__proc_lastvalue_0_' + template_name)
    Enable_2_sig_hold_proc_lastvalue_2: Var = vf.add_var('Enable 2 sig _hold__proc_lastvalue_2_' + template_name)
    Enable_2_sig_hold_proc_select_1: Var = vf.add_var('Enable 2 sig _hold__proc_select_1_' + template_name)
    Enable_2_sig_hold_proc_select_3: Var = vf.add_var('Enable 2 sig _hold__proc_select_3_' + template_name)
    Enable_2_sig_hold_yi1_register: Var = vf.add_var('Enable 2 sig _hold_yi1_register_' + template_name)
    Enable_2_sig_hold_yi2_register: Var = vf.add_var('Enable 2 sig _hold_yi2_register_' + template_name)
    yi1: Var = vf.add_var('yi1_' + template_name)
    yi2: Var = vf.add_var('yi2_' + template_name)
    yo1: Var = vf.add_var('yo1_' + template_name)
    yo2: Var = vf.add_var('yo2_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo1 - Enable_2_sig_hold_yi1_register))
    algebraic_equations.append((yo2 - Enable_2_sig_hold_yi2_register))
    algebraic_equations.append((Enable_2_sig_hold_yi1_register - ((Enable_2_sig_hold_proc_select_1 * yi1) + ((sym.Const(1.0) - Enable_2_sig_hold_proc_select_1) * Enable_2_sig_hold_proc_lastvalue_0))))
    algebraic_equations.append((Enable_2_sig_hold_yi2_register - ((Enable_2_sig_hold_proc_select_3 * yi2) + ((sym.Const(1.0) - Enable_2_sig_hold_proc_select_3) * Enable_2_sig_hold_proc_lastvalue_2))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo1)
    algebraic_variables.append(yo2)
    algebraic_variables.append(Enable_2_sig_hold_yi1_register)
    algebraic_variables.append(Enable_2_sig_hold_yi2_register)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(yi1)
    input_variables.append(yi2)
    input_variables.append(Enable)
    output_variables: list[Var] = list()
    output_variables.append(yo1)
    output_variables.append(yo2)
    event_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Enable_2_sig_hold_proc_lastvalue_0] = vf.add_const(0.0, name='')
    mode_parameters[Enable_2_sig_hold_proc_select_1] = vf.add_const(0.0, name='')
    mode_parameters[Enable_2_sig_hold_proc_lastvalue_2] = vf.add_const(0.0, name='')
    mode_parameters[Enable_2_sig_hold_proc_select_3] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Enable_2_sig_hold_yi1_register] = yi1
    initial_equations[Enable_2_sig_hold_yi2_register] = yi2
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(lastvalue(Enable_2_sig_hold_yi1_register, output=Enable_2_sig_hold_proc_lastvalue_0))
    procedural_logic_entries.append(sampled_value(output=Enable_2_sig_hold_proc_select_1, source=Enable))
    procedural_logic_entries.append(lastvalue(Enable_2_sig_hold_yi2_register, output=Enable_2_sig_hold_proc_lastvalue_2))
    procedural_logic_entries.append(sampled_value(output=Enable_2_sig_hold_proc_select_3, source=Enable))

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

