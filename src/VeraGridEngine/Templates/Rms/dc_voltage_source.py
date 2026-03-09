# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import (Block, VarPowerFlowRefferenceType)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory


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
            Vpv: Rpv * Idc + Vdc,
            Vpv0: Rpv * Idc + Vdc,
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
        C: vfactory.add_const(0.01),
        Rpv: vfactory.add_const(0.001),
        Vpv0: vfactory.add_const(None),
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
            Vpv: Rpv * Idc + Vdc,
            Vpv0: Rpv * Idc + Vdc,
        },
        external_mapping={
            VarPowerFlowRefferenceType.P: Pdc,
            VarPowerFlowRefferenceType.Idc: Idc,
            VarPowerFlowRefferenceType.Vdc: Vdc,
        },
    )
    templ.block = dc_block

    return templ
