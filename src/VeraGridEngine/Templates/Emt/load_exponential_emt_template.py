# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np

from VeraGridEngine.enumerations import ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate

def ExponentialLoad3phEmtBuild(vf: VarFactory, name: str = "EXP_Load_EMT_3ph") -> EmtModelTemplate:
    """
    EMT 3-phase abc exponential load as CURRENT INJECTION.

      P = P0 * (Vm/V0)^a
      Q = Q0 * (Vm/V0)^b

    Same explicit structure as ZIP: all intermediates are algebraic vars with algebraic eqs.
    """

    templ = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    v_A = vf.add_var("v_A_" + name)
    v_B = vf.add_var("v_B_" + name)
    v_C = vf.add_var("v_C_" + name)
    templ.block.in_vars = [v_A, v_B, v_C]

    P0_A = vf.add_var("P0_A_" + name)
    Q0_A = vf.add_var("Q0_A_" + name)
    P0_B = vf.add_var("P0_B_" + name)
    Q0_B = vf.add_var("Q0_B_" + name)
    P0_C = vf.add_var("P0_C_" + name)
    Q0_C = vf.add_var("Q0_C_" + name)

    V0 = vf.add_var("V0_" + name)
    a  = vf.add_var("a_"  + name)
    b  = vf.add_var("b_"  + name)

    f_nom  = vf.add_var("f_nom_" + name)
    k_sogi = vf.add_var("k_sogi_" + name)
    eps    = vf.add_var("eps_" + name)

    templ.block.event_dict[P0_A] = vf.add_const(-0.0999999/3.0)
    templ.block.event_dict[Q0_A] = vf.add_const(-0.009999999862208533/3.0)
    templ.block.event_dict[P0_B] = vf.add_const(-0.0999999/3.0)
    templ.block.event_dict[Q0_B] = vf.add_const(-0.009999999862208533/3.0)
    templ.block.event_dict[P0_C] = vf.add_const(-0.0999999/3.0)
    templ.block.event_dict[Q0_C] = vf.add_const(-0.009999999862208533/3.0)

    templ.block.event_dict[V0] = vf.add_const(1.0)
    templ.block.event_dict[a]  = vf.add_const(5.0)
    templ.block.event_dict[b]  = vf.add_const(5.0)

    templ.block.event_dict[f_nom]  = vf.add_const(50.0)
    templ.block.event_dict[k_sogi] = vf.add_const(1.41421356237)
    templ.block.event_dict[eps]    = vf.add_const(1e-6)

    u_A = vf.add_var("u_A_" + name)
    q_A = vf.add_var("q_A_" + name)
    u_B = vf.add_var("u_B_" + name)
    q_B = vf.add_var("q_B_" + name)
    u_C = vf.add_var("u_C_" + name)
    q_C = vf.add_var("q_C_" + name)

    d_u_A = vf.add_diff_var("d_u_A_" + name, base_var=u_A)
    d_q_A = vf.add_diff_var("d_q_A_" + name, base_var=q_A)
    d_u_B = vf.add_diff_var("d_u_B_" + name, base_var=u_B)
    d_q_B = vf.add_diff_var("d_q_B_" + name, base_var=q_B)
    d_u_C = vf.add_diff_var("d_u_C_" + name, base_var=u_C)
    d_q_C = vf.add_diff_var("d_q_C_" + name, base_var=q_C)

    templ.block.state_vars = [u_A, q_A, u_B, q_B, u_C, q_C]
    templ.block.diff_vars  = [d_u_A, d_q_A, d_u_B, d_q_B, d_u_C, d_q_C]

    templ.block.state_eqs = [
        d_u_A - (k_sogi * (2 * np.pi * f_nom) * (v_A - u_A) - (2 * np.pi * f_nom) * q_A),
        d_q_A - ((2 * np.pi * f_nom) * u_A),

        d_u_B - (k_sogi * (2 * np.pi * f_nom) * (v_B - u_B) - (2 * np.pi * f_nom) * q_B),
        d_q_B - ((2 * np.pi * f_nom) * u_B),

        d_u_C - (k_sogi * (2 * np.pi * f_nom) * (v_C - u_C) - (2 * np.pi * f_nom) * q_C),
        d_q_C - ((2 * np.pi * f_nom) * u_C),
    ]

    VA2 = vf.add_var("VA2_" + name)
    VB2 = vf.add_var("VB2_" + name)
    VC2 = vf.add_var("VC2_" + name)
    VmA = vf.add_var("VmA_" + name)
    VmB = vf.add_var("VmB_" + name)
    VmC = vf.add_var("VmC_" + name)
    rA  = vf.add_var("rA_"  + name)
    rB  = vf.add_var("rB_"  + name)
    rC  = vf.add_var("rC_"  + name)

    P_A = vf.add_var("P_A_" + name)
    Q_A = vf.add_var("Q_A_" + name)
    P_B = vf.add_var("P_B_" + name)
    Q_B = vf.add_var("Q_B_" + name)
    P_C = vf.add_var("P_C_" + name)
    Q_C = vf.add_var("Q_C_" + name)

    i_A = vf.add_var("i_A_" + name)
    i_B = vf.add_var("i_B_" + name)
    i_C = vf.add_var("i_C_" + name)

    templ.block.algebraic_vars = [
        VA2, VB2, VC2, VmA, VmB, VmC, rA, rB, rC,
        P_A, Q_A, P_B, Q_B, P_C, Q_C,
        i_A, i_B, i_C
    ]

    templ.block.algebraic_eqs = [
        VA2 - (u_A*u_A + q_A*q_A),
        VB2 - (u_B*u_B + q_B*q_B),
        VC2 - (u_C*u_C + q_C*q_C),

        VmA - ((VA2 + eps) ** vf.add_const(0.5)),
        VmB - ((VB2 + eps) ** vf.add_const(0.5)),
        VmC - ((VC2 + eps) ** vf.add_const(0.5)),

        rA - (VmA / V0),
        rB - (VmB / V0),
        rC - (VmC / V0),

        P_A - (P0_A * (rA ** a)),
        Q_A - (Q0_A * (rA ** b)),

        P_B - (P0_B * (rB ** a)),
        Q_B - (Q0_B * (rB ** b)),

        P_C - (P0_C * (rC ** a)),
        Q_C - (Q0_C * (rC ** b)),

        i_A - ((u_A*P_A + q_A*Q_A) / (VA2 + eps)),
        i_B - ((u_B*P_B + q_B*Q_B) / (VB2 + eps)),
        i_C - ((u_C*P_C + q_C*Q_C) / (VC2 + eps)),
    ]

    templ.block.init_eqs = {
        u_A: v_A,
        q_A: vf.add_const(0.0),
        u_B: v_B,
        q_B: vf.add_const(0.0),
        u_C: v_C,
        q_C: vf.add_const(0.0),
    }

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.P: None,
        VarPowerFlowRefferenceType.Q: None,
        VarPowerFlowRefferenceType.P_N: None,
        VarPowerFlowRefferenceType.Q_N: None,
        VarPowerFlowRefferenceType.P_A: P_A,
        VarPowerFlowRefferenceType.Q_A: Q_A,
        VarPowerFlowRefferenceType.P_B: P_B,
        VarPowerFlowRefferenceType.Q_B: Q_B,
        VarPowerFlowRefferenceType.P_C: P_C,
        VarPowerFlowRefferenceType.Q_C: Q_C,
        VarPowerFlowRefferenceType.i_N: None,
        VarPowerFlowRefferenceType.i_A: i_A,
        VarPowerFlowRefferenceType.i_B: i_B,
        VarPowerFlowRefferenceType.i_C: i_C,
        VarPowerFlowRefferenceType.theta: None
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.Pl0_A: P0_A,
        ParamPowerFlowRefferenceType.Ql0_A: Q0_A,
        ParamPowerFlowRefferenceType.Pl0_B: P0_B,
        ParamPowerFlowRefferenceType.Ql0_B: Q0_B,
        ParamPowerFlowRefferenceType.Pl0_C: P0_C,
        ParamPowerFlowRefferenceType.Ql0_C: Q0_C,
    }

    return templ