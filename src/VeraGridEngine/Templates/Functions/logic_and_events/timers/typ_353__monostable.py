# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Monostable'.

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
from VeraGridEngine.Utils.procedural_logic import flipflop, lastvalue, reset, sampled_value
from VeraGridEngine.enumerations import DeviceType

def build_typ_353__monostable_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Monostable__353'

def build_typ_353__monostable_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_353__monostable_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Monostable_T: Var = vf.add_var('Monostable__T_' + template_name)
    # Declare the state variables used by the template.
    Monostable_x: Var = vf.add_var('Monostable__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Monostable_proc_flipflop_1: Var = vf.add_var('Monostable__proc_flipflop_1_' + template_name)
    Monostable_proc_lastvalue_0: Var = vf.add_var('Monostable__proc_lastvalue_0_' + template_name)
    Monostable_proc_select_2: Var = vf.add_var('Monostable__proc_select_2_' + template_name)
    Monostable_rst: Var = vf.add_var('Monostable_rst_' + template_name)
    Monostable_set: Var = vf.add_var('Monostable_set_' + template_name)
    Monostable_t0: Var = vf.add_var('Monostable_t0_' + template_name)
    glob_time: Var = vf.add_var('glob_time_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_Monostable_x: Var = vf.add_diff_var('d_Monostable__x_' + template_name, base_var=Monostable_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(((Monostable_proc_select_2 * sym.Const(1.0)) + ((sym.Const(1.0) - Monostable_proc_select_2) * sym.Const(0.0))))
    state_variables: list[Var] = list()
    state_variables.append(Monostable_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Monostable_set - (sym.heaviside(((sym.Const(0.5) - Monostable_proc_lastvalue_0) - sym.Const(1e-06))) * sym.heaviside(((yi - sym.Const(0.5)) + sym.Const(1e-06))))))
    algebraic_equations.append((Monostable_rst - sym.heaviside((((Monostable_x - Monostable_T) - sym.Const(0.0)) - sym.Const(1e-06)))))
    algebraic_equations.append((yo - Monostable_proc_flipflop_1))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Monostable_set)
    algebraic_variables.append(Monostable_rst)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Monostable_x)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Monostable_T] = vf.add_const(None, name='T')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Monostable_proc_lastvalue_0] = vf.add_const(0.0, name='')
    mode_parameters[Monostable_proc_flipflop_1] = vf.add_const(0.0, name='')
    mode_parameters[Monostable_proc_select_2] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Monostable_t0] = glob_time
    initial_equations[Monostable_set] = vf.add_const(0.0, name='')
    initial_equations[Monostable_rst] = vf.add_const(0.0, name='')
    initial_equations[Monostable_x] = vf.add_const(0.0, name='')
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(lastvalue(yi, output=Monostable_proc_lastvalue_0))
    procedural_logic_entries.append(flipflop(Monostable_set, Monostable_rst, output=Monostable_proc_flipflop_1))
    procedural_logic_entries.append(sampled_value(output=Monostable_proc_select_2, source=(sym.heaviside(((glob_time - (Monostable_t0 + 0.001)) - 1e-06)) * sym.heaviside(((yo - 0.5) - 1e-06)))))
    procedural_logic_entries.append(reset(Monostable_x, ((Monostable_x - Monostable_T) + 0.500001), 0.0))

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

