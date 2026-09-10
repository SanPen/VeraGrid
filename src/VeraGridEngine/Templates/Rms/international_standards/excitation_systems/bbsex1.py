# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'BbSex1'.

This is the runtime implementation shipped by VeraGrid.
It exposes the imported public interface, explicit symbolic equations, and
"""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp

def build_bbsex1_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'BbSex1'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    avr_Efd0Pu: Var = vf.add_var('avr.Efd0Pu_' + template_name)
    avr_EfdMaxPu: Var = vf.add_var('avr.EfdMaxPu_' + template_name)
    avr_EfdMinPu: Var = vf.add_var('avr.EfdMinPu_' + template_name)
    avr_K: Var = vf.add_var('avr.K_' + template_name)
    avr_Us0Pu: Var = vf.add_var('avr.Us0Pu_' + template_name)
    avr_UsRef0Pu: Var = vf.add_var('avr.UsRef0Pu_' + template_name)
    avr_VrMaxPu: Var = vf.add_var('avr.VrMaxPu_' + template_name)
    avr_VrMinPu: Var = vf.add_var('avr.VrMinPu_' + template_name)
    avr_add_k1: Var = vf.add_var('avr.add.k1_' + template_name)
    avr_add_k2: Var = vf.add_var('avr.add.k2_' + template_name)
    avr_firstOrder_T: Var = vf.add_var('avr.firstOrder.T_' + template_name)
    avr_firstOrder_initType: Var = vf.add_var('avr.firstOrder.initType_' + template_name)
    avr_firstOrder_k: Var = vf.add_var('avr.firstOrder.k_' + template_name)
    avr_firstOrder_y_start: Var = vf.add_var('avr.firstOrder.y_start_' + template_name)
    avr_firstOrder1_T: Var = vf.add_var('avr.firstOrder1.T_' + template_name)
    avr_firstOrder1_initType: Var = vf.add_var('avr.firstOrder1.initType_' + template_name)
    avr_firstOrder1_k: Var = vf.add_var('avr.firstOrder1.k_' + template_name)
    avr_firstOrder1_y_start: Var = vf.add_var('avr.firstOrder1.y_start_' + template_name)
    avr_gain1_k: Var = vf.add_var('avr.gain1.k_' + template_name)
    avr_gain2_k: Var = vf.add_var('avr.gain2.k_' + template_name)
    avr_gain3_k: Var = vf.add_var('avr.gain3.k_' + template_name)
    avr_gain4_k: Var = vf.add_var('avr.gain4.k_' + template_name)
    avr_limiter_homotopyType: Var = vf.add_var('avr.limiter.homotopyType_' + template_name)
    avr_limiter_limitsAtInit: Var = vf.add_var('avr.limiter.limitsAtInit_' + template_name)
    avr_limiter_strict: Var = vf.add_var('avr.limiter.strict_' + template_name)
    avr_limiter_uMax: Var = vf.add_var('avr.limiter.uMax_' + template_name)
    avr_limiter_uMin: Var = vf.add_var('avr.limiter.uMin_' + template_name)
    avr_sum1_k_1: Var = vf.add_var('avr.sum1.k[1]_' + template_name)
    avr_sum1_k_2: Var = vf.add_var('avr.sum1.k[2]_' + template_name)
    avr_sum1_k_3: Var = vf.add_var('avr.sum1.k[3]_' + template_name)
    avr_sum1_k_4: Var = vf.add_var('avr.sum1.k[4]_' + template_name)
    avr_sum1_k_5: Var = vf.add_var('avr.sum1.k[5]_' + template_name)
    avr_sum1_nin: Var = vf.add_var('avr.sum1.nin_' + template_name)
    avr_t1: Var = vf.add_var('avr.t1_' + template_name)
    avr_t2: Var = vf.add_var('avr.t2_' + template_name)
    avr_t3: Var = vf.add_var('avr.t3_' + template_name)
    avr_t4: Var = vf.add_var('avr.t4_' + template_name)
    avr_tR: Var = vf.add_var('avr.tR_' + template_name)
    avr_transferFunction_a_1: Var = vf.add_var('avr.transferFunction.a[1]_' + template_name)
    avr_transferFunction_a_2: Var = vf.add_var('avr.transferFunction.a[2]_' + template_name)
    avr_transferFunction_a_end: Var = vf.add_var('avr.transferFunction.a_end_' + template_name)
    avr_transferFunction_b_1: Var = vf.add_var('avr.transferFunction.b[1]_' + template_name)
    avr_transferFunction_b_2: Var = vf.add_var('avr.transferFunction.b[2]_' + template_name)
    avr_transferFunction_bb_1: Var = vf.add_var('avr.transferFunction.bb[1]_' + template_name)
    avr_transferFunction_bb_2: Var = vf.add_var('avr.transferFunction.bb[2]_' + template_name)
    avr_transferFunction_d: Var = vf.add_var('avr.transferFunction.d_' + template_name)
    avr_transferFunction_na: Var = vf.add_var('avr.transferFunction.na_' + template_name)
    avr_transferFunction_nb: Var = vf.add_var('avr.transferFunction.nb_' + template_name)
    avr_transferFunction_nx: Var = vf.add_var('avr.transferFunction.nx_' + template_name)
    avr_transferFunction_x_start_1: Var = vf.add_var('avr.transferFunction.x_start[1]_' + template_name)
    avr_transferFunction_y_start: Var = vf.add_var('avr.transferFunction.y_start_' + template_name)
    avr_variableLimiter_homotopyType: Var = vf.add_var('avr.variableLimiter.homotopyType_' + template_name)
    avr_variableLimiter_limitsAtInit: Var = vf.add_var('avr.variableLimiter.limitsAtInit_' + template_name)
    avr_variableLimiter_strict: Var = vf.add_var('avr.variableLimiter.strict_' + template_name)
    avr_variableLimiter_ySimplified: Var = vf.add_var('avr.variableLimiter.ySimplified_' + template_name)
    # Declare the state variables used by the template.
    avr_firstOrder_y: Var = vf.add_var('avr.firstOrder.y_' + template_name)
    avr_firstOrder1_y: Var = vf.add_var('avr.firstOrder1.y_' + template_name)
    avr_transferFunction_x_scaled_1: Var = vf.add_var('avr.transferFunction.x_scaled[1]_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_avr_firstOrder_y: Var = vf.add_var('$START.avr.firstOrder.y_' + template_name)
    START_avr_firstOrder1_y: Var = vf.add_var('$START.avr.firstOrder1.y_' + template_name)
    START_avr_transferFunction_x_scaled_1: Var = vf.add_var('$START.avr.transferFunction.x_scaled[1]_' + template_name)
    avr_EfdPu: Var = vf.add_var('avr.EfdPu_' + template_name)
    avr_UOelPu: Var = vf.add_var('avr.UOelPu_' + template_name)
    avr_UPssPu: Var = vf.add_var('avr.UPssPu_' + template_name)
    avr_UUelPu: Var = vf.add_var('avr.UUelPu_' + template_name)
    avr_UsPu: Var = vf.add_var('avr.UsPu_' + template_name)
    avr_UsRefPu: Var = vf.add_var('avr.UsRefPu_' + template_name)
    avr_add_y: Var = vf.add_var('avr.add.y_' + template_name)
    avr_gain1_y: Var = vf.add_var('avr.gain1.y_' + template_name)
    avr_gain2_y: Var = vf.add_var('avr.gain2.y_' + template_name)
    avr_gain3_y: Var = vf.add_var('avr.gain3.y_' + template_name)
    avr_gain4_y: Var = vf.add_var('avr.gain4.y_' + template_name)
    avr_limiter_simplifiedExpr: Var = vf.add_var('avr.limiter.simplifiedExpr_' + template_name)
    avr_limiter_y: Var = vf.add_var('avr.limiter.y_' + template_name)
    avr_sum1_y: Var = vf.add_var('avr.sum1.y_' + template_name)
    avr_transferFunction_x_1: Var = vf.add_var('avr.transferFunction.x[1]_' + template_name)
    avr_transferFunction_y: Var = vf.add_var('avr.transferFunction.y_' + template_name)
    avr_variableLimiter_simplifiedExpr: Var = vf.add_var('avr.variableLimiter.simplifiedExpr_' + template_name)
    # Declare the differential variables used by the template.
    d_avr_firstOrder_y: Var = vf.add_diff_var('d_avr.firstOrder.y_' + template_name, base_var=avr_firstOrder_y)
    d_avr_firstOrder1_y: Var = vf.add_diff_var('d_avr.firstOrder1.y_' + template_name, base_var=avr_firstOrder1_y)
    d_avr_transferFunction_x_scaled_1: Var = vf.add_diff_var('d_avr.transferFunction.x_scaled[1]_' + template_name, base_var=avr_transferFunction_x_scaled_1)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((avr_transferFunction_a_end * avr_sum1_y) - (avr_transferFunction_a_2 * avr_transferFunction_x_scaled_1)) / avr_transferFunction_a_1))
    state_equations.append((((avr_firstOrder_k * avr_limiter_y) - avr_firstOrder_y) / avr_firstOrder_T))
    state_equations.append((((avr_firstOrder1_k * avr_UsPu) - avr_firstOrder1_y) / avr_firstOrder1_T))
    state_variables: list[Var] = list()
    state_variables.append(avr_transferFunction_x_scaled_1)
    state_variables.append(avr_firstOrder_y)
    state_variables.append(avr_firstOrder1_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((avr_sum1_y - (((((avr_sum1_k_1 * avr_UOelPu) + (avr_sum1_k_2 * avr_UPssPu)) + (avr_sum1_k_3 * avr_UUelPu)) + (avr_sum1_k_4 * avr_UsRefPu)) + (avr_sum1_k_5 * avr_firstOrder1_y))))
    algebraic_equations.append((avr_transferFunction_x_1 - (avr_transferFunction_x_scaled_1 / avr_transferFunction_a_end)))
    algebraic_equations.append((avr_transferFunction_y - (((avr_transferFunction_bb_2 - (avr_transferFunction_d * avr_transferFunction_a_2)) * avr_transferFunction_x_1) + (avr_transferFunction_d * avr_sum1_y))))
    algebraic_equations.append((avr_gain2_y - (avr_gain2_k * avr_firstOrder_y)))
    algebraic_equations.append((avr_add_y - ((avr_add_k1 * avr_transferFunction_y) + (avr_add_k2 * avr_gain2_y))))
    algebraic_equations.append((avr_gain1_y - (avr_gain1_k * avr_add_y)))
    algebraic_equations.append((avr_limiter_y - ((sym.heaviside(((avr_gain1_y - avr_limiter_uMax) - sym.Const(1e-06))) * avr_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_gain1_y - avr_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limiter_uMin - avr_gain1_y) - sym.Const(1e-06))) * avr_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limiter_uMin - avr_gain1_y) - sym.Const(1e-06)))) * avr_gain1_y))))))
    algebraic_equations.append((avr_gain3_y - (avr_gain3_k * avr_firstOrder1_y)))
    algebraic_equations.append((avr_gain4_y - (avr_gain4_k * avr_firstOrder1_y)))
    algebraic_equations.append((avr_EfdPu - ((sym.heaviside(((avr_limiter_y - avr_gain3_y) - sym.Const(1e-06))) * avr_gain3_y) + ((sym.Const(1.0) - sym.heaviside(((avr_limiter_y - avr_gain3_y) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_gain4_y - avr_limiter_y) - sym.Const(1e-06))) * avr_gain4_y) + ((sym.Const(1.0) - sym.heaviside(((avr_gain4_y - avr_limiter_y) - sym.Const(1e-06)))) * avr_limiter_y))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(avr_sum1_y)
    algebraic_variables.append(avr_transferFunction_x_1)
    algebraic_variables.append(avr_transferFunction_y)
    algebraic_variables.append(avr_gain2_y)
    algebraic_variables.append(avr_add_y)
    algebraic_variables.append(avr_gain1_y)
    algebraic_variables.append(avr_limiter_y)
    algebraic_variables.append(avr_gain3_y)
    algebraic_variables.append(avr_gain4_y)
    algebraic_variables.append(avr_EfdPu)
    algebraic_variables.append(avr_UOelPu)
    algebraic_variables.append(avr_UPssPu)
    algebraic_variables.append(avr_UUelPu)
    algebraic_variables.append(avr_UsPu)
    algebraic_variables.append(avr_UsRefPu)
    algebraic_variables.append(avr_limiter_simplifiedExpr)
    algebraic_variables.append(avr_variableLimiter_simplifiedExpr)
    algebraic_variables.append(START_avr_transferFunction_x_scaled_1)
    algebraic_variables.append(START_avr_firstOrder_y)
    algebraic_variables.append(START_avr_firstOrder1_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_avr_transferFunction_x_scaled_1)
    differential_variables.append(d_avr_firstOrder_y)
    differential_variables.append(d_avr_firstOrder1_y)
    input_variables: list[Var] = list()
    input_variables.append(avr_UOelPu)
    input_variables.append(avr_UPssPu)
    input_variables.append(avr_UUelPu)
    input_variables.append(avr_UsPu)
    input_variables.append(avr_UsRefPu)
    output_variables: list[Var] = list()
    output_variables.append(avr_EfdPu)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[avr_Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_EfdMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_EfdMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_K] = vf.add_const(100.0, name='')
    event_parameters[avr_Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_UsRef0Pu] = (avr_Us0Pu + (avr_Efd0Pu / avr_K))
    event_parameters[avr_VrMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VrMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_add_k1] = avr_K
    event_parameters[avr_add_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_T] = avr_t2
    event_parameters[avr_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_y_start] = avr_Efd0Pu
    event_parameters[avr_firstOrder1_T] = avr_tR
    event_parameters[avr_firstOrder1_k] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder1_y_start] = avr_Us0Pu
    event_parameters[avr_gain1_k] = (avr_t2 / avr_t1)
    event_parameters[avr_gain2_k] = (sym.Const(-1.0) + (avr_t1 / avr_t2))
    event_parameters[avr_gain3_k] = avr_EfdMaxPu
    event_parameters[avr_gain4_k] = avr_EfdMinPu
    event_parameters[avr_limiter_uMax] = avr_VrMaxPu
    event_parameters[avr_limiter_uMin] = avr_VrMinPu
    event_parameters[avr_sum1_k_1] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_2] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_3] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_4] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_5] = vf.add_const(-1.0, name='')
    event_parameters[avr_t1] = vf.add_const(0.02, name='')
    event_parameters[avr_t2] = vf.add_const(0.1, name='')
    event_parameters[avr_t3] = vf.add_const(0.1, name='')
    event_parameters[avr_t4] = vf.add_const(0.5, name='')
    event_parameters[avr_tR] = vf.add_const(0.02, name='')
    event_parameters[avr_transferFunction_a_1] = avr_t4
    event_parameters[avr_transferFunction_a_2] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction_a_end] = ((sym.heaviside(((avr_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((avr_transferFunction_a_1 ** sym.Const(2.0)) + (avr_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * avr_transferFunction_a_2) + ((sym.Const(1.0) - sym.heaviside(((avr_transferFunction_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((avr_transferFunction_a_1 ** sym.Const(2.0)) + (avr_transferFunction_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[avr_transferFunction_b_1] = avr_t3
    event_parameters[avr_transferFunction_b_2] = vf.add_const(1.0, name='')
    event_parameters[avr_transferFunction_bb_1] = avr_transferFunction_b_1
    event_parameters[avr_transferFunction_bb_2] = avr_transferFunction_b_2
    event_parameters[avr_transferFunction_d] = (avr_transferFunction_bb_1 / avr_transferFunction_a_1)
    event_parameters[avr_transferFunction_x_start_1] = (avr_Efd0Pu / avr_K)
    event_parameters[avr_transferFunction_y_start] = (avr_Efd0Pu / avr_K)
    event_parameters[avr_variableLimiter_ySimplified] = vf.add_const(0.0, name='')
    event_parameters[avr_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_nin] = vf.add_const(5.0, name='')
    event_parameters[avr_transferFunction_na] = vf.add_const(2.0, name='')
    event_parameters[avr_transferFunction_nb] = vf.add_const(2.0, name='')
    event_parameters[avr_transferFunction_nx] = vf.add_const(1.0, name='')
    event_parameters[avr_variableLimiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_variableLimiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_variableLimiter_strict] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[avr_firstOrder_y] = avr_firstOrder_y_start
    initial_equations[avr_firstOrder1_y] = (avr_firstOrder1_k * avr_UsPu)
    initial_equations[avr_transferFunction_x_scaled_1] = (avr_transferFunction_a_end * avr_transferFunction_x_start_1)
    initial_equations[avr_EfdPu] = vf.add_const(1.0, name='')
    initial_equations[avr_UOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UsPu] = vf.add_const(1.0, name='')
    initial_equations[avr_UsRefPu] = avr_UsRef0Pu
    initial_equations[avr_transferFunction_x_1] = avr_transferFunction_x_start_1
    initial_equations[avr_transferFunction_y] = avr_transferFunction_y_start
    initial_equations[avr_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_variableLimiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_y] = (((((avr_sum1_k_1 * avr_UOelPu) + (avr_sum1_k_2 * avr_UPssPu)) + (avr_sum1_k_3 * avr_UUelPu)) + (avr_sum1_k_4 * avr_UsRefPu)) + (avr_sum1_k_5 * avr_firstOrder1_y))
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

    template.comment = 'Generator AVR/exciter BBSEX1'
    return template
