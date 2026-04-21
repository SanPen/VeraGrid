# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Clock _sig'.

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
from VeraGridEngine.Utils.procedural_logic import reset
from VeraGridEngine.enumerations import DeviceType

def build_typ_480__clock_sig_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Clock _sig__480'

def build_typ_480__clock_sig_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_480__clock_sig_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    # Declare the state variables used by the template.
    Clock_sig_x: Var = vf.add_var('Clock _sig__x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Clock_sig_clock: Var = vf.add_var('Clock _sig_clock_' + template_name)
    extfrq: Var = vf.add_var('extfrq_' + template_name)
    output: Var = vf.add_var('output_' + template_name)
    # Declare the differential variables used by the template.
    d_Clock_sig_x: Var = vf.add_diff_var('d_Clock _sig__x_' + template_name, base_var=Clock_sig_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((sym.Const(2.0) * sym.abs(extfrq)))
    state_variables: list[Var] = list()
    state_variables.append(Clock_sig_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((output - Clock_sig_clock))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(output)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Clock_sig_x)
    input_variables: list[Var] = list()
    input_variables.append(extfrq)
    output_variables: list[Var] = list()
    output_variables.append(output)
    event_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Clock_sig_clock] = vf.add_const(0.0, name='')
    initial_equations[Clock_sig_x] = vf.add_const(0.0, name='')
    initial_equations[output] = Clock_sig_clock
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(reset(Clock_sig_x, (Clock_sig_x - 1.5), 0.0))
    procedural_logic_entries.append(reset(Clock_sig_clock, (Clock_sig_x - 0.5), 0.0))
    procedural_logic_entries.append(reset(Clock_sig_clock, (Clock_sig_x - 1.5), 1.0))

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

