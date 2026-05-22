# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List
import math

from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType
from VeraGridEngine.enumerations import ParamPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import (Block, Var)
from VeraGridEngine.Utils.Symbolic.block_helpers import tf_to_block
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_gfm_converter_model(vfactory: VarFactory, inputs: List[Var],
                              multilinear: bool = False):
    """
    Build Grid Forming Converter model (Droop + voltage + current control)
    based on the provided conceptual equations.
    """
    Vm = inputs[0]
    Va = inputs[1]
    Pt_vsc = inputs[2]
    Qt_vsc = inputs[3]

    algebraic_eqs = []
    algebraic_vars = []
    res_block = Block()

    # Filter elements (per-unitized on converter base)
    Rf = vfactory.add_var('Rf')  # Resistance filter
    Lf = vfactory.add_var('Lf')  # Inductance filter
    Cf = vfactory.add_var('Cf')  # Capacitance filter
    
    Rc = vfactory.add_var('Rc')  # Grid Filter
    Lc = vfactory.add_var('Lc')  # Grid Filter
    Rcap = vfactory.add_var('Rcap')  # Grid Filter
    
    # Droop gains and references
    Kdp = vfactory.add_var('Kdp')
    Kdq = vfactory.add_var('Kdq')
    omega_nom = vfactory.add_var('omega_nom')  # rad/s
    omega_ref = vfactory.add_var('omega_ref')  # p.u.
    V_ref = vfactory.add_var('V_ref')
    P_ref = vfactory.add_var('P_ref')
    Q_ref = vfactory.add_var('Q_ref')
    fn = vfactory.add_var('fn')

    # Inner loop PI gains
    Kp_icl = vfactory.add_var('Kp_icl')
    Ki_icl = vfactory.add_var('Ki_icl')

    # Filter time constants for power measurements
    tau_P = vfactory.add_var('tau_P')
    tau_Q = vfactory.add_var('tau_Q')

    # Limits
    V_max = vfactory.add_var('V_max')
    I_max = vfactory.add_var('I_max')

    #V ref variables
    vd_ref = vfactory.add_var('vd_ref')
    vq_ref = vfactory.add_var('vq_ref')
    event_dict = {
        Rf: vfactory.add_const(0.02),
        Lf: vfactory.add_const(0.15),
        Cf: vfactory.add_const(0.05),
        Rc: vfactory.add_const(0.01),
        Lc: vfactory.add_const(0.1),
        Rcap: vfactory.add_const(1e6),  # Large value to effectively disable damping
        Kdp: vfactory.add_const(0.05),
        Kdq: vfactory.add_const(0.05),
        omega_nom: vfactory.add_const(2 * math.pi * 50),
        omega_ref: vfactory.add_const(1.0),
        V_ref: vfactory.add_const(1.0),
        P_ref: vfactory.add_const(None),  # Initialized from power flow
        Q_ref: vfactory.add_const(None),
        vd_ref: vfactory.add_const(None),
        vq_ref: vfactory.add_const(None),
        fn: vfactory.add_const(50.0),
        Kp_icl: vfactory.add_const(0.05),
        Ki_icl: vfactory.add_const(50.0),
        tau_P: vfactory.add_const(0.01),
        tau_Q: vfactory.add_const(0.01),
        V_max: vfactory.add_const(1.1),
        I_max: vfactory.add_const(1.2),
    }

    # Variables - P and Q represent terminal power (flowing into the grid)
    # They are linked to Pt_vsc and Qt_vsc via algebraic equations
    P = vfactory.add_var('P')
    Q = vfactory.add_var('Q')
    omega = vfactory.add_var('omega')
    theta = vfactory.add_var('theta')
    V = vfactory.add_var('V')

    vd_g = vfactory.add_var('vd_g')
    vq_g = vfactory.add_var('vq_g')
    vd_c = vfactory.add_var('vd_c')
    vq_c = vfactory.add_var('vq_c')

    id_c = vfactory.add_var('id_c')
    iq_c = vfactory.add_var('iq_c')
    vd_f = vfactory.add_var('vd_f')
    vq_f = vfactory.add_var('vq_f')
    id_g = vfactory.add_var('id_g')
    iq_g = vfactory.add_var('iq_g')

    vd_c_ref = vfactory.add_var('vd_c_ref')
    vq_c_ref = vfactory.add_var('vq_c_ref')

    id_c_ref = vfactory.add_var('id_c_ref')
    iq_c_ref = vfactory.add_var('iq_c_ref')

    # Mapping terminal voltages to dq relative to internal angle theta
    algebraic_eqs.append(vd_g - Vm * sym.sin(Va - theta))
    algebraic_eqs.append(vq_g - Vm * sym.cos(Va - theta))

    # Filter nodes (simplified algebraic representation for RMS for EMT add di/dt terms)
    algebraic_eqs.append(vd_f - vd_g - (Rc*id_g - omega*Lc*iq_g))
    algebraic_eqs.append(vq_f - vq_g - (Rc*iq_g + omega*Lc*id_g))

    algebraic_eqs.append(vd_c - vd_f - (Rf*id_c - omega*Lf*iq_c))
    algebraic_eqs.append(vq_c - vq_f - (Rf*iq_c + omega*Lf*id_c))

    # Grid currents (mapped from converter side)
    algebraic_eqs.append(iq_c - iq_g - (-Cf*omega*vq_f + vd_f/Rcap))
    algebraic_eqs.append(id_c - id_g - ( Cf*omega*vd_f + vq_f/Rcap))

    # Power measurement
    k = vfactory.add_const(1.0)  # Power calculation constant for dq frame
    algebraic_eqs.append(P - k * (vq_g * iq_g + vd_g * id_g))
    algebraic_eqs.append(Q - k * (vq_g * id_g - vd_g * iq_g))

    # Droop control with Low-pass filters
    # Transfer function: 1/(tau*s + 1)
    # At steady state: output = input, derivative = 0
    block_P, P_lowpass = tf_to_block(vfactory, num=[vfactory.add_const(1)], den=[vfactory.add_const(1), tau_P], x=P,
                                     name='P_loop')
    block_Q, Q_lowpass = tf_to_block(vfactory, num=[vfactory.add_const(1)], den=[vfactory.add_const(1), tau_Q], x=Q,
                                     name='Q_loop')
    block_P.init_eqs = {P_lowpass: P}
    block_Q.init_eqs = {Q_lowpass: Q}
    res_block.add(block_P)
    res_block.add(block_Q)

    # omega = omega_ref - Kdp * (P_filt - P_ref)
    algebraic_eqs.append(omega - (omega_ref - Kdp * (P_lowpass - P_ref)))
    # V = V_ref - Kdq * (Q_filt - Q_ref)
    algebraic_eqs.append(V - (V_ref - Kdq * (Q_lowpass - Q_ref)))

    # Internal angle integration
    # d(theta)/dt = 2*pi*fn * (omega - 1)
    dt_theta = vfactory.add_diff_var('dt_theta', base_var=theta)
    algebraic_eqs.append(dt_theta - 2 * math.pi * fn * (omega - 1))

    # Voltage control loop


    # PI controllers for voltage
    block_vd, id_hat = tf_to_block(vfactory, num=[Ki_icl, Kp_icl], den=[0, 1], x=vd_ref - vd_f, name='vd_ctrl')
    block_vq, iq_hat = tf_to_block(vfactory, num=[Ki_icl, Kp_icl], den=[0, 1], x=vq_ref - vq_f, name='vq_ctrl')
    res_block.add(block_vd)
    res_block.add(block_vq)

    # Current reference calculation (with feedforward and decoupling)
    i_d_ref_raw = iq_hat + iq_g - Cf * omega * vq_f
    i_q_ref_raw = id_hat + id_g + Cf * omega * vd_f

    # Current limitation with anti-windup (UPC-style back-calculation path):
    # positive feedback through LPF 1/(1+s*tau_aw), tau_aw = Kp_icl/Ki_icl.
    eps_aw = vfactory.add_const(1e-9)
    tau_aw = Kp_icl / (Ki_icl + eps_aw)
    aw_d_in = vfactory.add_var('aw_d_in')
    aw_q_in = vfactory.add_var('aw_q_in')
    block_aw_d, aw_d = tf_to_block(vfactory, num=[vfactory.add_const(1.0)], den=[vfactory.add_const(1.0), tau_aw],
                                   x=aw_d_in, name='aw_d')
    block_aw_q, aw_q = tf_to_block(vfactory, num=[vfactory.add_const(1.0)], den=[vfactory.add_const(1.0), tau_aw],
                                   x=aw_q_in, name='aw_q')
    res_block.add(block_aw_d)
    res_block.add(block_aw_q)

    i_d_ref_aw = vfactory.add_var('i_d_ref_aw')
    i_q_ref_aw = vfactory.add_var('i_q_ref_aw')
    algebraic_eqs.append(i_d_ref_aw - (i_d_ref_raw + aw_d))
    algebraic_eqs.append(i_q_ref_aw - (i_q_ref_raw + aw_q))

    # Saturation plant: q-axis first, then d-axis headroom.
    iq_for_id_lim = sym.max(iq_c, i_q_ref_aw)
    id_max = sym.sqrt(sym.max(I_max**2 - iq_for_id_lim**2, vfactory.add_const(1e-5)))
    i_d_ref_sat = sym.hard_sat(i_d_ref_aw, -id_max, id_max)
    i_q_ref_sat = sym.hard_sat(i_q_ref_aw, -I_max, I_max)

    i_d_ref_sat_var = vfactory.add_var('i_d_ref_sat')
    i_q_ref_sat_var = vfactory.add_var('i_q_ref_sat')
    algebraic_eqs.append(i_d_ref_sat_var - i_d_ref_sat)
    algebraic_eqs.append(i_q_ref_sat_var - i_q_ref_sat)
    algebraic_eqs.append(aw_d_in - (i_d_ref_sat_var - i_d_ref_aw))
    algebraic_eqs.append(aw_q_in - (i_q_ref_sat_var - i_q_ref_aw))

    algebraic_eqs.append(id_c_ref - i_d_ref_sat_var)
    algebraic_eqs.append(iq_c_ref - i_q_ref_sat_var)

    # Current loop PI controllers
    block_id, vd_hat = tf_to_block(vfactory, num=[Ki_icl, Kp_icl], den=[0, 1], x=id_c_ref - id_c, name='id_ctrl')
    block_iq, vq_hat = tf_to_block(vfactory, num=[Ki_icl, Kp_icl], den=[0, 1], x=iq_c_ref - iq_c, name='iq_ctrl')
    res_block.add(block_id)
    res_block.add(block_iq)

    # Converter voltage reference calculation
    algebraic_eqs.append(vd_c_ref - (vd_hat + vd_f - Lf * omega * iq_c))
    algebraic_eqs.append(vq_c_ref - (vq_hat + vq_f + Lf * omega * id_c))

    #Now we control the converter's voltage with an ideal voltage source.
    algebraic_eqs.append(vd_c - vd_c_ref)
    algebraic_eqs.append(vq_c - vq_c_ref)

    # Collect all variables
    algebraic_vars.extend(
         [P, Q, omega, theta, V, vd_g, vq_g, id_g, iq_g, id_c, iq_c, vd_f, vq_f, vd_c, vq_c, vd_c_ref, vq_c_ref, id_c_ref, iq_c_ref,
          i_d_ref_aw, i_q_ref_aw, i_d_ref_sat_var, i_q_ref_sat_var, aw_d_in, aw_q_in])

    core_block = Block(
        algebraic_eqs=algebraic_eqs,
        algebraic_vars=algebraic_vars,
        diff_vars=[dt_theta],
        event_dict=event_dict,
        init_eqs={
            P: -Pt_vsc,
            Q: -Qt_vsc,
            P_ref: P,
            Q_ref: Q,
            theta: Va,
            omega: vfactory.add_const(1.0),
            V: Vm,
            V_ref: Vm,
            vd_g: vfactory.add_const(0.0),
            vq_g: Vm,
            id_g: (1 / k) * Q / vq_g,
            iq_g: (1 / k) * P / vq_g,
            vd_f: vd_g + (Rc*id_g - omega*Lc*iq_g),
            vq_f: vq_g + (Rc*iq_g + omega*Lc*id_g),
            vd_ref: vd_f,
            vq_ref: vq_f,

            # Capacitor currents (Rcap is large, so damping terms are negligible)
            id_c: id_g + Cf * omega * vd_f + vq_f / Rcap,
            iq_c: iq_g - Cf * omega * vq_f - vd_f / Rcap,
            
            # Current references match currents (PI input = 0)
            id_c_ref: id_c,
            iq_c_ref: iq_c,
            i_d_ref_aw: id_c,
            i_q_ref_aw: iq_c,
            i_d_ref_sat_var: id_c,
            i_q_ref_sat_var: iq_c,
            aw_d_in: vfactory.add_const(0.0),
            aw_q_in: vfactory.add_const(0.0),
            aw_d: vfactory.add_const(0.0),
            aw_q: vfactory.add_const(0.0),
            vd_c_ref: Rf * id_c - Lf * omega * iq_c + vd_f,
            vq_c_ref: Rf * iq_c + Lf * omega * id_c + vq_f,
            vq_c: vq_c_ref,
            vd_c: vd_c_ref,

            #control loop init
            vd_hat: (vd_c_ref) - (vd_f) + (Lf * omega * iq_c),
            vq_hat: (vq_c_ref) - (vq_f) - (Lf * omega * id_c),
            # Voltage PI controller outputs (feedforward currents)
            # From id_c_ref = y_vq_ctrl + iq_g - Cf*vq_f with id_c_ref = id_c:
            iq_hat: id_c - iq_g + Cf * omega * vq_f,
            # From iq_c_ref = y_vd_ctrl + id_g + Cf*vd_f with iq_c_ref = iq_c:
            id_hat: iq_c - id_g - Cf * omega * vd_f,
        },
        external_mapping={
            VarPowerFlowRefferenceType.P: P,
            VarPowerFlowRefferenceType.Q: Q,
        }
    )
    res_block.add(core_block)
    res_block.unify_blocks()

    return res_block, id_c, iq_c, P, Q, {
        "Rf": Rf,
        "Rc": Rc,
        "Rcap": Rcap,
        "id_g": id_g,
        "iq_g": iq_g,
        "vd_c": vd_c,
        "vq_c": vq_c,
        "vd_f": vd_f,
        "vq_f": vq_f,
        "L": Lf,
    }


