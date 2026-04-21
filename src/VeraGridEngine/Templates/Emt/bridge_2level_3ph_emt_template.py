# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple

import numpy as np

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType


def _inverse_dq0_to_abc_expressions(
        d_value: Expr,
        q_value: Expr,
        zero_value: Expr,
        theta_value: Expr,
) -> Tuple[Expr, Expr, Expr]:
    """
    Transform one dq0 quantity into its abc representation.

    :param d_value: d-axis component.
    :param q_value: q-axis component.
    :param zero_value: Zero-sequence component.
    :param theta_value: Electrical angle.
    :return: Tuple ``(a_value, b_value, c_value)``.
    """
    theta_b: Expr = theta_value - Const(2.0 * np.pi / 3.0)
    theta_c: Expr = theta_value + Const(2.0 * np.pi / 3.0)

    # The bridge uses the same dq0-to-abc convention as the converter EMT templates.
    a_value: Expr = d_value * sym.sin(theta_value) - q_value * sym.cos(theta_value) + zero_value
    b_value: Expr = d_value * sym.sin(theta_b) - q_value * sym.cos(theta_b) + zero_value
    c_value: Expr = d_value * sym.sin(theta_c) - q_value * sym.cos(theta_c) + zero_value

    return a_value, b_value, c_value


