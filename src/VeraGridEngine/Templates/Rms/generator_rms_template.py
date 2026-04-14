# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block, Var, Const, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import cos, sin, real, imag, conj, exp, log, abs, UndefinedConst



def get_generator_rms_template() -> RmsModelTemplate():
    """
    Get the RMS template of a grnerator
    :return: RmsModelTemplate
    """

    templ = RmsModelTemplate()

    Vm: Var = Var('Vm_placeholder')
    Va: Var = Var('Va_placeholder')

    P_g: Var = Var('P_g')
    Q_g: Var = Var('Q_g')

    delta = Var("delta")
    omega = Var("omega")
    psid = Var("psid")
    psiq = Var("psiq")
    i_d = Var("i_d")
    i_q = Var("i_q")
    v_d = Var("v_d")
    v_q = Var("v_q")
    te = Var("te")
    et = Var("et")
    tm = Var("tm")

    R1 = Var("R1")
    X1 = Var("X1")
    freq = Var("frequ")
    M = Var("M")
    D = Var("D")
    omega_ref = Var("omega_ref")
    Kp = Var("Kp")
    Ki = Var("Ki")

    vf = UndefinedConst()  # this will disappear when the generator and the exciter model are decoupled
    tm0 = UndefinedConst()

    templ.block = Block(
        state_vars=[delta, omega],
        state_eqs=[
            (2 * np.pi * freq) * (omega - omega_ref),
            (tm - te - D * (omega - omega_ref)) / M,
        ],
        algebraic_vars=[P_g, Q_g, v_d, v_q, i_d, i_q, psid, psiq, te,
                        tm, et],
        algebraic_eqs=[
            psid - (R1 * i_q + v_q),
            psiq + (R1 * i_d + v_d),
            0 - (psid + X1 * i_d - vf),
            0 - (psiq + X1 * i_q),
            v_d - (Vm * sin(delta - Va)),
            v_q - (Vm * cos(delta - Va)),
            te - (psid * i_q - psiq * i_d),
            P_g - (v_d * i_d + v_q * i_q),
            Q_g - (v_q * i_d - v_d * i_q),
            tm - (tm0 + Kp * (omega - omega_ref) + Ki * et),
            2 * np.pi * freq * et - delta,  #
        ],

        init_eqs={
            delta: imag(
                log((Vm * exp(1j * Va) + (R1 + 1j * X1) * (
                    conj((P_g + 1j * Q_g) / (Vm * exp(1j * Va))))) / (
                        abs(Vm * exp(1j * Va) + (R1 + 1j * X1) * (
                            conj((P_g + 1j * Q_g) / (Vm * exp(1j * Va)))))))),
            omega: omega_ref,
            v_d: real((Vm * exp(1j * Va)) * exp(-1j * (delta - np.pi / 2))),
            v_q: imag((Vm * exp(1j * Va)) * exp(-1j * (delta - np.pi / 2))),
            i_d: real(
                conj((P_g + 1j * Q_g) / (Vm * exp(1j * Va))) * exp(-1j * (delta - np.pi / 2))),
            i_q: imag(
                conj((P_g + 1j * Q_g) / (Vm * exp(1j * Va))) * exp(-1j * (delta - np.pi / 2))),
            psid: R1 * i_q + v_q,
            psiq: -R1 * i_d - v_d,
            te: psid * i_q - psiq * i_d,
            tm: te,
            et: Const(0),
        })

    templ.block.fix_vars = [tm0, vf]
    templ.block.fix_vars_eqs = {tm0.uid: tm,
                                vf.uid: psid + X1 * i_d}

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.P: P_g,
        VarPowerFlowRefferenceType.Q: Q_g
    }

    templ.block.event_dict = {R1: Const(0.0),
                              X1: Const(0.3),
                              freq: Const(60.0),
                              M: Const(4.0),
                              D: Const(1.0),
                              omega_ref: Const(1.0),
                              Kp: Const(0.0),
                              Ki: Const(0.0)}

    return templ
