# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np


def reec_d(u, Vpf, Paux, Qext, Pref):
    """

    :param u:
    :param Vpf:
    :param Paux:
    :param Qext:
    :param Pref:
    :return:
    """
    Vt = u  # Input 0
    Qext = Qext  # Input 8
    Paux = Paux  # Input 11
    Speed = 1.0  # Input 12
    Pref = Pref  # Input 13

    # Reactive Current Injection
    Vref0_sig = Vpf
    dbd2 = 0.05
    Kqv = 2.0
    Vdif = Vref0_sig - Vt
    Verr = Vdif - abs(dbd2)
    Iqinj = Verr * Kqv

    # Q-V Limitation
    o5 = Qext / Vt

    Iqcmd = Iqinj + o5

    o6 = Pref

    yi10 = Speed * o6

    Pord = yi10
    o12 = Paux + Pord
    o7 = Vt
    Ipcmd = o12 / o7

    return Iqcmd, Ipcmd


def regc_c(Iqcmd, ir, ii, ur, ui, fref, Fnom, Vt, Ipcmd, is_blocked):
    """

    :param Iqcmd:
    :param ir:
    :param ii:
    :param ur:
    :param ui:
    :param fref:
    :param Fnom:
    :param Vt:
    :param Ipcmd:
    :param is_blocked:
    :return:
    """
    iq_ref = - Iqcmd

    V_or_one = 1

    ip_or_pp = Ipcmd * V_or_one
    id_ref = ip_or_pp / V_or_one

    return iq_ref, id_ref


def genstat(ur, ui, iq_ref, id_ref, Sn):
    """

    :param ur:
    :param ui:
    :param iq_ref:
    :param id_ref:
    :param Sn:
    :return:
    """
    u1 = ur + 1j * ui

    cos_u1 = np.real(u1) / abs(u1)
    sin_u1 = np.imag(u1) / abs(u1)

    i1 = (id_ref * cos_u1 - iq_ref * sin_u1) + 1j * (id_ref * sin_u1 + iq_ref * cos_u1)

    s1 = u1 * np.conj(i1)

    Pref = np.real(s1) * Sn  # MW
    Qref = np.imag(s1) * Sn  # MVAr

    return Pref, Qref


def wecc_wt_type_4b_no_ifs(V_measured, P_measured, Q_measured, S_base_vg, S_rated_vsc, Vpf):
    """

    :param V_measured:
    :param P_measured:
    :param Q_measured:
    :param S_base_vg:
    :param S_rated_vsc:
    :param Vpf:
    :return:
    """
    Vt = np.abs(V_measured)  # Absolute value of the converter's voltage [pu]
    Vt_r = np.real(V_measured)  # Real component of the converter's voltage [pu]
    Vt_i = np.imag(V_measured)  # Imaginary component of the converter's voltage [pu]

    S_measured = (-P_measured - 1j * Q_measured) * S_base_vg / S_rated_vsc  # Converter's power [pu]

    I_measured = np.conj(S_measured / V_measured)  # Converter's current [pu]
    Ir = np.real(I_measured)  # Real component of the converter's current [pu]
    Ii = np.imag(I_measured)  # Imaginary component of the converter's current [pu]

    Iqcmd, Ipcmd, = reec_d(u=Vt,
                           Vpf=Vpf,
                           Paux=0.0,
                           Qext=0.0,
                           Pref=1.0)

    iq_ref, id_ref = regc_c(
        Iqcmd=Iqcmd,  # Current reference from REEC_D [pu]
        ir=Ir,  # Real component of the converter's current [pu]
        ii=Ii,  # Imaginary component of the converter's current [pu]
        ur=Vt_r,  # Real component of the converter's voltage [pu]
        ui=Vt_i,  # Imaginary component of the converter's voltage [pu]
        fref=1.0,  # Reference frequency [pu]
        Fnom=50.0,  # Nominal frequency [Hz]
        Vt=Vt,  # Absolute value of the converter's voltage [pu]
        Ipcmd=Ipcmd,  # Current reference from REEC_D [pu]
        is_blocked=0.0  # Converter's disconnection = 1
    )

    Pref, Qref = genstat(
        ur=Vt_r,  # Real component of the converter's voltage [pu]
        ui=Vt_i,  # Imaginary component of the converter's voltage [pu]
        iq_ref=iq_ref,  # Current reference from REGC_C [pu]
        id_ref=id_ref,  # Current reference from REGC_C [pu]
        Sn=S_rated_vsc  # Converter's nominal power [MVA]
    )

    # print("\nPref =", Pref, 'MW')
    # print("\nQref =", Qref, 'MVAr\n')

    return -Pref / S_base_vg, -Qref / S_base_vg
