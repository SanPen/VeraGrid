# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


import numpy as np
from typing import List, Any
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, DeviceType, ParamPowerFlowRefferenceType

def get_generator_thevenin_rl_emt_template(vf: VarFactory,
                                           name: str = "emt_thevenin_eq_generator_template"
                                           ) -> EmtModelTemplate:
    """
    Simple EMT three-phase Thevenin generator behind series R-X.

    Purpose:
        This is a robust test injection model to validate the EMT injection interface
        (bus KCL coupling, initialization from PF, current sign conventions, etc.)
        without the full complexity of a synchronous machine model.

    Sign convention:
        Currents i_A, i_B, i_C are positive when injected from the generator into the bus.
        This matches the sign convention already used by the rest of the EMT injection interface.

    Inputs:
        v_A, v_B, v_C : instantaneous bus terminal voltages [pu]

    States:
        i_A, i_B, i_C : phase currents injected into the bus [pu]
        theta         : absolute electrical angle of the internal source [rad]

    Differential equations:
        di/dt = omega_base * (e - R_s i - v_bus) / X_s
        dtheta/dt = omega_base

    Initialization from PF:
        The model expects the generic PF->EMT init layer to provide:
            - i_A, i_B, i_C  (instantaneous current values at t=0)
            - phi_v          (positive-sequence voltage angle)
            - phi            (current angle relative to positive-sequence voltage)
            - Vpk            (positive-sequence voltage peak magnitude)
            - Ipk            (positive-sequence current peak magnitude)

        From those values, the model computes:
            - delta : internal source angle relative to terminal positive-sequence voltage
            - Epk   : internal source peak magnitude
            - theta = phi_v + delta

        using the Thevenin steady-state relation:
            E = V + (R + jX) I

    :param vf: EMT  VarFactory
    :param name: Model name
    :return: EmtModelTemplate
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    # ----------------------------------------------------------------------------------
    # Constants for symbolic expressions
    # ----------------------------------------------------------------------------------
    c05 = vf.add_const(0.5)

    # ----------------------------------------------------------------------------------
    # Inputs: bus terminal instantaneous phase voltages
    # ----------------------------------------------------------------------------------
    v_A = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowRefferenceType.v_A)
    v_B = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowRefferenceType.v_B)
    v_C = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowRefferenceType.v_C)
    inputs = [v_A, v_B, v_C]

    # ----------------------------------------------------------------------------------
    # States
    # ----------------------------------------------------------------------------------
    i_A = vf.add_var(name=f"i_A_{name}", reference=VarPowerFlowRefferenceType.i_A)
    i_B = vf.add_var(name=f"i_B_{name}", reference=VarPowerFlowRefferenceType.i_B)
    i_C = vf.add_var(name=f"i_C_{name}", reference=VarPowerFlowRefferenceType.i_C)
    theta = vf.add_var("theta_" + name)

    # Diff vars
    d_i_A = vf.add_diff_var(name=f"d_i_A_{name}", base_var=i_A)
    d_i_B = vf.add_diff_var(name=f"d_i_B_{name}", base_var=i_B)
    d_i_C = vf.add_diff_var(name=f"d_i_C_{name}", base_var=i_C)
    d_theta = vf.add_diff_var(name=f"d_theta_{name}", base_var=theta)

    # ----------------------------------------------------------------------------------
    # Algebraic vars
    # ----------------------------------------------------------------------------------
    e_A = vf.add_var("e_A_" + name)
    e_B = vf.add_var("e_B_" + name)
    e_C = vf.add_var("e_C_" + name)

    Pe = vf.add_var("Pe_" + name)
    Qe = vf.add_var("Qe_" + name)

    # ----------------------------------------------------------------------------------
    # Parameters
    # ----------------------------------------------------------------------------------
    omega_base = vf.add_var("omega_base")
    R_s = vf.add_var("R_s")
    X_s = vf.add_var("X_s")

    # Init-only / PF-derived auxiliary quantities
    phi_v = vf.add_var("phi_v_" + name)
    phi = vf.add_var("phi_" + name)
    Vpk = vf.add_var("Vpk_" + name)
    Ipk = vf.add_var("Ipk_" + name)

    E_scale = vf.add_var("E_scale_" + name)

    E_re = Vpk + R_s * Ipk * sym.cos(phi) - X_s * Ipk * sym.sin(phi)
    E_im = R_s * Ipk * sym.sin(phi) + X_s * Ipk * sym.cos(phi)
    delta_expr = sym.atan(E_im / E_re)
    Epk_expr = ((E_re ** 2 + E_im ** 2) ** c05)

    # ----------------------------------------------------------------------------------
    # Block
    # ----------------------------------------------------------------------------------
    templ.block = Block(
        state_eqs=[
            omega_base * (e_A - R_s * i_A - v_A) / X_s,
            omega_base * (e_B - R_s * i_B - v_B) / X_s,
            omega_base * (e_C - R_s * i_C - v_C) / X_s,
            omega_base,
        ],
        state_vars=[i_A, i_B, i_C, theta],

        algebraic_eqs=[
            e_A - E_scale * Epk_expr * sym.sin(theta),
            e_B - E_scale * Epk_expr * sym.sin(theta - 2 * np.pi / 3),
            e_C - E_scale * Epk_expr * sym.sin(theta + 2 * np.pi / 3),

            Pe - (i_A * v_A + i_B * v_B + i_C * v_C),
            Qe - (1 / np.sqrt(3)) * (
                (v_A - v_B) * i_C +
                (v_B - v_C) * i_A +
                (v_C - v_A) * i_B
            ),
        ],
        algebraic_vars=[e_A, e_B, e_C, Pe, Qe],

        in_vars=inputs,
        out_vars=[i_A, i_B, i_C],
    )

    templ.block.diff_vars = [d_i_A, d_i_B, d_i_C, d_theta]

    # ----------------------------------------------------------------------------------
    # External mapping
    # ----------------------------------------------------------------------------------
    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.v_N: None,
        VarPowerFlowRefferenceType.v_A: v_A,
        VarPowerFlowRefferenceType.v_B: v_B,
        VarPowerFlowRefferenceType.v_C: v_C,
        VarPowerFlowRefferenceType.P: None,
        VarPowerFlowRefferenceType.Q: None,
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

    # ----------------------------------------------------------------------------------
    # Event dict
    # ----------------------------------------------------------------------------------

    templ.block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.omega_base: omega_base,
        ParamPowerFlowRefferenceType.R1: R_s,
        ParamPowerFlowRefferenceType.X1: X_s,
        ParamPowerFlowRefferenceType.X0: None,
    }

    templ.block.event_dict = {
        # PF-derived init-only values
        phi_v: vf.add_const(None),
        phi: vf.add_const(None),
        Vpk: vf.add_const(None),
        Ipk: vf.add_const(None),
        # Local eventable source-voltage scaling.
        # This allows creating overvoltage events.
        E_scale: vf.add_const(1.0),
    }

    # ----------------------------------------------------------------------------------
    # Initialization equations
    # ----------------------------------------------------------------------------------
    #
    # Thevenin steady-state in positive sequence:
    #
    #   E = V + (R + jX) I
    #
    # If:
    #   V = Vpk ∠phi_v
    #   I = Ipk ∠(phi_v + phi)
    #
    # then relative to phi_v:
    #
    #   E_rel = Vpk + (R + jX) Ipk ∠phi
    #
    # whose rectangular components are:
    #
    #   E_re = Vpk + R Ipk cos(phi) - X Ipk sin(phi)
    #   E_im =       R Ipk sin(phi) + X Ipk cos(phi)
    #
    # so:
    #
    #   delta = angle(E_rel)
    #   Epk = |E_rel|
    #   theta = phi_v + delta
    #


    templ.block.init_eqs = {
        theta: phi_v + delta_expr,

        e_A: E_scale * Epk_expr * sym.sin(theta),
        e_B: E_scale * Epk_expr * sym.sin(theta - 2 * np.pi / 3),
        e_C: E_scale * Epk_expr * sym.sin(theta + 2 * np.pi / 3),

        Pe: (i_A * v_A + i_B * v_B + i_C * v_C),
        Qe: (1 / np.sqrt(3)) * (
            (v_A - v_B) * i_C +
            (v_B - v_C) * i_A +
            (v_C - v_A) * i_B
        ),
    }

    # ----------------------------------------------------------------------------------
    # Differential init equations
    # ----------------------------------------------------------------------------------
    #
    # If PF initialization is consistent, the currents are already those of the
    # steady-state operating point, so the current derivatives should start at zero.
    #
    templ.block.diff_init_eqs = {
        d_i_A: omega_base * (e_A - R_s * i_A - v_A) / X_s,
        d_i_B: omega_base * (e_B - R_s * i_B - v_B) / X_s,
        d_i_C: omega_base * (e_C - R_s * i_C - v_C) / X_s,
        d_theta: omega_base,
    }

    return templ

def get_generator_thevenin_rl_emt_template_with_ref(
        vf: VarFactory,
        name: str = "emt_thevenin_eq_generator_template",
) -> EmtModelTemplate:
    """
    Build a three-phase EMT Thevenin generator with optional slow sharing control.

    The model is still a balanced internal sinusoidal source behind a series
    ``R-X`` branch. The sharing extension is intentionally lightweight and does
    not try to emulate a full synchronous-machine + AVR + governor model.

    The key design decision is the following:

    * The absolute electrical angle ``theta`` keeps the nominal synchronous speed.
    * Active-power sharing acts on a bounded internal angle offset
      ``delta_share`` instead of acting directly on ``dtheta/dt``.
    * Reactive-power sharing acts on the internal emf scaling ``E_scale`` and
      includes a restoring term towards ``1.0``.

    This avoids the unbounded phase drift that appears when the active-power
    controller directly biases the absolute electrical speed.

    Inputs
    ------
    ``v_A``, ``v_B``, ``v_C``:
        Instantaneous bus terminal voltages in pu.

    States
    ------
    ``i_A``, ``i_B``, ``i_C``:
        Phase currents injected into the bus in pu.

    ``theta``:
        Absolute electrical angle of the internal balanced source in rad.

    ``delta_share``:
        Slow internal angle offset used only for active-power sharing.

    ``E_scale``:
        Slow scaling factor of the internal emf magnitude.

    ``xi_share_p``, ``xi_share_q``:
        Integral states of the active/reactive sharing controllers.

    Parameters
    ----------
    Static generator parameters:
        ``omega_base``, ``R_s``, ``X_s``

    PF-derived initialization parameters:
        ``phi_v``, ``phi``, ``Vpk``, ``Ipk``

    Optional sharing references:
        ``share_enable``, ``P_share_ref``, ``Q_share_ref``

    Event parameters:
        ``kp_share_p``, ``ki_share_p``, ``kp_share_q``, ``ki_share_q``,
        ``k_delta_share``, ``k_e_scale``

    Initialization
    --------------
    The PF initialization reconstructs the positive-sequence internal emf using:

    .. math::

        E = V + (R + jX) I

    and then initializes:

    * ``theta = phi_v + delta``
    * ``delta_share = 0``
    * ``E_scale = 1``
    * ``xi_share_p = 0``
    * ``xi_share_q = 0``

    so that the sharing controller starts exactly from the open-loop PF point.

    :param vf: EMT variable factory.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    # ------------------------------------------------------------------
    # Constants used in symbolic expressions.
    # ------------------------------------------------------------------
    c05 = vf.add_const(0.5)
    c0 = vf.add_const(0.0)
    c1 = vf.add_const(1.0)

    # ------------------------------------------------------------------
    # Inputs: terminal bus voltages in abc.
    # ------------------------------------------------------------------
    v_A = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowRefferenceType.v_A)
    v_B = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowRefferenceType.v_B)
    v_C = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowRefferenceType.v_C)
    inputs: List[Any] = list([v_A, v_B, v_C])

    # ------------------------------------------------------------------
    # States:
    # - current dynamics
    # - absolute synchronous angle
    # - bounded sharing angle offset
    # - emf scaling
    # - PI controller integral states
    # ------------------------------------------------------------------
    i_A = vf.add_var(name=f"i_A_{name}", reference=VarPowerFlowRefferenceType.i_A)
    i_B = vf.add_var(name=f"i_B_{name}", reference=VarPowerFlowRefferenceType.i_B)
    i_C = vf.add_var(name=f"i_C_{name}", reference=VarPowerFlowRefferenceType.i_C)

    theta = vf.add_var(name=f"theta_{name}")
    delta_share = vf.add_var(name=f"delta_share_{name}")
    E_scale = vf.add_var(name=f"E_scale_{name}")
    xi_share_p = vf.add_var(name=f"xi_share_p_{name}")
    xi_share_q = vf.add_var(name=f"xi_share_q_{name}")

    d_i_A = vf.add_diff_var(name=f"d_i_A_{name}", base_var=i_A)
    d_i_B = vf.add_diff_var(name=f"d_i_B_{name}", base_var=i_B)
    d_i_C = vf.add_diff_var(name=f"d_i_C_{name}", base_var=i_C)
    d_theta = vf.add_diff_var(name=f"d_theta_{name}", base_var=theta)
    d_delta_share = vf.add_diff_var(name=f"d_delta_share_{name}", base_var=delta_share)
    d_E_scale = vf.add_diff_var(name=f"d_E_scale_{name}", base_var=E_scale)
    d_xi_share_p = vf.add_diff_var(name=f"d_xi_share_p_{name}", base_var=xi_share_p)
    d_xi_share_q = vf.add_diff_var(name=f"d_xi_share_q_{name}", base_var=xi_share_q)

    # ------------------------------------------------------------------
    # Algebraic variables:
    # - internal phase emfs
    # - measured active/reactive power
    # ------------------------------------------------------------------
    e_A = vf.add_var(name=f"e_A_{name}")
    e_B = vf.add_var(name=f"e_B_{name}")
    e_C = vf.add_var(name=f"e_C_{name}")
    Pe = vf.add_var(name=f"Pe_{name}")
    Qe = vf.add_var(name=f"Qe_{name}")

    # ------------------------------------------------------------------
    # Static parameters and PF-derived initialization parameters.
    # ------------------------------------------------------------------
    omega_base = vf.add_var(name=f"omega_base_{name}")
    R_s = vf.add_var(name=f"R_s_{name}")
    X_s = vf.add_var(name=f"X_s_{name}")

    phi_v = vf.add_var(name=f"phi_v_{name}")
    phi = vf.add_var(name=f"phi_{name}")
    Vpk = vf.add_var(name=f"Vpk_{name}")
    Ipk = vf.add_var(name=f"Ipk_{name}")

    # ------------------------------------------------------------------
    # Optional sharing references and internal controller gains.
    # The references are assigned by EmtProblemDae when multiple generators
    # share the same slack bus. The gains remain purely local event params.
    # ------------------------------------------------------------------
    share_enable = vf.add_var(name=f"share_enable_{name}")
    P_share_ref = vf.add_var(name=f"P_share_ref_{name}")
    Q_share_ref = vf.add_var(name=f"Q_share_ref_{name}")

    kp_share_p = vf.add_var(name=f"kp_share_p_{name}")
    ki_share_p = vf.add_var(name=f"ki_share_p_{name}")
    kp_share_q = vf.add_var(name=f"kp_share_q_{name}")
    ki_share_q = vf.add_var(name=f"ki_share_q_{name}")
    k_delta_share = vf.add_var(name=f"k_delta_share_{name}")
    k_e_scale = vf.add_var(name=f"k_e_scale_{name}")

    # ------------------------------------------------------------------
    # PF-consistent positive-sequence internal emf.
    # This part remains identical in spirit to the original Thevenin model.
    # ------------------------------------------------------------------
    E_re = Vpk + R_s * Ipk * sym.cos(phi) - X_s * Ipk * sym.sin(phi)
    E_im = R_s * Ipk * sym.sin(phi) + X_s * Ipk * sym.cos(phi)
    delta_expr = sym.atan(E_im / E_re)
    Epk_expr = (E_re ** 2 + E_im ** 2) ** c05

    # ------------------------------------------------------------------
    # Power measurement errors used by the sharing controllers.
    # ------------------------------------------------------------------
    p_error = P_share_ref - Pe
    q_error = Q_share_ref - Qe

    # ------------------------------------------------------------------
    # Controller design:
    #
    # 1. The absolute angle keeps the synchronous speed.
    # 2. Active-power sharing acts on a bounded internal angle offset.
    # 3. Reactive-power sharing acts on the emf scale with a restoring term.
    #
    # This avoids the unbounded drift produced when the controller acts
    # directly on dtheta/dt.
    # ------------------------------------------------------------------
    theta_speed = omega_base

    delta_share_speed = share_enable * (
        kp_share_p * p_error
        + xi_share_p
        - k_delta_share * delta_share
    )

    E_scale_speed = share_enable * (
        kp_share_q * q_error
        + xi_share_q
        - k_e_scale * (E_scale - c1)
    )

    # The actual electrical source angle used by the balanced internal emf.
    theta_eff = theta + delta_share

    # ------------------------------------------------------------------
    # Build the EMT block.
    # ------------------------------------------------------------------
    state_eqs: List[Any] = list([
        omega_base * (e_A - R_s * i_A - v_A) / X_s,
        omega_base * (e_B - R_s * i_B - v_B) / X_s,
        omega_base * (e_C - R_s * i_C - v_C) / X_s,
        theta_speed,
        delta_share_speed,
        E_scale_speed,
        share_enable * ki_share_p * p_error,
        share_enable * ki_share_q * q_error,
    ])

    state_vars: List[Any] = list([
        i_A,
        i_B,
        i_C,
        theta,
        delta_share,
        E_scale,
        xi_share_p,
        xi_share_q,
    ])

    algebraic_eqs: List[Any] = list([
        e_A - E_scale * Epk_expr * sym.sin(theta_eff),
        e_B - E_scale * Epk_expr * sym.sin(theta_eff - 2.0 * np.pi / 3.0),
        e_C - E_scale * Epk_expr * sym.sin(theta_eff + 2.0 * np.pi / 3.0),
        Pe - (i_A * v_A + i_B * v_B + i_C * v_C),
        Qe - (1.0 / np.sqrt(3.0)) * (
            (v_A - v_B) * i_C +
            (v_B - v_C) * i_A +
            (v_C - v_A) * i_B
        ),
    ])

    algebraic_vars: List[Any] = list([e_A, e_B, e_C, Pe, Qe])

    templ.block = Block(
        state_eqs=state_eqs,
        state_vars=state_vars,
        algebraic_eqs=algebraic_eqs,
        algebraic_vars=algebraic_vars,
        in_vars=inputs,
        out_vars=list([i_A, i_B, i_C]),
    )

    templ.block.diff_vars = list([
        d_i_A,
        d_i_B,
        d_i_C,
        d_theta,
        d_delta_share,
        d_E_scale,
        d_xi_share_p,
        d_xi_share_q,
    ])

    # ------------------------------------------------------------------
    # External mapping:
    # keep the original EMT injection interface intact.
    # ------------------------------------------------------------------
    templ.block.external_mapping = dict({
        VarPowerFlowRefferenceType.v_N: None,
        VarPowerFlowRefferenceType.v_A: v_A,
        VarPowerFlowRefferenceType.v_B: v_B,
        VarPowerFlowRefferenceType.v_C: v_C,
        VarPowerFlowRefferenceType.P: None,
        VarPowerFlowRefferenceType.Q: None,
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
    })

    # ------------------------------------------------------------------
    # API-object mapping:
    # static generator parameters plus optional sharing references assigned
    # by EmtProblemDae.
    # ------------------------------------------------------------------
    templ.block.api_obj_mapping = dict({
        ParamPowerFlowRefferenceType.omega_base: omega_base,
        ParamPowerFlowRefferenceType.R1: R_s,
        ParamPowerFlowRefferenceType.X1: X_s,
        ParamPowerFlowRefferenceType.X0: None,
        ParamPowerFlowRefferenceType.generator_share_enable: share_enable,
        ParamPowerFlowRefferenceType.generator_share_p_ref: P_share_ref,
        ParamPowerFlowRefferenceType.generator_share_q_ref: Q_share_ref,
    })

    # ------------------------------------------------------------------
    # Event parameters:
    # PF-derived phasor quantities plus local controller gains.
    # The gains are intentionally conservative compared with the version
    # that acted directly on dtheta/dt.
    # ------------------------------------------------------------------
    templ.block.event_dict = dict({
        phi_v: vf.add_const(None),
        phi: vf.add_const(None),
        Vpk: vf.add_const(None),
        Ipk: vf.add_const(None),
        kp_share_p: vf.add_const(1.0),
        ki_share_p: vf.add_const(10.0),
        kp_share_q: vf.add_const(0.5),
        ki_share_q: vf.add_const(5.0),
        k_delta_share: vf.add_const(20.0),
        k_e_scale: vf.add_const(10.0),
    })

    # ------------------------------------------------------------------
    # Initialization equations:
    # the sharing controller starts exactly from the PF-consistent open-loop
    # operating point, so it does not create a jump at t = 0.
    # ------------------------------------------------------------------
    templ.block.init_eqs = dict({
        theta: phi_v + delta_expr,
        delta_share: c0,
        E_scale: c1,
        xi_share_p: c0,
        xi_share_q: c0,
        e_A: E_scale * Epk_expr * sym.sin(theta_eff),
        e_B: E_scale * Epk_expr * sym.sin(theta_eff - 2.0 * np.pi / 3.0),
        e_C: E_scale * Epk_expr * sym.sin(theta_eff + 2.0 * np.pi / 3.0),
        Pe: (i_A * v_A + i_B * v_B + i_C * v_C),
        Qe: (1.0 / np.sqrt(3.0)) * (
            (v_A - v_B) * i_C +
            (v_B - v_C) * i_A +
            (v_C - v_A) * i_B
        ),
    })

    # ------------------------------------------------------------------
    # Differential initialization equations:
    # these keep the standard EMT explicit-init semantics.
    # ------------------------------------------------------------------
    templ.block.diff_init_eqs = dict({
        d_i_A: omega_base * (e_A - R_s * i_A - v_A) / X_s,
        d_i_B: omega_base * (e_B - R_s * i_B - v_B) / X_s,
        d_i_C: omega_base * (e_C - R_s * i_C - v_C) / X_s,
        d_theta: theta_speed,
        d_delta_share: delta_share_speed,
        d_E_scale: E_scale_speed,
        d_xi_share_p: share_enable * ki_share_p * p_error,
        d_xi_share_q: share_enable * ki_share_q * q_error,
    })

    return templ

