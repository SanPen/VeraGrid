# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


import numpy as np
from VeraGridEngine import MultiCircuit
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, DeviceType, ParamPowerFlowRefferenceType

# def get_simple_generator_emt_template(vf: VarFactory, name: str = "simple_emt_type_generator_template") -> EmtModelTemplate:
#     """
#     EMT type machine model without damping effects.
#     :param grid: MultiCircuit
#     :param gen: Generator object to apply the template
#     :param name: string to identify the generator and model
#     :return: EmtModelTemplate
#     """
#
#     templ = EmtModelTemplate()
#     templ.tpe = DeviceType.GeneratorDevice
#     templ.name = name
#
#     # --------------------------------------------------------------------------------------
#     # Inputs: instantaneous abc terminal voltages in pu (at bus)
#     # --------------------------------------------------------------------------------------
#     inputs = [
#         vf.add_var(name=f"v_A_{name}", ref=VarPowerFlowRefferenceType.v_A),
#         vf.add_var(name=f"v_B_{name}", ref=VarPowerFlowRefferenceType.v_B),
#         vf.add_var(name=f"v_C_{name}", ref=VarPowerFlowRefferenceType.v_C)
#     ]# --------------------------------------------------------------------------------------
#     # States (pu, except theta [rad])
#     # --------------------------------------------------------------------------------------
#
#     theta = vf.add_var("theta_" + name)  # electrical angle [rad]
#     omega = vf.add_var("omega_" + name)  # speed [pu]
#     psi_d = vf.add_var("psi_d_" + name)  # flux linkages [pu] on psi_base = Vbase/omega_base
#     psi_q = vf.add_var("psi_q_" + name)
#     psi_f = vf.add_var("psi_f_" + name)
#     psi_0 = vf.add_var("psi_0_" + name)
#     et    = vf.add_var("et_" + name)     # PI integrator state (units: pu*s or equivalent)
#
#
#     # Diff vars (derivatives)
#     d_omega = vf.add_diff_var(name = f"d_omega_{name}", base_var=omega)
#     d_theta = vf.add_diff_var(name = f"d_theta_{name}", base_var=theta)
#     d_psi_d = vf.add_diff_var(name = f"d_psi_d_{name}", base_var=psi_d)
#     d_psi_q = vf.add_diff_var(name = f"d_psi_q_{name}", base_var=psi_q)
#     d_psi_0 = vf.add_diff_var(name = f"d_psi_0_{name}", base_var=psi_0)
#     d_psi_f = vf.add_diff_var(name = f"d_psi_f_{name}", base_var=psi_f)
#     d_et    = vf.add_diff_var(name = f"d_et_{name}", base_var=et)
#
#     # --------------------------------------------------------------------------------------
#     # Algebraic eqs
#     # --------------------------------------------------------------------------------------
#     i_A = vf.add_var(name=f"i_A_{name}", ref=VarPowerFlowRefferenceType.i_A)
#     i_B = vf.add_var(name=f"i_B_{name}", ref=VarPowerFlowRefferenceType.i_B)
#     i_C = vf.add_var(name=f"i_C_{name}", ref=VarPowerFlowRefferenceType.i_C)
#
#     # dq0 voltages
#     v_d = vf.add_var("v_d_" + name)
#     v_q = vf.add_var("v_q_" + name)
#     v_0 = vf.add_var("v_0_" + name)
#
#     # dq0 currents
#     i_d = vf.add_var("i_d_" + name)
#     i_q = vf.add_var("i_q_" + name)
#     i_0 = vf.add_var("i_0_" + name)
#
#     # field
#     v_f = vf.add_var("v_f_" + name)
#     i_f = vf.add_var("i_f_" + name)
#
#     # powers/torques
#     Te = vf.add_var("Te_" + name)
#     Tm = vf.add_var("Tm_" + name)
#     Pe = vf.add_var("Pe_" + name)
#     Qe = vf.add_var("Qe_" + name)
#     Pm = vf.add_var("Pm_" + name)
#
#     # --------------------------------------------------------------------------------------
#     # Parameters
#     # --------------------------------------------------------------------------------------
#     omega_base = vf.add_var("omega_base")
#     H = vf.add_var("H")
#     D = vf.add_var("D")
#
#     Ra  = vf.add_var("Ra")
#     La  = vf.add_var("La")
#     Lmd = vf.add_var("Lmd")
#     Lmq = vf.add_var("Lmq")
#     Lf  = vf.add_var("Lf")
#     Rf  = vf.add_var("Rf")
#     R0  = vf.add_var("R0")
#     L0  = vf.add_var("L0")
#
#     omega_ref = vf.add_var("omega_ref")  # pu
#     Kp = vf.add_var("Kp")
#     Ki = vf.add_var("Ki")
#
#     v_f0 = vf.add_var("v_f0")  # temporary fixed exciter output
#     Tm0 = vf.add_var("Tm0")  # temporary fixed exciter output
#
#     delta = vf.add_var("delta_" + name)  # difference between rotor angle and grid angle
#     Ipk = vf.add_var("Ipk")
#     Vpk = vf.add_var("Vpk")
#     phi = vf.add_var("phi")
#     phi_v = vf.add_var("phi_v")
#
#     templ.block = Block(
#         # --------------------------------------------------------------------------------------
#         # STATE EQUATIONS (seconds + pu)
#         # --------------------------------------------------------------------------------------
#         state_eqs=[
#             -v_d - Ra * i_d + omega * psi_q,
#             -v_q - Ra * i_q - omega * psi_d,
#             -v_0 - R0 * i_0,
#             v_f - Rf * i_f,
#             omega_base * omega,
#             (Tm - Te - D * (omega - omega_ref)) / (2 * H),
#             omega_base * (omega_ref - omega),
#         ],
#         state_vars=[psi_d, psi_q, psi_0, psi_f, theta, omega, et],
#
#         # --------------------------------------------------------------------------------------
#         # ALGEBRAIC EQUATIONS
#         # --------------------------------------------------------------------------------------
#         algebraic_eqs=[
#             psi_d - (Lmd * i_f - (Lmd + La) * i_d),
#             psi_q - (-(Lmq + La) * i_q),
#             psi_0 - (-L0 * i_0),
#             psi_f - ((Lmd + Lf) * i_f - Lmd * i_d),
#
#             v_d - (2 / 3) * (
#                     inputs[0] * sym.sin(theta) +
#                     inputs[1] * sym.sin(theta - 2 * np.pi / 3) +
#                     inputs[2] * sym.sin(theta + 2 * np.pi / 3)),
#             v_q - (2 / 3) * (
#                     inputs[0] * sym.cos(theta) +
#                     inputs[1] * sym.cos(theta - 2 * np.pi / 3) +
#                     inputs[2] * sym.cos(theta + 2 * np.pi / 3)),
#             v_0 - (1 / 3) * (inputs[0] + inputs[1] + inputs[2]),
#
#             i_A - (i_d * sym.sin(theta) + i_q * sym.cos(theta) + i_0),
#             i_B - (i_d * sym.sin(theta - 2 * np.pi / 3) + i_q * sym.cos(theta - 2 * np.pi / 3) + i_0),
#             i_C - (i_d * sym.sin(theta + 2 * np.pi / 3) + i_q * sym.cos(theta + 2 * np.pi / 3) + i_0),
#
#             Te - (3 / 2) * (psi_q * i_d - psi_d * i_q),
#             Pe - (i_A * inputs[0] + i_B * inputs[1] + i_C * inputs[2]),
#             Qe - (1 / np.sqrt(3)) * ((inputs[0] - inputs[1]) * i_C +
#                                      (inputs[1] - inputs[2]) * i_A +
#                                      (inputs[2] - inputs[0]) * i_B),
#             Tm - (Te + Kp * (omega_ref - omega) + Ki * et),
#             # Tm - Tm0,
#             v_f - v_f0,
#             # Pm - Tm * omega,
#             Pe - Pm,
#         ],
#         algebraic_vars=[
#             i_d, i_q, i_0, i_f,
#             v_d, v_q, v_0,
#             i_A, i_B, i_C,
#             Te, Pe, Qe,
#             Tm, v_f, Pm
#         ],
#         in_vars=inputs,
#         out_vars=[i_A, i_B, i_C],
#     )
#
#     templ.block.diff_vars = [d_psi_d, d_psi_q, d_psi_0, d_psi_f, d_theta, d_omega, d_et]
#
#     # --------------------------------------------------------------------------------------
#     # external mapping
#     # --------------------------------------------------------------------------------------
#
#     templ.block.external_mapping = {
#         VarPowerFlowRefferenceType.P_N: None,
#         VarPowerFlowRefferenceType.Q_N: None,
#         VarPowerFlowRefferenceType.P_A: None,
#         VarPowerFlowRefferenceType.Q_A: None,
#         VarPowerFlowRefferenceType.P_B: None,
#         VarPowerFlowRefferenceType.Q_B: None,
#         VarPowerFlowRefferenceType.P_C: None,
#         VarPowerFlowRefferenceType.Q_C: None,
#         VarPowerFlowRefferenceType.i_N: None,
#         VarPowerFlowRefferenceType.i_A: i_A,
#         VarPowerFlowRefferenceType.i_B: i_B,
#         VarPowerFlowRefferenceType.i_C: i_C,
#         VarPowerFlowRefferenceType.phi_v: phi_v,
#         VarPowerFlowRefferenceType.phi: phi,
#         VarPowerFlowRefferenceType.Vpk: Vpk,
#         VarPowerFlowRefferenceType.Ipk: Ipk,
#         VarPowerFlowRefferenceType.d_v_N: None,
#         VarPowerFlowRefferenceType.d_v_A: None,
#         VarPowerFlowRefferenceType.d_v_B: None,
#         VarPowerFlowRefferenceType.d_v_C: None,
#     }
#
#
#     # --------------------------------------------------------------------------------------
#     # Event dict (constants)
#     # --------------------------------------------------------------------------------------
#     w = 2 * np.pi * grid.fBase
#     # Ra = 0.001
#     Ld = gen.X1
#     La_num = 0.15
#     Lmd_num = Ld - La_num
#
#     templ.block.event_dict = {
#         omega_base: vf.add_const(w),
#         H:          vf.add_const(5.0),
#         D:          vf.add_const(2.0),
#         Ra:         vf.add_const(gen.R1),
#         La:         vf.add_const(La_num),
#         Lmd:        vf.add_const(Lmd_num),
#         Lmq:        vf.add_const(1.55),
#         Lf:         vf.add_const(0.10),
#         Rf:         vf.add_const(0.017),
#         R0:         vf.add_const(0.001),
#         L0:         vf.add_const(0.14),
#         omega_ref:  vf.add_const(1.0),
#         Kp:         vf.add_const(2.0),
#         Ki:         vf.add_const(2.0),
#         v_f0:       vf.add_const(-0.000006702), #-0.015522
#         Tm0:        vf.add_const(0.5063602154594633),
#
#         # init-only external values
#         phi_v: vf.add_const(None),
#         phi: vf.add_const(None),
#         Vpk: vf.add_const(None),
#         Ipk: vf.add_const(None),
#
#         # init-only auxiliary variable
#         delta: vf.add_const(None),
#     }
#
#     # --------------------------------------------------------------------------------------
#     # INIT EQUATIONS
#     # --------------------------------------------------------------------------------------
#
#     templ.block.init_eqs = {
#         omega: vf.add_const(1.0),
#         et: vf.add_const(0.0),
#         delta: sym.atan(
#             ( Ra * Ipk * sym.sin(phi) - omega * (Lmq + La) * Ipk * sym.cos(phi)) /
#             (Vpk + Ra * Ipk * sym.cos(phi) + omega * (Lmq + La) * Ipk * sym.sin(phi))
#         ),
#         theta: phi_v + delta,
#
#         v_d: 2 / 3 * (sym.sin(theta) * inputs[0] +
#                       sym.sin(theta - 2 * np.pi / 3) * inputs[1] +
#                       sym.sin(theta + 2 * np.pi / 3) * inputs[2]),
#         v_q: 2 / 3 * (sym.cos(theta) * inputs[0] +
#                       sym.cos(theta - 2 * np.pi / 3) * inputs[1] +
#                       sym.cos(theta + 2 * np.pi / 3) * inputs[2]),
#         v_0: (1 / 3) * (inputs[0] + inputs[1] + inputs[2]),
#
#         i_d: 2 / 3 * (sym.sin(theta) * i_A +
#                       sym.sin(theta - 2 * np.pi / 3) * i_B +
#                       sym.sin(theta + 2 * np.pi / 3) * i_C),
#         i_q: 2 / 3 * (sym.cos(theta) * i_A +
#                       sym.cos(theta - 2 * np.pi / 3) * i_B +
#                       sym.cos(theta + 2 * np.pi / 3) * i_C),
#         i_0: (1 / 3) * (i_A + i_B + i_C),
#
#         psi_q: (v_d + Ra * i_d),
#         psi_d: -(v_q + Ra * i_q),
#         psi_0: -L0 * i_0,
#
#         i_f: (psi_d + (Lmd + La) * i_d) / Lmd,
#         v_f: i_f * Rf,
#         psi_f: (Lmd + Lf) * i_f - Lmd * i_d,
#
#         Pe: (i_A * inputs[0] + i_B * inputs[1] + i_C * inputs[2]),
#         Qe: (1 / np.sqrt(3)) * ((inputs[0] - inputs[1]) * i_C +
#                                      (inputs[1] - inputs[2]) * i_A +
#                                      (inputs[2] - inputs[0]) * i_B),
#
#         Te: (3 / 2) * (psi_q * i_d - psi_d * i_q),
#         Tm: Te,
#         Pm: Tm * omega,
#     }
#
#     # --------------------------------------------------------------------------------------
#     # DIFF INIT EQS
#     # --------------------------------------------------------------------------------------
#     c0 = vf.add_const(0.0)
#     templ.block.diff_init_eqs = {
#         d_theta: omega_base*omega,
#         d_et: (omega_ref - omega),
#         d_omega: c0,
#         d_psi_d: c0,
#         d_psi_q: c0,
#         d_psi_0: c0,
#         d_psi_f: c0,
#     }
#
#     return templ

