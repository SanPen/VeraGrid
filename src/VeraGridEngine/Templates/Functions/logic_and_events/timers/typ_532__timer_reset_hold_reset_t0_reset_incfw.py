# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Timer (reset/hold reset/t0) _reset_incfw'.

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
from VeraGridEngine.Utils.procedural_logic import lastvalue, sampled_value, selfix
from VeraGridEngine.enumerations import DeviceType

def build_typ_532__timer_reset_hold_reset_t0_reset_incfw_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Timer (reset/hold reset/t0) _reset_incfw__532'

def build_typ_532__timer_reset_hold_reset_t0_reset_incfw_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_532__timer_reset_hold_reset_t0_reset_incfw_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Timer_reset_hold_reset_t0_reset_incfw_flank: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw__flank_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_t_start_delay: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw__t_start_delay_' + template_name)
    # Declare the state variables used by the template.
    Timer_reset_hold_reset_t0_reset_incfw_x: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Timer_reset_hold_reset_t0_reset_incfw_proc_lastvalue_3: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw__proc_lastvalue_3_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_proc_select_2: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw__proc_select_2_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_proc_select_4: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw__proc_select_4_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_0: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw__proc_selfix_0_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_1: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw__proc_selfix_1_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_dir: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw_dir_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_tinc: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw_tinc_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_tldf: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw_tldf_' + template_name)
    Timer_reset_hold_reset_t0_reset_incfw_tx: Var = vf.add_var('Timer (reset/hold reset/t0) _reset_incfw_tx_' + template_name)
    glob_time: Var = vf.add_var('glob_time_' + template_name)
    rst: Var = vf.add_var('rst_' + template_name)
    t0: Var = vf.add_var('t0_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_Timer_reset_hold_reset_t0_reset_incfw_x: Var = vf.add_diff_var('d_Timer (reset/hold reset/t0) _reset_incfw__x_' + template_name, base_var=Timer_reset_hold_reset_t0_reset_incfw_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((Timer_reset_hold_reset_t0_reset_incfw_proc_select_2 * sym.Const(1.0)) + ((sym.Const(1.0) - Timer_reset_hold_reset_t0_reset_incfw_proc_select_2) * sym.Const(0.0))))
    state_variables: list[Var] = list()
    state_variables.append(Timer_reset_hold_reset_t0_reset_incfw_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Timer_reset_hold_reset_t0_reset_incfw_dir - ((Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_1 * rst) + ((sym.Const(1.0) - Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_1) * ((-rst) + sym.Const(1.0))))))
    algebraic_equations.append((Timer_reset_hold_reset_t0_reset_incfw_tx - ((Timer_reset_hold_reset_t0_reset_incfw_proc_select_4 * Timer_reset_hold_reset_t0_reset_incfw_x) + ((sym.Const(1.0) - Timer_reset_hold_reset_t0_reset_incfw_proc_select_4) * Timer_reset_hold_reset_t0_reset_incfw_proc_lastvalue_3))))
    algebraic_equations.append((yo - ((Timer_reset_hold_reset_t0_reset_incfw_x - Timer_reset_hold_reset_t0_reset_incfw_tx) + Timer_reset_hold_reset_t0_reset_incfw_tinc)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Timer_reset_hold_reset_t0_reset_incfw_dir)
    algebraic_variables.append(Timer_reset_hold_reset_t0_reset_incfw_tx)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Timer_reset_hold_reset_t0_reset_incfw_x)
    input_variables: list[Var] = list()
    input_variables.append(rst)
    input_variables.append(t0)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Timer_reset_hold_reset_t0_reset_incfw_flank] = vf.add_const(None, name='flank')
    event_parameters[Timer_reset_hold_reset_t0_reset_incfw_t_start_delay] = vf.add_const(None, name='t_start_delay')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_0] = vf.add_const(0.0, name='')
    mode_parameters[Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_1] = vf.add_const(0.0, name='')
    mode_parameters[Timer_reset_hold_reset_t0_reset_incfw_proc_select_2] = vf.add_const(0.0, name='')
    mode_parameters[Timer_reset_hold_reset_t0_reset_incfw_proc_lastvalue_3] = vf.add_const(0.0, name='')
    mode_parameters[Timer_reset_hold_reset_t0_reset_incfw_proc_select_4] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Timer_reset_hold_reset_t0_reset_incfw_dir] = ((Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_0 * rst) + ((sym.Const(1.0) - Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_0) * ((-rst) + sym.Const(1.0))))
    initial_equations[Timer_reset_hold_reset_t0_reset_incfw_tldf] = glob_time
    initial_equations[Timer_reset_hold_reset_t0_reset_incfw_tx] = vf.add_const(0.0, name='')
    initial_equations[Timer_reset_hold_reset_t0_reset_incfw_x] = vf.add_const(0.0, name='')
    initial_equations[Timer_reset_hold_reset_t0_reset_incfw_tinc] = t0
    initial_equations[yo] = t0
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Timer_reset_hold_reset_t0_reset_incfw_flank, op=sym.CmpOp.LT, rhs=0.5), output=Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_0))
    procedural_logic_entries.append(selfix(sym.Comparison(lhs=Timer_reset_hold_reset_t0_reset_incfw_flank, op=sym.CmpOp.LT, rhs=0.5), output=Timer_reset_hold_reset_t0_reset_incfw_proc_selfix_1))
    procedural_logic_entries.append(sampled_value(output=Timer_reset_hold_reset_t0_reset_incfw_proc_select_2, source=sym.Comparison(lhs=(glob_time - Timer_reset_hold_reset_t0_reset_incfw_tldf), op=sym.CmpOp.GT, rhs=Timer_reset_hold_reset_t0_reset_incfw_t_start_delay)))
    procedural_logic_entries.append(lastvalue(Timer_reset_hold_reset_t0_reset_incfw_tx, output=Timer_reset_hold_reset_t0_reset_incfw_proc_lastvalue_3))
    procedural_logic_entries.append(sampled_value(output=Timer_reset_hold_reset_t0_reset_incfw_proc_select_4, source=sym.Comparison(lhs=Timer_reset_hold_reset_t0_reset_incfw_dir, op=sym.CmpOp.GT, rhs=0.5)))

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

