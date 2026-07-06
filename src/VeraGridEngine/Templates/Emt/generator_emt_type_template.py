# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


import numpy as np
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block, find_name_in_block, Const
from VeraGridEngine.enumerations import VarPowerFlowReferenceType, DeviceType, ParamPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.block_helpers import tf_to_block, tf_to_diffblock_with_output, \
    tf_to_block_with_states, tf_to_diffblock_with_antiwindup


def _get_pf_phase_voltage_components(
        v_phase: sym.Expr,
        d_v_phase: sym.Expr,
        omega_base: sym.Expr) -> tuple[sym.Expr, sym.Expr]:
    """
    Reconstruct the phase-voltage phasor components from EMT initialization references.

    :param v_phase: Instantaneous phase voltage at ``t = 0``.
    :param d_v_phase: Instantaneous phase-voltage derivative at ``t = 0``.
    :param omega_base: Electrical base angular frequency.
    :return: Tuple ``(v_real, v_imag)`` with the RMS phasor components.
    """
    c_sqrt_2: sym.Expr = sym.sqrt(2.0)
    v_real: sym.Expr = d_v_phase / (omega_base * c_sqrt_2)
    v_imag: sym.Expr = v_phase / c_sqrt_2
    return v_real, v_imag


def _get_pf_phase_current_components_from_power(
        p_phase: sym.Expr,
        q_phase: sym.Expr,
        v_real: sym.Expr,
        v_imag: sym.Expr) -> tuple[sym.Expr, sym.Expr]:
    """
    Reconstruct the phase-current phasor components from PF power and voltage references.

    :param p_phase: Active power for the phase.
    :param q_phase: Reactive power for the phase.
    :param v_real: Real part of the phase-voltage phasor.
    :param v_imag: Imaginary part of the phase-voltage phasor.
    :return: Tuple ``(i_real, i_imag)`` with the RMS current phasor components.
    """
    voltage_sq: sym.Expr = v_real * v_real + v_imag * v_imag
    i_real: sym.Expr = (p_phase * v_real + q_phase * v_imag) / voltage_sq
    i_imag: sym.Expr = (p_phase * v_imag - q_phase * v_real) / voltage_sq
    return i_real, i_imag


def _get_positive_sequence_components(
        phase_a_real: sym.Expr,
        phase_a_imag: sym.Expr,
        phase_b_real: sym.Expr,
        phase_b_imag: sym.Expr,
        phase_c_real: sym.Expr,
        phase_c_imag: sym.Expr) -> tuple[sym.Expr, sym.Expr]:
    """
    Compute the positive-sequence phasor components from three phase phasors.

    :param phase_a_real: Real part of phase A.
    :param phase_a_imag: Imaginary part of phase A.
    :param phase_b_real: Real part of phase B.
    :param phase_b_imag: Imaginary part of phase B.
    :param phase_c_real: Real part of phase C.
    :param phase_c_imag: Imaginary part of phase C.
    :return: Tuple ``(positive_real, positive_imag)``.
    """
    c_half: sym.Expr = 0.5
    c_sqrt_3_over_2: sym.Expr = sym.sqrt(3.0) / 2.0
    positive_real: sym.Expr = (
        phase_a_real
        - c_half * phase_b_real
        - c_sqrt_3_over_2 * phase_b_imag
        - c_half * phase_c_real
        + c_sqrt_3_over_2 * phase_c_imag
    ) / 3.0
    positive_imag: sym.Expr = (
        phase_a_imag
        - c_half * phase_b_imag
        + c_sqrt_3_over_2 * phase_b_real
        - c_half * phase_c_imag
        - c_sqrt_3_over_2 * phase_c_real
    ) / 3.0
    return positive_real, positive_imag


def get_pf_positive_sequence_init_refs(
        v_a: sym.Expr,
        v_b: sym.Expr,
        v_c: sym.Expr,
        d_v_a: sym.Expr,
        d_v_b: sym.Expr,
        d_v_c: sym.Expr,
        p_a: sym.Expr,
        q_a: sym.Expr,
        p_b: sym.Expr,
        q_b: sym.Expr,
        p_c: sym.Expr,
        q_c: sym.Expr,
        omega_base: sym.Expr) -> tuple[sym.Expr, sym.Expr, sym.Expr, sym.Expr]:
    """
    Compute generator initialization references from PF voltage and power inputs.

    :param v_a: Instantaneous phase-A voltage at ``t = 0``.
    :param v_b: Instantaneous phase-B voltage at ``t = 0``.
    :param v_c: Instantaneous phase-C voltage at ``t = 0``.
    :param d_v_a: Instantaneous derivative of phase-A voltage at ``t = 0``.
    :param d_v_b: Instantaneous derivative of phase-B voltage at ``t = 0``.
    :param d_v_c: Instantaneous derivative of phase-C voltage at ``t = 0``.
    :param p_a: Active power in phase A.
    :param q_a: Reactive power in phase A.
    :param p_b: Active power in phase B.
    :param q_b: Reactive power in phase B.
    :param p_c: Active power in phase C.
    :param q_c: Reactive power in phase C.
    :param omega_base: Electrical base angular frequency.
    :return: Tuple ``(phi_v, phi, vpk, ipk)``.
    """
    v_a_real: sym.Expr
    v_a_imag: sym.Expr
    v_b_real: sym.Expr
    v_b_imag: sym.Expr
    v_c_real: sym.Expr
    v_c_imag: sym.Expr
    v_a_real, v_a_imag = _get_pf_phase_voltage_components(v_phase=v_a, d_v_phase=d_v_a, omega_base=omega_base)
    v_b_real, v_b_imag = _get_pf_phase_voltage_components(v_phase=v_b, d_v_phase=d_v_b, omega_base=omega_base)
    v_c_real, v_c_imag = _get_pf_phase_voltage_components(v_phase=v_c, d_v_phase=d_v_c, omega_base=omega_base)

    i_a_real: sym.Expr
    i_a_imag: sym.Expr
    i_b_real: sym.Expr
    i_b_imag: sym.Expr
    i_c_real: sym.Expr
    i_c_imag: sym.Expr
    i_a_real, i_a_imag = _get_pf_phase_current_components_from_power(
        p_phase=p_a,
        q_phase=q_a,
        v_real=v_a_real,
        v_imag=v_a_imag,
    )
    i_b_real, i_b_imag = _get_pf_phase_current_components_from_power(
        p_phase=p_b,
        q_phase=q_b,
        v_real=v_b_real,
        v_imag=v_b_imag,
    )
    i_c_real, i_c_imag = _get_pf_phase_current_components_from_power(
        p_phase=p_c,
        q_phase=q_c,
        v_real=v_c_real,
        v_imag=v_c_imag,
    )

    v1_real: sym.Expr
    v1_imag: sym.Expr
    i1_real: sym.Expr
    i1_imag: sym.Expr
    v1_real, v1_imag = _get_positive_sequence_components(
        phase_a_real=v_a_real,
        phase_a_imag=v_a_imag,
        phase_b_real=v_b_real,
        phase_b_imag=v_b_imag,
        phase_c_real=v_c_real,
        phase_c_imag=v_c_imag,
    )
    i1_real, i1_imag = _get_positive_sequence_components(
        phase_a_real=i_a_real,
        phase_a_imag=i_a_imag,
        phase_b_real=i_b_real,
        phase_b_imag=i_b_imag,
        phase_c_real=i_c_real,
        phase_c_imag=i_c_imag,
    )

    phi_v: sym.Expr = sym.atan2(v1_imag, v1_real)
    phi_i: sym.Expr = sym.atan2(i1_imag, i1_real)
    delta_phi: sym.Expr = phi_i - phi_v
    phi: sym.Expr = sym.atan2(sym.sin(delta_phi), sym.cos(delta_phi))
    vpk: sym.Expr = sym.sqrt(2.0) * sym.sqrt(v1_real * v1_real + v1_imag * v1_imag)
    ipk: sym.Expr = sym.sqrt(2.0) * sym.sqrt(i1_real * i1_real + i1_imag * i1_imag)
    return phi_v, phi, vpk, ipk


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
    v_A = vf.add_var(name=f"v_A_{name}", reference= VarPowerFlowReferenceType.v_A)
    v_B = vf.add_var(name=f"v_B_{name}", reference= VarPowerFlowReferenceType.v_B)
    v_C = vf.add_var(name=f"v_C_{name}", reference= VarPowerFlowReferenceType.v_C)
    Tm = vf.add_var(name=f"Tm_{name}")
    v_f = vf.add_var(name=f"v_f_{name}")

    d_v_A = vf.add_var(name=f"d_v_A_{name}", reference=VarPowerFlowReferenceType.d_v_A)
    d_v_B = vf.add_var(name=f"d_v_B_{name}", reference=VarPowerFlowReferenceType.d_v_B)
    d_v_C = vf.add_var(name=f"d_v_C_{name}", reference=VarPowerFlowReferenceType.d_v_C)
    p_A = vf.add_var(name=f"P_A_{name}", reference=VarPowerFlowReferenceType.P_A)
    q_A = vf.add_var(name=f"Q_A_{name}", reference=VarPowerFlowReferenceType.Q_A)
    p_B = vf.add_var(name=f"P_B_{name}", reference=VarPowerFlowReferenceType.P_B)
    q_B = vf.add_var(name=f"Q_B_{name}", reference=VarPowerFlowReferenceType.Q_B)
    p_C = vf.add_var(name=f"P_C_{name}", reference=VarPowerFlowReferenceType.P_C)
    q_C = vf.add_var(name=f"Q_C_{name}", reference=VarPowerFlowReferenceType.Q_C)
    inputs = [v_A, v_B, v_C, Tm, v_f]
    # --------------------------------------------------------------------------------------
    # States (pu, except theta [rad])
    # --------------------------------------------------------------------------------------

    theta = vf.add_var("theta_" + name)  # electrical angle [rad]
    omega = vf.add_var(name=f"omega_{name}")  # speed [pu]
    psi_d = vf.add_var("psi_d_" + name)  # flux linkages [pu] on psi_base = Vbase/omega_base
    psi_q = vf.add_var("psi_q_" + name)
    psi_f = vf.add_var("psi_f_" + name)
    psi_0 = vf.add_var("psi_0_" + name)


    # Diff vars (derivatives)
    d_omega = vf.add_diff_var(name = f"d_omega_{name}", base_var=omega)
    d_theta = vf.add_diff_var(name = f"d_theta_{name}", base_var=theta)
    d_psi_d = vf.add_diff_var(name = f"d_psi_d_{name}", base_var=psi_d)
    d_psi_q = vf.add_diff_var(name = f"d_psi_q_{name}", base_var=psi_q)
    d_psi_0 = vf.add_diff_var(name = f"d_psi_0_{name}", base_var=psi_0)
    d_psi_f = vf.add_diff_var(name = f"d_psi_f_{name}", base_var=psi_f)

    # --------------------------------------------------------------------------------------
    # Algebraic eqs
    # --------------------------------------------------------------------------------------
    i_A = vf.add_var(name=f"i_A_{name}", reference= VarPowerFlowReferenceType.i_A)
    i_B = vf.add_var(name=f"i_B_{name}", reference= VarPowerFlowReferenceType.i_B)
    i_C = vf.add_var(name=f"i_C_{name}", reference= VarPowerFlowReferenceType.i_C)

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

    phi_v_init: sym.Expr
    phi_init: sym.Expr
    vpk_init: sym.Expr
    ipk_init: sym.Expr
    phi_v_init, phi_init, vpk_init, ipk_init = get_pf_positive_sequence_init_refs(
        v_a=v_A,
        v_b=v_B,
        v_c=v_C,
        d_v_a=d_v_A,
        d_v_b=d_v_B,
        d_v_c=d_v_C,
        p_a=p_A,
        q_a=q_A,
        p_b=p_B,
        q_b=q_B,
        p_c=p_C,
        q_c=q_C,
        omega_base=omega_base,
    )

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
        ],
        state_vars=[psi_d, psi_q, psi_0, psi_f, theta, omega],

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
        ],
        algebraic_vars=[
            i_d, i_q, i_0, i_f,
            v_d, v_q, v_0,
            i_A, i_B, i_C,
            Te, Pe, Qe, Pm
        ],
        in_vars=inputs,
        out_vars=[i_A, i_B, i_C, omega, i_f, Te],
    )

    templ.block.diff_vars = [d_psi_d, d_psi_q, d_psi_0, d_psi_f, d_theta, d_omega]

    # --------------------------------------------------------------------------------------
    # external mapping
    # --------------------------------------------------------------------------------------

    templ.block.external_mapping = {
        # VarPowerFlowReferenceType.P_N: None,
        # VarPowerFlowReferenceType.Q_N: None,
        # VarPowerFlowReferenceType.P_A: None,
        # VarPowerFlowReferenceType.Q_A: None,
        # VarPowerFlowReferenceType.P_B: None,
        # VarPowerFlowReferenceType.Q_B: None,
        # VarPowerFlowReferenceType.P_C: None,
        # VarPowerFlowReferenceType.Q_C: None,
        # VarPowerFlowReferenceType.i_N: None,
        VarPowerFlowReferenceType.i_A: i_A,
        VarPowerFlowReferenceType.i_B: i_B,
        VarPowerFlowReferenceType.i_C: i_C,
        VarPowerFlowReferenceType.d_v_A: d_v_A,
        VarPowerFlowReferenceType.d_v_B: d_v_B,
        VarPowerFlowReferenceType.d_v_C: d_v_C,
        VarPowerFlowReferenceType.P_A: p_A,
        VarPowerFlowReferenceType.Q_A: q_A,
        VarPowerFlowReferenceType.P_B: p_B,
        VarPowerFlowReferenceType.Q_B: q_B,
        VarPowerFlowReferenceType.P_C: p_C,
        VarPowerFlowReferenceType.Q_C: q_C,
        # VarPowerFlowReferenceType.d_v_N: None,
        # VarPowerFlowReferenceType.d_v_A: None,
        # VarPowerFlowReferenceType.d_v_B: None,
        # VarPowerFlowReferenceType.d_v_C: None,
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
        Lmd: Ld - La,
        d_v_A: vf.add_const(None),
        d_v_B: vf.add_const(None),
        d_v_C: vf.add_const(None),
        p_A: vf.add_const(None),
        q_A: vf.add_const(None),
        p_B: vf.add_const(None),
        q_B: vf.add_const(None),
        p_C: vf.add_const(None),
        q_C: vf.add_const(None),
        delta: vf.add_const(None),
    }
    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.omega_base : omega_base,
        ParamPowerFlowReferenceType.R1: Ra,
        ParamPowerFlowReferenceType.X1: Ld,
        ParamPowerFlowReferenceType.X0: L0,
    }


    # --------------------------------------------------------------------------------------
    # INIT EQUATIONS
    # --------------------------------------------------------------------------------------

    templ.block.init_eqs = {
        omega: omega_ref,
        delta: sym.atan(
            (Ra * ipk_init * sym.sin(phi_init) - omega * (Lmq + La) * ipk_init * sym.cos(phi_init)) /
            (vpk_init + Ra * ipk_init * sym.cos(phi_init) + omega * (Lmq + La) * ipk_init * sym.sin(phi_init))
        ),
        theta: phi_v_init + delta,

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
        d_omega: c0,
        d_psi_d: c0,
        d_psi_q: c0,
        d_psi_0: c0,
        d_psi_f: c0,
    }

    return templ

