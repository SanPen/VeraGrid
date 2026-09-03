# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'REGCbCS'.

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

def build_regcbcs_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'REGCbCS'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    ctrl_Id0Pu: Var = vf.add_var('ctrl.Id0Pu_' + template_name)
    ctrl_Iq0Pu: Var = vf.add_var('ctrl.Iq0Pu_' + template_name)
    ctrl_IqrMaxPu: Var = vf.add_var('ctrl.IqrMaxPu_' + template_name)
    ctrl_IqrMaxPu0_k: Var = vf.add_var('ctrl.IqrMaxPu0.k_' + template_name)
    ctrl_IqrMinPu: Var = vf.add_var('ctrl.IqrMinPu_' + template_name)
    ctrl_IqrMinPu0_k: Var = vf.add_var('ctrl.IqrMinPu0.k_' + template_name)
    ctrl_RateFlag: Var = vf.add_var('ctrl.RateFlag_' + template_name)
    ctrl_RateFlag0_k: Var = vf.add_var('ctrl.RateFlag0.k_' + template_name)
    ctrl_RrpwrNeg0_k: Var = vf.add_var('ctrl.RrpwrNeg0.k_' + template_name)
    ctrl_RrpwrPos0_k: Var = vf.add_var('ctrl.RrpwrPos0.k_' + template_name)
    ctrl_RrpwrPu: Var = vf.add_var('ctrl.RrpwrPu_' + template_name)
    ctrl_UInj0Pu: Var = vf.add_var('ctrl.UInj0Pu_' + template_name)
    ctrl_UNomFix_k: Var = vf.add_var('ctrl.UNomFix.k_' + template_name)
    ctrl_constant1_k: Var = vf.add_var('ctrl.constant1.k_' + template_name)
    ctrl_constant2_k: Var = vf.add_var('ctrl.constant2.k_' + template_name)
    ctrl_firstOrder_T: Var = vf.add_var('ctrl.firstOrder.T_' + template_name)
    ctrl_firstOrder_initType: Var = vf.add_var('ctrl.firstOrder.initType_' + template_name)
    ctrl_firstOrder_k: Var = vf.add_var('ctrl.firstOrder.k_' + template_name)
    ctrl_firstOrder_y_start: Var = vf.add_var('ctrl.firstOrder.y_start_' + template_name)
    ctrl_gain_k: Var = vf.add_var('ctrl.gain.k_' + template_name)
    ctrl_limiter_homotopyType: Var = vf.add_var('ctrl.limiter.homotopyType_' + template_name)
    ctrl_limiter_limitsAtInit: Var = vf.add_var('ctrl.limiter.limitsAtInit_' + template_name)
    ctrl_limiter_strict: Var = vf.add_var('ctrl.limiter.strict_' + template_name)
    ctrl_limiter_uMax: Var = vf.add_var('ctrl.limiter.uMax_' + template_name)
    ctrl_limiter_uMin: Var = vf.add_var('ctrl.limiter.uMin_' + template_name)
    ctrl_offDelay_tDelay: Var = vf.add_var('ctrl.offDelay.tDelay_' + template_name)
    ctrl_rateLimFirstOrderFreeze_T: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze.T_' + template_name)
    ctrl_rateLimFirstOrderFreeze_UseFreeze: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze.UseFreeze_' + template_name)
    ctrl_rateLimFirstOrderFreeze_UseRateLim: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze.UseRateLim_' + template_name)
    ctrl_rateLimFirstOrderFreeze_Y0: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze.Y0_' + template_name)
    ctrl_rateLimFirstOrderFreeze_k: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze.k_' + template_name)
    ctrl_rateLimFirstOrderFreeze1_T: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze1.T_' + template_name)
    ctrl_rateLimFirstOrderFreeze1_UseFreeze: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze1.UseFreeze_' + template_name)
    ctrl_rateLimFirstOrderFreeze1_UseRateLim: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze1.UseRateLim_' + template_name)
    ctrl_rateLimFirstOrderFreeze1_Y0: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze1.Y0_' + template_name)
    ctrl_rateLimFirstOrderFreeze1_k: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze1.k_' + template_name)
    ctrl_tFilterGC: Var = vf.add_var('ctrl.tFilterGC_' + template_name)
    ctrl_tG: Var = vf.add_var('ctrl.tG_' + template_name)
    # Declare the state variables used by the template.
    ctrl_firstOrder_y: Var = vf.add_var('ctrl.firstOrder.y_' + template_name)
    ctrl_rateLimFirstOrderFreeze_y: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze.y_' + template_name)
    ctrl_rateLimFirstOrderFreeze1_y: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze1.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_ctrl_firstOrder_y: Var = vf.add_var('$START.ctrl.firstOrder.y_' + template_name)
    START_ctrl_rateLimFirstOrderFreeze_y: Var = vf.add_var('$START.ctrl.rateLimFirstOrderFreeze.y_' + template_name)
    START_ctrl_rateLimFirstOrderFreeze1_y: Var = vf.add_var('$START.ctrl.rateLimFirstOrderFreeze1.y_' + template_name)
    cse1: Var = vf.add_var('$cse1_' + template_name)
    cse2: Var = vf.add_var('$cse2_' + template_name)
    cse3: Var = vf.add_var('$cse3_' + template_name)
    cse4: Var = vf.add_var('$cse4_' + template_name)
    ctrl_UPu: Var = vf.add_var('ctrl.UPu_' + template_name)
    ctrl_frtOn: Var = vf.add_var('ctrl.frtOn_' + template_name)
    ctrl_idCmdPu: Var = vf.add_var('ctrl.idCmdPu_' + template_name)
    ctrl_idRefPu: Var = vf.add_var('ctrl.idRefPu_' + template_name)
    ctrl_iqCmdPu: Var = vf.add_var('ctrl.iqCmdPu_' + template_name)
    ctrl_iqRefPu: Var = vf.add_var('ctrl.iqRefPu_' + template_name)
    ctrl_limiter_simplifiedExpr: Var = vf.add_var('ctrl.limiter.simplifiedExpr_' + template_name)
    ctrl_limiter_y: Var = vf.add_var('ctrl.limiter.y_' + template_name)
    ctrl_offDelay_delaySignal: Var = vf.add_var('ctrl.offDelay.delaySignal_' + template_name)
    ctrl_offDelay_tNext: Var = vf.add_var('ctrl.offDelay.tNext_' + template_name)
    ctrl_offDelay_y: Var = vf.add_var('ctrl.offDelay.y_' + template_name)
    ctrl_product_y: Var = vf.add_var('ctrl.product.y_' + template_name)
    ctrl_rateLimFirstOrderFreeze_local_freeze: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze.local_freeze_' + template_name)
    ctrl_rateLimFirstOrderFreeze1_local_freeze: Var = vf.add_var('ctrl.rateLimFirstOrderFreeze1.local_freeze_' + template_name)
    ctrl_switch_y: Var = vf.add_var('ctrl.switch.y_' + template_name)
    ctrl_switch1_y: Var = vf.add_var('ctrl.switch1.y_' + template_name)
    ctrl_switch2_y: Var = vf.add_var('ctrl.switch2.y_' + template_name)
    time: Var = vf.add_var('time_' + template_name)
    # Declare the differential variables used by the template.
    d_ctrl_firstOrder_y: Var = vf.add_diff_var('d_ctrl.firstOrder.y_' + template_name, base_var=ctrl_firstOrder_y)
    d_ctrl_rateLimFirstOrderFreeze_y: Var = vf.add_diff_var('d_ctrl.rateLimFirstOrderFreeze.y_' + template_name, base_var=ctrl_rateLimFirstOrderFreeze_y)
    d_ctrl_rateLimFirstOrderFreeze1_y: Var = vf.add_diff_var('d_ctrl.rateLimFirstOrderFreeze1.y_' + template_name, base_var=ctrl_rateLimFirstOrderFreeze1_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append(cse3)
    state_equations.append((((ctrl_firstOrder_k * ctrl_UInj0Pu) - ctrl_firstOrder_y) / ctrl_firstOrder_T))
    state_equations.append(cse1)
    state_variables: list[Var] = list()
    state_variables.append(ctrl_rateLimFirstOrderFreeze_y)
    state_variables.append(ctrl_firstOrder_y)
    state_variables.append(ctrl_rateLimFirstOrderFreeze1_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((ctrl_iqRefPu - (ctrl_gain_k * ctrl_rateLimFirstOrderFreeze_y)))
    algebraic_equations.append((ctrl_offDelay_y - ((ctrl_offDelay_delaySignal * sym.heaviside(((ctrl_offDelay_tNext - time) + sym.Const(1e-06)))) + ((sym.Const(1.0) - ctrl_offDelay_delaySignal) * sym.Const(0.0)))))
    algebraic_equations.append((ctrl_switch2_y - ((ctrl_offDelay_y * ctrl_IqrMinPu0_k) + ((sym.Const(1.0) - ctrl_offDelay_y) * ctrl_constant2_k))))
    algebraic_equations.append((cse4 - sym.max(((-ctrl_rateLimFirstOrderFreeze_y) / ctrl_rateLimFirstOrderFreeze_T), ctrl_switch2_y)))
    algebraic_equations.append((ctrl_switch1_y - ((ctrl_offDelay_y * ctrl_IqrMaxPu0_k) + ((sym.Const(1.0) - ctrl_offDelay_y) * ctrl_constant1_k))))
    algebraic_equations.append((cse3 - sym.min(cse4, ctrl_switch1_y)))
    algebraic_equations.append((ctrl_limiter_y - ((sym.heaviside(((ctrl_firstOrder_y - ctrl_limiter_uMax) - sym.Const(1e-06))) * ctrl_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((ctrl_firstOrder_y - ctrl_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((ctrl_limiter_uMin - ctrl_firstOrder_y) - sym.Const(1e-06))) * ctrl_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((ctrl_limiter_uMin - ctrl_firstOrder_y) - sym.Const(1e-06)))) * ctrl_firstOrder_y))))))
    algebraic_equations.append((ctrl_switch_y - ((ctrl_RateFlag0_k * ctrl_limiter_y) + ((sym.Const(1.0) - ctrl_RateFlag0_k) * ctrl_UNomFix_k))))
    algebraic_equations.append((ctrl_idRefPu - (ctrl_rateLimFirstOrderFreeze1_y / ctrl_switch_y)))
    algebraic_equations.append((ctrl_product_y - (ctrl_idCmdPu * ctrl_switch_y)))
    algebraic_equations.append((cse2 - sym.max((((ctrl_rateLimFirstOrderFreeze1_k * ctrl_product_y) - ctrl_rateLimFirstOrderFreeze1_y) / ctrl_rateLimFirstOrderFreeze1_T), ctrl_RrpwrNeg0_k)))
    algebraic_equations.append((cse1 - sym.min(cse2, ctrl_RrpwrPos0_k)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(ctrl_iqRefPu)
    algebraic_variables.append(ctrl_offDelay_y)
    algebraic_variables.append(ctrl_switch2_y)
    algebraic_variables.append(cse4)
    algebraic_variables.append(ctrl_switch1_y)
    algebraic_variables.append(cse3)
    algebraic_variables.append(ctrl_limiter_y)
    algebraic_variables.append(ctrl_switch_y)
    algebraic_variables.append(ctrl_idRefPu)
    algebraic_variables.append(ctrl_product_y)
    algebraic_variables.append(cse2)
    algebraic_variables.append(cse1)
    algebraic_variables.append(ctrl_offDelay_delaySignal)
    algebraic_variables.append(ctrl_offDelay_tNext)
    algebraic_variables.append(ctrl_UPu)
    algebraic_variables.append(ctrl_idCmdPu)
    algebraic_variables.append(ctrl_iqCmdPu)
    algebraic_variables.append(ctrl_frtOn)
    algebraic_variables.append(ctrl_limiter_simplifiedExpr)
    algebraic_variables.append(ctrl_rateLimFirstOrderFreeze1_local_freeze)
    algebraic_variables.append(ctrl_rateLimFirstOrderFreeze_local_freeze)
    algebraic_variables.append(START_ctrl_rateLimFirstOrderFreeze_y)
    algebraic_variables.append(START_ctrl_firstOrder_y)
    algebraic_variables.append(START_ctrl_rateLimFirstOrderFreeze1_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_ctrl_rateLimFirstOrderFreeze_y)
    differential_variables.append(d_ctrl_firstOrder_y)
    differential_variables.append(d_ctrl_rateLimFirstOrderFreeze1_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[ctrl_Id0Pu] = vf.add_const(0.8, name='')
    event_parameters[ctrl_Iq0Pu] = vf.add_const(0.0, name='')
    event_parameters[ctrl_IqrMaxPu] = vf.add_const(999.0, name='')
    event_parameters[ctrl_IqrMaxPu0_k] = ctrl_IqrMaxPu
    event_parameters[ctrl_IqrMinPu] = vf.add_const(-999.0, name='')
    event_parameters[ctrl_IqrMinPu0_k] = ctrl_IqrMinPu
    event_parameters[ctrl_RrpwrNeg0_k] = (-ctrl_RrpwrPu)
    event_parameters[ctrl_RrpwrPos0_k] = ctrl_RrpwrPu
    event_parameters[ctrl_RrpwrPu] = vf.add_const(10.0, name='')
    event_parameters[ctrl_UInj0Pu] = vf.add_const(1.0, name='')
    event_parameters[ctrl_UNomFix_k] = ctrl_UInj0Pu
    event_parameters[ctrl_constant1_k] = vf.add_const(9999.0, name='')
    event_parameters[ctrl_constant2_k] = vf.add_const(-9999.0, name='')
    event_parameters[ctrl_firstOrder_T] = ctrl_tFilterGC
    event_parameters[ctrl_firstOrder_k] = vf.add_const(1.0, name='')
    event_parameters[ctrl_firstOrder_y_start] = ctrl_UInj0Pu
    event_parameters[ctrl_gain_k] = vf.add_const(-1.0, name='')
    event_parameters[ctrl_limiter_uMax] = vf.add_const(999.0, name='')
    event_parameters[ctrl_limiter_uMin] = vf.add_const(0.01, name='')
    event_parameters[ctrl_offDelay_tDelay] = sym.max(sym.abs((sym.Const(1.0) / ctrl_IqrMaxPu)), sym.abs((sym.Const(1.0) / ctrl_IqrMinPu)))
    event_parameters[ctrl_rateLimFirstOrderFreeze_T] = ctrl_tG
    event_parameters[ctrl_rateLimFirstOrderFreeze_Y0] = ctrl_Iq0Pu
    event_parameters[ctrl_rateLimFirstOrderFreeze_k] = vf.add_const(1.0, name='')
    event_parameters[ctrl_rateLimFirstOrderFreeze1_T] = ctrl_tG
    event_parameters[ctrl_rateLimFirstOrderFreeze1_Y0] = (ctrl_Id0Pu * ctrl_UInj0Pu)
    event_parameters[ctrl_rateLimFirstOrderFreeze1_k] = vf.add_const(1.0, name='')
    event_parameters[ctrl_tFilterGC] = vf.add_const(0.02, name='')
    event_parameters[ctrl_tG] = vf.add_const(0.02, name='')
    event_parameters[ctrl_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[ctrl_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[ctrl_RateFlag] = vf.add_const(0.0, name='')
    event_parameters[ctrl_RateFlag0_k] = ctrl_RateFlag
    event_parameters[ctrl_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[ctrl_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[ctrl_rateLimFirstOrderFreeze_UseFreeze] = vf.add_const(0.0, name='')
    event_parameters[ctrl_rateLimFirstOrderFreeze_UseRateLim] = vf.add_const(1.0, name='')
    event_parameters[ctrl_rateLimFirstOrderFreeze1_UseFreeze] = vf.add_const(0.0, name='')
    event_parameters[ctrl_rateLimFirstOrderFreeze1_UseRateLim] = vf.add_const(1.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[ctrl_firstOrder_y] = START_ctrl_firstOrder_y
    initial_equations[ctrl_rateLimFirstOrderFreeze_y] = START_ctrl_rateLimFirstOrderFreeze_y
    initial_equations[ctrl_rateLimFirstOrderFreeze1_y] = START_ctrl_rateLimFirstOrderFreeze1_y
    initial_equations[ctrl_UPu] = vf.add_const(1.0, name='')
    initial_equations[ctrl_idCmdPu] = vf.add_const(0.8, name='')
    initial_equations[ctrl_idRefPu] = vf.add_const(0.8, name='')
    initial_equations[ctrl_iqCmdPu] = vf.add_const(0.0, name='')
    initial_equations[ctrl_iqRefPu] = vf.add_const(0.0, name='')
    initial_equations[ctrl_product_y] = vf.add_const(0.8, name='')
    initial_equations[ctrl_switch_y] = vf.add_const(1.0, name='')
    initial_equations[ctrl_switch1_y] = vf.add_const(9999.0, name='')
    initial_equations[ctrl_switch2_y] = vf.add_const(-9999.0, name='')
    initial_equations[ctrl_frtOn] = vf.add_const(0.0, name='')
    initial_equations[ctrl_offDelay_delaySignal] = vf.add_const(0.0, name='')
    initial_equations[ctrl_offDelay_y] = vf.add_const(0.0, name='')
    initial_equations[ctrl_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[ctrl_rateLimFirstOrderFreeze1_local_freeze] = vf.add_const(0.0, name='')
    initial_equations[ctrl_rateLimFirstOrderFreeze_local_freeze] = vf.add_const(0.0, name='')
    differential_initial_equations: dict[Var, Expr | Const] = dict()
    differential_initial_equations[d_ctrl_rateLimFirstOrderFreeze_y] = sym.min(sym.max(((-ctrl_rateLimFirstOrderFreeze_y) / ctrl_rateLimFirstOrderFreeze_T), ctrl_switch2_y), ctrl_switch1_y)
    differential_initial_equations[d_ctrl_rateLimFirstOrderFreeze1_y] = sym.min(sym.max((((ctrl_rateLimFirstOrderFreeze1_k * ctrl_product_y) - ctrl_rateLimFirstOrderFreeze1_y) / ctrl_rateLimFirstOrderFreeze1_T), ctrl_RrpwrNeg0_k), ctrl_RrpwrPos0_k)
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

    template.block.state_eqs[0] = ((sym.Const(1.0) - ctrl_rateLimFirstOrderFreeze_local_freeze) * sym.min(sym.max((((ctrl_rateLimFirstOrderFreeze_k * ctrl_iqCmdPu) - ctrl_rateLimFirstOrderFreeze_y) / ctrl_rateLimFirstOrderFreeze_T), ctrl_switch2_y), ctrl_switch1_y))
    template.block.state_eqs[2] = ((sym.Const(1.0) - ctrl_rateLimFirstOrderFreeze1_local_freeze) * sym.min(sym.max((((ctrl_rateLimFirstOrderFreeze1_k * ctrl_product_y) - ctrl_rateLimFirstOrderFreeze1_y) / ctrl_rateLimFirstOrderFreeze1_T), ctrl_RrpwrNeg0_k), ctrl_RrpwrPos0_k))
    template.block.init_eqs[ctrl_firstOrder_y] = ctrl_firstOrder_y_start
    template.block.init_eqs[ctrl_rateLimFirstOrderFreeze_y] = ctrl_rateLimFirstOrderFreeze_Y0
    template.block.init_eqs[ctrl_rateLimFirstOrderFreeze1_y] = ctrl_rateLimFirstOrderFreeze1_Y0

    template.comment = 'Generator WECC converter control REGCbCS'
    return template
