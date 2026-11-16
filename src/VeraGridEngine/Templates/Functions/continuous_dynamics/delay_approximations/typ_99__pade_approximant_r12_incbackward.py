# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Pade approximant R12 _incbackward'.

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

def build_typ_99__pade_approximant_r12_incbackward_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Pade approximant R12 _incbackward__99'

def build_typ_99__pade_approximant_r12_incbackward_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_99__pade_approximant_r12_incbackward_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Pade_approximant_R12_incbackward_Td: Var = vf.add_var('Pade approximant R12 _incbackward__Td_' + template_name)
    # Declare the state variables used by the template.
    Pade_approximant_R12_incbackward_x1: Var = vf.add_var('Pade approximant R12 _incbackward__x1_' + template_name)
    Pade_approximant_R12_incbackward_x2: Var = vf.add_var('Pade approximant R12 _incbackward__x2_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    Pade_approximant_R12_incbackward_A0: Var = vf.add_var('Pade approximant R12 _incbackward_A0_' + template_name)
    Pade_approximant_R12_incbackward_A1: Var = vf.add_var('Pade approximant R12 _incbackward_A1_' + template_name)
    Pade_approximant_R12_incbackward_A2: Var = vf.add_var('Pade approximant R12 _incbackward_A2_' + template_name)
    Pade_approximant_R12_incbackward_B0: Var = vf.add_var('Pade approximant R12 _incbackward_B0_' + template_name)
    Pade_approximant_R12_incbackward_B1: Var = vf.add_var('Pade approximant R12 _incbackward_B1_' + template_name)
    Pade_approximant_R12_incbackward_offset: Var = vf.add_var('Pade approximant R12 _incbackward_offset_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.
    d_Pade_approximant_R12_incbackward_x1: Var = vf.add_diff_var('d_Pade approximant R12 _incbackward__x1_' + template_name, base_var=Pade_approximant_R12_incbackward_x1)
    d_Pade_approximant_R12_incbackward_x2: Var = vf.add_diff_var('d_Pade approximant R12 _incbackward__x2_' + template_name, base_var=Pade_approximant_R12_incbackward_x2)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(Pade_approximant_R12_incbackward_x2)
    state_equations.append((((-((Pade_approximant_R12_incbackward_A0 * Pade_approximant_R12_incbackward_x1) + (Pade_approximant_R12_incbackward_A1 * Pade_approximant_R12_incbackward_x2))) / Pade_approximant_R12_incbackward_A2) + ((yi - Pade_approximant_R12_incbackward_offset) / Pade_approximant_R12_incbackward_A2)))
    state_variables: list[Var] = list()
    state_variables.append(Pade_approximant_R12_incbackward_x1)
    state_variables.append(Pade_approximant_R12_incbackward_x2)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((yo - (((Pade_approximant_R12_incbackward_B0 * Pade_approximant_R12_incbackward_x1) + (Pade_approximant_R12_incbackward_B1 * Pade_approximant_R12_incbackward_x2)) + Pade_approximant_R12_incbackward_offset)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    differential_variables.append(d_Pade_approximant_R12_incbackward_x1)
    differential_variables.append(d_Pade_approximant_R12_incbackward_x2)
    input_variables: list[Var] = list()
    input_variables.append(yi)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Pade_approximant_R12_incbackward_Td] = vf.add_const(None, name='Td')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Pade_approximant_R12_incbackward_offset] = yo
    initial_equations[Pade_approximant_R12_incbackward_x1] = vf.add_const(0.0, name='')
    initial_equations[Pade_approximant_R12_incbackward_x2] = vf.add_const(0.0, name='')
    initial_equations[Pade_approximant_R12_incbackward_A0] = vf.add_const(1.0, name='')
    initial_equations[Pade_approximant_R12_incbackward_A1] = (sym.Const(0.666666667) * ((Pade_approximant_R12_incbackward_Td * sym.heaviside((Pade_approximant_R12_incbackward_Td - sym.Const(0.0001)))) + (sym.Const(0.0001) * (sym.Const(1) - sym.heaviside((Pade_approximant_R12_incbackward_Td - sym.Const(0.0001)))))))
    initial_equations[Pade_approximant_R12_incbackward_A2] = ((sym.Const(0.166666667) * ((Pade_approximant_R12_incbackward_Td * sym.heaviside((Pade_approximant_R12_incbackward_Td - sym.Const(0.0001)))) + (sym.Const(0.0001) * (sym.Const(1) - sym.heaviside((Pade_approximant_R12_incbackward_Td - sym.Const(0.0001))))))) * ((Pade_approximant_R12_incbackward_Td * sym.heaviside((Pade_approximant_R12_incbackward_Td - sym.Const(0.0001)))) + (sym.Const(0.0001) * (sym.Const(1) - sym.heaviside((Pade_approximant_R12_incbackward_Td - sym.Const(0.0001)))))))
    initial_equations[Pade_approximant_R12_incbackward_B0] = vf.add_const(1.0, name='')
    initial_equations[Pade_approximant_R12_incbackward_B1] = ((-sym.Const(0.333333333)) * ((Pade_approximant_R12_incbackward_Td * sym.heaviside((Pade_approximant_R12_incbackward_Td - sym.Const(0.0001)))) + (sym.Const(0.0001) * (sym.Const(1) - sym.heaviside((Pade_approximant_R12_incbackward_Td - sym.Const(0.0001)))))))
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

