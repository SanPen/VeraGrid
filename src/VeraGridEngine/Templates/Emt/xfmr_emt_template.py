# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict
import numpy as np

from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType, ParamPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Var, Expr
import VeraGridEngine.Utils.Symbolic.symbolic as sym


# def _mat_vec_expr(mat: np.ndarray, vec: list[Expr], c0: Expr) -> list[Expr]:
#     out: list[Expr] = []
#     rows, cols = mat.shape
#     for i in range(rows):
#         rhs = c0
#         for j in range(cols):
#             coeff = float(mat[i, j])
#             if abs(coeff) > 1e-15:
#                 rhs = rhs + coeff * vec[j]
#         out.append(rhs)
#     return out
#
#
# def get_xfmr_emt_template(
#     vf: VarFactory,
#     name: str = "xfmr_emt_template",
# ) -> EmtModelTemplate:
#     """
#     Build the local XFMR-style transformer EMT DAE template.
#
#     - leakage and copper losses are separated from the main/core flux path,
#     - short-circuit report data parameterize the series leakage branch,
#     - open-circuit report data parameterize the core branch,
#     - the core branch uses the basic Frohlich ``lambda(i)`` law,
#     - core losses remain linear resistive branches,
#     - the magnetic return path distinguishes 3-legged and 5-legged stacked cores.
#
#     Static quantities that already exist on ``Transformer2W`` are not sourced from
#     ``event_dict``. They are exposed as dynamic block parameters through
#     ``api_obj_mapping`` so the EMT assembler can assign them from the static
#     transformer object. Only data not stored on ``Transformer2W`` remain in
#     ``event_dict``.
#
#     Because ``core_topology`` and the optional relative core geometry are not
#     stored on ``Transformer2W`` in the current repository, they remain local
#     non-mapped block parameters. The default local topology code is ``3.0`` for a
#     three-legged core.
#
#     :param vf: EMT variable factory.
#     :param name: Symbolic model name.
#     :return: EMT transformer template.
#     """
#     templ = EmtModelTemplate()
#     templ.tpe = DeviceType.TransformerTypeDevice
#     templ.name = name
#     templ.block.name = name
#
#     c0: Expr = vf.add_const(0.0)
#     c_eps: Expr = vf.add_const(1e-9)
#
#     # ------------------------------------------------------------------
#     # Create the derivative inputs used by the terminal capacitance path.
#     # These are event-driven because they belong to the instantaneous electrical
#     # coupling contract, not to the static transformer object.
#     # ------------------------------------------------------------------
#     d_v_f: list[Var] = list([
#         vf.add_var(name=f"d_vf_A_{name}", reference=VarPowerFlowRefferenceType.d_v_A_f),
#         vf.add_var(name=f"d_vf_B_{name}", reference=VarPowerFlowRefferenceType.d_v_B_f),
#         vf.add_var(name=f"d_vf_C_{name}", reference=VarPowerFlowRefferenceType.d_v_C_f),
#     ])
#     d_v_t: list[Var] = list([
#         vf.add_var(name=f"d_vt_A_{name}", reference=VarPowerFlowRefferenceType.d_v_A_t),
#         vf.add_var(name=f"d_vt_B_{name}", reference=VarPowerFlowRefferenceType.d_v_B_t),
#         vf.add_var(name=f"d_vt_C_{name}", reference=VarPowerFlowRefferenceType.d_v_C_t),
#     ])
#
#     for d_var in d_v_f:
#         templ.block.event_dict[d_var] = vf.add_const(None)
#     for d_var in d_v_t:
#         templ.block.event_dict[d_var] = vf.add_const(None)
#
#     # ------------------------------------------------------------------
#     # Create mapped XFMR parameters.
#     #
#     # Model reason:
#     # These quantities are sourced from the static transformer object through the
#     # EMT assembler rather than copied into event_dict.
#     #
#     # Algorithm reason:
#     # The variables are registered in api_obj_mapping so the template becomes a
#     # pure symbolic consumer of mapped parameters, in the same architectural
#     # style as the pi-line EMT template.
#     # ------------------------------------------------------------------
#     omega_base: Var = vf.add_var(name=f"omega_base_{name}")
#     xfmr_s_rated_mva: Var = vf.add_var(name=f"xfmr_s_rated_mva_{name}")
#     xfmr_v_hv_ll_kv: Var = vf.add_var(name=f"xfmr_v_hv_ll_kv_{name}")
#     xfmr_v_lv_ll_kv: Var = vf.add_var(name=f"xfmr_v_lv_ll_kv_{name}")
#     xfmr_vector_group_clock: Var = vf.add_var(name=f"xfmr_vector_group_clock_{name}")
#     xfmr_oc_current_pct: Var = vf.add_var(name=f"xfmr_oc_current_pct_{name}")
#     xfmr_oc_loss_kw: Var = vf.add_var(name=f"xfmr_oc_loss_kw_{name}")
#     xfmr_sc_voltage_pct: Var = vf.add_var(name=f"xfmr_sc_voltage_pct_{name}")
#     xfmr_sc_resistance_pct: Var = vf.add_var(name=f"xfmr_sc_resistance_pct_{name}")
#     xfmr_sc_loss_kw: Var = vf.add_var(name=f"xfmr_sc_loss_kw_{name}")
#     xfmr_tap_module: Var = vf.add_var(name=f"xfmr_tap_module_{name}")
#     xfmr_c_term: Var = vf.add_var(name=f"xfmr_c_term_{name}")
#     xfmr_core_linear_l_pu: Var = vf.add_var(name=f"xfmr_core_linear_l_pu_{name}")
#     xfmr_core_a_prime: Var = vf.add_var(name=f"xfmr_core_a_prime_{name}")
#     xfmr_core_b_prime: Var = vf.add_var(name=f"xfmr_core_b_prime_{name}")
#     xfmr_use_linear_core: Var = vf.add_var(name=f"xfmr_use_linear_core_{name}")
#
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.omega_base] = omega_base
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_rated_power_mva] = xfmr_s_rated_mva
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding1_rated_voltage_ll_kv] = xfmr_v_hv_ll_kv
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_winding2_rated_voltage_ll_kv] = xfmr_v_lv_ll_kv
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_connection_clock] = xfmr_vector_group_clock
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct] = xfmr_oc_current_pct
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw] = xfmr_oc_loss_kw
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct] = xfmr_sc_voltage_pct
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_short_circuit_resistance_pct] = xfmr_sc_resistance_pct
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_short_circuit_loss_kw] = xfmr_sc_loss_kw
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_tap_ratio] = xfmr_tap_module
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_terminal_capacitance_pu_s] = xfmr_c_term
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_linear_core_inductance_pu_s] = xfmr_core_linear_l_pu
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_core_curve_a_prime] = xfmr_core_a_prime
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_core_curve_b_prime] = xfmr_core_b_prime
#     templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_use_linear_core] = xfmr_use_linear_core
#
#     cf_enums: list[list[ParamPowerFlowRefferenceType]] = list([
#         list([
#             ParamPowerFlowRefferenceType.transformer_from_connection_aa,
#             ParamPowerFlowRefferenceType.transformer_from_connection_ab,
#             ParamPowerFlowRefferenceType.transformer_from_connection_ac,
#         ]),
#         list([
#             ParamPowerFlowRefferenceType.transformer_from_connection_ba,
#             ParamPowerFlowRefferenceType.transformer_from_connection_bb,
#             ParamPowerFlowRefferenceType.transformer_from_connection_bc,
#         ]),
#         list([
#             ParamPowerFlowRefferenceType.transformer_from_connection_ca,
#             ParamPowerFlowRefferenceType.transformer_from_connection_cb,
#             ParamPowerFlowRefferenceType.transformer_from_connection_cc,
#         ]),
#     ])
#     ct_enums: list[list[ParamPowerFlowRefferenceType]] = list([
#         list([
#             ParamPowerFlowRefferenceType.transformer_to_connection_aa,
#             ParamPowerFlowRefferenceType.transformer_to_connection_ab,
#             ParamPowerFlowRefferenceType.transformer_to_connection_ac,
#         ]),
#         list([
#             ParamPowerFlowRefferenceType.transformer_to_connection_ba,
#             ParamPowerFlowRefferenceType.transformer_to_connection_bb,
#             ParamPowerFlowRefferenceType.transformer_to_connection_bc,
#         ]),
#         list([
#             ParamPowerFlowRefferenceType.transformer_to_connection_ca,
#             ParamPowerFlowRefferenceType.transformer_to_connection_cb,
#             ParamPowerFlowRefferenceType.transformer_to_connection_cc,
#         ]),
#     ])
#
#     c_f_vars: list[list[Var]] = list()
#     c_t_eff_vars: list[list[Var]] = list()
#     for i in range(3):
#         c_f_row: list[Var] = list()
#         c_t_row: list[Var] = list()
#         for j in range(3):
#             c_f_var: Var = vf.add_var(name=f"xfmr_cf_{i}_{j}_{name}")
#             c_t_var: Var = vf.add_var(name=f"xfmr_ct_{i}_{j}_{name}")
#             templ.block.api_obj_mapping[cf_enums[i][j]] = c_f_var
#             templ.block.api_obj_mapping[ct_enums[i][j]] = c_t_var
#             c_f_row.append(c_f_var)
#             c_t_row.append(c_t_var)
#         c_f_vars.append(c_f_row)
#         c_t_eff_vars.append(c_t_row)
#
#     # ------------------------------------------------------------------
#     # Create non-mapped local core-topology and geometry parameters.
#     #
#     # Model reason:
#     # The present Transformer2W object does not store this data, so there is no
#     # static source to connect through api_obj_mapping.
#     #
#     # Algorithm reason:
#     # Keeping these few parameters in event_dict preserves local configurability
#     # without creating a duplicate shadow path for data already on Transformer2W.
#     # ------------------------------------------------------------------
#     xfmr_core_topology_code: Var = vf.add_var(name=f"xfmr_core_topology_code_{name}")
#     xfmr_yoke_area_rel: Var = vf.add_var(name=f"xfmr_yoke_area_rel_{name}")
#     xfmr_yoke_length_rel: Var = vf.add_var(name=f"xfmr_yoke_length_rel_{name}")
#     xfmr_outer_leg_area_rel: Var = vf.add_var(name=f"xfmr_outer_leg_area_rel_{name}")
#     xfmr_outer_leg_length_rel: Var = vf.add_var(name=f"xfmr_outer_leg_length_rel_{name}")
#     templ.block.event_dict[xfmr_core_topology_code] = vf.add_const(3.0)
#     templ.block.event_dict[xfmr_yoke_area_rel] = vf.add_const(1.0)
#     templ.block.event_dict[xfmr_yoke_length_rel] = vf.add_const(1.0)
#     templ.block.event_dict[xfmr_outer_leg_area_rel] = vf.add_const(1.0)
#     templ.block.event_dict[xfmr_outer_leg_length_rel] = vf.add_const(1.0)
#
#     # ------------------------------------------------------------------
#     # Derive the leakage parameters directly from the short-circuit report.
#     #
#     # Model reason:
#     # XFMR separates leakage and main flux. The leakage branch must come from
#     # short-circuit data, while saturation must remain only in the core model.
#     #
#     # Algorithm reason:
#     # We compute z_sc, r_sc, and x_sc in per unit exactly in the paper/report
#     # style, then convert x_sc into a symbolic leakage inductance for the EMT
#     # differential equation. The single two-winding series branch preserves the
#     # existing VeraGrid block contract, so the equal resistance sharing is
#     # represented implicitly by this one equivalent branch.
#     # ------------------------------------------------------------------
#     z_sc_pu: Expr = xfmr_sc_voltage_pct / 100.0
#     r_sc_pu: Expr = xfmr_sc_resistance_pct / 100.0
#     x_sc_pu: Expr = sym.sqrt(sym.max(z_sc_pu * z_sc_pu - r_sc_pu * r_sc_pu, c0))
#     l_sigma: Expr = x_sc_pu / (omega_base + c_eps)
#     l_inv: Expr = 1.0 / (l_sigma + c_eps)
#
#     # ------------------------------------------------------------------
#     # Derive the linear core-loss conductance from the rated open-circuit loss.
#     #
#     # Model reason:
#     # The task explicitly keeps core losses linear and resistive even when the
#     # magnetizing inductive branch is nonlinear.
#     #
#     # Algorithm reason:
#     # We convert rated OC loss into a total per-unit conductance and distribute
#     # it evenly across the three legs in this local implementation so the model
#     # stays compatible with the current energized-side current injection layout.
#     # ------------------------------------------------------------------
#     g_core_total: Expr = (xfmr_oc_loss_kw / 1000.0) / (xfmr_s_rated_mva + c_eps)
#     g_core_leg: Expr = g_core_total / 3.0
#
#     # ------------------------------------------------------------------
#     # Recover the linear single-point open-circuit core slope from mapped test
#     # report values. This preserves the paper's one-point linear-core fallback
#     # without touching the static transformer object in the template.
#     # ------------------------------------------------------------------
#     oc_loss_pu: Expr = (xfmr_oc_loss_kw / 1000.0) / (xfmr_s_rated_mva + c_eps)
#     oc_current_pu: Expr = xfmr_oc_current_pct / 100.0
#     i_mag_pu: Expr = sym.sqrt(sym.max(oc_current_pu * oc_current_pu - oc_loss_pu * oc_loss_pu, c0))
#     lambda_peak: Expr = sym.sqrt(2.0) * 1.0
#     current_peak: Expr = sym.sqrt(2.0) * i_mag_pu
#     linear_lm_expr: Expr = lambda_peak / (current_peak + c_eps)
#
#     # Build matrix expressions from the mapped connection coefficients.
#     c_f_expr: list[list[Expr]] = list(c_f_vars)
#     c_t_eff_expr: list[list[Expr]] = list(c_t_eff_vars)
#
#     # ------------------------------------------------------------------
#     # Create the electrical interface variables.
#     #
#     # Model reason:
#     # These are the abc terminal voltages seen by the EMT network solver.
#     #
#     # Algorithm reason:
#     # They keep the same public mapping used elsewhere in VeraGrid, so callers
#     # and nodal KCL stamping continue to work unchanged.
#     # ------------------------------------------------------------------
#     v_f: list[Var] = list([
#         vf.add_var(name=f"vf_A_{name}", reference=VarPowerFlowRefferenceType.vf_A),
#         vf.add_var(name=f"vf_B_{name}", reference=VarPowerFlowRefferenceType.vf_B),
#         vf.add_var(name=f"vf_C_{name}", reference=VarPowerFlowRefferenceType.vf_C),
#     ])
#     v_t: list[Var] = list([
#         vf.add_var(name=f"vt_A_{name}", reference=VarPowerFlowRefferenceType.vt_A),
#         vf.add_var(name=f"vt_B_{name}", reference=VarPowerFlowRefferenceType.vt_B),
#         vf.add_var(name=f"vt_C_{name}", reference=VarPowerFlowRefferenceType.vt_C),
#     ])
#
#     # ------------------------------------------------------------------
#     # Differential variables.
#     #
#     # Model reason:
#     # - i_leak stores the leakage-channel current dynamics.
#     # - lam_leg stores the main-flux linkage of each core leg.
#     # - q_f and q_t store the terminal capacitor charges.
#     #
#     # Algorithm reason:
#     # Using leg flux linkages as explicit states lets the DAE express the core
#     # nonlinearity algebraically while keeping Faraday's law in differential
#     # form through d(lambda)/dt = omega * v in per-unit sinusoidal scaling.
#     # ------------------------------------------------------------------
#     i_leak: list[Var] = list(vf.add_var(name=f"i_leak_{ph}_{name}") for ph in ("A", "B", "C"))
#     lam_leg: list[Var] = list(vf.add_var(name=f"lam_leg_{ph}_{name}") for ph in ("A", "B", "C"))
#     q_f: list[Var] = list(vf.add_var(name=f"qf_{ph}_{name}") for ph in ("A", "B", "C"))
#     q_t: list[Var] = list(vf.add_var(name=f"qt_{ph}_{name}") for ph in ("A", "B", "C"))
#
#     di_leak: list[Var] = list(vf.add_diff_var(name=f"di_leak_{ph}_{name}", base_var=i_leak[k]) for k, ph in enumerate(("A", "B", "C")))
#     dlam_leg: list[Var] = list(vf.add_diff_var(name=f"dlam_leg_{ph}_{name}", base_var=lam_leg[k]) for k, ph in enumerate(("A", "B", "C")))
#     dq_f: list[Var] = list(vf.add_diff_var(name=f"dqf_{ph}_{name}", base_var=q_f[k]) for k, ph in enumerate(("A", "B", "C")))
#     dq_t: list[Var] = list(vf.add_diff_var(name=f"dqt_{ph}_{name}", base_var=q_t[k]) for k, ph in enumerate(("A", "B", "C")))
#
#     # ------------------------------------------------------------------
#     # Algebraic variables.
#     #
#     # Model reason:
#     # - i_leg_core are the nonlinear leg magnetizing currents.
#     # - i_return_path / i_return_total are the return-path currents that enforce
#     #   the chosen 3-legged or 5-legged core topology.
#     # - i_mag are the phase magnetizing currents injected into the electrical side.
#     # - i_loss_leg are the linear core-loss currents.
#     # - i_cap_f / i_cap_t are capacitor currents.
#     # - if_act / it_act are the final terminal currents stamped into network KCL.
#     #
#     # Algorithm reason:
#     # The Frohlich law is imposed as algebraic constitutive equations, which is
#     # the cleanest way to keep the model as a symbolic DAE block.
#     # ------------------------------------------------------------------
#     i_leg_core: list[Var] = list(vf.add_var(name=f"i_leg_core_{ph}_{name}") for ph in ("A", "B", "C"))
#     i_mag: list[Var] = list(vf.add_var(name=f"i_mag_{ph}_{name}") for ph in ("A", "B", "C"))
#     i_loss_leg: list[Var] = list(vf.add_var(name=f"i_loss_leg_{ph}_{name}") for ph in ("A", "B", "C"))
#     i_cap_f: list[Var] = list(vf.add_var(name=f"i_cap_f_{ph}_{name}") for ph in ("A", "B", "C"))
#     i_cap_t: list[Var] = list(vf.add_var(name=f"i_cap_t_{ph}_{name}") for ph in ("A", "B", "C"))
#     if_act: list[Var] = list(vf.add_var(name=f"if_{ph}_{name}") for ph in ("A", "B", "C"))
#     it_act: list[Var] = list(vf.add_var(name=f"it_{ph}_{name}") for ph in ("A", "B", "C"))
#
#     i_return_path: Var = vf.add_var(name=f"i_return_path_{name}")
#     i_return_total: Var = vf.add_var(name=f"i_return_total_{name}")
#
#     templ.block.in_vars = v_f + v_t + d_v_f + d_v_t
#     templ.block.state_vars = i_leak + lam_leg + q_f + q_t
#     templ.block.diff_vars = di_leak + dlam_leg + dq_f + dq_t
#     templ.block.algebraic_vars = i_leg_core + list([i_return_path, i_return_total]) + i_mag + i_loss_leg + i_cap_f + i_cap_t + if_act + it_act
#
#     c_f_expr_t: list[list[Expr]] = list(list(c_f_expr[j][i] for j in range(3)) for i in range(3))
#     c_t_expr_t: list[list[Expr]] = list(list(c_t_eff_expr[j][i] for j in range(3)) for i in range(3))
#
#     v_f_w: list[Expr] = list()
#     v_t_w: list[Expr] = list()
#     d_v_f_w: list[Expr] = list()
#     d_v_t_w: list[Expr] = list()
#     for i in range(3):
#         expr_vfw: Expr = c0
#         expr_vtw: Expr = c0
#         expr_dvfw: Expr = c0
#         expr_dvtw: Expr = c0
#         for j in range(3):
#             expr_vfw = expr_vfw + c_f_expr_t[i][j] * v_f[j]
#             expr_vtw = expr_vtw + c_t_expr_t[i][j] * v_t[j]
#             expr_dvfw = expr_dvfw + c_f_expr_t[i][j] * d_v_f[j]
#             expr_dvtw = expr_dvtw + c_t_expr_t[i][j] * d_v_t[j]
#         v_f_w.append(expr_vfw)
#         v_t_w.append(expr_vtw)
#         d_v_f_w.append(expr_dvfw)
#         d_v_t_w.append(expr_dvtw)
#
#     n_tap: Expr = xfmr_tap_module
#     v_leak: list[Expr] = list(v_f_w[k] - n_tap * v_t_w[k] for k in range(3))
#
#     # Build the leakage-current and flux-linkage differential equations.
#     #
#     # Model reason:
#     # The leakage branch is linear and separate from the saturable core branch.
#     # The leg flux states integrate the winding-side induced voltages.
#     #
#     # Algorithm reason:
#     # The state_eqs list must follow the same order as state_vars.
#     state_eqs: list[Expr] = list()
#     for k in range(3):
#         state_eqs.append(l_inv * (v_leak[k] - r_sc_pu * i_leak[k]))
#     for k in range(3):
#         state_eqs.append(omega_base * v_f_w[k])
#     for k in range(3):
#         state_eqs.append(i_cap_f[k])
#     for k in range(3):
#         state_eqs.append(i_cap_t[k])
#     templ.block.state_eqs = state_eqs
#
#     # ------------------------------------------------------------------
#     # Build the magnetic return-path equations.
#     #
#     # Model reason:
#     # This is where the model becomes topologically aware instead of collapsing
#     # everything into one shunt branch. The sum of the three leg fluxes must
#     # close through the yokes and, for a 5-legged core, through the two outer
#     # return limbs.
#     #
#     # Algorithm reason:
#     # We write the return path as algebraic lambda(i) equations so that the
#     # selected topology changes only the constitutive relation, not the external
#     # electrical contract of the template.
#     # ------------------------------------------------------------------
#     lam_return_total: Expr = -(lam_leg[0] + lam_leg[1] + lam_leg[2])
#     five_leg_selector: Expr = sym.heaviside(xfmr_core_topology_code - 4.0)
#     three_leg_selector: Expr = 1.0 - five_leg_selector
#
#     yoke_area_rel: Expr = xfmr_yoke_area_rel
#     yoke_length_rel: Expr = xfmr_yoke_length_rel
#     outer_leg_area_rel: Expr = xfmr_outer_leg_area_rel
#     outer_leg_length_rel: Expr = xfmr_outer_leg_length_rel
#
#     leg_linear_coeff: Expr = xfmr_use_linear_core * xfmr_core_linear_l_pu + (1.0 - xfmr_use_linear_core) * linear_lm_expr
#     yoke_linear_coeff: Expr = leg_linear_coeff * yoke_area_rel / (yoke_length_rel + c_eps)
#     outer_linear_coeff: Expr = leg_linear_coeff * outer_leg_area_rel / (outer_leg_length_rel + c_eps)
#
#     c_smooth: Expr = vf.add_const(1e-8)
#
#     # yoke_frolich_lam: Expr = yoke_area_rel * i_return_path / (xfmr_core_a_prime * yoke_length_rel + xfmr_core_b_prime * sym.abs(i_return_path) + c_eps)
#     # outer_frolich_lam: Expr = outer_leg_area_rel * i_return_path / (xfmr_core_a_prime * outer_leg_length_rel + xfmr_core_b_prime * sym.abs(i_return_path) + c_eps)
#     yoke_frolich_lam: Expr = yoke_area_rel * i_return_path / (
#                 xfmr_core_a_prime * yoke_length_rel + xfmr_core_b_prime * sym.sqrt(
#             i_return_path ** 2 + c_smooth) + c_eps)
#     outer_frolich_lam: Expr = outer_leg_area_rel * i_return_path / (
#                 xfmr_core_a_prime * outer_leg_length_rel + xfmr_core_b_prime * sym.sqrt(
#             i_return_path ** 2 + c_smooth) + c_eps)
#
#     i_series_from: list[Expr] = list()
#     i_series_to: list[Expr] = list()
#     for i in range(3):
#         expr_if: Expr = c0
#         expr_it: Expr = c0
#         for j in range(3):
#             expr_if = expr_if + c_f_expr[i][j] * i_leak[j]
#             expr_it = expr_it + c_t_eff_expr[i][j] * i_leak[j]
#         i_series_from.append(expr_if)
#         i_series_to.append(expr_it)
#
#     # Collect algebraic equations in the same order as algebraic_vars.
#     alg_eqs: list[Expr] = list()
#
#     for k in range(3):
#         # Main leg constitutive law.
#         #
#         # In the single-point default path the law is linear, matching the paper.
#         # If callers later override the fitted a' and b' parameters and disable
#         # the linear flag, this equation becomes the basic Fr"ohlich law.
#         linear_leg_eq: Expr = lam_leg[k] - leg_linear_coeff * i_leg_core[k]
#         # nonlinear_leg_eq: Expr = lam_leg[k] - i_leg_core[k] / (xfmr_core_a_prime + xfmr_core_b_prime * sym.abs(i_leg_core[k]) + c_eps)
#         # alg_eqs.append(xfmr_use_linear_core * linear_leg_eq + (1.0 - xfmr_use_linear_core) * nonlinear_leg_eq)
#         nonlinear_leg_eq: Expr = lam_leg[k] - i_leg_core[k] / (
#                     xfmr_core_a_prime + xfmr_core_b_prime * sym.sqrt(i_leg_core[k] ** 2 + c_smooth) + c_eps)
#         alg_eqs.append(xfmr_use_linear_core * linear_leg_eq + (1.0 - xfmr_use_linear_core) * nonlinear_leg_eq)
#
#     five_leg_eq_linear: Expr = 0.5 * lam_return_total - (2.0 * yoke_linear_coeff * i_return_path + outer_linear_coeff * i_return_path)
#     five_leg_eq_nonlinear: Expr = 0.5 * lam_return_total - (2.0 * yoke_frolich_lam + outer_frolich_lam)
#     three_leg_eq_linear: Expr = lam_return_total - 2.0 * yoke_linear_coeff * i_return_path
#     three_leg_eq_nonlinear: Expr = lam_return_total - 2.0 * yoke_frolich_lam
#
#     alg_eqs.append(
#         five_leg_selector * (xfmr_use_linear_core * five_leg_eq_linear + (1.0 - xfmr_use_linear_core) * five_leg_eq_nonlinear)
#         + three_leg_selector * (xfmr_use_linear_core * three_leg_eq_linear + (1.0 - xfmr_use_linear_core) * three_leg_eq_nonlinear)
#     )
#     alg_eqs.append(i_return_total - (five_leg_selector * 2.0 * i_return_path + three_leg_selector * i_return_path))
#
#     for k in range(3):
#         # Convert magnetic branch currents into electrical magnetizing current at
#         # each phase. The return-path current subtracts from each leg current.
#         alg_eqs.append(i_mag[k] - (i_leg_core[k] - i_return_total))
#
#     for k in range(3):
#         # Linear core-loss branch in parallel with the inductive core branch.
#         alg_eqs.append(i_loss_leg[k] - g_core_leg * v_f_w[k])
#
#     for k in range(3):
#         # Capacitor constitutive equations using supplied bus voltage derivatives.
#         alg_eqs.append(i_cap_f[k] - xfmr_c_term * d_v_f[k])
#         alg_eqs.append(i_cap_t[k] - xfmr_c_term * d_v_t[k])
#
#     for k in range(3):
#         # Charge/voltage relations for the retained terminal capacitance states.
#         alg_eqs.append(q_f[k] - xfmr_c_term * v_f[k])
#         alg_eqs.append(q_t[k] - xfmr_c_term * v_t[k])
#
#     for k in range(3):
#         # Final terminal current assembly.
#         #
#         # From-side current includes leakage, magnetizing, core-loss, and local
#         # terminal capacitance currents. To-side current includes the referred
#         # leakage current plus the to-side terminal capacitance current.
#         alg_eqs.append(if_act[k] - (i_series_from[k] + i_mag[k] + i_loss_leg[k] + i_cap_f[k]))
#         alg_eqs.append(it_act[k] - (-n_tap * i_series_to[k] + i_cap_t[k]))
#
#     templ.block.algebraic_eqs = alg_eqs
#     templ.block.out_vars = if_act + it_act + i_mag
#     templ.block.name = name
#
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
#         VarPowerFlowRefferenceType.d_v_A_f: d_v_f[0],
#         VarPowerFlowRefferenceType.d_v_B_f: d_v_f[1],
#         VarPowerFlowRefferenceType.d_v_C_f: d_v_f[2],
#         VarPowerFlowRefferenceType.d_v_N_t: None,
#         VarPowerFlowRefferenceType.d_v_A_t: d_v_t[0],
#         VarPowerFlowRefferenceType.d_v_B_t: d_v_t[1],
#         VarPowerFlowRefferenceType.d_v_C_t: d_v_t[2],
#     })
#
#     # ------------------------------------------------------------------
#     # Initialize the dynamic states from the instantaneous voltages.
#     #
#     # Model reason:
#     # Initialization should start from a physically coherent magnetic and
#     # capacitive state without introducing extra assumptions outside this file.
#     #
#     # Algorithm reason:
#     # We compute direct constitutive initial values where possible and leave the
#     # nonlinear fallback conservative when the linear-core flag is disabled.
#     # ------------------------------------------------------------------
#     d_v_leak: list[Expr] = list(d_v_f_w[k] - n_tap * d_v_t_w[k] for k in range(3))
#     z2_sc_pu: Expr = r_sc_pu * r_sc_pu + x_sc_pu * x_sc_pu + c_eps
#
#     init_eqs: Dict[Var, Expr] = dict()
#     for k in range(3):
#         init_eqs[q_f[k]] = xfmr_c_term * v_f[k]
#         init_eqs[q_t[k]] = xfmr_c_term * v_t[k]
#         init_eqs[i_cap_f[k]] = xfmr_c_term * d_v_f[k]
#         init_eqs[i_cap_t[k]] = xfmr_c_term * d_v_t[k]
#         init_eqs[lam_leg[k]] = -d_v_f_w[k] / (omega_base + c_eps)
#         init_eqs[i_loss_leg[k]] = g_core_leg * v_f_w[k]
#
#     init_eqs[i_return_path] = five_leg_selector * (lam_return_total / (2.0 * yoke_linear_coeff + outer_linear_coeff + c_eps)) + three_leg_selector * (lam_return_total / (2.0 * yoke_linear_coeff + c_eps))
#     init_eqs[i_return_total] = five_leg_selector * 2.0 * i_return_path + three_leg_selector * i_return_path
#
#     for k in range(3):
#         init_eqs[i_leg_core[k]] = xfmr_use_linear_core * (lam_leg[k] / (leg_linear_coeff + c_eps)) + (1.0 - xfmr_use_linear_core) * (lam_leg[k] / (xfmr_core_a_prime + c_eps))
#         init_eqs[i_mag[k]] = i_leg_core[k] - i_return_total
#         # Start leakage at zero because no separate steady-state PF-derived EMT
#         # current seed exists for this template path in the current repository.
#         # init_eqs[i_leak[k]] = c0
#         init_eqs[i_leak[k]] = (r_sc_pu * v_leak[k] - l_sigma * d_v_leak[k]) / z2_sc_pu
#         init_eqs[if_act[k]] = i_series_from[k] + i_mag[k] + i_loss_leg[k] + i_cap_f[k]
#         init_eqs[it_act[k]] = -n_tap * i_series_to[k] + i_cap_t[k]
#
#     templ.block.init_eqs = init_eqs
#
#     # Derivative initialization mirrors the transient equations so the explicit
#     # initializer can evaluate the same local physics consistently.
#     diff_init_eqs: Dict[Var, Expr] = dict()
#     for k in range(3):
#         diff_init_eqs[di_leak[k]] = l_inv * (v_leak[k] - r_sc_pu * i_leak[k])
#         diff_init_eqs[dlam_leg[k]] = omega_base * v_f_w[k]
#         diff_init_eqs[dq_f[k]] = i_cap_f[k]
#         diff_init_eqs[dq_t[k]] = i_cap_t[k]
#
#     templ.block.diff_init_eqs = diff_init_eqs
#
#     return templ


