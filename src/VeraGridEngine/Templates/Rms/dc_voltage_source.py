# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import (Block, VarPowerFlowRefferenceType)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic import symbolic as sym


def DCVoltageSource(vfactory: VarFactory, Vdc, name: str = "") -> RmsModelTemplate:
    """
    Builds an RMS model template for a DC voltage source with capacitive filtering.
    
    Models a DC voltage source (e.g., photovoltaic array, battery) connected through
    a DC-link capacitor and series resistance. The model captures the DC-side dynamics
    and power injection into the AC grid.
    
    The circuit consists of:
    - DC voltage source (Vpv) with internal resistance (Rpv)
    - DC-link capacitor (C) for energy storage and ripple filtering
    - DC current (Idc) and power (Pdc) output to the converter
    
    The differential-algebraic equations governing the system:
        - Algebraic: Pdc = Idc * Vdc (power balance)
        - Algebraic: Vpv = Vpv0 (source voltage)
        - Differential: C*dVdc/dt + Idc = (Vpv - Vdc)/Rpv (capacitor dynamics)
    
    Args:
        Vdc: DC voltage variable (pu)
        name (str): Name of the DC voltage source model
    
    Returns:
        RmsModelTemplate: Configured RMS model template for DC voltage source simulation
    """
    templ = RmsModelTemplate()

    # Vars:
    Idc = vfactory.add_var('Idc')
    Pdc = vfactory.add_var('Pdc')
    Vpv = vfactory.add_var('Vpv')
    dVdcdt = vfactory.add_diff_var('dVdcdt', base_var=Vdc)

    # Parameters
    C = vfactory.add_var('C')
    Rpv = vfactory.add_var('Rpv')
    Vpv0 = vfactory.add_var('Vpv0')

    event_dict = {
        C: vfactory.add_const(0.01),
        Rpv: vfactory.add_const(0.001),
        Vpv0: vfactory.add_const(None),
    }
    dc_block = Block(
        algebraic_eqs=[
            Pdc - Idc * Vdc,
            Vpv - Vpv0,
            dVdcdt * C + Idc - (Vpv - Vdc) / Rpv
        ],
        algebraic_vars=[Idc, Pdc, Vpv],
        diff_vars=[dVdcdt],
        event_dict=event_dict,
        out_vars=[Pdc, Idc],
        init_eqs={
            Idc: Pdc / Vdc,
            Vpv0: Vdc + Rpv * (Pdc / Vdc),
            Vpv: Vpv0,
        },
        external_mapping={
            VarPowerFlowRefferenceType.P: Pdc,
            VarPowerFlowRefferenceType.Idc: Idc,
            VarPowerFlowRefferenceType.Vdc: Vdc,
        },
    )
    templ.block = dc_block

    return templ

