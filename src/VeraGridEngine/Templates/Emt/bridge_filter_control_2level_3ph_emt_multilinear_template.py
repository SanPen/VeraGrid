# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, Tuple

import numpy as np

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.bridge_filter_2level_3ph_emt_multilinear_template import get_bridge_filter_2level_3ph_emt_multilinear_template
from VeraGridEngine.Utils.Symbolic.block import Block, build_name_to_var_lookup
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import hard_saturation
from VeraGridEngine.enumerations import DeviceType


def _build_bridge_filter_current_control_block(vf: VarFactory, name: str) -> Block:
    """
    Build one dq0 current controller matched to the switched bridge + filter plant.

    The switched plant is built from phase-domain RL equations and then measured in
    dq0. Under the retained ``sin / -cos`` convention used across the bridge/filter
    templates, the phase-domain dynamics induce the opposite dq cross-coupling signs
    to the validated pseudo-EMT branch model. Reusing the pseudo inner loop here
    therefore overdrives the d-axis command and collapses the residual q-axis
    headroom after handover.

    This block keeps the same saturation and nominal-voltage logic as the pseudo
    controller, but flips only the dq decoupling signs so the inner loop matches the
    actual switched abc plant.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name suffix.
    :return: dq0 current-controller block.
    """
    v_d: Var = vf.add_var(name=f"v_d_inner_in_{name}")
    v_q: Var = vf.add_var(name=f"v_q_inner_in_{name}")
    v_0: Var = vf.add_var(name=f"v_0_inner_in_{name}")
    i_d: Var = vf.add_var(name=f"i_d_inner_in_{name}")
    i_q: Var = vf.add_var(name=f"i_q_inner_in_{name}")
    i_0: Var = vf.add_var(name=f"i_0_inner_in_{name}")
    omega_pll: Var = vf.add_var(name=f"omega_pll_inner_in_{name}")
    omega_base: Var = vf.add_var(name=f"omega_base_inner_in_{name}")
    R_f: Var = vf.add_var(name=f"R_eq_inner_in_{name}")
    L_f: Var = vf.add_var(name=f"L_eq_inner_in_{name}")
    i_0_ref: Var = vf.add_var(name=f"i_0_ref_inner_in_{name}")
    i_d_ref: Var = vf.add_var(name=f"i_d_ref_inner_in_{name}")
    i_q_ref: Var = vf.add_var(name=f"i_q_ref_inner_in_{name}")
    i_kp: Var = vf.add_var(name=f"i_kp_inner_in_{name}")
    i_ki: Var = vf.add_var(name=f"i_ki_inner_in_{name}")
    aw_gain: Var = vf.add_var(name=f"aw_gain_inner_in_{name}")
    m_max: Var = vf.add_var(name=f"m_max_inner_in_{name}")
    Vdc_ref: Var = vf.add_var(name=f"Vdc_ref_inner_in_{name}")
    v_dc: Var = vf.add_var(name=f"v_dc_inner_in_{name}")
    vdc_floor: Var = vf.add_var(name=f"vdc_floor_inner_in_{name}")
    sbase: Var = vf.add_var(name=f"sbase_inner_in_{name}")
    P_ref: Var = vf.add_var(name=f"P_ref_inner_in_{name}")
    Q_ref: Var = vf.add_var(name=f"Q_ref_inner_in_{name}")
    P_loss0: Var = vf.add_var(name=f"P_loss0_inner_in_{name}")
    Vpk: Var = vf.add_var(name=f"Vpk_inner_in_{name}")

    xi_id: Var = vf.add_var(name=f"xi_id_{name}")
    xi_iq: Var = vf.add_var(name=f"xi_iq_{name}")
    xi_i0: Var = vf.add_var(name=f"xi_i0_{name}")
    d_xi_id: Var = vf.add_diff_var(name=f"d_xi_id_{name}", base_var=xi_id)
    d_xi_iq: Var = vf.add_diff_var(name=f"d_xi_iq_{name}", base_var=xi_iq)
    d_xi_i0: Var = vf.add_diff_var(name=f"d_xi_i0_{name}", base_var=xi_i0)

    v_pi_d_u: Var = vf.add_var(name=f"v_pi_d_u_{name}")
    v_pi_q_u: Var = vf.add_var(name=f"v_pi_q_u_{name}")
    v_pi_0_u: Var = vf.add_var(name=f"v_pi_0_u_{name}")
    v_cmd_d_u: Var = vf.add_var(name=f"v_cmd_d_u_{name}")
    v_cmd_q_u: Var = vf.add_var(name=f"v_cmd_q_u_{name}")
    v_cmd_0_u: Var = vf.add_var(name=f"v_cmd_0_u_{name}")
    k_v_conv: Var = vf.add_var(name=f"k_v_conv_{name}")
    v_lim: Var = vf.add_var(name=f"v_lim_{name}")
    v_cmd_d: Var = vf.add_var(name=f"v_cmd_d_{name}")
    v_cmd_q: Var = vf.add_var(name=f"v_cmd_q_{name}")
    v_cmd_0: Var = vf.add_var(name=f"v_cmd_0_{name}")
    v_d_cap_out: Var = vf.add_var(name=f"v_d_cap_{name}")
    v_d_cap_mode: Var = vf.add_var(name=f"v_d_cap_mode_{name}")
    v_q_cap: Var = vf.add_var(name=f"v_q_cap_{name}")
    v_q_cap_aux: Var = vf.add_var(name=f"v_q_cap_aux_{name}")
    v_0_cap: Var = vf.add_var(name=f"v_0_cap_{name}")
    v_0_cap_aux: Var = vf.add_var(name=f"v_0_cap_aux_{name}")
    v_lim_aux: Var = vf.add_var(name=f"v_lim_aux_{name}")
    v_cmd_d_aux: Var = vf.add_var(name=f"v_cmd_d_aux_{name}")
    v_cmd_q_aux: Var = vf.add_var(name=f"v_cmd_q_aux_{name}")
    v_cmd_norm: Var = vf.add_var(name=f"v_cmd_norm_{name}")
    v_cmd_norm_aux: Var = vf.add_var(name=f"v_cmd_norm_aux_{name}")
    v_cmd_d0_aux: Var = vf.add_var(name=f"v_cmd_d0_aux_{name}")
    v_cmd_q0_aux: Var = vf.add_var(name=f"v_cmd_q0_aux_{name}")

    eps: Const = Const(1.0e-10)
    c0: Const = Const(0.0)
    c23: Const = Const(2.0 / 3.0)
    v_dc_eff: Expr = sym.max(v_dc, vdc_floor)
    omega_ratio: Expr = omega_pll / (omega_base + eps)
    i_d0: Expr = c23 * ((P_ref / sbase) + (P_loss0 / sbase)) / (Vpk + eps)
    i_q0: Expr = c23 * (Q_ref / sbase) / (Vpk + eps)
    v_cmd_d0: Expr = Vpk - R_f * i_d0 - L_f * i_q0
    v_cmd_q0: Expr = -R_f * i_q0 + L_f * i_d0
    v_lim_sq_expr: Expr = v_lim * v_lim_aux
    v_cmd_d_sq_expr: Expr = v_cmd_d * v_cmd_d_aux
    v_cmd_q_sq_expr: Expr = v_cmd_q * v_cmd_q_aux
    v_cmd_d0_sq_expr: Expr = v_cmd_d0 * v_cmd_d0_aux
    v_cmd_q0_sq_expr: Expr = v_cmd_q0 * v_cmd_q0_aux
    v_q_cap_rhs: Expr = sym.max(v_lim_sq_expr - v_cmd_d_sq_expr, eps)
    v_0_cap_rhs: Expr = sym.max((v_lim_sq_expr - v_cmd_d_sq_expr - v_cmd_q_sq_expr) / Const(3.0), eps / Const(3.0))

    return Block(
        state_eqs=list([
            # The d-axis current integrator accumulates the d-axis current error plus anti-windup feedback.
            i_ki * ((i_d_ref - i_d) + aw_gain * (v_cmd_d - v_cmd_d_u)),
            # The q-axis current integrator accumulates the q-axis current error plus anti-windup feedback.
            i_ki * ((i_q_ref - i_q) + aw_gain * (v_cmd_q - v_cmd_q_u)),
            # The zero-sequence current integrator accumulates the zero-sequence current error plus anti-windup feedback.
            i_ki * ((i_0_ref - i_0) + aw_gain * (v_cmd_0 - v_cmd_0_u)),
        ]),
        state_vars=list([xi_id, xi_iq, xi_i0]),
        diff_vars=list([d_xi_id, d_xi_iq, d_xi_i0]),
        algebraic_eqs=list([
            v_pi_d_u - (i_kp * (i_d_ref - i_d) + xi_id),
            v_pi_q_u - (i_kp * (i_q_ref - i_q) + xi_iq),
            v_pi_0_u - (i_kp * (i_0_ref - i_0) + xi_i0),
            # The switched abc RL plant induces the opposite dq cross-coupling signs to the pseudo
            # dq branch, so the decoupling terms must be flipped here to recover the same low-
            # frequency closed-loop behaviour after handover.
            v_cmd_d_u - (v_d - R_f * i_d - omega_ratio * L_f * i_q - v_pi_d_u),
            v_cmd_q_u - (v_q - R_f * i_q + omega_ratio * L_f * i_d - v_pi_q_u),
            v_cmd_0_u - (v_0 - R_f * i_0 - v_pi_0_u),
            v_cmd_d0_aux - v_cmd_d0,
            v_cmd_q0_aux - v_cmd_q0,
            v_cmd_norm * v_cmd_norm_aux - (v_cmd_d0_sq_expr + v_cmd_q0_sq_expr + eps),
            v_cmd_norm - v_cmd_norm_aux,
            k_v_conv * (m_max * (Vdc_ref + eps)) - v_cmd_norm,
            v_lim - (k_v_conv * m_max * v_dc_eff),
            v_lim_aux - v_lim,
            v_cmd_d_aux - v_cmd_d,
            v_cmd_q_aux - v_cmd_q,
            v_q_cap * v_q_cap_aux - v_q_cap_rhs,
            v_q_cap - v_q_cap_aux,
            v_0_cap * v_0_cap_aux - v_0_cap_rhs,
            v_0_cap - v_0_cap_aux,
            v_d_cap_out - v_d_cap_mode,
            v_cmd_d - v_d_cap_out,
            v_cmd_q - sym.hard_sat(v_cmd_q_u, -v_q_cap, v_q_cap),
            v_cmd_0 - sym.hard_sat(v_cmd_0_u, -v_0_cap, v_0_cap),
        ]),
        algebraic_vars=list([
            v_pi_d_u, v_pi_q_u, v_pi_0_u,
            v_cmd_d_u, v_cmd_q_u, v_cmd_0_u,
            k_v_conv, v_lim,
            v_lim_aux, v_cmd_d_aux, v_cmd_q_aux,
            v_cmd_norm, v_cmd_norm_aux, v_cmd_d0_aux, v_cmd_q0_aux,
            v_q_cap, v_q_cap_aux, v_0_cap, v_0_cap_aux,
            v_d_cap_out, v_cmd_d, v_cmd_q, v_cmd_0,
        ]),
        mode_dict=dict([
            (v_d_cap_mode, c0),
        ]),
        init_eqs=dict([
            (xi_id, c0),
            (xi_iq, c0),
            (xi_i0, c0),
            (v_pi_d_u, c0),
            (v_pi_q_u, c0),
            (v_pi_0_u, c0),
            (v_cmd_d_u, v_cmd_d0),
            (v_cmd_q_u, v_cmd_q0),
            (v_cmd_0_u, c0),
            (v_cmd_norm, sym.sqrt(v_cmd_d0 * v_cmd_d0 + v_cmd_q0 * v_cmd_q0 + eps)),
            (v_cmd_norm_aux, sym.sqrt(v_cmd_d0 * v_cmd_d0 + v_cmd_q0 * v_cmd_q0 + eps)),
            (v_cmd_d0_aux, v_cmd_d0),
            (v_cmd_q0_aux, v_cmd_q0),
            (k_v_conv, v_cmd_norm / (m_max * (Vdc_ref + eps))),
            (v_lim, k_v_conv * m_max * v_dc_eff),
            (v_lim_aux, v_lim),
            (v_cmd_d_aux, v_cmd_d),
            (v_cmd_q_aux, v_cmd_q),
            (v_q_cap, sym.sqrt(v_q_cap_rhs)),
            (v_q_cap_aux, sym.sqrt(v_q_cap_rhs)),
            (v_0_cap, sym.sqrt(v_0_cap_rhs)),
            (v_0_cap_aux, sym.sqrt(v_0_cap_rhs)),
            (v_d_cap_out, sym.hard_sat(v_cmd_d_u, -v_lim, v_lim)),
            (v_cmd_d, v_cmd_d0),
            (v_cmd_q, v_cmd_q0),
            (v_cmd_0, c0),
        ]),
        diff_init_eqs=dict([
            (d_xi_id, c0),
            (d_xi_iq, c0),
            (d_xi_i0, c0),
        ]),
        in_vars=list([v_d, v_q, v_0, i_d, i_q, i_0, omega_pll, omega_base, R_f, L_f, i_0_ref, i_d_ref, i_q_ref, i_kp, i_ki, aw_gain, m_max, Vdc_ref, v_dc, vdc_floor, sbase, P_ref, Q_ref, P_loss0, Vpk]),
        out_vars=list([v_cmd_d, v_cmd_q, v_cmd_0, k_v_conv]),
        procedural_logic=list([
            hard_saturation(
                output=v_d_cap_mode,
                u=v_cmd_d_u,
                u_min=-v_lim,
                u_max=v_lim,
                name=f"v_d_cap_sat_sample_{name}",
            ),
        ]),
        name=f"{name}_current_ctrl",
    )


