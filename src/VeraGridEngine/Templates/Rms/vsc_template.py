# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np

from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import (Block, VarPowerFlowReferenceType)
from VeraGridEngine.Utils.Symbolic.block_helpers import tf_to_diffblock_with_antiwindup
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def VSCShuntBuild(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    """
     VSC shunt model
     with from side the DC bus and to side the AC bus
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.VscDevice
    inputs = [vfactory.add_var("Vm"), vfactory.add_var("Va"), vfactory.add_var("Vdc"), vfactory.add_var("Idc")]
    Vm = inputs[0]
    Va = inputs[1]
    v_dc = inputs[2]
    i_dc = inputs[3]

    # Vars:
    P_ac = vfactory.add_var('P_ac')
    Q_ac = vfactory.add_var('Q_ac')
    P_dc = vfactory.add_var('P_dc')
    alpha = vfactory.add_var('alpha')
    am = vfactory.add_var('am')
    Im = vfactory.add_var('Im')
    Ia = vfactory.add_var('Ia')

    # Parameters:
    bt = vfactory.add_var('bt')
    gt = vfactory.add_var('gt')
    event_dict = {
        bt: vfactory.add_const(0.0),
        gt: vfactory.add_const(0.1),
    }

    sqrt_38 = vfactory.add_const(np.sqrt(3 / 8))
    vsc_block = Block(
        algebraic_eqs=[
            P_ac - (gt * Vm ** 2 - sqrt_38 * am * v_dc * Vm * sym.cos(Va - alpha)
                    - sqrt_38 * bt * am * v_dc * Vm * sym.sin(Va - alpha)),
            Q_ac - (-bt * Vm ** 2 + sqrt_38 * bt * am * v_dc * Vm * sym.cos(Va - alpha)
                    - sqrt_38 * bt * am * v_dc * Vm * sym.sin(Va - alpha)),
            gt * (sqrt_38 * am * v_dc) ** 2 - sqrt_38 * am * v_dc * Vm * sym.cos(Va - alpha)
            + sqrt_38 * am * v_dc * Vm * sym.sin(Va - alpha),
            P_ac ** 2 + Q_ac ** 2 - Vm * Im,
            P_ac * sym.sin(Va - alpha) - Q_ac * sym.cos(Va - alpha),
        ],
        algebraic_vars=[P_ac, Q_ac, alpha, am, Im, Ia],
    )

    vsc_block.event_dict = event_dict
    vsc_block.in_vars = inputs
    vsc_block.out_vars = [P_ac, Q_ac, alpha, am]

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.Vmt: inputs[0],
        VarPowerFlowReferenceType.Vat: inputs[1],
        VarPowerFlowReferenceType.Pt: P_ac,
        VarPowerFlowReferenceType.Qt: Q_ac,
        VarPowerFlowReferenceType.Pf: v_dc * i_dc,
        VarPowerFlowReferenceType.Vdc: v_dc,
        VarPowerFlowReferenceType.Idc: i_dc,
    }

    vsc_block.name = name
    templ.block = vsc_block
    return templ


def VSCShuntBuild2(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    """
     VSC shunt model
     with from side the DC bus and to side the AC bus
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.VscDevice
    inputs = [vfactory.add_var("Vm_"), vfactory.add_var("Va_"), vfactory.add_var("Vdc_")]
    Vm = inputs[0]
    Va = inputs[1]
    v_dc = inputs[2]

    # Vars:
    Pt_vsc = vfactory.add_var('Pt_vsc')
    Qt_vsc = vfactory.add_var('Qt_vsc')
    Pf_vsc = vfactory.add_var('Pf_vsc')
    vsh = vfactory.add_var('vsh')
    ash = vfactory.add_var('ash')
    # Parameters:
    bt = vfactory.add_var('bt')
    gt = vfactory.add_var('gt')
    Qf = vfactory.add_var('Qf')
    event_dict = {
        Qf: vfactory.add_const(0.0),
        bt: vfactory.add_const(0.0),
        gt: vfactory.add_const(0.1),
    }

    sqrt_38 = vfactory.add_const(np.sqrt(3 / 8))
    exp1 = Qt_vsc + bt * Vm ** 2
    exp2 = Pt_vsc - gt * Vm ** 2
    vsc_block = Block(
        algebraic_eqs=[
            Pt_vsc + (-bt * vsh * Vm * sym.sin(ash - Va) + gt * Vm ** 2 - gt * vsh * Vm * sym.cos(ash - Va)),
            Qt_vsc + (bt * vsh * Vm * sym.cos(ash - Va) - bt * Vm ** 2 - gt * vsh * Vm * sym.sin(ash - Va)),
            Pf_vsc + (bt * vsh * Vm * sym.sin(ash - Va) + gt * Vm ** 2 - gt * vsh * Vm * sym.cos(ash - Va)),
        ],
        algebraic_vars=[Pt_vsc, Qt_vsc, vsh, ash, Pf_vsc],
        init_eqs={
            vsh: sym.sqrt((exp1 ** 2 + exp2 ** 2) / (gt ** 2 + bt ** 2)) / Vm,
            ash: sym.atan((-gt * exp1 - bt * exp2) / (bt * exp1 - gt * exp2)),
        }
    )

    vsc_block.event_dict = event_dict
    vsc_block.in_vars = inputs
    vsc_block.out_vars = [Pt_vsc, Qt_vsc, vsh, ash, Pf_vsc]

    vsc_block.external_mapping = {
        VarPowerFlowReferenceType.Vmt: inputs[0],
        VarPowerFlowReferenceType.Vat: inputs[1],
        VarPowerFlowReferenceType.Pt: Pt_vsc,
        VarPowerFlowReferenceType.Qt: Qt_vsc,
        VarPowerFlowReferenceType.Pf: Pf_vsc,
        VarPowerFlowReferenceType.Qf: Qf,
        VarPowerFlowReferenceType.Vdc: v_dc,
    }

    vsc_block.name = name
    templ.block = vsc_block
    return templ


def PVControlBuild2(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    templ = RmsModelTemplate()
    inputs = [vfactory.add_var("Vm_"), vfactory.add_var("Vdc_"), vfactory.add_var("vhs_"), vfactory.add_var("ahs_"),
              vfactory.add_var("Pdc_")]
    Vm = inputs[0]
    vdc = inputs[1]
    vhs = inputs[2]
    ahs = inputs[3]
    Pdc = inputs[4]

    # Vars:
    x = vfactory.add_var('x')

    # Parameters:
    Kp = vfactory.add_var('Kp')
    Ki = vfactory.add_var('Ki')
    vdc_ref = vfactory.add_var('vdc_ref')
    Temp = vfactory.add_var('Temp')
    G = vfactory.add_var('G')
    gamma_p = vfactory.add_var('gamma_p')
    Pref = vfactory.add_var('Pref')
    Gref = vfactory.add_var('Gref')
    Tref = vfactory.add_var('Tref')
    vref = vfactory.add_var('vref')
    Km = vfactory.add_var('Km')
    Ts = vfactory.add_var('Ts_controller')
    event_dict = {
        vref: vfactory.add_const(None),
        Km: vfactory.add_const(10.0),
        Ts: vfactory.add_const(0.01),
        Kp: vfactory.add_const(0.1),
        Ki: vfactory.add_const(0.1),
        Temp: vfactory.add_const(300.0),
        G: vfactory.add_const(1000.0),
        Gref: vfactory.add_const(1000.0),
        Pref: vfactory.add_const(None),
        Tref: vfactory.add_const(300.0),
        gamma_p: vfactory.add_const(-0.001),
        vdc_ref: vfactory.add_const(1.033),
    }

    Ppv = (G / vfactory.add_const(1000.0)) * (Pref * (1 + gamma_p * (Temp - Tref)))
    i_dc_ref = Ppv / vdc_ref
    init_eqs = {
        vref: inputs[0],
        Pref: inputs[4],
    }

    block_vhs_control, _ = tf_to_diffblock_with_antiwindup(
        vfactory,
        x=(Vm - vref),
        y=vhs,
        num=[Km],
        den=[vfactory.add_const(1), Ts],
        name="VSC Vhs Control",
        sat_min=vfactory.add_const(-1.0),
        sat_max=vfactory.add_const(1.0),
    )
    # Block that Controls Vdc_ref based on MPPT optimal point
    solar_block = Block(
        state_eqs=[Ki * (vdc_ref - vdc)],
        state_vars=[x],
        algebraic_eqs=[
            Kp * (vdc_ref - vdc) + x - ahs,
            i_dc_ref + vdc_ref * i_dc_ref.diff(vdc_ref),
        ],
        algebraic_vars=[vdc_ref],
        in_vars=inputs,
        init_eqs=init_eqs,
        # children = [block_vhs_control],
        event_dict=event_dict,
    )

    solar_block.name = name

    templ.block = solar_block
    templ.block.event_dict = event_dict

    return templ


def PVControlBuild(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    templ = RmsModelTemplate()
    inputs = [vfactory.add_var("Vdc_"), vfactory.add_var("ahs_")]
    Vdc = inputs[0]
    alpha = inputs[1]

    # Vars:
    x = vfactory.add_var('x')

    # Parameters:
    Kp = vfactory.add_var('Kp')
    Ki = vfactory.add_var('Ki')
    vdc_ref = vfactory.add_var('vdc_ref')
    Temp = vfactory.add_var('Temp')
    G = vfactory.add_var('G')
    gamma_p = vfactory.add_var('gamma_p')
    Pref = vfactory.add_var('Pref')
    Gref = vfactory.add_var('Gref')
    Tref = vfactory.add_var('Tref')

    event_dict = {
        vdc_ref: vfactory.add_const(1.0),
        Kp: vfactory.add_const(0.1),
        Ki: vfactory.add_const(0.1),
        Temp: vfactory.add_const(300.0),
        G: vfactory.add_const(1000.0),
        Gref: vfactory.add_const(1000.0),
        Pref: vfactory.add_const(0.1),
        Tref: vfactory.add_const(300.0),
        gamma_p: vfactory.add_const(-0.001),
    }

    Ppv = (G / vfactory.add_const(1000.0)) * (Pref * (1 + gamma_p * (Temp - Tref)))
    i_dc_ref = Ppv / vdc_ref
    init_eqs = {}
    solar_block = Block(
        state_eqs=[Ki * (vdc_ref - Vdc)],
        state_vars=[x],
        algebraic_eqs=[
            Kp * (vdc_ref - Vdc) + x - alpha,
            i_dc_ref + vdc_ref * i_dc_ref.diff(vdc_ref),
        ],
        in_vars=inputs,
        init_eqs=init_eqs,
    )

    solar_block.name = name
    templ.block = solar_block
    templ.block.event_dict = event_dict

    return templ


def PVCellBuild(vfactory: VarFactory, name: str = "") -> RmsModelTemplate:
    templ = RmsModelTemplate()
    inputs = [vfactory.add_var("Vdc_")]
    Vdc = inputs[0]

    # Vars:
    iD = vfactory.add_var('iD')
    iL = vfactory.add_var('iL')
    Idc = vfactory.add_var('Idc')
    vD = vfactory.add_var('vD')
    Pdc = vfactory.add_var('Pdc')

    # Parameters:
    Temp = vfactory.add_var('Temp')
    gamma_p = vfactory.add_var('gamma_p')
    Pref = vfactory.add_var('Pref')
    Gref = vfactory.add_var('Gref')
    Tref = vfactory.add_var('Tref')
    Rsh = vfactory.add_var('Rsh')
    Rse = vfactory.add_var('Rse')
    Temp0 = vfactory.add_var('Temp0')
    is0 = vfactory.add_var('is0')
    Sn = vfactory.add_var('Sn')
    Aa = vfactory.add_var('Aa')
    rho_e = vfactory.add_var('rho_e')
    C_temp = vfactory.add_var('C_temp')
    G = vfactory.add_var('G')
    iL0 = vfactory.add_var('iL0')

    event_dict = {
        Temp: vfactory.add_const(298.15),
        gamma_p: vfactory.add_const(-0.004),
        Pref: vfactory.add_const(0.02),
        Gref: vfactory.add_const(1000.0),
        Tref: vfactory.add_const(298.15),
        Rsh: vfactory.add_const(1000.0),
        Rse: vfactory.add_const(0.005),
        Temp0: vfactory.add_const(298.15),
        is0: vfactory.add_const(1e-10),
        Sn: vfactory.add_const(1.0),
        Aa: vfactory.add_const(1.2),
        rho_e: vfactory.add_const(1.68e-8),
        C_temp: vfactory.add_const(1000.0),
        G: vfactory.add_const(1000.0),
        iL0: vfactory.add_const(None)
    }

    qe = vfactory.add_const(1.60217662e-19)  # Electron charge (C)
    kB = vfactory.add_const(1.380649e-23)  # Boltzmann constant (J/K)
    gamma = vfactory.add_const(1.2)  # Diode ideality factor (unitless)

    def energy_band(Temp):
        # Empirical relation for silicon
        Eg0 = 1.17  # eV
        alpha = 4.73e-4  # eV/K
        beta = 636  # K
        Eg_of_Temp = Eg0 - (alpha * Temp ** 2) / (Temp + beta)
        Eg_of_Temp0 = Eg0 - (alpha * Temp0 ** 2) / (Temp0 + beta)
        return qe * Eg0 / (kB * gamma) * (Eg_of_Temp0 - Eg_of_Temp)

    v_T = kB * Temp / qe
    Is = is0 * (Temp / Temp0) ** 3 * sym.exp(energy_band(Temp))

    # TODO: Include Temperature dynamics model
    solar_block = Block(
        algebraic_eqs=[
            Idc - (iL - iD - vD / Rsh),
            Pdc - Idc * Vdc,
            vD - Vdc - Rse * Idc,
            Is * (sym.exp(vD / (gamma * v_T)) - vfactory.add_const(1)) - iD,
            iL - iL0,
        ],
        algebraic_vars=[iD, iL, Idc, vD, Pdc],
        in_vars=inputs,
        out_vars=[Pdc, Idc],
        external_mapping={
            VarPowerFlowReferenceType.P: Pdc,
            VarPowerFlowReferenceType.Idc: Idc,
            VarPowerFlowReferenceType.Vdc: Vdc,
        },
        init_eqs={
            Idc: Pdc / Vdc,
            vD: Vdc + Rse * Idc,
            iD: Is * (sym.exp(vD / (gamma * v_T)) - vfactory.add_const(1)),
            iL0: Idc - (- iD - vD / Rsh),
            iL: Idc - (- iD - vD / Rsh),
        }
    )

    solar_block.name = "PVCell" + name
    solar_block.event_dict = event_dict
    templ.block = solar_block

    return templ


def VscControlledPV(vfactory: VarFactory, name='VscControlledPV') -> RmsModelTemplate:
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice

    vsc_block = VSCShuntBuild2(vfactory).block
    pv_block = PVControlBuild2(vfactory).block
    pv_cell_block = PVCellBuild(vfactory).block

    vfactory.add_connections([pv_block.in_vars[2]], [vsc_block.out_vars[2]])
    vfactory.add_connections([pv_block.in_vars[3]], [vsc_block.out_vars[3]])

    vfactory.add_connections([pv_cell_block.in_vars[0]], [vsc_block.out_vars[0]])

    templ.block = Block(children=[pv_block, pv_cell_block])

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.Vm: vsc_block.in_vars[0],
        VarPowerFlowReferenceType.Va: vsc_block.in_vars[1],
        VarPowerFlowReferenceType.P: vsc_block.out_vars[0],
        VarPowerFlowReferenceType.Q: vsc_block.out_vars[1],
    }

    return templ