def _mat_vec_expr(mat: np.ndarray, vec: list[Expr], c0: Expr) -> list[Expr]:
    """
    Multiply a numerical matrix by a symbolic vector.

    :param mat: Numerical matrix.
    :param vec: Symbolic vector.
    :param c0: Zero-like expression used as the initial accumulator.
    :return: Symbolic matrix-vector product.
    """
    out: list[Expr] = []
    rows, cols = mat.shape
    for i in range(rows):
        rhs = c0
        for j in range(cols):
            coeff = float(mat[i, j])
            if abs(coeff) > 1e-15:
                rhs = rhs + coeff * vec[j]
        out.append(rhs)
    return out


def _project_currents(
    coeffs: list[list[Expr]],
    currents: list[Expr],
    c0: Expr,
) -> list[Expr]:
    """
    Project winding-frame currents to terminal-frame currents.

    The voltage transformation used in the template is
    ``v_w = C^T v_terminal``. The associated current back-projection is
    therefore ``i_terminal = C i_w``.

    :param coeffs: Connection matrix as symbolic expressions.
    :param currents: Winding-frame currents.
    :param c0: Zero-like expression used as the initial accumulator.
    :return: Terminal-frame currents.
    """
    out: list[Expr] = []
    for i in range(3):
        rhs: Expr = c0
        for j in range(3):
            rhs = rhs + coeffs[i][j] * currents[j]
        out.append(rhs)
    return out


