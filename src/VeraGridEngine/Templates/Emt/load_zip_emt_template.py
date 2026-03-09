# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np

from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate

def get_load_ZIP_3ph_emt_template(vf: VarFactory, sbase: float, fbase: float, name: str = "ZIP_Load_EMT_3ph") -> EmtModelTemplate:

    # In the load model S and currents are defined as positive, from powerflow they are negative (sign convention).
    # That's why the  VarPowerFlowReferenceType has the sign changed.
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    # Symbolic constants for math operations
    c0 = vf.add_const(0.0)
    c2 = vf.add_const(2.0)
    c05 = vf.add_const(0.5)

    # Inputs: Instantaneous phase voltages from the grid
    v_A = vf.add_var("v_A_" + name)
    v_B = vf.add_var("v_B_" + name)
    v_C = vf.add_var("v_C_" + name)
    templ.block.in_vars = [v_A, v_B, v_C]

    # Parameters: Nominal power (P0, Q0) and Voltage (V0)
    P0_A = vf.add_var("P0_A_" + name)
    Q0_A = vf.add_var("Q0_A_" + name)
    P0_B = vf.add_var("P0_B_" + name)
    Q0_B = vf.add_var("Q0_B_" + name)
    P0_C = vf.add_var("P0_C_" + name)
    Q0_C = vf.add_var("Q0_C_" + name)
    V0 = vf.add_var("V0_" + name)

    # ZIP coefficients and SOGI filter parameters
    a1 = vf.add_var("a1_" + name)
    a2 = vf.add_var("a2_" + name)
    a3 = vf.add_var("a3_" + name)
    a4 = vf.add_var("a4_" + name)
    a5 = vf.add_var("a5_" + name)
    a6 = vf.add_var("a6_" + name)
    f_nom = vf.add_var("f_nom_" + name)
    k_sogi = vf.add_var("k_sogi_" + name)
    eps = vf.add_var("eps_" + name)

    # Parameter Registration (event_dict) for the case P= 9.999999, Q= 0.999999
    P0 = 1 / sbase
    Q0 = 0.999999 / sbase
    # P0 = -0.0 / sbase
    # Q0 = -0.0 / sbase
    templ.block.event_dict[P0_A] = vf.add_const(P0 / 3.0)
    templ.block.event_dict[Q0_A] = vf.add_const(Q0 / 3.0)
    templ.block.event_dict[P0_B] = vf.add_const(P0/ 3.0)
    templ.block.event_dict[Q0_B] = vf.add_const(Q0 / 3.0)
    templ.block.event_dict[P0_C] = vf.add_const(P0 / 3.0)
    templ.block.event_dict[Q0_C] = vf.add_const(Q0 / 3.0)
    # templ.block.event_dict[V0] = vf.add_const(1.0)
    templ.block.event_dict[V0] = vf.add_const(np.sqrt(2))
    templ.block.event_dict[f_nom] = vf.add_const(fbase)
    templ.block.event_dict[k_sogi] = vf.add_const(1.41421356)
    templ.block.event_dict[eps] = vf.add_const(1e-12)

    # Default ZIP coefficients: Constant Power behavior (a3=1, a6=1)
    for p in [a1, a2, a4, a5]: templ.block.event_dict[p] = c0
    for p in [a3, a6]: templ.block.event_dict[p] = vf.add_const(1.0)

    # State Variables (SOGI output and its quadrature signal)
    u_A = vf.add_var("u_A_" + name)
    q_A = vf.add_var("q_A_" + name)
    u_B = vf.add_var("u_B_" + name)
    q_B = vf.add_var("q_B_" + name)
    u_C = vf.add_var("u_C_" + name)
    q_C = vf.add_var("q_C_" + name)
    templ.block.state_vars = [u_A, q_A, u_B, q_B, u_C, q_C]

    # Differential Variables (Derivatives)
    d_u_A = vf.add_diff_var("d_u_A_" + name, base_var=u_A)
    d_q_A = vf.add_diff_var("d_q_A_" + name, base_var=q_A)
    d_u_B = vf.add_diff_var("d_u_B_" + name, base_var=u_B)
    d_q_B = vf.add_diff_var("d_q_B_" + name, base_var=q_B)
    d_u_C = vf.add_diff_var("d_u_C_" + name, base_var=u_C)
    d_q_C = vf.add_diff_var("d_q_C_" + name, base_var=q_C)
    templ.block.diff_vars = [d_u_A, d_q_A, d_u_B, d_q_B, d_u_C, d_q_C]

    # Fundamental angular frequency
    w = (2.0 * np.pi) * f_nom

    # State Equations: SOGI Dynamics (Standard Orthogonal Filter)
    # templ.block.state_eqs = [
    #     (k_sogi * w * (v_A - u_A) - w * q_A),
    #     (w * u_A),
    #     (k_sogi * w * (v_B - u_B) - w * q_B),
    #     (w * u_B),
    #     (k_sogi * w * (v_C - u_C) - w * q_C),
    #     (w * u_C),
    # ]
    templ.block.state_eqs = [
        (w * q_A),  # This is d_u_A
        (k_sogi * w * (v_A - u_A) - w * q_A),  # This is d_q_A
        (w * q_B),  # This is d_u_B
        (k_sogi * w * (v_B - u_B) - w * q_B),  # This is d_q_B
        (w * q_C),  # This is d_u_C
        (k_sogi * w * (v_C - u_C) - w * q_C),  # This is d_q_C
    ]

    # Algebraic Variables for ZIP model
    VA2 = vf.add_var("VA2_" + name)
    VB2 = vf.add_var("VB2_" + name)
    VC2 = vf.add_var("VC2_" + name)
    VmA = vf.add_var("VmA_" + name)
    VmB = vf.add_var("VmB_" + name)
    VmC = vf.add_var("VmC_" + name)
    rA = vf.add_var("rA_" + name)
    rB = vf.add_var("rB_" + name)
    rC = vf.add_var("rC_" + name)
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
        P_A, Q_A, P_B, Q_B, P_C, Q_C, i_A, i_B, i_C
    ]

    # Algebraic Equations: Definitions for magnitudes and the ZIP polynomial
    templ.block.algebraic_eqs = [
        # Magnitudes squared (u^2 + q^2)
        VA2 - (u_A ** 2 + q_A ** 2),
        VB2 - (u_B ** 2 + q_B ** 2),
        VC2 - (u_C ** 2 + q_C ** 2),
        # Peak amplitudes
        VmA - ((VA2 + eps) ** c05),
        VmB - ((VB2 + eps) ** c05),
        VmC - ((VC2 + eps) ** c05),
        # Voltage ratios (V/V_nominal)
        rA - (VmA / V0),
        rB - (VmB / V0),
        rC - (VmC / V0),
        # # ZIP Polynomials for P and Q
        # P_A - (P0_A * (a1 * rA ** 2 + a2 * rA + a3)),
        # Q_A - (Q0_A * (a4 * rA ** 2 + a5 * rA + a6)),
        # P_B - (P0_B * (a1 * rB ** 2 + a2 * rB + a3)),
        # Q_B - (Q0_B * (a4 * rB ** 2 + a5 * rB + a6)),
        # P_C - (P0_C * (a1 * rC ** 2 + a2 * rC + a3)),
        # Q_C - (Q0_C * (a4 * rC ** 2 + a5 * rC + a6)),
        # # Current injection: i = 2 * (u*P + q*Q) / V_peak^2
        # i_A - (c2 * (u_A * P_A + q_A * Q_A) / (VA2 + eps)),
        # i_B - (c2 * (u_B * P_B + q_B * Q_B) / (VB2 + eps)),
        # i_C - (c2 * (u_C * P_C + q_C * Q_C) / (VC2 + eps)),

        # CHANGE SIGN CONVENTION ! POWERS AND CURRENTS FROM POWERFLOW ARE NEGATIVE (sign convention injection leaving the bus is negative)
        # ZIP Polynomials for P and Q
        P_A + (P0_A * (a1 * rA ** 2 + a2 * rA + a3)),
        Q_A + (Q0_A * (a4 * rA ** 2 + a5 * rA + a6)),
        P_B + (P0_B * (a1 * rB ** 2 + a2 * rB + a3)),
        Q_B + (Q0_B * (a4 * rB ** 2 + a5 * rB + a6)),
        P_C + (P0_C * (a1 * rC ** 2 + a2 * rC + a3)),
        Q_C + (Q0_C * (a4 * rC ** 2 + a5 * rC + a6)),
        # Current injection: i = 2 * (u*P + q*Q) / V_peak^2
        i_A + (c2 * (u_A * (-P_A) + q_A * (-Q_A)) / (VA2 + eps)),
        i_B + (c2 * (u_B * (-P_B) + q_B * (-Q_B)) / (VB2 + eps)),
        i_C + (c2 * (u_C * (-P_C) + q_C * (-Q_C)) / (VC2 + eps)),
    ]

    # FULL INITIALIZATION (30 Variables)
    # This section ensures zero residuals at t=0 by accounting for AC steady state.
    templ.block.init_eqs = {
        # 6 States: u follows grid voltage, q is the orthogonal component
        # u_A: v_A,
        # q_A: ((V0 ** 2 - v_A ** 2 + eps) ** c05),
        # u_B: v_B,
        # q_B: ((V0 ** 2 - v_B ** 2 + eps) ** c05),
        # u_C: v_C,
        # q_C: ((V0 ** 2 - v_C ** 2 + eps) ** c05),
        u_A: v_A,
        q_A: c0,
        u_B: v_B,
        q_B: c0,
        u_C: v_C,
        q_C: c0,

        # 18 Algebraics: Complete chain for current injection
        VA2: (u_A ** 2 + q_A ** 2), VmA: ((VA2 + eps) ** c05), rA: (VmA / V0),
        VB2: (u_B ** 2 + q_B ** 2), VmB: ((VB2 + eps) ** c05), rB: (VmB / V0),
        VC2: (u_C ** 2 + q_C ** 2), VmC: ((VC2 + eps) ** c05), rC: (VmC / V0),
    }

    templ.block.diff_init_eqs = {
        # 6 Derivatives: MUST be non-zero in EMT to match harmonic motion
        # d_u_A: -w * q_A,
        # d_q_A: w * u_A,
        # d_u_B: -w * q_B,
        # d_q_B: w * u_B,
        # d_u_C: -w * q_C,
        # d_q_C: w * u_C,
        d_u_A: c0,
        d_q_A: c0,
        d_u_B: c0,
        d_q_B: c0,
        d_u_C: c0,
        d_q_C: c0,
    }

    # Complete External Mapping (Interface with the simulation engine)
    # templ.block.external_mapping = {
    #     VarPowerFlowRefferenceType.P: None,
    #     VarPowerFlowRefferenceType.Q: None,
    #     VarPowerFlowRefferenceType.P_N: None,
    #     VarPowerFlowRefferenceType.Q_N: None,
    #     VarPowerFlowRefferenceType.P_A: -P_A,
    #     VarPowerFlowRefferenceType.Q_A: -Q_A,
    #     VarPowerFlowRefferenceType.P_B: -P_B,
    #     VarPowerFlowRefferenceType.Q_B: -Q_B,
    #     VarPowerFlowRefferenceType.P_C: -P_C,
    #     VarPowerFlowRefferenceType.Q_C: -Q_C,
    #     VarPowerFlowRefferenceType.i_N: None,
    #     VarPowerFlowRefferenceType.i_A: -i_A,
    #     VarPowerFlowRefferenceType.i_B: -i_B,
    #     VarPowerFlowRefferenceType.i_C: -i_C,
    #     VarPowerFlowRefferenceType.theta: None
    # }
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

    return templ
