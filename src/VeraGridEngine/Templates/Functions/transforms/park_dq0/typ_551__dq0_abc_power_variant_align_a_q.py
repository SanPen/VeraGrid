# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'dq0->abc (power variant -- align a->q)'.

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

def build_typ_551__dq0_abc_power_variant_align_a_q_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'dq0->abc (power variant -- align a->q)__551'

def build_typ_551__dq0_abc_power_variant_align_a_q_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_551__dq0_abc_power_variant_align_a_q_default_template_name()
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
    a: Var = vf.add_var('a_' + template_name)
    b: Var = vf.add_var('b_' + template_name)
    c: Var = vf.add_var('c_' + template_name)
    d: Var = vf.add_var('d_' + template_name)
    dq0_abc_power_variant_align_a_q_twopi_3: Var = vf.add_var('dq0->abc (power variant -- align a->q)_twopi_3_' + template_name)
    q: Var = vf.add_var('q_' + template_name)
    theta: Var = vf.add_var('theta_' + template_name)
    zero: Var = vf.add_var('zero_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((a - (((sym.sin(theta) * d) + (sym.cos(theta) * q)) + zero)))
    algebraic_equations.append((b - (((sym.sin((theta - dq0_abc_power_variant_align_a_q_twopi_3)) * d) + (sym.cos((theta - dq0_abc_power_variant_align_a_q_twopi_3)) * q)) + zero)))
    algebraic_equations.append((c - (((sym.sin((theta + dq0_abc_power_variant_align_a_q_twopi_3)) * d) + (sym.cos((theta + dq0_abc_power_variant_align_a_q_twopi_3)) * q)) + zero)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(a)
    algebraic_variables.append(b)
    algebraic_variables.append(c)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(d)
    input_variables.append(q)
    input_variables.append(zero)
    input_variables.append(theta)
    output_variables: list[Var] = list()
    output_variables.append(a)
    output_variables.append(b)
    output_variables.append(c)
    event_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[dq0_abc_power_variant_align_a_q_twopi_3] = (sym.Const(6.283185307179586) / sym.Const(3.0))
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

