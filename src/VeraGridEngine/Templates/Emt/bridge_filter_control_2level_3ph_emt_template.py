# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.bridge_filter_2level_3ph_emt_template import get_bridge_filter_2level_3ph_emt_template
from VeraGridEngine.Templates.Emt.converter_emt_template import _build_pseudo_emt_converter_pll_block
from VeraGridEngine.Utils.Symbolic.block import Block, find_name_in_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType


def _build_bridge_filter_current_control_block(vf: VarFactory, name: str) -> Block:
    """
    Build one standalone dq0 current controller for the bridge + filter stage.

    The controller is intentionally simpler than the full converter inner loop:
    it only regulates the dq0 currents against direct current references and uses
    a fixed voltage scaling factor for the modulation limit. This keeps the
    incremental bridge validation compact and well isolated from the outer VSC
    hierarchy.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name suffix.
    :return: dq0 current-controller block.
    """
    v_d: Var = vf.add_var(name=f"v_d_ctrl_in_{name}")
    v_q: Var = vf.add_var(name=f"v_q_ctrl_in_{name}")
    v_0: Var = vf.add_var(name=f"v_0_ctrl_in_{name}")
    i_d: Var = vf.add_var(name=f"i_d_ctrl_in_{name}")
    i_q: Var = vf.add_var(name=f"i_q_ctrl_in_{name}")
    i_0: Var = vf.add_var(name=f"i_0_ctrl_in_{name}")
    omega_pll: Var = vf.add_var(name=f"omega_pll_ctrl_in_{name}")
    omega_base: Var = vf.add_var(name=f"omega_base_ctrl_in_{name}")
    R_f: Var = vf.add_var(name=f"R_f_ctrl_in_{name}")
    L_f: Var = vf.add_var(name=f"L_f_ctrl_in_{name}")
    i_d_ref: Var = vf.add_var(name=f"i_d_ref_ctrl_in_{name}")
    i_q_ref: Var = vf.add_var(name=f"i_q_ref_ctrl_in_{name}")
    i_0_ref: Var = vf.add_var(name=f"i_0_ref_ctrl_in_{name}")
    i_kp: Var = vf.add_var(name=f"i_kp_ctrl_in_{name}")
    i_ki: Var = vf.add_var(name=f"i_ki_ctrl_in_{name}")
    aw_gain: Var = vf.add_var(name=f"aw_gain_ctrl_in_{name}")
    m_max: Var = vf.add_var(name=f"m_max_ctrl_in_{name}")
    v_dc: Var = vf.add_var(name=f"v_dc_ctrl_in_{name}")
    vdc_floor: Var = vf.add_var(name=f"vdc_floor_ctrl_in_{name}")
    k_v_conv: Var = vf.add_var(name=f"k_v_conv_ctrl_in_{name}")

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
    v_lim: Var = vf.add_var(name=f"v_lim_{name}")
    v_cmd_d: Var = vf.add_var(name=f"v_cmd_d_{name}")
    v_cmd_q: Var = vf.add_var(name=f"v_cmd_q_{name}")
    v_cmd_0: Var = vf.add_var(name=f"v_cmd_0_{name}")

    eps: Const = Const(1.0e-10)
    c0: Const = Const(0.0)
    v_dc_eff: Expr = sym.max(v_dc, vdc_floor)
    omega_ratio: Expr = omega_pll / (omega_base + eps)
    v_d_cap: Expr = sym.hard_sat(v_cmd_d_u, -v_lim, v_lim)
    v_q_cap: Expr = sym.sqrt(sym.max(v_lim * v_lim - v_cmd_d * v_cmd_d, eps))
    v_0_cap: Expr = sym.sqrt(sym.max((v_lim * v_lim - v_cmd_d * v_cmd_d - v_cmd_q * v_cmd_q) / Const(3.0), eps / Const(3.0)))

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
            # The decoupling terms follow the same dq branch equations as the proven EMT current loop.
            v_cmd_d_u - (v_d - R_f * i_d + omega_ratio * L_f * i_q - v_pi_d_u),
            v_cmd_q_u - (v_q - R_f * i_q - omega_ratio * L_f * i_d - v_pi_q_u),
            v_cmd_0_u - (v_0 - R_f * i_0 - v_pi_0_u),
            v_lim - (k_v_conv * m_max * v_dc_eff),
            v_cmd_d - v_d_cap,
            v_cmd_q - sym.hard_sat(v_cmd_q_u, -v_q_cap, v_q_cap),
            v_cmd_0 - sym.hard_sat(v_cmd_0_u, -v_0_cap, v_0_cap),
        ]),
        algebraic_vars=list([v_pi_d_u, v_pi_q_u, v_pi_0_u, v_cmd_d_u, v_cmd_q_u, v_cmd_0_u, v_lim, v_cmd_d, v_cmd_q, v_cmd_0]),
        init_eqs=dict([
            (xi_id, c0),
            (xi_iq, c0),
            (xi_i0, c0),
            (v_pi_d_u, c0),
            (v_pi_q_u, c0),
            (v_pi_0_u, c0),
            (v_cmd_d_u, c0),
            (v_cmd_q_u, c0),
            (v_cmd_0_u, c0),
            (v_lim, k_v_conv * m_max * v_dc_eff),
            (v_cmd_d, c0),
            (v_cmd_q, c0),
            (v_cmd_0, c0),
        ]),
        diff_init_eqs=dict([
            (d_xi_id, c0),
            (d_xi_iq, c0),
            (d_xi_i0, c0),
        ]),
        in_vars=list([v_d, v_q, v_0, i_d, i_q, i_0, omega_pll, omega_base, R_f, L_f, i_d_ref, i_q_ref, i_0_ref, i_kp, i_ki, aw_gain, m_max, v_dc, vdc_floor, k_v_conv]),
        out_vars=list([v_cmd_d, v_cmd_q, v_cmd_0]),
        name=f"{name}_current_ctrl",
    )


