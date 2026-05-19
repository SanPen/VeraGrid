# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import cos, sin, exp, imag, log, conj, real, abs


def get_genrow_rms_template(vfactory: VarFactory, name="Genrow rms template") -> RmsModelTemplate:
    """
    Get the RMS template model of the Genrow
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate(name=name)
    templ.tpe = DeviceType.GeneratorDevice

    inputs = [vfactory.add_var("Vm_" + name, reference=VarPowerFlowRefferenceType.Vm),
              vfactory.add_var("Va_" + name, reference=VarPowerFlowRefferenceType.Va)]

    P_g = vfactory.add_var('P_g')
    Q_g = vfactory.add_var('Q_g')

    delta = vfactory.add_var("delta")
    omega = vfactory.add_var("omega")
    psid = vfactory.add_var("psid")
    psiq = vfactory.add_var("psiq")
    i_d = vfactory.add_var("i_d")
    i_q = vfactory.add_var("i_q")
    v_d = vfactory.add_var("v_d")
    v_q = vfactory.add_var("v_q")
    te = vfactory.add_var("te")
    et = vfactory.add_var("et")
    tm = vfactory.add_var("tm")

    # Parameters
    R1 = vfactory.add_var("R1")
    X1 = vfactory.add_var("X1")
    freq = vfactory.add_var("frequ")
    M = vfactory.add_var("M")
    D = vfactory.add_var("D")
    omega_ref = vfactory.add_var("omega_ref")
    Kp = vfactory.add_var("Kp")
    Ki = vfactory.add_var("Ki")

    vf = vfactory.add_var("vf")
    tm0 = vfactory.add_var("tm0")

    templ.block.event_dict[R1] = vfactory.add_const(0.3)
    templ.block.event_dict[X1] = vfactory.add_const(0.86138701)
    templ.block.event_dict[freq] = vfactory.add_const(50.0)
    templ.block.event_dict[M] = vfactory.add_const(4.0)
    templ.block.event_dict[D] = vfactory.add_const(1.0)
    templ.block.event_dict[omega_ref] = vfactory.add_const(1.0)
    templ.block.event_dict[Kp] = vfactory.add_const(0.0)
    templ.block.event_dict[Ki] = vfactory.add_const(0.0)
    templ.block.event_dict[vf] = psid + X1 * i_d
    templ.block.event_dict[tm0] = tm

    templ.block.algebraic_vars = [P_g, Q_g, v_d, v_q, i_d, i_q, psid, psiq, te, tm, et]

    templ.block.algebraic_eqs = [
        psid - (R1 * i_q + v_q),
        psiq + (R1 * i_d + v_d),
        0 - (psid + X1 * i_d - vf),
        0 - (psiq + X1 * i_q),
        v_d - (inputs[0] * sin(delta - inputs[1])),
        v_q - (inputs[0] * cos(delta - inputs[1])),
        te - (psid * i_q - psiq * i_d),
        P_g - (v_d * i_d + v_q * i_q),
        Q_g - (v_q * i_d - v_d * i_q),
        tm - (tm0 + Kp * (omega - omega_ref) + Ki * et),
        2 * np.pi * freq * et - delta,
    ]

    templ.block.state_vars = [delta, omega]
    templ.block.state_eqs = [
        (2 * np.pi * freq) * (omega - omega_ref),
        (tm - te - D * (omega - omega_ref)) / M,
    ]

    templ.block.init_eqs = {
        delta: imag(
            log((inputs[0] * exp(1j * inputs[1]) + (R1 + 1j * X1) * (
                conj((P_g + 1j * Q_g) / (inputs[0] * exp(1j * inputs[1]))))) / (
                    abs(inputs[0] * exp(1j * inputs[1]) + (R1 + 1j * X1) * (
                        conj((P_g + 1j * Q_g) / (inputs[0] * exp(1j * inputs[1])))))))),
        omega: omega_ref,
        v_d: real((inputs[0] * exp(1j * inputs[1])) * exp(-1j * (delta - np.pi / 2))),
        v_q: imag((inputs[0] * exp(1j * inputs[1])) * exp(-1j * (delta - np.pi / 2))),
        i_d: real(
            conj((P_g + 1j * Q_g) / (inputs[0] * exp(1j * inputs[1]))) * exp(-1j * (delta - np.pi / 2))),
        i_q: imag(
            conj((P_g + 1j * Q_g) / (inputs[0] * exp(1j * inputs[1]))) * exp(-1j * (delta - np.pi / 2))),
        psid: R1 * i_q + v_q,
        psiq: -R1 * i_d - v_d,
        te: psid * i_q - psiq * i_d,
        tm: te,
        et: vfactory.add_const(0),
        tm0: tm,
        vf: psid + X1 * i_d
    }

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.Vm: inputs[0],
        VarPowerFlowRefferenceType.Va: inputs[1],
        VarPowerFlowRefferenceType.P: P_g,
        VarPowerFlowRefferenceType.Q: Q_g
    }

    templ.block.api_obj_mapping = {
        # Electrical parameters
        ParamPowerFlowRefferenceType.R1: R1,
        ParamPowerFlowRefferenceType.X1: X1,
        ParamPowerFlowRefferenceType.freq: freq,

        # Mechanical parameters
        ParamPowerFlowRefferenceType.M: M,
        ParamPowerFlowRefferenceType.D: D,

        # Control parameters
        ParamPowerFlowRefferenceType.omega_ref: omega_ref,
        ParamPowerFlowRefferenceType.Kp: Kp,
        ParamPowerFlowRefferenceType.Ki: Ki,

        # Inputs / initial conditions
        ParamPowerFlowRefferenceType.vf: vf,
        ParamPowerFlowRefferenceType.tm0: tm0,
    }

    templ.block.in_vars = inputs
    templ.block.out_vars = [P_g, Q_g]

    return templ
