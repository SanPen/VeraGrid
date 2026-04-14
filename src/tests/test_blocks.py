# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import math
import numpy as np

from VeraGridEngine.Utils.Symbolic.block import Block, Var, Const, Expr, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import cos, sin, real, imag, conj, angle, exp, log, abs, UndefinedConst

def test_block_save_to_disk():
    """
       Checks the serialization to disk and recovery from disk of several blocks.
       :return: Nothing if ok, fails if not
       """

    # build Block to test
    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    Qline_from = Var("Qline_from")
    Qline_to = Var("Qline_to")
    Pline_from = Var("Pline_from")
    Pline_to = Var("Pline_to")
    Vline_from = Var("Vline_from")
    Vline_to = Var("Vline_to")
    dline_from = Var("dline_from")
    dline_to = Var("dline_to")

    g = Const(5)
    b = Const(-12)
    bsh = Const(0.03)

    line_block = Block(
        algebraic_eqs=[
            Pline_from - ((Vline_from ** 2 * g) - g * Vline_from * Vline_to * cos(
                dline_from - dline_to) + b * Vline_from * Vline_to * cos(dline_from - dline_to + np.pi / 2)),
            Qline_from - (Vline_from ** 2 * (-bsh / 2 - b) - g * Vline_from * Vline_to * sin(
                dline_from - dline_to) + b * Vline_from * Vline_to * sin(dline_from - dline_to + np.pi / 2)),
            Pline_to - ((Vline_to ** 2 * g) - g * Vline_to * Vline_from * cos(
                dline_to - dline_from) + b * Vline_to * Vline_from * cos(dline_to - dline_from + np.pi / 2)),
            Qline_to - (Vline_to ** 2 * (-bsh / 2 - b) - g * Vline_to * Vline_from * sin(
                dline_to - dline_from) + b * Vline_to * Vline_from * sin(dline_to - dline_from + np.pi / 2)),
        ],
        algebraic_vars=[dline_from, Vline_from, dline_to, Vline_to],
    )

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------

    Ql = Var("Ql")
    Pl = Var("Pl")

    coeff_alfa = Const(1.8)
    Pl0 = Var('Pl0')
    Ql0 = Const(0.1)
    coeff_beta = Const(8.0)

    load_block = Block(
        algebraic_eqs=[
            Pl - Pl0,
            Ql - Ql0
        ],
        algebraic_vars=[Ql, Pl],
    )

    # ----------------------------------------------------------------------------------------------------------------------
    # Generator 1
    # ----------------------------------------------------------------------------------------------------------------------

    delta = Var("delta")
    omega = Var("omega")
    psid = Var("psid")
    psiq = Var("psiq")
    i_d = Var("i_d")
    i_q = Var("i_q")
    v_d = Var("v_d")
    v_q = Var("v_q")
    t_e = Var("t_e")
    p_g = Var("P_e")
    Q_g = Var("Q_e")
    Vg = Var("Vg")
    dg = Var("dg")
    tm = Var("tm")
    et = Var("et")

    pi = Const(math.pi)
    fn = Const(50)
    # tm = Const(0.1)
    M = Const(1.0)
    D = Const(100)
    ra = Const(0.3)
    xd = Const(0.86138701)
    vf = Const(1.081099313)

    Kp = Const(1.0)
    Ki = Const(10.0)
    Kw = Const(10.0)

    generator_block = Block(
        state_eqs=[
            # delta - (2 * pi * fn) * (omega - 1),
            # omega - (-tm / M + t_e / M - D / M * (omega - 1))
            (2 * pi * fn) * (omega - 1),  # dδ/dt
            (tm - t_e - D * (omega - 1)) / M,  # dω/dt
            -Kp * et - Ki * et - Kw * (omega - 1)  # det/dt
        ],
        state_vars=[delta, omega, et],
        algebraic_eqs=[
            et - (tm - t_e),
            psid - (-ra * i_q + v_q),
            psiq - (-ra * i_d + v_d),
            i_d - (psid + xd * i_d - vf),
            i_q - (psiq + xd * i_q),
            v_d - (Vg * sin(delta - dg)),
            v_q - (Vg * cos(delta - dg)),
            t_e - (psid * i_q - psiq * i_d),
            (v_d * i_d + v_q * i_q) - p_g,
            (v_q * i_d - v_d * i_q) - Q_g
        ],
        algebraic_vars=[tm, psid, psiq, i_d, i_q, v_d, v_q, t_e, p_g, Q_g],
    )

    # ----------------------------------------------------------------------------------------------------------------------
    # Generator 2
    # ----------------------------------------------------------------------------------------------------------------------

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



    block = Block(
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

    block.fix_vars = [tm0, vf]
    block.fix_vars_eqs = {tm0.uid: tm,
                          vf.uid: psid + X1 * i_d}

    block.external_mapping = {
        VarPowerFlowRefferenceType.P: P_g,
        VarPowerFlowRefferenceType.Q: Q_g
    }

    block.event_dict = {R1: Const(0.0),
                        X1: Const(0.3),
                        freq: Const(60.0),
                        M: Const(4.0),
                        D: Const(1.0),
                        omega_ref: Const(1.0),
                        Kp: Const(0.0),
                        Ki: Const(0.0)}

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------

    bus1_block = Block(
        algebraic_eqs=[
            p_g - Pline_from,
            Q_g - Qline_from,
            Vg - Vline_from,
            dg - dline_from
        ],
        algebraic_vars=[Pline_from, Qline_from, Vg, dg]
    )

    bus2_block = Block(
        algebraic_eqs=[
            Pl + Pline_to,
            Ql + Qline_to,
        ],
        algebraic_vars=[Pline_to, Qline_to]
    )

    # ----------------------------------------------------------------------------------------------------------------------
    # System
    # ----------------------------------------------------------------------------------------------------------------------

    sys = Block(
        children=[line_block, load_block, generator_block, bus1_block, bus2_block],
        in_vars=[]
    )

    blocks_to_test = [line_block, load_block, bus1_block, bus2_block, generator_block]

    for blk in blocks_to_test:

        saved_block = blk.to_dict()
        reconstructed_block = Block.parse(saved_block)

        if reconstructed_block != saved_block:
            print('block save to disk test for {} failed'.format(blk))

        assert reconstructed_block == blk

    print('test block save to disk ok')