def get_simple_generator_emt_template(vf: VarFactory, name: str = "simple_emt_type_generator_template") -> EmtModelTemplate:
    """
    EMT type machine model without damping effects.
    :param vf: grid.var_factory
    :param name: string to identify the generator and model
    :return: EmtModelTemplate
    """

    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    # --------------------------------------------------------------------------------------
    # Inputs: instantaneous abc terminal voltages in pu (at bus)
    # --------------------------------------------------------------------------------------
    v_A = vf.add_var(name=f"v_A_{name}", reference= VarPowerFlowRefferenceType.v_A)
    v_B = vf.add_var(name=f"v_B_{name}", reference= VarPowerFlowRefferenceType.v_B)
    v_C = vf.add_var(name=f"v_C_{name}", reference= VarPowerFlowRefferenceType.v_C)
    Tm = vf.add_var(name=f"Tm_{name}")
    v_f = vf.add_var(name=f"v_f_{name}")

    # to connect complete block with gen block
    Ipk = vf.add_var(name="Ipk", reference= VarPowerFlowRefferenceType.Ipk)
    Vpk = vf.add_var(name="Vpk", reference= VarPowerFlowRefferenceType.Vpk)
    phi = vf.add_var(name="phi", reference= VarPowerFlowRefferenceType.phi)
    phi_v = vf.add_var(name="phi_v", reference= VarPowerFlowRefferenceType.phi_v)
    inputs = [v_A, v_B, v_C]
    # --------------------------------------------------------------------------------------
    # States (pu, except theta [rad])
    # --------------------------------------------------------------------------------------

    theta = vf.add_var("theta_" + name)  # electrical angle [rad]
    omega = vf.add_var(name=f"omega_{name}")  # speed [pu]
    psi_d = vf.add_var("psi_d_" + name)  # flux linkages [pu] on psi_base = Vbase/omega_base
    psi_q = vf.add_var("psi_q_" + name)
    psi_f = vf.add_var("psi_f_" + name)
    psi_0 = vf.add_var("psi_0_" + name)
    et    = vf.add_var("et_" + name)     # PI integrator state (units: pu*s or equivalent)


    # Diff vars (derivatives)
    d_omega = vf.add_diff_var(name = f"d_omega_{name}", base_var=omega)
    d_theta = vf.add_diff_var(name = f"d_theta_{name}", base_var=theta)
    d_psi_d = vf.add_diff_var(name = f"d_psi_d_{name}", base_var=psi_d)
    d_psi_q = vf.add_diff_var(name = f"d_psi_q_{name}", base_var=psi_q)
    d_psi_0 = vf.add_diff_var(name = f"d_psi_0_{name}", base_var=psi_0)
    d_psi_f = vf.add_diff_var(name = f"d_psi_f_{name}", base_var=psi_f)
    d_et    = vf.add_diff_var(name = f"d_et_{name}", base_var=et)

    # --------------------------------------------------------------------------------------
    # Algebraic eqs
    # --------------------------------------------------------------------------------------
    i_A = vf.add_var(name=f"i_A_{name}", reference= VarPowerFlowRefferenceType.i_A)
    i_B = vf.add_var(name=f"i_B_{name}", reference= VarPowerFlowRefferenceType.i_B)
    i_C = vf.add_var(name=f"i_C_{name}", reference= VarPowerFlowRefferenceType.i_C)

    # dq0 voltages
    v_d = vf.add_var("v_d_" + name)
    v_q = vf.add_var("v_q_" + name)
    v_0 = vf.add_var("v_0_" + name)

    # dq0 currents
    i_d = vf.add_var("i_d_" + name)
    i_q = vf.add_var("i_q_" + name)
    i_0 = vf.add_var("i_0_" + name)

    # field
    i_f = vf.add_var(name=f"i_f_{name}")

    # powers/torques
    Te = vf.add_var("Te_" + name)
    Pe = vf.add_var("Pe_" + name)
    Qe = vf.add_var("Qe_" + name)
    Pm = vf.add_var("Pm_" + name)

    # --------------------------------------------------------------------------------------
    # Parameters
    # --------------------------------------------------------------------------------------
    omega_base = vf.add_var("omega_base")
    H = vf.add_var("H")
    D = vf.add_var("D")

    Ra  = vf.add_var("Ra")
    La  = vf.add_var("La")
    Ld  = vf.add_var("Ld")
    Lmd = vf.add_var("Lmd")
    Lmq = vf.add_var("Lmq")
    Lf  = vf.add_var("Lf")
    Rf  = vf.add_var("Rf")
    R0  = vf.add_var("R0")
    L0  = vf.add_var("L0")

    omega_ref = vf.add_var("omega_ref")  # pu
    delta = vf.add_var("delta_" + name)  # difference between rotor angle and grid angle

    Kp = vf.add_var("Kp")
    Ki = vf.add_var("Ki")

    v_f0 = vf.add_var("v_f0")  # temporary fixed exciter output

    templ.block = Block(
        # --------------------------------------------------------------------------------------
        # STATE EQUATIONS (seconds + pu)
        # --------------------------------------------------------------------------------------
        state_eqs=[
            -v_d - Ra * i_d + omega * psi_q,
            -v_q - Ra * i_q - omega * psi_d,
            -v_0 - R0 * i_0,
            v_f - Rf * i_f,
            omega_base * omega,
            (Tm - Te - D * (omega - omega_ref)) / (2 * H),
            omega_base * (omega_ref - omega),
        ],
        state_vars=[psi_d, psi_q, psi_0, psi_f, theta, omega, et],

        # --------------------------------------------------------------------------------------
        # ALGEBRAIC EQUATIONS
        # --------------------------------------------------------------------------------------
        algebraic_eqs=[
            psi_d - (Lmd * i_f - (Lmd + La) * i_d),
            psi_q - (-(Lmq + La) * i_q),
            psi_0 - (-L0 * i_0),
            psi_f - ((Lmd + Lf) * i_f - Lmd * i_d),

            v_d - (2 / 3) * (
                    inputs[0] * sym.sin(theta) +
                    inputs[1] * sym.sin(theta - 2 * np.pi / 3) +
                    inputs[2] * sym.sin(theta + 2 * np.pi / 3)),
            v_q - (2 / 3) * (
                    inputs[0] * sym.cos(theta) +
                    inputs[1] * sym.cos(theta - 2 * np.pi / 3) +
                    inputs[2] * sym.cos(theta + 2 * np.pi / 3)),
            v_0 - (1 / 3) * (inputs[0] + inputs[1] + inputs[2]),

            i_A - (i_d * sym.sin(theta) + i_q * sym.cos(theta) + i_0),
            i_B - (i_d * sym.sin(theta - 2 * np.pi / 3) + i_q * sym.cos(theta - 2 * np.pi / 3) + i_0),
            i_C - (i_d * sym.sin(theta + 2 * np.pi / 3) + i_q * sym.cos(theta + 2 * np.pi / 3) + i_0),

            Te - (3 / 2) * (psi_q * i_d - psi_d * i_q),
            Pe - (i_A * inputs[0] + i_B * inputs[1] + i_C * inputs[2]),
            Qe - (1 / np.sqrt(3)) * ((inputs[0] - inputs[1]) * i_C +
                                     (inputs[1] - inputs[2]) * i_A +
                                     (inputs[2] - inputs[0]) * i_B),
            Pe - Pm,
            Tm - (Te + Kp * (omega_ref - omega) + Ki * et),
            v_f - v_f0,
        ],
        algebraic_vars=[
            i_d, i_q, i_0, i_f,
            v_d, v_q, v_0,
            i_A, i_B, i_C,
            Te, Pe, Qe, Pm,Tm, v_f,
        ],
        in_vars=inputs,
        out_vars=[i_A, i_B, i_C, omega],
        # out_vars=[i_A, i_B, i_C],
    )

    templ.block.diff_vars = [d_psi_d, d_psi_q, d_psi_0, d_psi_f, d_theta, d_omega, d_et]

    # --------------------------------------------------------------------------------------
    # external mapping
    # --------------------------------------------------------------------------------------

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.v_N: None,
        VarPowerFlowRefferenceType.v_A: v_A,
        VarPowerFlowRefferenceType.v_B: v_B,
        VarPowerFlowRefferenceType.v_C: v_C,
        VarPowerFlowRefferenceType.P_N: None,
        VarPowerFlowRefferenceType.Q_N: None,
        VarPowerFlowRefferenceType.P_A: None,
        VarPowerFlowRefferenceType.Q_A: None,
        VarPowerFlowRefferenceType.P_B: None,
        VarPowerFlowRefferenceType.Q_B: None,
        VarPowerFlowRefferenceType.P_C: None,
        VarPowerFlowRefferenceType.Q_C: None,
        VarPowerFlowRefferenceType.i_N: None,
        VarPowerFlowRefferenceType.i_A: i_A,
        VarPowerFlowRefferenceType.i_B: i_B,
        VarPowerFlowRefferenceType.i_C: i_C,
        VarPowerFlowRefferenceType.phi_v: phi_v,
        VarPowerFlowRefferenceType.phi: phi,
        VarPowerFlowRefferenceType.Vpk: Vpk,
        VarPowerFlowRefferenceType.Ipk: Ipk,
        VarPowerFlowRefferenceType.d_v_N: None,
        VarPowerFlowRefferenceType.d_v_A: None,
        VarPowerFlowRefferenceType.d_v_B: None,
        VarPowerFlowRefferenceType.d_v_C: None,
    }


    # --------------------------------------------------------------------------------------
    # Event dict (constants)
    # --------------------------------------------------------------------------------------

    templ.block.event_dict = {
        H:          vf.add_const(5.0),
        D:          vf.add_const(2.0),
        La:         vf.add_const(0.15),
        Lmq:        vf.add_const(1.55),
        Lf:         vf.add_const(0.10),
        Rf:         vf.add_const(0.017),
        R0:         vf.add_const(0.001),
        omega_ref:  vf.add_const(1.0),
        Kp:         vf.add_const(2.0),
        Ki:         vf.add_const(2.0),
        v_f0:       vf.add_const(-0.000006702),
        Lmd: Ld - La,
        # init-only external auxiliary values
        phi_v: vf.add_const(None),
        phi: vf.add_const(None),
        Vpk: vf.add_const(None),
        Ipk: vf.add_const(None),
        # delta: vf.add_const(None),
        # delta: sym.atan(
        #     (Ra * Ipk * sym.sin(phi) - omega * (Lmq + La) * Ipk * sym.cos(phi)) /
        #     (Vpk + Ra * Ipk * sym.cos(phi) + omega * (Lmq + La) * Ipk * sym.sin(phi))
        # ),
        delta: sym.atan(
            (Ra * Ipk * sym.sin(phi) - omega_ref * (Lmq + La) * Ipk * sym.cos(phi)) /
            (Vpk + Ra * Ipk * sym.cos(phi) + omega_ref * (Lmq + La) * Ipk * sym.sin(phi))
        ),
    }
    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.omega_base : omega_base,
        ParamPowerFlowRefferenceType.R1: Ra,
        ParamPowerFlowRefferenceType.X1: Ld,
        ParamPowerFlowRefferenceType.X0: L0,
    }

    # --------------------------------------------------------------------------------------
    # INIT EQUATIONS
    # --------------------------------------------------------------------------------------

    templ.block.init_eqs = {
        et: vf.add_const(0.0),
        omega: omega_ref,

        theta: phi_v + delta,

        v_d: 2 / 3 * (sym.sin(theta) * inputs[0] +
                      sym.sin(theta - 2 * np.pi / 3) * inputs[1] +
                      sym.sin(theta + 2 * np.pi / 3) * inputs[2]),
        v_q: 2 / 3 * (sym.cos(theta) * inputs[0] +
                      sym.cos(theta - 2 * np.pi / 3) * inputs[1] +
                      sym.cos(theta + 2 * np.pi / 3) * inputs[2]),
        v_0: (1 / 3) * (inputs[0] + inputs[1] + inputs[2]),

        i_d: 2 / 3 * (sym.sin(theta) * i_A +
                      sym.sin(theta - 2 * np.pi / 3) * i_B +
                      sym.sin(theta + 2 * np.pi / 3) * i_C),
        i_q: 2 / 3 * (sym.cos(theta) * i_A +
                      sym.cos(theta - 2 * np.pi / 3) * i_B +
                      sym.cos(theta + 2 * np.pi / 3) * i_C),
        i_0: (1 / 3) * (i_A + i_B + i_C),

        psi_q: (v_d + Ra * i_d),
        psi_d: -(v_q + Ra * i_q),
        psi_0: -L0 * i_0,

        i_f: (psi_d + (Lmd + La) * i_d) / Lmd,
        v_f: i_f * Rf,
        psi_f: (Lmd + Lf) * i_f - Lmd * i_d,

        Pe: (i_A * inputs[0] + i_B * inputs[1] + i_C * inputs[2]),
        Qe: (1 / np.sqrt(3)) * ((inputs[0] - inputs[1]) * i_C +
                                     (inputs[1] - inputs[2]) * i_A +
                                     (inputs[2] - inputs[0]) * i_B),

        Te: (3 / 2) * (psi_q * i_d - psi_d * i_q),
        Pm: Pe,


    }

    # --------------------------------------------------------------------------------------
    # DIFF INIT EQS
    # --------------------------------------------------------------------------------------
    c0 = vf.add_const(0.0)
    templ.block.diff_init_eqs = {
        d_theta: omega_base*omega,
        d_et: (omega_ref - omega),
        d_omega: c0,
        d_psi_d: c0,
        d_psi_q: c0,
        d_psi_0: c0,
        d_psi_f: c0,
    }

    return templ