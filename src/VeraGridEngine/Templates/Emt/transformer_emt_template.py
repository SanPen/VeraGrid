# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict

from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowRefferenceType,
    VarPowerFlowRefferenceType,
)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Var, Expr


# def get_transformer_emt_template(
#     vf: VarFactory,
#     name: str = "transformer_emt_template",
# ) -> EmtModelTemplate:
#     """
#     Build the classical linear coupled-inductor equivalent of a two-winding transformer.
#
#     The template models each phase as two coupled windings with the state
#     variables chosen as the winding currents. All static electrical constants
#     are exposed through ``api_obj_mapping`` so the EMT assembler can inject the
#     values from the static transformer API object without the template touching
#     the grid or the transformer instance directly.
#
#     :param vf: EMT variable factory.
#     :param name: Symbolic model name.
#     :return: EMT transformer model template.
#     """
#     templ: EmtModelTemplate = EmtModelTemplate()
#     templ.tpe = DeviceType.TransformerTypeDevice
#     templ.name = name
#     templ.block.name = name
#
#     c_eps = vf.add_const(1e-12)
#
#     # ------------------------------------------------------------------
#     # Publish every static transformer quantity needed by the coupled DAE.
#     # The EMT problem later writes numerical values into these symbolic
#     # variables, which keeps the template architecture aligned with pi-line EMT.
#     # ------------------------------------------------------------------
#     r1: Var = vf.add_var(name=f"xfmr_r1_{name}")
#     r2: Var = vf.add_var(name=f"xfmr_r2_{name}")
#     l1: Var = vf.add_var(name=f"xfmr_l1_{name}")
#     l2: Var = vf.add_var(name=f"xfmr_l2_{name}")
#     m12: Var = vf.add_var(name=f"xfmr_m_{name}")
#     gm: Var = vf.add_var(name=f"xfmr_gm_{name}")
#
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu] = r1
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu] = r2
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s] = l1
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s] = l2
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s] = m12
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu] = gm
#
#     # ------------------------------------------------------------------
#     # Create the terminal voltage inputs. These are the electrical interface to
#     # the network and therefore remain power-flow referenced block inputs.
#     # ------------------------------------------------------------------
#     vf_vars: list[Var] = list([
#         vf.add_var(name=f"vf_A_{name}", reference=VarPowerFlowRefferenceType.vf_A),
#         vf.add_var(name=f"vf_B_{name}", reference=VarPowerFlowRefferenceType.vf_B),
#         vf.add_var(name=f"vf_C_{name}", reference=VarPowerFlowRefferenceType.vf_C),
#     ])
#     vt_vars: list[Var] = list([
#         vf.add_var(name=f"vt_A_{name}", reference=VarPowerFlowRefferenceType.vt_A),
#         vf.add_var(name=f"vt_B_{name}", reference=VarPowerFlowRefferenceType.vt_B),
#         vf.add_var(name=f"vt_C_{name}", reference=VarPowerFlowRefferenceType.vt_C),
#     ])
#
#     # ------------------------------------------------------------------
#     # Create one primary and one secondary current state per phase. This state
#     # choice makes the coupled RL equations explicit and keeps the inductance
#     # matrix validation local to the template equations.
#     # ------------------------------------------------------------------
#     i_f: list[Var] = list([
#         vf.add_var(name=f"i_f_A_{name}"),
#         vf.add_var(name=f"i_f_B_{name}"),
#         vf.add_var(name=f"i_f_C_{name}"),
#     ])
#     i_t: list[Var] = list([
#         vf.add_var(name=f"i_t_A_{name}"),
#         vf.add_var(name=f"i_t_B_{name}"),
#         vf.add_var(name=f"i_t_C_{name}"),
#     ])
#
#     di_f: list[Var] = list([
#         vf.add_diff_var(name=f"di_f_A_{name}", base_var=i_f[0]),
#         vf.add_diff_var(name=f"di_f_B_{name}", base_var=i_f[1]),
#         vf.add_diff_var(name=f"di_f_C_{name}", base_var=i_f[2]),
#     ])
#     di_t: list[Var] = list([
#         vf.add_diff_var(name=f"di_t_A_{name}", base_var=i_t[0]),
#         vf.add_diff_var(name=f"di_t_B_{name}", base_var=i_t[1]),
#         vf.add_diff_var(name=f"di_t_C_{name}", base_var=i_t[2]),
#     ])
#
#     # ------------------------------------------------------------------
#     # Create terminal current algebraic variables. They expose the branch
#     # injections to the network KCL assembly while remaining consistent with the
#     # winding-current state choice inside the transformer block.
#     # ------------------------------------------------------------------
#     if_act: list[Var] = list([
#         vf.add_var(name=f"if_{name}_A"),
#         vf.add_var(name=f"if_{name}_B"),
#         vf.add_var(name=f"if_{name}_C"),
#     ])
#     it_act: list[Var] = list([
#         vf.add_var(name=f"it_{name}_A"),
#         vf.add_var(name=f"it_{name}_B"),
#         vf.add_var(name=f"it_{name}_C"),
#     ])
#
#     templ.block.in_vars = vf_vars + vt_vars
#     templ.block.state_vars = i_f + i_t
#     templ.block.diff_vars = di_f + di_t
#     templ.block.algebraic_vars = if_act + it_act
#
#     # ------------------------------------------------------------------
#     # Build the coupled winding differential equations. Both winding voltages are
#     # written in their own winding coordinates with the same symmetric mutual
#     # inductance matrix. The external two-port sign inversion is handled only in
#     # the terminal-current algebraic equations, which keeps the magnetic model
#     # physically symmetric while still exposing opposite branch-port currents.
#     # ------------------------------------------------------------------
#     state_eqs_f: list[Expr] = list()
#     state_eqs_t: list[Expr] = list()
#     det_l: Expr = l1 * l2 - m12 * m12
#
#     for idx in range(3):
#         primary_rhs: Expr = vf_vars[idx] - r1 * i_f[idx]
#         secondary_rhs: Expr = vt_vars[idx] - r2 * i_t[idx]
#
#         state_eqs_f.append((l2 * primary_rhs - m12 * secondary_rhs) / (det_l + c_eps))
#         state_eqs_t.append((l1 * secondary_rhs - m12 * primary_rhs) / (det_l + c_eps))
#         # state_eqs_f.append((l2 * primary_rhs + m12 * secondary_rhs) / (det_l + c_eps))
#         # state_eqs_t.append((m12 * primary_rhs + l1 * secondary_rhs) / (det_l + c_eps))
#
#     templ.block.state_eqs = state_eqs_f + state_eqs_t
#
#     # ------------------------------------------------------------------
#     # Tie the branch terminal currents to the internal winding currents. The
#     # magnetizing/core-loss conductance is modeled as a primary-side shunt term,
#     # which is the only conductance contribution present in the original block.
#     # The secondary terminal current is the negative of the winding current
#     # because the external port orientation is opposite to the winding current
#     # reference used in the coupled inductance equations.
#     # ------------------------------------------------------------------
#     alg_eqs: list[Expr] = list()
#     for idx in range(3):
#         # alg_eqs.append(if_act[idx] - (i_f[idx] + gm * vf_vars[idx]))
#         alg_eqs.append(if_act[idx] - i_f[idx])
#         alg_eqs.append(it_act[idx] - i_t[idx])
#
#     templ.block.algebraic_eqs = alg_eqs
#     templ.block.out_vars = if_act + it_act
#
#     # ------------------------------------------------------------------
#     # Publish the terminal-current mapping used by the EMT network stamping.
#     # The transformer has no neutral leg in this classical template, so the
#     # neutral and derivative slots remain explicitly empty.
#     # ------------------------------------------------------------------
#     templ.block.external_mapping = dict({
#         VarPowerFlowRefferenceType.if_N: None,
#         VarPowerFlowRefferenceType.if_A: if_act[0],
#         VarPowerFlowRefferenceType.if_B: if_act[1],
#         VarPowerFlowRefferenceType.if_C: if_act[2],
#         VarPowerFlowRefferenceType.it_N: None,
#         VarPowerFlowRefferenceType.it_A: it_act[0],
#         VarPowerFlowRefferenceType.it_B: it_act[1],
#         VarPowerFlowRefferenceType.it_C: it_act[2],
#         VarPowerFlowRefferenceType.Sf_A: None,
#         VarPowerFlowRefferenceType.Sf_B: None,
#         VarPowerFlowRefferenceType.Sf_C: None,
#         VarPowerFlowRefferenceType.St_A: None,
#         VarPowerFlowRefferenceType.St_B: None,
#         VarPowerFlowRefferenceType.St_C: None,
#         VarPowerFlowRefferenceType.d_v_N_f: None,
#         VarPowerFlowRefferenceType.d_v_A_f: None,
#         VarPowerFlowRefferenceType.d_v_B_f: None,
#         VarPowerFlowRefferenceType.d_v_C_f: None,
#         VarPowerFlowRefferenceType.d_v_N_t: None,
#         VarPowerFlowRefferenceType.d_v_A_t: None,
#         VarPowerFlowRefferenceType.d_v_B_t: None,
#         VarPowerFlowRefferenceType.d_v_C_t: None,
#     })
#
#     # ------------------------------------------------------------------
#     # Initialize the winding currents from the terminal-current algebraic view.
#     # This keeps every internal state explicitly seeded while leaving the power-
#     # flow driven network inputs to the global EMT initializer.
#     # ------------------------------------------------------------------
#     init_eqs: Dict[Var, Expr] = dict()
#     for idx in range(3):
#         # init_eqs[i_f[idx]] = if_act[idx] - gm * vf_vars[idx]
#         init_eqs[i_f[idx]] = if_act[idx]
#         init_eqs[i_t[idx]] = it_act[idx]
#     templ.block.init_eqs = init_eqs
#
#     # ------------------------------------------------------------------
#     # Initialize the current derivatives with the exact same coupled equations
#     # used in the runtime DAE. This keeps startup and runtime dynamics aligned.
#     # ------------------------------------------------------------------
#     diff_init_eqs: Dict[Var, Expr] = dict()
#     for idx in range(3):
#         primary_rhs = vf_vars[idx] - r1 * i_f[idx]
#         secondary_rhs = vt_vars[idx] - r2 * i_t[idx]
#
#         diff_init_eqs[di_f[idx]] = (l2 * primary_rhs - m12 * secondary_rhs) / (det_l + c_eps)
#         diff_init_eqs[di_t[idx]] = (l1 * secondary_rhs - m12 * primary_rhs) / (det_l + c_eps)
#         # diff_init_eqs[di_f[idx]] = (l2 * primary_rhs + m12 * secondary_rhs) / (det_l + c_eps)
#         # diff_init_eqs[di_t[idx]] = (m12 * primary_rhs + l1 * secondary_rhs) / (det_l + c_eps)
#
#     templ.block.diff_init_eqs = diff_init_eqs
#
#     return templ