def _build_bridge_filter_pll_block(vf: VarFactory, name: str) -> Block:
    """
    Build the SRF-PLL used by the switched bridge/filter/control template.

    The switched bridge/filter/control stack keeps its own local copy of the PLL
    helper so this template does not depend on another converter template module.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name suffix.
    :return: PLL block.
    """
    v_q: Var = vf.add_var(name=f"v_q_pll_in_{name}")
    omega_base: Var = vf.add_var(name=f"omega_base_pll_in_{name}")
    pll_kp: Var = vf.add_var(name=f"pll_kp_in_{name}")
    pll_ki: Var = vf.add_var(name=f"pll_ki_in_{name}")
    phi_v: Var = vf.add_var(name=f"phi_v_pll_in_{name}")

    theta_pll: Var = vf.add_var(name=f"theta_pll_{name}")
    xi_pll: Var = vf.add_var(name=f"xi_pll_{name}")
    omega_pll: Var = vf.add_var(name=f"omega_pll_{name}")

    d_theta_pll: Var = vf.add_diff_var(name=f"d_theta_pll_{name}", base_var=theta_pll)
    d_xi_pll: Var = vf.add_diff_var(name=f"d_xi_pll_{name}", base_var=xi_pll)
    c0: Const = vf.add_const(0.0)

    return Block(
        state_eqs=list([
            omega_pll,
            -pll_ki * v_q,
        ]),
        state_vars=list([theta_pll, xi_pll]),
        diff_vars=list([d_theta_pll, d_xi_pll]),
        algebraic_eqs=list([
            omega_pll - (omega_base - pll_kp * v_q + xi_pll),
        ]),
        algebraic_vars=list([omega_pll]),
        init_eqs=dict([
            (theta_pll, phi_v),
            (xi_pll, c0),
            (omega_pll, omega_base),
        ]),
        diff_init_eqs=dict([
            (d_theta_pll, omega_base),
            (d_xi_pll, c0),
        ]),
        in_vars=list([v_q, omega_base, pll_kp, pll_ki, phi_v]),
        out_vars=list([theta_pll, omega_pll]),
        name=f"{name}_pll",
    )


