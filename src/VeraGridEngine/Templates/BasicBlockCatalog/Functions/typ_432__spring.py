# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Spring'.

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

def build_typ_432__spring_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Spring__432'

def build_typ_432__spring_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_432__spring_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Spring_D: Var = vf.add_var('Spring__D_' + template_name)
    Spring_K: Var = vf.add_var('Spring__K_' + template_name)
    # Declare the state variables used by the template.
    Spring_xphi: Var = vf.add_var('Spring__xphi_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    M: Var = vf.add_var('M_' + template_name)
    Spring_dxphi: Var = vf.add_var('Spring_dxphi_' + template_name)
    omega1: Var = vf.add_var('omega1_' + template_name)
    omega2: Var = vf.add_var('omega2_' + template_name)
    # Declare the differential variables used by the template.
    d_Spring_xphi: Var = vf.add_diff_var('d_Spring__xphi_' + template_name, base_var=Spring_xphi)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((Spring_dxphi * Spring_K))
    state_variables: list[Var] = list()
    state_variables.append(Spring_xphi)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Spring_dxphi - (omega1 - omega2)))
    algebraic_equations.append((M - (Spring_xphi + (Spring_D * Spring_dxphi))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Spring_dxphi)
    algebraic_variables.append(M)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Spring_xphi)
    input_variables: list[Var] = list()
    input_variables.append(omega1)
    input_variables.append(omega2)
    output_variables: list[Var] = list()
    output_variables.append(M)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Spring_K] = vf.add_const(None, name='K')
    event_parameters[Spring_D] = vf.add_const(None, name='D')
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

