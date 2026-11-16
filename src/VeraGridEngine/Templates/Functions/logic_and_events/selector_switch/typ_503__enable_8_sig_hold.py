# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Enable 8 sig _hold'.

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

def build_typ_503__enable_8_sig_hold_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Enable 8 sig _hold__503'

def build_typ_503__enable_8_sig_hold_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_503__enable_8_sig_hold_default_template_name()
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
    Enable_8_sig_hold_proc_lastvalue_0: Var = vf.add_var('Enable 8 sig _hold__proc_lastvalue_0_' + template_name)
    Enable_8_sig_hold_proc_lastvalue_10: Var = vf.add_var('Enable 8 sig _hold__proc_lastvalue_10_' + template_name)
    Enable_8_sig_hold_proc_lastvalue_12: Var = vf.add_var('Enable 8 sig _hold__proc_lastvalue_12_' + template_name)
    Enable_8_sig_hold_proc_lastvalue_14: Var = vf.add_var('Enable 8 sig _hold__proc_lastvalue_14_' + template_name)
    Enable_8_sig_hold_proc_lastvalue_2: Var = vf.add_var('Enable 8 sig _hold__proc_lastvalue_2_' + template_name)
    Enable_8_sig_hold_proc_lastvalue_4: Var = vf.add_var('Enable 8 sig _hold__proc_lastvalue_4_' + template_name)
    Enable_8_sig_hold_proc_lastvalue_6: Var = vf.add_var('Enable 8 sig _hold__proc_lastvalue_6_' + template_name)
    Enable_8_sig_hold_proc_lastvalue_8: Var = vf.add_var('Enable 8 sig _hold__proc_lastvalue_8_' + template_name)
    Enable_8_sig_hold_proc_select_1: Var = vf.add_var('Enable 8 sig _hold__proc_select_1_' + template_name)
    Enable_8_sig_hold_proc_select_11: Var = vf.add_var('Enable 8 sig _hold__proc_select_11_' + template_name)
    Enable_8_sig_hold_proc_select_13: Var = vf.add_var('Enable 8 sig _hold__proc_select_13_' + template_name)
    Enable_8_sig_hold_proc_select_15: Var = vf.add_var('Enable 8 sig _hold__proc_select_15_' + template_name)
    Enable_8_sig_hold_proc_select_3: Var = vf.add_var('Enable 8 sig _hold__proc_select_3_' + template_name)
    Enable_8_sig_hold_proc_select_5: Var = vf.add_var('Enable 8 sig _hold__proc_select_5_' + template_name)
    Enable_8_sig_hold_proc_select_7: Var = vf.add_var('Enable 8 sig _hold__proc_select_7_' + template_name)
    Enable_8_sig_hold_proc_select_9: Var = vf.add_var('Enable 8 sig _hold__proc_select_9_' + template_name)
    Enable_8_sig_hold_yi1_register: Var = vf.add_var('Enable 8 sig _hold_yi1_register_' + template_name)
    Enable_8_sig_hold_yi2_register: Var = vf.add_var('Enable 8 sig _hold_yi2_register_' + template_name)
    Enable_8_sig_hold_yi3_register: Var = vf.add_var('Enable 8 sig _hold_yi3_register_' + template_name)
    Enable_8_sig_hold_yi4_register: Var = vf.add_var('Enable 8 sig _hold_yi4_register_' + template_name)
    Enable_8_sig_hold_yi5_register: Var = vf.add_var('Enable 8 sig _hold_yi5_register_' + template_name)
    Enable_8_sig_hold_yi6_register: Var = vf.add_var('Enable 8 sig _hold_yi6_register_' + template_name)
    Enable_8_sig_hold_yi7_register: Var = vf.add_var('Enable 8 sig _hold_yi7_register_' + template_name)
    Enable_8_sig_hold_yi8_register: Var = vf.add_var('Enable 8 sig _hold_yi8_register_' + template_name)
    yi1: Var = vf.add_var('yi1_' + template_name)
    yi2: Var = vf.add_var('yi2_' + template_name)
    yi3: Var = vf.add_var('yi3_' + template_name)
    yi4: Var = vf.add_var('yi4_' + template_name)
    yi5: Var = vf.add_var('yi5_' + template_name)
    yi6: Var = vf.add_var('yi6_' + template_name)
    yi7: Var = vf.add_var('yi7_' + template_name)
    yi8: Var = vf.add_var('yi8_' + template_name)
    yo1: Var = vf.add_var('yo1_' + template_name)
    yo2: Var = vf.add_var('yo2_' + template_name)
    yo3: Var = vf.add_var('yo3_' + template_name)
    yo4: Var = vf.add_var('yo4_' + template_name)
    yo5: Var = vf.add_var('yo5_' + template_name)
    yo6: Var = vf.add_var('yo6_' + template_name)
    yo7: Var = vf.add_var('yo7_' + template_name)
    yo8: Var = vf.add_var('yo8_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo1 - Enable_8_sig_hold_yi1_register))
    algebraic_equations.append((yo2 - Enable_8_sig_hold_yi2_register))
    algebraic_equations.append((yo3 - Enable_8_sig_hold_yi3_register))
    algebraic_equations.append((yo4 - Enable_8_sig_hold_yi4_register))
    algebraic_equations.append((yo5 - Enable_8_sig_hold_yi5_register))
    algebraic_equations.append((yo6 - Enable_8_sig_hold_yi6_register))
    algebraic_equations.append((yo7 - Enable_8_sig_hold_yi7_register))
    algebraic_equations.append((yo8 - Enable_8_sig_hold_yi8_register))
    algebraic_equations.append((Enable_8_sig_hold_yi1_register - ((Enable_8_sig_hold_proc_select_1 * yi1) + ((sym.Const(1.0) - Enable_8_sig_hold_proc_select_1) * Enable_8_sig_hold_proc_lastvalue_0))))
    algebraic_equations.append((Enable_8_sig_hold_yi2_register - ((Enable_8_sig_hold_proc_select_3 * yi2) + ((sym.Const(1.0) - Enable_8_sig_hold_proc_select_3) * Enable_8_sig_hold_proc_lastvalue_2))))
    algebraic_equations.append((Enable_8_sig_hold_yi3_register - ((Enable_8_sig_hold_proc_select_5 * yi3) + ((sym.Const(1.0) - Enable_8_sig_hold_proc_select_5) * Enable_8_sig_hold_proc_lastvalue_4))))
    algebraic_equations.append((Enable_8_sig_hold_yi4_register - ((Enable_8_sig_hold_proc_select_7 * yi4) + ((sym.Const(1.0) - Enable_8_sig_hold_proc_select_7) * Enable_8_sig_hold_proc_lastvalue_6))))
    algebraic_equations.append((Enable_8_sig_hold_yi5_register - ((Enable_8_sig_hold_proc_select_9 * yi5) + ((sym.Const(1.0) - Enable_8_sig_hold_proc_select_9) * Enable_8_sig_hold_proc_lastvalue_8))))
    algebraic_equations.append((Enable_8_sig_hold_yi6_register - ((Enable_8_sig_hold_proc_select_11 * yi6) + ((sym.Const(1.0) - Enable_8_sig_hold_proc_select_11) * Enable_8_sig_hold_proc_lastvalue_10))))
    algebraic_equations.append((Enable_8_sig_hold_yi7_register - ((Enable_8_sig_hold_proc_select_13 * yi7) + ((sym.Const(1.0) - Enable_8_sig_hold_proc_select_13) * Enable_8_sig_hold_proc_lastvalue_12))))
    algebraic_equations.append((Enable_8_sig_hold_yi8_register - ((Enable_8_sig_hold_proc_select_15 * yi8) + ((sym.Const(1.0) - Enable_8_sig_hold_proc_select_15) * Enable_8_sig_hold_proc_lastvalue_14))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo1)
    algebraic_variables.append(yo2)
    algebraic_variables.append(yo3)
    algebraic_variables.append(yo4)
    algebraic_variables.append(yo5)
    algebraic_variables.append(yo6)
    algebraic_variables.append(yo7)
    algebraic_variables.append(yo8)
    algebraic_variables.append(Enable_8_sig_hold_yi1_register)
    algebraic_variables.append(Enable_8_sig_hold_yi2_register)
    algebraic_variables.append(Enable_8_sig_hold_yi3_register)
    algebraic_variables.append(Enable_8_sig_hold_yi4_register)
    algebraic_variables.append(Enable_8_sig_hold_yi5_register)
    algebraic_variables.append(Enable_8_sig_hold_yi6_register)
    algebraic_variables.append(Enable_8_sig_hold_yi7_register)
    algebraic_variables.append(Enable_8_sig_hold_yi8_register)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(yi1)
    input_variables.append(yi2)
    input_variables.append(yi3)
    input_variables.append(yi4)
    input_variables.append(yi5)
    input_variables.append(yi6)
    input_variables.append(yi7)
    input_variables.append(yi8)
    input_variables.append(Enable)
    output_variables: list[Var] = list()
    output_variables.append(yo1)
    output_variables.append(yo2)
    output_variables.append(yo3)
    output_variables.append(yo4)
    output_variables.append(yo5)
    output_variables.append(yo6)
    output_variables.append(yo7)
    output_variables.append(yo8)
    event_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Enable_8_sig_hold_proc_lastvalue_0] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_select_1] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_lastvalue_2] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_select_3] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_lastvalue_4] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_select_5] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_lastvalue_6] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_select_7] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_lastvalue_8] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_select_9] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_lastvalue_10] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_select_11] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_lastvalue_12] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_select_13] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_lastvalue_14] = vf.add_const(0.0, name='')
    mode_parameters[Enable_8_sig_hold_proc_select_15] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Enable_8_sig_hold_yi1_register] = yi1
    initial_equations[Enable_8_sig_hold_yi2_register] = yi2
    initial_equations[Enable_8_sig_hold_yi3_register] = yi3
    initial_equations[Enable_8_sig_hold_yi4_register] = yi4
    initial_equations[Enable_8_sig_hold_yi5_register] = yi5
    initial_equations[Enable_8_sig_hold_yi6_register] = yi6
    initial_equations[Enable_8_sig_hold_yi7_register] = yi7
    initial_equations[Enable_8_sig_hold_yi8_register] = yi8
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(lastvalue(Enable_8_sig_hold_yi1_register, output=Enable_8_sig_hold_proc_lastvalue_0))
    procedural_logic_entries.append(sampled_value(output=Enable_8_sig_hold_proc_select_1, source=Enable))
    procedural_logic_entries.append(lastvalue(Enable_8_sig_hold_yi2_register, output=Enable_8_sig_hold_proc_lastvalue_2))
    procedural_logic_entries.append(sampled_value(output=Enable_8_sig_hold_proc_select_3, source=Enable))
    procedural_logic_entries.append(lastvalue(Enable_8_sig_hold_yi3_register, output=Enable_8_sig_hold_proc_lastvalue_4))
    procedural_logic_entries.append(sampled_value(output=Enable_8_sig_hold_proc_select_5, source=Enable))
    procedural_logic_entries.append(lastvalue(Enable_8_sig_hold_yi4_register, output=Enable_8_sig_hold_proc_lastvalue_6))
    procedural_logic_entries.append(sampled_value(output=Enable_8_sig_hold_proc_select_7, source=Enable))
    procedural_logic_entries.append(lastvalue(Enable_8_sig_hold_yi5_register, output=Enable_8_sig_hold_proc_lastvalue_8))
    procedural_logic_entries.append(sampled_value(output=Enable_8_sig_hold_proc_select_9, source=Enable))
    procedural_logic_entries.append(lastvalue(Enable_8_sig_hold_yi6_register, output=Enable_8_sig_hold_proc_lastvalue_10))
    procedural_logic_entries.append(sampled_value(output=Enable_8_sig_hold_proc_select_11, source=Enable))
    procedural_logic_entries.append(lastvalue(Enable_8_sig_hold_yi7_register, output=Enable_8_sig_hold_proc_lastvalue_12))
    procedural_logic_entries.append(sampled_value(output=Enable_8_sig_hold_proc_select_13, source=Enable))
    procedural_logic_entries.append(lastvalue(Enable_8_sig_hold_yi8_register, output=Enable_8_sig_hold_proc_lastvalue_14))
    procedural_logic_entries.append(sampled_value(output=Enable_8_sig_hold_proc_select_15, source=Enable))

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

