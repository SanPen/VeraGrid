#!/usr/bin/env python3

import math
import numpy as np

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.block_helpers import tf_to_block
from VeraGridEngine.enumerations import ConverterControlType, ParamPowerFlowReferenceType


def park_transform_block(vf, v_abc, theta, name: str):
    v_a, v_b, v_c = v_abc
    v_d = vf.add_var(f"vd_{name}")
    v_q = vf.add_var(f"vq_{name}")
    sqrt3 = vf.add_const(np.sqrt(3.0))
    c13 = vf.add_const(1.0 / 3.0)

    eqs = [
        v_d - c13 * (
            vf.add_const(2.0) * sym.cos(theta) * v_a
            + (-sym.cos(theta) - sqrt3 * sym.sin(theta)) * v_b
            + (-sym.cos(theta) + sqrt3 * sym.sin(theta)) * v_c
        ),
        v_q - c13 * (
            vf.add_const(2.0) * sym.sin(theta) * v_a
            + (-sym.sin(theta) + sqrt3 * sym.cos(theta)) * v_b
            + (-sym.sin(theta) - sqrt3 * sym.cos(theta)) * v_c
        ),
    ]
    return Block(algebraic_eqs=eqs, algebraic_vars=[v_d, v_q]), (v_d, v_q)


def inverse_park_currents_block(vf, i_d, i_q, theta, name: str):
    i_a = vf.add_var(f"i_A_{name}", reference=VarPowerFlowReferenceType.i_A)
    i_b = vf.add_var(f"i_B_{name}", reference=VarPowerFlowReferenceType.i_B)
    i_c = vf.add_var(f"i_C_{name}", reference=VarPowerFlowReferenceType.i_C)
    sqrt3 = vf.add_const(np.sqrt(3.0))
    half = vf.add_const(0.5)
    two = vf.add_const(2.0)

    eqs = [
        i_a - (i_d * sym.cos(theta) + i_q * sym.sin(theta)),
        i_b - ((-half * i_d - (sqrt3 / two) * i_q) * sym.cos(theta)
               + ((sqrt3 / two) * i_d - half * i_q) * sym.sin(theta)),
        i_c - ((-half * i_d + (sqrt3 / two) * i_q) * sym.cos(theta)
               + ((-sqrt3 / two) * i_d - half * i_q) * sym.sin(theta)),
    ]
    return Block(algebraic_eqs=eqs, algebraic_vars=[i_a, i_b, i_c]), (i_a, i_b, i_c)