def _build_bridge_filter_pll_input_filter_block(vf: VarFactory, name: str) -> Block:
    """
    Build one first-order filter for the q-axis PLL input of the switched plant.

    The pseudo-EMT converter sees a smooth fundamental q-axis voltage, while the
    switched bridge/filter plant exposes switching ripple at the same measurement
    point. Filtering the q-axis voltage before feeding the PLL makes both models
    comparable without altering the converter control hierarchy itself.

    The time constant is tied to the PWM carrier half-period:

    ``tau_pll_vq = pi / omega_sw``

    This keeps the filter physically interpretable and avoids introducing one ad hoc
    fixed delay parameter into the public switched-converter model.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name suffix.
    :return: q-axis PLL-input filter block.
    """
    v_q_raw: Var = vf.add_var(name=f"v_q_pll_filter_in_{name}")
    omega_sw: Var = vf.add_var(name=f"omega_sw_pll_filter_in_{name}")

    v_q_pll_f: Var = vf.add_var(name=f"v_q_pll_f_{name}")
    d_v_q_pll_f: Var = vf.add_diff_var(name=f"d_v_q_pll_f_{name}", base_var=v_q_pll_f)

    eps: Const = Const(1.0e-10)
    c_pi: Const = Const(np.pi)
    c0: Const = Const(0.0)

    return Block(
        state_vars=list([v_q_pll_f]),
        state_eqs=list([
            # The switched plant should feed the PLL with the low-frequency q-axis content rather than
            # with the raw switching ripple of the network-side voltage measurement.
            (v_q_raw - v_q_pll_f) * (sym.max(omega_sw, eps)/c_pi),
        ]),
        diff_vars=list([d_v_q_pll_f]),
        init_eqs=dict([
            (v_q_pll_f, v_q_raw),
        ]),
        diff_init_eqs=dict([
            (d_v_q_pll_f, c0),
        ]),
        in_vars=list([v_q_raw, omega_sw]),
        out_vars=list([v_q_pll_f]),
        name=f"{name}_pll_input_filter",
    )


