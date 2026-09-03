# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Maintainable international-standard module for 'VRKundur'.

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

def build_vrkundur_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Materialize the international-standard EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str
    if name is None:
        template_name: str = 'VRKundur'
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
    avr_Ka: Var = vf.add_var('avr.Ka_' + template_name)
    avr_Us0Pu: Var = vf.add_var('avr.Us0Pu_' + template_name)
    avr_UsRef0Pu: Var = vf.add_var('avr.UsRef0Pu_' + template_name)
    avr_error_k1: Var = vf.add_var('avr.error.k1_' + template_name)
    avr_error_k2: Var = vf.add_var('avr.error.k2_' + template_name)
    avr_error_k3: Var = vf.add_var('avr.error.k3_' + template_name)
    avr_exciter_k: Var = vf.add_var('avr.exciter.k_' + template_name)
    avr_limiterAVR_homotopyType: Var = vf.add_var('avr.limiterAVR.homotopyType_' + template_name)
    avr_limiterAVR_limitsAtInit: Var = vf.add_var('avr.limiterAVR.limitsAtInit_' + template_name)
    avr_limiterAVR_strict: Var = vf.add_var('avr.limiterAVR.strict_' + template_name)
    avr_limiterAVR_uMax: Var = vf.add_var('avr.limiterAVR.uMax_' + template_name)
    avr_limiterAVR_uMin: Var = vf.add_var('avr.limiterAVR.uMin_' + template_name)
    avr_tR: Var = vf.add_var('avr.tR_' + template_name)
    avr_transducer_T: Var = vf.add_var('avr.transducer.T_' + template_name)
    avr_transducer_initType: Var = vf.add_var('avr.transducer.initType_' + template_name)
    avr_transducer_k: Var = vf.add_var('avr.transducer.k_' + template_name)
    avr_transducer_y_start: Var = vf.add_var('avr.transducer.y_start_' + template_name)
    # Declare the state variables used by the template.
    avr_transducer_y: Var = vf.add_var('avr.transducer.y_' + template_name)
    # Declare the algebraic/shared variables used by the template.
    START_avr_transducer_y: Var = vf.add_var('$START.avr.transducer.y_' + template_name)
    avr_UPssPu: Var = vf.add_var('avr.UPssPu_' + template_name)
    avr_UsPu: Var = vf.add_var('avr.UsPu_' + template_name)
    avr_UsRefPu: Var = vf.add_var('avr.UsRefPu_' + template_name)
    avr_efdPu: Var = vf.add_var('avr.efdPu_' + template_name)
    avr_error_y: Var = vf.add_var('avr.error.y_' + template_name)
    avr_exciter_y: Var = vf.add_var('avr.exciter.y_' + template_name)
    avr_limiterAVR_simplifiedExpr: Var = vf.add_var('avr.limiterAVR.simplifiedExpr_' + template_name)
    # Declare the differential variables used by the template.
    d_avr_transducer_y: Var = vf.add_diff_var('d_avr.transducer.y_' + template_name, base_var=avr_transducer_y)

    # Build explicit typed collections so the symbolic surface is easy to inspect.
    state_equations: list[Expr] = list()
    state_equations.append((((avr_transducer_k * avr_UsPu) - avr_transducer_y) / avr_transducer_T))
    state_variables: list[Var] = list()
    state_variables.append(avr_transducer_y)
    algebraic_equations: list[Expr] = list()
    algebraic_equations.append((avr_error_y - (((avr_error_k1 * avr_UsRefPu) + (avr_error_k2 * avr_transducer_y)) + (avr_error_k3 * avr_UPssPu))))
    algebraic_equations.append((avr_exciter_y - (avr_exciter_k * avr_error_y)))
    algebraic_equations.append((avr_efdPu - ((sym.heaviside(((avr_exciter_y - avr_limiterAVR_uMax) - sym.Const(1e-06))) * avr_limiterAVR_uMax) + ((sym.Const(1.0) - sym.heaviside(((avr_exciter_y - avr_limiterAVR_uMax) - sym.Const(1e-06)))) * ((sym.heaviside(((avr_limiterAVR_uMin - avr_exciter_y) - sym.Const(1e-06))) * avr_limiterAVR_uMin) + ((sym.Const(1.0) - sym.heaviside(((avr_limiterAVR_uMin - avr_exciter_y) - sym.Const(1e-06)))) * avr_exciter_y))))))
    algebraic_variables: list[Var] = list()
    algebraic_variables.append(avr_error_y)
    algebraic_variables.append(avr_exciter_y)
    algebraic_variables.append(avr_efdPu)
    algebraic_variables.append(avr_UPssPu)
    algebraic_variables.append(avr_UsPu)
    algebraic_variables.append(avr_UsRefPu)
    algebraic_variables.append(avr_limiterAVR_simplifiedExpr)
    algebraic_variables.append(START_avr_transducer_y)
    differential_variables: list[Var] = list()
    differential_variables.append(d_avr_transducer_y)
    input_variables: list[Var] = list()
    input_variables.append(avr_UPssPu)
    input_variables.append(avr_UsPu)
    input_variables.append(avr_UsRefPu)
    output_variables: list[Var] = list()
    output_variables.append(avr_efdPu)
    event_parameters: dict[Var, Expr | Const] = dict()
    event_parameters[avr_Efd0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_EfdMaxPu] = vf.add_const(5.0, name='')
    event_parameters[avr_EfdMinPu] = vf.add_const(0.0, name='')
    event_parameters[avr_Ka] = vf.add_const(200.0, name='')
    event_parameters[avr_Us0Pu] = vf.add_const(1.0, name='')
    event_parameters[avr_UsRef0Pu] = ((avr_Efd0Pu / avr_Ka) + avr_Us0Pu)
    event_parameters[avr_error_k1] = vf.add_const(1.0, name='')
    event_parameters[avr_error_k2] = vf.add_const(-1.0, name='')
    event_parameters[avr_error_k3] = vf.add_const(1.0, name='')
    event_parameters[avr_exciter_k] = avr_Ka
    event_parameters[avr_limiterAVR_uMax] = avr_EfdMaxPu
    event_parameters[avr_limiterAVR_uMin] = avr_EfdMinPu
    event_parameters[avr_tR] = vf.add_const(0.02, name='')
    event_parameters[avr_transducer_T] = avr_tR
    event_parameters[avr_transducer_k] = vf.add_const(1.0, name='')
    event_parameters[avr_transducer_y_start] = avr_Us0Pu
    event_parameters[avr_limiterAVR_homotopyType] = vf.add_const(1.0, name='')
    event_parameters[avr_transducer_initType] = vf.add_const(1.0, name='')
    event_parameters[avr_limiterAVR_limitsAtInit] = vf.add_const(1.0, name='')
    event_parameters[avr_limiterAVR_strict] = vf.add_const(0.0, name='')
    mode_parameters: dict[Var, Expr | Const] = dict()
    initial_equations: dict[Var, Expr | Const] = dict()
    initial_equations[avr_transducer_y] = (avr_transducer_k * avr_UsPu)
    initial_equations[avr_UPssPu] = vf.add_const(0.0, name='')
    initial_equations[avr_UsPu] = avr_Us0Pu
    initial_equations[avr_UsRefPu] = avr_UsRef0Pu
    initial_equations[avr_efdPu] = vf.add_const(1.0, name='')
    initial_equations[avr_limiterAVR_simplifiedExpr] = vf.add_const(0.0, name='')
    initial_equations[avr_error_y] = (((avr_error_k1 * avr_UsRefPu) + (avr_error_k2 * avr_transducer_y)) + (avr_error_k3 * avr_UPssPu))
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

    template.comment = 'Generator voltage regulator Kundur'
    return template
