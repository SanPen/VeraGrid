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
from VeraGridEngine.Utils.procedural_logic import ThreePhaseCarrierPwmLogic
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
    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.DynamicModelHostDevice
    templ.name = name
    templ.block.name = name

    # ------------------------------------------------------------------
    # External inputs.
    # ------------------------------------------------------------------
    theta_pll: Var = vf.add_var(name=f"theta_pll_in")
    omega_base: Var = vf.add_var(name=f"omega_base_in")
    v_cmd_d: Var = vf.add_var(name=f"v_cmd_d_in")
    v_cmd_q: Var = vf.add_var(name=f"v_cmd_q_in")
    v_cmd_0: Var = vf.add_var(name=f"v_cmd_0_in")
    v_dc: Var = vf.add_var(name=f"v_dc_in")
    k_v_conv: Var = vf.add_var(name=f"k_v_conv_in")
    m_max: Var = vf.add_var(name=f"m_max_in")
    vdc_floor: Var = vf.add_var(name=f"vdc_floor_in")
    omega_sw: Var = vf.add_var(name=f"omega_sw_in")
    carrier_phase: Var = vf.add_var(name=f"carrier_phase_in")

    # ------------------------------------------------------------------
    # Internal modulation and gate variables.
    # ------------------------------------------------------------------
    v_ref_a_raw: Var = vf.add_var(name=f"v_ref_a_raw")
    v_ref_b_raw: Var = vf.add_var(name=f"v_ref_b_raw")
    v_ref_c_raw: Var = vf.add_var(name=f"v_ref_c_raw")
    v_ref_common_inj: Var = vf.add_var(name=f"v_ref_common_inj")
    v_ref_a: Var = vf.add_var(name=f"v_ref_a")
    v_ref_b: Var = vf.add_var(name=f"v_ref_b")
    v_ref_c: Var = vf.add_var(name=f"v_ref_c")
    theta_pwm_sample: Var = vf.add_var(name=f"theta_pwm_sample")
    v_ref_a_pwm: Var = vf.add_var(name=f"v_ref_a_pwm")
    v_ref_b_pwm: Var = vf.add_var(name=f"v_ref_b_pwm")
    v_ref_c_pwm: Var = vf.add_var(name=f"v_ref_c_pwm")
    m_a_u: Var = vf.add_var(name=f"m_a_u")
    m_b_u: Var = vf.add_var(name=f"m_b_u")
    m_c_u: Var = vf.add_var(name=f"m_c_u")
    m_a: Var = vf.add_var(name=f"m_a")
    m_b: Var = vf.add_var(name=f"m_b")
    m_c: Var = vf.add_var(name=f"m_c")

    gate_a_mode: Var = vf.add_var(name=f"gate_a_mode")
    gate_b_mode: Var = vf.add_var(name=f"gate_b_mode")
    gate_c_mode: Var = vf.add_var(name=f"gate_c_mode")
    gate_a: Var = vf.add_var(name=f"gate_a")
    gate_b: Var = vf.add_var(name=f"gate_b")
    gate_c: Var = vf.add_var(name=f"gate_c")

    # ------------------------------------------------------------------
    # Internal DC rails and converter phase voltages.
    # ------------------------------------------------------------------
    v_p: Var = vf.add_var(name=f"v_p")
    v_n: Var = vf.add_var(name=f"v_n")
    v_leg_a: Var = vf.add_var(name=f"v_leg_a")
    v_leg_b: Var = vf.add_var(name=f"v_leg_b")
    v_leg_c: Var = vf.add_var(name=f"v_leg_c")
    v_common_mode: Var = vf.add_var(name=f"v_common_mode")
    v_conv_a: Var = vf.add_var(name=f"v_conv_a")
    v_conv_b: Var = vf.add_var(name=f"v_conv_b")
    v_conv_c: Var = vf.add_var(name=f"v_conv_c")
    v_conv_d: Var = vf.add_var(name=f"v_conv_d")
    v_conv_q: Var = vf.add_var(name=f"v_conv_q")
    v_conv_0: Var = vf.add_var(name=f"v_conv_0")

    # ------------------------------------------------------------------
    # Fixed numerical safeguards.
    # ------------------------------------------------------------------
    eps: Const = Const(1.0e-10)
    c_half: Const = Const(0.5)
    c_one: Const = Const(1.0)
    c_two: Const = Const(2.0)
    c_three: Const = Const(3.0)
    c_pi: Const = Const(np.pi)
    c13: Const = Const(1.0 / 3.0)
    c23: Const = Const(2.0 / 3.0)

    # ------------------------------------------------------------------
    # Bridge equations.
    # ------------------------------------------------------------------
    v_dc_eff: Expr = sym.max(v_dc, vdc_floor)

    # The pseudo-EMT inner loop interprets ``k_v_conv`` as the full bus-side voltage gain available
    # from modulation and the effective converter-side transformation ratio. The switched bridge must
    # therefore use the same full gain in both the modulation normalization and the reconstructed
    # pole-voltage scale; otherwise the bridge fundamental becomes systematically weaker than the
    # averaged reference that the controller was tuned against.
    v_mod_scale: Expr = sym.max(k_v_conv * v_dc_eff, eps)
    v_leg_scale: Expr = k_v_conv * v_dc_eff
    pwm_sample_enable: Expr = omega_sw / sym.max(omega_sw, eps)
    pwm_sample_phase_lead: Expr = pwm_sample_enable * omega_base * c_pi / (c_two * sym.max(omega_sw, eps))
    theta_pwm_sample_expr: Expr = theta_pll + pwm_sample_phase_lead

    v_ref_a_raw_expr: Expr
    v_ref_b_raw_expr: Expr
    v_ref_c_raw_expr: Expr
    v_ref_common_inj_expr: Expr
    v_ref_a_expr: Expr
    v_ref_b_expr: Expr
    v_ref_c_expr: Expr
    v_ref_a_pwm_raw_expr: Expr
    v_ref_b_pwm_raw_expr: Expr
    v_ref_c_pwm_raw_expr: Expr
    v_ref_common_inj_pwm_expr: Expr
    v_ref_a_pwm_expr: Expr
    v_ref_b_pwm_expr: Expr
    v_ref_c_pwm_expr: Expr
    v_ref_a_raw_expr, v_ref_b_raw_expr, v_ref_c_raw_expr = _inverse_dq0_to_abc_expressions(
        d_value=v_cmd_d,
        q_value=v_cmd_q,
        zero_value=v_cmd_0,
        theta_value=theta_pll,
    )
    v_ref_a_pwm_raw_expr, v_ref_b_pwm_raw_expr, v_ref_c_pwm_raw_expr = _inverse_dq0_to_abc_expressions(
        d_value=v_cmd_d,
        q_value=v_cmd_q,
        zero_value=v_cmd_0,
        # The PWM schedule holds one sampled modulation command over the full carrier half-period.
        # Advancing only the sampled phase reference by half that interval compensates the hold delay
        # without perturbing the continuous averaged bridge reference used by the hybrid handover path.
        theta_value=theta_pwm_sample_expr,
    )

    # Standard zero-sequence injection improves the linear modulation range of the switched bridge.
    # Without it the bridge saturates too early and the hybrid switched converter diverges from the
    # physically meaningful pseudo-EMT reference under the same operating point.
    v_ref_common_inj_expr = Const(0.5) * (
        sym.max(sym.max(v_ref_a_raw_expr, v_ref_b_raw_expr), v_ref_c_raw_expr)
        + sym.min(sym.min(v_ref_a_raw_expr, v_ref_b_raw_expr), v_ref_c_raw_expr)
    )
    v_ref_common_inj_pwm_expr = Const(0.5) * (
        sym.max(sym.max(v_ref_a_pwm_raw_expr, v_ref_b_pwm_raw_expr), v_ref_c_pwm_raw_expr)
        + sym.min(sym.min(v_ref_a_pwm_raw_expr, v_ref_b_pwm_raw_expr), v_ref_c_pwm_raw_expr)
    )
    v_ref_a_expr = v_ref_a_raw_expr - v_ref_common_inj_expr
    v_ref_b_expr = v_ref_b_raw_expr - v_ref_common_inj_expr
    v_ref_c_expr = v_ref_c_raw_expr - v_ref_common_inj_expr
    v_ref_a_pwm_expr = v_ref_a_pwm_raw_expr - v_ref_common_inj_pwm_expr
    v_ref_b_pwm_expr = v_ref_b_pwm_raw_expr - v_ref_common_inj_pwm_expr
    v_ref_c_pwm_expr = v_ref_c_pwm_raw_expr - v_ref_common_inj_pwm_expr

    m_a_u_expr: Expr = v_ref_a_pwm_expr / v_mod_scale
    m_b_u_expr: Expr = v_ref_b_pwm_expr / v_mod_scale
    m_c_u_expr: Expr = v_ref_c_pwm_expr / v_mod_scale
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
            v_ref_a_raw,
            v_ref_b_raw,
            v_ref_c_raw,
            v_ref_common_inj,
            v_ref_a,
            v_ref_b,
            v_ref_c,
            theta_pwm_sample,
            v_ref_a_pwm,
            v_ref_b_pwm,
            v_ref_c_pwm,
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
        event_dict=dict([
            # The procedural PWM logic needs the switching frequency retained as a runtime parameter even
            # when connected symbolic inputs are pruned from the final problem tree.
            (omega_sw, Const(2.0 * np.pi * 1000.0)),
            # The procedural PWM logic needs the carrier phase stored as a runtime parameter even when
            # the symbolic problem prunes unused input variables from the retained block tree.
            (carrier_phase, Const(0.0)),
        ]),
        mode_dict=dict([
            (gate_a_mode, Const(0.0)),
            (gate_b_mode, Const(0.0)),
            (gate_c_mode, Const(0.0)),
        ]),
        init_eqs=dict([
            (v_ref_a_raw, v_ref_a_raw_expr),
            (v_ref_b_raw, v_ref_b_raw_expr),
            (v_ref_c_raw, v_ref_c_raw_expr),
            (v_ref_common_inj, v_ref_common_inj_expr),
            (v_ref_a, v_ref_a_expr),
            (v_ref_b, v_ref_b_expr),
            (v_ref_c, v_ref_c_expr),
            (theta_pwm_sample, theta_pwm_sample_expr),
            (v_ref_a_pwm, v_ref_a_pwm_expr),
            (v_ref_b_pwm, v_ref_b_pwm_expr),
            (v_ref_c_pwm, v_ref_c_pwm_expr),
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
            omega_base,
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
            v_ref_a_raw,
            v_ref_b_raw,
            v_ref_c_raw,
            v_ref_common_inj,
            v_ref_a,
            v_ref_b,
            v_ref_c,
            m_a_u,
            m_b_u,
            m_c_u,
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
                name=f"three_phase_pwm",
            ),
        ]),
    )

    return templ
