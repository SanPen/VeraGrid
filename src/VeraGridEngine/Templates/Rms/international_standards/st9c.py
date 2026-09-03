# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'St9c'.

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

def build_st9c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'St9c'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    avr_Efd0Pu: Var = vf.add_var('avr.Efd0Pu_' + template_name)
    avr_Ir0Pu: Var = vf.add_var('avr.Ir0Pu_' + template_name)
    avr_Ka: Var = vf.add_var('avr.Ka_' + template_name)
    avr_Kas: Var = vf.add_var('avr.Kas_' + template_name)
    avr_Kc: Var = vf.add_var('avr.Kc_' + template_name)
    avr_Ki: Var = vf.add_var('avr.Ki_' + template_name)
    avr_Kp: Var = vf.add_var('avr.Kp_' + template_name)
    avr_Ku: Var = vf.add_var('avr.Ku_' + template_name)
    avr_PositionOel: Var = vf.add_var('avr.PositionOel_' + template_name)
    avr_PositionScl: Var = vf.add_var('avr.PositionScl_' + template_name)
    avr_PositionUel: Var = vf.add_var('avr.PositionUel_' + template_name)
    avr_Sw1: Var = vf.add_var('avr.Sw1_' + template_name)
    avr_Thetap: Var = vf.add_var('avr.Thetap_' + template_name)
    avr_UOel0Pu: Var = vf.add_var('avr.UOel0Pu_' + template_name)
    avr_USclOel0Pu: Var = vf.add_var('avr.USclOel0Pu_' + template_name)
    avr_USclUel0Pu: Var = vf.add_var('avr.USclUel0Pu_' + template_name)
    avr_UUel0Pu: Var = vf.add_var('avr.UUel0Pu_' + template_name)
    avr_Us0Pu: Var = vf.add_var('avr.Us0Pu_' + template_name)
    avr_Vb0Pu: Var = vf.add_var('avr.Vb0Pu_' + template_name)
    avr_VbMaxPu: Var = vf.add_var('avr.VbMaxPu_' + template_name)
    avr_VrMaxPu: Var = vf.add_var('avr.VrMaxPu_' + template_name)
    avr_VrMinPu: Var = vf.add_var('avr.VrMinPu_' + template_name)
    avr_XlPu: Var = vf.add_var('avr.XlPu_' + template_name)
    avr_ZaPu: Var = vf.add_var('avr.ZaPu_' + template_name)
    avr_add_k1: Var = vf.add_var('avr.add.k1_' + template_name)
    avr_add_k2: Var = vf.add_var('avr.add.k2_' + template_name)
    avr_add1_k1: Var = vf.add_var('avr.add1.k1_' + template_name)
    avr_add1_k2: Var = vf.add_var('avr.add1.k2_' + template_name)
    avr_booleanConstant_k: Var = vf.add_var('avr.booleanConstant.k_' + template_name)
    avr_const_k: Var = vf.add_var('avr.const.k_' + template_name)
    avr_const1_k: Var = vf.add_var('avr.const1.k_' + template_name)
    avr_const2_k: Var = vf.add_var('avr.const2.k_' + template_name)
    avr_derivative_T: Var = vf.add_var('avr.derivative.T_' + template_name)
    avr_derivative_initType: Var = vf.add_var('avr.derivative.initType_' + template_name)
    avr_derivative_k: Var = vf.add_var('avr.derivative.k_' + template_name)
    avr_derivative_x_start: Var = vf.add_var('avr.derivative.x_start_' + template_name)
    avr_derivative_y_start: Var = vf.add_var('avr.derivative.y_start_' + template_name)
    avr_derivative_zeroGain: Var = vf.add_var('avr.derivative.zeroGain_' + template_name)
    avr_firstOrder_T: Var = vf.add_var('avr.firstOrder.T_' + template_name)
    avr_firstOrder_initType: Var = vf.add_var('avr.firstOrder.initType_' + template_name)
    avr_firstOrder_k: Var = vf.add_var('avr.firstOrder.k_' + template_name)
    avr_firstOrder_y_start: Var = vf.add_var('avr.firstOrder.y_start_' + template_name)
    avr_firstOrder1_T: Var = vf.add_var('avr.firstOrder1.T_' + template_name)
    avr_firstOrder1_initType: Var = vf.add_var('avr.firstOrder1.initType_' + template_name)
    avr_firstOrder1_k: Var = vf.add_var('avr.firstOrder1.k_' + template_name)
    avr_firstOrder1_y_start: Var = vf.add_var('avr.firstOrder1.y_start_' + template_name)
    avr_gain_k: Var = vf.add_var('avr.gain.k_' + template_name)
    avr_gain1_k: Var = vf.add_var('avr.gain1.k_' + template_name)
    avr_gain2_k: Var = vf.add_var('avr.gain2.k_' + template_name)
    avr_gain3_k: Var = vf.add_var('avr.gain3.k_' + template_name)
    avr_integrator_initType: Var = vf.add_var('avr.integrator.initType_' + template_name)
    avr_integrator_k: Var = vf.add_var('avr.integrator.k_' + template_name)
    avr_integrator_use_reset: Var = vf.add_var('avr.integrator.use_reset_' + template_name)
    avr_integrator_use_set: Var = vf.add_var('avr.integrator.use_set_' + template_name)
    avr_integrator_y_start: Var = vf.add_var('avr.integrator.y_start_' + template_name)
    avr_it0Pu_im: Var = vf.add_var('avr.it0Pu.im_' + template_name)
    avr_it0Pu_re: Var = vf.add_var('avr.it0Pu.re_' + template_name)
    avr_limiter_homotopyType: Var = vf.add_var('avr.limiter.homotopyType_' + template_name)
    avr_limiter_limitsAtInit: Var = vf.add_var('avr.limiter.limitsAtInit_' + template_name)
    avr_limiter_strict: Var = vf.add_var('avr.limiter.strict_' + template_name)
    avr_limiter_uMax: Var = vf.add_var('avr.limiter.uMax_' + template_name)
    avr_limiter_uMin: Var = vf.add_var('avr.limiter.uMin_' + template_name)
    avr_limiter1_homotopyType: Var = vf.add_var('avr.limiter1.homotopyType_' + template_name)
    avr_limiter1_limitsAtInit: Var = vf.add_var('avr.limiter1.limitsAtInit_' + template_name)
    avr_limiter1_strict: Var = vf.add_var('avr.limiter1.strict_' + template_name)
    avr_limiter1_uMax: Var = vf.add_var('avr.limiter1.uMax_' + template_name)
    avr_limiter1_uMin: Var = vf.add_var('avr.limiter1.uMin_' + template_name)
    avr_limiter2_homotopyType: Var = vf.add_var('avr.limiter2.homotopyType_' + template_name)
    avr_limiter2_limitsAtInit: Var = vf.add_var('avr.limiter2.limitsAtInit_' + template_name)
    avr_limiter2_strict: Var = vf.add_var('avr.limiter2.strict_' + template_name)
    avr_limiter2_uMax: Var = vf.add_var('avr.limiter2.uMax_' + template_name)
    avr_limiter2_uMin: Var = vf.add_var('avr.limiter2.uMin_' + template_name)
    avr_max1_nu: Var = vf.add_var('avr.max1.nu_' + template_name)
    avr_min1_nu: Var = vf.add_var('avr.min1.nu_' + template_name)
    avr_potentialCircuit_Ki: Var = vf.add_var('avr.potentialCircuit.Ki_' + template_name)
    avr_potentialCircuit_Kp: Var = vf.add_var('avr.potentialCircuit.Kp_' + template_name)
    avr_potentialCircuit_Theta: Var = vf.add_var('avr.potentialCircuit.Theta_' + template_name)
    avr_potentialCircuit_X: Var = vf.add_var('avr.potentialCircuit.X_' + template_name)
    avr_potentialCircuit_j_im: Var = vf.add_var('avr.potentialCircuit.j.im_' + template_name)
    avr_potentialCircuit_j_re: Var = vf.add_var('avr.potentialCircuit.j.re_' + template_name)
    avr_rectifierRegulationCharacteristic_A1: Var = vf.add_var('avr.rectifierRegulationCharacteristic.A1_' + template_name)
    avr_rectifierRegulationCharacteristic_A2: Var = vf.add_var('avr.rectifierRegulationCharacteristic.A2_' + template_name)
    avr_rectifierRegulationCharacteristic_UHigh: Var = vf.add_var('avr.rectifierRegulationCharacteristic.UHigh_' + template_name)
    avr_rectifierRegulationCharacteristic_ULow: Var = vf.add_var('avr.rectifierRegulationCharacteristic.ULow_' + template_name)
    avr_sum1_k_1: Var = vf.add_var('avr.sum1.k[1]_' + template_name)
    avr_sum1_k_2: Var = vf.add_var('avr.sum1.k[2]_' + template_name)
    avr_sum1_k_3: Var = vf.add_var('avr.sum1.k[3]_' + template_name)
    avr_sum1_k_4: Var = vf.add_var('avr.sum1.k[4]_' + template_name)
    avr_sum1_k_5: Var = vf.add_var('avr.sum1.k[5]_' + template_name)
    avr_sum1_k_6: Var = vf.add_var('avr.sum1.k[6]_' + template_name)
    avr_sum1_k_7: Var = vf.add_var('avr.sum1.k[7]_' + template_name)
    avr_sum1_k_8: Var = vf.add_var('avr.sum1.k[8]_' + template_name)
    avr_sum1_nin: Var = vf.add_var('avr.sum1.nin_' + template_name)
    avr_tA: Var = vf.add_var('avr.tA_' + template_name)
    avr_tAUel: Var = vf.add_var('avr.tAUel_' + template_name)
    avr_tAs: Var = vf.add_var('avr.tAs_' + template_name)
    avr_tBd: Var = vf.add_var('avr.tBd_' + template_name)
    avr_tCd: Var = vf.add_var('avr.tCd_' + template_name)
    avr_tR: Var = vf.add_var('avr.tR_' + template_name)
    avr_ut0Pu_im: Var = vf.add_var('avr.ut0Pu.im_' + template_name)
    avr_ut0Pu_re: Var = vf.add_var('avr.ut0Pu.re_' + template_name)
    # Declare the state variables used by the template.
    avr_derivative_x: Var = vf.add_var('avr.derivative.x_' + template_name)
    avr_firstOrder_y: Var = vf.add_var('avr.firstOrder.y_' + template_name)
    avr_firstOrder1_y: Var = vf.add_var('avr.firstOrder1.y_' + template_name)
    avr_integrator_y: Var = vf.add_var('avr.integrator.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_avr_derivative_x: Var = vf.add_var('$START.avr.derivative.x_' + template_name)
    START_avr_firstOrder_y: Var = vf.add_var('$START.avr.firstOrder.y_' + template_name)
    START_avr_firstOrder1_y: Var = vf.add_var('$START.avr.firstOrder1.y_' + template_name)
    avr_EfdPu: Var = vf.add_var('avr.EfdPu_' + template_name)
    avr_IrPu: Var = vf.add_var('avr.IrPu_' + template_name)
    avr_UOelPu: Var = vf.add_var('avr.UOelPu_' + template_name)
    avr_UPssPu: Var = vf.add_var('avr.UPssPu_' + template_name)
    avr_USclOelPu: Var = vf.add_var('avr.USclOelPu_' + template_name)
    avr_USclUelPu: Var = vf.add_var('avr.USclUelPu_' + template_name)
    avr_UUelPu: Var = vf.add_var('avr.UUelPu_' + template_name)
    avr_UsPu: Var = vf.add_var('avr.UsPu_' + template_name)
    avr_UsRefPu: Var = vf.add_var('avr.UsRefPu_' + template_name)
    avr_add_y: Var = vf.add_var('avr.add.y_' + template_name)
    avr_add1_y: Var = vf.add_var('avr.add1.y_' + template_name)
    avr_division_y: Var = vf.add_var('avr.division.y_' + template_name)
    avr_feedback_y: Var = vf.add_var('avr.feedback.y_' + template_name)
    avr_gain1_y: Var = vf.add_var('avr.gain1.y_' + template_name)
    avr_gain3_y: Var = vf.add_var('avr.gain3.y_' + template_name)
    avr_integrator_local_reset: Var = vf.add_var('avr.integrator.local_reset_' + template_name)
    avr_integrator_local_set: Var = vf.add_var('avr.integrator.local_set_' + template_name)
    avr_itPu_im: Var = vf.add_var('avr.itPu.im_' + template_name)
    avr_itPu_re: Var = vf.add_var('avr.itPu.re_' + template_name)
    avr_limiter_simplifiedExpr: Var = vf.add_var('avr.limiter.simplifiedExpr_' + template_name)
    avr_limiter1_simplifiedExpr: Var = vf.add_var('avr.limiter1.simplifiedExpr_' + template_name)
    avr_limiter1_y: Var = vf.add_var('avr.limiter1.y_' + template_name)
    avr_limiter2_simplifiedExpr: Var = vf.add_var('avr.limiter2.simplifiedExpr_' + template_name)
    avr_max1_u_3: Var = vf.add_var('avr.max1.u[3]_' + template_name)
    avr_min1_u_3: Var = vf.add_var('avr.min1.u[3]_' + template_name)
    avr_min2_y: Var = vf.add_var('avr.min2.y_' + template_name)
    avr_potentialCircuit_v1_im: Var = vf.add_var('avr.potentialCircuit.v1.im_' + template_name)
    avr_potentialCircuit_v1_re: Var = vf.add_var('avr.potentialCircuit.v1.re_' + template_name)
    avr_potentialCircuit_v2_im: Var = vf.add_var('avr.potentialCircuit.v2.im_' + template_name)
    avr_potentialCircuit_v2_re: Var = vf.add_var('avr.potentialCircuit.v2.re_' + template_name)
    avr_potentialCircuit_vE: Var = vf.add_var('avr.potentialCircuit.vE_' + template_name)
    avr_product1_y: Var = vf.add_var('avr.product1.y_' + template_name)
    avr_product2_y: Var = vf.add_var('avr.product2.y_' + template_name)
    avr_realExpression_y: Var = vf.add_var('avr.realExpression.y_' + template_name)
    avr_rectifierRegulationCharacteristic_y: Var = vf.add_var('avr.rectifierRegulationCharacteristic.y_' + template_name)
    avr_sum1_u_1: Var = vf.add_var('avr.sum1.u[1]_' + template_name)
    avr_sum1_u_2: Var = vf.add_var('avr.sum1.u[2]_' + template_name)
    avr_sum1_u_6: Var = vf.add_var('avr.sum1.u[6]_' + template_name)
    avr_sum1_u_7: Var = vf.add_var('avr.sum1.u[7]_' + template_name)
    avr_sum1_u_8: Var = vf.add_var('avr.sum1.u[8]_' + template_name)
    avr_sum1_y: Var = vf.add_var('avr.sum1.y_' + template_name)
    avr_switch_y: Var = vf.add_var('avr.switch.y_' + template_name)
    avr_utPu_im: Var = vf.add_var('avr.utPu.im_' + template_name)
    avr_utPu_re: Var = vf.add_var('avr.utPu.re_' + template_name)
    # Declare the differential variables used by the template.
    d_avr_derivative_x: Var = vf.add_diff_var('d_avr.derivative.x_' + template_name, base_var=avr_derivative_x)
    d_avr_firstOrder_y: Var = vf.add_diff_var('d_avr.firstOrder.y_' + template_name, base_var=avr_firstOrder_y)
    d_avr_firstOrder1_y: Var = vf.add_diff_var('d_avr.firstOrder1.y_' + template_name, base_var=avr_firstOrder1_y)
    d_avr_integrator_y: Var = vf.add_diff_var('d_avr.integrator.y_' + template_name, base_var=avr_integrator_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((avr_firstOrder_k * avr_UsPu) - avr_firstOrder_y) / avr_firstOrder_T))
    state_equations.append(((avr_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_derivative_zeroGain) * ((avr_firstOrder_y - avr_derivative_x) / avr_derivative_T))))
    state_equations.append((((avr_firstOrder1_k * avr_min1_u_3) - avr_firstOrder1_y) / avr_firstOrder1_T))
    state_equations.append((avr_integrator_k * avr_product1_y))
    state_variables: list[Var] = list()
    state_variables.append(avr_firstOrder_y)
    state_variables.append(avr_derivative_x)
    state_variables.append(avr_firstOrder1_y)
    state_variables.append(avr_integrator_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((avr_gain3_y - (avr_gain3_k * avr_limiter1_y)))
    algebraic_equations.append((avr_add1_y - ((avr_add1_k1 * avr_gain3_y) + (avr_add1_k2 * avr_const_k))))
    algebraic_equations.append((avr_switch_y - ((avr_booleanConstant_k * avr_potentialCircuit_vE) + ((sym.Const(1.0) - avr_booleanConstant_k) * avr_const1_k))))
    algebraic_equations.append((avr_division_y - (avr_gain2_k / avr_switch_y)))
    algebraic_equations.append((avr_rectifierRegulationCharacteristic_y - ((sym.heaviside(((sym.Const(0.0) - avr_division_y) + sym.Const(1e-06))) * sym.Const(1.0)) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(0.0) - avr_division_y) + sym.Const(1e-06)))) * ((((sym.heaviside(((avr_division_y - sym.Const(0.0)) - sym.Const(1e-06))) * sym.heaviside(((avr_division_y - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.heaviside(((avr_rectifierRegulationCharacteristic_ULow - avr_division_y) + sym.Const(1e-06)))) * (sym.Const(1.0) - (avr_rectifierRegulationCharacteristic_A1 * avr_division_y))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_division_y - sym.Const(0.0)) - sym.Const(1e-06))) * sym.heaviside(((avr_division_y - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.heaviside(((avr_rectifierRegulationCharacteristic_ULow - avr_division_y) + sym.Const(1e-06))))) * ((((sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06))) * sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06)))) * sym.heaviside(((avr_rectifierRegulationCharacteristic_UHigh - avr_division_y) - sym.Const(1e-06)))) * sym.sqrt((avr_rectifierRegulationCharacteristic_UHigh - (avr_division_y ** sym.Const(2.0))))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06))) * sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_ULow) - sym.Const(1e-06)))) * sym.heaviside(((avr_rectifierRegulationCharacteristic_UHigh - avr_division_y) - sym.Const(1e-06))))) * ((((sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))) * sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - avr_division_y) + sym.Const(1e-06)))) * (avr_rectifierRegulationCharacteristic_A2 * (sym.Const(1.0) - avr_division_y))) + ((sym.Const(1.0) - ((sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))) * sym.heaviside(((avr_division_y - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.heaviside(((sym.Const(1.0) - avr_division_y) + sym.Const(1e-06))))) * sym.Const(0.0)))))))))))
    algebraic_equations.append((avr_product2_y - (avr_rectifierRegulationCharacteristic_y * avr_switch_y)))
    algebraic_equations.append((avr_min2_y - ((avr_const2_k * sym.heaviside((avr_product2_y - avr_const2_k))) + (avr_product2_y * (sym.Const(1) - sym.heaviside((avr_product2_y - avr_const2_k)))))))
    algebraic_equations.append((avr_EfdPu - (avr_min2_y * avr_firstOrder1_y)))
    algebraic_equations.append((avr_sum1_u_2 - ((avr_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_derivative_zeroGain) * ((avr_derivative_k / avr_derivative_T) * (avr_firstOrder_y - avr_derivative_x))))))
    algebraic_equations.append((avr_sum1_u_1 - ((sym.heaviside(((avr_sum1_u_2 - avr_limiter2_uMax) - sym.Const(1e-06))) * avr_limiter2_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_sum1_u_2 - avr_limiter2_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limiter2_uMin - avr_sum1_u_2) - sym.Const(1e-06))) * avr_limiter2_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limiter2_uMin - avr_sum1_u_2) - sym.Const(1e-06)))) * avr_sum1_u_2))))))
    algebraic_equations.append((avr_sum1_y - ((((((avr_UsRefPu - avr_firstOrder_y) + avr_UOelPu) + avr_UPssPu) + avr_USclOelPu) + avr_USclUelPu) + avr_UUelPu)))
    algebraic_equations.append((avr_max1_u_3 - (avr_gain_k * avr_sum1_y)))
    algebraic_equations.append((avr_add_y - ((avr_add_k1 * avr_max1_u_3) + (avr_add_k2 * avr_integrator_y))))
    algebraic_equations.append((avr_min1_u_3 - ((sym.heaviside(((avr_add_y - avr_limiter_uMax) - sym.Const(1e-06))) * avr_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_add_y - avr_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limiter_uMin - avr_add_y) - sym.Const(1e-06))) * avr_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limiter_uMin - avr_add_y) - sym.Const(1e-06)))) * avr_add_y))))))
    algebraic_equations.append((avr_feedback_y - (avr_min1_u_3 - avr_integrator_y)))
    algebraic_equations.append((avr_product1_y - (avr_feedback_y * avr_add1_y)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(avr_gain3_y)
    algebraic_variables.append(avr_add1_y)
    algebraic_variables.append(avr_switch_y)
    algebraic_variables.append(avr_division_y)
    algebraic_variables.append(avr_rectifierRegulationCharacteristic_y)
    algebraic_variables.append(avr_product2_y)
    algebraic_variables.append(avr_min2_y)
    algebraic_variables.append(avr_EfdPu)
    algebraic_variables.append(avr_sum1_u_2)
    algebraic_variables.append(avr_sum1_u_1)
    algebraic_variables.append(avr_sum1_y)
    algebraic_variables.append(avr_max1_u_3)
    algebraic_variables.append(avr_add_y)
    algebraic_variables.append(avr_min1_u_3)
    algebraic_variables.append(avr_feedback_y)
    algebraic_variables.append(avr_product1_y)
    algebraic_variables.append(avr_limiter1_y)
    algebraic_variables.append(avr_potentialCircuit_vE)
    algebraic_variables.append(avr_IrPu)
    algebraic_variables.append(avr_UOelPu)
    algebraic_variables.append(avr_UPssPu)
    algebraic_variables.append(avr_USclOelPu)
    algebraic_variables.append(avr_USclUelPu)
    algebraic_variables.append(avr_UUelPu)
    algebraic_variables.append(avr_UsPu)
    algebraic_variables.append(avr_UsRefPu)
    algebraic_variables.append(avr_itPu_im)
    algebraic_variables.append(avr_itPu_re)
    algebraic_variables.append(avr_utPu_im)
    algebraic_variables.append(avr_utPu_re)
    algebraic_variables.append(avr_limiter_simplifiedExpr)
    algebraic_variables.append(avr_integrator_local_reset)
    algebraic_variables.append(avr_integrator_local_set)
    algebraic_variables.append(avr_limiter2_simplifiedExpr)
    algebraic_variables.append(avr_limiter1_simplifiedExpr)
    algebraic_variables.append(START_avr_firstOrder_y)
    algebraic_variables.append(START_avr_firstOrder1_y)
    algebraic_variables.append(START_avr_derivative_x)
    algebraic_variables.append(avr_potentialCircuit_v2_re)
    algebraic_variables.append(avr_potentialCircuit_v2_im)
    algebraic_variables.append(avr_potentialCircuit_v1_re)
    algebraic_variables.append(avr_potentialCircuit_v1_im)
    algebraic_variables.append(avr_gain1_y)
    algebraic_variables.append(avr_sum1_u_6)
    algebraic_variables.append(avr_sum1_u_7)
    algebraic_variables.append(avr_sum1_u_8)
    algebraic_variables.append(avr_realExpression_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_avr_firstOrder_y)
    differential_variables.append(d_avr_derivative_x)
    differential_variables.append(d_avr_firstOrder1_y)
    differential_variables.append(d_avr_integrator_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[avr_Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Ir0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Ka] = vf.add_const(200.0, name='')
    event_parameters[avr_Kas] = vf.add_const(1.0, name='')
    event_parameters[avr_Kc] = vf.add_const(0.0, name='')
    event_parameters[avr_Ki] = vf.add_const(0.0, name='')
    event_parameters[avr_Kp] = vf.add_const(1.0, name='')
    event_parameters[avr_Ku] = vf.add_const(0.0, name='')
    event_parameters[avr_Thetap] = vf.add_const(0.0, name='')
    event_parameters[avr_UOel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_USclOel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_USclUel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_UUel0Pu] = vf.add_const(0.0, name='')
    event_parameters[avr_Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_Vb0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_VbMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VrMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_VrMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_XlPu] = vf.add_const(0.0, name='')
    event_parameters[avr_ZaPu] = vf.add_const(0.0, name='')
    event_parameters[avr_add_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_add_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_add1_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_add1_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_const_k] = (sym.Const(1.0) / avr_tA)
    event_parameters[avr_const1_k] = avr_Kp
    event_parameters[avr_const2_k] = avr_VbMaxPu
    event_parameters[avr_derivative_T] = avr_tBd
    event_parameters[avr_derivative_k] = avr_tCd
    event_parameters[avr_derivative_x_start] = avr_Us0Pu
    event_parameters[avr_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[avr_firstOrder_T] = avr_tR
    event_parameters[avr_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_y_start] = avr_Us0Pu
    event_parameters[avr_firstOrder1_T] = avr_tAs
    event_parameters[avr_firstOrder1_k] = avr_Kas
    event_parameters[avr_firstOrder1_y_start] = (avr_Efd0Pu / avr_Vb0Pu)
    event_parameters[avr_gain_k] = avr_Ka
    event_parameters[avr_gain1_k] = avr_Ku
    event_parameters[avr_gain2_k] = avr_Kc
    event_parameters[avr_gain3_k] = ((sym.Const(1.0) / avr_tAUel) + (sym.Const(-1.0) / avr_tA))
    event_parameters[avr_integrator_k] = vf.add_const(1.0, name='')
    event_parameters[avr_integrator_y_start] = (avr_Efd0Pu / (avr_Vb0Pu * avr_Kas))
    event_parameters[avr_it0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[avr_it0Pu_re] = vf.add_const(0.8, name='')
    event_parameters[avr_limiter_uMax] = avr_VrMaxPu
    event_parameters[avr_limiter_uMin] = avr_VrMinPu
    event_parameters[avr_limiter1_uMax] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter1_uMin] = vf.add_const(0.0, name='')
    event_parameters[avr_limiter2_uMax] = avr_ZaPu
    event_parameters[avr_limiter2_uMin] = (-avr_limiter2_uMax)
    event_parameters[avr_potentialCircuit_Ki] = avr_Ki
    event_parameters[avr_potentialCircuit_Kp] = avr_Kp
    event_parameters[avr_potentialCircuit_Theta] = avr_Thetap
    event_parameters[avr_potentialCircuit_X] = avr_XlPu
    event_parameters[avr_rectifierRegulationCharacteristic_A1] = (((sym.heaviside(((avr_rectifierRegulationCharacteristic_ULow - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - avr_rectifierRegulationCharacteristic_ULow) + sym.Const(1e-06)))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.heaviside(((avr_rectifierRegulationCharacteristic_ULow - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - avr_rectifierRegulationCharacteristic_ULow) + sym.Const(1e-06))))) * ((sym.Const(1.0) - sym.sqrt((avr_rectifierRegulationCharacteristic_UHigh - (avr_rectifierRegulationCharacteristic_ULow ** sym.Const(2.0))))) / avr_rectifierRegulationCharacteristic_ULow)))
    event_parameters[avr_rectifierRegulationCharacteristic_A2] = (((sym.heaviside(((avr_rectifierRegulationCharacteristic_UHigh - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06)))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.heaviside(((avr_rectifierRegulationCharacteristic_UHigh - sym.Const(1.0)) + sym.Const(1e-06))) * sym.heaviside(((sym.Const(1.0) - avr_rectifierRegulationCharacteristic_UHigh) + sym.Const(1e-06))))) * sym.sqrt((avr_rectifierRegulationCharacteristic_UHigh / (sym.Const(1.0) - avr_rectifierRegulationCharacteristic_UHigh)))))
    event_parameters[avr_rectifierRegulationCharacteristic_UHigh] = vf.add_const(0.75, name='')
    event_parameters[avr_rectifierRegulationCharacteristic_ULow] = vf.add_const(0.4330127018922193, name='')
    event_parameters[avr_sum1_k_1] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_2] = vf.add_const(-1.0, name='')
    event_parameters[avr_sum1_k_3] = vf.add_const(-1.0, name='')
    event_parameters[avr_sum1_k_4] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_5] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_6] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_7] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_8] = vf.add_const(-1.0, name='')
    event_parameters[avr_tA] = vf.add_const(0.02, name='')
    event_parameters[avr_tAUel] = vf.add_const(0.02, name='')
    event_parameters[avr_tAs] = vf.add_const(0.02, name='')
    event_parameters[avr_tBd] = vf.add_const(0.02, name='')
    event_parameters[avr_tCd] = vf.add_const(0.02, name='')
    event_parameters[avr_tR] = vf.add_const(0.02, name='')
    event_parameters[avr_ut0Pu_im] = vf.add_const(0.0, name='')
    event_parameters[avr_ut0Pu_re] = vf.add_const(1.0, name='')
    event_parameters[avr_PositionOel] = vf.add_const(0.0, name='')
    event_parameters[avr_PositionScl] = vf.add_const(0.0, name='')
    event_parameters[avr_PositionUel] = vf.add_const(0.0, name='')
    event_parameters[avr_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder1_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter2_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_max1_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_min1_nu] = vf.add_const(3.0, name='')
    event_parameters[avr_sum1_nin] = vf.add_const(8.0, name='')
    event_parameters[avr_Sw1] = vf.add_const(0.0, name='')
    event_parameters[avr_booleanConstant_k] = avr_Sw1
    event_parameters[avr_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(avr_derivative_k)) - sym.Const(1e-06)))
    event_parameters[avr_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter1_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_limiter2_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limiter2_strict] = vf.add_const(0.0, name='')
    event_parameters[avr_potentialCircuit_j_im] = vf.add_const(1.0, name='')
    event_parameters[avr_potentialCircuit_j_re] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[avr_derivative_x] = avr_derivative_x_start
    initial_equations[avr_firstOrder_y] = (avr_firstOrder_k * avr_UsPu)
    initial_equations[avr_firstOrder1_y] = avr_firstOrder1_y_start
    initial_equations[avr_integrator_y] = avr_integrator_y_start
    initial_equations[avr_EfdPu] = vf.add_const(1.0, name='')
    initial_equations[avr_IrPu] = vf.add_const(1.0, name='')
    initial_equations[avr_UOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[avr_USclOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_USclUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UsPu] = vf.add_const(1.0, name='')
    initial_equations[avr_UsRefPu] = vf.add_const(1.0, name='')
    initial_equations[avr_division_y] = vf.add_const(0.0, name='')
    initial_equations[avr_gain3_y] = vf.add_const(0.0, name='')
    initial_equations[avr_itPu_im] = vf.add_const(0.0, name='')
    initial_equations[avr_itPu_re] = vf.add_const(0.8, name='')
    initial_equations[avr_switch_y] = vf.add_const(1.0, name='')
    initial_equations[avr_utPu_im] = vf.add_const(0.0, name='')
    initial_equations[avr_utPu_re] = vf.add_const(1.0, name='')
    initial_equations[avr_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_limiter2_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_limiter1_y] = ((sym.heaviside(((sym.Const(0.0) - avr_limiter1_uMax) - sym.Const(1e-06))) * avr_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((sym.Const(0.0) - avr_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limiter1_uMin - sym.Const(0.0)) - sym.Const(1e-06))) * avr_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limiter1_uMin - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.Const(0.0)))))
    initial_equations[avr_potentialCircuit_v2_re] = (sym.Const(0.8) * (avr_potentialCircuit_Ki + (avr_potentialCircuit_X * (avr_potentialCircuit_Kp * sym.cos(avr_potentialCircuit_Theta)))))
    initial_equations[avr_potentialCircuit_v2_im] = (sym.Const(0.8) * (avr_potentialCircuit_X * (avr_potentialCircuit_Kp * sym.sin(avr_potentialCircuit_Theta))))
    initial_equations[avr_potentialCircuit_v1_re] = (avr_potentialCircuit_Kp * sym.cos(avr_potentialCircuit_Theta))
    initial_equations[avr_potentialCircuit_v1_im] = (avr_potentialCircuit_Kp * sym.sin(avr_potentialCircuit_Theta))
    initial_equations[avr_potentialCircuit_vE] = ((((avr_potentialCircuit_v1_re - avr_potentialCircuit_v2_im) ** sym.Const(2.0)) + ((avr_potentialCircuit_v1_im + avr_potentialCircuit_v2_re) ** sym.Const(2.0))) ** sym.Const(0.5))
    initial_equations[avr_gain1_y] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_6] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_7] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_u_8] = vf.add_const(0.0, name='')
    initial_equations[avr_realExpression_y] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_y] = ((((((avr_UsRefPu - avr_firstOrder_y) + avr_UOelPu) + avr_UPssPu) + avr_USclOelPu) + avr_USclUelPu) + avr_UUelPu)
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

    template.comment = 'Generator AVR/exciter IEEE ST9C'
    return template