def get_bridge_filter_control_2level_3ph_emt_template(vf: VarFactory, name: str = "bridge_filter_control_2level_3ph_emt") -> EmtModelTemplate:
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

    theta_pll_in: Var = vf.add_var(name=f"theta_pll_in_{name}")
    omega_base_in: Var = vf.add_var(name=f"omega_base_in_{name}")
    v_A_in: Var = vf.add_var(name=f"v_A_in_{name}")
    v_B_in: Var = vf.add_var(name=f"v_B_in_{name}")
    v_C_in: Var = vf.add_var(name=f"v_C_in_{name}")
    v_dc_in: Var = vf.add_var(name=f"v_dc_in_{name}")
    i_d_ref_in: Var = vf.add_var(name=f"i_d_ref_in_{name}")
    i_q_ref_in: Var = vf.add_var(name=f"i_q_ref_in_{name}")
    i_0_ref_in: Var = vf.add_var(name=f"i_0_ref_in_{name}")
    k_v_conv_in: Var = vf.add_var(name=f"k_v_conv_in_{name}")
    m_max_in: Var = vf.add_var(name=f"m_max_in_{name}")
    vdc_floor_in: Var = vf.add_var(name=f"vdc_floor_in_{name}")
    omega_sw_in: Var = vf.add_var(name=f"omega_sw_in_{name}")
    carrier_phase_in: Var = vf.add_var(name=f"carrier_phase_in_{name}")
    R_f_in: Var = vf.add_var(name=f"R_f_in_{name}")
    L_f_in: Var = vf.add_var(name=f"L_f_in_{name}")
    pll_kp_in: Var = vf.add_var(name=f"pll_kp_in_{name}")
    pll_ki_in: Var = vf.add_var(name=f"pll_ki_in_{name}")
    i_kp_in: Var = vf.add_var(name=f"i_kp_in_{name}")
    i_ki_in: Var = vf.add_var(name=f"i_ki_in_{name}")
    aw_gain_in: Var = vf.add_var(name=f"aw_gain_in_{name}")
    phi_v_in: Var = vf.add_var(name=f"phi_v_in_{name}")

    plant_block: Block = get_bridge_filter_2level_3ph_emt_template(vf=vf, name=f"{name}_plant").block
    pll_block: Block = _build_pseudo_emt_converter_pll_block(vf=vf, name=name)
    current_ctrl_block: Block = _build_bridge_filter_current_control_block(vf=vf, name=name)

    plant_i_A: Var = find_name_in_block(f"i_A_{name}_plant", plant_block)
    plant_i_B: Var = find_name_in_block(f"i_B_{name}_plant", plant_block)
    plant_i_C: Var = find_name_in_block(f"i_C_{name}_plant", plant_block)
    plant_i_d: Var = find_name_in_block(f"i_d_{name}_plant", plant_block)
    plant_i_q: Var = find_name_in_block(f"i_q_{name}_plant", plant_block)
    plant_i_0: Var = find_name_in_block(f"i_0_{name}_plant", plant_block)
    plant_v_d: Var = find_name_in_block(f"v_d_{name}_plant", plant_block)
    plant_v_q: Var = find_name_in_block(f"v_q_{name}_plant", plant_block)
    plant_v_0: Var = find_name_in_block(f"v_0_{name}_plant", plant_block)
    plant_gate_a: Var = find_name_in_block(f"gate_a_{name}_plant_bridge", plant_block)
    plant_gate_b: Var = find_name_in_block(f"gate_b_{name}_plant_bridge", plant_block)
    plant_gate_c: Var = find_name_in_block(f"gate_c_{name}_plant_bridge", plant_block)
    plant_v_conv_a: Var = find_name_in_block(f"v_conv_a_{name}_plant_bridge", plant_block)
    plant_v_conv_b: Var = find_name_in_block(f"v_conv_b_{name}_plant_bridge", plant_block)
    plant_v_conv_c: Var = find_name_in_block(f"v_conv_c_{name}_plant_bridge", plant_block)
    pll_theta: Var = find_name_in_block(f"theta_pll_{name}", pll_block)
    pll_omega: Var = find_name_in_block(f"omega_pll_{name}", pll_block)
    ctrl_v_cmd_d: Var = find_name_in_block(f"v_cmd_d_{name}", current_ctrl_block)
    ctrl_v_cmd_q: Var = find_name_in_block(f"v_cmd_q_{name}", current_ctrl_block)
    ctrl_v_cmd_0: Var = find_name_in_block(f"v_cmd_0_{name}", current_ctrl_block)

    if plant_i_A is None or plant_i_B is None or plant_i_C is None or plant_i_d is None or plant_i_q is None or plant_i_0 is None or plant_v_d is None or plant_v_q is None or plant_v_0 is None or plant_gate_a is None or plant_gate_b is None or plant_gate_c is None or plant_v_conv_a is None or plant_v_conv_b is None or plant_v_conv_c is None or pll_theta is None or pll_omega is None or ctrl_v_cmd_d is None or ctrl_v_cmd_q is None or ctrl_v_cmd_0 is None:
        raise KeyError(f"The bridge + filter + control template '{name}' could not resolve one or more internal variables")
    else:
        pass

    # The plant receives electrical inputs and the voltage commands produced by the current controller.
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
        k_v_conv_in,
        m_max_in,
        vdc_floor_in,
        omega_sw_in,
        carrier_phase_in,
        R_f_in,
        L_f_in,
    ]))

    # The PLL uses the q-axis plant voltage exactly as in the converter EMT hierarchy.
    pll_block.connect(pll_block.in_vars[0:5], list([
        plant_v_q,
        omega_base_in,
        pll_kp_in,
        pll_ki_in,
        phi_v_in,
    ]))

    # The current controller regulates the plant dq currents against explicit references.
    current_ctrl_block.connect(current_ctrl_block.in_vars[0:20], list([
        plant_v_d,
        plant_v_q,
        plant_v_0,
        plant_i_d,
        plant_i_q,
        plant_i_0,
        pll_omega,
        omega_base_in,
        R_f_in,
        L_f_in,
        i_d_ref_in,
        i_q_ref_in,
        i_0_ref_in,
        i_kp_in,
        i_ki_in,
        aw_gain_in,
        m_max_in,
        v_dc_in,
        vdc_floor_in,
        k_v_conv_in,
    ]))

    templ.block.children.extend(list([plant_block, pll_block, current_ctrl_block]))
    templ.block.unify_blocks()
    templ.block.in_vars = list([
        theta_pll_in,
        omega_base_in,
        v_A_in,
        v_B_in,
        v_C_in,
        v_dc_in,
        i_d_ref_in,
        i_q_ref_in,
        i_0_ref_in,
        k_v_conv_in,
        m_max_in,
        vdc_floor_in,
        omega_sw_in,
        carrier_phase_in,
        R_f_in,
        L_f_in,
        pll_kp_in,
        pll_ki_in,
        i_kp_in,
        i_ki_in,
        aw_gain_in,
        phi_v_in,
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
        pll_theta,
        pll_omega,
    ])

    return templ