def get_generator_emt_type_template(vf: VarFactory, name: str = "emt_type_generator_template"
) -> EmtModelTemplate:
    """
    9-winding Synchronous Machine EMT model. The synchronous machine used by EMTP with 1 mass.
    Sign Convention: Generator (i_A, i_B, i_C are positive when injecting power into the grid).
    Park Transform: Amplitude invariant (2/3 factor), d-axis leads q-axis (d=sin, q=cos).
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    # ----------------------------------------------------------------------------------
    # Constants and Base Values
    # ----------------------------------------------------------------------------------
    c0 = vf.add_const(0.0)
    c1 = vf.add_const(1.0)
    two_pi_over_3 = 2.0 * np.pi / 3.0

    # ----------------------------------------------------------------------------------
    # Inputs: instantaneous abc terminal voltages at the bus
    # ----------------------------------------------------------------------------------
    v_A = vf.add_var("v_A_" + name, reference=VarPowerFlowReferenceType.v_A)
    v_B = vf.add_var("v_B_" + name, reference=VarPowerFlowReferenceType.v_B)
    v_C = vf.add_var("v_C_" + name, reference=VarPowerFlowReferenceType.v_C)
    Tm = vf.add_var("Tm_" + name)
    v_f = vf.add_var("v_f_" + name)

    d_v_A = vf.add_var("d_v_A_" + name, reference=VarPowerFlowReferenceType.d_v_A)
    d_v_B = vf.add_var("d_v_B_" + name, reference=VarPowerFlowReferenceType.d_v_B)
    d_v_C = vf.add_var("d_v_C_" + name, reference=VarPowerFlowReferenceType.d_v_C)
    p_A = vf.add_var("P_A_" + name, reference=VarPowerFlowReferenceType.P_A)
    q_A = vf.add_var("Q_A_" + name, reference=VarPowerFlowReferenceType.Q_A)
    p_B = vf.add_var("P_B_" + name, reference=VarPowerFlowReferenceType.P_B)
    q_B = vf.add_var("Q_B_" + name, reference=VarPowerFlowReferenceType.Q_B)
    p_C = vf.add_var("P_C_" + name, reference=VarPowerFlowReferenceType.P_C)
    q_C = vf.add_var("Q_C_" + name, reference=VarPowerFlowReferenceType.Q_C)
    inputs = [v_A, v_B, v_C, Tm, v_f]

    # ----------------------------------------------------------------------------------
    # State variables
    # ----------------------------------------------------------------------------------
    # Flux linkages
    psi_d = vf.add_var("psi_d_" + name)
    psi_q = vf.add_var("psi_q_" + name)
    psi_0 = vf.add_var("psi_0_" + name)
    psi_f = vf.add_var("psi_f_" + name)
    psi_d1 = vf.add_var("psi_d1_" + name)
    psi_d2 = vf.add_var("psi_d2_" + name)
    psi_q1 = vf.add_var("psi_q1_" + name)
    psi_q2 = vf.add_var("psi_q2_" + name)
    psi_q3 = vf.add_var("psi_q3_" + name)

    # Rotor electrical angle and mechanical speed
    theta_elec = vf.add_var("theta_elec_" + name)
    w_mec = vf.add_var("w_mec_" + name)

    # Differential variables
    d_psi_d = vf.add_diff_var(name=f"d_psi_d_{name}", base_var=psi_d)
    d_psi_q = vf.add_diff_var(name=f"d_psi_q_{name}", base_var=psi_q)
    d_psi_0 = vf.add_diff_var(name=f"d_psi_0_{name}", base_var=psi_0)
    d_psi_f = vf.add_diff_var(name=f"d_psi_f_{name}", base_var=psi_f)
    d_psi_d1 = vf.add_diff_var(name=f"d_psi_d1_{name}", base_var=psi_d1)
    d_psi_d2 = vf.add_diff_var(name=f"d_psi_d2_{name}", base_var=psi_d2)
    d_psi_q1 = vf.add_diff_var(name=f"d_psi_q1_{name}", base_var=psi_q1)
    d_psi_q2 = vf.add_diff_var(name=f"d_psi_q2_{name}", base_var=psi_q2)
    d_psi_q3 = vf.add_diff_var(name=f"d_psi_q3_{name}", base_var=psi_q3)

    d_theta_elec = vf.add_diff_var(name=f"d_theta_elec_{name}", base_var=theta_elec)
    d_w_mec = vf.add_diff_var(name=f"d_w_mec_{name}", base_var=w_mec)

    # ----------------------------------------------------------------------------------
    # Algebraic variables
    # ----------------------------------------------------------------------------------
    # dq0 voltages
    v_d = vf.add_var("v_d_" + name)
    v_q = vf.add_var("v_q_" + name)
    v_0 = vf.add_var("v_0_" + name)

    # abc stator currents (positive when machine injects into the bus)
    i_A = vf.add_var("i_A_" + name, reference=VarPowerFlowReferenceType.i_A)
    i_B = vf.add_var("i_B_" + name, reference=VarPowerFlowReferenceType.i_B)
    i_C = vf.add_var("i_C_" + name, reference=VarPowerFlowReferenceType.i_C)

    # dq0 and rotor currents
    i_d = vf.add_var("i_d_" + name)
    i_q = vf.add_var("i_q_" + name)
    i_0 = vf.add_var("i_0_" + name)
    i_f = vf.add_var("i_f_" + name)
    i_d1 = vf.add_var("i_d1_" + name)
    i_d2 = vf.add_var("i_d2_" + name)
    i_q1 = vf.add_var("i_q1_" + name)
    i_q2 = vf.add_var("i_q2_" + name)
    i_q3 = vf.add_var("i_q3_" + name)

    # Mechanical/electrical auxiliaries
    w_elec = vf.add_var("w_elec_" + name)

    # Powers and torque
    Te = vf.add_var("Te_" + name)
    Pe = vf.add_var("Pe_" + name)
    Qe = vf.add_var("Qe_" + name)
    Pm = vf.add_var("Pm_" + name)

    # ----------------------------------------------------------------------------------
    # Parameters
    # ----------------------------------------------------------------------------------
    omega_base = vf.add_var("omega_base")

    La = vf.add_var("La_" + name)
    Lmq = vf.add_var("Lmq_" + name)
    X0 = vf.add_var("X0_" + name)
    Lf = vf.add_var("Lf_" + name)
    # Electrical resistances
    Ra = vf.add_var("Ra_" + name)
    Rf = vf.add_var("Rf_" + name)
    Rd1 = vf.add_var("Rd1_" + name)
    Rd2 = vf.add_var("Rd2_" + name)
    Rq1 = vf.add_var("Rq1_" + name)
    Rq2 = vf.add_var("Rq2_" + name)
    Rq3 = vf.add_var("Rq3_" + name)
    R0 = vf.add_var("R0_" + name)

    # Self inductances
    Ld = vf.add_var("Ld_" + name)
    Lq = vf.add_var("Lq_" + name)
    L0 = vf.add_var("L0_" + name)
    Lff = vf.add_var("Lff_" + name)
    Ld1 = vf.add_var("Ld1_" + name)
    Ld2 = vf.add_var("Ld2_" + name)
    Lq1 = vf.add_var("Lq1_" + name)
    Lq2 = vf.add_var("Lq2_" + name)
    Lq3 = vf.add_var("Lq3_" + name)

    # Mutual inductances
    Mdf = vf.add_var("Mdf_" + name)
    Mdd1 = vf.add_var("Mdd1_" + name)
    Mdd2 = vf.add_var("Mdd2_" + name)
    Mqq1 = vf.add_var("Mqq1_" + name)
    Mqq2 = vf.add_var("Mqq2_" + name)
    Mqq3 = vf.add_var("Mqq3_" + name)
    Mfd1 = vf.add_var("Mfd1_" + name)
    Mfd2 = vf.add_var("Mfd2_" + name)
    Md1d2 = vf.add_var("Md1d2_" + name)
    Mq1q2 = vf.add_var("Mq1q2_" + name)
    Mq1q3 = vf.add_var("Mq1q3_" + name)
    Mq2q3 = vf.add_var("Mq2q3_" + name)

    # Machine and base data
    p_poles = vf.add_var("p_poles_" + name)
    w_elec_base = vf.add_var("w_elec_base_" + name)
    w_mec_base = vf.add_var("w_mec_base_" + name)

    # Mechanical equivalent one-mass data
    H = vf.add_var("H_" + name)
    D = vf.add_var("D_" + name)
    w_mec_ref = vf.add_var("w_mec_ref_" + name)

    # ----------------------------------------------------------------------------------
    # Parameters needed for initialization from PF
    # ----------------------------------------------------------------------------------
    delta = vf.add_var("delta_" + name)

    phi_v_init: sym.Expr
    phi_init: sym.Expr
    vpk_init: sym.Expr
    ipk_init: sym.Expr
    phi_v_init, phi_init, vpk_init, ipk_init = get_pf_positive_sequence_init_refs(
        v_a=v_A,
        v_b=v_B,
        v_c=v_C,
        d_v_a=d_v_A,
        d_v_b=d_v_B,
        d_v_c=d_v_C,
        p_a=p_A,
        q_a=q_A,
        p_b=p_B,
        q_b=q_B,
        p_c=p_C,
        q_c=q_C,
        omega_base=omega_base,
    )

    # ----------------------------------------------------------------------------------
    # MODEL EQUATIONS
    # ----------------------------------------------------------------------------------
    templ.block = Block(
        state_eqs=[
            # 1. Stator and Rotor voltage equations (Generator sign convention)
            (-v_d - Ra * i_d + w_elec * psi_q),  # d_psi_d / dt
            (-v_q - Ra * i_q - w_elec * psi_d),  # d_psi_q / dt
            (-v_0 - R0 * i_0),  # d_psi_0 / dt
            (v_f - Rf * i_f),  # d_psi_f / dt
            (-Rd1 * i_d1),  # d_psi_d1 / dt
            (-Rd2 * i_d2),  # d_psi_d2 / dt
            (-Rq1 * i_q1),  # d_psi_q1 / dt
            (-Rq2 * i_q2),  # d_psi_q2 / dt
            (-Rq3 * i_q3),  # d_psi_q3 / dt

            # 2. Swing equations (Swing dynamics)
            w_elec_base * w_elec, # d_theta_elec
            (1.0 / (2.0 * H)) * (Tm - Te - D * (w_mec - w_mec_ref)), # d_omega_mec

        ],
        state_vars=[psi_d, psi_q, psi_0, psi_f, psi_d1, psi_d2, psi_q1, psi_q2, psi_q3, theta_elec, w_mec],
        diff_vars=[d_psi_d, d_psi_q, d_psi_0, d_psi_f, d_psi_d1, d_psi_d2,
            d_psi_q1, d_psi_q2, d_psi_q3, d_theta_elec, d_w_mec],

        algebraic_eqs=[
            # 3. Park Transform (abc -> dq0) - Synchronized with Simple Model
            v_d - (2 / 3) * (
                        sym.sin(theta_elec) * inputs[0] + sym.sin(theta_elec - two_pi_over_3) * inputs[1] + sym.sin(
                    theta_elec + two_pi_over_3) * inputs[2]),
            v_q - (2 / 3) * (
                        sym.cos(theta_elec) * inputs[0] + sym.cos(theta_elec - two_pi_over_3) * inputs[1] + sym.cos(
                    theta_elec + two_pi_over_3) * inputs[2]),
            v_0 - (1 / 3) * (inputs[0] + inputs[1] + inputs[2]),

            # 4. Inverse Park Transform (dq0 -> abc) for Stator Currents
            # i_A - (i_d * sym.sin(theta_elec) + i_q * sym.cos(theta_elec) + i_0),
            # i_B - (i_d * sym.sin(theta_elec - two_pi_over_3) + i_q * sym.cos(theta_elec - two_pi_over_3) + i_0),
            # i_C - (i_d * sym.sin(theta_elec + two_pi_over_3) + i_q * sym.cos(theta_elec + two_pi_over_3) + i_0),
            # 4. Park Transform (abc -> dq0) for Stator Currents
            i_d - (2 / 3) * (sym.sin(theta_elec) * i_A + sym.sin(theta_elec - two_pi_over_3) * i_B + sym.sin(
                theta_elec + two_pi_over_3) * i_C),
            i_q - (2 / 3) * (sym.cos(theta_elec) * i_A + sym.cos(theta_elec - two_pi_over_3) * i_B + sym.cos(
                theta_elec + two_pi_over_3) * i_C),
            i_0 - (1 / 3) * (i_A + i_B + i_C),

            # 5. Magnetic Flux-Current Equations (Stator current opposes rotor flux)
            psi_d - (Mdf * i_f + Mdd1 * i_d1 + Mdd2 * i_d2 - Ld * i_d),
            psi_q - (Mqq1 * i_q1 + Mqq2 * i_q2 + Mqq3 * i_q3 - Lq * i_q),
            psi_0 - (-L0 * i_0),
            psi_f - (Lff * i_f + Mfd1 * i_d1 + Mfd2 * i_d2 - Mdf * i_d),
            psi_d1 - (Mfd1 * i_f + Ld1 * i_d1 + Md1d2 * i_d2 - Mdd1 * i_d),
            psi_d2 - (Mfd2 * i_f + Md1d2 * i_d1 + Ld2 * i_d2 - Mdd2 * i_d),
            psi_q1 - (Lq1 * i_q1 + Mq1q2 * i_q2 + Mq1q3 * i_q3 - Mqq1 * i_q),
            psi_q2 - (Mq1q2 * i_q1 + Lq2 * i_q2 + Mq2q3 * i_q3 - Mqq2 * i_q),
            psi_q3 - (Mq1q3 * i_q1 + Mq2q3 * i_q2 + Lq3 * i_q3 - Mqq3 * i_q),


            # 6. Mechanical and Power Relations
            w_elec - (0.5 * p_poles) * w_mec,
            Te - (3 / 2) * (psi_q * i_d - psi_d * i_q),
            Pe - (inputs[0] * i_A + inputs[1] * i_B + inputs[2] * i_C),
            Qe - (1 / np.sqrt(3)) * (
                        (inputs[0] - inputs[1]) * i_C + (inputs[1] - inputs[2]) * i_A + (inputs[2] - inputs[0]) * i_B),

            Pe - Pm,
        ],
        algebraic_vars=[v_d, v_q, v_0,
                        i_d, i_q, i_0, i_f, i_d1, i_d2, i_q1, i_q2, i_q3,
                        i_A, i_B, i_C,
                        w_elec, Te, Pe, Qe, Pm],
        in_vars=inputs,
        out_vars=[i_A, i_B, i_C, w_mec, i_f, Te],
    )

    # ----------------------------------------------------------------------------------
    # External Mapping (Connecting to Grid/Power Flow)
    # ----------------------------------------------------------------------------------
    templ.block.external_mapping = {
        # VarPowerFlowReferenceType.P_N: None,
        # VarPowerFlowReferenceType.Q_N: None,
        # VarPowerFlowReferenceType.P_A: None,
        # VarPowerFlowReferenceType.Q_A: None,
        # VarPowerFlowReferenceType.P_B: None,
        # VarPowerFlowReferenceType.Q_B: None,
        # VarPowerFlowReferenceType.P_C: None,
        # VarPowerFlowReferenceType.Q_C: None,
        # VarPowerFlowReferenceType.i_N: None,
        VarPowerFlowReferenceType.i_A: i_A,
        VarPowerFlowReferenceType.i_B: i_B,
        VarPowerFlowReferenceType.i_C: i_C,
        VarPowerFlowReferenceType.d_v_A: d_v_A,
        VarPowerFlowReferenceType.d_v_B: d_v_B,
        VarPowerFlowReferenceType.d_v_C: d_v_C,
        VarPowerFlowReferenceType.P_A: p_A,
        VarPowerFlowReferenceType.Q_A: q_A,
        VarPowerFlowReferenceType.P_B: p_B,
        VarPowerFlowReferenceType.Q_B: q_B,
        VarPowerFlowReferenceType.P_C: p_C,
        VarPowerFlowReferenceType.Q_C: q_C,
        # VarPowerFlowReferenceType.d_v_N: None,
        # VarPowerFlowReferenceType.d_v_A: None,
        # VarPowerFlowReferenceType.d_v_B: None,
        # VarPowerFlowReferenceType.d_v_C: None,
    }

    # ----------------------------------------------------------------------------------
    # Parameter Definitions (Constants)
    # ----------------------------------------------------------------------------------

    templ.block.event_dict = {
        # --------------------------------------------------------------------------
        # Resistances
        # --------------------------------------------------------------------------
        La: vf.add_const(0.15),
        Lmq: vf.add_const(1.55),
        X0: vf.add_const(0.14),
        Lf: vf.add_const(0.10),

        Rf: vf.add_const(0.017),
        Rd1: vf.add_const(0.020),
        Rd2: vf.add_const(0.030),
        Rq1: vf.add_const(0.020),
        Rq2: vf.add_const(0.030),
        Rq3: vf.add_const(0.040),
        R0: vf.add_const(0.001),

        # --------------------------------------------------------------------------
        # Magnetic coefficients
        # Coherent with the simple model when dampers are zero:
        #
        # simple model:
        #   psi_d = Lmd*i_f - (Lmd + La)*i_d
        #   psi_q = -(Lmq + La)*i_q
        #   psi_f = (Lmd + Lf)*i_f - Lmd*i_d
        #
        # therefore:
        #   Ld  = Xd = La + Lmd
        #   Lq  = La + Lmq
        #   Mdf = Lmd
        #   Lff = Lmd + Lf
        # --------------------------------------------------------------------------
        # Rotor/damper self terms
        # These do not affect the reduction to the simple model when damper currents are zero,
        # but they should remain positive and of the same order as the rest of the magnetic terms.
        Ld1: vf.add_const(0.40),
        Ld2: vf.add_const(0.30),
        Lq1: vf.add_const(0.40),
        Lq2: vf.add_const(0.30),
        Lq3: vf.add_const(0.25),

        # --------------------------------------------------------------------------
        # Mutual inductances
        # --------------------------------------------------------------------------

        Mdd1: vf.add_const(0.25),
        Mdd2: vf.add_const(0.18),

        Mqq1: vf.add_const(0.30),
        Mqq2: vf.add_const(0.20),
        Mqq3: vf.add_const(0.10),

        Mfd1: vf.add_const(0.20),
        Mfd2: vf.add_const(0.15),
        Md1d2: vf.add_const(0.12),

        Mq1q2: vf.add_const(0.10),
        Mq1q3: vf.add_const(0.08),
        Mq2q3: vf.add_const(0.06),

        Mdf: Ld - La,
        Lff: Ld + Lf,
        Lq: Lmq + La,

        # --------------------------------------------------------------------------
        # Pole number and bases
        # --------------------------------------------------------------------------
        p_poles: vf.add_const(2.0),
        # --------------------------------------------------------------------------
        # One-mass mechanics
        # --------------------------------------------------------------------------
        H: vf.add_const(5.0),
        D: vf.add_const(2.0),
        w_mec_ref: vf.add_const(1.0),
        # --------------------------------------------------------------------------
        # Initialization auxiliaries obtained from PF
        # --------------------------------------------------------------------------
        delta: vf.add_const(None),
        d_v_A: vf.add_const(None),
        d_v_B: vf.add_const(None),
        d_v_C: vf.add_const(None),
        p_A: vf.add_const(None),
        q_A: vf.add_const(None),
        p_B: vf.add_const(None),
        q_B: vf.add_const(None),
        p_C: vf.add_const(None),
        q_C: vf.add_const(None),
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.omega_base: omega_base,
        ParamPowerFlowReferenceType.R1: Ra,
        ParamPowerFlowReferenceType.X1: Ld,
        ParamPowerFlowReferenceType.X0: L0,
    }

    # ----------------------------------------------------------------------------------
    # STEADY-STATE INITIALIZATION (Init Eqs)
    # ----------------------------------------------------------------------------------
    templ.block.init_eqs = {


        w_elec_base: omega_base,
        w_mec_base: omega_base,
        w_mec: c1,
        w_elec: (0.5 * p_poles) * w_mec,
        # Rotor angle initialization based on Load Angle (delta)
        delta: sym.atan((Ra * ipk_init * sym.sin(phi_init) - w_elec * Lq * ipk_init * sym.cos(phi_init)) / (
                    vpk_init + Ra * ipk_init * sym.cos(phi_init) + w_elec * Lq * ipk_init * sym.sin(phi_init))),
        theta_elec: phi_v_init + delta,

        # Terminal dq voltages and currents
        v_d: (2 / 3) * (sym.sin(theta_elec) * inputs[0] + sym.sin(theta_elec - two_pi_over_3) * inputs[1] + sym.sin(
            theta_elec + two_pi_over_3) * inputs[2]),
        v_q: (2 / 3) * (sym.cos(theta_elec) * inputs[0] + sym.cos(theta_elec - two_pi_over_3) * inputs[1] + sym.cos(
            theta_elec + two_pi_over_3) * inputs[2]),
        i_d: (2 / 3) * (sym.sin(theta_elec) * i_A + sym.sin(theta_elec - two_pi_over_3) * i_B + sym.sin(
            theta_elec + two_pi_over_3) * i_C),
        i_q: (2 / 3) * (sym.cos(theta_elec) * i_A + sym.cos(theta_elec - two_pi_over_3) * i_B + sym.cos(
            theta_elec + two_pi_over_3) * i_C),
        i_0: (1 / 3) * (i_A + i_B + i_C),

        # Dampers are in equilibrium (zero current in steady state)
        i_d1: c0, i_d2: c0, i_q1: c0, i_q2: c0, i_q3: c0,

        # Initial flux linkages from algebraic relations
        psi_q: (v_d + Ra * i_d) / w_elec,
        psi_d: -(v_q + Ra * i_q) / w_elec,
        psi_0: -L0 * i_0,

        # Field current initialization to match psi_d
        i_f: (psi_d + Ld * i_d) / Mdf,
        psi_f: Lff * i_f - Mdf * i_d,

        # Damper winding flux linkages
        psi_d1: Mfd1 * i_f - Mdd1 * i_d,
        psi_d2: Mfd2 * i_f - Mdd2 * i_d,
        psi_q1: -Mqq1 * i_q, psi_q2: -Mqq2 * i_q, psi_q3: -Mqq3 * i_q,

        # Initial mechanical torque to match electrical torque
        Te: (3 / 2) * (psi_q * i_d - psi_d * i_q),
        Pm: Pe,
    }

    # Derivatives must be zero in steady state
    templ.block.diff_init_eqs = {
        d_theta_elec: w_elec_base * w_elec,
        d_w_mec: c0,
        d_psi_d: c0,
        d_psi_q: c0,
        d_psi_0: c0,
        d_psi_f: c0,
        d_psi_d1: c0,
        d_psi_d2: c0,
        d_psi_q1: c0,
        d_psi_q2: c0,
        d_psi_q3: c0
    }

    return templ


def get_generator_sauer_pai_type_emt_template(vf: VarFactory, name: str = "sauer_pai_generator_emt_template"
                                              ) -> EmtModelTemplate:
    """
    Sauer-Pai synchronous generator model embedded in the EMT architecture,
    including explicit zero-sequence dynamics.

    References
    ----------
    Federico Milano, Power System Modelling and Scripting:
      - Section 15.1.3 Common Equations
      - Section 15.1.4 Stator Electrical Equations
      - Section 15.1.5 Magnetic Equations, Sauer-Pai model (15.13)-(15.15)

    Model structure
    ---------------
    Electromagnetic states:
        psi_d, psi_q, psi_0,
        e_qp, e_dp, psi_pp_d, psi_pp_q

    Mechanical / kinematic states:
        theta_abs, delta_rel, omega

    Inputs
    ------
    v_A, v_B, v_C:
        instantaneous abc terminal voltages
    Tm:
        mechanical torque input from governor
    v_f:
        field voltage input from exciter

    Sign convention
    ---------------
    - abc stator currents i_A, i_B, i_C are positive when LEAVING the generator
      and entering the network.
    - internal magnetic/electrical equations are written in Milano's physical d-q axes.
    - zero sequence is retained explicitly and represented as a stator-only homopolar
      branch:
            psi_0 + x0 * i_0 = 0

    Angles
    ------
    theta_abs:
        absolute electrical angle for abc <-> dq0 transforms
    delta_rel:
        rotor angle relative to the synchronous reference, used in Milano's
        common electromechanical equations

    Park transform convention used here
    -----------------------------------
    Physical dq0 quantities are defined from abc voltages/currents as:

        v_d = -(2/3) * Σ cos(theta_abs + shift_k) * v_k
        v_q =  (2/3) * Σ sin(theta_abs + shift_k) * v_k
        v_0 =  (1/3) * (v_A + v_B + v_C)

        i_d = -(2/3) * Σ cos(theta_abs + shift_k) * i_k
        i_q =  (2/3) * Σ sin(theta_abs + shift_k) * i_k
        i_0 =  (1/3) * (i_A + i_B + i_C)

    and the inverse transform is:

        i_A =  i_q*sin(theta_abs) - i_d*cos(theta_abs) + i_0
        i_B =  i_q*sin(theta_abs - 2π/3) - i_d*cos(theta_abs - 2π/3) + i_0
        i_C =  i_q*sin(theta_abs + 2π/3) - i_d*cos(theta_abs + 2π/3) + i_0

    Implemented equations
    ---------------------
    Common equations:
        d(theta_abs)/dt = omega_b * omega
        d(delta_rel)/dt = omega_b * (omega - omega_s)
        d(omega)/dt     = (Tm - T_e - D*(omega - omega_s)) / (2H)

        T_e = psi_d*i_q - psi_q*i_d

    Stator electrical equations:
        d(psi_d)/dt = omega_b * (ra*i_d + omega*psi_q + v_d)
        d(psi_q)/dt = omega_b * (ra*i_q - omega*psi_d + v_q)
        d(psi_0)/dt = omega_b * (ra*i_0 + v_0)

    Sauer-Pai magnetic equations:
        d(e_qp)/dt =
            (-e_qp - (xd - xdp)*(gamma_d1*i_d - gamma_d2*psi_pp_d + gamma_d2*e_qp) + v_f) / Td0p

        d(e_dp)/dt =
            (-e_dp + (xq - xqp)*(gamma_q1*i_q - gamma_q2*psi_pp_q - gamma_q2*e_dp)) / Tq0p

        d(psi_pp_d)/dt = (-psi_pp_d + e_qp - (xdp - xl)*i_d) / Td0pp
        d(psi_pp_q)/dt = (-psi_pp_q - e_dp - (xqp - xl)*i_q) / Tq0pp

    Algebraic magnetic equations:
        0 = psi_d + xdpp*i_d - gamma_d1*e_qp - (1 - gamma_d1)*psi_pp_d
        0 = psi_q + xqpp*i_q + gamma_q1*e_dp - (1 - gamma_q1)*psi_pp_q
        0 = psi_0 + x0*i_0

    Terminal powers (abc domain):
        p_e = v_A*i_A + v_B*i_B + v_C*i_C
        q_e = 1/sqrt(3) * [(v_A-v_B)i_C + (v_B-v_C)i_A + (v_C-v_A)i_B]

    Assumptions
    -----------
    1. Balanced rotor / Park-model machine.
    2. Zero sequence is NOT neglected.
    3. Zero-sequence path has no rotor coupling and is represented by x0 only.
    4. Tm and v_f are external controller inputs and are initialized at equilibrium.
    5. Initialization is pragmatic and closed-form, not a full nonlinear equilibrium solve.
    """

    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------
    c0 = vf.add_const(0.0)
    c1 = vf.add_const(1.0)
    two_pi_over_3 = 2.0 * np.pi / 3.0

    # ------------------------------------------------------------------
    # Inputs: abc terminal voltages + controller inputs
    # ------------------------------------------------------------------
    v_A = vf.add_var("v_A_" + name, reference=VarPowerFlowReferenceType.v_A)
    v_B = vf.add_var("v_B_" + name, reference=VarPowerFlowReferenceType.v_B)
    v_C = vf.add_var("v_C_" + name, reference=VarPowerFlowReferenceType.v_C)
    Tm = vf.add_var("Tm_" + name, shared_reference = "Tm_reference")
    v_f = vf.add_var("v_f_" + name, shared_reference = "v_f_reference")

    d_v_A = vf.add_var("d_v_A_" + name, reference=VarPowerFlowReferenceType.d_v_A)
    d_v_B = vf.add_var("d_v_B_" + name, reference=VarPowerFlowReferenceType.d_v_B)
    d_v_C = vf.add_var("d_v_C_" + name, reference=VarPowerFlowReferenceType.d_v_C)
    p_A = vf.add_var("P_A_" + name, reference=VarPowerFlowReferenceType.P_A)
    q_A = vf.add_var("Q_A_" + name, reference=VarPowerFlowReferenceType.Q_A)
    p_B = vf.add_var("P_B_" + name, reference=VarPowerFlowReferenceType.P_B)
    q_B = vf.add_var("Q_B_" + name, reference=VarPowerFlowReferenceType.Q_B)
    p_C = vf.add_var("P_C_" + name, reference=VarPowerFlowReferenceType.P_C)
    q_C = vf.add_var("Q_C_" + name, reference=VarPowerFlowReferenceType.Q_C)
    inputs = [v_A, v_B, v_C, Tm, v_f]
    #
    # ------------------------------------------------------------------
    # State variables
    # ------------------------------------------------------------------
    theta_abs = vf.add_var("theta_abs_" + name)
    omega = vf.add_var("omega_" + name, shared_reference = "omega_reference")

    psi_d = vf.add_var("psi_d_" + name)
    psi_q = vf.add_var("psi_q_" + name)
    psi_0 = vf.add_var("psi_0_" + name)

    e_qp = vf.add_var("e_qp_" + name)
    e_dp = vf.add_var("e_dp_" + name)
    psi_pp_d = vf.add_var("psi_pp_d_" + name)
    psi_pp_q = vf.add_var("psi_pp_q_" + name)

    # Differential variables
    d_theta_abs = vf.add_diff_var(name=f"d_theta_abs_{name}", base_var=theta_abs)
    d_omega = vf.add_diff_var(name=f"d_omega_{name}", base_var=omega)

    d_psi_d = vf.add_diff_var(name=f"d_psi_d_{name}", base_var=psi_d)
    d_psi_q = vf.add_diff_var(name=f"d_psi_q_{name}", base_var=psi_q)
    d_psi_0 = vf.add_diff_var(name=f"d_psi_0_{name}", base_var=psi_0)

    d_e_qp = vf.add_diff_var(name=f"d_e_qp_{name}", base_var=e_qp)
    d_e_dp = vf.add_diff_var(name=f"d_e_dp_{name}", base_var=e_dp)
    d_psi_pp_d = vf.add_diff_var(name=f"d_psi_pp_d_{name}", base_var=psi_pp_d)
    d_psi_pp_q = vf.add_diff_var(name=f"d_psi_pp_q_{name}", base_var=psi_pp_q)

    # ------------------------------------------------------------------
    # Algebraic variables
    # ------------------------------------------------------------------
    v_d = vf.add_var("v_d_" + name)
    v_q = vf.add_var("v_q_" + name)
    v_0 = vf.add_var("v_0_" + name)

    i_d = vf.add_var("i_d_" + name)
    i_q = vf.add_var("i_q_" + name)
    i_0 = vf.add_var("i_0_" + name)

    i_A = vf.add_var("i_A_" + name, reference=VarPowerFlowReferenceType.i_A)
    i_B = vf.add_var("i_B_" + name, reference=VarPowerFlowReferenceType.i_B)
    i_C = vf.add_var("i_C_" + name, reference=VarPowerFlowReferenceType.i_C)

    Te = vf.add_var("Te_" + name, shared_reference = "Te_reference")
    p_e = vf.add_var("p_e_" + name)
    q_e = vf.add_var("q_e_" + name)

    IRPu = vf.add_var("IRPu_" + name, shared_reference = "IRPu_reference")

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------
    ra = vf.add_var("ra_" + name)

    xd = vf.add_var("xd_" + name)
    xq = vf.add_var("xq_" + name)
    xdp = vf.add_var("xdp_" + name)
    xqp = vf.add_var("xqp_" + name)
    xdpp = vf.add_var("xdpp_" + name)
    xqpp = vf.add_var("xqpp_" + name)
    xl = vf.add_var("xl_" + name)
    x0 = vf.add_var("x0_" + name)

    Td0p = vf.add_var("Td0p_" + name)
    Tq0p = vf.add_var("Tq0p_" + name)
    Td0pp = vf.add_var("Td0pp_" + name)
    Tq0pp = vf.add_var("Tq0pp_" + name)

    gamma_d1 = vf.add_var("gamma_d1_" + name)
    gamma_q1 = vf.add_var("gamma_q1_" + name)
    gamma_d2 = vf.add_var("gamma_d2_" + name)
    gamma_q2 = vf.add_var("gamma_q2_" + name)

    H = vf.add_var("H_" + name)
    D = vf.add_var("D_" + name)
    omega_b = vf.add_var("omega_b_" + name)
    omega_s = vf.add_var("omega_s_" + name)

    phi_v_init: sym.Expr
    phi_init: sym.Expr
    vpk_init: sym.Expr
    ipk_init: sym.Expr
    phi_v_init, phi_init, vpk_init, ipk_init = get_pf_positive_sequence_init_refs(
        v_a=v_A,
        v_b=v_B,
        v_c=v_C,
        d_v_a=d_v_A,
        d_v_b=d_v_B,
        d_v_c=d_v_C,
        p_a=p_A,
        q_a=q_A,
        p_b=p_B,
        q_b=q_B,
        p_c=p_C,
        q_c=q_C,
        omega_base=omega_b,
    )


    # ------------------------------------------------------------------
    # MODEL EQUATIONS
    # ------------------------------------------------------------------
    templ.block = Block(
        state_eqs=[
            # absolute electrical angle for EMT transforms
            omega_b * omega,

            # swing equation driven by governor torque input
            (Tm - Te - D * (omega - omega_s)) / (2.0 * H),

            # stator electrical equations
            omega_b * (ra * i_d + omega * psi_q + v_d),
            omega_b * (ra * i_q - omega * psi_d + v_q),
            omega_b * (ra * i_0 + v_0),

            # Sauer-Pai magnetic equations
            (-IRPu + v_f) / Td0p,

            ( -e_dp + (xq - xqp) * (gamma_q1 * i_q - gamma_q2 * psi_pp_q - gamma_q2 * e_dp)) / Tq0p,

            (-psi_pp_d + e_qp - (xdp - xl) * i_d) / Td0pp,
            (-psi_pp_q - e_dp - (xqp - xl) * i_q) / Tq0pp,
        ],
        state_vars=[
            theta_abs, omega,
            psi_d, psi_q, psi_0,
            e_qp, e_dp, psi_pp_d, psi_pp_q
        ],
        diff_vars=[
            d_theta_abs, d_omega,
            d_psi_d, d_psi_q, d_psi_0,
            d_e_qp, d_e_dp, d_psi_pp_d, d_psi_pp_q
        ],

        algebraic_eqs=[
            # ----------------------------------------------------------
            # abc -> physical d-q-0
            # ----------------------------------------------------------
            v_d + (2.0 / 3.0) * (
                sym.cos(theta_abs) * v_A +
                sym.cos(theta_abs - two_pi_over_3) * v_B +
                sym.cos(theta_abs + two_pi_over_3) * v_C
            ),

            v_q - (2.0 / 3.0) * (
                sym.sin(theta_abs) * v_A +
                sym.sin(theta_abs - two_pi_over_3) * v_B +
                sym.sin(theta_abs + two_pi_over_3) * v_C
            ),

            v_0 - (1.0 / 3.0) * (v_A + v_B + v_C),

            # ----------------------------------------------------------
            # Sauer-Pai algebraic magnetic equations
            # ----------------------------------------------------------
            psi_d + xdpp * i_d - gamma_d1 * e_qp - (c1 - gamma_d1) * psi_pp_d,

            psi_q + xqpp * i_q + gamma_q1 * e_dp - (c1 - gamma_q1) * psi_pp_q,

            # zero-sequence algebraic magnetic relation
            psi_0 + x0 * i_0,

            # ----------------------------------------------------------
            # physical d-q-0 -> abc injected currents
            # ----------------------------------------------------------
            i_A - (i_q * sym.sin(theta_abs) - i_d * sym.cos(theta_abs) + i_0),

            i_B - (
                i_q * sym.sin(theta_abs - two_pi_over_3)
                - i_d * sym.cos(theta_abs - two_pi_over_3)
                + i_0
            ),

            i_C - (
                i_q * sym.sin(theta_abs + two_pi_over_3)
                - i_d * sym.cos(theta_abs + two_pi_over_3)
                + i_0
            ),

            # electromagnetic torque
            Te - (3.0 / 2.0) * (psi_d * i_q - psi_q * i_d),

            # terminal powers
            p_e - (v_A * i_A + v_B * i_B + v_C * i_C),

            q_e - (1.0 / np.sqrt(3.0)) * (
                (v_A - v_B) * i_C +
                (v_B - v_C) * i_A +
                (v_C - v_A) * i_B
            ),

            IRPu - (
                    e_qp + (xd - xdp) * (
                    gamma_d1 * i_d - gamma_d2 * psi_pp_d + gamma_d2 * e_qp
            )),
        ],
        algebraic_vars=[
            v_d, v_q, v_0,
            i_d, i_q, i_0,
            i_A, i_B, i_C,
            Te, p_e, q_e,
            IRPu
        ],
        in_vars=inputs,
        out_vars=[i_A, i_B, i_C, omega, IRPu, Te],
    )

    # ------------------------------------------------------------------
    # Parameter values
    # ------------------------------------------------------------------

    # Replace these defaults with actual machine data when available.




    templ.block.event_dict = {
        xq: vf.add_const(1.70),
        xdp: vf.add_const(0.30),
        xqp: vf.add_const(0.55),
        xdpp: vf.add_const(0.20),
        xqpp: vf.add_const(0.25),
        xl: vf.add_const(0.15),

        Td0p: vf.add_const(6.0),
        Tq0p: vf.add_const(0.8),
        Td0pp: vf.add_const(0.03),
        Tq0pp: vf.add_const(0.05),

        H: vf.add_const(5.0),
        D: vf.add_const(0.0),
        omega_s: vf.add_const(1.0),

        gamma_d1: (xdpp - xl) / (xdp - xl),
        gamma_q1: (xqpp - xl) / (xqp - xl),
        gamma_d2: (xdp - xdpp) / ((xdp - xl) ** 2),
        gamma_q2: (xqp - xqpp) / ((xqp - xl) ** 2),

        d_v_A: vf.add_const(None),
        d_v_B: vf.add_const(None),
        d_v_C: vf.add_const(None),
        p_A: vf.add_const(None),
        q_A: vf.add_const(None),
        p_B: vf.add_const(None),
        q_B: vf.add_const(None),
        p_C: vf.add_const(None),
        q_C: vf.add_const(None),
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.omega_base: omega_b,
        ParamPowerFlowReferenceType.R1: ra,
        ParamPowerFlowReferenceType.X1: xd,
        ParamPowerFlowReferenceType.X0: x0,
    }
    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------
    # Rotor angle estimate from transient internal emf phasor
    E_re = (
        vpk_init * sym.cos(phi_v_init)
        + ra * ipk_init * sym.cos(phi_init)
        - xqp * ipk_init * sym.sin(phi_init)
    )
    E_im = (
        vpk_init * sym.sin(phi_v_init)
        + ra * ipk_init * sym.sin(phi_init)
        + xqp * ipk_init * sym.cos(phi_init)
    )
    q_axis_span = xq - xqp
    q_axis_det = (vf.add_const(1.0) - gamma_q1) + q_axis_span * gamma_q2
    e_dp_init = (
        -(psi_q + xqpp * i_q) * q_axis_span * gamma_q2
        + (vf.add_const(1.0) - gamma_q1) * q_axis_span * gamma_q1 * i_q
    ) / q_axis_det
    psi_pp_q_init = (
        gamma_q1 * q_axis_span * gamma_q1 * i_q
        + (vf.add_const(1.0) + q_axis_span * gamma_q2) * (psi_q + xqpp * i_q)
    ) / q_axis_det

    templ.block.init_eqs = {

        omega: omega_s,

        theta_abs: sym.atan2(E_im, E_re),
        # terminal dq0 values in Milano physical axes
        v_d: vpk_init * sym.sin(theta_abs - phi_v_init),
        v_q: vpk_init * sym.cos(theta_abs - phi_v_init),
        v_0: c0,

        i_d: ipk_init * sym.sin(theta_abs - phi_init),
        i_q: ipk_init * sym.cos(theta_abs - phi_init),

        # PF initialization is typically balanced; keep zero-seq explicit but zero initially
        i_0: c0,

        # stator steady state from 15.9 with omega = 1 and dpsi/dt = 0
        psi_d: v_q + ra * i_q,
        psi_q: -v_d - ra * i_d,

        # zero-sequence magnetic initialization
        psi_0: -x0 * i_0,

        # Sauer-Pai q-axis steady-state initialization. These expressions are
        # chosen to satisfy both d_psi_pp_q = 0 and d_e_dp = 0 for the
        # implemented model equations.
        e_qp: psi_d + xdp * i_d,
        e_dp: (
            (xq - xqp) * (gamma_q1 + gamma_q2 * (xqp - xl))
            / (c1 - (xq - xqp) * gamma_q2)
        ) * i_q,

        psi_pp_d: (psi_d + xdpp * i_d - gamma_d1 * e_qp) / (c1 - gamma_d1),
        psi_pp_q: -e_dp - (xqp - xl) * i_q,

        # abc current injection
        i_A: i_q * sym.sin(theta_abs) - i_d * sym.cos(theta_abs) + i_0,
        i_B: i_q * sym.sin(theta_abs - two_pi_over_3) - i_d * sym.cos(theta_abs - two_pi_over_3) + i_0,
        i_C: i_q * sym.sin(theta_abs + two_pi_over_3) - i_d * sym.cos(theta_abs + two_pi_over_3) + i_0,

        IRPu: e_qp + (xd - xdp) * (
                gamma_d1 * i_d - gamma_d2 * psi_pp_d + gamma_d2 * e_qp
        ),

        # electromagnetic torque
        Te: (3.0 / 2.0) * (psi_d * i_q - psi_q * i_d),

        v_f: e_qp + (xd - xdp) * (
            gamma_d1 * i_d - gamma_d2 * psi_pp_d + gamma_d2 * e_qp
        ),

        p_e: v_A * i_A + v_B * i_B + v_C * i_C,

        q_e: (1.0 / np.sqrt(3.0)) * (
            (v_A - v_B) * i_C +
            (v_B - v_C) * i_A +
            (v_C - v_A) * i_B
        ),
    }

    templ.block.diff_init_eqs = {
        d_theta_abs: omega_b * c1,
        d_omega: c0,
        d_psi_d: c0,
        d_psi_q: c0,
        d_psi_0: c0,
        d_e_qp: c0,
        d_e_dp: c0,
        d_psi_pp_d: c0,
        d_psi_pp_q: c0,
    }

    # ------------------------------------------------------------------
    # External mapping
    # ------------------------------------------------------------------
    templ.block.external_mapping = {
        # VarPowerFlowReferenceType.P_N: None,
        # VarPowerFlowReferenceType.Q_N: None,
        # VarPowerFlowReferenceType.P_A: None,
        # VarPowerFlowReferenceType.Q_A: None,
        # VarPowerFlowReferenceType.P_B: None,
        # VarPowerFlowReferenceType.Q_B: None,
        # VarPowerFlowReferenceType.P_C: None,
        # VarPowerFlowReferenceType.Q_C: None,
        # VarPowerFlowReferenceType.i_N: None,
        VarPowerFlowReferenceType.i_A: i_A,
        VarPowerFlowReferenceType.i_B: i_B,
        VarPowerFlowReferenceType.i_C: i_C,
        VarPowerFlowReferenceType.d_v_A: d_v_A,
        VarPowerFlowReferenceType.d_v_B: d_v_B,
        VarPowerFlowReferenceType.d_v_C: d_v_C,
        VarPowerFlowReferenceType.P_A: p_A,
        VarPowerFlowReferenceType.Q_A: q_A,
        VarPowerFlowReferenceType.P_B: p_B,
        VarPowerFlowReferenceType.Q_B: q_B,
        VarPowerFlowReferenceType.P_C: p_C,
        VarPowerFlowReferenceType.Q_C: q_C,
        # VarPowerFlowReferenceType.d_v_N: None,
        # VarPowerFlowReferenceType.d_v_A: None,
        # VarPowerFlowReferenceType.d_v_B: None,
        # VarPowerFlowReferenceType.d_v_C: None,
    }

    return templ



def get_governor_emt(vf: VarFactory, name: str = "Governor") -> EmtModelTemplate:
    templ = EmtModelTemplate(name=name)
    inputs = [vf.add_var(name=f"omega_{name}", shared_reference = "omega_reference"), vf.add_var(name=f'Te_{name}', shared_reference = "Te_reference")]
    Tm = vf.add_var(name=f"Tm_{name}", shared_reference = "Tm_reference")  # Mechanical power input (pu
    Pm_ref = vf.add_var(f'Pm_ref_{name}')
    y_gov0 = vf.add_var(f'y_gov0_{name}')
    y2_3 = vf.add_var(f'y2_3_gov_{name}')

    d_y_gov0 = vf.add_diff_var(name=f'd_y_gov0_{name}', base_var=y_gov0)
    K = vf.add_var(f"K_{name}")  # governor gain (inverse droop)
    Pmax = vf.add_var(f"Pmax_{name}")  # max mechanical power (pu)
    Pmin = vf.add_var(f"Pmin_{name}")  # min mechanical power (pu)
    Uc = vf.add_var(f"Uc_{name}")  # max valve closing rate (pu/s)
    Uo = vf.add_var(f"Uo_{name}")  # max valve opening rate (pu/s)
    T_aux = vf.add_var(f"T_aux_{name}")

    # Control
    Kp = vf.add_var(f"Kp_{name}")
    Ki = vf.add_var(f"Ki_{name}")
    omega_ref = vf.add_var(f'omega_ref_{name}')
    p0 = vf.add_var(f'p0_{name}')
    P0 = vf.add_var(f'P0_{name}')
    T1 = vf.add_var(f'T1_gov_{name}')
    T3 = vf.add_var(f'T3_gov_{name}')

    events_dict = {
        # control parameters
        # The complete generator wrapper may replace this placeholder with a
        # model-level shared-power reference. The standalone governor keeps a
        # neutral default until the wrapper or initialization layer provides it.
        # Pm_ref: vf.add_const(None),
        Kp: vf.add_const(-0.01),
        Ki: vf.add_const(-0.01),
        p0: vf.add_const(1.0),
        P0: vf.add_const(0.01),
        omega_ref: vf.add_const(1),
        # Governor parameters
        K: vf.add_const(10.0),  # governor gain (inverse droop)
        Pmax: vf.add_const(12.0),  # max mechanical power (pu)
        Pmin: vf.add_const(-1.0),  # min mechanical power (pu)
        Uc: vf.add_const(-0.5),  # max valve closing rate (pu/s)
        Uo: vf.add_const(0.5),  # max valve opening rate (pu/s)
        T_aux: vf.add_const(0.0),
        T1: vf.add_const(0.2),
        T3: vf.add_const(1.0),
    }
    speed_error = omega_ref - inputs[0]
    # The governor regulates around the assigned mechanical-power reference so a
    # shared slack-bus initialization can prescribe one target per generator.
    torque_order = Pm_ref + y_gov0
    torque_tracking_error = inputs[1] - Pm_ref
    ramped_torque_order = sym.hard_sat(torque_order, Pmin, Pmax)

    templ.block = Block(
        state_eqs=[
            (K * speed_error + torque_tracking_error - y_gov0) / T1,
        ],
        state_vars=[y_gov0],
        diff_vars=[d_y_gov0],
        algebraic_eqs=[
            y2_3 - ramped_torque_order,
            Tm - y2_3,
        ],
        algebraic_vars=[y2_3, Tm],
        out_vars=[Tm],
        in_vars=inputs,
        event_dict=events_dict,
        name=name,

        init_eqs={
            y_gov0: vf.add_const(0.0),
            y2_3: ramped_torque_order,
            Tm: ramped_torque_order
        },
        api_obj_mapping={
            # Gains and limits
            ParamPowerFlowReferenceType.K: K,  # governor gain (inverse droop)
            ParamPowerFlowReferenceType.Pmax: Pmax,  # max mechanical power (pu)
            ParamPowerFlowReferenceType.Pmin: Pmin,  # min mechanical power (pu)
            ParamPowerFlowReferenceType.Uc: Uc,  # max valve closing rate (pu/s)
            ParamPowerFlowReferenceType.Uo: Uo,  # max valve opening rate (pu/s)
            ParamPowerFlowReferenceType.T_aux: T_aux,

            # Control
            ParamPowerFlowReferenceType.Kp: Kp,
            ParamPowerFlowReferenceType.Ki: Ki,
            ParamPowerFlowReferenceType.omega_ref: omega_ref,
            ParamPowerFlowReferenceType.p0: p0,
            ParamPowerFlowReferenceType.P0: P0,

            # shared ref
            ParamPowerFlowReferenceType.generator_share_p_ref: Pm_ref
        }

    )

    return templ


def get_stabilizer_emt(vf: VarFactory, name: str = "stabilizer") -> EmtModelTemplate:
    templ = EmtModelTemplate(name=name)

    parameters = {
        "t1": vf.add_const(0.1),  # lead time constant
        "t2": vf.add_const(0.02),  # lag time constant
        "t3": vf.add_const(0.02),  # lag time constant
        "t4": vf.add_const(0.1),  # second lag time constant
        "t5": vf.add_const(10.0),  # washout time constant
        "t6": vf.add_const(0.02),  # transducer time constant
    }

    # input variables
    # omega: omega from generator

    inputs = [vf.add_var(f"omega_{name}", shared_reference = "omega_reference")]

    # PSS parameters with typical values

    Ks = vf.add_var(f"Ks_{name}")  # stabilizer gain
    VPssMaxPu = vf.add_var(f"VPssMaxPu_{name}")  # max stabilizer output
    VPssMinPu = vf.add_var(f"VPssMinPu_{name}")  # min stabilizer output
    SNom = vf.add_var(f"SNom_{name}")  # nominal apparent power

    events_dict = {
        # Stabilizer parameters
        Ks: vf.add_const(20.0),  # stabilizer gain
        VPssMaxPu: vf.add_const(1.0),  # max stabilizer output
        VPssMinPu: vf.add_const(-1.0),  # min stabilizer output
        SNom: vf.add_const(1.0),  # nominal apparent power
    }

    # variables
    Vpss = vf.add_var(f'V_pss_{name}', shared_reference = "V_pss_reference")
    y1 = vf.add_var(f'y_stabilizer1_{name}')
    y2 = vf.add_var(f'y_stabilizer2_{name}')
    y3 = vf.add_var(f'y_stabilizer3_{name}')
    y4 = vf.add_var(f'y_stabilizer4_{name}')
    y5 = vf.add_var(f'y_stabilizer5_{name}')

    d_y1 = vf.add_diff_var(name=f'd_y_stabilizer1_{name}', base_var=y1)
    d_y2 = vf.add_diff_var(name=f'd_y_stabilizer2_{name}', base_var=y2)
    d_y4 = vf.add_diff_var(name=f'd_y_stabilizer4_{name}', base_var=y4)
    d_y5 = vf.add_diff_var(name=f'd_y_stabilizer5_{name}', base_var=y5)

    speed_deviation = inputs[0] - vf.add_const(1.0)
    washout_output = Ks * (y1 - y2)
    lead_lag_1 = y4 + (parameters["t1"].value / parameters["t2"].value) * (y3 - y4)
    lead_lag_2 = y5 + (parameters["t3"].value / parameters["t4"].value) * (lead_lag_1 - y5)

    templ.block = Block(
        state_eqs=[
            (speed_deviation - y1) / parameters["t6"].value,
            (y1 - y2) / parameters["t5"].value,
            (y3 - y4) / parameters["t2"].value,
            (lead_lag_1 - y5) / parameters["t4"].value,
        ],
        state_vars=[y1, y2, y4, y5],
        diff_vars=[d_y1, d_y2, d_y4, d_y5],
        algebraic_eqs=[
            y3 - washout_output,
            Vpss - sym.hard_sat(lead_lag_2, VPssMinPu, VPssMaxPu),
        ],
        algebraic_vars=[y3, Vpss],
        in_vars=inputs,
        out_vars=[Vpss],
        event_dict=events_dict,
        name=name,

        init_eqs={
            Vpss: vf.add_const(0.0),
            y1: vf.add_const(0.0),
            y2: vf.add_const(0.0),
            y3: vf.add_const(0.0),
            y4: vf.add_const(0.0),
            y5: vf.add_const(0.0),
        }
    )

    return templ


def get_exciter_emt(vf: VarFactory, name: str = "exciter") -> EmtModelTemplate:
    """

    :param vf:
    :param name:
    :return:
    """
    templ = EmtModelTemplate(name=name)

    parameters = {
        "Ka": vf.add_const(50.0),
        "Kf": vf.add_const(0.03),
        "tA": vf.add_const(0.1),
        "tB": vf.add_const(10.0),
        "tC": vf.add_const(1.0),
        "tE": vf.add_const(0.5),
        "tF": vf.add_const(1.0),
        "tR": vf.add_const(0.08),
        "Kd": vf.add_const(0.1),
        "Ke": vf.add_const(1.0),
        # The complete EMT generator uses the Sauer-Pai model, whose field channel
        # is initialized in the same units as IRPu.
        "Kfd": vf.add_const(1.0),
    }

    # input variables
    # IRPu: rotor current (pu) ???
    # Va: measured stator voltage (from generator) (pu)
    # Vpss: output from power system stabilizer (pu)

    IRPu = vf.add_var(f"IRPu_{name}", shared_reference = "IRPu_reference")
    v_A = vf.add_var("v_A_" + name, reference=VarPowerFlowReferenceType.v_A)
    v_B = vf.add_var("v_B_" + name, reference=VarPowerFlowReferenceType.v_B)
    v_C = vf.add_var("v_C_" + name, reference=VarPowerFlowReferenceType.v_C)
    Vpss = vf.add_var(f"V_pss_{name}", shared_reference = "V_pss_reference")

    inputs = [IRPu, v_A, v_B, v_C, Vpss]

    Vm = vf.add_var(f"Vm_{name}")

    Vf = vf.add_var(f"Vf_{name}", shared_reference = "v_f_reference")
    Efe = vf.add_var(f'Efe_{name}')
    UsRefPu = vf.add_var(name=f"UsRefPu_{name}")  # reference voltage (pu)
    y1 = vf.add_var(f'y_exciter1_{name}')
    y2 = vf.add_var(f'y_exciter2_{name}')
    y3 = vf.add_var(f'y_exciter3_{name}')
    y4 = vf.add_var(f'y_exciter4_{name}')

    d_y1 = vf.add_diff_var(name=f'd_y_exciter1_{name}', base_var=y1)
    d_y2 = vf.add_diff_var(name=f'd_y_exciter2_{name}', base_var=y2)
    d_y3 = vf.add_diff_var(name=f'd_y_exciter3_{name}', base_var=y3)
    d_y4 = vf.add_diff_var(name=f'd_y_exciter4_{name}', base_var=y4)
    d_Vf = vf.add_diff_var(name=f'd_Vf_{name}', base_var=Vf)

    # Exciter internal variables
    VeMaxPu = vf.add_var(f'VeMaxPu_{name}')
    u_aux = vf.add_var(f'u_aux_{name}')

    # ______________________________________________________________________________________
    #                                    parameters
    # ______________________________________________________________________________________

    # ---- Exciter (AVR) parameters ----
    AEz = vf.add_var(f"AEz_{name}")  # saturation gain
    BEz = vf.add_var(f"BEz_{name}")  # saturation exponential coefficient
    EfeMaxPu = vf.add_var(f"EfeMaxPu_{name}")  # max exciter field voltage (pu)
    EfeMinPu = vf.add_var(f"EfeMinPu_{name}")  # min exciter field voltage (pu)

    # ---- Exciter (AVR) time constants and limits ----

    TolLi = vf.add_var(f"TolLi_{name}")  # limiter crossing tolerance (fraction)

    VaMaxPu = vf.add_var(f"VaMaxPu_{name}")  # AVR output max (pu)
    VaMinPu = vf.add_var(f"VaMinPu_{name}")  # AVR output min (pu)
    VeMinPu = vf.add_var(f"VeMinPu_{name}")  # min exciter output voltage (pu)
    VfeMaxPu = vf.add_var(f"VfeMaxPu_{name}")  # max exciter field current signal (pu)

    # exciter submodel parameters
    AEx = vf.add_var(f"AEx_{name}")  # Gain of saturation function
    BEx = vf.add_var(f"BEx_{name}")  # Exponential coefficient of saturation function
    Se_threshold = vf.add_var(f"Se_threshold_{name}")  # Exponential coefficient of saturation function
    ToLLi = vf.add_var(f"ToLLi_{name}")  # Tolerance on limit crossing
    VeMinPu_submodel = vf.add_var(f"VeMinPu_submodel_{name}")  # Minimum exciter output voltage (pu)
    VfeMaxPu_submodel = vf.add_var(f"VfeMaxPu_submodel_{name}")  # Maximum exciter field current signal (pu)

    events_dict = {
        # Exciter (AVR) parameters
        UsRefPu: vf.add_const(None),  # reference voltage (pu)
        AEz: vf.add_const(0.02),  # saturation gain
        BEz: vf.add_const(1.5),  # saturation exponential coefficient
        Se_threshold: vf.add_const(1.0),  # saturation threshold
        EfeMaxPu: vf.add_const(15.0),  # max exciter field voltage (pu)
        EfeMinPu: vf.add_const(-5.0),  # min exciter field voltage (pu)

        # Time constants
        TolLi: vf.add_const(0.05),  # limiter crossing tolerance (fraction)

        # Limits
        VaMaxPu: vf.add_const(2.0),  # AVR output max (pu)
        VaMinPu: vf.add_const(-2.0),  # AVR output min (pu)
        VeMinPu: vf.add_const(-2.0),  # min exciter output voltage (pu)
        VfeMaxPu: vf.add_const(5.0),  # max exciter field current signal (pu)

        # Exciter submodel parameters
        AEx: vf.add_const(0.02),  # saturation gain
        BEx: vf.add_const(0.01),  # exponential coeff of saturation function
        ToLLi: vf.add_const(0.05),  # tolerance on limit crossing
        VeMinPu_submodel: vf.add_const(-5.1),  # minimum exciter output voltage
        VfeMaxPu_submodel: vf.add_const(5.0),  # max exciter field current signal
    }

    min_const = max(events_dict[VaMinPu].value, events_dict[EfeMinPu].value)
    i_field_abs = sym.abs(inputs[0])
    measured_vm = sym.sqrt((1.0 / 3.0) * (v_A * v_A + v_B * v_B + v_C * v_C))
    exciter_error = UsRefPu + inputs[4] - y1 - y2
    lead_lag_output = y3 + (parameters["tC"].value / parameters["tB"].value) * (exciter_error - y3)
    vf_positive = sym.hard_sat(Vf, vf.add_const(0.0), vf.add_const(1e6))
    saturation_term = AEx * vf_positive * (
        sym.exp(BEx * (vf_positive - Se_threshold)) - vf.add_const(1.0)
    ) * sym.heaviside(vf_positive - Se_threshold)
    field_feedback = parameters['Ke'].value * Vf + saturation_term
    field_ceiling = sym.hard_sat(VfeMaxPu - parameters['Kd'].value * i_field_abs,
                                 VeMinPu_submodel,
                                 VfeMaxPu_submodel)
    field_voltage_ref = sym.hard_sat(y4, min_const, field_ceiling)
    vf_init = parameters['Kfd'].value * inputs[0]
    field_feedback_init = parameters['Ke'].value * vf_init + AEx * sym.hard_sat(vf_init, vf.add_const(0.0), vf.add_const(1e6)) * (
        sym.exp(BEx * (sym.hard_sat(vf_init, vf.add_const(0.0), vf.add_const(1e6)) - Se_threshold)) - vf.add_const(1.0)
    ) * sym.heaviside(sym.hard_sat(vf_init, vf.add_const(0.0), vf.add_const(1e6)) - Se_threshold)
    templ.block = Block(
        state_eqs=[
            (Vm - y1) / parameters["tR"].value,
            (parameters["Kf"].value * Vf - y2) / parameters["tF"].value,
            (exciter_error - y3) / parameters["tB"].value,
            (parameters["Ka"].value * lead_lag_output - y4) / parameters["tA"].value,
            (field_voltage_ref - field_feedback) / parameters["tE"].value,
        ],
        state_vars=[y1, y2, y3, y4, Vf],
        diff_vars=[d_y1, d_y2, d_y3, d_y4, d_Vf],
        out_vars=[Vf],
        algebraic_eqs=[
            Vm - measured_vm,
            VeMaxPu - field_ceiling,
            u_aux - field_feedback,
            Efe - field_voltage_ref,
        ],
        algebraic_vars=[Vm, VeMaxPu, u_aux, Efe],
        in_vars=inputs,
        event_dict=events_dict,
        init_eqs={
            Vm: measured_vm,
            y1: Vm,
            Vf: vf_init,
            y2: parameters["Kf"].value * Vf,
            u_aux: field_feedback_init,
            VeMaxPu: field_ceiling,
            Efe: field_feedback_init,
            y4: Efe,
            y3: Efe / parameters["Ka"].value,
            UsRefPu: y1 + y2 - inputs[4] + y3,
        },
        name=name,
    )

    return templ


def get_complete_generator_template_emt(vf: VarFactory, name="complete_generator_emt_template") -> EmtModelTemplate:
    """

    :return:
    """
    templ = EmtModelTemplate(name=name)
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    # The wrapper exposes its own terminal-voltage inputs so EmtProblemDae can
    # bind the complete generator at the wrapper boundary. The internal machine
    # and exciter inputs are then connected to these wrapper variables before the
    # child blocks are flattened.
    v_a_in = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowReferenceType.v_A)
    v_b_in = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowReferenceType.v_B)
    v_c_in = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowReferenceType.v_C)

    # generate models
    # The exciter interface is defined in terms of IRPu -> v_f, which matches the
    # Sauer-Pai EMT generator semantics directly.
    # gen_mdl = get_simple_generator_emt_template(vf = vf).block
    # gen_mdl = get_generator_emt_type_template(vf = vf).block
    gen_mdl = get_generator_sauer_pai_type_emt_template(vf=vf, name=f"{name}_gen").block

    exciter_mdl = get_exciter_emt(vf=vf, name=f"{name}_exciter").block
    governor_mdl = get_governor_emt(vf=vf, name=f"{name}_governor").block
    stabilizer_mdl = get_stabilizer_emt(vf=vf, name=f"{name}_stabilizer").block

    # connect models
    # The wrapper boundary must substitute the internal voltage placeholders by
    # the exact wrapper input variables. Using ``update_model`` here keeps one
    # symbolic object across the whole flattened model, which is required later
    # when EmtProblemDae rewrites the wrapper terminal voltages to bus variables.
    gen_mdl.update_model(gen_mdl.in_vars[0], v_a_in)
    gen_mdl.update_model(gen_mdl.in_vars[1], v_b_in)
    gen_mdl.update_model(gen_mdl.in_vars[2], v_c_in)

    vf.add_connections([gen_mdl.in_vars[4]], [exciter_mdl.out_vars[0]]) # v_f
    vf.add_connections([exciter_mdl.in_vars[0]], [gen_mdl.out_vars[4]]) # IRPu / i_f

    # gen_mdl.connect([gen_mdl.in_vars[4]], [exciter_mdl.out_vars[0]])  # v_f
    # exciter_mdl.connect([exciter_mdl.in_vars[0]], [gen_mdl.out_vars[4]])  # IRPu / i_f

    exciter_mdl.update_model(exciter_mdl.in_vars[1], v_a_in)  # v_A
    exciter_mdl.update_model(exciter_mdl.in_vars[2], v_b_in)  # v_B
    exciter_mdl.update_model(exciter_mdl.in_vars[3], v_c_in)  # v_C

    vf.add_connections([exciter_mdl.in_vars[4]], [stabilizer_mdl.out_vars[0]]) # Vpps
    vf.add_connections([stabilizer_mdl.in_vars[0]], [gen_mdl.out_vars[3]]) # omega
    vf.add_connections([gen_mdl.in_vars[3]], [governor_mdl.out_vars[0]]) # Tm
    vf.add_connections([governor_mdl.in_vars[0]], [gen_mdl.out_vars[3]]) # omega
    vf.add_connections([governor_mdl.in_vars[1]], [gen_mdl.out_vars[5]]) # Te

    # exciter_mdl.connect([exciter_mdl.in_vars[4]], [stabilizer_mdl.out_vars[0]])  # Vpps
    # stabilizer_mdl.connect([stabilizer_mdl.in_vars[0]], [gen_mdl.out_vars[3]])  # omega
    # gen_mdl.connect([gen_mdl.in_vars[3]], [governor_mdl.out_vars[0]])  # Tm
    # governor_mdl.connect([governor_mdl.in_vars[0]], [gen_mdl.out_vars[3]])  # omega
    # governor_mdl.connect([governor_mdl.in_vars[1]], [gen_mdl.out_vars[5]])  # Te


    templ.block.children.append(gen_mdl)
    templ.block.children.append(governor_mdl)
    templ.block.children.append(stabilizer_mdl)
    templ.block.children.append(exciter_mdl)
    templ.block.in_vars = [v_a_in, v_b_in, v_c_in]
    # templ.block.unify_blocks()

    # pm_ref_var = None
    # event_parameter_var = None
    # for event_parameter_var in templ.block.event_dict.keys():
    #     if event_parameter_var.name.startswith("Pm_ref_"):
    #         pm_ref_var = event_parameter_var
    #     else:
    #         pass

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.v_A: v_a_in,
        VarPowerFlowReferenceType.v_B: v_b_in,
        VarPowerFlowReferenceType.v_C: v_c_in,
        VarPowerFlowReferenceType.i_A: gen_mdl.out_vars[0],
        VarPowerFlowReferenceType.i_B: gen_mdl.out_vars[1],
        VarPowerFlowReferenceType.i_C: gen_mdl.out_vars[2],
        VarPowerFlowReferenceType.d_v_A: gen_mdl.external_mapping[VarPowerFlowReferenceType.d_v_A],
        VarPowerFlowReferenceType.d_v_B: gen_mdl.external_mapping[VarPowerFlowReferenceType.d_v_B],
        VarPowerFlowReferenceType.d_v_C: gen_mdl.external_mapping[VarPowerFlowReferenceType.d_v_C],
        VarPowerFlowReferenceType.P_A: gen_mdl.external_mapping[VarPowerFlowReferenceType.P_A],
        VarPowerFlowReferenceType.Q_A: gen_mdl.external_mapping[VarPowerFlowReferenceType.Q_A],
        VarPowerFlowReferenceType.P_B: gen_mdl.external_mapping[VarPowerFlowReferenceType.P_B],
        VarPowerFlowReferenceType.Q_B: gen_mdl.external_mapping[VarPowerFlowReferenceType.Q_B],
        VarPowerFlowReferenceType.P_C: gen_mdl.external_mapping[VarPowerFlowReferenceType.P_C],
        VarPowerFlowReferenceType.Q_C: gen_mdl.external_mapping[VarPowerFlowReferenceType.Q_C],
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.omega_base:
            gen_mdl.api_obj_mapping[ParamPowerFlowReferenceType.omega_base],
        ParamPowerFlowReferenceType.R1:
            gen_mdl.api_obj_mapping[ParamPowerFlowReferenceType.R1],
        ParamPowerFlowReferenceType.X1:
            gen_mdl.api_obj_mapping[ParamPowerFlowReferenceType.X1],
        ParamPowerFlowReferenceType.X0:
            gen_mdl.api_obj_mapping[ParamPowerFlowReferenceType.X0],
        ParamPowerFlowReferenceType.generator_share_p_ref: governor_mdl.api_obj_mapping[ParamPowerFlowReferenceType.generator_share_p_ref],
    }

    templ.block.in_vars = [v_a_in, v_b_in, v_c_in] # v_abc
    templ.block.out_vars = [gen_mdl.out_vars[0], gen_mdl.out_vars[1], gen_mdl.out_vars[2]] #i_abc

    return templ
