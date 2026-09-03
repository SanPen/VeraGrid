# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Uel1'.

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

def build_uel1_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'Uel1'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    uel_Kuc: Var = vf.add_var('uel.Kuc_' + template_name)
    uel_Kuf: Var = vf.add_var('uel.Kuf_' + template_name)
    uel_Kui: Var = vf.add_var('uel.Kui_' + template_name)
    uel_Kul: Var = vf.add_var('uel.Kul_' + template_name)
    uel_Kur: Var = vf.add_var('uel.Kur_' + template_name)
    uel_VUcMaxPu: Var = vf.add_var('uel.VUcMaxPu_' + template_name)
    uel_VUiMaxPu: Var = vf.add_var('uel.VUiMaxPu_' + template_name)
    uel_VUiMinPu: Var = vf.add_var('uel.VUiMinPu_' + template_name)
    uel_VUrMaxPu: Var = vf.add_var('uel.VUrMaxPu_' + template_name)
    uel_Vf0Pu: Var = vf.add_var('uel.Vf0Pu_' + template_name)
    uel_add1_k1_im: Var = vf.add_var('uel.add1.k1.im_' + template_name)
    uel_add1_k1_re: Var = vf.add_var('uel.add1.k1.re_' + template_name)
    uel_add1_k2_im: Var = vf.add_var('uel.add1.k2.im_' + template_name)
    uel_add1_k2_re: Var = vf.add_var('uel.add1.k2.re_' + template_name)
    uel_add1_useConjugateInput1: Var = vf.add_var('uel.add1.useConjugateInput1_' + template_name)
    uel_add1_useConjugateInput2: Var = vf.add_var('uel.add1.useConjugateInput2_' + template_name)
    uel_add3_k1: Var = vf.add_var('uel.add3.k1_' + template_name)
    uel_add3_k2: Var = vf.add_var('uel.add3.k2_' + template_name)
    uel_add3_k3: Var = vf.add_var('uel.add3.k3_' + template_name)
    uel_gain_k: Var = vf.add_var('uel.gain.k_' + template_name)
    uel_gain1_k: Var = vf.add_var('uel.gain1.k_' + template_name)
    uel_it0Pu_im: Var = vf.add_var('uel.it0Pu.im_' + template_name)
    uel_it0Pu_re: Var = vf.add_var('uel.it0Pu.re_' + template_name)
    uel_limitedPI_Ki: Var = vf.add_var('uel.limitedPI.Ki_' + template_name)
    uel_limitedPI_Kp: Var = vf.add_var('uel.limitedPI.Kp_' + template_name)
    uel_limitedPI_Tol: Var = vf.add_var('uel.limitedPI.Tol_' + template_name)
    uel_limitedPI_Y0: Var = vf.add_var('uel.limitedPI.Y0_' + template_name)
    uel_limitedPI_YMax: Var = vf.add_var('uel.limitedPI.YMax_' + template_name)
    uel_limitedPI_YMin: Var = vf.add_var('uel.limitedPI.YMin_' + template_name)
    uel_limitedPI_add_k1: Var = vf.add_var('uel.limitedPI.add.k1_' + template_name)
    uel_limitedPI_add_k2: Var = vf.add_var('uel.limitedPI.add.k2_' + template_name)
    uel_limitedPI_const_k: Var = vf.add_var('uel.limitedPI.const.k_' + template_name)
    uel_limitedPI_hysteresisMax_pre_y_start: Var = vf.add_var('uel.limitedPI.hysteresisMax.pre_y_start_' + template_name)
    uel_limitedPI_hysteresisMax_uHigh: Var = vf.add_var('uel.limitedPI.hysteresisMax.uHigh_' + template_name)
    uel_limitedPI_hysteresisMax_uLow: Var = vf.add_var('uel.limitedPI.hysteresisMax.uLow_' + template_name)
    uel_limitedPI_hysteresisMin_pre_y_start: Var = vf.add_var('uel.limitedPI.hysteresisMin.pre_y_start_' + template_name)
    uel_limitedPI_hysteresisMin_uHigh: Var = vf.add_var('uel.limitedPI.hysteresisMin.uHigh_' + template_name)
    uel_limitedPI_hysteresisMin_uLow: Var = vf.add_var('uel.limitedPI.hysteresisMin.uLow_' + template_name)
    uel_limitedPI_integrator_initType: Var = vf.add_var('uel.limitedPI.integrator.initType_' + template_name)
    uel_limitedPI_integrator_k: Var = vf.add_var('uel.limitedPI.integrator.k_' + template_name)
    uel_limitedPI_integrator_use_reset: Var = vf.add_var('uel.limitedPI.integrator.use_reset_' + template_name)
    uel_limitedPI_integrator_use_set: Var = vf.add_var('uel.limitedPI.integrator.use_set_' + template_name)
    uel_limitedPI_integrator_y_start: Var = vf.add_var('uel.limitedPI.integrator.y_start_' + template_name)
    uel_limitedPI_limiter1_homotopyType: Var = vf.add_var('uel.limitedPI.limiter1.homotopyType_' + template_name)
    uel_limitedPI_limiter1_limitsAtInit: Var = vf.add_var('uel.limitedPI.limiter1.limitsAtInit_' + template_name)
    uel_limitedPI_limiter1_strict: Var = vf.add_var('uel.limitedPI.limiter1.strict_' + template_name)
    uel_limitedPI_limiter1_uMax: Var = vf.add_var('uel.limitedPI.limiter1.uMax_' + template_name)
    uel_limitedPI_limiter1_uMin: Var = vf.add_var('uel.limitedPI.limiter1.uMin_' + template_name)
    uel_limiter_homotopyType: Var = vf.add_var('uel.limiter.homotopyType_' + template_name)
    uel_limiter_limitsAtInit: Var = vf.add_var('uel.limiter.limitsAtInit_' + template_name)
    uel_limiter_strict: Var = vf.add_var('uel.limiter.strict_' + template_name)
    uel_limiter_uMax: Var = vf.add_var('uel.limiter.uMax_' + template_name)
    uel_limiter_uMin: Var = vf.add_var('uel.limiter.uMin_' + template_name)
    uel_limiter1_homotopyType: Var = vf.add_var('uel.limiter1.homotopyType_' + template_name)
    uel_limiter1_limitsAtInit: Var = vf.add_var('uel.limiter1.limitsAtInit_' + template_name)
    uel_limiter1_strict: Var = vf.add_var('uel.limiter1.strict_' + template_name)
    uel_limiter1_uMax: Var = vf.add_var('uel.limiter1.uMax_' + template_name)
    uel_limiter1_uMin: Var = vf.add_var('uel.limiter1.uMin_' + template_name)
    uel_limiter2_homotopyType: Var = vf.add_var('uel.limiter2.homotopyType_' + template_name)
    uel_limiter2_limitsAtInit: Var = vf.add_var('uel.limiter2.limitsAtInit_' + template_name)
    uel_limiter2_strict: Var = vf.add_var('uel.limiter2.strict_' + template_name)
    uel_limiter2_uMax: Var = vf.add_var('uel.limiter2.uMax_' + template_name)
    uel_limiter2_uMin: Var = vf.add_var('uel.limiter2.uMin_' + template_name)
    uel_tU1: Var = vf.add_var('uel.tU1_' + template_name)
    uel_tU2: Var = vf.add_var('uel.tU2_' + template_name)
    uel_tU3: Var = vf.add_var('uel.tU3_' + template_name)
    uel_tU4: Var = vf.add_var('uel.tU4_' + template_name)
    uel_transferFunction_a_1: Var = vf.add_var('uel.transferFunction.a[1]_' + template_name)
    uel_transferFunction_a_2: Var = vf.add_var('uel.transferFunction.a[2]_' + template_name)
    uel_transferFunction_a_end: Var = vf.add_var('uel.transferFunction.a_end_' + template_name)
    uel_transferFunction_a_one: Var = vf.add_var('uel.transferFunction.a_one_' + template_name)
    uel_transferFunction_b_1: Var = vf.add_var('uel.transferFunction.b[1]_' + template_name)
    uel_transferFunction_b_2: Var = vf.add_var('uel.transferFunction.b[2]_' + template_name)
    uel_transferFunction_bb_1: Var = vf.add_var('uel.transferFunction.bb[1]_' + template_name)
    uel_transferFunction_bb_2: Var = vf.add_var('uel.transferFunction.bb[2]_' + template_name)
    uel_transferFunction_d: Var = vf.add_var('uel.transferFunction.d_' + template_name)
    uel_transferFunction_na: Var = vf.add_var('uel.transferFunction.na_' + template_name)
    uel_transferFunction_nb: Var = vf.add_var('uel.transferFunction.nb_' + template_name)
    uel_transferFunction_nx: Var = vf.add_var('uel.transferFunction.nx_' + template_name)
    uel_transferFunction_x_start_1: Var = vf.add_var('uel.transferFunction.x_start[1]_' + template_name)
    uel_transferFunction_y_start: Var = vf.add_var('uel.transferFunction.y_start_' + template_name)
    uel_transferFunction1_a_1: Var = vf.add_var('uel.transferFunction1.a[1]_' + template_name)
    uel_transferFunction1_a_2: Var = vf.add_var('uel.transferFunction1.a[2]_' + template_name)
    uel_transferFunction1_a_end: Var = vf.add_var('uel.transferFunction1.a_end_' + template_name)
    uel_transferFunction1_a_one: Var = vf.add_var('uel.transferFunction1.a_one_' + template_name)
    uel_transferFunction1_b_1: Var = vf.add_var('uel.transferFunction1.b[1]_' + template_name)
    uel_transferFunction1_b_2: Var = vf.add_var('uel.transferFunction1.b[2]_' + template_name)
    uel_transferFunction1_bb_1: Var = vf.add_var('uel.transferFunction1.bb[1]_' + template_name)
    uel_transferFunction1_bb_2: Var = vf.add_var('uel.transferFunction1.bb[2]_' + template_name)
    uel_transferFunction1_d: Var = vf.add_var('uel.transferFunction1.d_' + template_name)
    uel_transferFunction1_na: Var = vf.add_var('uel.transferFunction1.na_' + template_name)
    uel_transferFunction1_nb: Var = vf.add_var('uel.transferFunction1.nb_' + template_name)
    uel_transferFunction1_nx: Var = vf.add_var('uel.transferFunction1.nx_' + template_name)
    uel_transferFunction1_x_start_1: Var = vf.add_var('uel.transferFunction1.x_start[1]_' + template_name)
    uel_transferFunction1_y_start: Var = vf.add_var('uel.transferFunction1.y_start_' + template_name)
    uel_ut0Pu_im: Var = vf.add_var('uel.ut0Pu.im_' + template_name)
    uel_ut0Pu_re: Var = vf.add_var('uel.ut0Pu.re_' + template_name)
    # Declare the state variables used by the template.
    uel_limitedPI_integrator_y: Var = vf.add_var('uel.limitedPI.integrator.y_' + template_name)
    uel_transferFunction_x_scaled_1: Var = vf.add_var('uel.transferFunction.x_scaled[1]_' + template_name)
    uel_transferFunction1_x_scaled_1: Var = vf.add_var('uel.transferFunction1.x_scaled[1]_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_uel_limitedPI_hysteresisMax_y: Var = vf.add_var('$PRE.uel.limitedPI.hysteresisMax.y_' + template_name)
    PRE_uel_limitedPI_hysteresisMin_y: Var = vf.add_var('$PRE.uel.limitedPI.hysteresisMin.y_' + template_name)
    START_uel_transferFunction_x_scaled_1: Var = vf.add_var('$START.uel.transferFunction.x_scaled[1]_' + template_name)
    START_uel_transferFunction1_x_scaled_1: Var = vf.add_var('$START.uel.transferFunction1.x_scaled[1]_' + template_name)
    uel_UUelPu: Var = vf.add_var('uel.UUelPu_' + template_name)
    uel_VfPu: Var = vf.add_var('uel.VfPu_' + template_name)
    uel_add1_y_im: Var = vf.add_var('uel.add1.y.im_' + template_name)
    uel_add1_y_re: Var = vf.add_var('uel.add1.y.re_' + template_name)
    uel_add3_y: Var = vf.add_var('uel.add3.y_' + template_name)
    uel_complexToPolar_len: Var = vf.add_var('uel.complexToPolar.len_' + template_name)
    uel_complexToPolar_phi: Var = vf.add_var('uel.complexToPolar.phi_' + template_name)
    uel_complexToPolar1_len: Var = vf.add_var('uel.complexToPolar1.len_' + template_name)
    uel_complexToPolar1_phi: Var = vf.add_var('uel.complexToPolar1.phi_' + template_name)
    uel_gain_y: Var = vf.add_var('uel.gain.y_' + template_name)
    uel_gain1_y: Var = vf.add_var('uel.gain1.y_' + template_name)
    uel_itPu_im: Var = vf.add_var('uel.itPu.im_' + template_name)
    uel_itPu_re: Var = vf.add_var('uel.itPu.re_' + template_name)
    uel_limitedPI_add_y: Var = vf.add_var('uel.limitedPI.add.y_' + template_name)
    uel_limitedPI_hysteresisMax_y: Var = vf.add_var('uel.limitedPI.hysteresisMax.y_' + template_name)
    uel_limitedPI_hysteresisMin_y: Var = vf.add_var('uel.limitedPI.hysteresisMin.y_' + template_name)
    uel_limitedPI_integrator_local_reset: Var = vf.add_var('uel.limitedPI.integrator.local_reset_' + template_name)
    uel_limitedPI_integrator_local_set: Var = vf.add_var('uel.limitedPI.integrator.local_set_' + template_name)
    uel_limitedPI_limiter1_simplifiedExpr: Var = vf.add_var('uel.limitedPI.limiter1.simplifiedExpr_' + template_name)
    uel_limitedPI_switch1_u2: Var = vf.add_var('uel.limitedPI.switch1.u2_' + template_name)
    uel_limitedPI_switch1_y: Var = vf.add_var('uel.limitedPI.switch1.y_' + template_name)
    uel_limitedPI_y: Var = vf.add_var('uel.limitedPI.y_' + template_name)
    uel_limiter_simplifiedExpr: Var = vf.add_var('uel.limiter.simplifiedExpr_' + template_name)
    uel_limiter1_simplifiedExpr: Var = vf.add_var('uel.limiter1.simplifiedExpr_' + template_name)
    uel_limiter1_y: Var = vf.add_var('uel.limiter1.y_' + template_name)
    uel_limiter2_simplifiedExpr: Var = vf.add_var('uel.limiter2.simplifiedExpr_' + template_name)
    uel_limiter2_y: Var = vf.add_var('uel.limiter2.y_' + template_name)
    uel_transferFunction_x_1: Var = vf.add_var('uel.transferFunction.x[1]_' + template_name)
    uel_transferFunction_y: Var = vf.add_var('uel.transferFunction.y_' + template_name)
    uel_transferFunction1_x_1: Var = vf.add_var('uel.transferFunction1.x[1]_' + template_name)
    uel_transferFunction1_y: Var = vf.add_var('uel.transferFunction1.y_' + template_name)
    uel_utPu_im: Var = vf.add_var('uel.utPu.im_' + template_name)
    uel_utPu_re: Var = vf.add_var('uel.utPu.re_' + template_name)
    # Declare the differential variables used by the template.
    d_uel_limitedPI_integrator_y: Var = vf.add_diff_var('d_uel.limitedPI.integrator.y_' + template_name, base_var=uel_limitedPI_integrator_y)
    d_uel_transferFunction_x_scaled_1: Var = vf.add_diff_var('d_uel.transferFunction.x_scaled[1]_' + template_name, base_var=uel_transferFunction_x_scaled_1)
    d_uel_transferFunction1_x_scaled_1: Var = vf.add_diff_var('d_uel.transferFunction1.x_scaled[1]_' + template_name, base_var=uel_transferFunction1_x_scaled_1)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((uel_transferFunction_a_end * uel_limitedPI_y) - uel_transferFunction_x_scaled_1) / uel_transferFunction_a_one))
    state_equations.append((uel_limitedPI_integrator_k * uel_limitedPI_switch1_y))
    state_equations.append((((uel_transferFunction1_a_end * uel_transferFunction_y) - uel_transferFunction1_x_scaled_1) / uel_transferFunction1_a_one))
    state_variables: list[Var] = list()
    state_variables.append(uel_transferFunction_x_scaled_1)
    state_variables.append(uel_limitedPI_integrator_y)
    state_variables.append(uel_transferFunction1_x_scaled_1)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((uel_gain_y - (uel_gain_k * uel_complexToPolar1_len)))
    algebraic_equations.append((uel_limiter1_y - ((sym.heaviside(((uel_gain_y - uel_limiter1_uMax) - sym.Const(1e-06))) * uel_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((uel_gain_y - uel_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((uel_limiter1_uMin - uel_gain_y) - sym.Const(1e-06))) * uel_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((uel_limiter1_uMin - uel_gain_y) - sym.Const(1e-06)))) * uel_gain_y))))))
    algebraic_equations.append((uel_add1_y_im - ((uel_Kuc * uel_utPu_im) + (uel_add1_k2_im * uel_itPu_re))))
    algebraic_equations.append((uel_add1_y_re - ((uel_Kuc * uel_utPu_re) + uel_itPu_im)))
    algebraic_equations.append((uel_complexToPolar_len - (((uel_add1_y_re ** sym.Const(2.0)) + (uel_add1_y_im ** sym.Const(2.0))) ** sym.Const(0.5))))
    algebraic_equations.append((uel_limiter2_y - ((sym.heaviside(((uel_complexToPolar_len - uel_limiter2_uMax) - sym.Const(1e-06))) * uel_limiter2_uMax) + ((sym.Const(1.0) - sym.heaviside(((uel_complexToPolar_len - uel_limiter2_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((uel_limiter2_uMin - uel_complexToPolar_len) - sym.Const(1e-06))) * uel_limiter2_uMin) + ((sym.Const(1.0) - sym.heaviside(((uel_limiter2_uMin - uel_complexToPolar_len) - sym.Const(1e-06)))) * uel_complexToPolar_len))))))
    algebraic_equations.append((uel_gain1_y - (uel_gain1_k * uel_VfPu)))
    algebraic_equations.append((uel_add3_y - ((uel_add3_k1 * uel_limiter1_y) + ((uel_add3_k2 * uel_limiter2_y) + (uel_add3_k3 * uel_gain1_y)))))
    algebraic_equations.append((uel_limitedPI_add_y - ((uel_limitedPI_add_k1 * uel_add3_y) + (uel_limitedPI_add_k2 * uel_limitedPI_integrator_y))))
    algebraic_equations.append((uel_limitedPI_y - ((sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_limiter1_uMax) - sym.Const(1e-06))) * uel_limitedPI_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((uel_limitedPI_limiter1_uMin - uel_limitedPI_add_y) - sym.Const(1e-06))) * uel_limitedPI_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((uel_limitedPI_limiter1_uMin - uel_limitedPI_add_y) - sym.Const(1e-06)))) * uel_limitedPI_add_y))))))
    algebraic_equations.append((uel_limitedPI_hysteresisMax_y - (sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_uel_limitedPI_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((uel_limitedPI_hysteresisMax_uLow - uel_limitedPI_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((uel_limitedPI_hysteresisMin_y - (sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_uel_limitedPI_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((uel_limitedPI_hysteresisMin_uLow - uel_limitedPI_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((uel_limitedPI_switch1_u2 - (sym.Const(1.0) - ((sym.Const(1.0) - uel_limitedPI_hysteresisMax_y) * (sym.Const(1.0) - (sym.Const(1.0) - uel_limitedPI_hysteresisMin_y))))))
    algebraic_equations.append((uel_limitedPI_switch1_y - ((uel_limitedPI_switch1_u2 * uel_limitedPI_const_k) + ((sym.Const(1.0) - uel_limitedPI_switch1_u2) * uel_add3_y))))
    algebraic_equations.append((uel_complexToPolar_phi - sym.atan2(uel_add1_y_im, (uel_add1_y_re + sym.Const(2.220446049250313e-16)))))
    algebraic_equations.append((uel_transferFunction_x_1 - (uel_transferFunction_x_scaled_1 / uel_transferFunction_a_end)))
    algebraic_equations.append((uel_transferFunction_y - (((uel_transferFunction_bb_2 - uel_transferFunction_d) * uel_transferFunction_x_1) + (uel_transferFunction_d * uel_limitedPI_y))))
    algebraic_equations.append((uel_transferFunction1_x_1 - (uel_transferFunction1_x_scaled_1 / uel_transferFunction1_a_end)))
    algebraic_equations.append((uel_transferFunction1_y - (((uel_transferFunction1_bb_2 - uel_transferFunction1_d) * uel_transferFunction1_x_1) + (uel_transferFunction1_d * uel_transferFunction_y))))
    algebraic_equations.append((uel_UUelPu - ((sym.heaviside(((uel_transferFunction1_y - uel_limiter_uMax) - sym.Const(1e-06))) * uel_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((uel_transferFunction1_y - uel_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((uel_limiter_uMin - uel_transferFunction1_y) - sym.Const(1e-06))) * uel_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((uel_limiter_uMin - uel_transferFunction1_y) - sym.Const(1e-06)))) * uel_transferFunction1_y))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(uel_limiter1_y)
    algebraic_variables.append(uel_add1_y_im)
    algebraic_variables.append(uel_add1_y_re)
    algebraic_variables.append(uel_complexToPolar_len)
    algebraic_variables.append(uel_gain_y)
    algebraic_variables.append(uel_limiter2_y)
    algebraic_variables.append(uel_add3_y)
    algebraic_variables.append(uel_limitedPI_add_y)
    algebraic_variables.append(uel_limitedPI_y)
    algebraic_variables.append(uel_limitedPI_hysteresisMax_y)
    algebraic_variables.append(uel_limitedPI_hysteresisMin_y)
    algebraic_variables.append(uel_limitedPI_switch1_u2)
    algebraic_variables.append(uel_limitedPI_switch1_y)
    algebraic_variables.append(uel_complexToPolar_phi)
    algebraic_variables.append(uel_transferFunction_x_1)
    algebraic_variables.append(uel_transferFunction_y)
    algebraic_variables.append(uel_transferFunction1_x_1)
    algebraic_variables.append(uel_transferFunction1_y)
    algebraic_variables.append(uel_UUelPu)
    algebraic_variables.append(uel_VfPu)
    algebraic_variables.append(uel_itPu_im)
    algebraic_variables.append(uel_itPu_re)
    algebraic_variables.append(uel_utPu_im)
    algebraic_variables.append(uel_utPu_re)
    algebraic_variables.append(uel_limiter_simplifiedExpr)
    algebraic_variables.append(uel_limiter1_simplifiedExpr)
    algebraic_variables.append(uel_limiter2_simplifiedExpr)
    algebraic_variables.append(uel_limitedPI_limiter1_simplifiedExpr)
    algebraic_variables.append(uel_limitedPI_integrator_local_reset)
    algebraic_variables.append(uel_limitedPI_integrator_local_set)
    algebraic_variables.append(uel_gain1_y)
    algebraic_variables.append(uel_complexToPolar1_phi)
    algebraic_variables.append(uel_complexToPolar1_len)
    algebraic_variables.append(START_uel_transferFunction_x_scaled_1)
    algebraic_variables.append(START_uel_transferFunction1_x_scaled_1)
    algebraic_variables.append(PRE_uel_limitedPI_hysteresisMin_y)
    algebraic_variables.append(PRE_uel_limitedPI_hysteresisMax_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_uel_transferFunction_x_scaled_1)
    differential_variables.append(d_uel_limitedPI_integrator_y)
    differential_variables.append(d_uel_transferFunction1_x_scaled_1)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[uel_Kuc] = vf.add_const(0.0, name='')
    event_parameters[uel_Kuf] = vf.add_const(1.0, name='')
    event_parameters[uel_Kui] = vf.add_const(1.0, name='')
    event_parameters[uel_Kul] = vf.add_const(1.0, name='')
    event_parameters[uel_Kur] = vf.add_const(1.0, name='')
    event_parameters[uel_VUcMaxPu] = vf.add_const(5.0, name='')
    event_parameters[uel_VUiMaxPu] = vf.add_const(1.0, name='')
    event_parameters[uel_VUiMinPu] = vf.add_const(-1.0, name='')
    event_parameters[uel_VUrMaxPu] = vf.add_const(5.0, name='')
    event_parameters[uel_Vf0Pu] = (((((((uel_Kuc * uel_ut0Pu_re) + uel_it0Pu_im) ** sym.Const(2.0)) + (((uel_Kuc * uel_ut0Pu_im) - uel_it0Pu_re) ** sym.Const(2.0))) ** sym.Const(0.5)) - (uel_Kur * (((uel_ut0Pu_re ** sym.Const(2.0)) + (uel_ut0Pu_im ** sym.Const(2.0))) ** sym.Const(0.5)))) / uel_Kuf)
    event_parameters[uel_add1_k1_im] = vf.add_const(0.0, name='')
    event_parameters[uel_add1_k1_re] = vf.add_const(0.0, name='')
    event_parameters[uel_add1_k2_im] = vf.add_const(-1.0, name='')
    event_parameters[uel_add1_k2_re] = vf.add_const(0.0, name='')
    event_parameters[uel_add3_k1] = vf.add_const(-1.0, name='')
    event_parameters[uel_add3_k2] = vf.add_const(1.0, name='')
    event_parameters[uel_add3_k3] = vf.add_const(-1.0, name='')
    event_parameters[uel_gain_k] = uel_Kur
    event_parameters[uel_gain1_k] = uel_Kuf
    event_parameters[uel_it0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[uel_it0Pu_re] = vf.add_const(0.8, name='')
    event_parameters[uel_limitedPI_Ki] = uel_Kui
    event_parameters[uel_limitedPI_Kp] = uel_Kul
    event_parameters[uel_limitedPI_Tol] = vf.add_const(1e-05, name='')
    event_parameters[uel_limitedPI_Y0] = vf.add_const(0.0, name='')
    event_parameters[uel_limitedPI_YMax] = uel_VUiMaxPu
    event_parameters[uel_limitedPI_YMin] = uel_VUiMinPu
    event_parameters[uel_limitedPI_add_k1] = uel_limitedPI_Kp
    event_parameters[uel_limitedPI_add_k2] = vf.add_const(1.0, name='')
    event_parameters[uel_limitedPI_const_k] = vf.add_const(0.0, name='')
    event_parameters[uel_limitedPI_hysteresisMax_uHigh] = uel_limitedPI_YMax
    event_parameters[uel_limitedPI_hysteresisMax_uLow] = (uel_limitedPI_YMax + (uel_limitedPI_Tol * (uel_limitedPI_YMin - uel_limitedPI_YMax)))
    event_parameters[uel_limitedPI_hysteresisMin_uHigh] = (uel_limitedPI_YMin + (uel_limitedPI_Tol * (uel_limitedPI_YMax - uel_limitedPI_YMin)))
    event_parameters[uel_limitedPI_hysteresisMin_uLow] = uel_limitedPI_YMin
    event_parameters[uel_limitedPI_integrator_k] = uel_limitedPI_Ki
    event_parameters[uel_limitedPI_integrator_y_start] = uel_limitedPI_Y0
    event_parameters[uel_limitedPI_limiter1_uMax] = uel_limitedPI_YMax
    event_parameters[uel_limitedPI_limiter1_uMin] = uel_limitedPI_YMin
    event_parameters[uel_limiter_uMax] = uel_VUiMaxPu
    event_parameters[uel_limiter_uMin] = uel_VUiMinPu
    event_parameters[uel_limiter1_uMax] = uel_VUrMaxPu
    event_parameters[uel_limiter1_uMin] = vf.add_const(-999.0, name='')
    event_parameters[uel_limiter2_uMax] = uel_VUcMaxPu
    event_parameters[uel_limiter2_uMin] = vf.add_const(-999.0, name='')
    event_parameters[uel_tU1] = vf.add_const(1.0, name='')
    event_parameters[uel_tU2] = vf.add_const(1.0, name='')
    event_parameters[uel_tU3] = vf.add_const(1.0, name='')
    event_parameters[uel_tU4] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction_a_1] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction_a_2] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction_a_end] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction_a_one] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction_b_1] = uel_tU1
    event_parameters[uel_transferFunction_b_2] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction_bb_1] = uel_transferFunction_b_1
    event_parameters[uel_transferFunction_bb_2] = uel_transferFunction_b_2
    event_parameters[uel_transferFunction_d] = (uel_transferFunction_bb_1 / uel_transferFunction_a_one)
    event_parameters[uel_transferFunction_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[uel_transferFunction_y_start] = vf.add_const(0.0, name='')
    event_parameters[uel_transferFunction1_a_1] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction1_a_2] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction1_a_end] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction1_a_one] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction1_b_1] = uel_tU3
    event_parameters[uel_transferFunction1_b_2] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction1_bb_1] = uel_transferFunction1_b_1
    event_parameters[uel_transferFunction1_bb_2] = uel_transferFunction1_b_2
    event_parameters[uel_transferFunction1_d] = (uel_transferFunction1_bb_1 / uel_transferFunction1_a_one)
    event_parameters[uel_transferFunction1_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[uel_transferFunction1_y_start] = vf.add_const(0.0, name='')
    event_parameters[uel_ut0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[uel_ut0Pu_re] = vf.add_const(1.0, name='')
    event_parameters[uel_limitedPI_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[uel_limitedPI_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[uel_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[uel_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[uel_limiter2_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction_na] = vf.add_const(2.0, name='')
    event_parameters[uel_transferFunction_nb] = vf.add_const(2.0, name='')
    event_parameters[uel_transferFunction_nx] = vf.add_const(1.0, name='')
    event_parameters[uel_transferFunction1_na] = vf.add_const(2.0, name='')
    event_parameters[uel_transferFunction1_nb] = vf.add_const(2.0, name='')
    event_parameters[uel_transferFunction1_nx] = vf.add_const(1.0, name='')
    event_parameters[uel_add1_useConjugateInput1] = vf.add_const(0.0, name='')
    event_parameters[uel_add1_useConjugateInput2] = vf.add_const(0.0, name='')
    event_parameters[uel_limitedPI_hysteresisMax_pre_y_start] = vf.add_const(0.0, name='')
    event_parameters[uel_limitedPI_hysteresisMin_pre_y_start] = vf.add_const(1.0, name='')
    event_parameters[uel_limitedPI_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[uel_limitedPI_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[uel_limitedPI_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[uel_limitedPI_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[uel_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[uel_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[uel_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[uel_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[uel_limiter2_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[uel_limiter2_strict] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[uel_limitedPI_integrator_y] = uel_limitedPI_integrator_y_start
    initial_equations[uel_transferFunction_x_scaled_1] = (uel_transferFunction_a_end * uel_transferFunction_x_start_1)
    initial_equations[uel_transferFunction1_x_scaled_1] = (uel_transferFunction1_a_end * uel_transferFunction1_x_start_1)
    initial_equations[uel_UUelPu] = vf.add_const(0.0, name='')
    initial_equations[uel_VfPu] = uel_Vf0Pu
    initial_equations[uel_itPu_im] = vf.add_const(0.0, name='')
    initial_equations[uel_itPu_re] = vf.add_const(0.8, name='')
    initial_equations[uel_limitedPI_y] = uel_limitedPI_Y0
    initial_equations[uel_transferFunction_x_1] = uel_transferFunction_x_start_1
    initial_equations[uel_transferFunction_y] = uel_transferFunction_y_start
    initial_equations[uel_transferFunction1_x_1] = uel_transferFunction1_x_start_1
    initial_equations[uel_transferFunction1_y] = uel_transferFunction1_y_start
    initial_equations[uel_utPu_im] = vf.add_const(0.0, name='')
    initial_equations[uel_utPu_re] = vf.add_const(1.0, name='')
    initial_equations[uel_limitedPI_hysteresisMin_y] = (sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_uel_limitedPI_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((uel_limitedPI_hysteresisMin_uLow - uel_limitedPI_add_y) + sym.Const(1e-06))))))
    initial_equations[uel_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[uel_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[uel_limiter2_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[uel_limitedPI_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[uel_limitedPI_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[uel_limitedPI_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[uel_complexToPolar1_phi] = vf.add_const(0.0, name='')
    initial_equations[uel_complexToPolar1_len] = vf.add_const(1.0, name='')
    initial_equations[uel_gain_y] = (uel_gain_k * uel_complexToPolar1_len)
    initial_equations[uel_gain1_y] = (uel_gain1_k * uel_VfPu)
    initial_equations[PRE_uel_limitedPI_hysteresisMin_y] = uel_limitedPI_hysteresisMin_pre_y_start
    initial_equations[PRE_uel_limitedPI_hysteresisMax_y] = uel_limitedPI_hysteresisMax_pre_y_start
    initial_equations[uel_limitedPI_hysteresisMax_y] = (sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_uel_limitedPI_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((uel_limitedPI_add_y - uel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((uel_limitedPI_hysteresisMax_uLow - uel_limitedPI_add_y) + sym.Const(1e-06))))))
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

    template.comment = 'Generator under-excitation limiter UEL1'
    return template
