# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Clarke transform (power invariant)'.

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

def build_typ_533__clarke_transform_power_invariant_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Clarke transform (power invariant)__533'

def build_typ_533__clarke_transform_power_invariant_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_533__clarke_transform_power_invariant_default_template_name()
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
    alpha: Var = vf.add_var('alpha_' + template_name)
    b: Var = vf.add_var('b_' + template_name)
    beta: Var = vf.add_var('beta_' + template_name)
    c: Var = vf.add_var('c_' + template_name)
    gamma: Var = vf.add_var('gamma_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((alpha - (((sym.sqrt((sym.Const(2.0) / sym.Const(3.0))) * a) - ((sym.Const(1.0) / sym.sqrt(sym.Const(6.0))) * b)) - ((sym.Const(1.0) / sym.sqrt(sym.Const(6.0))) * c))))
    algebraic_equations.append((beta - (((sym.Const(1.0) / sym.sqrt(sym.Const(2.0))) * b) - (sym.sqrt(sym.Const(2.0)) * c))))
    algebraic_equations.append((gamma - ((((sym.Const(1.0) / sym.sqrt(sym.Const(3.0))) * a) + ((sym.Const(1.0) / sym.sqrt(sym.Const(3.0))) * b)) + ((sym.Const(1.0) / sym.sqrt(sym.Const(3.0))) * c))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(alpha)
    algebraic_variables.append(beta)
    algebraic_variables.append(gamma)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(a)
    input_variables.append(b)
    input_variables.append(c)
    output_variables: list[Var] = list()
    output_variables.append(alpha)
    output_variables.append(beta)
    output_variables.append(gamma)
    event_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
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

