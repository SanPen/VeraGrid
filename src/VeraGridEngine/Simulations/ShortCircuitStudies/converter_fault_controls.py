import numpy as np
import bisect

def vdl(x, points):
    """
    Linear approximation with clamping.
    points: list of (x_i, y_i), sorted by x_i
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    # Clamp
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]

    # Find segment
    i = bisect.bisect_right(xs, x) - 1
    x0, y0 = xs[i], ys[i]
    x1, y1 = xs[i + 1], ys[i + 1]

    # Linear interpolation
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

def current_limit_logic(Iqcmd, vdlq, vdlp, is_blocked):

    Imax = 1.3 # Maximum converter current limit in [pu]
    ipmin = 0.0

    if is_blocked > 0.0:
        blocking_factor = 0.0
    else:
        blocking_factor = 1.0

    # Reactive limits
    iqmax = min(vdlq, Imax) * blocking_factor

    if iqmax < 0.0:
        iqmin = iqmax * blocking_factor
    else:
        iqmin = -iqmax * blocking_factor

    # Reactive limits
    iq_used = min(vdlq, Imax, Iqcmd)
    ipmax = min(vdlp, np.sqrt(max(Imax ** 2 - iq_used ** 2, 0.0)))

    return iqmin, iqmax, ipmin, ipmax

def reec_d(u,
           Vpf,
           Qpf,
           Ppf,
           ):

    Vt = u  # Input 0
    Qext = Qpf  # Input 8
    Paux = 0.0  # Input 11
    Speed = 1.0  # Input 12
    Pref_WGO = Ppf  # Input 14

    # Current Blocking
    vblkl = 0.65 # Voltage below which the converter is blocked in [pu]
    vblkh = 1.2 # Voltage above which the converter is blocked in [pu]
    is_blocked = float((Vt >= vblkh) or (Vt <= vblkl))

    # Reactive Current Injection
    dbd1 = -0.05
    dbd2 = 0.05
    Kqv = 2.0
    Iqh1 = 1.1  # Maximum limit of reactive current injection in [pu]
    Iql1 = -1.1  # Minimum limit of reactive current injection in [pu]

    Vdif = Vpf - Vt

    if Vdif > abs(dbd2):
        Verr = Vdif - abs(dbd2)
    elif Vdif < -abs(dbd1):
        Verr = Vdif + abs(dbd1)
    else:
        Verr = 0.0

    Iqv = Verr * Kqv
    Iqinj = min(max(Iqv, Iql1), Iqh1)

    # Q-V Limitation
    yi = Qext
    qvmin = -1.0  # Minimum reactive power limit in [pu]
    qvmax = 1.0  # Maximum reactive power limit in [pu]
    o3 = min(max(yi, qvmin), qvmax)

    o5 = o3 / max(0.01, Vt)

    Iq_unlim = Iqinj + o5

    o6 = Pref_WGO

    yi10 = Speed * o6

    Pmin, Pmax = 0, 1 # Minimum and Maximum power reference in [pu]
    Pord = max(min(yi10, Pmax), Pmin)

    o12 = Paux + Pord

    o7 = max(Vt, 0.01)

    Ip_unlim = o12 / o7

    oarray_vdlq = [(1.10, 1.10), (1.15, 1.00), (1.30, 0.00)]
    vdlq = vdl(Vt, oarray_vdlq)

    oarray_vdlp = [(1.10, 1.10), (1.15, 1.00), (1.30, 0.00)]
    vdlp = vdl(Vt, oarray_vdlp)

    iqmin, iqmax, i_in1, i_in = current_limit_logic(Iq_unlim, vdlq, vdlp, is_blocked)

    Iqcmd = max(min(Iq_unlim, iqmax), iqmin)

    Ipcmd = max(min(Ip_unlim, i_in), i_in1)

    return Iqcmd, Ipcmd, is_blocked


def regc_c(Iqcmd, Ipcmd):

    iq_ref = - Iqcmd

    id_ref = Ipcmd

    return iq_ref, id_ref

def genstat(ur, ui, iq_ref, id_ref, Sn, is_blocked):

    if is_blocked == 1.0:

        return 0.0, 0.0

    else:

        u1 = ur + 1j * ui

        cos_u1 = np.real(u1) / abs(u1)
        sin_u1 = np.imag(u1) / abs(u1)

        i1 = (id_ref * cos_u1 - iq_ref * sin_u1) + 1j * (id_ref * sin_u1 + iq_ref * cos_u1)

        s1 = u1 * np.conj(i1)

        Pref = np.real(s1) * Sn  # MW
        Qref = np.imag(s1) * Sn  # MVAr

        return Pref, Qref

def wecc_wt_type_4b(V_measured, Vpf, St_vsc_pf, S_base_vg, S_rated_vsc):

    Vt = abs(V_measured) # Absolute value of the converter's voltage [pu]
    Vt_r = np.real(V_measured) # Real component of the converter's voltage [pu]
    Vt_i = np.imag(V_measured) # Imaginary component of the converter's voltage [pu]

    Ppf = -1 * np.real(St_vsc_pf) / S_rated_vsc
    Qpf = -1 * np.imag(St_vsc_pf) / S_rated_vsc

    Iqcmd, Ipcmd, is_blocked = reec_d(u=Vt,
                                      Vpf=Vpf,
                                      Qpf=Qpf,
                                      Ppf=Ppf)

    iq_ref, id_ref = regc_c(Iqcmd=Iqcmd, # Current reference from REEC_D [pu]
                            Ipcmd=Ipcmd, # Current reference from REEC_D [pu]
                            )

    Pref, Qref = genstat(ur=Vt_r,  # Real component of the converter's voltage [pu]
                         ui=Vt_i,  # Imaginary component of the converter's voltage [pu]
                         iq_ref=iq_ref,  # Current reference from REGC_C [pu]
                         id_ref=id_ref,  # Current reference from REGC_C [pu]
                         Sn=S_rated_vsc,  # Converter's nominal power [MVA]
                         is_blocked=is_blocked  # Converter's disconnection = 1
                         )

    return -Pref/S_base_vg, -Qref/S_base_vg