def DCCurrentSource(vfactory: VarFactory, Vdc, name: str = "") -> RmsModelTemplate:
    """
    Builds an RMS model template for a DC current source with capacitive filtering.

    Models a DC current source (e.g., fuel cell, grid-connected inverter) connected through
    a DC-link capacitor and series resistance. The model captures the DC-side dynamics
    and power injection into the AC grid.
    
    The circuit consists of:
    - DC voltage source (Vpv) with internal resistance (Rpv)
    - DC-link capacitor (C) for energy storage and ripple filtering
    - DC current (Idc) and power (Pdc) output to the converter
    
    The differential-algebraic equations governing the system:
        - Algebraic: Pdc = Idc * Vdc (power balance)
        - Algebraic: Vpv = Vpv0 (source voltage)
        - Differential: C*dVdc/dt + Idc = (Vpv - Vdc)/Rpv (capacitor dynamics)
    
    Args:
        Vdc: DC voltage variable (pu)
        name (str): Name of the DC voltage source model
    
    Returns:
        RmsModelTemplate: Configured RMS model template for DC voltage source simulation
    """
    templ = RmsModelTemplate()

    # Vars:
    Idc = vfactory.add_var('Idc')
    Idc_src = vfactory.add_var('Idc_src')
    Pdc = vfactory.add_var('Pdc')
    Idc_src0 = vfactory.add_var('Idc_src0')
    dVdcdt = vfactory.add_diff_var('dVdcdt', base_var=Vdc)

    # Parameters
    C = vfactory.add_var('C')
    Rpv = vfactory.add_var('Rpv')
    Vpv0 = vfactory.add_var('Vpv0')

    event_dict = {
        C: vfactory.add_const(0.05),
        Rpv: vfactory.add_const(0.005),
        Vpv0: vfactory.add_const(None),
        Idc_src0: vfactory.add_const(None),
    }
    dc_block = Block(
        algebraic_eqs=[
            Pdc - Idc * Vdc,
            Idc_src - Idc_src0,
            dVdcdt * C + Idc - Idc_src
        ],
        algebraic_vars=[Idc, Pdc, Idc_src],
        diff_vars=[dVdcdt],
        event_dict=event_dict,
        out_vars=[Pdc, Idc],
        init_eqs={
            Idc: Pdc / Vdc,
            Idc_src0: Pdc / Vdc,
            Idc_src: Pdc / Vdc,
            Vpv0: Vdc + Rpv * (Pdc / Vdc),
        },
        external_mapping={
            VarPowerFlowRefferenceType.P: Pdc,
            VarPowerFlowRefferenceType.Idc: Idc,
            VarPowerFlowRefferenceType.Vdc: Vdc,
        },
    )
    templ.block = dc_block

    return templ


def DCPowerLimitedSource(vfactory: VarFactory, Vdc, name: str = "") -> RmsModelTemplate:
    """
    RMS DC source driven by a power reference with saturation.

    This model injects a commanded DC power into the DC-link while limiting
    the requested power with hard saturation:

        P_cmd = hard_sat(Pdc_ref0, -Pmax, Pmax)
        Idc_src = P_cmd / (Vdc + eps_v)

    DC-link dynamics are then:

        C * dVdc/dt + Idc - Idc_src = 0

    where Pdc = Idc * Vdc is the converter-side DC power variable.
    """
    templ = RmsModelTemplate()

    Idc = vfactory.add_var('Idc')
    Idc_src = vfactory.add_var('Idc_src')
    Pdc = vfactory.add_var('Pdc')
    dVdcdt = vfactory.add_diff_var('dVdcdt', base_var=Vdc)

    C = vfactory.add_var('C')
    Pdc_ref0 = vfactory.add_var('Pdc_ref0')
    Pmax = vfactory.add_var('Pmax')
    eps_v = vfactory.add_var('eps_v')

    p_cmd = sym.hard_sat(Pdc_ref0, -Pmax, Pmax)

    event_dict = {
        C: vfactory.add_const(0.05),
        Pdc_ref0: vfactory.add_const(None),
        Pmax: vfactory.add_const(1.0),
        eps_v: vfactory.add_const(1e-6),
    }

    dc_block = Block(
        algebraic_eqs=[
            Pdc - Idc * Vdc,
            Idc_src - p_cmd / (Vdc + eps_v),
            dVdcdt * C + Idc - Idc_src,
        ],
        algebraic_vars=[Idc, Pdc, Idc_src],
        diff_vars=[dVdcdt],
        event_dict=event_dict,
        out_vars=[Pdc, Idc],
        init_eqs={
            Idc: Pdc / (Vdc + eps_v),
            Idc_src: Pdc / (Vdc + eps_v),
            Pdc_ref0: Pdc,
        },
        external_mapping={
            VarPowerFlowRefferenceType.P: Pdc,
            VarPowerFlowRefferenceType.Idc: Idc,
            VarPowerFlowRefferenceType.Vdc: Vdc,
        },
    )

    templ.block = dc_block
    return templ


