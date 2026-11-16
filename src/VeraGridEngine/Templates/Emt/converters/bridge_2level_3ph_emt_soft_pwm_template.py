# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple

import numpy as np

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.Symbolic.symbolic_ml import ml_three_phase_carrier_pwm_direct
from VeraGridEngine.enumerations import DeviceType


def _inverse_dq0_to_abc_expressions(
    d_value: Expr,
    q_value: Expr,
    zero_value: Expr,
    theta_value: Expr,
) -> Tuple[Expr, Expr, Expr]:
    theta_b: Expr = theta_value - Const(2.0 * np.pi / 3.0)
    theta_c: Expr = theta_value + Const(2.0 * np.pi / 3.0)
    return (
        d_value * sym.sin(theta_value) - q_value * sym.cos(theta_value) + zero_value,
        d_value * sym.sin(theta_b) - q_value * sym.cos(theta_b) + zero_value,
        d_value * sym.sin(theta_c) - q_value * sym.cos(theta_c) + zero_value,
    )


def get_bridge_2level_3ph_emt_soft_pwm_template(
    vf: VarFactory,
    name: str = "bridge_2level_3ph_emt_soft_pwm",
    lamda: Expr | float | int = 1.0e-6,
    gate_tau: Expr | float | int = 1.0e-5,
) -> EmtModelTemplate:
    """Build an ideal two-level bridge using smooth soft-sign carrier PWM."""

    templ = EmtModelTemplate()
    templ.tpe = DeviceType.DynamicModelHostDevice
    templ.name = name

    theta_pll = vf.add_var(name=f"theta_pll_in_{name}")
    omega_base = vf.add_var(name=f"omega_base_in_{name}")
    v_cmd_d = vf.add_var(name=f"v_cmd_d_in_{name}")
    v_cmd_q = vf.add_var(name=f"v_cmd_q_in_{name}")
    v_cmd_0 = vf.add_var(name=f"v_cmd_0_in_{name}")
    v_dc = vf.add_var(name=f"v_dc_in_{name}")
    k_v_conv = vf.add_var(name=f"k_v_conv_in_{name}")
    m_max = vf.add_var(name=f"m_max_in_{name}")
    vdc_floor = vf.add_var(name=f"vdc_floor_in_{name}")
    omega_sw = vf.add_var(name=f"omega_sw_in_{name}")
    carrier_phase = vf.add_var(name=f"carrier_phase_in_{name}")
    carrier_enable = vf.add_var(name=f"carrier_enable_in_{name}")

    v_ref_a_raw = vf.add_var(name=f"v_ref_a_raw_{name}")
    v_ref_b_raw = vf.add_var(name=f"v_ref_b_raw_{name}")
    v_ref_c_raw = vf.add_var(name=f"v_ref_c_raw_{name}")
    v_ref_common_inj = vf.add_var(name=f"v_ref_common_inj_{name}")
    v_ref_a = vf.add_var(name=f"v_ref_a_{name}")
    v_ref_b = vf.add_var(name=f"v_ref_b_{name}")
    v_ref_c = vf.add_var(name=f"v_ref_c_{name}")
    theta_pwm_sample = vf.add_var(name=f"theta_pwm_sample_{name}")
    v_ref_a_pwm = vf.add_var(name=f"v_ref_a_pwm_{name}")
    v_ref_b_pwm = vf.add_var(name=f"v_ref_b_pwm_{name}")
    v_ref_c_pwm = vf.add_var(name=f"v_ref_c_pwm_{name}")
    m_a_u = vf.add_var(name=f"m_a_u_{name}")
    m_b_u = vf.add_var(name=f"m_b_u_{name}")
    m_c_u = vf.add_var(name=f"m_c_u_{name}")
    m_a = vf.add_var(name=f"m_a_{name}")
    m_b = vf.add_var(name=f"m_b_{name}")
    m_c = vf.add_var(name=f"m_c_{name}")
    carrier = vf.add_var(name=f"carrier_pwm_{name}")

    v_p = vf.add_var(name=f"v_p_{name}")
    v_n = vf.add_var(name=f"v_n_{name}")
    v_leg_a = vf.add_var(name=f"v_leg_a_{name}")
    v_leg_b = vf.add_var(name=f"v_leg_b_{name}")
    v_leg_c = vf.add_var(name=f"v_leg_c_{name}")
    v_common_mode = vf.add_var(name=f"v_common_mode_{name}")
    v_conv_a = vf.add_var(name=f"v_conv_a_{name}")
    v_conv_b = vf.add_var(name=f"v_conv_b_{name}")
    v_conv_c = vf.add_var(name=f"v_conv_c_{name}")
    v_conv_d = vf.add_var(name=f"v_conv_d_{name}")
    v_conv_q = vf.add_var(name=f"v_conv_q_{name}")
    v_conv_0 = vf.add_var(name=f"v_conv_0_{name}")

    eps = Const(1.0e-10)
    c_half = Const(0.5)
    c_one = Const(1.0)
    c_two = Const(2.0)
    c_three = Const(3.0)
    c_pi = Const(np.pi)
    c13 = Const(1.0 / 3.0)
    c23 = Const(2.0 / 3.0)
    time_var = Var(EmtProblemTemplate.TIME_NAME)

    v_dc_eff = sym.max(v_dc, vdc_floor)
    v_mod_scale = sym.max(k_v_conv * v_dc_eff, eps)
    v_leg_scale = k_v_conv * v_dc_eff
    theta_pwm_sample_expr = theta_pll + carrier_enable * omega_base * c_pi / (c_two * omega_sw)
    carrier_expr = -carrier_enable * sym.sin(omega_sw * time_var + carrier_phase)

    v_ref_a_raw_expr, v_ref_b_raw_expr, v_ref_c_raw_expr = _inverse_dq0_to_abc_expressions(v_cmd_d, v_cmd_q, v_cmd_0, theta_pll)
    v_ref_a_pwm_raw_expr, v_ref_b_pwm_raw_expr, v_ref_c_pwm_raw_expr = _inverse_dq0_to_abc_expressions(
        v_cmd_d,
        v_cmd_q,
        v_cmd_0,
        theta_pwm_sample_expr,
    )
    v_ref_common_inj_expr = c_half * (
        sym.max(sym.max(v_ref_a_raw_expr, v_ref_b_raw_expr), v_ref_c_raw_expr)
        + sym.min(sym.min(v_ref_a_raw_expr, v_ref_b_raw_expr), v_ref_c_raw_expr)
    )
    v_ref_common_inj_pwm_expr = c_half * (
        sym.max(sym.max(v_ref_a_pwm_raw_expr, v_ref_b_pwm_raw_expr), v_ref_c_pwm_raw_expr)
        + sym.min(sym.min(v_ref_a_pwm_raw_expr, v_ref_b_pwm_raw_expr), v_ref_c_pwm_raw_expr)
    )
    v_ref_a_expr = v_ref_a_raw_expr - v_ref_common_inj_expr
    v_ref_b_expr = v_ref_b_raw_expr - v_ref_common_inj_expr
    v_ref_c_expr = v_ref_c_raw_expr - v_ref_common_inj_expr
    v_ref_a_pwm_expr = v_ref_a_pwm_raw_expr - v_ref_common_inj_pwm_expr
    v_ref_b_pwm_expr = v_ref_b_pwm_raw_expr - v_ref_common_inj_pwm_expr
    v_ref_c_pwm_expr = v_ref_c_pwm_raw_expr - v_ref_common_inj_pwm_expr
    m_a_u_expr = v_ref_a_pwm_expr / v_mod_scale
    m_b_u_expr = v_ref_b_pwm_expr / v_mod_scale
    m_c_u_expr = v_ref_c_pwm_expr / v_mod_scale
    m_a_expr = sym.hard_sat(m_a_u_expr, -m_max, m_max)
    m_b_expr = sym.hard_sat(m_b_u_expr, -m_max, m_max)
    m_c_expr = sym.hard_sat(m_c_u_expr, -m_max, m_max)

    pwm_block, gate_a, gate_b, gate_c = ml_three_phase_carrier_pwm_direct(
        vf=vf,
        ref_a=m_a,
        ref_b=m_b,
        ref_c=m_c,
        carrier=carrier,
        lamda=lamda,
        name=name,
    )

    gate_a_out = vf.add_var(name=f"gate_a_{name}")
    gate_b_out = vf.add_var(name=f"gate_b_{name}")
    gate_c_out = vf.add_var(name=f"gate_c_{name}")
    dgate_a_out = vf.add_diff_var(name=f"dt_gate_a_{name}", base_var=gate_a_out)
    dgate_b_out = vf.add_diff_var(name=f"dt_gate_b_{name}", base_var=gate_b_out)
    dgate_c_out = vf.add_diff_var(name=f"dt_gate_c_{name}", base_var=gate_c_out)
    gate_tau_expr = Const(float(gate_tau)) if isinstance(gate_tau, (float, int)) else gate_tau

    v_p_expr = c_half * v_dc_eff
    v_n_expr = -c_half * v_dc_eff
    v_leg_a_expr = (c_two * gate_a_out - c_one) * v_leg_scale
    v_leg_b_expr = (c_two * gate_b_out - c_one) * v_leg_scale
    v_leg_c_expr = (c_two * gate_c_out - c_one) * v_leg_scale
    v_common_mode_expr = (v_leg_a_expr + v_leg_b_expr + v_leg_c_expr) / c_three
    v_conv_a_expr = v_leg_a_expr - v_common_mode_expr
    v_conv_b_expr = v_leg_b_expr - v_common_mode_expr
    v_conv_c_expr = v_leg_c_expr - v_common_mode_expr
    theta_b = theta_pll - Const(2.0 * np.pi / 3.0)
    theta_c = theta_pll + Const(2.0 * np.pi / 3.0)
    v_conv_d_expr = c23 * (sym.sin(theta_pll) * v_conv_a_expr + sym.sin(theta_b) * v_conv_b_expr + sym.sin(theta_c) * v_conv_c_expr)
    v_conv_q_expr = -c23 * (sym.cos(theta_pll) * v_conv_a_expr + sym.cos(theta_b) * v_conv_b_expr + sym.cos(theta_c) * v_conv_c_expr)
    v_conv_0_expr = c13 * (v_conv_a_expr + v_conv_b_expr + v_conv_c_expr)

    bridge_block = Block(
        name=name,
        algebraic_eqs=[
            v_ref_a_raw - v_ref_a_raw_expr,
            v_ref_b_raw - v_ref_b_raw_expr,
            v_ref_c_raw - v_ref_c_raw_expr,
            v_ref_common_inj - v_ref_common_inj_expr,
            v_ref_a - v_ref_a_expr,
            v_ref_b - v_ref_b_expr,
            v_ref_c - v_ref_c_expr,
            theta_pwm_sample - theta_pwm_sample_expr,
            v_ref_a_pwm - v_ref_a_pwm_expr,
            v_ref_b_pwm - v_ref_b_pwm_expr,
            v_ref_c_pwm - v_ref_c_pwm_expr,
            m_a_u - m_a_u_expr,
            m_b_u - m_b_u_expr,
            m_c_u - m_c_u_expr,
            m_a - m_a_expr,
            m_b - m_b_expr,
            m_c - m_c_expr,
            v_p - v_p_expr,
            v_n - v_n_expr,
            v_leg_a - v_leg_a_expr,
            v_leg_b - v_leg_b_expr,
            v_leg_c - v_leg_c_expr,
            v_common_mode - v_common_mode_expr,
            v_conv_a - v_conv_a_expr,
            v_conv_b - v_conv_b_expr,
            v_conv_c - v_conv_c_expr,
            v_conv_d - v_conv_d_expr,
            v_conv_q - v_conv_q_expr,
            v_conv_0 - v_conv_0_expr,
        ],
        algebraic_vars=[
            v_ref_a_raw, v_ref_b_raw, v_ref_c_raw, v_ref_common_inj,
            v_ref_a, v_ref_b, v_ref_c, theta_pwm_sample,
            v_ref_a_pwm, v_ref_b_pwm, v_ref_c_pwm,
            m_a_u, m_b_u, m_c_u, m_a, m_b, m_c,
            v_p, v_n, v_leg_a, v_leg_b, v_leg_c, v_common_mode,
            v_conv_a, v_conv_b, v_conv_c, v_conv_d, v_conv_q, v_conv_0,
        ],
        state_vars=[gate_a_out, gate_b_out, gate_c_out],
        state_eqs=[
            (gate_a - gate_a_out) / gate_tau_expr,
            (gate_b - gate_b_out) / gate_tau_expr,
            (gate_c - gate_c_out) / gate_tau_expr,
        ],
        diff_vars=[dgate_a_out, dgate_b_out, dgate_c_out],
        diff_init_eqs={
            dgate_a_out: Const(0.0),
            dgate_b_out: Const(0.0),
            dgate_c_out: Const(0.0),
        },
        event_dict={
            omega_sw: Const(2.0 * np.pi * 1000.0),
            carrier_phase: Const(0.0),
            carrier: carrier_expr,
        },
        init_eqs={
            v_ref_a_raw: v_ref_a_raw_expr,
            v_ref_b_raw: v_ref_b_raw_expr,
            v_ref_c_raw: v_ref_c_raw_expr,
            v_ref_common_inj: v_ref_common_inj_expr,
            v_ref_a: v_ref_a_expr,
            v_ref_b: v_ref_b_expr,
            v_ref_c: v_ref_c_expr,
            theta_pwm_sample: theta_pwm_sample_expr,
            v_ref_a_pwm: v_ref_a_pwm_expr,
            v_ref_b_pwm: v_ref_b_pwm_expr,
            v_ref_c_pwm: v_ref_c_pwm_expr,
            m_a_u: m_a_u_expr,
            m_b_u: m_b_u_expr,
            m_c_u: m_c_u_expr,
            m_a: m_a_expr,
            m_b: m_b_expr,
            m_c: m_c_expr,
            v_p: v_p_expr,
            v_n: v_n_expr,
            v_leg_a: v_leg_a_expr,
            v_leg_b: v_leg_b_expr,
            v_leg_c: v_leg_c_expr,
            v_common_mode: Const(0.0),
            v_conv_a: v_conv_a_expr,
            v_conv_b: v_conv_b_expr,
            v_conv_c: v_conv_c_expr,
            v_conv_d: v_conv_d_expr,
            v_conv_q: v_conv_q_expr,
            v_conv_0: v_conv_0_expr,
            gate_a_out: gate_a,
            gate_b_out: gate_b,
            gate_c_out: gate_c,
        },
        in_vars=[theta_pll, omega_base, v_cmd_d, v_cmd_q, v_cmd_0, v_dc, k_v_conv, m_max, vdc_floor, omega_sw, carrier_phase, carrier_enable],
        out_vars=[gate_a_out, gate_b_out, gate_c_out, v_conv_a, v_conv_b, v_conv_c, m_a, m_b, m_c, v_conv_d, v_conv_q, v_conv_0],
    )
    bridge_block.add(pwm_block)
    bridge_block.unify_blocks()
    templ.block = bridge_block
    return templ
