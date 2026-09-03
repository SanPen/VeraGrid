# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'IEEET1'.

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

def build_ieeet1_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'IEEET1'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    avr_Bsq: Var = vf.add_var('avr.Bsq_' + template_name)
    avr_Efd0Pu: Var = vf.add_var('avr.Efd0Pu_' + template_name)
    avr_EfdHighPu: Var = vf.add_var('avr.EfdHighPu_' + template_name)
    avr_EfdLowPu: Var = vf.add_var('avr.EfdLowPu_' + template_name)
    avr_EfdRaw0Pu: Var = vf.add_var('avr.EfdRaw0Pu_' + template_name)
    avr_EfdRawMaxPu: Var = vf.add_var('avr.EfdRawMaxPu_' + template_name)
    avr_EfdRawMinPu: Var = vf.add_var('avr.EfdRawMinPu_' + template_name)
    avr_EfdSatHighPu: Var = vf.add_var('avr.EfdSatHighPu_' + template_name)
    avr_EfdSatLowPu: Var = vf.add_var('avr.EfdSatLowPu_' + template_name)
    avr_EfdThresholdPu: Var = vf.add_var('avr.EfdThresholdPu_' + template_name)
    avr_Ka: Var = vf.add_var('avr.Ka_' + template_name)
    avr_Ke: Var = vf.add_var('avr.Ke_' + template_name)
    avr_Kf: Var = vf.add_var('avr.Kf_' + template_name)
    avr_Sq: Var = vf.add_var('avr.Sq_' + template_name)
    avr_Us0Pu: Var = vf.add_var('avr.Us0Pu_' + template_name)
    avr_UsRef0Pu: Var = vf.add_var('avr.UsRef0Pu_' + template_name)
    avr_add3_k1: Var = vf.add_var('avr.add3.k1_' + template_name)
    avr_add3_k2: Var = vf.add_var('avr.add3.k2_' + template_name)
    avr_add3_k3: Var = vf.add_var('avr.add3.k3_' + template_name)
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
    avr_integrator_initType: Var = vf.add_var('avr.integrator.initType_' + template_name)
    avr_integrator_k: Var = vf.add_var('avr.integrator.k_' + template_name)
    avr_integrator_use_reset: Var = vf.add_var('avr.integrator.use_reset_' + template_name)
    avr_integrator_use_set: Var = vf.add_var('avr.integrator.use_set_' + template_name)
    avr_integrator_y_start: Var = vf.add_var('avr.integrator.y_start_' + template_name)
    avr_limitedFirstOrder_G_k: Var = vf.add_var('avr.limitedFirstOrder.G.k_' + template_name)
    avr_limitedFirstOrder_Gk_k: Var = vf.add_var('avr.limitedFirstOrder.Gk.k_' + template_name)
    avr_limitedFirstOrder_I_initType: Var = vf.add_var('avr.limitedFirstOrder.I.initType_' + template_name)
    avr_limitedFirstOrder_I_k: Var = vf.add_var('avr.limitedFirstOrder.I.k_' + template_name)
    avr_limitedFirstOrder_I_use_reset: Var = vf.add_var('avr.limitedFirstOrder.I.use_reset_' + template_name)
    avr_limitedFirstOrder_I_use_set: Var = vf.add_var('avr.limitedFirstOrder.I.use_set_' + template_name)
    avr_limitedFirstOrder_I_y_start: Var = vf.add_var('avr.limitedFirstOrder.I.y_start_' + template_name)
    avr_limitedFirstOrder_K: Var = vf.add_var('avr.limitedFirstOrder.K_' + template_name)
    avr_limitedFirstOrder_Y0: Var = vf.add_var('avr.limitedFirstOrder.Y0_' + template_name)
    avr_limitedFirstOrder_YMax: Var = vf.add_var('avr.limitedFirstOrder.YMax_' + template_name)
    avr_limitedFirstOrder_YMin: Var = vf.add_var('avr.limitedFirstOrder.YMin_' + template_name)
    avr_limitedFirstOrder_lim_homotopyType: Var = vf.add_var('avr.limitedFirstOrder.lim.homotopyType_' + template_name)
    avr_limitedFirstOrder_lim_limitsAtInit: Var = vf.add_var('avr.limitedFirstOrder.lim.limitsAtInit_' + template_name)
    avr_limitedFirstOrder_lim_strict: Var = vf.add_var('avr.limitedFirstOrder.lim.strict_' + template_name)
    avr_limitedFirstOrder_lim_uMax: Var = vf.add_var('avr.limitedFirstOrder.lim.uMax_' + template_name)
    avr_limitedFirstOrder_lim_uMin: Var = vf.add_var('avr.limitedFirstOrder.lim.uMin_' + template_name)
    avr_limitedFirstOrder_tFilter: Var = vf.add_var('avr.limitedFirstOrder.tFilter_' + template_name)
    avr_satChar_Asq: Var = vf.add_var('avr.satChar.Asq_' + template_name)
    avr_satChar_Bsq: Var = vf.add_var('avr.satChar.Bsq_' + template_name)
    avr_satChar_Sq: Var = vf.add_var('avr.satChar.Sq_' + template_name)
    avr_satChar_UHigh: Var = vf.add_var('avr.satChar.UHigh_' + template_name)
    avr_satChar_ULow: Var = vf.add_var('avr.satChar.ULow_' + template_name)
    avr_satChar_YHigh: Var = vf.add_var('avr.satChar.YHigh_' + template_name)
    avr_satChar_YLow: Var = vf.add_var('avr.satChar.YLow_' + template_name)
    avr_sum1_k_1: Var = vf.add_var('avr.sum1.k[1]_' + template_name)
    avr_sum1_k_2: Var = vf.add_var('avr.sum1.k[2]_' + template_name)
    avr_sum1_k_3: Var = vf.add_var('avr.sum1.k[3]_' + template_name)
    avr_sum1_k_4: Var = vf.add_var('avr.sum1.k[4]_' + template_name)
    avr_sum1_k_5: Var = vf.add_var('avr.sum1.k[5]_' + template_name)
    avr_sum1_nin: Var = vf.add_var('avr.sum1.nin_' + template_name)
    avr_tA: Var = vf.add_var('avr.tA_' + template_name)
    avr_tE: Var = vf.add_var('avr.tE_' + template_name)
    avr_tF: Var = vf.add_var('avr.tF_' + template_name)
    avr_tR: Var = vf.add_var('avr.tR_' + template_name)
    # Declare the state variables used by the template.
    avr_derivative_x: Var = vf.add_var('avr.derivative.x_' + template_name)
    avr_firstOrder_y: Var = vf.add_var('avr.firstOrder.y_' + template_name)
    avr_integrator_y: Var = vf.add_var('avr.integrator.y_' + template_name)
    avr_limitedFirstOrder_I_y: Var = vf.add_var('avr.limitedFirstOrder.I.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_avr_derivative_x: Var = vf.add_var('$START.avr.derivative.x_' + template_name)
    avr_UOelPu: Var = vf.add_var('avr.UOelPu_' + template_name)
    avr_UPssPu: Var = vf.add_var('avr.UPssPu_' + template_name)
    avr_UUelPu: Var = vf.add_var('avr.UUelPu_' + template_name)
    avr_UsPu: Var = vf.add_var('avr.UsPu_' + template_name)
    avr_UsRefPu: Var = vf.add_var('avr.UsRefPu_' + template_name)
    avr_add3_y: Var = vf.add_var('avr.add3.y_' + template_name)
    avr_derivative_y: Var = vf.add_var('avr.derivative.y_' + template_name)
    avr_feedback_y: Var = vf.add_var('avr.feedback.y_' + template_name)
    avr_integrator_local_reset: Var = vf.add_var('avr.integrator.local_reset_' + template_name)
    avr_integrator_local_set: Var = vf.add_var('avr.integrator.local_set_' + template_name)
    avr_limitedFirstOrder_G_y: Var = vf.add_var('avr.limitedFirstOrder.G.y_' + template_name)
    avr_limitedFirstOrder_Gk_y: Var = vf.add_var('avr.limitedFirstOrder.Gk.y_' + template_name)
    avr_limitedFirstOrder_I_local_reset: Var = vf.add_var('avr.limitedFirstOrder.I.local_reset_' + template_name)
    avr_limitedFirstOrder_I_local_set: Var = vf.add_var('avr.limitedFirstOrder.I.local_set_' + template_name)
    avr_limitedFirstOrder_I_u: Var = vf.add_var('avr.limitedFirstOrder.I.u_' + template_name)
    avr_limitedFirstOrder_feedback_y: Var = vf.add_var('avr.limitedFirstOrder.feedback.y_' + template_name)
    avr_limitedFirstOrder_lim_simplifiedExpr: Var = vf.add_var('avr.limitedFirstOrder.lim.simplifiedExpr_' + template_name)
    avr_limitedFirstOrder_y: Var = vf.add_var('avr.limitedFirstOrder.y_' + template_name)
    avr_satChar_y: Var = vf.add_var('avr.satChar.y_' + template_name)
    avr_sum1_y: Var = vf.add_var('avr.sum1.y_' + template_name)
    # Declare the differential variables used by the template.
    d_avr_derivative_x: Var = vf.add_diff_var('d_avr.derivative.x_' + template_name, base_var=avr_derivative_x)
    d_avr_firstOrder_y: Var = vf.add_diff_var('d_avr.firstOrder.y_' + template_name, base_var=avr_firstOrder_y)
    d_avr_integrator_y: Var = vf.add_diff_var('d_avr.integrator.y_' + template_name, base_var=avr_integrator_y)
    d_avr_limitedFirstOrder_I_y: Var = vf.add_diff_var('d_avr.limitedFirstOrder.I.y_' + template_name, base_var=avr_limitedFirstOrder_I_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((avr_firstOrder_k * avr_UsPu) - avr_firstOrder_y) / avr_firstOrder_T))
    state_equations.append((avr_integrator_k * avr_add3_y))
    state_equations.append(((avr_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_derivative_zeroGain) * ((avr_integrator_y - avr_derivative_x) / avr_derivative_T))))
    state_equations.append((avr_limitedFirstOrder_I_k * avr_limitedFirstOrder_I_u))
    state_variables: list[Var] = list()
    state_variables.append(avr_firstOrder_y)
    state_variables.append(avr_integrator_y)
    state_variables.append(avr_derivative_x)
    state_variables.append(avr_limitedFirstOrder_I_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((avr_satChar_y - ((sym.heaviside(((avr_integrator_y - avr_satChar_Asq) - sym.Const(1e-06))) * (avr_satChar_Bsq * ((avr_integrator_y - avr_satChar_Asq) ** sym.Const(2.0)))) + ((sym.Const(1.0) - sym.heaviside(((avr_integrator_y - avr_satChar_Asq) - sym.Const(1e-06)))) * sym.Const(0.0)))))
    algebraic_equations.append((avr_limitedFirstOrder_y - ((sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))) * avr_limitedFirstOrder_lim_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06))) * avr_limitedFirstOrder_lim_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06)))) * avr_limitedFirstOrder_I_y))))))
    algebraic_equations.append((avr_sum1_y - ((((avr_UOelPu + avr_UPssPu) + avr_UUelPu) + (avr_sum1_k_4 * avr_UsRefPu)) + (avr_sum1_k_5 * avr_firstOrder_y))))
    algebraic_equations.append((avr_add3_y - ((avr_add3_k1 * avr_satChar_y) + ((avr_add3_k2 * avr_limitedFirstOrder_y) + (avr_add3_k3 * avr_integrator_y)))))
    algebraic_equations.append((avr_derivative_y - ((avr_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - avr_derivative_zeroGain) * ((avr_derivative_k / avr_derivative_T) * (avr_integrator_y - avr_derivative_x))))))
    algebraic_equations.append((avr_feedback_y - (avr_sum1_y - avr_derivative_y)))
    algebraic_equations.append((avr_limitedFirstOrder_Gk_y - (avr_limitedFirstOrder_Gk_k * avr_feedback_y)))
    algebraic_equations.append((avr_limitedFirstOrder_feedback_y - (avr_limitedFirstOrder_Gk_y - avr_limitedFirstOrder_y)))
    algebraic_equations.append((avr_limitedFirstOrder_G_y - (avr_limitedFirstOrder_G_k * avr_limitedFirstOrder_feedback_y)))
    algebraic_equations.append((avr_limitedFirstOrder_I_u - (((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_G_y - sym.Const(0.0)) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_I_y - avr_limitedFirstOrder_lim_uMax) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - avr_limitedFirstOrder_G_y) + sym.Const(1e-06)))) * sym.heaviside(((avr_limitedFirstOrder_lim_uMin - avr_limitedFirstOrder_I_y) - sym.Const(1e-06)))))))) * avr_limitedFirstOrder_G_y))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(avr_satChar_y)
    algebraic_variables.append(avr_limitedFirstOrder_y)
    algebraic_variables.append(avr_sum1_y)
    algebraic_variables.append(avr_add3_y)
    algebraic_variables.append(avr_derivative_y)
    algebraic_variables.append(avr_feedback_y)
    algebraic_variables.append(avr_limitedFirstOrder_Gk_y)
    algebraic_variables.append(avr_limitedFirstOrder_feedback_y)
    algebraic_variables.append(avr_limitedFirstOrder_G_y)
    algebraic_variables.append(avr_limitedFirstOrder_I_u)
    algebraic_variables.append(avr_UOelPu)
    algebraic_variables.append(avr_UPssPu)
    algebraic_variables.append(avr_UUelPu)
    algebraic_variables.append(avr_UsPu)
    algebraic_variables.append(avr_UsRefPu)
    algebraic_variables.append(avr_limitedFirstOrder_lim_simplifiedExpr)
    algebraic_variables.append(avr_limitedFirstOrder_I_local_reset)
    algebraic_variables.append(avr_limitedFirstOrder_I_local_set)
    algebraic_variables.append(avr_integrator_local_reset)
    algebraic_variables.append(avr_integrator_local_set)
    algebraic_variables.append(START_avr_derivative_x)
    differential_variables: list[Var] = list()
    differential_variables.append(d_avr_firstOrder_y)
    differential_variables.append(d_avr_integrator_y)
    differential_variables.append(d_avr_derivative_x)
    differential_variables.append(d_avr_limitedFirstOrder_I_y)
    input_variables: list[Var] = list()
    input_variables.append(avr_UOelPu)
    input_variables.append(avr_UPssPu)
    input_variables.append(avr_UUelPu)
    input_variables.append(avr_UsPu)
    input_variables.append(avr_UsRefPu)
    output_variables: list[Var] = list()
    output_variables.append(avr_integrator_y)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[avr_Bsq] = ((sym.heaviside(((avr_EfdHighPu - avr_EfdThresholdPu) - sym.Const(1e-06))) * ((avr_EfdHighPu * avr_EfdSatHighPu) / ((avr_EfdHighPu - avr_EfdThresholdPu) ** sym.Const(2.0)))) + ((sym.Const(1.0) - sym.heaviside(((avr_EfdHighPu - avr_EfdThresholdPu) - sym.Const(1e-06)))) * sym.Const(0.0)))
    event_parameters[avr_Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_EfdHighPu] = vf.add_const(3.1, name='')
    event_parameters[avr_EfdLowPu] = vf.add_const(2.3, name='')
    event_parameters[avr_EfdRaw0Pu] = ((avr_Ke * avr_Efd0Pu) + ((sym.heaviside(((avr_Efd0Pu - avr_EfdThresholdPu) - sym.Const(1e-06))) * (avr_Bsq * ((avr_Efd0Pu - avr_EfdThresholdPu) ** sym.Const(2.0)))) + ((sym.Const(1.0) - sym.heaviside(((avr_Efd0Pu - avr_EfdThresholdPu) - sym.Const(1e-06)))) * sym.Const(0.0))))
    event_parameters[avr_EfdRawMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_EfdRawMinPu] = vf.add_const(-5.0, name='')
    event_parameters[avr_EfdSatHighPu] = vf.add_const(0.33, name='')
    event_parameters[avr_EfdSatLowPu] = vf.add_const(0.1, name='')
    event_parameters[avr_EfdThresholdPu] = ((avr_EfdLowPu - (avr_EfdHighPu * avr_Sq)) / (sym.Const(1.0) - avr_Sq))
    event_parameters[avr_Ka] = vf.add_const(200.0, name='')
    event_parameters[avr_Ke] = vf.add_const(1.0, name='')
    event_parameters[avr_Kf] = vf.add_const(0.05, name='')
    event_parameters[avr_Sq] = (((sym.heaviside(((avr_EfdHighPu - sym.Const(0.0)) - sym.Const(1e-06))) * sym.heaviside(((avr_EfdSatHighPu - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.sqrt(((avr_EfdLowPu * avr_EfdSatLowPu) / (avr_EfdHighPu * avr_EfdSatHighPu)))) + ((sym.Const(1.0) - (sym.heaviside(((avr_EfdHighPu - sym.Const(0.0)) - sym.Const(1e-06))) * sym.heaviside(((avr_EfdSatHighPu - sym.Const(0.0)) - sym.Const(1e-06))))) * sym.Const(0.0)))
    event_parameters[avr_Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_UsRef0Pu] = ((sym.heaviside(((avr_Ka - sym.Const(0.0)) - sym.Const(1e-06))) * (avr_Us0Pu + (avr_EfdRaw0Pu / avr_Ka))) + ((sym.Const(1.0) - sym.heaviside(((avr_Ka - sym.Const(0.0)) - sym.Const(1e-06)))) * sym.Const(0.0)))
    event_parameters[avr_add3_k1] = vf.add_const(-1.0, name='')
    event_parameters[avr_add3_k2] = vf.add_const(1.0, name='')
    event_parameters[avr_add3_k3] = (-avr_Ke)
    event_parameters[avr_derivative_T] = avr_tF
    event_parameters[avr_derivative_k] = avr_Kf
    event_parameters[avr_derivative_x_start] = avr_Efd0Pu
    event_parameters[avr_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[avr_firstOrder_T] = avr_tR
    event_parameters[avr_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_y_start] = avr_Us0Pu
    event_parameters[avr_integrator_k] = (sym.Const(1.0) / avr_tE)
    event_parameters[avr_integrator_y_start] = avr_Efd0Pu
    event_parameters[avr_limitedFirstOrder_G_k] = (sym.Const(1.0) / avr_limitedFirstOrder_tFilter)
    event_parameters[avr_limitedFirstOrder_Gk_k] = avr_limitedFirstOrder_K
    event_parameters[avr_limitedFirstOrder_I_k] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_I_y_start] = avr_limitedFirstOrder_Y0
    event_parameters[avr_limitedFirstOrder_K] = avr_Ka
    event_parameters[avr_limitedFirstOrder_Y0] = avr_EfdRaw0Pu
    event_parameters[avr_limitedFirstOrder_YMax] = avr_EfdRawMaxPu
    event_parameters[avr_limitedFirstOrder_YMin] = avr_EfdRawMinPu
    event_parameters[avr_limitedFirstOrder_lim_uMax] = avr_limitedFirstOrder_YMax
    event_parameters[avr_limitedFirstOrder_lim_uMin] = avr_limitedFirstOrder_YMin
    event_parameters[avr_limitedFirstOrder_tFilter] = avr_tA
    event_parameters[avr_satChar_Asq] = avr_EfdThresholdPu
    event_parameters[avr_satChar_Bsq] = avr_Bsq
    event_parameters[avr_satChar_Sq] = avr_Sq
    event_parameters[avr_satChar_UHigh] = avr_EfdHighPu
    event_parameters[avr_satChar_ULow] = avr_EfdLowPu
    event_parameters[avr_satChar_YHigh] = avr_EfdSatHighPu
    event_parameters[avr_satChar_YLow] = avr_EfdSatLowPu
    event_parameters[avr_sum1_k_1] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_2] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_3] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_4] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_k_5] = vf.add_const(-1.0, name='')
    event_parameters[avr_tA] = vf.add_const(0.02, name='')
    event_parameters[avr_tE] = vf.add_const(0.5, name='')
    event_parameters[avr_tF] = vf.add_const(1.0, name='')
    event_parameters[avr_tR] = vf.add_const(0.02, name='')
    event_parameters[avr_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_firstOrder_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limitedFirstOrder_I_initType] = vf.add_const(3.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_sum1_nin] = vf.add_const(5.0, name='')
    event_parameters[avr_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(avr_derivative_k)) - sym.Const(1e-06)))
    event_parameters[avr_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_I_use_reset] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_I_use_set] = vf.add_const(0.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limitedFirstOrder_lim_strict] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[avr_derivative_x] = avr_derivative_x_start
    initial_equations[avr_firstOrder_y] = (avr_firstOrder_k * avr_UsPu)
    initial_equations[avr_integrator_y] = avr_integrator_y_start
    initial_equations[avr_limitedFirstOrder_I_y] = avr_limitedFirstOrder_I_y_start
    initial_equations[avr_UOelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UUelPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UsPu] = avr_Us0Pu
    initial_equations[avr_UsRefPu] = avr_UsRef0Pu
    initial_equations[avr_limitedFirstOrder_y] = avr_limitedFirstOrder_Y0
    initial_equations[avr_limitedFirstOrder_lim_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_I_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_limitedFirstOrder_I_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[avr_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[avr_sum1_y] = ((((avr_UOelPu + avr_UPssPu) + avr_UUelPu) + (avr_sum1_k_4 * avr_UsRefPu)) + (avr_sum1_k_5 * avr_firstOrder_y))
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

    template.comment = 'Generator AVR/exciter IEEET1'
    return template