def get_xfmr_emt_template(
    vf: VarFactory,
    name: str = "xfmr_emt_template",
) -> EmtModelTemplate:
    """
    Build the EMT DAE template of the ATPDraw/EMTP hybrid transformer style.

    Behaviour and modelling assumptions
    -----------------------------------
    This block represents a three-phase, two-winding transformer using the same
    qualitative decomposition as the ATPDraw XFMR model:

    1. A linear series leakage branch represents the short-circuit path.
       Its parameters are derived from test-report short-circuit data.
    2. A topologically-aware core branch represents the main magnetic path.
       The core may be three-legged or five-legged and uses one magnetic branch
       per leg plus the corresponding return path through yokes and optional
       outer legs.
    3. The core constitutive law can be either linear or Frohlich-type
       nonlinear saturation.
    4. Core losses are represented by linear conductances driven by the same
       internal core excitation voltage that drives the magnetising flux states.
    5. Terminal capacitances are retained explicitly as charges and capacitor
       currents at both transformer terminals.

    Electrical reference frames
    ---------------------------
    The public electrical interface of the block is the terminal abc frame at
    the from and to buses. Internally, the magnetic and leakage equations are
    written in a winding frame. The mapped connection matrices ``C_f`` and
    ``C_t`` are responsible for the conversion between terminal and winding
    variables:

    * ``v_f_w = C_f^T v_f``
    * ``v_t_w = C_t^T v_t``
    * ``i_f = C_f i_w``
    * ``i_t = C_t i_w``

    This means that winding connections and vector-group phase relationships are
    encoded by the mapped connection matrices. For this reason the scalar clock
    number is not consumed directly by the symbolic equations and is not mapped
    as a standalone parameter in this template.

    Internal magnetic excitation
    ----------------------------
    In the ATPDraw XFMR documentation the core is attached to an artificial
    winding and is not modelled as a one-sided shunt on a single physical
    terminal. To remain faithful to that idea within VeraGrid's present
    two-terminal block contract, the core excitation voltage is defined as the
    internal winding voltage shared by both sides after equal splitting of the
    lumped leakage drop:

    * ``v_core = 0.5 * (v_f_w + n_tap * v_t_w)``

    The magnetising flux states are therefore driven by both windings, not only
    by the from side. The corresponding core currents are projected back to both
    terminals in a power-consistent symmetric manner.

    Sign convention
    ---------------
    Branch currents exported through ``if_*`` and ``it_*`` follow VeraGrid's
    branch sign convention: current is positive when it leaves the bus. The
    series leakage branch is assembled accordingly, so in the absence of shunt
    currents and ideal-ratio effects the two terminal currents are equal and
    opposite after referral.

    model structure
    ---------------
    The electrical model is divided into the following parts:

    1. Leakage branch
       - Built from the short-circuit report.
       - Represents winding copper losses and leakage inductance.
       - This branch is the series transfer path between transformer terminals.

    2. Core branch
       - Built from the open-circuit report.
       - Represents magnetizing current and core-loss current.
       - The magnetic return path can represent either a 3-legged or a 5-legged core.

    3. Terminal capacitance
       - Represented as explicit shunt charge states at both terminals.
       - This parameter is template-owned and is not derived from the static
         Transformer2W object.

    Core model options
    ------------------
    The core constitutive law can be selected with the parameter:

        xfmr_use_linear_core

    Its behavior is:

    - xfmr_use_linear_core = 1
        Use the purely linear core model.

    - xfmr_use_linear_core = 0
        Use the automatically generated approximate Frohlich nonlinear core model.

    Linear core mode
    ----------------
    In linear mode, the magnetizing branch uses the parameter:

        xfmr_core_linear_l_pu

    which is mapped from the static transformer object through api_obj_mapping.
    This quantity is derived internally from the open-circuit test data and
    represents the nominal linear magnetizing inductance.

    Automatic Frohlich nonlinear mode
    ---------------------------------
    In nonlinear mode, the model uses the Frohlich-type constitutive law already
    implemented in the template. However, the static Transformer2W object does not
    contain enough information to identify a unique nonlinear saturation curve.
    It only provides one open-circuit operating point through Pfe and I0, which is
    enough to derive a linear slope, but not a full fitted saturation law.

    For that reason, the nonlinear Frohlich coefficients are generated internally
    by the template from:

    1. the nominal linear magnetizing inductance, and
    2. a heuristic knee point.

    The two local template parameters that control this internally generated
    nonlinear curve are:

        xfmr_core_knee_flux_mult
        xfmr_core_knee_current_mult

    Their meaning is:

    - xfmr_core_knee_flux_mult
        Multiplier applied to the nominal peak flux to define the heuristic knee flux.

    - xfmr_core_knee_current_mult
        Multiplier applied to the nominal peak magnetizing current to define the
        heuristic knee current.

    These parameters do not come from the static transformer object. They are
    template-owned modelling parameters stored in event_dict.

    Interpretation
    --------------
    The automatically generated Frohlich curve is an approximate internal model.
    It is consistent with the nominal open-circuit point and provides a reasonable
    saturating core behavior for EMT studies, but it is not a manufacturer-fitted
    saturation curve unless explicit magnetic test data are available.

    Therefore:

    - Linear mode is the safest default.
    - Nonlinear mode gives an approximate saturation behavior without forcing the
      user to manually fit Frohlich coefficients.
    - If detailed magnetic data become available in the future, the template-owned
      Frohlich coefficients can be replaced by user-specified fitted values.

    Parameter ownership
    -------------------
    In particular:

    - The following belong to api_obj_mapping:
        * transformer_rated_power_mva
        * transformer_open_circuit_current_pct
        * transformer_open_circuit_loss_kw
        * transformer_short_circuit_voltage_pct
        * transformer_short_circuit_resistance_pct
        * transformer_tap_ratio
        * transformer_linear_core_inductance_pu_s
        * transformer_from_connection_**
        * transformer_to_connection_**

    - The following belong to event_dict:
        * xfmr_c_term
        * xfmr_use_linear_core
        * xfmr_core_a_prime
        * xfmr_core_b_prime
        * xfmr_core_knee_flux_mult
        * xfmr_core_knee_current_mult
        * xfmr_core_topology_code
        * xfmr_yoke_area_rel
        * xfmr_yoke_length_rel
        * xfmr_outer_leg_area_rel
        * xfmr_outer_leg_length_rel

    :param vf: EMT variable factory.
    :param name: Symbolic model name.
    :return: EMT transformer template.
    """

    templ = EmtModelTemplate()
    templ.tpe = DeviceType.TransformerTypeDevice
    templ.name = name
    templ.block.name = name

    c0: Expr = vf.add_const(0.0)
    c_eps: Expr = vf.add_const(1e-9)
    c_half: Expr = vf.add_const(0.5)
    c_smooth: Expr = vf.add_const(1e-8)

    # ------------------------------------------------------------------
    # Event-driven terminal-voltage derivatives.
    #
    # These are not static transformer parameters. They are part of the EMT
    # interface contract with the network assembly and are therefore stored in
    # event_dict.
    # ------------------------------------------------------------------
    d_v_f: list[Var] = [
        vf.add_var(name=f"d_vf_A_{name}", reference=VarPowerFlowRefferenceType.d_v_A_f),
        vf.add_var(name=f"d_vf_B_{name}", reference=VarPowerFlowRefferenceType.d_v_B_f),
        vf.add_var(name=f"d_vf_C_{name}", reference=VarPowerFlowRefferenceType.d_v_C_f),
    ]
    d_v_t: list[Var] = [
        vf.add_var(name=f"d_vt_A_{name}", reference=VarPowerFlowRefferenceType.d_v_A_t),
        vf.add_var(name=f"d_vt_B_{name}", reference=VarPowerFlowRefferenceType.d_v_B_t),
        vf.add_var(name=f"d_vt_C_{name}", reference=VarPowerFlowRefferenceType.d_v_C_t),
    ]
    # for d_var in d_v_f + d_v_t:
    #     templ.block.event_dict[d_var] = vf.add_const(None)

    # ------------------------------------------------------------------
    # Static transformer parameters mapped from the API object.
    #
    # Only parameters that are directly consumed by the symbolic equations are
    # mapped here.
    # ------------------------------------------------------------------
    omega_base: Var = vf.add_var(name=f"omega_base_{name}")
    xfmr_s_rated_mva: Var = vf.add_var(name=f"xfmr_s_rated_mva_{name}")
    xfmr_oc_current_pct: Var = vf.add_var(name=f"xfmr_oc_current_pct_{name}")
    xfmr_oc_loss_kw: Var = vf.add_var(name=f"xfmr_oc_loss_kw_{name}")
    xfmr_sc_voltage_pct: Var = vf.add_var(name=f"xfmr_sc_voltage_pct_{name}")
    xfmr_sc_resistance_pct: Var = vf.add_var(name=f"xfmr_sc_resistance_pct_{name}")
    xfmr_tap_module: Var = vf.add_var(name=f"xfmr_tap_module_{name}")
    xfmr_core_linear_l_pu: Var = vf.add_var(name=f"xfmr_core_linear_l_pu_{name}")

    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.omega_base] = omega_base
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_rated_power_mva] = xfmr_s_rated_mva
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct] = xfmr_oc_current_pct
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw] = xfmr_oc_loss_kw
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct] = xfmr_sc_voltage_pct
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_short_circuit_resistance_pct] = xfmr_sc_resistance_pct
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_tap_ratio] = xfmr_tap_module
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.transformer_linear_core_inductance_pu_s] = xfmr_core_linear_l_pu

    # ------------------------------------------------------------------
    # Mapped terminal-to-winding connection matrices.
    #
    # These matrices embed the winding connection and phase-shift behaviour.
    # ------------------------------------------------------------------
    cf_enums: list[list[ParamPowerFlowRefferenceType]] = [
        [
            ParamPowerFlowRefferenceType.transformer_from_connection_aa,
            ParamPowerFlowRefferenceType.transformer_from_connection_ab,
            ParamPowerFlowRefferenceType.transformer_from_connection_ac,
        ],
        [
            ParamPowerFlowRefferenceType.transformer_from_connection_ba,
            ParamPowerFlowRefferenceType.transformer_from_connection_bb,
            ParamPowerFlowRefferenceType.transformer_from_connection_bc,
        ],
        [
            ParamPowerFlowRefferenceType.transformer_from_connection_ca,
            ParamPowerFlowRefferenceType.transformer_from_connection_cb,
            ParamPowerFlowRefferenceType.transformer_from_connection_cc,
        ],
    ]
    ct_enums: list[list[ParamPowerFlowRefferenceType]] = [
        [
            ParamPowerFlowRefferenceType.transformer_to_connection_aa,
            ParamPowerFlowRefferenceType.transformer_to_connection_ab,
            ParamPowerFlowRefferenceType.transformer_to_connection_ac,
        ],
        [
            ParamPowerFlowRefferenceType.transformer_to_connection_ba,
            ParamPowerFlowRefferenceType.transformer_to_connection_bb,
            ParamPowerFlowRefferenceType.transformer_to_connection_bc,
        ],
        [
            ParamPowerFlowRefferenceType.transformer_to_connection_ca,
            ParamPowerFlowRefferenceType.transformer_to_connection_cb,
            ParamPowerFlowRefferenceType.transformer_to_connection_cc,
        ],
    ]

    c_f_expr: list[list[Expr]] = []
    c_t_expr: list[list[Expr]] = []
    for i in range(3):
        c_f_row: list[Expr] = []
        c_t_row: list[Expr] = []
        for j in range(3):
            c_f_var: Var = vf.add_var(name=f"xfmr_cf_{i}_{j}_{name}")
            c_t_var: Var = vf.add_var(name=f"xfmr_ct_{i}_{j}_{name}")
            templ.block.api_obj_mapping[cf_enums[i][j]] = c_f_var
            templ.block.api_obj_mapping[ct_enums[i][j]] = c_t_var
            c_f_row.append(c_f_var)
            c_t_row.append(c_t_var)
        c_f_expr.append(c_f_row)
        c_t_expr.append(c_t_row)

    # ------------------------------------------------------------------
    # Local core-topology and relative-geometry parameters.
    #
    # These are not currently available on the static Transformer2W object, so
    # they remain local event_dict parameters.
    # ------------------------------------------------------------------
    xfmr_core_topology_code: Var = vf.add_var(name=f"xfmr_core_topology_code_{name}")
    xfmr_yoke_area_rel: Var = vf.add_var(name=f"xfmr_yoke_area_rel_{name}")
    xfmr_yoke_length_rel: Var = vf.add_var(name=f"xfmr_yoke_length_rel_{name}")
    xfmr_outer_leg_area_rel: Var = vf.add_var(name=f"xfmr_outer_leg_area_rel_{name}")
    xfmr_outer_leg_length_rel: Var = vf.add_var(name=f"xfmr_outer_leg_length_rel_{name}")
    xfmr_c_term: Var = vf.add_var(name=f"xfmr_c_term_{name}")
    xfmr_core_a_prime: Var = vf.add_var(name=f"xfmr_core_a_prime_{name}")
    xfmr_core_b_prime: Var = vf.add_var(name=f"xfmr_core_b_prime_{name}")
    xfmr_use_linear_core: Var = vf.add_var(name=f"xfmr_use_linear_core_{name}")
    xfmr_core_knee_flux_mult: Var = vf.add_var(name=f"xfmr_core_knee_flux_mult_{name}")
    xfmr_core_knee_current_mult: Var = vf.add_var(name=f"xfmr_core_knee_current_mult_{name}")

    templ.block.event_dict[xfmr_core_topology_code] = vf.add_const(3.0)
    templ.block.event_dict[xfmr_yoke_area_rel] = vf.add_const(1.0)
    templ.block.event_dict[xfmr_yoke_length_rel] = vf.add_const(1.0)
    templ.block.event_dict[xfmr_outer_leg_area_rel] = vf.add_const(1.0)
    templ.block.event_dict[xfmr_outer_leg_length_rel] = vf.add_const(1.0)
    templ.block.event_dict[xfmr_c_term] = vf.add_const(0.0)
    # templ.block.event_dict[xfmr_core_a_prime] = vf.add_const(1.0)
    # templ.block.event_dict[xfmr_core_b_prime] = vf.add_const(0.0)
    templ.block.event_dict[xfmr_use_linear_core] = vf.add_const(1.0)
    templ.block.event_dict[xfmr_core_knee_flux_mult] = vf.add_const(1.05)
    templ.block.event_dict[xfmr_core_knee_current_mult] = vf.add_const(8.0)

    # ------------------------------------------------------------------
    # Automatic approximate Frohlich fit from the nominal linear core slope.
    #
    # Model reason:
    # Transformer2W provides only one open-circuit operating point through I0 and Pfe.
    # That is sufficient to derive a linear magnetizing inductance, but not a unique
    # nonlinear saturation curve. We therefore construct an approximate Frohlich law
    # by enforcing:
    #   1) small-signal slope at the origin equal to the linear core slope
    #   2) one heuristic knee point defined by local template parameters
    #
    # Algorithm reason:
    # The fit stays template-owned in event_dict. Only the linear slope is mapped
    # from the static object through api_obj_mapping.
    # ------------------------------------------------------------------
    lambda_nom_peak: Expr = sym.sqrt(vf.add_const(2.0)) * 1.0
    i_nom_peak_from_linear: Expr = lambda_nom_peak / (xfmr_core_linear_l_pu + c_eps)

    a_prime_auto: Expr = 1.0 / (xfmr_core_linear_l_pu + c_eps)

    lambda_knee: Expr = xfmr_core_knee_flux_mult * lambda_nom_peak
    i_knee: Expr = xfmr_core_knee_current_mult * i_nom_peak_from_linear

    b_prime_auto: Expr = sym.max(
        (i_knee / (lambda_knee + c_eps) - a_prime_auto) / (i_knee + c_eps),
        c0,
    )

    templ.block.event_dict[xfmr_core_a_prime] = a_prime_auto
    templ.block.event_dict[xfmr_core_b_prime] = b_prime_auto

    # ------------------------------------------------------------------
    # Leakage-branch parameter derivation from short-circuit test data.
    #
    # ``uk%`` gives the short-circuit impedance magnitude and ``ur%`` gives the
    # resistive component. The EMT assembler already derives ``ur%`` from the
    # static transformer data, so the template consumes that mapped percentage
    # directly and keeps the symbolic model free of discrete fallback logic.
    # ------------------------------------------------------------------
    z_sc_pu: Expr = xfmr_sc_voltage_pct / 100.0
    r_sc_pu: Expr = xfmr_sc_resistance_pct / 100.0
    x_sc_pu: Expr = sym.sqrt(sym.max(z_sc_pu * z_sc_pu - r_sc_pu * r_sc_pu, c0))
    l_sigma: Expr = x_sc_pu / (omega_base + c_eps)
    l_inv: Expr = 1.0 / (l_sigma + c_eps)

    # ------------------------------------------------------------------
    # Open-circuit test parameter derivation for core losses and the linear-core
    # fallback inductance.
    # ------------------------------------------------------------------
    g_core_total: Expr = (xfmr_oc_loss_kw / 1000.0) / (xfmr_s_rated_mva + c_eps)
    g_core_leg: Expr = g_core_total / 3.0

    oc_loss_pu: Expr = (xfmr_oc_loss_kw / 1000.0) / (xfmr_s_rated_mva + c_eps)
    oc_current_pu: Expr = xfmr_oc_current_pct / 100.0
    i_mag_pu: Expr = sym.sqrt(sym.max(oc_current_pu * oc_current_pu - oc_loss_pu * oc_loss_pu, c0))
    lambda_peak: Expr = sym.sqrt(vf.add_const(2.0))
    current_peak: Expr = sym.sqrt(vf.add_const(2.0)) * i_mag_pu
    linear_lm_expr: Expr = lambda_peak / (current_peak + c_eps)

    # ------------------------------------------------------------------
    # Terminal electrical interface variables in the public abc frame.
    # ------------------------------------------------------------------
    v_f: list[Var] = [
        vf.add_var(name=f"vf_A_{name}", reference=VarPowerFlowRefferenceType.vf_A),
        vf.add_var(name=f"vf_B_{name}", reference=VarPowerFlowRefferenceType.vf_B),
        vf.add_var(name=f"vf_C_{name}", reference=VarPowerFlowRefferenceType.vf_C),
    ]
    v_t: list[Var] = [
        vf.add_var(name=f"vt_A_{name}", reference=VarPowerFlowRefferenceType.vt_A),
        vf.add_var(name=f"vt_B_{name}", reference=VarPowerFlowRefferenceType.vt_B),
        vf.add_var(name=f"vt_C_{name}", reference=VarPowerFlowRefferenceType.vt_C),
    ]

    # ------------------------------------------------------------------
    # Dynamic states and their derivatives.
    #
    # ``i_leak``: leakage-branch currents in winding frame.
    # ``lam_leg``: leg flux-linkage states of the core model.
    # ``q_f``, ``q_t``: terminal capacitance charges.
    # ------------------------------------------------------------------
    i_leak: list[Var] = [vf.add_var(name=f"i_leak_{ph}_{name}") for ph in ("A", "B", "C")]
    lam_leg: list[Var] = [vf.add_var(name=f"lam_leg_{ph}_{name}") for ph in ("A", "B", "C")]
    q_f: list[Var] = [vf.add_var(name=f"qf_{ph}_{name}") for ph in ("A", "B", "C")]
    q_t: list[Var] = [vf.add_var(name=f"qt_{ph}_{name}") for ph in ("A", "B", "C")]

    di_leak: list[Var] = [vf.add_diff_var(name=f"di_leak_{ph}_{name}", base_var=i_leak[k]) for k, ph in enumerate(("A", "B", "C"))]
    dlam_leg: list[Var] = [vf.add_diff_var(name=f"dlam_leg_{ph}_{name}", base_var=lam_leg[k]) for k, ph in enumerate(("A", "B", "C"))]
    dq_f: list[Var] = [vf.add_diff_var(name=f"dqf_{ph}_{name}", base_var=q_f[k]) for k, ph in enumerate(("A", "B", "C"))]
    dq_t: list[Var] = [vf.add_diff_var(name=f"dqt_{ph}_{name}", base_var=q_t[k]) for k, ph in enumerate(("A", "B", "C"))]

    # ------------------------------------------------------------------
    # Algebraic variables.
    #
    # ``i_leg_core``: nonlinear magnetising currents in each core leg.
    # ``i_return_path`` and ``i_return_total``: return-path currents of the
    # selected core topology.
    # ``i_mag``: per-leg magnetising current seen by the artificial core winding.
    # ``i_loss_leg``: per-leg core-loss current driven by the internal core
    # voltage.
    # ``i_cap_f`` and ``i_cap_t``: terminal capacitance currents.
    # ``if_act`` and ``it_act``: terminal currents exported to the EMT network.
    # ------------------------------------------------------------------
    i_leg_core: list[Var] = [vf.add_var(name=f"i_leg_core_{ph}_{name}") for ph in ("A", "B", "C")]
    i_mag: list[Var] = [vf.add_var(name=f"i_mag_{ph}_{name}") for ph in ("A", "B", "C")]
    i_loss_leg: list[Var] = [vf.add_var(name=f"i_loss_leg_{ph}_{name}") for ph in ("A", "B", "C")]
    i_cap_f: list[Var] = [vf.add_var(name=f"i_cap_f_{ph}_{name}") for ph in ("A", "B", "C")]
    i_cap_t: list[Var] = [vf.add_var(name=f"i_cap_t_{ph}_{name}") for ph in ("A", "B", "C")]
    if_act: list[Var] = [vf.add_var(name=f"if_{ph}_{name}") for ph in ("A", "B", "C")]
    it_act: list[Var] = [vf.add_var(name=f"it_{ph}_{name}") for ph in ("A", "B", "C")]
    i_return_path: Var = vf.add_var(name=f"i_return_path_{name}")
    i_return_total: Var = vf.add_var(name=f"i_return_total_{name}")

    templ.block.in_vars = v_f + v_t + d_v_f + d_v_t
    templ.block.state_vars = i_leak + lam_leg + q_f + q_t
    templ.block.diff_vars = di_leak + dlam_leg + dq_f + dq_t
    templ.block.algebraic_vars = i_leg_core + [i_return_path, i_return_total] + i_mag + i_loss_leg + i_cap_f + i_cap_t + if_act + it_act

    # ------------------------------------------------------------------
    # Terminal-to-winding voltage transformations.
    # ------------------------------------------------------------------
    c_f_expr_t: list[list[Expr]] = [[c_f_expr[j][i] for j in range(3)] for i in range(3)]
    c_t_expr_t: list[list[Expr]] = [[c_t_expr[j][i] for j in range(3)] for i in range(3)]

    v_f_w: list[Expr] = []
    v_t_w: list[Expr] = []
    d_v_f_w: list[Expr] = []
    d_v_t_w: list[Expr] = []
    for i in range(3):
        expr_vfw: Expr = c0
        expr_vtw: Expr = c0
        expr_dvfw: Expr = c0
        expr_dvtw: Expr = c0
        for j in range(3):
            expr_vfw = expr_vfw + c_f_expr_t[i][j] * v_f[j]
            expr_vtw = expr_vtw + c_t_expr_t[i][j] * v_t[j]
            expr_dvfw = expr_dvfw + c_f_expr_t[i][j] * d_v_f[j]
            expr_dvtw = expr_dvtw + c_t_expr_t[i][j] * d_v_t[j]
        v_f_w.append(expr_vfw)
        v_t_w.append(expr_vtw)
        d_v_f_w.append(expr_dvfw)
        d_v_t_w.append(expr_dvtw)

    # ------------------------------------------------------------------
    # Leakage, core and referred internal voltages.
    #
    # ``v_leak`` is the lumped series drop across the leakage branch.
    # ``v_core`` is the internal excitation voltage of the artificial core
    # winding, obtained by symmetric splitting of the lumped leakage drop.
    # ------------------------------------------------------------------
    n_tap: Expr = xfmr_tap_module
    v_leak: list[Expr] = [v_f_w[k] - n_tap * v_t_w[k] for k in range(3)]
    v_core_w: list[Expr] = [c_half * (v_f_w[k] + n_tap * v_t_w[k]) for k in range(3)]
    d_v_leak: list[Expr] = [d_v_f_w[k] - n_tap * d_v_t_w[k] for k in range(3)]
    d_v_core_w: list[Expr] = [c_half * (d_v_f_w[k] + n_tap * d_v_t_w[k]) for k in range(3)]

    # ------------------------------------------------------------------
    # State equations.
    #
    # 1. Leakage-current dynamics: ``L_sigma di/dt = v_leak - R_sigma i``.
    # 2. Core-flux dynamics: ``d lambda / dt = omega_base * v_core``.
    # 3. Capacitor-charge dynamics: ``dq/dt = i_cap``.
    # ------------------------------------------------------------------
    state_eqs: list[Expr] = []
    for k in range(3):
        state_eqs.append(l_inv * (v_leak[k] - r_sc_pu * i_leak[k]))
    for k in range(3):
        state_eqs.append(omega_base * v_core_w[k])
    for k in range(3):
        state_eqs.append(i_cap_f[k])
    for k in range(3):
        state_eqs.append(i_cap_t[k])
    templ.block.state_eqs = state_eqs

    # ------------------------------------------------------------------
    # Core return-path constitutive equations.
    # ------------------------------------------------------------------
    lam_return_total: Expr = -(lam_leg[0] + lam_leg[1] + lam_leg[2])

    # The topology code is a template-owned discrete modelling choice. The
    # supported values are 3.0 for a three-legged core and 5.0 for a five-
    # legged core, so a simple affine selector is sufficient and avoids
    # symbolic heaviside calls in initialization-generated functions.
    five_leg_selector: Expr = (xfmr_core_topology_code - 3.0) / 2.0
    three_leg_selector: Expr = 1.0 - five_leg_selector

    yoke_area_rel: Expr = xfmr_yoke_area_rel
    yoke_length_rel: Expr = xfmr_yoke_length_rel
    outer_leg_area_rel: Expr = xfmr_outer_leg_area_rel
    outer_leg_length_rel: Expr = xfmr_outer_leg_length_rel

    leg_linear_coeff: Expr = xfmr_use_linear_core * xfmr_core_linear_l_pu + (1.0 - xfmr_use_linear_core) * linear_lm_expr
    yoke_linear_coeff: Expr = leg_linear_coeff * yoke_area_rel / (yoke_length_rel + c_eps)
    outer_linear_coeff: Expr = leg_linear_coeff * outer_leg_area_rel / (outer_leg_length_rel + c_eps)

    yoke_frolich_lam: Expr = yoke_area_rel * i_return_path / (
        xfmr_core_a_prime * yoke_length_rel + xfmr_core_b_prime * sym.sqrt(i_return_path ** 2 + c_smooth) + c_eps
    )
    outer_frolich_lam: Expr = outer_leg_area_rel * i_return_path / (
        xfmr_core_a_prime * outer_leg_length_rel + xfmr_core_b_prime * sym.sqrt(i_return_path ** 2 + c_smooth) + c_eps
    )

    # ------------------------------------------------------------------
    # Projection of leakage currents to the public terminal frame.
    # ------------------------------------------------------------------
    i_series_from: list[Expr] = _project_currents(c_f_expr, i_leak, c0)
    i_series_to: list[Expr] = _project_currents(c_t_expr, i_leak, c0)

    # ------------------------------------------------------------------
    # Projection of magnetic-branch currents to the public terminal frame.
    #
    # The artificial core winding is coupled to both physical sides through a
    # symmetric split of the internal core voltage. To preserve the associated
    # instantaneous power balance, the core currents are split consistently
    # between from and to sides.
    # ------------------------------------------------------------------
    i_core_branch_w: list[Expr] = [i_mag[k] + i_loss_leg[k] for k in range(3)]
    i_core_from_w: list[Expr] = [c_half * i_core_branch_w[k] for k in range(3)]
    i_core_to_w: list[Expr] = [c_half * n_tap * i_core_branch_w[k] for k in range(3)]
    i_core_from_term: list[Expr] = _project_currents(c_f_expr, i_core_from_w, c0)
    i_core_to_term: list[Expr] = _project_currents(c_t_expr, i_core_to_w, c0)

    # ------------------------------------------------------------------
    # Algebraic equations.
    # ------------------------------------------------------------------
    alg_eqs: list[Expr] = []

    # Leg constitutive equations: linear core or Frohlich law.
    for k in range(3):
        linear_leg_eq: Expr = lam_leg[k] - leg_linear_coeff * i_leg_core[k]
        nonlinear_leg_eq: Expr = lam_leg[k] - i_leg_core[k] / (
            xfmr_core_a_prime + xfmr_core_b_prime * sym.sqrt(i_leg_core[k] ** 2 + c_smooth) + c_eps
        )
        alg_eqs.append(xfmr_use_linear_core * linear_leg_eq + (1.0 - xfmr_use_linear_core) * nonlinear_leg_eq)

    # Return-path constitutive equations for three-legged and five-legged cores.
    five_leg_eq_linear: Expr = c_half * lam_return_total - (2.0 * yoke_linear_coeff * i_return_path + outer_linear_coeff * i_return_path)
    five_leg_eq_nonlinear: Expr = c_half * lam_return_total - (2.0 * yoke_frolich_lam + outer_frolich_lam)
    three_leg_eq_linear: Expr = lam_return_total - 2.0 * yoke_linear_coeff * i_return_path
    three_leg_eq_nonlinear: Expr = lam_return_total - 2.0 * yoke_frolich_lam
    alg_eqs.append(
        five_leg_selector * (xfmr_use_linear_core * five_leg_eq_linear + (1.0 - xfmr_use_linear_core) * five_leg_eq_nonlinear)
        + three_leg_selector * (xfmr_use_linear_core * three_leg_eq_linear + (1.0 - xfmr_use_linear_core) * three_leg_eq_nonlinear)
    )
    alg_eqs.append(i_return_total - (five_leg_selector * 2.0 * i_return_path + three_leg_selector * i_return_path))

    # Magnetising current conversion from leg currents to the artificial core
    # winding currents.
    for k in range(3):
        alg_eqs.append(i_mag[k] - (i_leg_core[k] - i_return_total))

    # Core-loss current equations driven by the internal core excitation voltage.
    for k in range(3):
        alg_eqs.append(i_loss_leg[k] - g_core_leg * v_core_w[k])

    # Terminal capacitance constitutive equations.
    for k in range(3):
        alg_eqs.append(i_cap_f[k] - xfmr_c_term * d_v_f[k])
        alg_eqs.append(i_cap_t[k] - xfmr_c_term * d_v_t[k])

    # Charge-voltage relations for the capacitance states.
    for k in range(3):
        alg_eqs.append(q_f[k] - xfmr_c_term * v_f[k])
        alg_eqs.append(q_t[k] - xfmr_c_term * v_t[k])

    # Final terminal-current assembly in VeraGrid sign convention.
    for k in range(3):
        alg_eqs.append(if_act[k] - (i_series_from[k] + i_core_from_term[k] + i_cap_f[k]))
        alg_eqs.append(it_act[k] - (-n_tap * i_series_to[k] + i_core_to_term[k] + i_cap_t[k]))

    templ.block.algebraic_eqs = alg_eqs
    templ.block.out_vars = if_act + it_act + i_mag
    templ.block.name = name

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
        VarPowerFlowRefferenceType.d_v_A_f: d_v_f[0],
        VarPowerFlowRefferenceType.d_v_B_f: d_v_f[1],
        VarPowerFlowRefferenceType.d_v_C_f: d_v_f[2],
        VarPowerFlowRefferenceType.d_v_N_t: None,
        VarPowerFlowRefferenceType.d_v_A_t: d_v_t[0],
        VarPowerFlowRefferenceType.d_v_B_t: d_v_t[1],
        VarPowerFlowRefferenceType.d_v_C_t: d_v_t[2],
    })

    # ------------------------------------------------------------------
    # Initial conditions.
    #
    # The objective is to create a self-consistent initial state for the explicit
    # EMT initializer using the same constitutive relations as the transient
    # model. The leakage branch uses the local RL steady-state relation and the
    # core states are initialized from the internal core excitation voltage, not
    # from one terminal only.
    # ------------------------------------------------------------------
    z2_sc_pu: Expr = r_sc_pu * r_sc_pu + x_sc_pu * x_sc_pu + c_eps

    init_eqs: Dict[Var, Expr] = dict()

    # Capacitor states and capacitor currents.
    for k in range(3):
        init_eqs[q_f[k]] = xfmr_c_term * v_f[k]
        init_eqs[q_t[k]] = xfmr_c_term * v_t[k]
        init_eqs[i_cap_f[k]] = xfmr_c_term * d_v_f[k]
        init_eqs[i_cap_t[k]] = xfmr_c_term * d_v_t[k]

    # Core flux-linkage states from the internal core excitation voltage.
    for k in range(3):
        init_eqs[lam_leg[k]] = -d_v_core_w[k] / (omega_base + c_eps)

    # Core return-path currents from the linearized initial constitutive law.
    init_eqs[i_return_path] = (
        five_leg_selector * (lam_return_total / (2.0 * yoke_linear_coeff + outer_linear_coeff + c_eps))
        + three_leg_selector * (lam_return_total / (2.0 * yoke_linear_coeff + c_eps))
    )
    init_eqs[i_return_total] = five_leg_selector * 2.0 * i_return_path + three_leg_selector * i_return_path

    # Core leg currents and core-loss currents.
    for k in range(3):
        init_eqs[i_leg_core[k]] = (
            xfmr_use_linear_core * (lam_leg[k] / (leg_linear_coeff + c_eps))
            + (1.0 - xfmr_use_linear_core) * (lam_leg[k] / (xfmr_core_a_prime + c_eps))
        )
        init_eqs[i_mag[k]] = i_leg_core[k] - i_return_total
        init_eqs[i_loss_leg[k]] = g_core_leg * v_core_w[k]

    # Leakage-current states from the local RL steady-state relation.
    for k in range(3):
        init_eqs[i_leak[k]] = (r_sc_pu * v_leak[k] - l_sigma * d_v_leak[k]) / z2_sc_pu

    # Final terminal currents.
    for k in range(3):
        init_eqs[if_act[k]] = i_series_from[k] + i_core_from_term[k] + i_cap_f[k]
        init_eqs[it_act[k]] = -n_tap * i_series_to[k] + i_core_to_term[k] + i_cap_t[k]

    templ.block.init_eqs = init_eqs

    # ------------------------------------------------------------------
    # Derivative initial conditions.
    #
    # These mirror the transient equations exactly so that the explicit
    # initializer and the DAE residuals are consistent at the initial point.
    # ------------------------------------------------------------------
    diff_init_eqs: Dict[Var, Expr] = dict()
    for k in range(3):
        diff_init_eqs[di_leak[k]] = l_inv * (v_leak[k] - r_sc_pu * i_leak[k])
        diff_init_eqs[dlam_leg[k]] = omega_base * v_core_w[k]
        diff_init_eqs[dq_f[k]] = i_cap_f[k]
        diff_init_eqs[dq_t[k]] = i_cap_t[k]

    templ.block.diff_init_eqs = diff_init_eqs

    return templ
