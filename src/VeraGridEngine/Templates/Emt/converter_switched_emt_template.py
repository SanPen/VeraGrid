# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.bridge_filter_control_2level_3ph_emt_template import get_bridge_filter_control_2level_3ph_emt_template
from VeraGridEngine.Templates.Emt.converter_emt_template import (
    _build_pseudo_emt_converter_outer_loop_block,
    _resolve_converter_control_reference_exprs,
)
from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowRefferenceType, find_name_in_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType


def _build_switched_converter_data_block(vf: VarFactory, name: str) -> Block:
    """
    Build the parameter and DC-link block of the switched EMT converter.

    The block preserves the same outer VSC control contract as the averaged EMT
    converter. The key difference is that the DC-link capacitor current is driven
    by the switched bridge current instead of by an averaged power-balance source.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name suffix.
    :return: Data and DC-link block.
    """
    v_d: Var = vf.add_var(name=f"v_d_in_{name}")
    v_q: Var = vf.add_var(name=f"v_q_in_{name}")
    v_0: Var = vf.add_var(name=f"v_0_in_{name}")
    i_d: Var = vf.add_var(name=f"i_d_in_{name}")
    i_q: Var = vf.add_var(name=f"i_q_in_{name}")
    i_0: Var = vf.add_var(name=f"i_0_in_{name}")
    i_A: Var = vf.add_var(name=f"i_A_in_{name}")
    i_B: Var = vf.add_var(name=f"i_B_in_{name}")
    i_C: Var = vf.add_var(name=f"i_C_in_{name}")
    gate_a: Var = vf.add_var(name=f"gate_a_in_{name}")
    gate_b: Var = vf.add_var(name=f"gate_b_in_{name}")
    gate_c: Var = vf.add_var(name=f"gate_c_in_{name}")
    v_dc_bus: Var = vf.add_var(name=f"v_dc_bus_in_{name}")
    switching_enabled: Var = vf.add_var(name=f"switching_enabled_in_{name}")

    v_dc: Var = vf.add_var(name=f"v_dc_{name}")
    i_dc: Var = vf.add_var(name=f"i_dc_{name}", reference=VarPowerFlowRefferenceType.Idc)
    P: Var = vf.add_var(name=f"P_{name}", reference=VarPowerFlowRefferenceType.P)
    Q: Var = vf.add_var(name=f"Q_{name}", reference=VarPowerFlowRefferenceType.Q)
    i_mag: Var = vf.add_var(name=f"i_mag_{name}")
    i_dc_conv: Var = vf.add_var(name=f"i_dc_conv_{name}")
    k_v_conv_nom: Var = vf.add_var(name=f"k_v_conv_nom_{name}")
    P_ref: Var = vf.add_var(name=f"P_ref_{name}")
    Q_ref: Var = vf.add_var(name=f"Q_ref_{name}")
    Vdc_ref: Var = vf.add_var(name=f"Vdc_ref_{name}")

    sbase: Var = vf.add_var(name=f"sbase_{name}")
    P0_sched: Var = vf.add_var(name=f"P0_{name}")
    control1: Var = vf.add_var(name=f"control1_{name}")
    control2: Var = vf.add_var(name=f"control2_{name}")
    control1_val: Var = vf.add_var(name=f"control1_val_{name}")
    control2_val: Var = vf.add_var(name=f"control2_val_{name}")
    omega_base: Var = vf.add_var(name=f"omega_base_{name}")
    phi_v: Var = vf.add_var(name=f"phi_v_{name}")
    Vpk: Var = vf.add_var(name=f"Vpk_{name}")
    R_eq: Var = vf.add_var(name=f"R_eq_{name}")
    L_eq: Var = vf.add_var(name=f"L_eq_{name}")
    pll_kp: Var = vf.add_var(name=f"pll_kp_{name}")
    pll_ki: Var = vf.add_var(name=f"pll_ki_{name}")
    i_kp: Var = vf.add_var(name=f"i_kp_{name}")
    i_ki: Var = vf.add_var(name=f"i_ki_{name}")
    vdc_kp: Var = vf.add_var(name=f"vdc_kp_{name}")
    vdc_ki: Var = vf.add_var(name=f"vdc_ki_{name}")
    q_kp: Var = vf.add_var(name=f"q_kp_{name}")
    q_ki: Var = vf.add_var(name=f"q_ki_{name}")
    i_max: Var = vf.add_var(name=f"i_max_{name}")
    m_max: Var = vf.add_var(name=f"m_max_{name}")
    P_loss0: Var = vf.add_var(name=f"P_loss0_{name}")
    tau_meas: Var = vf.add_var(name=f"tau_meas_{name}")
    aw_gain: Var = vf.add_var(name=f"aw_gain_{name}")
    vdc_floor: Var = vf.add_var(name=f"vdc_floor_{name}")
    omega_sw: Var = vf.add_var(name=f"omega_sw_{name}")
    carrier_phase: Var = vf.add_var(name=f"carrier_phase_{name}")

    p_ref_expr: Expr
    q_ref_expr: Expr
    vdc_ref_expr: Expr
    _unused_regulate_vdc: Expr
    _unused_regulate_q: Expr
    p_ref_expr, q_ref_expr, vdc_ref_expr, _unused_regulate_vdc, _unused_regulate_q = _resolve_converter_control_reference_exprs(
        control1=control1,
        control2=control2,
        control1_val=control1_val,
        control2_val=control2_val,
        p0=P0_sched,
    )

    eps: Const = Const(1.0e-10)
    c32: Const = Const(1.5)
    c_three: Const = Const(3.0)
    c_one: Const = Const(1.0)
    v_dc_eff: Expr = sym.max(v_dc, vdc_floor)
    p_expr: Expr = c32 * (v_d * i_d + v_q * i_q) + c_three * v_0 * i_0
    q_expr: Expr = c32 * (v_d * i_q - v_q * i_d)
    i_mag_expr: Expr = sym.sqrt(i_d * i_d + i_q * i_q + c_three * i_0 * i_0 + eps)
    i_dc_sw_expr: Expr = -(gate_a * i_A + gate_b * i_B + gate_c * i_C)
    p_loss0_pu_expr: Expr = P_loss0 / sym.max(sbase, eps)
    i_dc_avg_expr: Expr = -(p_expr - p_loss0_pu_expr) / v_dc_eff
    i_dc_expr: Expr = (c_one - switching_enabled) * i_dc_avg_expr + switching_enabled * i_dc_sw_expr
    k_v_conv_nom_expr: Expr = Vpk / (m_max * sym.max(Vdc_ref, vdc_floor) + eps)

    block: Block = Block(
        algebraic_eqs=list([
            v_dc - v_dc_bus,
            P_ref - p_ref_expr,
            Q_ref - q_ref_expr,
            Vdc_ref - vdc_ref_expr,
            P - p_expr,
            Q - q_expr,
            i_mag - i_mag_expr,
            i_dc_conv - i_dc_sw_expr,
            k_v_conv_nom - k_v_conv_nom_expr,
            i_dc - i_dc_expr,
        ]),
        algebraic_vars=list([
            v_dc,
            i_dc,
            P,
            Q,
            i_mag,
            i_dc_conv,
            k_v_conv_nom,
            P_ref,
            Q_ref,
            Vdc_ref,
        ]),
        event_dict=dict([
            (sbase, Const(100.0)),
            (P0_sched, Const(0.0)),
            (control1, Const(float(1.0))),
            (control2, Const(float(4.0))),
            (control1_val, Const(1.0)),
            (control2_val, Const(0.0)),
            (omega_base, Const(2.0 * np.pi * 50.0)),
            (phi_v, Const(0.0)),
            (Vpk, Const(np.sqrt(2.0))),
            (R_eq, Const(max(0.02, 1.0e-9))),
            (L_eq, Const(max(0.08, 1.0e-9))),
            (pll_kp, Const(40.0)),
            (pll_ki, Const(400.0)),
            (i_kp, Const(0.5)),
            (i_ki, Const(40.0)),
            (vdc_kp, Const(1.5)),
            (vdc_ki, Const(30.0)),
            (q_kp, Const(0.6)),
            (q_ki, Const(25.0)),
            (i_max, Const(max(1.2, 1.0e-6))),
            (m_max, Const(max(0.95, 1.0e-6))),
            (P_loss0, Const(0.0)),
            (tau_meas, Const(max(0.01, 1.0e-6))),
            (aw_gain, Const(1.0)),
            (vdc_floor, Const(max(0.05, 1.0e-6))),
            (omega_sw, Const(2.0 * np.pi * 1000.0)),
            (carrier_phase, Const(0.0)),
        ]),
        init_eqs=dict([
            (v_dc, v_dc_bus),
            (P_ref, p_ref_expr),
            (Q_ref, q_ref_expr),
            (Vdc_ref, vdc_ref_expr),
            (P, p_expr),
            (Q, q_expr),
            (i_mag, i_mag_expr),
            (i_dc_conv, i_dc_sw_expr),
            (k_v_conv_nom, k_v_conv_nom_expr),
            (i_dc, i_dc_expr),
        ]),
        in_vars=list([
            v_d,
            v_q,
            v_0,
            i_d,
            i_q,
            i_0,
            i_A,
            i_B,
            i_C,
            gate_a,
            gate_b,
            gate_c,
            v_dc_bus,
            switching_enabled,
        ]),
        out_vars=list([
            v_dc,
            i_dc,
            P,
            Q,
            k_v_conv_nom,
            sbase,
            P_ref,
            Q_ref,
            Vdc_ref,
            omega_base,
            phi_v,
            Vpk,
            R_eq,
            L_eq,
            pll_kp,
            pll_ki,
            i_kp,
            i_ki,
            vdc_kp,
            vdc_ki,
            q_kp,
            q_ki,
            i_max,
            m_max,
            P_loss0,
            tau_meas,
            aw_gain,
            vdc_floor,
            omega_sw,
            carrier_phase,
        ]),
        name=f"{name}_switched_data",
    )

    block.api_obj_mapping = dict([
        (ParamPowerFlowRefferenceType.Sbase, sbase),
        (ParamPowerFlowRefferenceType.P0, P0_sched),
        (ParamPowerFlowRefferenceType.converter_loss_power_0, P_loss0),
        (ParamPowerFlowRefferenceType.omega_base, omega_base),
        (ParamPowerFlowRefferenceType.converter_control_mode_1, control1),
        (ParamPowerFlowRefferenceType.converter_control_mode_2, control2),
        (ParamPowerFlowRefferenceType.converter_control_target_1, control1_val),
        (ParamPowerFlowRefferenceType.converter_control_target_2, control2_val),
    ])

    return block