def _build_bridge_filter_measurement_filter_block(vf: VarFactory, name: str) -> Block:
    """
    Build one first-order dq0 measurement filter for the switched bridge + filter plant.

    The averaged pseudo-EMT converter controllers act on smooth dq0 quantities. The
    switched bridge plant, in contrast, exposes carrier-frequency ripple directly in
    its reconstructed dq0 measurements. Filtering those measurements before they feed
    the PLL and inner current loop isolates the low-frequency controller dynamics from
    switching artifacts without altering the electrical plant itself.

    The time constant is tied to the PWM carrier half-period:

    ``tau_meas = pi / omega_sw``

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name suffix.
    :return: dq0 measurement-filter block.
    """
    v_d_raw: Var = vf.add_var(name=f"v_d_meas_filter_in_{name}")
    v_q_raw: Var = vf.add_var(name=f"v_q_meas_filter_in_{name}")
    v_0_raw: Var = vf.add_var(name=f"v_0_meas_filter_in_{name}")
    i_d_raw: Var = vf.add_var(name=f"i_d_meas_filter_in_{name}")
    i_q_raw: Var = vf.add_var(name=f"i_q_meas_filter_in_{name}")
    i_0_raw: Var = vf.add_var(name=f"i_0_meas_filter_in_{name}")
    omega_sw: Var = vf.add_var(name=f"omega_sw_meas_filter_in_{name}")

    v_d_meas_f: Var = vf.add_var(name=f"v_d_meas_f_{name}")
    v_q_meas_f: Var = vf.add_var(name=f"v_q_meas_f_{name}")
    v_0_meas_f: Var = vf.add_var(name=f"v_0_meas_f_{name}")
    i_d_meas_f: Var = vf.add_var(name=f"i_d_meas_f_{name}")
    i_q_meas_f: Var = vf.add_var(name=f"i_q_meas_f_{name}")
    i_0_meas_f: Var = vf.add_var(name=f"i_0_meas_f_{name}")

    d_v_d_meas_f: Var = vf.add_diff_var(name=f"d_v_d_meas_f_{name}", base_var=v_d_meas_f)
    d_v_q_meas_f: Var = vf.add_diff_var(name=f"d_v_q_meas_f_{name}", base_var=v_q_meas_f)
    d_v_0_meas_f: Var = vf.add_diff_var(name=f"d_v_0_meas_f_{name}", base_var=v_0_meas_f)
    d_i_d_meas_f: Var = vf.add_diff_var(name=f"d_i_d_meas_f_{name}", base_var=i_d_meas_f)
    d_i_q_meas_f: Var = vf.add_diff_var(name=f"d_i_q_meas_f_{name}", base_var=i_q_meas_f)
    d_i_0_meas_f: Var = vf.add_diff_var(name=f"d_i_0_meas_f_{name}", base_var=i_0_meas_f)

    eps: Const = Const(1.0e-10)
    c_pi: Const = Const(np.pi)
    c0: Const = Const(0.0)
    inv_tau_meas_expr: Expr = sym.max(omega_sw, eps)/c_pi

    return Block(
        state_eqs=list([
            (v_d_raw - v_d_meas_f) * inv_tau_meas_expr,
            (v_q_raw - v_q_meas_f) * inv_tau_meas_expr,
            (v_0_raw - v_0_meas_f) * inv_tau_meas_expr,
            (i_d_raw - i_d_meas_f) * inv_tau_meas_expr,
            (i_q_raw - i_q_meas_f) * inv_tau_meas_expr,
            (i_0_raw - i_0_meas_f) * inv_tau_meas_expr,
        ]),
        state_vars=list([v_d_meas_f, v_q_meas_f, v_0_meas_f, i_d_meas_f, i_q_meas_f, i_0_meas_f]),
        diff_vars=list([d_v_d_meas_f, d_v_q_meas_f, d_v_0_meas_f, d_i_d_meas_f, d_i_q_meas_f, d_i_0_meas_f]),
        init_eqs=dict([
            (v_d_meas_f, v_d_raw),
            (v_q_meas_f, v_q_raw),
            (v_0_meas_f, v_0_raw),
            (i_d_meas_f, i_d_raw),
            (i_q_meas_f, i_q_raw),
            (i_0_meas_f, i_0_raw),
        ]),
        diff_init_eqs=dict([
            (d_v_d_meas_f, c0),
            (d_v_q_meas_f, c0),
            (d_v_0_meas_f, c0),
            (d_i_d_meas_f, c0),
            (d_i_q_meas_f, c0),
            (d_i_0_meas_f, c0),
        ]),
        in_vars=list([v_d_raw, v_q_raw, v_0_raw, i_d_raw, i_q_raw, i_0_raw, omega_sw]),
        out_vars=list([v_d_meas_f, v_q_meas_f, v_0_meas_f, i_d_meas_f, i_q_meas_f, i_0_meas_f]),
        name=f"{name}_measurement_filter",
    )


