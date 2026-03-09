# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


import numpy as np
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, DeviceType

def get_generator_emt_template(vf: VarFactory, name: str = "emt_type_generator_template") -> EmtModelTemplate:
    """
    EMT generator template (seconds + per-unit electrical variables).

    Time base: seconds
    Electrical variables: pu
    Speed omega: pu (1.0 = synchronous)
    omega_base: rad/s = 2*pi*f_base

    Consistent pu-second model key scalings:
      - d(psi)/dt includes omega_base factor because psi_base = V_base/omega_base
      - swing equation includes omega_base/(2H)
      - d(theta)/dt = omega_base*omega  (theta in rad)
      - integrator state et uses d(et)/dt = (omega_ref - omega)  (NO omega_base)
    """

    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name

    # --------------------------------------------------------------------------------------
    # Inputs: instantaneous abc terminal voltages in pu (at bus)
    # --------------------------------------------------------------------------------------
    inputs = [
        vf.add_var("v_A_" + name),
        vf.add_var("v_B_" + name),
        vf.add_var("v_C_" + name),
    ]

    # --------------------------------------------------------------------------------------
    # States (pu, except theta [rad])
    # --------------------------------------------------------------------------------------
    theta = vf.add_var("theta_" + name)  # electrical angle [rad]
    omega = vf.add_var("omega_" + name)  # speed [pu]
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
    # Terminal currents (abc) leaving the bus (your branch convention for generator should be set in stamping)
    # --------------------------------------------------------------------------------------
    i_A = vf.add_var("i_A_" + name)
    i_B = vf.add_var("i_B_" + name)
    i_C = vf.add_var("i_C_" + name)

    # dq0 voltages
    v_d = vf.add_var("v_d_" + name)
    v_q = vf.add_var("v_q_" + name)
    v_0 = vf.add_var("v_0_" + name)

    # dq0 currents
    i_d = vf.add_var("i_d_" + name)
    i_q = vf.add_var("i_q_" + name)
    i_0 = vf.add_var("i_0_" + name)

    # field
    v_f = vf.add_var("v_f_" + name)
    i_f = vf.add_var("i_f_" + name)

    # powers/torques
    Te = vf.add_var("Te_" + name)
    Tm = vf.add_var("Tm_" + name)
    Pe = vf.add_var("Pe_" + name)
    Qe = vf.add_var("Qe_" + name)
    Pm = vf.add_var("Pm_" + name)

    # --------------------------------------------------------------------------------------
    # Parameters (use const via event_dict)
    # --------------------------------------------------------------------------------------
    freq       = vf.add_var("Freq")
    omega_base = vf.add_var("omega_base")  # rad/s
    H          = vf.add_var("H")
    D          = vf.add_var("D")

    Ra  = vf.add_var("Ra")
    La  = vf.add_var("La")
    Lmd = vf.add_var("Lmd")
    Lmq = vf.add_var("Lmq")
    Lf  = vf.add_var("Lf")
    Rf  = vf.add_var("Rf")
    R0  = vf.add_var("R0")
    L0  = vf.add_var("L0")

    omega_ref = vf.add_var("omega_ref")  # pu
    Kp        = vf.add_var("Kp")
    Ki        = vf.add_var("Ki")

    v_f0 = vf.add_var("v_f0")  # temporary fixed exciter output

    # --------------------------------------------------------------------------------------
    # STATE EQUATIONS (seconds + pu)
    # --------------------------------------------------------------------------------------
    # Define omega_e = omega_base * omega (rad/s). In the pu-flux model we use omega (pu) inside the bracket
    # and omega_base multiplies the whole bracket, which results in omega_base*omega*psi coupling (correct).
    templ.block = Block(
        state_eqs=[
            # # d_psi_d = omega_base * (v_d - Ra*i_d + omega*psi_q)
            # omega_base * (v_d - Ra * i_d + omega * psi_q),
            # # d_psi_q = omega_base * (v_q - Ra*i_q - omega*psi_d)
            # omega_base * (v_q - Ra * i_q - omega * psi_d),
            # # d_psi_0 = omega_base * (v_0 - R0*i_0)
            # omega_base * (v_0 - R0 * i_0),
            # # d_psi_f = omega_base * (v_f - Rf*i_f)
            # omega_base * (v_f - Rf * i_f),
            # # d_theta = omega_base * omega
            # omega_base * omega,
            # # d_omega = omega_base/(2H) * (Tm - Te - D*(omega-omega_ref))
            # (omega_base * (Tm - Te - D * (omega - omega_ref))) / (2 * H),
            # # d_et = (omega_ref - omega)   (NO omega_base)
            # (omega_ref - omega),


            v_d - Ra * i_d + omega * psi_q,
            v_q - Ra * i_q - omega * psi_d,
            v_0 - R0 * i_0,
            v_f - Rf * i_f,
            omega,
            (Tm - Te - D * (omega - omega_ref)) / (2 * H),
            (omega_ref - omega),
        ],
        state_vars=[psi_d, psi_q, psi_0, psi_f, theta, omega, et],

        # --------------------------------------------------------------------------------------
        # ALGEBRAIC EQUATIONS
        # --------------------------------------------------------------------------------------
        algebraic_eqs=[
            # Flux-current relations (pu inductances)
            psi_d - ((Lmd + La) * i_d + Lmd * i_f),
            psi_q - ((Lmq + La) * i_q),
            psi_0 - (L0 * i_0),
            psi_f - (Lmd * i_d + (Lmd + Lf) * i_f),

            # dq0 voltage from abc voltages using theta
            v_d - (2 / 3) * (inputs[0] * sym.cos(theta) +
                             inputs[1] * sym.cos(theta - 2 * np.pi / 3) +
                             inputs[2] * sym.cos(theta + 2 * np.pi / 3)),
            v_q - (2 / 3) * (inputs[0] * sym.sin(theta) +
                             inputs[1] * sym.sin(theta - 2 * np.pi / 3) +
                             inputs[2] * sym.sin(theta + 2 * np.pi / 3)),
            v_0 - (2 / 3) * (0.5 * inputs[0] + 0.5 * inputs[1] + 0.5 * inputs[2]),

            # abc currents from dq0 currents
            i_A - (i_d * sym.cos(theta) + i_q * sym.sin(theta) + i_0),
            i_B - (i_d * sym.cos(theta - 2 * np.pi / 3) + i_q * sym.sin(theta - 2 * np.pi / 3) + i_0),
            i_C - (i_d * sym.cos(theta + 2 * np.pi / 3) + i_q * sym.sin(theta + 2 * np.pi / 3) + i_0),

            # Electrical torque (sign consistent with your dq convention)
            Te - (3 / 2) * (psi_d * i_q - psi_q * i_d),

            # Instantaneous three-phase power (EMT instantaneous p, q proxy)
            Pe - (i_A * inputs[0] + i_B * inputs[1] + i_C * inputs[2]),
            Qe - (1 / np.sqrt(3)) * ((inputs[0] - inputs[1]) * i_C +
                                     (inputs[1] - inputs[2]) * i_A +
                                     (inputs[2] - inputs[0]) * i_B),

            # Governor/torque control algebraic closure
            Tm - (Te + Kp * (omega_ref - omega) + Ki * et),

            # Fixed exciter (temporary)
            v_f - v_f0,

            # Mechanical power proxy
            Pm - Pe,
        ],
        algebraic_vars=[
            i_d, i_q, i_0, i_f,
            v_d, v_q, v_0,
            i_A, i_B, i_C,
            Te, Pe, Qe,
            Tm, v_f, Pm
        ],
        in_vars=inputs,
        out_vars=[i_A, i_B, i_C],
    )

    templ.block.diff_vars = [d_psi_d, d_psi_q, d_psi_0, d_psi_f, d_theta, d_omega, d_et]

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.P: Pe,
        VarPowerFlowRefferenceType.Q: Qe,
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
        VarPowerFlowRefferenceType.theta: theta,
    }

    # --------------------------------------------------------------------------------------
    # Event dict (constants)
    # --------------------------------------------------------------------------------------
    w = 2 * np.pi * 50.0
    templ.block.event_dict = {
        freq:       vf.add_const(50.0),
        omega_base: vf.add_const(w),
        H:          vf.add_const(5.0),
        D:          vf.add_const(2.0),
        Ra:         vf.add_const(0.001),
        La:         vf.add_const(0.15),
        Lmd:        vf.add_const(1.55),
        Lmq:        vf.add_const(1.55),
        Lf:         vf.add_const(0.10),
        Rf:         vf.add_const(0.017),
        R0:         vf.add_const(0.001),
        L0:         vf.add_const(0.14),
        omega_ref:  vf.add_const(1.0),
        Kp:         vf.add_const(2.0),
        Ki:         vf.add_const(2.0),
        v_f0:       vf.add_const(-0.000091),
    }

    # --------------------------------------------------------------------------------------
    # INIT EQS (consistent steady state in seconds+pu)
    # We assume synchronous steady state: d(psi)/dt = 0, d(omega)/dt = 0, omega = omega_ref = 1.
    # From electrical equations (setting bracket = 0):
    #   0 = v_d - Ra*i_d + omega*psi_q   -> psi_q = (Ra*i_d - v_d)/omega
    #   0 = v_q - Ra*i_q - omega*psi_d   -> psi_d = (v_q - Ra*i_q)/omega
    #   0 = v_0 - R0*i_0                 -> (already handled by psi_0 = L0*i_0)
    #   0 = v_f - Rf*i_f                 -> v_f = Rf*i_f
    #
    # Note: these are "electrical steady-state" assumptions, not a full machine equilibrium.
    # --------------------------------------------------------------------------------------
    templ.block.init_eqs = {
        # omega: omega_ref,
        omega: vf.add_const(1.0),
        et:    vf.add_const(0.0),

        # dq0 from abc voltages
        v_d: 2 / 3 * (sym.cos(theta) * inputs[0] +
                      sym.cos(theta - 2 * np.pi / 3) * inputs[1] +
                      sym.cos(theta + 2 * np.pi / 3) * inputs[2]),
        v_q: 2 / 3 * (sym.sin(theta) * inputs[0] +
                      sym.sin(theta - 2 * np.pi / 3) * inputs[1] +
                      sym.sin(theta + 2 * np.pi / 3) * inputs[2]),
        v_0: 2 / 3 * (0.5 * inputs[0] + 0.5 * inputs[1] + 0.5 * inputs[2]),

        # dq0 from abc currents (inverse-consistent with your algebraic abc reconstruction)
        i_d: 2 / 3 * (sym.cos(theta) * i_A +
                      sym.cos(theta - 2 * np.pi / 3) * i_B +
                      sym.cos(theta + 2 * np.pi / 3) * i_C),
        i_q: 2 / 3 * (sym.sin(theta) * i_A +
                      sym.sin(theta - 2 * np.pi / 3) * i_B +
                      sym.sin(theta + 2 * np.pi / 3) * i_C),
        i_0: 2 / 3 * (0.5 * i_A + 0.5 * i_B + 0.5 * i_C),

        # electrical steady-state fluxes (corrected signs!)
        psi_d: (v_q - Ra * i_q) / omega,
        psi_q: (Ra * i_d - v_d) / omega,

        # choose i_f from psi_d relation (kept from your original approach)
        i_f: -((La + Lmd) * i_d - psi_d) / Lmd,

        # field voltage steady-state
        v_f: i_f * Rf,

        # remaining flux algebraic closures
        psi_f: Lmd * i_d + (Lmd + Lf) * i_f,
        psi_0: L0 * i_0,

        Te: (3 / 2) * (psi_d * i_q - psi_q * i_d),

        # close mechanical with Te at init
        Tm: Te,
        Pm: Pe,
    }

    # --------------------------------------------------------------------------------------
    # DIFF INIT EQS
    # Must be consistent with the chosen model:
    #   d_theta = omega_base*omega
    #   d_et    = omega_ref - omega
    # and at equilibrium: d_omega = 0, d_psi_* = 0, d_et = 0
    # --------------------------------------------------------------------------------------
    c0 = vf.add_const(0.0)
    templ.block.diff_init_eqs = {
        d_theta: omega,
        d_et:    (omega_ref - omega),
        d_omega: c0,
        d_psi_d: c0,
        d_psi_q: c0,
        d_psi_0: c0,
        d_psi_f: c0,
    }

    return templ

