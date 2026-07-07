# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Limit [p] (complex)'.

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
from VeraGridEngine.Utils.procedural_logic import sampled_value
from VeraGridEngine.enumerations import DeviceType

def build_typ_314__limit_p_complex_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Limit [p] (complex)__314'

def build_typ_314__limit_p_complex_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_314__limit_p_complex_default_template_name()
    else:
        template_name = name

    # Allocate the template container before building the symbolic surface.
    template: EmtModelTemplate = EmtModelTemplate()
    template.tpe = DeviceType.NoDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    Limit_p_complex_MAG_MAX: Var = vf.add_var('Limit [p] (complex)__MAG_MAX_' + template_name)
    # Declare the state variables used by the template.
    # Declare the algebraic/shared variables used by the template.
    Limit_p_complex_proc_select_0: Var = vf.add_var('Limit [p] (complex)__proc_select_0_' + template_name)
    Limit_p_complex_mag: Var = vf.add_var('Limit [p] (complex)_mag_' + template_name)
    Limit_p_complex_rescale_factor: Var = vf.add_var('Limit [p] (complex)_rescale_factor_' + template_name)
    d: Var = vf.add_var('d_' + template_name)
    q: Var = vf.add_var('q_' + template_name)
    yo_d: Var = vf.add_var('yo_d_' + template_name)
    yo_q: Var = vf.add_var('yo_q_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Limit_p_complex_mag - sym.sqrt(((d * d) + (q * q)))))
    algebraic_equations.append((Limit_p_complex_rescale_factor - ((Limit_p_complex_proc_select_0 * (Limit_p_complex_mag / Limit_p_complex_MAG_MAX)) + ((sym.Const(1.0) - Limit_p_complex_proc_select_0) * sym.Const(1.0)))))
    algebraic_equations.append((yo_d - (d / Limit_p_complex_rescale_factor)))
    algebraic_equations.append((yo_q - (q / Limit_p_complex_rescale_factor)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Limit_p_complex_mag)
    algebraic_variables.append(Limit_p_complex_rescale_factor)
    algebraic_variables.append(yo_d)
    algebraic_variables.append(yo_q)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(d)
    input_variables.append(q)
    output_variables: list[Var] = list()
    output_variables.append(yo_d)
    output_variables.append(yo_q)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[Limit_p_complex_MAG_MAX] = vf.add_const(None, name='MAG_MAX')
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Limit_p_complex_proc_select_0] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(sampled_value(output=Limit_p_complex_proc_select_0, source=sym.Comparison(lhs=Limit_p_complex_mag, op=sym.CmpOp.GT, rhs=Limit_p_complex_MAG_MAX)))

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

