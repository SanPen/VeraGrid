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


def _mat_vec_expr(mat: np.ndarray, vec: list[Expr], c0: Expr) -> list[Expr]:
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


def get_xfmr_emt_template(
    vf: VarFactory,
    name: str = "xfmr_emt_template",
) -> EmtModelTemplate:
    """
    Build the local XFMR-style transformer EMT DAE template.

    - leakage and copper losses are separated from the main/core flux path,
    - short-circuit report data parameterize the series leakage branch,
    - open-circuit report data parameterize the core branch,
    - the core branch uses the basic Frohlich ``lambda(i)`` law,
    - core losses remain linear resistive branches,
    - the magnetic return path distinguishes 3-legged and 5-legged stacked cores.

    Static quantities that already exist on ``Transformer2W`` are not sourced from
    ``event_dict``. They are exposed as dynamic block parameters through
    ``api_obj_mapping`` so the EMT assembler can assign them from the static
    transformer object. Only data not stored on ``Transformer2W`` remain in
    ``event_dict``.

    Because ``core_topology`` and the optional relative core geometry are not
    stored on ``Transformer2W`` in the current repository, they remain local
    non-mapped block parameters. The default local topology code is ``3.0`` for a
    three-legged core.

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

    # ------------------------------------------------------------------
    # Create the derivative inputs used by the terminal capacitance path.
    # These are event-driven because they belong to the instantaneous electrical
    # coupling contract, not to the static transformer object.
    # ------------------------------------------------------------------
    d_v_f: list[Var] = list([
        vf.add_var(name=f"d_vf_A_{name}", reference=VarPowerFlowRefferenceType.d_v_A_f),
        vf.add_var(name=f"d_vf_B_{name}", reference=VarPowerFlowRefferenceType.d_v_B_f),
        vf.add_var(name=f"d_vf_C_{name}", reference=VarPowerFlowRefferenceType.d_v_C_f),
    ])
    d_v_t: list[Var] = list([
        vf.add_var(name=f"d_vt_A_{name}", reference=VarPowerFlowRefferenceType.d_v_A_t),
        vf.add_var(name=f"d_vt_B_{name}", reference=VarPowerFlowRefferenceType.d_v_B_t),
        vf.add_var(name=f"d_vt_C_{name}", reference=VarPowerFlowRefferenceType.d_v_C_t),
    ])

    for d_var in d_v_f:
        templ.block.event_dict[d_var] = vf.add_const(None)
    for d_var in d_v_t:
        templ.block.event_dict[d_var] = vf.add_const(None)

    # ------------------------------------------------------------------
    # Create mapped XFMR parameters.
    #
    # Model reason:
    # These quantities are sourced from the static transformer object through the
    # EMT assembler rather than copied into event_dict.
    #
    # Algorithm reason:
    # The variables are registered in api_obj_mapping so the template becomes a
    # pure symbolic consumer of mapped parameters, in the same architectural
    # style as the pi-line EMT template.
    # ------------------------------------------------------------------
    omega_base: Var = vf.add_var(name=f"omega_base_{name}")
    xfmr_s_rated_mva: Var = vf.add_var(name=f"xfmr_s_rated_mva_{name}")
    xfmr_v_hv_ll_kv: Var = vf.add_var(name=f"xfmr_v_hv_ll_kv_{name}")
    xfmr_v_lv_ll_kv: Var = vf.add_var(name=f"xfmr_v_lv_ll_kv_{name}")
    xfmr_vector_group_clock: Var = vf.add_var(name=f"xfmr_vector_group_clock_{name}")
    xfmr_oc_current_pct: Var = vf.add_var(name=f"xfmr_oc_current_pct_{name}")
    xfmr_oc_loss_kw: Var = vf.add_var(name=f"xfmr_oc_loss_kw_{name}")
    xfmr_sc_voltage_pct: Var = vf.add_var(name=f"xfmr_sc_voltage_pct_{name}")
    xfmr_sc_resistance_pct: Var = vf.add_var(name=f"xfmr_sc_resistance_pct_{name}")
    xfmr_sc_loss_kw: Var = vf.add_var(name=f"xfmr_sc_loss_kw_{name}")
    xfmr_tap_module: Var = vf.add_var(name=f"xfmr_tap_module_{name}")
    xfmr_c_term: Var = vf.add_var(name=f"xfmr_c_term_{name}")
    xfmr_core_linear_l_pu: Var = vf.add_var(name=f"xfmr_core_linear_l_pu_{name}")
    xfmr_core_a_prime: Var = vf.add_var(name=f"xfmr_core_a_prime_{name}")
    xfmr_core_b_prime: Var = vf.add_var(name=f"xfmr_core_b_prime_{name}")
    xfmr_use_linear_core: Var = vf.add_var(name=f"xfmr_use_linear_core_{name}")

    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.omega_base] = omega_base
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_s_rated_mva] = xfmr_s_rated_mva
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_v_hv_ll_kv] = xfmr_v_hv_ll_kv
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_v_lv_ll_kv] = xfmr_v_lv_ll_kv
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_vector_group_clock] = xfmr_vector_group_clock
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_oc_current_pct] = xfmr_oc_current_pct
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_oc_loss_kw] = xfmr_oc_loss_kw
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_sc_voltage_pct] = xfmr_sc_voltage_pct
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_sc_resistance_pct] = xfmr_sc_resistance_pct
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_sc_loss_kw] = xfmr_sc_loss_kw
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_tap_module] = xfmr_tap_module
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_c_term] = xfmr_c_term
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_core_linear_l_pu] = xfmr_core_linear_l_pu
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_core_a_prime] = xfmr_core_a_prime
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_core_b_prime] = xfmr_core_b_prime
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.xfmr_use_linear_core] = xfmr_use_linear_core

    cf_enums: list[list[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.xfmr_cf_aa,
            ParamPowerFlowRefferenceType.xfmr_cf_ab,
            ParamPowerFlowRefferenceType.xfmr_cf_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.xfmr_cf_ba,
            ParamPowerFlowRefferenceType.xfmr_cf_bb,
            ParamPowerFlowRefferenceType.xfmr_cf_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.xfmr_cf_ca,
            ParamPowerFlowRefferenceType.xfmr_cf_cb,
            ParamPowerFlowRefferenceType.xfmr_cf_cc,
        ]),
    ])
    ct_enums: list[list[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.xfmr_ct_aa,
            ParamPowerFlowRefferenceType.xfmr_ct_ab,
            ParamPowerFlowRefferenceType.xfmr_ct_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.xfmr_ct_ba,
            ParamPowerFlowRefferenceType.xfmr_ct_bb,
            ParamPowerFlowRefferenceType.xfmr_ct_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.xfmr_ct_ca,
            ParamPowerFlowRefferenceType.xfmr_ct_cb,
            ParamPowerFlowRefferenceType.xfmr_ct_cc,
        ]),
    ])

    c_f_vars: list[list[Var]] = list()
    c_t_eff_vars: list[list[Var]] = list()
    for i in range(3):
        c_f_row: list[Var] = list()
        c_t_row: list[Var] = list()
        for j in range(3):
            c_f_var: Var = vf.add_var(name=f"xfmr_cf_{i}_{j}_{name}")
            c_t_var: Var = vf.add_var(name=f"xfmr_ct_{i}_{j}_{name}")
            templ.block.api_obj_mapping[cf_enums[i][j]] = c_f_var
            templ.block.api_obj_mapping[ct_enums[i][j]] = c_t_var
            c_f_row.append(c_f_var)
            c_t_row.append(c_t_var)
        c_f_vars.append(c_f_row)
        c_t_eff_vars.append(c_t_row)

    # ------------------------------------------------------------------
    # Create non-mapped local core-topology and geometry parameters.
    #
    # Model reason:
    # The present Transformer2W object does not store this data, so there is no
    # static source to connect through api_obj_mapping.
    #
    # Algorithm reason:
    # Keeping these few parameters in event_dict preserves local configurability
    # without creating a duplicate shadow path for data already on Transformer2W.
    # ------------------------------------------------------------------
    xfmr_core_topology_code: Var = vf.add_var(name=f"xfmr_core_topology_code_{name}")
    xfmr_yoke_area_rel: Var = vf.add_var(name=f"xfmr_yoke_area_rel_{name}")
    xfmr_yoke_length_rel: Var = vf.add_var(name=f"xfmr_yoke_length_rel_{name}")
    xfmr_outer_leg_area_rel: Var = vf.add_var(name=f"xfmr_outer_leg_area_rel_{name}")
    xfmr_outer_leg_length_rel: Var = vf.add_var(name=f"xfmr_outer_leg_length_rel_{name}")
    templ.block.event_dict[xfmr_core_topology_code] = vf.add_const(3.0)
    templ.block.event_dict[xfmr_yoke_area_rel] = vf.add_const(1.0)
    templ.block.event_dict[xfmr_yoke_length_rel] = vf.add_const(1.0)
    templ.block.event_dict[xfmr_outer_leg_area_rel] = vf.add_const(1.0)
    templ.block.event_dict[xfmr_outer_leg_length_rel] = vf.add_const(1.0)

    # ------------------------------------------------------------------
    # Derive the leakage parameters directly from the short-circuit report.
    #
    # Model reason:
    # XFMR separates leakage and main flux. The leakage branch must come from
    # short-circuit data, while saturation must remain only in the core model.
    #
    # Algorithm reason:
    # We compute z_sc, r_sc, and x_sc in per unit exactly in the paper/report
    # style, then convert x_sc into a symbolic leakage inductance for the EMT
    # differential equation. The single two-winding series branch preserves the
    # existing VeraGrid block contract, so the equal resistance sharing is
    # represented implicitly by this one equivalent branch.
    # ------------------------------------------------------------------
    z_sc_pu: Expr = xfmr_sc_voltage_pct / 100.0
    r_sc_pu: Expr = xfmr_sc_resistance_pct / 100.0
    x_sc_pu: Expr = sym.sqrt(sym.max(z_sc_pu * z_sc_pu - r_sc_pu * r_sc_pu, c0))
    l_sigma: Expr = x_sc_pu / (omega_base + c_eps)
    l_inv: Expr = 1.0 / (l_sigma + c_eps)

    # ------------------------------------------------------------------
    # Derive the linear core-loss conductance from the rated open-circuit loss.
    #
    # Model reason:
    # The task explicitly keeps core losses linear and resistive even when the
    # magnetizing inductive branch is nonlinear.
    #
    # Algorithm reason:
    # We convert rated OC loss into a total per-unit conductance and distribute
    # it evenly across the three legs in this local implementation so the model
    # stays compatible with the current energized-side current injection layout.
    # ------------------------------------------------------------------
    g_core_total: Expr = (xfmr_oc_loss_kw / 1000.0) / (xfmr_s_rated_mva + c_eps)
    g_core_leg: Expr = g_core_total / 3.0

    # ------------------------------------------------------------------
    # Recover the linear single-point open-circuit core slope from mapped test
    # report values. This preserves the paper's one-point linear-core fallback
    # without touching the static transformer object in the template.
    # ------------------------------------------------------------------
    oc_loss_pu: Expr = (xfmr_oc_loss_kw / 1000.0) / (xfmr_s_rated_mva + c_eps)
    oc_current_pu: Expr = xfmr_oc_current_pct / 100.0
    i_mag_pu: Expr = sym.sqrt(sym.max(oc_current_pu * oc_current_pu - oc_loss_pu * oc_loss_pu, c0))
    lambda_peak: Expr = sym.sqrt(2.0) * 1.0
    current_peak: Expr = sym.sqrt(2.0) * i_mag_pu
    linear_lm_expr: Expr = lambda_peak / (current_peak + c_eps)

    # Build matrix expressions from the mapped connection coefficients.
    c_f_expr: list[list[Expr]] = list(c_f_vars)
    c_t_eff_expr: list[list[Expr]] = list(c_t_eff_vars)

    # ------------------------------------------------------------------
    # Create the electrical interface variables.
    #
    # Model reason:
    # These are the abc terminal voltages seen by the EMT network solver.
    #
    # Algorithm reason:
    # They keep the same public mapping used elsewhere in VeraGrid, so callers
    # and nodal KCL stamping continue to work unchanged.
    # ------------------------------------------------------------------
    v_f: list[Var] = list([
        vf.add_var(name=f"vf_A_{name}", reference=VarPowerFlowRefferenceType.vf_A),
        vf.add_var(name=f"vf_B_{name}", reference=VarPowerFlowRefferenceType.vf_B),
        vf.add_var(name=f"vf_C_{name}", reference=VarPowerFlowRefferenceType.vf_C),
    ])
    v_t: list[Var] = list([
        vf.add_var(name=f"vt_A_{name}", reference=VarPowerFlowRefferenceType.vt_A),
        vf.add_var(name=f"vt_B_{name}", reference=VarPowerFlowRefferenceType.vt_B),
        vf.add_var(name=f"vt_C_{name}", reference=VarPowerFlowRefferenceType.vt_C),
    ])

    # ------------------------------------------------------------------
    # Differential variables.
    #
    # Model reason:
    # - i_leak stores the leakage-channel current dynamics.
    # - lam_leg stores the main-flux linkage of each core leg.
    # - q_f and q_t store the terminal capacitor charges.
    #
    # Algorithm reason:
    # Using leg flux linkages as explicit states lets the DAE express the core
    # nonlinearity algebraically while keeping Faraday's law in differential
    # form through d(lambda)/dt = omega * v in per-unit sinusoidal scaling.
    # ------------------------------------------------------------------
    i_leak: list[Var] = list(vf.add_var(name=f"i_leak_{ph}_{name}") for ph in ("A", "B", "C"))
    lam_leg: list[Var] = list(vf.add_var(name=f"lam_leg_{ph}_{name}") for ph in ("A", "B", "C"))
    q_f: list[Var] = list(vf.add_var(name=f"qf_{ph}_{name}") for ph in ("A", "B", "C"))
    q_t: list[Var] = list(vf.add_var(name=f"qt_{ph}_{name}") for ph in ("A", "B", "C"))

    di_leak: list[Var] = list(vf.add_diff_var(name=f"di_leak_{ph}_{name}", base_var=i_leak[k]) for k, ph in enumerate(("A", "B", "C")))
    dlam_leg: list[Var] = list(vf.add_diff_var(name=f"dlam_leg_{ph}_{name}", base_var=lam_leg[k]) for k, ph in enumerate(("A", "B", "C")))
    dq_f: list[Var] = list(vf.add_diff_var(name=f"dqf_{ph}_{name}", base_var=q_f[k]) for k, ph in enumerate(("A", "B", "C")))
    dq_t: list[Var] = list(vf.add_diff_var(name=f"dqt_{ph}_{name}", base_var=q_t[k]) for k, ph in enumerate(("A", "B", "C")))

    # ------------------------------------------------------------------
    # Algebraic variables.
    #
    # Model reason:
    # - i_leg_core are the nonlinear leg magnetizing currents.
    # - i_return_path / i_return_total are the return-path currents that enforce
    #   the chosen 3-legged or 5-legged core topology.
    # - i_mag are the phase magnetizing currents injected into the electrical side.
    # - i_loss_leg are the linear core-loss currents.
    # - i_cap_f / i_cap_t are capacitor currents.
    # - if_act / it_act are the final terminal currents stamped into network KCL.
    #
    # Algorithm reason:
    # The Frohlich law is imposed as algebraic constitutive equations, which is
    # the cleanest way to keep the model as a symbolic DAE block.
    # ------------------------------------------------------------------
    i_leg_core: list[Var] = list(vf.add_var(name=f"i_leg_core_{ph}_{name}") for ph in ("A", "B", "C"))
    i_mag: list[Var] = list(vf.add_var(name=f"i_mag_{ph}_{name}") for ph in ("A", "B", "C"))
    i_loss_leg: list[Var] = list(vf.add_var(name=f"i_loss_leg_{ph}_{name}") for ph in ("A", "B", "C"))
    i_cap_f: list[Var] = list(vf.add_var(name=f"i_cap_f_{ph}_{name}") for ph in ("A", "B", "C"))
    i_cap_t: list[Var] = list(vf.add_var(name=f"i_cap_t_{ph}_{name}") for ph in ("A", "B", "C"))
    if_act: list[Var] = list(vf.add_var(name=f"if_{ph}_{name}") for ph in ("A", "B", "C"))
    it_act: list[Var] = list(vf.add_var(name=f"it_{ph}_{name}") for ph in ("A", "B", "C"))

    i_return_path: Var = vf.add_var(name=f"i_return_path_{name}")
    i_return_total: Var = vf.add_var(name=f"i_return_total_{name}")

    templ.block.in_vars = v_f + v_t + d_v_f + d_v_t
    templ.block.state_vars = i_leak + lam_leg + q_f + q_t
    templ.block.diff_vars = di_leak + dlam_leg + dq_f + dq_t
    templ.block.algebraic_vars = i_leg_core + list([i_return_path, i_return_total]) + i_mag + i_loss_leg + i_cap_f + i_cap_t + if_act + it_act

    c_f_expr_t: list[list[Expr]] = list(list(c_f_expr[j][i] for j in range(3)) for i in range(3))
    c_t_expr_t: list[list[Expr]] = list(list(c_t_eff_expr[j][i] for j in range(3)) for i in range(3))

    v_f_w: list[Expr] = list()
    v_t_w: list[Expr] = list()
    d_v_f_w: list[Expr] = list()
    d_v_t_w: list[Expr] = list()
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

    n_tap: Expr = xfmr_tap_module
    v_leak: list[Expr] = list(v_f_w[k] - n_tap * v_t_w[k] for k in range(3))

    # Build the leakage-current and flux-linkage differential equations.
    #
    # Model reason:
    # The leakage branch is linear and separate from the saturable core branch.
    # The leg flux states integrate the winding-side induced voltages.
    #
    # Algorithm reason:
    # The state_eqs list must follow the same order as state_vars.
    state_eqs: list[Expr] = list()
    for k in range(3):
        state_eqs.append(l_inv * (v_leak[k] - r_sc_pu * i_leak[k]))
    for k in range(3):
        state_eqs.append(omega_base * v_f_w[k])
    for k in range(3):
        state_eqs.append(i_cap_f[k])
    for k in range(3):
        state_eqs.append(i_cap_t[k])
    templ.block.state_eqs = state_eqs

    # ------------------------------------------------------------------
    # Build the magnetic return-path equations.
    #
    # Model reason:
    # This is where the model becomes topologically aware instead of collapsing
    # everything into one shunt branch. The sum of the three leg fluxes must
    # close through the yokes and, for a 5-legged core, through the two outer
    # return limbs.
    #
    # Algorithm reason:
    # We write the return path as algebraic lambda(i) equations so that the
    # selected topology changes only the constitutive relation, not the external
    # electrical contract of the template.
    # ------------------------------------------------------------------
    lam_return_total: Expr = -(lam_leg[0] + lam_leg[1] + lam_leg[2])
    five_leg_selector: Expr = sym.heaviside(xfmr_core_topology_code - 4.0)
    three_leg_selector: Expr = 1.0 - five_leg_selector

    yoke_area_rel: Expr = xfmr_yoke_area_rel
    yoke_length_rel: Expr = xfmr_yoke_length_rel
    outer_leg_area_rel: Expr = xfmr_outer_leg_area_rel
    outer_leg_length_rel: Expr = xfmr_outer_leg_length_rel

    leg_linear_coeff: Expr = xfmr_use_linear_core * xfmr_core_linear_l_pu + (1.0 - xfmr_use_linear_core) * linear_lm_expr
    yoke_linear_coeff: Expr = leg_linear_coeff * yoke_area_rel / (yoke_length_rel + c_eps)
    outer_linear_coeff: Expr = leg_linear_coeff * outer_leg_area_rel / (outer_leg_length_rel + c_eps)

    yoke_frolich_lam: Expr = yoke_area_rel * i_return_path / (xfmr_core_a_prime * yoke_length_rel + xfmr_core_b_prime * sym.abs(i_return_path) + c_eps)
    outer_frolich_lam: Expr = outer_leg_area_rel * i_return_path / (xfmr_core_a_prime * outer_leg_length_rel + xfmr_core_b_prime * sym.abs(i_return_path) + c_eps)

    i_series_from: list[Expr] = list()
    i_series_to: list[Expr] = list()
    for i in range(3):
        expr_if: Expr = c0
        expr_it: Expr = c0
        for j in range(3):
            expr_if = expr_if + c_f_expr[i][j] * i_leak[j]
            expr_it = expr_it + c_t_eff_expr[i][j] * i_leak[j]
        i_series_from.append(expr_if)
        i_series_to.append(expr_it)

    # Collect algebraic equations in the same order as algebraic_vars.
    alg_eqs: list[Expr] = list()

    for k in range(3):
        # Main leg constitutive law.
        #
        # In the single-point default path the law is linear, matching the paper.
        # If callers later override the fitted a' and b' parameters and disable
        # the linear flag, this equation becomes the basic Fr"ohlich law.
        linear_leg_eq: Expr = lam_leg[k] - leg_linear_coeff * i_leg_core[k]
        nonlinear_leg_eq: Expr = lam_leg[k] - i_leg_core[k] / (xfmr_core_a_prime + xfmr_core_b_prime * sym.abs(i_leg_core[k]) + c_eps)
        alg_eqs.append(xfmr_use_linear_core * linear_leg_eq + (1.0 - xfmr_use_linear_core) * nonlinear_leg_eq)

    five_leg_eq_linear: Expr = 0.5 * lam_return_total - (2.0 * yoke_linear_coeff * i_return_path + outer_linear_coeff * i_return_path)
    five_leg_eq_nonlinear: Expr = 0.5 * lam_return_total - (2.0 * yoke_frolich_lam + outer_frolich_lam)
    three_leg_eq_linear: Expr = lam_return_total - 2.0 * yoke_linear_coeff * i_return_path
    three_leg_eq_nonlinear: Expr = lam_return_total - 2.0 * yoke_frolich_lam

    alg_eqs.append(
        five_leg_selector * (xfmr_use_linear_core * five_leg_eq_linear + (1.0 - xfmr_use_linear_core) * five_leg_eq_nonlinear)
        + three_leg_selector * (xfmr_use_linear_core * three_leg_eq_linear + (1.0 - xfmr_use_linear_core) * three_leg_eq_nonlinear)
    )
    alg_eqs.append(i_return_total - (five_leg_selector * 2.0 * i_return_path + three_leg_selector * i_return_path))

    for k in range(3):
        # Convert magnetic branch currents into electrical magnetizing current at
        # each phase. The return-path current subtracts from each leg current.
        alg_eqs.append(i_mag[k] - (i_leg_core[k] - i_return_total))

    for k in range(3):
        # Linear core-loss branch in parallel with the inductive core branch.
        alg_eqs.append(i_loss_leg[k] - g_core_leg * v_f_w[k])

    for k in range(3):
        # Capacitor constitutive equations using supplied bus voltage derivatives.
        alg_eqs.append(i_cap_f[k] - xfmr_c_term * d_v_f[k])
        alg_eqs.append(i_cap_t[k] - xfmr_c_term * d_v_t[k])

    for k in range(3):
        # Charge/voltage relations for the retained terminal capacitance states.
        alg_eqs.append(q_f[k] - xfmr_c_term * v_f[k])
        alg_eqs.append(q_t[k] - xfmr_c_term * v_t[k])

    for k in range(3):
        # Final terminal current assembly.
        #
        # From-side current includes leakage, magnetizing, core-loss, and local
        # terminal capacitance currents. To-side current includes the referred
        # leakage current plus the to-side terminal capacitance current.
        alg_eqs.append(if_act[k] - (i_series_from[k] + i_mag[k] + i_loss_leg[k] + i_cap_f[k]))
        alg_eqs.append(it_act[k] - (-n_tap * i_series_to[k] + i_cap_t[k]))

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
    # Initialize the dynamic states from the instantaneous voltages.
    #
    # Model reason:
    # Initialization should start from a physically coherent magnetic and
    # capacitive state without introducing extra assumptions outside this file.
    #
    # Algorithm reason:
    # We compute direct constitutive initial values where possible and leave the
    # nonlinear fallback conservative when the linear-core flag is disabled.
    # ------------------------------------------------------------------
    init_eqs: Dict[Var, Expr] = dict()
    for k in range(3):
        init_eqs[q_f[k]] = xfmr_c_term * v_f[k]
        init_eqs[q_t[k]] = xfmr_c_term * v_t[k]
        init_eqs[i_cap_f[k]] = xfmr_c_term * d_v_f[k]
        init_eqs[i_cap_t[k]] = xfmr_c_term * d_v_t[k]
        init_eqs[lam_leg[k]] = -d_v_f_w[k] / (omega_base + c_eps)
        init_eqs[i_loss_leg[k]] = g_core_leg * v_f_w[k]

    init_eqs[i_return_path] = five_leg_selector * (lam_return_total / (2.0 * yoke_linear_coeff + outer_linear_coeff + c_eps)) + three_leg_selector * (lam_return_total / (2.0 * yoke_linear_coeff + c_eps))
    init_eqs[i_return_total] = five_leg_selector * 2.0 * i_return_path + three_leg_selector * i_return_path

    for k in range(3):
        init_eqs[i_leg_core[k]] = xfmr_use_linear_core * (lam_leg[k] / (leg_linear_coeff + c_eps)) + (1.0 - xfmr_use_linear_core) * (lam_leg[k] / (xfmr_core_a_prime + c_eps))
        init_eqs[i_mag[k]] = i_leg_core[k] - i_return_total
        # Start leakage at zero because no separate steady-state PF-derived EMT
        # current seed exists for this template path in the current repository.
        init_eqs[i_leak[k]] = c0
        init_eqs[if_act[k]] = i_series_from[k] + i_mag[k] + i_loss_leg[k] + i_cap_f[k]
        init_eqs[it_act[k]] = -n_tap * i_series_to[k] + i_cap_t[k]

    templ.block.init_eqs = init_eqs

    # Derivative initialization mirrors the transient equations so the explicit
    # initializer can evaluate the same local physics consistently.
    diff_init_eqs: Dict[Var, Expr] = dict()
    for k in range(3):
        diff_init_eqs[di_leak[k]] = l_inv * (v_leak[k] - r_sc_pu * i_leak[k])
        diff_init_eqs[dlam_leg[k]] = omega_base * v_f_w[k]
        diff_init_eqs[dq_f[k]] = i_cap_f[k]
        diff_init_eqs[dq_t[k]] = i_cap_t[k]

    templ.block.diff_init_eqs = diff_init_eqs

    return templ