def get_bridge_2level_3ph_emt_template(vf: VarFactory, name: str = "bridge_2level_3ph_emt") -> EmtModelTemplate:
    """
    Build one standalone ideal 2-level three-phase bridge EMT template.

    The bridge is driven by dq0 voltage references and uses a regular-sampled
    three-phase PWM logic implemented in the procedural layer. The symbolic DAE
    only sees the held gate states and the resulting converter phase voltages.

    The DC side is represented by one positive rail and one internal negative rail
    derived from the external DC-link voltage. This keeps the bridge standalone and
    directly testable before integrating it inside a full converter template.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name.
    :return: Standalone EMT bridge template.
    """
    from VeraGridEngine.Utils.procedural_logic import ThreePhaseCarrierPwmLogic

    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.DynamicModelHostDevice
    templ.name = name
    templ.block.name = name

    # ------------------------------------------------------------------
    # External inputs.
    # ------------------------------------------------------------------
    theta_pll: Var = vf.add_var(name=f"theta_pll_in_{name}")
    v_cmd_d: Var = vf.add_var(name=f"v_cmd_d_in_{name}")
    v_cmd_q: Var = vf.add_var(name=f"v_cmd_q_in_{name}")
    v_cmd_0: Var = vf.add_var(name=f"v_cmd_0_in_{name}")
    v_dc: Var = vf.add_var(name=f"v_dc_in_{name}")
    k_v_conv: Var = vf.add_var(name=f"k_v_conv_in_{name}")
    m_max: Var = vf.add_var(name=f"m_max_in_{name}")
    vdc_floor: Var = vf.add_var(name=f"vdc_floor_in_{name}")
    omega_sw: Var = vf.add_var(name=f"omega_sw_in_{name}")
    carrier_phase: Var = vf.add_var(name=f"carrier_phase_in_{name}")

    # ------------------------------------------------------------------
    # Internal modulation and gate variables.
    # ------------------------------------------------------------------
    v_ref_a: Var = vf.add_var(name=f"v_ref_a_{name}")
    v_ref_b: Var = vf.add_var(name=f"v_ref_b_{name}")
    v_ref_c: Var = vf.add_var(name=f"v_ref_c_{name}")
    m_a_u: Var = vf.add_var(name=f"m_a_u_{name}")
    m_b_u: Var = vf.add_var(name=f"m_b_u_{name}")
    m_c_u: Var = vf.add_var(name=f"m_c_u_{name}")
    m_a: Var = vf.add_var(name=f"m_a_{name}")
    m_b: Var = vf.add_var(name=f"m_b_{name}")
    m_c: Var = vf.add_var(name=f"m_c_{name}")

    gate_a_mode: Var = vf.add_var(name=f"gate_a_mode_{name}")
    gate_b_mode: Var = vf.add_var(name=f"gate_b_mode_{name}")
    gate_c_mode: Var = vf.add_var(name=f"gate_c_mode_{name}")
    gate_a: Var = vf.add_var(name=f"gate_a_{name}")
    gate_b: Var = vf.add_var(name=f"gate_b_{name}")
    gate_c: Var = vf.add_var(name=f"gate_c_{name}")

    # ------------------------------------------------------------------
    # Internal DC rails and converter phase voltages.
    # ------------------------------------------------------------------
    v_p: Var = vf.add_var(name=f"v_p_{name}")
    v_n: Var = vf.add_var(name=f"v_n_{name}")
    v_leg_a: Var = vf.add_var(name=f"v_leg_a_{name}")
    v_leg_b: Var = vf.add_var(name=f"v_leg_b_{name}")
    v_leg_c: Var = vf.add_var(name=f"v_leg_c_{name}")
    v_common_mode: Var = vf.add_var(name=f"v_common_mode_{name}")
    v_conv_a: Var = vf.add_var(name=f"v_conv_a_{name}")
    v_conv_b: Var = vf.add_var(name=f"v_conv_b_{name}")
    v_conv_c: Var = vf.add_var(name=f"v_conv_c_{name}")
    v_conv_d: Var = vf.add_var(name=f"v_conv_d_{name}")
    v_conv_q: Var = vf.add_var(name=f"v_conv_q_{name}")
    v_conv_0: Var = vf.add_var(name=f"v_conv_0_{name}")

    # ------------------------------------------------------------------
    # Fixed numerical safeguards.
    # ------------------------------------------------------------------
    eps: Const = Const(1.0e-10)
    c_half: Const = Const(0.5)
    c_one: Const = Const(1.0)
    c_two: Const = Const(2.0)
    c_three: Const = Const(3.0)
    c13: Const = Const(1.0 / 3.0)
    c23: Const = Const(2.0 / 3.0)

    # ------------------------------------------------------------------
    # Bridge equations.
    # ------------------------------------------------------------------
    v_dc_eff: Expr = sym.max(v_dc, vdc_floor)
    v_mod_scale: Expr = sym.max(k_v_conv * v_dc_eff, eps)
    v_leg_scale: Expr = Const(0.5) * v_dc_eff

    v_ref_a_expr: Expr
    v_ref_b_expr: Expr
    v_ref_c_expr: Expr
    v_ref_a_expr, v_ref_b_expr, v_ref_c_expr = _inverse_dq0_to_abc_expressions(
        d_value=v_cmd_d,
        q_value=v_cmd_q,
        zero_value=v_cmd_0,
        theta_value=theta_pll,
    )

    m_a_u_expr: Expr = v_ref_a_expr / v_mod_scale
    m_b_u_expr: Expr = v_ref_b_expr / v_mod_scale
    m_c_u_expr: Expr = v_ref_c_expr / v_mod_scale
    m_a_expr: Expr = sym.hard_sat(m_a_u_expr, -m_max, m_max)
    m_b_expr: Expr = sym.hard_sat(m_b_u_expr, -m_max, m_max)
    m_c_expr: Expr = sym.hard_sat(m_c_u_expr, -m_max, m_max)

    v_p_expr: Expr = c_half * v_dc_eff
    v_n_expr: Expr = -c_half * v_dc_eff

    # Each phase leg toggles between the positive and negative rails using the retained gate mode.
    v_leg_a_expr: Expr = (c_two * gate_a_mode - c_one) * v_leg_scale
    v_leg_b_expr: Expr = (c_two * gate_b_mode - c_one) * v_leg_scale
    v_leg_c_expr: Expr = (c_two * gate_c_mode - c_one) * v_leg_scale
    v_common_mode_expr: Expr = (v_leg_a_expr + v_leg_b_expr + v_leg_c_expr) / c_three

    v_conv_a_expr: Expr = v_leg_a_expr - v_common_mode_expr
    v_conv_b_expr: Expr = v_leg_b_expr - v_common_mode_expr
    v_conv_c_expr: Expr = v_leg_c_expr - v_common_mode_expr

    theta_b: Expr = theta_pll - Const(2.0 * np.pi / 3.0)
    theta_c: Expr = theta_pll + Const(2.0 * np.pi / 3.0)
    v_conv_d_expr: Expr = c23 * (sym.sin(theta_pll) * v_conv_a_expr + sym.sin(theta_b) * v_conv_b_expr + sym.sin(theta_c) * v_conv_c_expr)
    v_conv_q_expr: Expr = -c23 * (sym.cos(theta_pll) * v_conv_a_expr + sym.cos(theta_b) * v_conv_b_expr + sym.cos(theta_c) * v_conv_c_expr)
    v_conv_0_expr: Expr = c13 * (v_conv_a_expr + v_conv_b_expr + v_conv_c_expr)

    templ.block = Block(
        name=name,
        algebraic_eqs=list([
            v_ref_a - v_ref_a_expr,
            v_ref_b - v_ref_b_expr,
            v_ref_c - v_ref_c_expr,
            m_a_u - m_a_u_expr,
            m_b_u - m_b_u_expr,
            m_c_u - m_c_u_expr,
            m_a - m_a_expr,
            m_b - m_b_expr,
            m_c - m_c_expr,
            v_p - v_p_expr,
            v_n - v_n_expr,
            gate_a - gate_a_mode,
            gate_b - gate_b_mode,
            gate_c - gate_c_mode,
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
        ]),
        algebraic_vars=list([
            v_ref_a,
            v_ref_b,
            v_ref_c,
            m_a_u,
            m_b_u,
            m_c_u,
            m_a,
            m_b,
            m_c,
            v_p,
            v_n,
            gate_a,
            gate_b,
            gate_c,
            v_leg_a,
            v_leg_b,
            v_leg_c,
            v_common_mode,
            v_conv_a,
            v_conv_b,
            v_conv_c,
            v_conv_d,
            v_conv_q,
            v_conv_0,
        ]),
        event_dict=dict(),
        mode_dict=dict([
            (gate_a_mode, Const(0.0)),
            (gate_b_mode, Const(0.0)),
            (gate_c_mode, Const(0.0)),
        ]),
        init_eqs=dict([
            (v_ref_a, v_ref_a_expr),
            (v_ref_b, v_ref_b_expr),
            (v_ref_c, v_ref_c_expr),
            (m_a_u, m_a_u_expr),
            (m_b_u, m_b_u_expr),
            (m_c_u, m_c_u_expr),
            (m_a, m_a_expr),
            (m_b, m_b_expr),
            (m_c, m_c_expr),
            (v_p, v_p_expr),
            (v_n, v_n_expr),
            (gate_a, Const(0.0)),
            (gate_b, Const(0.0)),
            (gate_c, Const(0.0)),
            (v_leg_a, -v_leg_scale),
            (v_leg_b, -v_leg_scale),
            (v_leg_c, -v_leg_scale),
            (v_common_mode, Const(0.0)),
            (v_conv_a, v_conv_a_expr),
            (v_conv_b, v_conv_b_expr),
            (v_conv_c, v_conv_c_expr),
            (v_conv_d, v_conv_d_expr),
            (v_conv_q, v_conv_q_expr),
            (v_conv_0, v_conv_0_expr),
        ]),
        in_vars=list([
            theta_pll,
            v_cmd_d,
            v_cmd_q,
            v_cmd_0,
            v_dc,
            k_v_conv,
            m_max,
            vdc_floor,
            omega_sw,
            carrier_phase,
        ]),
        out_vars=list([
            gate_a,
            gate_b,
            gate_c,
            v_conv_a,
            v_conv_b,
            v_conv_c,
            m_a,
            m_b,
            m_c,
            v_conv_d,
            v_conv_q,
            v_conv_0,
        ]),
        procedural_logic=list([
            ThreePhaseCarrierPwmLogic(
                mod_a_var_name=m_a.name,
                mod_b_var_name=m_b.name,
                mod_c_var_name=m_c.name,
                gate_a_mode_var_name=gate_a_mode.name,
                gate_b_mode_var_name=gate_b_mode.name,
                gate_c_mode_var_name=gate_c_mode.name,
                omega_sw_var_name=omega_sw.name,
                carrier_phase_var_name=carrier_phase.name,
                name=f"three_phase_pwm_{name}",
            ),
        ]),
    )

    return templ
