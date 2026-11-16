# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Rate limiter {s'.

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
from VeraGridEngine.Utils.procedural_logic import lastvalue
from VeraGridEngine.enumerations import DeviceType

def build_typ_333__rate_limiter_s_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Rate limiter {s__333'

def build_typ_333__rate_limiter_s_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name = build_typ_333__rate_limiter_s_default_template_name()
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
    Rate_limiter_s_proc_lastvalue_0: Var = vf.add_var('Rate limiter {s__proc_lastvalue_0_' + template_name)
    Rate_limiter_s_proc_lastvalue_1: Var = vf.add_var('Rate limiter {s__proc_lastvalue_1_' + template_name)
    Rate_limiter_s_dt: Var = vf.add_var('Rate limiter {s_dt_' + template_name)
    Rate_limiter_s_dy: Var = vf.add_var('Rate limiter {s_dy_' + template_name)
    Rate_limiter_s_t0: Var = vf.add_var('Rate limiter {s_t0_' + template_name)
    Rate_limiter_s_yi0: Var = vf.add_var('Rate limiter {s_yi0_' + template_name)
    glob_time: Var = vf.add_var('glob_time_' + template_name)
    grd_down: Var = vf.add_var('grd_down_' + template_name)
    grd_up: Var = vf.add_var('grd_up_' + template_name)
    yi: Var = vf.add_var('yi_' + template_name)
    yo: Var = vf.add_var('yo_' + template_name)
    # Declare the differential variables used by the template.

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_variables: list[Var] = list()
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((Rate_limiter_s_t0 - Rate_limiter_s_proc_lastvalue_0))
    algebraic_equations.append((Rate_limiter_s_yi0 - Rate_limiter_s_proc_lastvalue_1))
    algebraic_equations.append((Rate_limiter_s_dt - (glob_time - Rate_limiter_s_t0)))
    algebraic_equations.append((Rate_limiter_s_dy - (((-sym.abs(grd_down)) + ((((yi - Rate_limiter_s_yi0) / ((Rate_limiter_s_dt * sym.heaviside((Rate_limiter_s_dt - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside((Rate_limiter_s_dt - sym.Const(1e-12))))))) - (-sym.abs(grd_down))) * sym.heaviside((((yi - Rate_limiter_s_yi0) / ((Rate_limiter_s_dt * sym.heaviside((Rate_limiter_s_dt - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside((Rate_limiter_s_dt - sym.Const(1e-12))))))) - (-sym.abs(grd_down)))))) - ((((yi - Rate_limiter_s_yi0) / ((Rate_limiter_s_dt * sym.heaviside((Rate_limiter_s_dt - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside((Rate_limiter_s_dt - sym.Const(1e-12))))))) - sym.abs(grd_up)) * sym.heaviside((((yi - Rate_limiter_s_yi0) / ((Rate_limiter_s_dt * sym.heaviside((Rate_limiter_s_dt - sym.Const(1e-12)))) + (sym.Const(1e-12) * (sym.Const(1) - sym.heaviside((Rate_limiter_s_dt - sym.Const(1e-12))))))) - sym.abs(grd_up)))))))
    algebraic_equations.append((yo - ((Rate_limiter_s_dy * Rate_limiter_s_dt) + Rate_limiter_s_yi0)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(Rate_limiter_s_t0)
    algebraic_variables.append(Rate_limiter_s_yi0)
    algebraic_variables.append(Rate_limiter_s_dt)
    algebraic_variables.append(Rate_limiter_s_dy)
    algebraic_variables.append(yo)
    differential_variables: list[Var] = list()
    input_variables: list[Var] = list()
    input_variables.append(yi)
    input_variables.append(grd_up)
    input_variables.append(grd_down)
    output_variables: list[Var] = list()
    output_variables.append(yo)
    event_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters: dict[Var, Expr | Const] = dict()
    mode_parameters[Rate_limiter_s_proc_lastvalue_0] = vf.add_const(0.0, name='')
    mode_parameters[Rate_limiter_s_proc_lastvalue_1] = vf.add_const(0.0, name='')
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[Rate_limiter_s_dt] = vf.add_const(0.001, name='')
    initial_equations[Rate_limiter_s_dy] = vf.add_const(0.0, name='')
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    procedural_logic_entries: list[object] = list()
    procedural_logic_entries.append(lastvalue(glob_time, output=Rate_limiter_s_proc_lastvalue_0))
    procedural_logic_entries.append(lastvalue(yo, output=Rate_limiter_s_proc_lastvalue_1))

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