def _find_child_block_by_name(root_block: Block, block_name: str) -> Block | None:
    """
    Return one nested child block by its symbolic name.

    :param root_block: Root block to inspect.
    :param block_name: Requested block name.
    :return: Matching child block or ``None``.
    """
    child_block: Block
    nested_block: Block | None

    for child_block in root_block.children:
        if child_block.name == block_name:
            return child_block
        else:
            pass

        nested_block = _find_child_block_by_name(root_block=child_block, block_name=block_name)
        if nested_block is not None:
            return nested_block
        else:
            pass

    return None


def get_switched_emt_converter(vf: VarFactory, name: str = "switched_converter_emt") -> EmtModelTemplate:
    """
    Assemble a switched EMT converter with the same external interface as the averaged converter.

    The switched converter is rebuilt incrementally around the validated
    ``bridge + filter + control`` plant. The only reused piece from the averaged
    converter is the outer loop and the DC-side measurement/parameter block.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name.
    :return: Switched EMT converter template.
    """
    from VeraGridEngine.Utils.procedural_logic import startup_handover

    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.VscDevice
    templ.name = name
    templ.block.name = name

    v_A: Var = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowRefferenceType.v_A)
    v_B: Var = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowRefferenceType.v_B)
    v_C: Var = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowRefferenceType.v_C)
    v_dc_bus: Var = vf.add_var(name=f"v_dc_bus_{name}", reference=VarPowerFlowRefferenceType.Vdc)
    switching_enabled_mode: Var = vf.add_var(name=f"switching_enabled_mode_{name}")
    t_enable_sw: Var = vf.add_var(name=f"t_enable_sw_{name}")
    i_A: Var = vf.add_var(name=f"i_A_{name}", reference=VarPowerFlowRefferenceType.i_A)
    i_B: Var = vf.add_var(name=f"i_B_{name}", reference=VarPowerFlowRefferenceType.i_B)
    i_C: Var = vf.add_var(name=f"i_C_{name}", reference=VarPowerFlowRefferenceType.i_C)
    gate_a: Var = vf.add_var(name=f"gate_a_{name}")
    gate_b: Var = vf.add_var(name=f"gate_b_{name}")
    gate_c: Var = vf.add_var(name=f"gate_c_{name}")
    v_conv_a: Var = vf.add_var(name=f"v_conv_a_{name}")
    v_conv_b: Var = vf.add_var(name=f"v_conv_b_{name}")
    v_conv_c: Var = vf.add_var(name=f"v_conv_c_{name}")
    v_conv_d: Var = vf.add_var(name=f"v_conv_d_{name}")
    v_conv_q: Var = vf.add_var(name=f"v_conv_q_{name}")
    v_conv_0: Var = vf.add_var(name=f"v_conv_0_{name}")

    data_block: Block = _build_switched_converter_data_block(vf=vf, name=name)
    outer_loop_block: Block = _build_pseudo_emt_converter_outer_loop_block(vf=vf, name=name)
    plant_block: Block = get_bridge_filter_control_2level_3ph_emt_template(vf=vf, name=name).block
    filter_stage_block: Block = plant_block

    data_vdc: Var = find_name_in_block(f"v_dc_{name}", data_block)
    data_idc: Var = find_name_in_block(f"i_dc_{name}", data_block)
    data_p: Var = find_name_in_block(f"P_{name}", data_block)
    data_q: Var = find_name_in_block(f"Q_{name}", data_block)
    data_sbase: Var = find_name_in_block(f"sbase_{name}", data_block)
    data_p_ref: Var = find_name_in_block(f"P_ref_{name}", data_block)
    data_q_ref: Var = find_name_in_block(f"Q_ref_{name}", data_block)
    data_vdc_ref: Var = find_name_in_block(f"Vdc_ref_{name}", data_block)
    data_omega_base: Var = find_name_in_block(f"omega_base_{name}", data_block)
    data_phi_v: Var = find_name_in_block(f"phi_v_{name}", data_block)
    data_vpk: Var = find_name_in_block(f"Vpk_{name}", data_block)
    data_r_eq: Var = find_name_in_block(f"R_eq_{name}", data_block)
    data_l_eq: Var = find_name_in_block(f"L_eq_{name}", data_block)
    data_pll_kp: Var = find_name_in_block(f"pll_kp_{name}", data_block)
    data_pll_ki: Var = find_name_in_block(f"pll_ki_{name}", data_block)
    data_i_kp: Var = find_name_in_block(f"i_kp_{name}", data_block)
    data_i_ki: Var = find_name_in_block(f"i_ki_{name}", data_block)
    data_vdc_kp: Var = find_name_in_block(f"vdc_kp_{name}", data_block)
    data_vdc_ki: Var = find_name_in_block(f"vdc_ki_{name}", data_block)
    data_q_kp: Var = find_name_in_block(f"q_kp_{name}", data_block)
    data_q_ki: Var = find_name_in_block(f"q_ki_{name}", data_block)
    data_i_max: Var = find_name_in_block(f"i_max_{name}", data_block)
    data_m_max: Var = find_name_in_block(f"m_max_{name}", data_block)
    data_k_v_conv_nom: Var = find_name_in_block(f"k_v_conv_nom_{name}", data_block)
    data_p_loss0: Var = find_name_in_block(f"P_loss0_{name}", data_block)
    data_tau_meas: Var = find_name_in_block(f"tau_meas_{name}", data_block)
    data_aw_gain: Var = find_name_in_block(f"aw_gain_{name}", data_block)
    data_vdc_floor: Var = find_name_in_block(f"vdc_floor_{name}", data_block)
    data_omega_sw: Var = find_name_in_block(f"omega_sw_{name}", data_block)
    data_carrier_phase: Var = find_name_in_block(f"carrier_phase_{name}", data_block)

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
    plant_v_ref_a: Var = find_name_in_block(f"v_ref_a_{name}_plant_bridge", plant_block)
    plant_v_ref_b: Var = find_name_in_block(f"v_ref_b_{name}_plant_bridge", plant_block)
    plant_v_ref_c: Var = find_name_in_block(f"v_ref_c_{name}_plant_bridge", plant_block)
    plant_v_conv_a: Var = find_name_in_block(f"v_conv_a_{name}_plant_bridge", plant_block)
    plant_v_conv_b: Var = find_name_in_block(f"v_conv_b_{name}_plant_bridge", plant_block)
    plant_v_conv_c: Var = find_name_in_block(f"v_conv_c_{name}_plant_bridge", plant_block)
    plant_v_conv_d: Var = find_name_in_block(f"v_conv_d_{name}_plant_bridge", plant_block)
    plant_v_conv_q: Var = find_name_in_block(f"v_conv_q_{name}_plant_bridge", plant_block)
    plant_v_conv_0: Var = find_name_in_block(f"v_conv_0_{name}_plant_bridge", plant_block)
    plant_pll_theta: Var = find_name_in_block(f"theta_pll_{name}", plant_block)
    plant_pll_omega: Var = find_name_in_block(f"omega_pll_{name}", plant_block)
    plant_v_cmd_d: Var = find_name_in_block(f"v_cmd_d_{name}", plant_block)
    plant_v_cmd_q: Var = find_name_in_block(f"v_cmd_q_{name}", plant_block)
    plant_v_cmd_0: Var = find_name_in_block(f"v_cmd_0_{name}", plant_block)
    outer_i_0_ref: Var = find_name_in_block(f"i_0_ref_{name}", outer_loop_block)
    outer_i_d_ref: Var = find_name_in_block(f"i_d_ref_{name}", outer_loop_block)
    outer_i_q_ref: Var = find_name_in_block(f"i_q_ref_{name}", outer_loop_block)
    if data_vdc is None or data_idc is None or data_p is None or data_q is None or data_sbase is None or data_p_ref is None or data_q_ref is None or data_vdc_ref is None or data_omega_base is None or data_phi_v is None or data_vpk is None or data_r_eq is None or data_l_eq is None or data_pll_kp is None or data_pll_ki is None or data_i_kp is None or data_i_ki is None or data_vdc_kp is None or data_vdc_ki is None or data_q_kp is None or data_q_ki is None or data_i_max is None or data_m_max is None or data_k_v_conv_nom is None or data_p_loss0 is None or data_tau_meas is None or data_aw_gain is None or data_vdc_floor is None or data_omega_sw is None or data_carrier_phase is None or plant_i_A is None or plant_i_B is None or plant_i_C is None or plant_i_d is None or plant_i_q is None or plant_i_0 is None or plant_v_d is None or plant_v_q is None or plant_v_0 is None or plant_gate_a is None or plant_gate_b is None or plant_gate_c is None or plant_v_ref_a is None or plant_v_ref_b is None or plant_v_ref_c is None or plant_v_conv_a is None or plant_v_conv_b is None or plant_v_conv_c is None or plant_v_conv_d is None or plant_v_conv_q is None or plant_v_conv_0 is None or plant_pll_theta is None or plant_pll_omega is None or plant_v_cmd_d is None or plant_v_cmd_q is None or plant_v_cmd_0 is None or outer_i_0_ref is None or outer_i_d_ref is None or outer_i_q_ref is None:
        raise KeyError(f"The switched EMT converter '{name}' could not resolve one or more internal variables")
    else:
        pass

    one: Const = Const(1.0)
    averaged_mode: Expr = one - switching_enabled_mode

    # The bridge keeps switching procedurally from t = 0, but the RL filter only sees the discrete
    # bridge pole voltages after the exact startup handover time.
    filter_stage_block.state_eqs = list([
        equation.subs({
            plant_v_conv_a: v_conv_a,
            plant_v_conv_b: v_conv_b,
            plant_v_conv_c: v_conv_c,
        })
        for equation in filter_stage_block.state_eqs
    ])

    templ.block.algebraic_eqs.extend(list([
        i_A - plant_i_A,
        i_B - plant_i_B,
        i_C - plant_i_C,
        gate_a - plant_gate_a,
        gate_b - plant_gate_b,
        gate_c - plant_gate_c,
        v_conv_a - (averaged_mode * plant_v_ref_a + switching_enabled_mode * plant_v_conv_a),
        v_conv_b - (averaged_mode * plant_v_ref_b + switching_enabled_mode * plant_v_conv_b),
        v_conv_c - (averaged_mode * plant_v_ref_c + switching_enabled_mode * plant_v_conv_c),
        v_conv_d - (averaged_mode * plant_v_cmd_d + switching_enabled_mode * plant_v_conv_d),
        v_conv_q - (averaged_mode * plant_v_cmd_q + switching_enabled_mode * plant_v_conv_q),
        v_conv_0 - (averaged_mode * plant_v_cmd_0 + switching_enabled_mode * plant_v_conv_0),
    ]))
    templ.block.algebraic_vars.extend(list([
        i_A,
        i_B,
        i_C,
        gate_a,
        gate_b,
        gate_c,
        v_conv_a,
        v_conv_b,
        v_conv_c,
        v_conv_d,
        v_conv_q,
        v_conv_0,
    ]))
    templ.block.init_eqs.update(dict([
        (i_A, plant_i_A),
        (i_B, plant_i_B),
        (i_C, plant_i_C),
        (gate_a, plant_gate_a),
        (gate_b, plant_gate_b),
        (gate_c, plant_gate_c),
        (v_conv_a, averaged_mode * plant_v_ref_a + switching_enabled_mode * plant_v_conv_a),
        (v_conv_b, averaged_mode * plant_v_ref_b + switching_enabled_mode * plant_v_conv_b),
        (v_conv_c, averaged_mode * plant_v_ref_c + switching_enabled_mode * plant_v_conv_c),
        (v_conv_d, averaged_mode * plant_v_cmd_d + switching_enabled_mode * plant_v_conv_d),
        (v_conv_q, averaged_mode * plant_v_cmd_q + switching_enabled_mode * plant_v_conv_q),
        (v_conv_0, averaged_mode * plant_v_cmd_0 + switching_enabled_mode * plant_v_conv_0),
    ]))
    templ.block.event_dict.update(dict([
        (t_enable_sw, Const(1.0e-4)),
    ]))
    templ.block.mode_dict.update(dict([
        (switching_enabled_mode, Const(0.0)),
    ]))
    templ.block.procedural_logic.append(
        startup_handover(
            mode=switching_enabled_mode,
            t_enable=t_enable_sw,
            name=f"startup_handover_{name}",
        )
    )

    # The data block receives plant measurements, bridge currents and gate states, and the external DC bus voltage.
    data_block.connect(data_block.in_vars[0:14], list([
        plant_v_d,
        plant_v_q,
        plant_v_0,
        plant_i_d,
        plant_i_q,
        plant_i_0,
        plant_i_A,
        plant_i_B,
        plant_i_C,
        plant_gate_a,
        plant_gate_b,
        plant_gate_c,
        v_dc_bus,
        switching_enabled_mode,
    ]))

    # The outer loop is reused unchanged and receives the same measurements as the averaged converter.
    outer_loop_block.connect(outer_loop_block.in_vars[0:22], list([
        plant_v_d,
        plant_v_q,
        plant_v_0,
        plant_i_d,
        plant_i_q,
        plant_i_0,
        data_vdc,
        data_p,
        data_q,
        data_sbase,
        data_p_ref,
        data_q_ref,
        data_vdc_ref,
        data_vpk,
        data_p_loss0,
        data_vdc_kp,
        data_vdc_ki,
        data_q_kp,
        data_q_ki,
        data_i_max,
        data_tau_meas,
        data_aw_gain,
    ]))

    # The bridge + filter + control plant receives network voltages, control references and PWM parameters.
    plant_block.connect(plant_block.in_vars[0:22], list([
        data_phi_v,
        data_omega_base,
        v_A,
        v_B,
        v_C,
        data_vdc,
        outer_i_d_ref,
        outer_i_q_ref,
        outer_i_0_ref,
        data_k_v_conv_nom,
        data_m_max,
        data_vdc_floor,
        data_omega_sw,
        data_carrier_phase,
        data_r_eq,
        data_l_eq,
        data_pll_kp,
        data_pll_ki,
        data_i_kp,
        data_i_ki,
        data_aw_gain,
        data_phi_v,
    ]))

    templ.block.children.extend(list([data_block, outer_loop_block, plant_block]))
    templ.block.unify_blocks()
    templ.block.in_vars = list([v_A, v_B, v_C, v_dc_bus])
    templ.block.out_vars = list([
        i_A,
        i_B,
        i_C,
        data_idc,
        gate_a,
        gate_b,
        gate_c,
        v_conv_a,
        v_conv_b,
        v_conv_c,
        v_conv_d,
        v_conv_q,
        v_conv_0,
    ])

    templ.block.external_mapping = dict([
        (VarPowerFlowRefferenceType.v_N, None),
        (VarPowerFlowRefferenceType.v_A, v_A),
        (VarPowerFlowRefferenceType.v_B, v_B),
        (VarPowerFlowRefferenceType.v_C, v_C),
        (VarPowerFlowRefferenceType.Vdc, v_dc_bus),
        (VarPowerFlowRefferenceType.i_N, None),
        (VarPowerFlowRefferenceType.i_A, i_A),
        (VarPowerFlowRefferenceType.i_B, i_B),
        (VarPowerFlowRefferenceType.i_C, i_C),
        (VarPowerFlowRefferenceType.if_N, None),
        (VarPowerFlowRefferenceType.if_A, None),
        (VarPowerFlowRefferenceType.if_B, None),
        (VarPowerFlowRefferenceType.if_C, None),
        (VarPowerFlowRefferenceType.it_N, None),
        (VarPowerFlowRefferenceType.it_A, None),
        (VarPowerFlowRefferenceType.it_B, None),
        (VarPowerFlowRefferenceType.it_C, None),
        (VarPowerFlowRefferenceType.Sf_A, None),
        (VarPowerFlowRefferenceType.Sf_B, None),
        (VarPowerFlowRefferenceType.Sf_C, None),
        (VarPowerFlowRefferenceType.St_A, None),
        (VarPowerFlowRefferenceType.St_B, None),
        (VarPowerFlowRefferenceType.St_C, None),
        (VarPowerFlowRefferenceType.d_v_N_f, None),
        (VarPowerFlowRefferenceType.d_v_A_f, None),
        (VarPowerFlowRefferenceType.d_v_B_f, None),
        (VarPowerFlowRefferenceType.d_v_C_f, None),
        (VarPowerFlowRefferenceType.d_v_N_t, None),
        (VarPowerFlowRefferenceType.d_v_A_t, None),
        (VarPowerFlowRefferenceType.d_v_B_t, None),
        (VarPowerFlowRefferenceType.d_v_C_t, None),
        (VarPowerFlowRefferenceType.Idc, data_idc),
        (VarPowerFlowRefferenceType.P, data_p),
        (VarPowerFlowRefferenceType.Q, data_q),
        (VarPowerFlowRefferenceType.phi_v, data_phi_v),
        (VarPowerFlowRefferenceType.Vpk, data_vpk),
    ])

    templ.block.api_obj_mapping = dict(data_block.api_obj_mapping)

    return templ