def build_emt_gfm_aggregated_model(
    vf,
    name: str = "gfm_agg_emt",
    control1: ConverterControlType = ConverterControlType.Pac,
    control2: ConverterControlType = ConverterControlType.Qac,
) -> Block:
    _ = control1
    _ = control2

    v_a = vf.add_var(f"v_A_{name}", reference=VarPowerFlowReferenceType.v_A)
    v_b = vf.add_var(f"v_B_{name}", reference=VarPowerFlowReferenceType.v_B)
    v_c = vf.add_var(f"v_C_{name}", reference=VarPowerFlowReferenceType.v_C)

    theta = vf.add_var(f"theta_{name}")
    omega = vf.add_var(f"omega_{name}")
    dtheta = vf.add_diff_var(f"dtheta_{name}", base_var=theta)

    pt = vf.add_var(f"Pt_vsc_{name}")
    qt = vf.add_var(f"Qt_vsc_{name}")
    pf = vf.add_var(f"Pf_vsc_{name}")
    qf = vf.add_var(f"Qf_vsc_{name}")
    d_v_a = vf.add_var(f"d_v_A_{name}")
    d_v_b = vf.add_var(f"d_v_B_{name}")
    d_v_c = vf.add_var(f"d_v_C_{name}")

    vd_g = vf.add_var(f"vd_g_{name}")
    vq_g = vf.add_var(f"vq_g_{name}")
    vd_f = vf.add_var(f"vd_f_{name}")
    vq_f = vf.add_var(f"vq_f_{name}")
    vd_c = vf.add_var(f"vd_c_{name}")
    vq_c = vf.add_var(f"vq_c_{name}")

    id_g = vf.add_var(f"id_g_{name}")
    iq_g = vf.add_var(f"iq_g_{name}")
    id_c = vf.add_var(f"id_c_{name}")
    iq_c = vf.add_var(f"iq_c_{name}")

    p = vf.add_var(f"P_{name}")
    q = vf.add_var(f"Q_{name}")
    p_a = vf.add_var(f"P_A_{name}")
    p_b = vf.add_var(f"P_B_{name}")
    p_c = vf.add_var(f"P_C_{name}")
    q_a = vf.add_var(f"Q_A_{name}")
    q_b = vf.add_var(f"Q_B_{name}")
    q_c = vf.add_var(f"Q_C_{name}")
    p_ref = vf.add_var(f"P_ref_{name}")
    q_ref = vf.add_var(f"Q_ref_{name}")
    v_ref = vf.add_var(f"V_ref_{name}")
    v_mag = vf.add_var(f"V_{name}")
    vd_ref = vf.add_var(f"vd_ref_{name}")
    vq_ref = vf.add_var(f"vq_ref_{name}")

    id_ref = vf.add_var(f"id_ref_{name}")
    iq_ref = vf.add_var(f"iq_ref_{name}")
    id_ref_sat = vf.add_var(f"id_ref_sat_{name}")
    iq_ref_sat = vf.add_var(f"iq_ref_sat_{name}")
    vd_ctrl_out = vf.add_var(f"vd_ctrl_out_{name}")
    vq_ctrl_out = vf.add_var(f"vq_ctrl_out_{name}")
    vd_c_ref = vf.add_var(f"vd_c_ref_{name}")
    vq_c_ref = vf.add_var(f"vq_c_ref_{name}")

    Rf = vf.add_var(f"Rf_{name}")
    Lf = vf.add_var(f"Lf_{name}")
    Rc = vf.add_var(f"Rc_{name}")
    Lc = vf.add_var(f"Lc_{name}")
    Cf = vf.add_var(f"Cf_{name}")
    Rcap = vf.add_var(f"Rcap_{name}")
    Kdp = vf.add_var(f"Kdp_{name}")
    Kdq = vf.add_var(f"Kdq_{name}")
    fn = vf.add_var(f"fn_{name}")
    omega_base = vf.add_var(f"omega_base_{name}")
    Kp = vf.add_var(f"Kp_icl_{name}")
    Ki = vf.add_var(f"Ki_icl_{name}")
    tau_p = vf.add_var(f"tau_P_{name}")
    tau_q = vf.add_var(f"tau_Q_{name}")
    i_max = vf.add_var(f"I_max_{name}")
    a0 = vf.add_var(f"a0_{name}")
    a1 = vf.add_var(f"a1_{name}")
    a2 = vf.add_var(f"a2_{name}")

    park_v_block, (vd_bus, vq_bus) = park_transform_block(vf, [v_a, v_b, v_c], theta, name=f"{name}_bus")
    inv_i_block, (i_a, i_b, i_c) = inverse_park_currents_block(vf, id_g, iq_g, theta, name=name)

    eqs = [
        vd_g - vd_bus,
        vq_g - vq_bus,
        vd_f - vd_g - (Rc * id_g - omega * Lc * iq_g),
        vq_f - vq_g - (Rc * iq_g + omega * Lc * id_g),
        vd_c - vd_f - (Rf * id_c - omega * Lf * iq_c),
        vq_c - vq_f - (Rf * iq_c + omega * Lf * id_c),
        iq_c - iq_g - (-Cf * omega * vq_f + vd_f / Rcap),
        id_c - id_g - (Cf * omega * vd_f + vq_f / Rcap),
        p_a - (v_a * i_a),
        p_b - (v_b * i_b),
        p_c - (v_c * i_c),
        q_a - (vd_g * iq_g),
        q_b - (vf.add_const(-0.5) * vd_g * iq_g + vf.add_const(np.sqrt(3.0) / 2.0) * vq_g * iq_g),
        q_c - (vf.add_const(-0.5) * vd_g * iq_g - vf.add_const(np.sqrt(3.0) / 2.0) * vq_g * iq_g),
        p - (p_a + p_b + p_c),
        q - (q_a + q_b + q_c),
    ]

    block_p, p_lp = tf_to_block(vf, num=[vf.add_const(1.0)], den=[vf.add_const(1.0), tau_p], x=p, name=f"p_lp_{name}")
    block_q, q_lp = tf_to_block(vf, num=[vf.add_const(1.0)], den=[vf.add_const(1.0), tau_q], x=q, name=f"q_lp_{name}")
    block_p.init_eqs = {p_lp: p}
    block_q.init_eqs = {q_lp: q}

    eqs += [
        omega - (vf.add_const(1.0) - Kdp * (p_lp - p_ref)),
        v_mag - (v_ref - Kdq * (q_lp - q_ref)),
        dtheta - omega_base * omega,
        vd_ref - vf.add_const(0.0),
        vq_ref - v_mag,
    ]

    block_vd, id_hat = tf_to_block(vf, num=[Ki, Kp], den=[0, 1], x=vd_ref - vd_f, name=f"vd_loop_{name}")
    block_vq, iq_hat = tf_to_block(vf, num=[Ki, Kp], den=[0, 1], x=vq_ref - vq_f, name=f"vq_loop_{name}")

    id_raw = iq_hat + iq_g - Cf * omega * vq_f
    iq_raw = id_hat + id_g + Cf * omega * vd_f
    iq_for_lim = sym.max(iq_c, iq_raw)
    id_lim = sym.sqrt(sym.max(i_max ** 2 - iq_for_lim ** 2, vf.add_const(1e-5)))

    eqs += [
        id_ref_sat - sym.hard_sat(id_raw, -id_lim, id_lim),
        iq_ref_sat - sym.hard_sat(iq_raw, -i_max, i_max),
        id_ref - id_ref_sat,
        iq_ref - iq_ref_sat,
    ]

    block_id, vd_hat = tf_to_block(vf, num=[Ki, Kp], den=[0, 1], x=id_ref - id_c, y=vd_ctrl_out, name=f"id_loop_{name}")
    block_iq, vq_hat = tf_to_block(vf, num=[Ki, Kp], den=[0, 1], x=iq_ref - iq_c, y=vq_ctrl_out, name=f"iq_loop_{name}")

    eqs += [
        vd_c_ref - (vd_hat + vd_f - Lf * omega * iq_c),
        vq_c_ref - (vq_hat + vq_f + Lf * omega * id_c),
        vd_c - vd_c_ref,
        vq_c - vq_c_ref,
        pt + p,
        qt + q,
    ]

    im = sym.sqrt(id_c ** 2 + iq_c ** 2 + vf.add_const(1e-5))
    p_loss = a0 + a1 * im + a2 * im ** 2
    p_conv = vf.add_const(1.5) * (vq_c * iq_c + vd_c * id_c)
    eqs += [
        pf + p_conv - p_loss,
        qf - vf.add_const(0.0),
        d_v_a - vf.add_const(0.0),
        d_v_b - vf.add_const(0.0),
        d_v_c - vf.add_const(0.0),
    ]

    model = Block(
        algebraic_eqs=eqs,
        algebraic_vars=[
            pt, qt, pf, qf, d_v_a, d_v_b, d_v_c, p, q, p_ref, q_ref, omega, theta, v_mag, v_ref,
            p_a, p_b, p_c, q_a, q_b, q_c,
            vd_ref, vq_ref, vd_g, vq_g, vd_f, vq_f, vd_c, vq_c,
            id_g, iq_g, id_c, iq_c, id_ref, iq_ref, id_ref_sat, iq_ref_sat, vd_c_ref, vq_c_ref,
        ],
        diff_vars=[dtheta],
        event_dict={
            Rf: vf.add_const(0.02), Lf: vf.add_const(0.15), Rc: vf.add_const(0.01), Lc: vf.add_const(0.1),
            Cf: vf.add_const(0.05), Rcap: vf.add_const(1e6), Kdp: vf.add_const(0.05), Kdq: vf.add_const(0.05),
            fn: vf.add_const(50.0), omega_base: vf.add_const(2.0 * math.pi * 50.0), Kp: vf.add_const(0.05), Ki: vf.add_const(50.0), tau_p: vf.add_const(0.01),
            tau_q: vf.add_const(0.01), i_max: vf.add_const(1.2), a0: vf.add_const(0.0), a1: vf.add_const(0.0), a2: vf.add_const(0.0),
        },
        init_eqs={
            theta: vf.add_const(0.0), omega: vf.add_const(1.0),
            p: -pt, q: -qt, p_ref: p, q_ref: q,
            p_a: vf.add_const(0.0), p_b: vf.add_const(0.0), p_c: vf.add_const(0.0),
            q_a: vf.add_const(0.0), q_b: vf.add_const(0.0), q_c: vf.add_const(0.0),
            v_ref: vf.add_const(1.0), v_mag: vf.add_const(1.0),
            vd_ref: vf.add_const(0.0), vq_ref: v_mag,
            id_g: vf.add_const(0.0), iq_g: vf.add_const(0.0),
            vd_g: vd_bus, vq_g: vq_bus,
            vd_f: vd_g, vq_f: vq_g,
            id_c: id_g, iq_c: iq_g,
            id_ref: id_c, iq_ref: iq_c,
            id_ref_sat: id_c, iq_ref_sat: iq_c,
            vd_c_ref: vd_f, vq_c_ref: vq_f,
            vd_c: vd_c_ref, vq_c: vq_c_ref,
            pf: -p_conv + p_loss, qf: vf.add_const(0.0),
            d_v_a: vf.add_const(0.0), d_v_b: vf.add_const(0.0), d_v_c: vf.add_const(0.0),
        },
        in_vars=[v_a, v_b, v_c],
        out_vars=[i_a, i_b, i_c],
        external_mapping={
            VarPowerFlowReferenceType.v_A: v_a,
            VarPowerFlowReferenceType.v_B: v_b,
            VarPowerFlowReferenceType.v_C: v_c,
            VarPowerFlowReferenceType.i_A: i_a,
            VarPowerFlowReferenceType.i_B: i_b,
            VarPowerFlowReferenceType.i_C: i_c,
            VarPowerFlowReferenceType.Pt: pt,
            VarPowerFlowReferenceType.Qt: qt,
            VarPowerFlowReferenceType.Pf: pf,
            VarPowerFlowReferenceType.Qf: qf,
            VarPowerFlowReferenceType.P_A: p_a,
            VarPowerFlowReferenceType.Q_A: q_a,
            VarPowerFlowReferenceType.P_B: p_b,
            VarPowerFlowReferenceType.Q_B: q_b,
            VarPowerFlowReferenceType.P_C: p_c,
            VarPowerFlowReferenceType.Q_C: q_c,
            VarPowerFlowReferenceType.d_v_A: d_v_a,
            VarPowerFlowReferenceType.d_v_B: d_v_b,
            VarPowerFlowReferenceType.d_v_C: d_v_c,
        },
        api_obj_mapping={
            ParamPowerFlowReferenceType.omega_base: omega_base,
            ParamPowerFlowReferenceType.alpha1: a0,
            ParamPowerFlowReferenceType.alpha2: a1,
            ParamPowerFlowReferenceType.alpha3: a2,
        },
    )

    model.add(park_v_block)
    model.add(inv_i_block)
    model.add(block_p)
    model.add(block_q)
    model.add(block_vd)
    model.add(block_vq)
    model.add(block_id)
    model.add(block_iq)
    model.unify_blocks()
    return model
