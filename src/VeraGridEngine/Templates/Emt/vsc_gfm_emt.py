# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Any, List

import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowRefferenceType,
    VarPowerFlowRefferenceType,
)
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Block


def get_gfm_emt_template(vf: VarFactory, name: str = "VSC_GridForming") -> EmtModelTemplate:
    """
    Build a three-phase EMT grid-forming VSC.

    The converter is represented as a balanced internal source behind a
    series RL. The grid-forming behaviour comes from two simple droops:

    * P-f droop: ``d_omega/dt = (omega_setpoint - omega) / tau_omega`` with
      ``omega_setpoint = omega_ref - Kdp * (Pe - P_ref)``.
    * Q-V droop: ``d_Epk/dt = (Epk_setpoint - Epk) / tau_v`` with
      ``Epk_setpoint = V_ref - Kdq * (Qe - Q_ref)``.

    The DC side is modelled as a stiff voltage input. The PF / EMT bridge
    populates the positive-sequence references ``Vpk``, ``phi_v``, ``Ipk``
    and ``phi`` (via ``_set_vsc_pf_positive_sequence``). Every initial
    value of the EMT problem is derived analytically from those four PF
    quantities so the model starts exactly on the steady-state sinusoidal
    trajectory and stays there until a disturbance arrives.

    Convention of the PF references:

    * ``Vpk`` :   peak per-phase voltage in pu  (``sqrt(2) * |V1|``).
    * ``phi_v``: phasor angle of the positive-sequence voltage.
    * ``Ipk`` :   peak per-phase current in pu  (``sqrt(2) * |I1|``).
    * ``phi``  : ``phi_I - phi_V`` with ``I = conj(S / V)`` so ``I`` is
                in the VSC branch convention "current from bus into the
                converter". For generation, ``phi`` is close to ``pi``.

    :param vf: EMT variable factory.
    :param name: Symbolic block name suffix.
    :return: Configured EMT template.
    """
    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.VscDevice
    templ.name = name
    templ.block.name = name

    # Inputs: instantaneous abc bus voltages + DC bus voltage.
    v_A = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowRefferenceType.v_A)
    v_B = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowRefferenceType.v_B)
    v_C = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowRefferenceType.v_C)
    v_dc = vf.add_var(name=f"v_dc_{name}", reference=VarPowerFlowRefferenceType.Vdc)
    inputs: List[Any] = [v_A, v_B, v_C, v_dc]

    # States: three phase currents, internal angle, frequency, EMF.
    i_A = vf.add_var(name=f"i_A_{name}", reference=VarPowerFlowRefferenceType.i_A)
    i_B = vf.add_var(name=f"i_B_{name}", reference=VarPowerFlowRefferenceType.i_B)
    i_C = vf.add_var(name=f"i_C_{name}", reference=VarPowerFlowRefferenceType.i_C)
    theta = vf.add_var(name=f"theta_{name}")
    omega = vf.add_var(name=f"omega_{name}")
    Epk = vf.add_var(name=f"Epk_{name}")

    d_i_A = vf.add_diff_var(name=f"d_i_A_{name}", base_var=i_A)
    d_i_B = vf.add_diff_var(name=f"d_i_B_{name}", base_var=i_B)
    d_i_C = vf.add_diff_var(name=f"d_i_C_{name}", base_var=i_C)
    d_theta = vf.add_diff_var(name=f"d_theta_{name}", base_var=theta)
    d_omega = vf.add_diff_var(name=f"d_omega_{name}", base_var=omega)
    d_Epk = vf.add_diff_var(name=f"d_Epk_{name}", base_var=Epk)

    # Algebraic variables: internal EMFs, powers.
    e_A = vf.add_var(name=f"e_A_{name}")
    e_B = vf.add_var(name=f"e_B_{name}")
    e_C = vf.add_var(name=f"e_C_{name}")
    Pe = vf.add_var(name=f"Pe_{name}")
    Qe = vf.add_var(name=f"Qe_{name}")

    # Static parameters and droop / control set-points.
    omega_base = vf.add_var(name=f"omega_base_{name}")
    R_s = vf.add_var(name=f"R_s_{name}")
    X_s = vf.add_var(name=f"X_s_{name}")
    Kdp = vf.add_var(name=f"Kdp_{name}")
    Kdq = vf.add_var(name=f"Kdq_{name}")
    tau_omega = vf.add_var(name=f"tau_omega_{name}")
    tau_v = vf.add_var(name=f"tau_v_{name}")
    omega_ref = vf.add_var(name=f"omega_ref_{name}")
    P_ref = vf.add_var(name=f"P_ref_{name}")
    Q_ref = vf.add_var(name=f"Q_ref_{name}")
    V_ref = vf.add_var(name=f"V_ref_{name}")
    Qf = vf.add_var(name=f"Qf_{name}")

    # PF positive-sequence references. The EMT bridge populates these
    # through ``_set_vsc_pf_positive_sequence`` when they are exposed in
    # the external mapping below. They are the SINGLE source of truth for
    # the EMT initialization — every initial value is derived from them.
    Vpk_ref = vf.add_var(name=f"Vpk_ref_{name}")
    phi_v_ref = vf.add_var(name=f"phi_v_ref_{name}")
    Ipk_ref = vf.add_var(name=f"Ipk_ref_{name}")
    phi_ref = vf.add_var(name=f"phi_ref_{name}")

    # Instantaneous algebraic expressions (used at runtime, NOT for init).
    # Sign convention: ``i_A`` is the current from the bus into the
    # converter (branch convention). The active and reactive power
    # ``delivered by the converter to the bus`` is therefore the negative
    # of the instantaneous ``i * v`` sum.
    Pe_expr = -(i_A * v_A + i_B * v_B + i_C * v_C)
    Qe_expr = -(1.0 / np.sqrt(3.0)) * (
        (v_A - v_B) * i_C
        + (v_B - v_C) * i_A
        + (v_C - v_A) * i_B
    )

    two_pi_over_3: float = 2.0 * np.pi / 3.0

    # --------------------------------------------------------------
    # Initialization derived analytically from the PF positive-
    # sequence references.
    #
    # Sin-convention sinusoid sample at ``t = 0``:
    #     v_a(t)  = Vpk * sin(omega * t + phi_v)
    #     i_a(t)  = Ipk * sin(omega * t + phi_v + phi)
    #
    # Per-phase peak voltage and current samples at ``t = 0``:
    theta_i_init_expr = phi_v_ref + phi_ref

    v_A_init_expr = Vpk_ref * sym.sin(phi_v_ref)
    v_B_init_expr = Vpk_ref * sym.sin(phi_v_ref - two_pi_over_3)
    v_C_init_expr = Vpk_ref * sym.sin(phi_v_ref + two_pi_over_3)

    i_A_init_expr = Ipk_ref * sym.sin(theta_i_init_expr)
    i_B_init_expr = Ipk_ref * sym.sin(theta_i_init_expr - two_pi_over_3)
    i_C_init_expr = Ipk_ref * sym.sin(theta_i_init_expr + two_pi_over_3)

    # EMF peak phasor (peak units, sin convention):
    #     E_phasor_peak = V_phasor_peak - Z * I_phasor_peak
    # where Z = R + j*X and the phasors are
    #     V_phasor_peak = Vpk * exp(j * phi_v)
    #     I_phasor_peak = Ipk * exp(j * (phi_v + phi))
    V_re_expr = Vpk_ref * sym.cos(phi_v_ref)
    V_im_expr = Vpk_ref * sym.sin(phi_v_ref)
    I_re_expr = Ipk_ref * sym.cos(theta_i_init_expr)
    I_im_expr = Ipk_ref * sym.sin(theta_i_init_expr)

    ZI_re_expr = R_s * I_re_expr - X_s * I_im_expr
    ZI_im_expr = R_s * I_im_expr + X_s * I_re_expr

    E_re_expr = V_re_expr - ZI_re_expr
    E_im_expr = V_im_expr - ZI_im_expr

    c_eps = vf.add_const(1.0e-24)
    Epk_init_expr = sym.sqrt(E_re_expr * E_re_expr
                             + E_im_expr * E_im_expr + c_eps)
    theta_init_expr = sym.atan2(E_im_expr, E_re_expr)

    e_A_init_expr = Epk_init_expr * sym.sin(theta_init_expr)
    e_B_init_expr = Epk_init_expr * sym.sin(theta_init_expr - two_pi_over_3)
    e_C_init_expr = Epk_init_expr * sym.sin(theta_init_expr + two_pi_over_3)

    # Average 3-ph powers for balanced steady state in branch convention.
    # For balanced sinusoids in sin convention (sin(omega*t + phi_*)):
    #     i_a·v_a + i_b·v_b + i_c·v_c        = (3/2)·Vpk·Ipk·cos(phi)
    #     (1/√3)·Σ (v_a−v_b)·i_c            = -(3/2)·Vpk·Ipk·sin(phi)
    # The model's algebraic equations use ``Pe_expr = -(i·v)_sum`` and
    # ``Qe_expr = -(1/√3)·Σ(...)``, so:
    #     Pe_steady = -(3/2)·Vpk·Ipk·cos(phi)
    #     Qe_steady = +(3/2)·Vpk·Ipk·sin(phi)
    # For generation, ``phi ≈ π`` so ``cos(phi) < 0`` and ``Pe > 0``;
    # the small imaginary part of the PF current phasor gives the
    # observed sign of ``Qe``.
    c_3_2 = vf.add_const(1.5)
    Pe_init_expr = -c_3_2 * Vpk_ref * Ipk_ref * sym.cos(phi_ref)
    Qe_init_expr = c_3_2 * Vpk_ref * Ipk_ref * sym.sin(phi_ref)

    # Classic droop differential equations: ``P_ref`` and ``Q_ref`` are
    # constants pinned at init to the PF operating point ``Pe_init`` /
    # ``Qe_init``. With matched load models in PF and EMT, this gives an
    # exactly flat start (droop input ``Pe - P_ref = 0`` at ``t = 0``)
    # and a textbook post-event response with permanent droop offset
    # ``Δomega = -Kdp · ΔPe``.
    state_eqs: List[Any] = [
        omega_base * (v_A - R_s * i_A - e_A) / X_s,
        omega_base * (v_B - R_s * i_B - e_B) / X_s,
        omega_base * (v_C - R_s * i_C - e_C) / X_s,
        omega_base * omega,
        ((omega_ref - Kdp * (Pe - P_ref)) - omega) / tau_omega,
        ((V_ref - Kdq * (Qe - Q_ref)) - Epk) / tau_v,
    ]
    state_vars: List[Any] = [i_A, i_B, i_C, theta, omega, Epk]

    # Algebraic equations.
    algebraic_eqs: List[Any] = [
        e_A - Epk * sym.sin(theta),
        e_B - Epk * sym.sin(theta - two_pi_over_3),
        e_C - Epk * sym.sin(theta + two_pi_over_3),
        Pe - Pe_expr,
        Qe - Qe_expr,
    ]
    algebraic_vars: List[Any] = [
        e_A, e_B, e_C,
        Pe, Qe,
    ]

    templ.block = Block(
        state_eqs=state_eqs,
        state_vars=state_vars,
        algebraic_eqs=algebraic_eqs,
        algebraic_vars=algebraic_vars,
        in_vars=inputs,
        out_vars=[i_A, i_B, i_C],
    )

    templ.block.diff_vars = [d_i_A, d_i_B, d_i_C, d_theta, d_omega, d_Epk]

    # External mapping. The four ``Vpk`` / ``phi_v`` / ``Ipk`` / ``phi``
    # entries are what the EMT bridge populates from the PF positive-
    # sequence solution (see ``_set_vsc_pf_positive_sequence``).
    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.v_A: v_A,
        VarPowerFlowRefferenceType.v_B: v_B,
        VarPowerFlowRefferenceType.v_C: v_C,
        VarPowerFlowRefferenceType.i_A: i_A,
        VarPowerFlowRefferenceType.i_B: i_B,
        VarPowerFlowRefferenceType.i_C: i_C,
        VarPowerFlowRefferenceType.Vdc: v_dc,
        VarPowerFlowRefferenceType.Qf: Qf,
        VarPowerFlowRefferenceType.Vpk: Vpk_ref,
        VarPowerFlowRefferenceType.phi_v: phi_v_ref,
        VarPowerFlowRefferenceType.Ipk: Ipk_ref,
        VarPowerFlowRefferenceType.phi: phi_ref,
    }

    # API-object mapping.
    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.omega_base: omega_base,
        ParamPowerFlowRefferenceType.R1: R_s,
        ParamPowerFlowRefferenceType.X1: X_s,
    }

    # Runtime / PF-bound parameters.
    # ``Vpk_ref``, ``phi_v_ref``, ``Ipk_ref``, ``phi_ref`` are seeded by
    # the bridge. ``P_ref``, ``Q_ref``, ``V_ref`` are pinned by
    # ``init_eqs`` to the analytical PF steady-state values, so the
    # droop input is zero at ``t = 0``.
    templ.block.event_dict = {
        omega_base: vf.add_const(2.0 * np.pi * 50.0),
        R_s: vf.add_const(0.01),
        X_s: vf.add_const(0.1),
        Kdp: vf.add_const(0.05),
        Kdq: vf.add_const(0.05),
        tau_omega: vf.add_const(0.05),
        tau_v: vf.add_const(0.05),
        omega_ref: vf.add_const(1.0),
        Qf: vf.add_const(0.0),
        Vpk_ref: vf.add_const(None),
        phi_v_ref: vf.add_const(None),
        Ipk_ref: vf.add_const(None),
        phi_ref: vf.add_const(None),
        P_ref: vf.add_const(None),
        Q_ref: vf.add_const(None),
        V_ref: vf.add_const(None),
    }

    # Initialization equations.
    #
    # Everything is pinned to a function of the PF positive-sequence
    # references (``Vpk_ref``, ``phi_v_ref``, ``Ipk_ref``, ``phi_ref``).
    # These are populated by the EMT-PF bridge once per build and do not
    # change during simulation, so the consistency Newton has nothing to
    # shift — the explicit init already places the system on the exact
    # steady-state sinusoidal trajectory.
    templ.block.init_eqs = {
        # Bus AC sample at t = 0 — pin v_A/v_B/v_C so KCL sees the same
        # values that the analytical EMF formula assumes.
        v_A: v_A_init_expr,
        v_B: v_B_init_expr,
        v_C: v_C_init_expr,

        # Converter currents at t = 0 in branch convention.
        i_A: i_A_init_expr,
        i_B: i_B_init_expr,
        i_C: i_C_init_expr,

        # Internal state.
        theta: theta_init_expr,
        omega: vf.add_const(1.0),
        Epk: Epk_init_expr,

        # Internal EMF samples at t = 0.
        e_A: e_A_init_expr,
        e_B: e_B_init_expr,
        e_C: e_C_init_expr,

        # ``Pe`` and ``Qe`` are NOT pinned via ``init_eqs`` because the
        # current init code path (``_collect_reduced_initialization_problem``)
        # adds every algebraic variable to the reduced Newton system with
        # the runtime algebraic equation as its residual, ignoring any
        # ``init_eqs`` entry for algebraic vars. Pinning them here is
        # silently dead code. Pe / Qe are determined by the runtime
        # equations from the seeded ``v`` and ``i`` samples.
        #
        # Side effect we know about: at t=0 the bus per-phase voltages
        # are not yet populated in the order the init Newton expects,
        # so ``Qe_expr(0)`` evaluates to exactly 0 instead of the
        # analytical PF value (~0.05 pu). The runtime algebraic equation
        # closes this in the very next integrator step, leaving a small
        # one-step jump on ``Pe`` and ``Qe`` (a few mpu on Pe, ~50 mpu
        # on Qe). Tracked: needs a fix to ``initialization_emt.py`` so
        # algebraic vars in ``init_guess`` are skipped by the reduced
        # system, or so the bridge populates buses before init starts.
        P_ref: Pe_init_expr,
        Q_ref: Qe_init_expr,
        V_ref: Epk_init_expr,
    }

    # Differential initialization equations.
    # ``d_i_A(0)`` is the analytical derivative of the steady-state
    # sinusoid at ``t = 0``:
    #     d/dt [Ipk * sin(omega_base * t + phi_v + phi)] _{t=0}
    #         = Ipk * omega_base * cos(phi_v + phi)
    d_i_A_init_expr = omega_base * Ipk_ref * sym.cos(theta_i_init_expr)
    d_i_B_init_expr = omega_base * Ipk_ref * sym.cos(theta_i_init_expr - two_pi_over_3)
    d_i_C_init_expr = omega_base * Ipk_ref * sym.cos(theta_i_init_expr + two_pi_over_3)
    templ.block.diff_init_eqs = {
        d_i_A: d_i_A_init_expr,
        d_i_B: d_i_B_init_expr,
        d_i_C: d_i_C_init_expr,
        d_theta: omega_base * vf.add_const(1.0),
        d_omega: vf.add_const(0.0),
        d_Epk: vf.add_const(0.0),
    }

    return templ