def get_transformer_emt_template(
    vf: VarFactory,
    name: str = "transformer_emt_template",
) -> EmtModelTemplate:
    """
    Build a linear two-winding transformer EMT template using coupled winding currents
    as state variables.

    This simplified version keeps only the series coupled-winding model and omits the
    primary shunt branch from the EMT equations. The transformer tap ratio is exposed
    through api_obj_mapping and is used to initialize the primary winding current from
    the secondary-side port current in a way that is consistent with the external port
    convention.

    Assumptions:
    - `l1`, `l2`, and `m12` already represent the physical transformer model in the
      chosen winding coordinates.
    - branch currents are positive when leaving the connected bus.
    - `if_act` and `it_act` are externally initialized by the EMT framework from the
      power-flow solution through `external_mapping`.
    """

    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.TransformerTypeDevice
    templ.name = name
    templ.block.name = name

    c_eps = vf.add_const(1e-12)

    # ------------------------------------------------------------------
    # Static parameters injected from the API object
    # ------------------------------------------------------------------
    r1: Var = vf.add_var(name=f"xfmr_r1_{name}")
    r2: Var = vf.add_var(name=f"xfmr_r2_{name}")
    l1: Var = vf.add_var(name=f"xfmr_l1_{name}")
    l2: Var = vf.add_var(name=f"xfmr_l2_{name}")
    m12: Var = vf.add_var(name=f"xfmr_m_{name}")
    gm: Var = vf.add_var(name=f"xfmr_gm_{name}")  # kept for compatibility, unused here
    tap_ratio: Var = vf.add_var(name=f"tap_ratio_{name}")

    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu] = r1
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu] = r2
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s] = l1
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s] = l2
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s] = m12
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu] = gm
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_tap_ratio] = tap_ratio

    # ------------------------------------------------------------------
    # Terminal voltages
    # ------------------------------------------------------------------
    vf_vars: list[Var] = [
        vf.add_var(name=f"vf_A_{name}", reference=VarPowerFlowRefferenceType.vf_A),
        vf.add_var(name=f"vf_B_{name}", reference=VarPowerFlowRefferenceType.vf_B),
        vf.add_var(name=f"vf_C_{name}", reference=VarPowerFlowRefferenceType.vf_C),
    ]
    vt_vars: list[Var] = [
        vf.add_var(name=f"vt_A_{name}", reference=VarPowerFlowRefferenceType.vt_A),
        vf.add_var(name=f"vt_B_{name}", reference=VarPowerFlowRefferenceType.vt_B),
        vf.add_var(name=f"vt_C_{name}", reference=VarPowerFlowRefferenceType.vt_C),
    ]

    # ------------------------------------------------------------------
    # Internal winding-current states
    # ------------------------------------------------------------------
    i_f: list[Var] = [
        vf.add_var(name=f"i_f_A_{name}"),
        vf.add_var(name=f"i_f_B_{name}"),
        vf.add_var(name=f"i_f_C_{name}"),
    ]
    i_t: list[Var] = [
        vf.add_var(name=f"i_t_A_{name}"),
        vf.add_var(name=f"i_t_B_{name}"),
        vf.add_var(name=f"i_t_C_{name}"),
    ]

    di_f: list[Var] = [
        vf.add_diff_var(name=f"di_f_A_{name}", base_var=i_f[0]),
        vf.add_diff_var(name=f"di_f_B_{name}", base_var=i_f[1]),
        vf.add_diff_var(name=f"di_f_C_{name}", base_var=i_f[2]),
    ]
    di_t: list[Var] = [
        vf.add_diff_var(name=f"di_t_A_{name}", base_var=i_t[0]),
        vf.add_diff_var(name=f"di_t_B_{name}", base_var=i_t[1]),
        vf.add_diff_var(name=f"di_t_C_{name}", base_var=i_t[2]),
    ]

    # ------------------------------------------------------------------
    # External branch-port currents
    # ------------------------------------------------------------------
    if_act: list[Var] = [
        vf.add_var(name=f"if_{name}_A"),
        vf.add_var(name=f"if_{name}_B"),
        vf.add_var(name=f"if_{name}_C"),
    ]
    it_act: list[Var] = [
        vf.add_var(name=f"it_{name}_A"),
        vf.add_var(name=f"it_{name}_B"),
        vf.add_var(name=f"it_{name}_C"),
    ]

    templ.block.in_vars = vf_vars + vt_vars
    templ.block.state_vars = i_f + i_t
    templ.block.diff_vars = di_f + di_t
    templ.block.algebraic_vars = if_act + it_act

    # ------------------------------------------------------------------
    # Coupled winding dynamics
    #
    # [l1  m12] [di_f/dt] = [vf - r1*i_f]
    # [m12 l2 ] [di_t/dt]   [vt - r2*i_t]
    #
    # Inverting the inductance matrix gives negative signs in the cross terms.
    # ------------------------------------------------------------------
    state_eqs_f: list[Expr] = []
    state_eqs_t: list[Expr] = []
    det_l: Expr = l1 * l2 - m12 * m12

    for idx in range(3):
        primary_rhs: Expr = vf_vars[idx] - r1 * i_f[idx]
        secondary_rhs: Expr = vt_vars[idx] - r2 * i_t[idx]

        state_eqs_f.append((l2 * primary_rhs - m12 * secondary_rhs) / (det_l + c_eps))
        state_eqs_t.append((l1 * secondary_rhs - m12 * primary_rhs) / (det_l + c_eps))

    templ.block.state_eqs = state_eqs_f + state_eqs_t

    # ------------------------------------------------------------------
    # Port-current algebraic equations
    #
    # In this simplified EMT model, the port currents are exactly the series
    # winding currents. The primary-side shunt branch is intentionally omitted.
    # ------------------------------------------------------------------
    alg_eqs: list[Expr] = []
    for idx in range(3):
        # alg_eqs.append(if_act[idx] - i_f[idx])
        # alg_eqs.append(it_act[idx] - i_t[idx])
        alg_eqs.append(if_act[idx] - (i_f[idx] + gm * vf_vars[idx]))
        alg_eqs.append(it_act[idx] - i_t[idx])

    templ.block.algebraic_eqs = alg_eqs
    templ.block.out_vars = if_act + it_act

    # ------------------------------------------------------------------
    # External mapping for network stamping / PF seeding
    # ------------------------------------------------------------------
    templ.block.external_mapping = dict({
        VarPowerFlowRefferenceType.if_N: None,
        VarPowerFlowRefferenceType.if_A: if_act[0],
        VarPowerFlowRefferenceType.if_B: if_act[1],
        VarPowerFlowRefferenceType.if_C: if_act[2],
        VarPowerFlowRefferenceType.it_N: None,
        VarPowerFlowRefferenceType.it_A: it_act[0],
        VarPowerFlowRefferenceType.it_B: it_act[1],
        VarPowerFlowRefferenceType.it_C: it_act[2],
        VarPowerFlowRefferenceType.Sf_A: None,
        VarPowerFlowRefferenceType.Sf_B: None,
        VarPowerFlowRefferenceType.Sf_C: None,
        VarPowerFlowRefferenceType.St_A: None,
        VarPowerFlowRefferenceType.St_B: None,
        VarPowerFlowRefferenceType.St_C: None,
        VarPowerFlowRefferenceType.d_v_N_f: None,
        VarPowerFlowRefferenceType.d_v_A_f: None,
        VarPowerFlowRefferenceType.d_v_B_f: None,
        VarPowerFlowRefferenceType.d_v_C_f: None,
        VarPowerFlowRefferenceType.d_v_N_t: None,
        VarPowerFlowRefferenceType.d_v_A_t: None,
        VarPowerFlowRefferenceType.d_v_B_t: None,
        VarPowerFlowRefferenceType.d_v_C_t: None,
    })

    # ------------------------------------------------------------------
    # State initialization
    #
    # Since the EMT model omits the shunt branch, initialize the secondary
    # winding current directly from the secondary port current and initialize
    # the primary winding current from the secondary current referred through
    # the tap ratio.
    #
    # With branch currents positive when leaving the bus:
    #   primary series current ~= -(secondary port current) / tap_ratio
    # ------------------------------------------------------------------
    init_eqs: Dict[Var, Expr] = dict()
    tap_ratio_safe: Expr = tap_ratio + c_eps

    for idx in range(3):
        # init_eqs[i_t[idx]] = it_act[idx]
        # init_eqs[i_f[idx]] = -it_act[idx] / tap_ratio_safe
        init_eqs[i_f[idx]] = if_act[idx] - gm * vf_vars[idx]
        init_eqs[i_t[idx]] = it_act[idx]

    templ.block.init_eqs = init_eqs

    # ------------------------------------------------------------------
    # Derivative initialization aligned with runtime dynamics
    # ------------------------------------------------------------------
    diff_init_eqs: Dict[Var, Expr] = dict()
    for idx in range(3):
        primary_rhs: Expr = vf_vars[idx] - r1 * i_f[idx]
        secondary_rhs: Expr = vt_vars[idx] - r2 * i_t[idx]

        diff_init_eqs[di_f[idx]] = (l2 * primary_rhs - m12 * secondary_rhs) / (det_l + c_eps)
        diff_init_eqs[di_t[idx]] = (l1 * secondary_rhs - m12 * primary_rhs) / (det_l + c_eps)

    templ.block.diff_init_eqs = diff_init_eqs

    return templ
