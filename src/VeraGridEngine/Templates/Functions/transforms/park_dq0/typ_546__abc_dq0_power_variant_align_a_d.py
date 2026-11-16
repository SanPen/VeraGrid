# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'abc->dq0 (power variant -- align a->d)'.

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

def build_typ_546__abc_dq0_power_variant_align_a_d_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'abc->dq0 (power variant -- align a->d)__546'

def build_typ_546__abc_dq0_power_variant_align_a_d_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_546__abc_dq0_power_variant_align_a_d_default_template_name()
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
    abc_dq0_power_variant_align_a_d_ratio2_3: Var = vf.add_var('abc->dq0 (power variant -- align a->d)_ratio2_3_' + template_name)
    abc_dq0_power_variant_align_a_d_twopi_3: Var = vf.add_var('abc->dq0 (power variant -- align a->d)_twopi_3_' + template_name)
    b: Var = vf.add_var('b_' + template_name)
    c: Var = vf.add_var('c_' + template_name)
    d: Var = vf.add_var('d_' + template_name)
    q: Var = vf.add_var('q_' + template_name)
    theta: Var = vf.add_var('theta_' + template_name)
    zero: Var = vf.add_var('zero_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((d - (abc_dq0_power_variant_align_a_d_ratio2_3 * (((sym.cos(theta) * a) + (sym.cos((theta - abc_dq0_power_variant_align_a_d_twopi_3)) * b)) + (sym.cos((theta + abc_dq0_power_variant_align_a_d_twopi_3)) * c)))))
    algebraic_equations.append((q - (abc_dq0_power_variant_align_a_d_ratio2_3 * ((((-sym.sin(theta)) * a) - (sym.sin((theta - abc_dq0_power_variant_align_a_d_twopi_3)) * b)) - (sym.sin((theta + abc_dq0_power_variant_align_a_d_twopi_3)) * c)))))
    algebraic_equations.append((zero - (abc_dq0_power_variant_align_a_d_ratio2_3 * (((sym.Const(0.5) * a) + (sym.Const(0.5) * b)) + (sym.Const(0.5) * c)))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(d)
    algebraic_variables.append(q)
    algebraic_variables.append(zero)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(a)
    input_variables.append(b)
    input_variables.append(c)
    input_variables.append(theta)
    output_variables: list[Var] = list()
    output_variables.append(d)
    output_variables.append(q)
    output_variables.append(zero)
    event_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[abc_dq0_power_variant_align_a_d_ratio2_3] = (sym.Const(2.0) / sym.Const(3.0))
    initial_equations[abc_dq0_power_variant_align_a_d_twopi_3] = (sym.Const(6.283185307179586) / sym.Const(3.0))
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

