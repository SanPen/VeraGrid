# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Sine Wave Generator'.

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

def build_typ_485__sine_wave_generator_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Sine Wave Generator__485'

def build_typ_485__sine_wave_generator_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_485__sine_wave_generator_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Sine_Wave_Generator_a: Var = vf.add_var('Sine Wave Generator__a_' + template_name)
    Sine_Wave_Generator_f: Var = vf.add_var('Sine Wave Generator__f_' + template_name)
    Sine_Wave_Generator_phi: Var = vf.add_var('Sine Wave Generator__phi_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Sine_Wave_Generator_deg_to_rad: Var = vf.add_var('Sine Wave Generator_deg_to_rad_' + template_name)
    Sine_Wave_Generator_t: Var = vf.add_var('Sine Wave Generator_t_' + template_name)
    Sine_Wave_Generator_two_pi: Var = vf.add_var('Sine Wave Generator_two_pi_' + template_name)
    glob_time: Var = vf.add_var('glob_time_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Sine_Wave_Generator_t - glob_time))
    algebraic_equations.append((yo - (Sine_Wave_Generator_a * sym.sin((((Sine_Wave_Generator_two_pi * Sine_Wave_Generator_f) * Sine_Wave_Generator_t) + (Sine_Wave_Generator_phi / Sine_Wave_Generator_deg_to_rad))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Sine_Wave_Generator_t)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Sine_Wave_Generator_a] = vf.add_const(None, name='a')
    event_parameters[Sine_Wave_Generator_f] = vf.add_const(None, name='f')
    event_parameters[Sine_Wave_Generator_phi] = vf.add_const(None, name='phi')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Sine_Wave_Generator_deg_to_rad] = (sym.Const(180.0) / sym.Const(3.141592653589793))
    initial_equations[Sine_Wave_Generator_two_pi] = (sym.Const(2.0) * sym.Const(3.141592653589793))
    initial_equations[yo] = (Sine_Wave_Generator_a * sym.sin((((Sine_Wave_Generator_two_pi * Sine_Wave_Generator_f) * Sine_Wave_Generator_t) + (Sine_Wave_Generator_phi / Sine_Wave_Generator_deg_to_rad))))
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