def DCPVSourceAveraged(vfactory: VarFactory, Vdc, name: str = "") -> RmsModelTemplate:
    """
    Averaged PV source with MPPT-like voltage reference and DC-link capacitor.

    Model structure:
    - Irradiance/temperature dependent available PV current (Ipv_av)
    - MPPT voltage reference set to estimated Vmp
    - Averaged boost relation to inject DC current into the link
    - DC-link capacitor dynamics: Cdc * dVdc/dt + Idc - Idc_src = 0
    """
    templ = RmsModelTemplate()

    # Variables
    Idc = vfactory.add_var('Idc')
    Idc_src = vfactory.add_var('Idc_src')
    Pdc = vfactory.add_var('Pdc')
    Ipv_av = vfactory.add_var('Ipv_av')
    Vmp_est = vfactory.add_var('Vmp_est')
    Vpv_ref = vfactory.add_var('Vpv_ref')
    duty = vfactory.add_var('duty')
    dVdcdt = vfactory.add_diff_var('dVdcdt', base_var=Vdc)

    # Parameters
    Cdc = vfactory.add_var('Cdc')
    eta_boost = vfactory.add_var('eta_boost')
    Isc_stc = vfactory.add_var('Isc_stc')
    Vmp_stc = vfactory.add_var('Vmp_stc')
    G = vfactory.add_var('G')
    T = vfactory.add_var('T')
    G_stc = vfactory.add_var('G_stc')
    T_stc = vfactory.add_var('T_stc')
    alpha_isc = vfactory.add_var('alpha_isc')
    beta_vmp = vfactory.add_var('beta_vmp')
    duty_min = vfactory.add_var('duty_min')
    duty_max = vfactory.add_var('duty_max')
    eps_v = vfactory.add_var('eps_v')

    event_dict = {
        Cdc: vfactory.add_const(0.01),
        eta_boost: vfactory.add_const(1.0),
        Isc_stc: vfactory.add_const(1.0),
        Vmp_stc: vfactory.add_const(0.01),
        G: vfactory.add_const(1000.0),
        T: vfactory.add_const(25.0),
        G_stc: vfactory.add_const(1000.0),
        T_stc: vfactory.add_const(25.0),
        alpha_isc: vfactory.add_const(0.0005),
        beta_vmp: vfactory.add_const(-0.0025),
        duty_min: vfactory.add_const(0.0),
        duty_max: vfactory.add_const(0.999),
        eps_v: vfactory.add_const(0.0),
    }

    duty_unsat = 1.0 - Vpv_ref / (Vdc + eps_v)

    dc_block = Block(
        algebraic_eqs=[
            Pdc - Idc * Vdc,
            Ipv_av - Isc_stc * (G / G_stc) * (1.0 + alpha_isc * (T - T_stc)),
            Vmp_est - Vmp_stc * (1.0 + beta_vmp * (T - T_stc)),
            Vpv_ref - Vmp_est,
            duty - duty_unsat,
            Idc_src - eta_boost * (1.0 - duty) * Ipv_av,
            dVdcdt * Cdc + Idc - Idc_src,
        ],
        algebraic_vars=[Idc, Pdc, Ipv_av, Vmp_est, Vpv_ref, duty, Idc_src],
        diff_vars=[dVdcdt],
        event_dict=event_dict,
        out_vars=[Pdc, Idc],
        init_eqs={
            Idc: Pdc / Vdc,
            Idc_src: Pdc / Vdc,
            Ipv_av: Isc_stc * (G / G_stc) * (1.0 + alpha_isc * (T - T_stc)),
            Vmp_est: Vmp_stc * (1.0 + beta_vmp * (T - T_stc)),
            Vpv_ref: Vmp_est,
            duty: 1.0 - Vpv_ref / (Vdc + eps_v),
        },
        external_mapping={
            VarPowerFlowRefferenceType.P: Pdc,
            VarPowerFlowRefferenceType.Idc: Idc,
            VarPowerFlowRefferenceType.Vdc: Vdc,
        },
    )
    templ.block = dc_block

    return templ
