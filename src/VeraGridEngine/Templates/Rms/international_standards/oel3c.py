# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Oel3c'.

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

def build_oel3c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'Oel3c'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    oel_ITfPu: Var = vf.add_var('oel.ITfPu_' + template_name)
    oel_Input0Pu: Var = vf.add_var('oel.Input0Pu_' + template_name)
    oel_K1: Var = vf.add_var('oel.K1_' + template_name)
    oel_KOel: Var = vf.add_var('oel.KOel_' + template_name)
    oel_KScale: Var = vf.add_var('oel.KScale_' + template_name)
    oel_KpOel: Var = vf.add_var('oel.KpOel_' + template_name)
    oel_VOel1MaxPu: Var = vf.add_var('oel.VOel1MaxPu_' + template_name)
    oel_VOel1MinPu: Var = vf.add_var('oel.VOel1MinPu_' + template_name)
    oel_VOel2MaxPu: Var = vf.add_var('oel.VOel2MaxPu_' + template_name)
    oel_VOel2MinPu: Var = vf.add_var('oel.VOel2MinPu_' + template_name)
    oel_add_k1: Var = vf.add_var('oel.add.k1_' + template_name)
    oel_add_k2: Var = vf.add_var('oel.add.k2_' + template_name)
    oel_add1_k1: Var = vf.add_var('oel.add1.k1_' + template_name)
    oel_add1_k2: Var = vf.add_var('oel.add1.k2_' + template_name)
    oel_const_k: Var = vf.add_var('oel.const.k_' + template_name)
    oel_const1_k: Var = vf.add_var('oel.const1.k_' + template_name)
    oel_firstOrder_T: Var = vf.add_var('oel.firstOrder.T_' + template_name)
    oel_firstOrder_initType: Var = vf.add_var('oel.firstOrder.initType_' + template_name)
    oel_firstOrder_k: Var = vf.add_var('oel.firstOrder.k_' + template_name)
    oel_firstOrder_y_start: Var = vf.add_var('oel.firstOrder.y_start_' + template_name)
    oel_gain_k: Var = vf.add_var('oel.gain.k_' + template_name)
    oel_gain1_k: Var = vf.add_var('oel.gain1.k_' + template_name)
    oel_greaterEqualThreshold_threshold: Var = vf.add_var('oel.greaterEqualThreshold.threshold_' + template_name)
    oel_limIntegrator_initType: Var = vf.add_var('oel.limIntegrator.initType_' + template_name)
    oel_limIntegrator_k: Var = vf.add_var('oel.limIntegrator.k_' + template_name)
    oel_limIntegrator_limitsAtInit: Var = vf.add_var('oel.limIntegrator.limitsAtInit_' + template_name)
    oel_limIntegrator_outMax: Var = vf.add_var('oel.limIntegrator.outMax_' + template_name)
    oel_limIntegrator_outMin: Var = vf.add_var('oel.limIntegrator.outMin_' + template_name)
    oel_limIntegrator_strict: Var = vf.add_var('oel.limIntegrator.strict_' + template_name)
    oel_limIntegrator_use_reset: Var = vf.add_var('oel.limIntegrator.use_reset_' + template_name)
    oel_limIntegrator_use_set: Var = vf.add_var('oel.limIntegrator.use_set_' + template_name)
    oel_limIntegrator_y_start: Var = vf.add_var('oel.limIntegrator.y_start_' + template_name)
    oel_limiter_homotopyType: Var = vf.add_var('oel.limiter.homotopyType_' + template_name)
    oel_limiter_limitsAtInit: Var = vf.add_var('oel.limiter.limitsAtInit_' + template_name)
    oel_limiter_strict: Var = vf.add_var('oel.limiter.strict_' + template_name)
    oel_limiter_uMax: Var = vf.add_var('oel.limiter.uMax_' + template_name)
    oel_limiter_uMin: Var = vf.add_var('oel.limiter.uMin_' + template_name)
    oel_power_N: Var = vf.add_var('oel.power.N_' + template_name)
    oel_power_NInteger: Var = vf.add_var('oel.power.NInteger_' + template_name)
    oel_power1_N: Var = vf.add_var('oel.power1.N_' + template_name)
    oel_power1_NInteger: Var = vf.add_var('oel.power1.NInteger_' + template_name)
    oel_tF: Var = vf.add_var('oel.tF_' + template_name)
    oel_tOel: Var = vf.add_var('oel.tOel_' + template_name)
    # Declare the state variables used by the template.
    oel_firstOrder_y: Var = vf.add_var('oel.firstOrder.y_' + template_name)
    oel_limIntegrator_y: Var = vf.add_var('oel.limIntegrator.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_oel_firstOrder_y: Var = vf.add_var('$START.oel.firstOrder.y_' + template_name)
    oel_UOelPu: Var = vf.add_var('oel.UOelPu_' + template_name)
    oel_add_y: Var = vf.add_var('oel.add.y_' + template_name)
    oel_add1_y: Var = vf.add_var('oel.add1.y_' + template_name)
    oel_gain_y: Var = vf.add_var('oel.gain.y_' + template_name)
    oel_gain1_y: Var = vf.add_var('oel.gain1.y_' + template_name)
    oel_greaterEqualThreshold_y: Var = vf.add_var('oel.greaterEqualThreshold.y_' + template_name)
    oel_inputPu: Var = vf.add_var('oel.inputPu_' + template_name)
    oel_limIntegrator_local_reset: Var = vf.add_var('oel.limIntegrator.local_reset_' + template_name)
    oel_limIntegrator_local_set: Var = vf.add_var('oel.limIntegrator.local_set_' + template_name)
    oel_limiter_simplifiedExpr: Var = vf.add_var('oel.limiter.simplifiedExpr_' + template_name)
    oel_power_y: Var = vf.add_var('oel.power.y_' + template_name)
    oel_power1_y: Var = vf.add_var('oel.power1.y_' + template_name)
    oel_switch_y: Var = vf.add_var('oel.switch.y_' + template_name)
    # Declare the differential variables used by the template.
    d_oel_firstOrder_y: Var = vf.add_diff_var('d_oel.firstOrder.y_' + template_name, base_var=oel_firstOrder_y)
    d_oel_limIntegrator_y: Var = vf.add_diff_var('d_oel.limIntegrator.y_' + template_name, base_var=oel_limIntegrator_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((oel_firstOrder_k * oel_Input0Pu) - oel_firstOrder_y) / oel_firstOrder_T))
    state_equations.append((((sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_gain_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_gain_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_gain_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((oel_limIntegrator_k * oel_gain_y) - sym.Const(0.0)) - sym.Const(1e-06))))))) * sym.Const(0.0)) + ((sym.Const(1.0) - (sym.Const(1.0) - ((sym.Const(1.0) - ((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_gain_y)) - sym.Const(1e-06))))) * (sym.Const(1.0) - ((((((sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_gain_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_outMin - oel_limIntegrator_y) - sym.Const(1e-06)))) * sym.heaviside(((sym.Const(0.0) - (oel_limIntegrator_k * oel_gain_y)) - sym.Const(1e-06)))) * sym.heaviside(((oel_limIntegrator_y - oel_limIntegrator_outMax) - sym.Const(1e-06)))) * sym.heaviside((((oel_limIntegrator_k * oel_gain_y) - sym.Const(0.0)) - sym.Const(1e-06)))))))) * (oel_limIntegrator_k * oel_gain_y))))
    state_variables: list[Var] = list()
    state_variables.append(oel_firstOrder_y)
    state_variables.append(oel_limIntegrator_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((oel_power_y - (oel_firstOrder_y ** oel_power_N)))
    algebraic_equations.append((oel_greaterEqualThreshold_y - sym.heaviside(((oel_limIntegrator_y - oel_greaterEqualThreshold_threshold) + sym.Const(1e-06)))))
    algebraic_equations.append((oel_add1_y - ((oel_add1_k1 * oel_power_y) + (oel_add1_k2 * oel_power1_y))))
    algebraic_equations.append((oel_gain_y - (oel_gain_k * oel_add1_y)))
    algebraic_equations.append((oel_switch_y - ((oel_greaterEqualThreshold_y * oel_const1_k) + ((sym.Const(1.0) - oel_greaterEqualThreshold_y) * oel_gain_y))))
    algebraic_equations.append((oel_gain1_y - (oel_gain1_k * oel_switch_y)))
    algebraic_equations.append((oel_add_y - ((oel_add_k1 * oel_gain1_y) + (oel_add_k2 * oel_limIntegrator_y))))
    algebraic_equations.append((oel_UOelPu - ((sym.heaviside(((oel_add_y - oel_limiter_uMax) - sym.Const(1e-06))) * oel_limiter_uMax) + ((sym.Const(1.0) - sym.heaviside(((oel_add_y - oel_limiter_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((oel_limiter_uMin - oel_add_y) - sym.Const(1e-06))) * oel_limiter_uMin) + ((sym.Const(1.0) - sym.heaviside(((oel_limiter_uMin - oel_add_y) - sym.Const(1e-06)))) * oel_add_y))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(oel_power_y)
    algebraic_variables.append(oel_greaterEqualThreshold_y)
    algebraic_variables.append(oel_add1_y)
    algebraic_variables.append(oel_gain_y)
    algebraic_variables.append(oel_switch_y)
    algebraic_variables.append(oel_gain1_y)
    algebraic_variables.append(oel_add_y)
    algebraic_variables.append(oel_UOelPu)
    algebraic_variables.append(oel_power1_y)
    algebraic_variables.append(oel_inputPu)
    algebraic_variables.append(oel_limiter_simplifiedExpr)
    algebraic_variables.append(oel_limIntegrator_local_reset)
    algebraic_variables.append(oel_limIntegrator_local_set)
    algebraic_variables.append(START_oel_firstOrder_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_oel_firstOrder_y)
    differential_variables.append(d_oel_limIntegrator_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[oel_ITfPu] = vf.add_const(1.1, name='')
    event_parameters[oel_Input0Pu] = vf.add_const(1.0, name='')
    event_parameters[oel_K1] = vf.add_const(1.0, name='')
    event_parameters[oel_KOel] = vf.add_const(1.0, name='')
    event_parameters[oel_KScale] = vf.add_const(1.1, name='')
    event_parameters[oel_KpOel] = vf.add_const(1.0, name='')
    event_parameters[oel_VOel1MaxPu] = vf.add_const(1.0, name='')
    event_parameters[oel_VOel1MinPu] = vf.add_const(-1.0, name='')
    event_parameters[oel_VOel2MaxPu] = vf.add_const(1.0, name='')
    event_parameters[oel_VOel2MinPu] = vf.add_const(-1.0, name='')
    event_parameters[oel_add_k1] = vf.add_const(1.0, name='')
    event_parameters[oel_add_k2] = vf.add_const(1.0, name='')
    event_parameters[oel_add1_k1] = vf.add_const(-1.0, name='')
    event_parameters[oel_add1_k2] = vf.add_const(1.0, name='')
    event_parameters[oel_const_k] = oel_ITfPu
    event_parameters[oel_const1_k] = vf.add_const(0.0, name='')
    event_parameters[oel_firstOrder_T] = oel_tF
    event_parameters[oel_firstOrder_k] = oel_KScale
    event_parameters[oel_firstOrder_y_start] = (oel_KScale * oel_Input0Pu)
    event_parameters[oel_gain_k] = oel_KOel
    event_parameters[oel_gain1_k] = oel_KpOel
    event_parameters[oel_greaterEqualThreshold_threshold] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_k] = (sym.Const(1.0) / oel_tOel)
    event_parameters[oel_limIntegrator_outMax] = oel_VOel1MaxPu
    event_parameters[oel_limIntegrator_outMin] = oel_VOel1MinPu
    event_parameters[oel_limIntegrator_y_start] = vf.add_const(0.0, name='')
    event_parameters[oel_limiter_uMax] = oel_VOel2MaxPu
    event_parameters[oel_limiter_uMin] = oel_VOel2MinPu
    event_parameters[oel_power_N] = oel_K1
    event_parameters[oel_power1_N] = oel_K1
    event_parameters[oel_tF] = vf.add_const(0.02, name='')
    event_parameters[oel_tOel] = vf.add_const(1.0, name='')
    event_parameters[oel_firstOrder_initType] = vf.add_const(1.0, name='')
    event_parameters[oel_limIntegrator_initType] = vf.add_const(3.0, name='')
    event_parameters[oel_limiter_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[oel_limIntegrator_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[oel_limIntegrator_strict] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[oel_limIntegrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[oel_limiter_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[oel_limiter_strict] = vf.add_const(0.0, name='')
    event_parameters[oel_power_NInteger] = vf.add_const(1.0, name='')
    event_parameters[oel_power1_NInteger] = vf.add_const(1.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[oel_firstOrder_y] = oel_firstOrder_y_start
    initial_equations[oel_limIntegrator_y] = oel_limIntegrator_y_start
    initial_equations[oel_UOelPu] = vf.add_const(0.0, name='')
    initial_equations[oel_inputPu] = vf.add_const(1.0, name='')
    initial_equations[oel_limiter_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[oel_limIntegrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[oel_limIntegrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[oel_power1_y] = (oel_const_k ** oel_power1_N)
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

    template.comment = 'Generator over-excitation limiter OEL3C'
    return template