def VscGfmBuild(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    """
    VSC GFM (Grid Forming) model template builder.
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.VscDevice

    inputs = [vfactory.add_var("Vm_"), vfactory.add_var("Va_"), vfactory.add_var("Vdc_")]
    Vm = inputs[0]
    Va = inputs[1]
    v_dc = inputs[2]

    # Power Flow related variables
    Pt_vsc = vfactory.add_var('Pt_vsc')
    Qt_vsc = vfactory.add_var('Qt_vsc')
    Pf_vsc = vfactory.add_var('Pf_vsc')

    # Optional loss parameters (following GFL pattern)
    a0 = vfactory.add_var('a0')
    a1 = vfactory.add_var('a1')
    a2 = vfactory.add_var('a2')
    Qf = vfactory.add_var('Qf')

    event_dict = {
        a0: vfactory.add_const(0.0),
        a1: vfactory.add_const(0.0),
        a2: vfactory.add_const(0.1),
        Qf: vfactory.add_const(0.0),
    }

    gfm_block, i_d, i_q, P, Q, internals = build_gfm_converter_model(vfactory=vfactory, inputs=[Vm, Va, Pt_vsc, Qt_vsc])

    Im = sym.sqrt(i_d ** 2 + i_q ** 2 + vfactory.add_const(1e-5))
    P_conv = vfactory.add_const(1.5) * (internals["vq_c"] * i_q + internals["vd_c"] * i_d)
    P_poly_loss = a0 + a1 * Im + a2 * Im ** 2

    vsc_wrapper = Block(
        algebraic_eqs=[
            Pf_vsc + P_conv,
            Pt_vsc + P,
            Qt_vsc + Q,
        ],
        algebraic_vars=[Pt_vsc, Qt_vsc, Pf_vsc],
        event_dict=event_dict,
        external_mapping={
            VarPowerFlowRefferenceType.Vmt: inputs[0],
            VarPowerFlowRefferenceType.Vat: inputs[1],
            VarPowerFlowRefferenceType.Pt: Pt_vsc,
            VarPowerFlowRefferenceType.Qt: Qt_vsc,
            VarPowerFlowRefferenceType.Pf: Pf_vsc,
            VarPowerFlowRefferenceType.Qf: Qf,
            VarPowerFlowRefferenceType.Vdc: v_dc,
        },
        in_vars=inputs,
        init_eqs={
            Pt_vsc: -P,
            Qt_vsc: -Q,
            Pf_vsc: -P_conv,
        },
        out_vars=[Pt_vsc, Qt_vsc, Pf_vsc]
    )

    vsc_wrapper.add(gfm_block)
    vsc_wrapper.name = 'gfm_block'
    vsc_wrapper.unify_blocks()  # Merge init_eqs from child blocks
    vsc_wrapper.init_eqs[Pf_vsc] = -P_conv

    vsc_wrapper.api_obj_mapping = {
        ParamPowerFlowRefferenceType.R1: internals["Rf"],
        ParamPowerFlowRefferenceType.X1: internals["L"],
        ParamPowerFlowRefferenceType.alpha1: a0,
        ParamPowerFlowRefferenceType.alpha2: a1,
        ParamPowerFlowRefferenceType.alpha3: a2,
    }

    templ.block = vsc_wrapper
    return templ