def get_bridge_filter_control_2level_3ph_emt_multilinear_template(vf: VarFactory, name: str = "bridge_filter_control_2level_3ph_emt_ml") -> EmtModelTemplate:
    """
    Build one standalone bridge + filter + control EMT template.

    The template reuses the validated standalone bridge + filter plant and adds
    one PLL plus one dq0 current controller. This is the next incremental step
    before reintegrating the switched plant into the full VSC model.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name.
    :return: Standalone bridge + filter + control EMT template.
    """
    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.DynamicModelHostDevice
    templ.name = name
    templ.block.name = name

    omega_base_in: Var = vf.add_var(name=f"omega_base_in_{name}")
    v_A_in: Var = vf.add_var(name=f"v_A_in_{name}")
    v_B_in: Var = vf.add_var(name=f"v_B_in_{name}")
    v_C_in: Var = vf.add_var(name=f"v_C_in_{name}")
    v_dc_in: Var = vf.add_var(name=f"v_dc_in_{name}")
    i_d_ref_in: Var = vf.add_var(name=f"i_d_ref_in_{name}")
    i_q_ref_in: Var = vf.add_var(name=f"i_q_ref_in_{name}")
    i_0_ref_in: Var = vf.add_var(name=f"i_0_ref_in_{name}")
    m_max_in: Var = vf.add_var(name=f"m_max_in_{name}")
    vdc_floor_in: Var = vf.add_var(name=f"vdc_floor_in_{name}")
    omega_sw_in: Var = vf.add_var(name=f"omega_sw_in_{name}")
    omega_meas_in: Var = vf.add_var(name=f"omega_meas_in_{name}")
    carrier_phase_in: Var = vf.add_var(name=f"carrier_phase_in_{name}")
    R_f_in: Var = vf.add_var(name=f"R_f_in_{name}")
    L_f_in: Var = vf.add_var(name=f"L_f_in_{name}")
    pll_kp_in: Var = vf.add_var(name=f"pll_kp_in_{name}")
    pll_ki_in: Var = vf.add_var(name=f"pll_ki_in_{name}")
    i_kp_in: Var = vf.add_var(name=f"i_kp_in_{name}")
    i_ki_in: Var = vf.add_var(name=f"i_ki_in_{name}")
    aw_gain_in: Var = vf.add_var(name=f"aw_gain_in_{name}")
    phi_v_in: Var = vf.add_var(name=f"phi_v_in_{name}")
    Vdc_ref_in: Var = vf.add_var(name=f"Vdc_ref_in_{name}")
    sbase_in: Var = vf.add_var(name=f"sbase_in_{name}")
    P_ref_in: Var = vf.add_var(name=f"P_ref_in_{name}")
    Q_ref_in: Var = vf.add_var(name=f"Q_ref_in_{name}")
    P_loss0_in: Var = vf.add_var(name=f"P_loss0_in_{name}")
    Vpk_in: Var = vf.add_var(name=f"Vpk_in_{name}")

    plant_block: Block = get_bridge_filter_2level_3ph_emt_multilinear_template(vf=vf, name=f"{name}_plant").block
    measurement_filter_block: Block = _build_bridge_filter_measurement_filter_block(vf=vf, name=name)
    pll_input_filter_block: Block = _build_bridge_filter_pll_input_filter_block(vf=vf, name=name)
    pll_block: Block = _build_bridge_filter_pll_block(vf=vf, name=name)
    current_ctrl_block: Block = _build_bridge_filter_current_control_block(vf=vf, name=name)
    plant_lookup: Dict[str, Var] = build_name_to_var_lookup(plant_block)
    measurement_filter_lookup: Dict[str, Var] = build_name_to_var_lookup(measurement_filter_block)
    pll_input_filter_lookup: Dict[str, Var] = build_name_to_var_lookup(pll_input_filter_block)
    pll_lookup: Dict[str, Var] = build_name_to_var_lookup(pll_block)
    current_ctrl_lookup: Dict[str, Var] = build_name_to_var_lookup(current_ctrl_block)

    plant_i_A: Var | None = plant_lookup.get(f"i_A_{name}_plant", None)
    plant_i_B: Var | None = plant_lookup.get(f"i_B_{name}_plant", None)
    plant_i_C: Var | None = plant_lookup.get(f"i_C_{name}_plant", None)
    plant_i_d: Var | None = plant_lookup.get(f"i_d_{name}_plant", None)
    plant_i_q: Var | None = plant_lookup.get(f"i_q_{name}_plant", None)
    plant_i_0: Var | None = plant_lookup.get(f"i_0_{name}_plant", None)
    plant_v_d: Var | None = plant_lookup.get(f"v_d_{name}_plant", None)
    plant_v_q: Var | None = plant_lookup.get(f"v_q_{name}_plant", None)
    plant_v_0: Var | None = plant_lookup.get(f"v_0_{name}_plant", None)
    plant_gate_a: Var | None = plant_lookup.get(f"gate_a_{name}_plant_bridge", None)
    plant_gate_b: Var | None = plant_lookup.get(f"gate_b_{name}_plant_bridge", None)
    plant_gate_c: Var | None = plant_lookup.get(f"gate_c_{name}_plant_bridge", None)
    plant_v_conv_a: Var | None = plant_lookup.get(f"v_conv_a_{name}_plant_bridge", None)
    plant_v_conv_b: Var | None = plant_lookup.get(f"v_conv_b_{name}_plant_bridge", None)
    plant_v_conv_c: Var | None = plant_lookup.get(f"v_conv_c_{name}_plant_bridge", None)
    meas_v_d_f: Var | None = measurement_filter_lookup.get(f"v_d_meas_f_{name}", None)
    meas_v_q_f: Var | None = measurement_filter_lookup.get(f"v_q_meas_f_{name}", None)
    meas_v_0_f: Var | None = measurement_filter_lookup.get(f"v_0_meas_f_{name}", None)
    meas_i_d_f: Var | None = measurement_filter_lookup.get(f"i_d_meas_f_{name}", None)
    meas_i_q_f: Var | None = measurement_filter_lookup.get(f"i_q_meas_f_{name}", None)
    meas_i_0_f: Var | None = measurement_filter_lookup.get(f"i_0_meas_f_{name}", None)
    pll_input_v_q_f: Var | None = pll_input_filter_lookup.get(f"v_q_pll_f_{name}", None)
    pll_theta: Var | None = pll_lookup.get(f"theta_pll_{name}", None)
    pll_omega: Var | None = pll_lookup.get(f"omega_pll_{name}", None)
    ctrl_v_cmd_d: Var | None = current_ctrl_lookup.get(f"v_cmd_d_{name}", None)
    ctrl_v_cmd_q: Var | None = current_ctrl_lookup.get(f"v_cmd_q_{name}", None)
    ctrl_v_cmd_0: Var | None = current_ctrl_lookup.get(f"v_cmd_0_{name}", None)
    ctrl_k_v_conv: Var | None = current_ctrl_lookup.get(f"k_v_conv_{name}", None)

    if plant_i_A is None or plant_i_B is None or plant_i_C is None or plant_i_d is None or plant_i_q is None or plant_i_0 is None or plant_v_d is None or plant_v_q is None or plant_v_0 is None or plant_gate_a is None or plant_gate_b is None or plant_gate_c is None or plant_v_conv_a is None or plant_v_conv_b is None or plant_v_conv_c is None or meas_v_d_f is None or meas_v_q_f is None or meas_v_0_f is None or meas_i_d_f is None or meas_i_q_f is None or meas_i_0_f is None or pll_input_v_q_f is None or pll_theta is None or pll_omega is None or ctrl_v_cmd_d is None or ctrl_v_cmd_q is None or ctrl_v_cmd_0 is None or ctrl_k_v_conv is None:
        raise KeyError(f"The bridge + filter + control template '{name}' could not resolve one or more internal variables")
    else:
        pass

    # The plant receives electrical inputs and the voltage commands produced by the current controller.
    # The PLL angle is generated internally by ``pll_block`` so the parent block does not expose
    # a dead external angle input.
    plant_block.connect(plant_block.in_vars[0:16], list([
        pll_theta,
        omega_base_in,
        v_A_in,
        v_B_in,
        v_C_in,
        ctrl_v_cmd_d,
        ctrl_v_cmd_q,
        ctrl_v_cmd_0,
        v_dc_in,
        ctrl_k_v_conv,
        m_max_in,
        vdc_floor_in,
        omega_sw_in,
        carrier_phase_in,
        R_f_in,
        L_f_in,
    ]))

    # The switched plant dq0 measurements are filtered before they feed the controls so the PLL and
    # current loop react to the low-frequency plant behaviour rather than to carrier ripple.
    measurement_filter_block.connect(measurement_filter_block.in_vars[0:7], list([
        plant_v_d,
        plant_v_q,
        plant_v_0,
        plant_i_d,
        plant_i_q,
        plant_i_0,
        omega_meas_in,
    ]))

    # The PLL still uses one dedicated q-axis input filter on top of the generic measurement filter.
    # This keeps the already-validated PLL smoothing path while removing the strongest carrier ripple
    # before it reaches that dedicated stage.
    pll_input_filter_block.connect(pll_input_filter_block.in_vars[0:2], list([
        meas_v_q_f,
        omega_meas_in,
    ]))

    # The PLL uses the filtered q-axis plant voltage.
    pll_block.connect(pll_block.in_vars[0:5], list([
        pll_input_v_q_f,
        omega_base_in,
        pll_kp_in,
        pll_ki_in,
        phi_v_in,
    ]))

    # The switched plant reuses the full pseudo-EMT inner loop so its dq controller shares the
    # same modulation-limit logic as the averaged reference converter.
    current_ctrl_block.connect(current_ctrl_block.in_vars[0:25], list([
        meas_v_d_f,
        meas_v_q_f,
        meas_v_0_f,
        meas_i_d_f,
        meas_i_q_f,
        meas_i_0_f,
        pll_omega,
        omega_base_in,
        R_f_in,
        L_f_in,
        i_0_ref_in,
        i_d_ref_in,
        i_q_ref_in,
        i_kp_in,
        i_ki_in,
        aw_gain_in,
        m_max_in,
        Vdc_ref_in,
        v_dc_in,
        vdc_floor_in,
        sbase_in,
        P_ref_in,
        Q_ref_in,
        P_loss0_in,
        Vpk_in,
    ]))

    templ.block.children.extend(list([plant_block, measurement_filter_block, pll_input_filter_block, pll_block, current_ctrl_block]))
    templ.block.unify_blocks()
    templ.block.in_vars = list([
        omega_base_in,
        v_A_in,
        v_B_in,
        v_C_in,
        v_dc_in,
        i_d_ref_in,
        i_q_ref_in,
        i_0_ref_in,
        m_max_in,
        vdc_floor_in,
        omega_sw_in,
        omega_meas_in,
        carrier_phase_in,
        R_f_in,
        L_f_in,
        pll_kp_in,
        pll_ki_in,
        i_kp_in,
        i_ki_in,
        aw_gain_in,
        phi_v_in,
        Vdc_ref_in,
        sbase_in,
        P_ref_in,
        Q_ref_in,
        P_loss0_in,
        Vpk_in,
    ])
    templ.block.out_vars = list([
        plant_i_A,
        plant_i_B,
        plant_i_C,
        plant_i_d,
        plant_i_q,
        plant_i_0,
        plant_gate_a,
        plant_gate_b,
        plant_gate_c,
        plant_v_conv_a,
        plant_v_conv_b,
        plant_v_conv_c,
        ctrl_v_cmd_d,
        ctrl_v_cmd_q,
        ctrl_v_cmd_0,
        meas_v_d_f,
        meas_v_q_f,
        meas_i_d_f,
        meas_i_q_f,
        pll_input_v_q_f,
        pll_theta,
        pll_omega,
    ])

    return templ
