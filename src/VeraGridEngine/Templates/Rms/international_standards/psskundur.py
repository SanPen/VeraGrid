# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'PssKundur'.

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

def build_psskundur_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'PssKundur'
    else:
        template_name: str = name

    # Allocate the template container before building the symbolic surface.
    template: RmsModelTemplate = RmsModelTemplate()
    template.tpe = DeviceType.GeneratorDevice
    template.name = template_name

    # Declare every variable explicitly before the equations reference it.
    # Declare the runtime parameter variables used by the template.
    pss_KStab: Var = vf.add_var('pss.KStab_' + template_name)
    pss_VsMaxPu: Var = vf.add_var('pss.VsMaxPu_' + template_name)
    pss_VsMinPu: Var = vf.add_var('pss.VsMinPu_' + template_name)
    pss_gainPSS_k: Var = vf.add_var('pss.gainPSS.k_' + template_name)
    pss_limiterPSS_homotopyType: Var = vf.add_var('pss.limiterPSS.homotopyType_' + template_name)
    pss_limiterPSS_limitsAtInit: Var = vf.add_var('pss.limiterPSS.limitsAtInit_' + template_name)
    pss_limiterPSS_strict: Var = vf.add_var('pss.limiterPSS.strict_' + template_name)
    pss_limiterPSS_uMax: Var = vf.add_var('pss.limiterPSS.uMax_' + template_name)
    pss_limiterPSS_uMin: Var = vf.add_var('pss.limiterPSS.uMin_' + template_name)
    pss_phaseCompensation_a_1: Var = vf.add_var('pss.phaseCompensation.a[1]_' + template_name)
    pss_phaseCompensation_a_2: Var = vf.add_var('pss.phaseCompensation.a[2]_' + template_name)
    pss_phaseCompensation_a_end: Var = vf.add_var('pss.phaseCompensation.a_end_' + template_name)
    pss_phaseCompensation_b_1: Var = vf.add_var('pss.phaseCompensation.b[1]_' + template_name)
    pss_phaseCompensation_b_2: Var = vf.add_var('pss.phaseCompensation.b[2]_' + template_name)
    pss_phaseCompensation_bb_1: Var = vf.add_var('pss.phaseCompensation.bb[1]_' + template_name)
    pss_phaseCompensation_bb_2: Var = vf.add_var('pss.phaseCompensation.bb[2]_' + template_name)
    pss_phaseCompensation_d: Var = vf.add_var('pss.phaseCompensation.d_' + template_name)
    pss_phaseCompensation_na: Var = vf.add_var('pss.phaseCompensation.na_' + template_name)
    pss_phaseCompensation_nb: Var = vf.add_var('pss.phaseCompensation.nb_' + template_name)
    pss_phaseCompensation_nx: Var = vf.add_var('pss.phaseCompensation.nx_' + template_name)
    pss_phaseCompensation_x_start_1: Var = vf.add_var('pss.phaseCompensation.x_start[1]_' + template_name)
    pss_phaseCompensation_y_start: Var = vf.add_var('pss.phaseCompensation.y_start_' + template_name)
    pss_t1: Var = vf.add_var('pss.t1_' + template_name)
    pss_t2: Var = vf.add_var('pss.t2_' + template_name)
    pss_tW: Var = vf.add_var('pss.tW_' + template_name)
    pss_washout_U0: Var = vf.add_var('pss.washout.U0_' + template_name)
    pss_washout_derivative_T: Var = vf.add_var('pss.washout.derivative.T_' + template_name)
    pss_washout_derivative_initType: Var = vf.add_var('pss.washout.derivative.initType_' + template_name)
    pss_washout_derivative_k: Var = vf.add_var('pss.washout.derivative.k_' + template_name)
    pss_washout_derivative_x_start: Var = vf.add_var('pss.washout.derivative.x_start_' + template_name)
    pss_washout_derivative_y_start: Var = vf.add_var('pss.washout.derivative.y_start_' + template_name)
    pss_washout_derivative_zeroGain: Var = vf.add_var('pss.washout.derivative.zeroGain_' + template_name)
    pss_washout_tW: Var = vf.add_var('pss.washout.tW_' + template_name)
    # Declare the state variables used by the template.
    pss_phaseCompensation_x_scaled_1: Var = vf.add_var('pss.phaseCompensation.x_scaled[1]_' + template_name)
    pss_washout_derivative_x: Var = vf.add_var('pss.washout.derivative.x_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_pss_phaseCompensation_x_scaled_1: Var = vf.add_var('$START.pss.phaseCompensation.x_scaled[1]_' + template_name)
    START_pss_washout_derivative_x: Var = vf.add_var('$START.pss.washout.derivative.x_' + template_name)
    pss_UPssPu: Var = vf.add_var('pss.UPssPu_' + template_name)
    pss_dW_y: Var = vf.add_var('pss.dW.y_' + template_name)
    pss_gainPSS_y: Var = vf.add_var('pss.gainPSS.y_' + template_name)
    pss_limiterPSS_simplifiedExpr: Var = vf.add_var('pss.limiterPSS.simplifiedExpr_' + template_name)
    pss_omegaPu: Var = vf.add_var('pss.omegaPu_' + template_name)
    pss_omegaRefPu: Var = vf.add_var('pss.omegaRefPu_' + template_name)
    pss_phaseCompensation_x_1: Var = vf.add_var('pss.phaseCompensation.x[1]_' + template_name)
    pss_phaseCompensation_y: Var = vf.add_var('pss.phaseCompensation.y_' + template_name)
    pss_washout_y: Var = vf.add_var('pss.washout.y_' + template_name)
    # Declare the differential variables used by the template.
    d_pss_phaseCompensation_x_scaled_1: Var = vf.add_diff_var('d_pss.phaseCompensation.x_scaled[1]_' + template_name, base_var=pss_phaseCompensation_x_scaled_1)
    d_pss_washout_derivative_x: Var = vf.add_diff_var('d_pss.washout.derivative.x_' + template_name, base_var=pss_washout_derivative_x)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((pss_phaseCompensation_a_end * pss_washout_y) - (pss_phaseCompensation_a_2 * pss_phaseCompensation_x_scaled_1)) / pss_phaseCompensation_a_1))
    state_equations.append(((pss_washout_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout_derivative_zeroGain) * ((pss_gainPSS_y - pss_washout_derivative_x) / pss_washout_derivative_T))))
    state_variables: list[Var] = list()
    state_variables.append(pss_phaseCompensation_x_scaled_1)
    state_variables.append(pss_washout_derivative_x)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((pss_phaseCompensation_x_1 - (pss_phaseCompensation_x_scaled_1 / pss_phaseCompensation_a_end)))
    algebraic_equations.append((pss_washout_y - ((pss_washout_derivative_zeroGain * sym.Const(0.0)) + ((sym.Const(1.0) - pss_washout_derivative_zeroGain) * (((pss_gainPSS_y - pss_washout_derivative_x) * pss_washout_derivative_k) / pss_washout_derivative_T)))))
    algebraic_equations.append((pss_phaseCompensation_y - (((pss_phaseCompensation_bb_2 - (pss_phaseCompensation_d * pss_phaseCompensation_a_2)) * pss_phaseCompensation_x_1) + (pss_phaseCompensation_d * pss_washout_y))))
    algebraic_equations.append((pss_UPssPu - ((sym.heaviside(((pss_phaseCompensation_y - pss_limiterPSS_uMax) - sym.Const(1e-06))) * pss_limiterPSS_uMax) + ((sym.Const(1.0) - sym.heaviside(((pss_phaseCompensation_y - pss_limiterPSS_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((pss_limiterPSS_uMin - pss_phaseCompensation_y) - sym.Const(1e-06))) * pss_limiterPSS_uMin) + ((sym.Const(1.0) - sym.heaviside(((pss_limiterPSS_uMin - pss_phaseCompensation_y) - sym.Const(1e-06)))) * pss_phaseCompensation_y))))))
    algebraic_equations.append((pss_dW_y - (pss_omegaPu - pss_omegaRefPu)))
    algebraic_equations.append((pss_gainPSS_y - (pss_gainPSS_k * pss_dW_y)))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(pss_phaseCompensation_x_1)
    algebraic_variables.append(pss_washout_y)
    algebraic_variables.append(pss_phaseCompensation_y)
    algebraic_variables.append(pss_UPssPu)
    algebraic_variables.append(pss_gainPSS_y)
    algebraic_variables.append(pss_omegaPu)
    algebraic_variables.append(pss_omegaRefPu)
    algebraic_variables.append(pss_limiterPSS_simplifiedExpr)
    algebraic_variables.append(pss_dW_y)
    algebraic_variables.append(START_pss_washout_derivative_x)
    algebraic_variables.append(START_pss_phaseCompensation_x_scaled_1)
    differential_variables: list[Var] = list()
    differential_variables.append(d_pss_phaseCompensation_x_scaled_1)
    differential_variables.append(d_pss_washout_derivative_x)
    input_variables: list[Var] = list()
    output_variables: list[Var] = list()
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[pss_KStab] = vf.add_const(10.0, name='')
    event_parameters[pss_VsMaxPu] = vf.add_const(0.1, name='')
    event_parameters[pss_VsMinPu] = vf.add_const(-0.1, name='')
    event_parameters[pss_gainPSS_k] = pss_KStab
    event_parameters[pss_limiterPSS_uMax] = pss_VsMaxPu
    event_parameters[pss_limiterPSS_uMin] = pss_VsMinPu
    event_parameters[pss_phaseCompensation_a_1] = pss_t2
    event_parameters[pss_phaseCompensation_a_2] = vf.add_const(1.0, name='')
    event_parameters[pss_phaseCompensation_a_end] = ((sym.heaviside(((pss_phaseCompensation_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((pss_phaseCompensation_a_1 ** sym.Const(2.0)) + (pss_phaseCompensation_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06))) * pss_phaseCompensation_a_2) + ((sym.Const(1.0) - sym.heaviside(((pss_phaseCompensation_a_2 - (sym.Const(2.220446049250313e-14) * sym.sqrt(((pss_phaseCompensation_a_1 ** sym.Const(2.0)) + (pss_phaseCompensation_a_2 ** sym.Const(2.0)))))) - sym.Const(1e-06)))) * sym.Const(1.0)))
    event_parameters[pss_phaseCompensation_b_1] = pss_t1
    event_parameters[pss_phaseCompensation_b_2] = vf.add_const(1.0, name='')
    event_parameters[pss_phaseCompensation_bb_1] = pss_phaseCompensation_b_1
    event_parameters[pss_phaseCompensation_bb_2] = pss_phaseCompensation_b_2
    event_parameters[pss_phaseCompensation_d] = (pss_phaseCompensation_bb_1 / pss_phaseCompensation_a_1)
    event_parameters[pss_phaseCompensation_x_start_1] = vf.add_const(0.0, name='')
    event_parameters[pss_phaseCompensation_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_t1] = vf.add_const(0.1, name='')
    event_parameters[pss_t2] = vf.add_const(0.05, name='')
    event_parameters[pss_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_U0] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_derivative_T] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_derivative_k] = vf.add_const(10.0, name='')
    event_parameters[pss_washout_derivative_x_start] = pss_washout_U0
    event_parameters[pss_washout_derivative_y_start] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_tW] = vf.add_const(10.0, name='')
    event_parameters[pss_limiterPSS_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[pss_phaseCompensation_na] = vf.add_const(2.0, name='')
    event_parameters[pss_phaseCompensation_nb] = vf.add_const(2.0, name='')
    event_parameters[pss_phaseCompensation_nx] = vf.add_const(1.0, name='')
    event_parameters[pss_washout_derivative_initType] = vf.add_const(1.0, name='')
    event_parameters[pss_limiterPSS_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[pss_limiterPSS_strict] = vf.add_const(0.0, name='')
    event_parameters[pss_washout_derivative_zeroGain] = sym.heaviside(((sym.Const(2.220446049250313e-16) - sym.abs(pss_washout_derivative_k)) - sym.Const(1e-06)))
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[pss_phaseCompensation_x_scaled_1] = START_pss_phaseCompensation_x_scaled_1
    initial_equations[pss_washout_derivative_x] = START_pss_washout_derivative_x
    initial_equations[pss_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[pss_gainPSS_y] = vf.add_const(0.0, name='')
    initial_equations[pss_omegaPu] = vf.add_const(1.0, name='')
    initial_equations[pss_omegaRefPu] = vf.add_const(1.0, name='')
    initial_equations[pss_phaseCompensation_x_1] = pss_phaseCompensation_x_start_1
    initial_equations[pss_phaseCompensation_y] = pss_phaseCompensation_y_start
    initial_equations[pss_washout_y] = vf.add_const(0.0, name='')
    initial_equations[pss_limiterPSS_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[pss_dW_y] = vf.add_const(0.0, name='')
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

    template.block.init_eqs[pss_phaseCompensation_x_scaled_1] = (pss_phaseCompensation_a_end * pss_phaseCompensation_x_start_1)
    template.block.init_eqs[pss_washout_derivative_x] = pss_washout_derivative_x_start

    template.comment = 'Generator power system stabilizer Kundur'
    return template
