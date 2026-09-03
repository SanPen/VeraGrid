# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'Oel4c'.

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

def build_oel4c_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'Oel4c'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    oel_Ki: Var = vf.add_var('oel.Ki_' + template_name)
    oel_Kp: Var = vf.add_var('oel.Kp_' + template_name)
    oel_QGen0Pu: Var = vf.add_var('oel.QGen0Pu_' + template_name)
    oel_VMinPu: Var = vf.add_var('oel.VMinPu_' + template_name)
    oel_const_k: Var = vf.add_var('oel.const.k_' + template_name)
    oel_lessThreshold_threshold: Var = vf.add_var('oel.lessThreshold.threshold_' + template_name)
    oel_lessThreshold1_threshold: Var = vf.add_var('oel.lessThreshold1.threshold_' + template_name)
    oel_limitedPI_Ki: Var = vf.add_var('oel.limitedPI.Ki_' + template_name)
    oel_limitedPI_Kp: Var = vf.add_var('oel.limitedPI.Kp_' + template_name)
    oel_limitedPI_Tol: Var = vf.add_var('oel.limitedPI.Tol_' + template_name)
    oel_limitedPI_Y0: Var = vf.add_var('oel.limitedPI.Y0_' + template_name)
    oel_limitedPI_YMax: Var = vf.add_var('oel.limitedPI.YMax_' + template_name)
    oel_limitedPI_YMin: Var = vf.add_var('oel.limitedPI.YMin_' + template_name)
    oel_limitedPI_add_k1: Var = vf.add_var('oel.limitedPI.add.k1_' + template_name)
    oel_limitedPI_add_k2: Var = vf.add_var('oel.limitedPI.add.k2_' + template_name)
    oel_limitedPI_const_k: Var = vf.add_var('oel.limitedPI.const.k_' + template_name)
    oel_limitedPI_hysteresisMax_pre_y_start: Var = vf.add_var('oel.limitedPI.hysteresisMax.pre_y_start_' + template_name)
    oel_limitedPI_hysteresisMax_uHigh: Var = vf.add_var('oel.limitedPI.hysteresisMax.uHigh_' + template_name)
    oel_limitedPI_hysteresisMax_uLow: Var = vf.add_var('oel.limitedPI.hysteresisMax.uLow_' + template_name)
    oel_limitedPI_hysteresisMin_pre_y_start: Var = vf.add_var('oel.limitedPI.hysteresisMin.pre_y_start_' + template_name)
    oel_limitedPI_hysteresisMin_uHigh: Var = vf.add_var('oel.limitedPI.hysteresisMin.uHigh_' + template_name)
    oel_limitedPI_hysteresisMin_uLow: Var = vf.add_var('oel.limitedPI.hysteresisMin.uLow_' + template_name)
    oel_limitedPI_integrator_initType: Var = vf.add_var('oel.limitedPI.integrator.initType_' + template_name)
    oel_limitedPI_integrator_k: Var = vf.add_var('oel.limitedPI.integrator.k_' + template_name)
    oel_limitedPI_integrator_use_reset: Var = vf.add_var('oel.limitedPI.integrator.use_reset_' + template_name)
    oel_limitedPI_integrator_use_set: Var = vf.add_var('oel.limitedPI.integrator.use_set_' + template_name)
    oel_limitedPI_integrator_y_start: Var = vf.add_var('oel.limitedPI.integrator.y_start_' + template_name)
    oel_limitedPI_limiter1_homotopyType: Var = vf.add_var('oel.limitedPI.limiter1.homotopyType_' + template_name)
    oel_limitedPI_limiter1_limitsAtInit: Var = vf.add_var('oel.limitedPI.limiter1.limitsAtInit_' + template_name)
    oel_limitedPI_limiter1_strict: Var = vf.add_var('oel.limitedPI.limiter1.strict_' + template_name)
    oel_limitedPI_limiter1_uMax: Var = vf.add_var('oel.limitedPI.limiter1.uMax_' + template_name)
    oel_limitedPI_limiter1_uMin: Var = vf.add_var('oel.limitedPI.limiter1.uMin_' + template_name)
    oel_tDelay: Var = vf.add_var('oel.tDelay_' + template_name)
    # Declare the state variables used by the template.
    oel_limitedPI_integrator_y: Var = vf.add_var('oel.limitedPI.integrator.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    PRE_oel_limitedPI_hysteresisMax_y: Var = vf.add_var('$PRE.oel.limitedPI.hysteresisMax.y_' + template_name)
    PRE_oel_limitedPI_hysteresisMin_y: Var = vf.add_var('$PRE.oel.limitedPI.hysteresisMin.y_' + template_name)
    PRE_oel_lessThreshold_y: Var = vf.add_var('$PRE.oel.lessThreshold.y_' + template_name)
    PRE_oel_timer_entryTime: Var = vf.add_var('$PRE.oel.timer.entryTime_' + template_name)
    whenCondition1: Var = vf.add_var('$whenCondition1_' + template_name)
    oel_QGenPu: Var = vf.add_var('oel.QGenPu_' + template_name)
    oel_QRefPu: Var = vf.add_var('oel.QRefPu_' + template_name)
    oel_UOelPu: Var = vf.add_var('oel.UOelPu_' + template_name)
    oel_feedback1_y: Var = vf.add_var('oel.feedback1.y_' + template_name)
    oel_lessThreshold_y: Var = vf.add_var('oel.lessThreshold.y_' + template_name)
    oel_lessThreshold1_y: Var = vf.add_var('oel.lessThreshold1.y_' + template_name)
    oel_limitedPI_add_y: Var = vf.add_var('oel.limitedPI.add.y_' + template_name)
    oel_limitedPI_hysteresisMax_y: Var = vf.add_var('oel.limitedPI.hysteresisMax.y_' + template_name)
    oel_limitedPI_hysteresisMin_y: Var = vf.add_var('oel.limitedPI.hysteresisMin.y_' + template_name)
    oel_limitedPI_integrator_local_reset: Var = vf.add_var('oel.limitedPI.integrator.local_reset_' + template_name)
    oel_limitedPI_integrator_local_set: Var = vf.add_var('oel.limitedPI.integrator.local_set_' + template_name)
    oel_limitedPI_limiter1_simplifiedExpr: Var = vf.add_var('oel.limitedPI.limiter1.simplifiedExpr_' + template_name)
    oel_limitedPI_switch1_u2: Var = vf.add_var('oel.limitedPI.switch1.u2_' + template_name)
    oel_limitedPI_switch1_y: Var = vf.add_var('oel.limitedPI.switch1.y_' + template_name)
    oel_switch_y: Var = vf.add_var('oel.switch.y_' + template_name)
    oel_timer_entryTime: Var = vf.add_var('oel.timer.entryTime_' + template_name)
    oel_timer_y: Var = vf.add_var('oel.timer.y_' + template_name)
    time: Var = vf.add_var('time_' + template_name)
    # Declare the differential variables used by the template.
    d_oel_limitedPI_integrator_y: Var = vf.add_diff_var('d_oel.limitedPI.integrator.y_' + template_name, base_var=oel_limitedPI_integrator_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((oel_limitedPI_integrator_k * oel_limitedPI_switch1_y))
    state_variables: list[Var] = list()
    state_variables.append(oel_limitedPI_integrator_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((oel_feedback1_y - (oel_QRefPu - oel_QGenPu)))
    algebraic_equations.append((whenCondition1 - sym.heaviside(((oel_lessThreshold_threshold - oel_feedback1_y) - sym.Const(1e-06)))))
    algebraic_equations.append((oel_lessThreshold_y - whenCondition1))
    algebraic_equations.append((oel_timer_entryTime - ((oel_lessThreshold_y * (((sym.Const(1.0) - PRE_oel_lessThreshold_y) * time) + (PRE_oel_lessThreshold_y * PRE_oel_timer_entryTime))) + ((sym.Const(1.0) - oel_lessThreshold_y) * PRE_oel_timer_entryTime))))
    algebraic_equations.append((oel_timer_y - ((oel_lessThreshold_y * (time - oel_timer_entryTime)) + ((sym.Const(1.0) - oel_lessThreshold_y) * sym.Const(0.0)))))
    algebraic_equations.append((oel_lessThreshold1_y - sym.heaviside(((oel_lessThreshold1_threshold - oel_timer_y) + sym.Const(1e-06)))))
    algebraic_equations.append((oel_switch_y - ((oel_lessThreshold1_y * sym.Const(0.0)) + ((sym.Const(1.0) - oel_lessThreshold1_y) * oel_feedback1_y))))
    algebraic_equations.append((oel_limitedPI_add_y - ((oel_limitedPI_add_k1 * oel_switch_y) + (oel_limitedPI_add_k2 * oel_limitedPI_integrator_y))))
    algebraic_equations.append((oel_UOelPu - ((sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_limiter1_uMax) - sym.Const(1e-06))) * oel_limitedPI_limiter1_uMax) + ((sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_limiter1_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((oel_limitedPI_limiter1_uMin - oel_limitedPI_add_y) - sym.Const(1e-06))) * oel_limitedPI_limiter1_uMin) + ((sym.Const(1.0) - sym.heaviside(((oel_limitedPI_limiter1_uMin - oel_limitedPI_add_y) - sym.Const(1e-06)))) * oel_limitedPI_add_y))))))
    algebraic_equations.append((oel_limitedPI_hysteresisMax_y - (sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_hysteresisMax_uLow - oel_limitedPI_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((oel_limitedPI_hysteresisMin_y - (sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_hysteresisMin_uLow - oel_limitedPI_add_y) + sym.Const(1e-06))))))))
    algebraic_equations.append((oel_limitedPI_switch1_u2 - (sym.Const(1.0) - ((sym.Const(1.0) - oel_limitedPI_hysteresisMax_y) * (sym.Const(1.0) - (sym.Const(1.0) - oel_limitedPI_hysteresisMin_y))))))
    algebraic_equations.append((oel_limitedPI_switch1_y - ((oel_limitedPI_switch1_u2 * oel_limitedPI_const_k) + ((sym.Const(1.0) - oel_limitedPI_switch1_u2) * oel_switch_y))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(whenCondition1)
    algebraic_variables.append(oel_timer_y)
    algebraic_variables.append(oel_lessThreshold1_y)
    algebraic_variables.append(oel_switch_y)
    algebraic_variables.append(oel_limitedPI_add_y)
    algebraic_variables.append(oel_UOelPu)
    algebraic_variables.append(oel_limitedPI_hysteresisMax_y)
    algebraic_variables.append(oel_limitedPI_hysteresisMin_y)
    algebraic_variables.append(oel_limitedPI_switch1_u2)
    algebraic_variables.append(oel_limitedPI_switch1_y)
    algebraic_variables.append(oel_lessThreshold_y)
    algebraic_variables.append(oel_timer_entryTime)
    algebraic_variables.append(oel_QGenPu)
    algebraic_variables.append(oel_QRefPu)
    algebraic_variables.append(oel_limitedPI_limiter1_simplifiedExpr)
    algebraic_variables.append(oel_limitedPI_integrator_local_reset)
    algebraic_variables.append(oel_limitedPI_integrator_local_set)
    algebraic_variables.append(PRE_oel_limitedPI_hysteresisMin_y)
    algebraic_variables.append(PRE_oel_limitedPI_hysteresisMax_y)
    algebraic_variables.append(PRE_oel_lessThreshold_y)
    algebraic_variables.append(PRE_oel_timer_entryTime)
    algebraic_variables.append(oel_feedback1_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_oel_limitedPI_integrator_y)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[oel_Ki] = vf.add_const(1.0, name='')
    event_parameters[oel_Kp] = vf.add_const(1.0, name='')
    event_parameters[oel_QGen0Pu] = vf.add_const(0.0, name='')
    event_parameters[oel_VMinPu] = vf.add_const(-1.0, name='')
    event_parameters[oel_const_k] = vf.add_const(0.0, name='')
    event_parameters[oel_lessThreshold_threshold] = vf.add_const(0.0, name='')
    event_parameters[oel_lessThreshold1_threshold] = oel_tDelay
    event_parameters[oel_limitedPI_Ki] = oel_Ki
    event_parameters[oel_limitedPI_Kp] = oel_Kp
    event_parameters[oel_limitedPI_Tol] = vf.add_const(1e-05, name='')
    event_parameters[oel_limitedPI_Y0] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_YMax] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_YMin] = oel_VMinPu
    event_parameters[oel_limitedPI_add_k1] = oel_limitedPI_Kp
    event_parameters[oel_limitedPI_add_k2] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI_const_k] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_hysteresisMax_uHigh] = oel_limitedPI_YMax
    event_parameters[oel_limitedPI_hysteresisMax_uLow] = (oel_limitedPI_YMax + (oel_limitedPI_Tol * (oel_limitedPI_YMin - oel_limitedPI_YMax)))
    event_parameters[oel_limitedPI_hysteresisMin_uHigh] = (oel_limitedPI_YMin + (oel_limitedPI_Tol * (oel_limitedPI_YMax - oel_limitedPI_YMin)))
    event_parameters[oel_limitedPI_hysteresisMin_uLow] = oel_limitedPI_YMin
    event_parameters[oel_limitedPI_integrator_k] = oel_limitedPI_Ki
    event_parameters[oel_limitedPI_integrator_y_start] = oel_limitedPI_Y0
    event_parameters[oel_limitedPI_limiter1_uMax] = oel_limitedPI_YMax
    event_parameters[oel_limitedPI_limiter1_uMin] = oel_limitedPI_YMin
    event_parameters[oel_tDelay] = vf.add_const(0.02, name='')
    event_parameters[oel_limitedPI_integrator_initType] = vf.add_const(3.0, name='')
    event_parameters[oel_limitedPI_limiter1_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI_hysteresisMax_pre_y_start] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_hysteresisMin_pre_y_start] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI_integrator_use_reset] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_integrator_use_set] = vf.add_const(0.0, name='')
    event_parameters[oel_limitedPI_limiter1_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[oel_limitedPI_limiter1_strict] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[oel_limitedPI_integrator_y] = oel_limitedPI_integrator_y_start
    initial_equations[oel_QGenPu] = vf.add_const(0.0, name='')
    initial_equations[oel_QRefPu] = vf.add_const(0.0, name='')
    initial_equations[oel_UOelPu] = oel_limitedPI_Y0
    initial_equations[oel_switch_y] = vf.add_const(0.0, name='')
    initial_equations[oel_timer_y] = vf.add_const(0.0, name='')
    initial_equations[whenCondition1] = vf.add_const(0.0, name='')
    initial_equations[oel_lessThreshold1_y] = vf.add_const(1.0, name='')
    initial_equations[oel_limitedPI_hysteresisMin_y] = (sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI_hysteresisMin_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMin_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_hysteresisMin_uLow - oel_limitedPI_add_y) + sym.Const(1e-06))))))
    initial_equations[oel_limitedPI_limiter1_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[oel_limitedPI_integrator_local_reset] = vf.add_const(0.0, name='')
    initial_equations[oel_limitedPI_integrator_local_set] = vf.add_const(0.0, name='')
    initial_equations[oel_lessThreshold_y] = sym.heaviside(((oel_lessThreshold_threshold - sym.Const(0.0)) - sym.Const(1e-06)))
    initial_equations[PRE_oel_limitedPI_hysteresisMin_y] = oel_limitedPI_hysteresisMin_pre_y_start
    initial_equations[PRE_oel_limitedPI_hysteresisMax_y] = oel_limitedPI_hysteresisMax_pre_y_start
    initial_equations[PRE_oel_lessThreshold_y] = vf.add_const(0.0, name='')
    initial_equations[PRE_oel_timer_entryTime] = vf.add_const(0.0, name='')
    initial_equations[oel_timer_entryTime] = PRE_oel_timer_entryTime
    initial_equations[oel_limitedPI_hysteresisMax_y] = (sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06))) + (PRE_oel_limitedPI_hysteresisMax_y * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_add_y - oel_limitedPI_hysteresisMax_uHigh) - sym.Const(1e-06)))) * (sym.Const(1.0) - sym.heaviside(((oel_limitedPI_hysteresisMax_uLow - oel_limitedPI_add_y) + sym.Const(1e-06))))))
    initial_equations[oel_feedback1_y] = vf.add_const(0.0, name='')
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

    template.comment = 'Generator over-excitation limiter OEL4C'
    return template
