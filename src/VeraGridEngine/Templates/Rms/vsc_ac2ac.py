# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np

from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def VscAc2acModel(vfactory: VarFactory, name: str = "VscAc2acModel") -> RmsModelTemplate:
    """
    VSC AC-to-DC Converter Model based on equations (18.9), (18.10), and (18.11)
    
    :param vfactory: Variable factory for creating symbolic variables
    :param name: Name of the model
    :return: RmsModelTemplate containing the VSC AC2AC model
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.VscDevice
    
    
    # Inputs from connected buses (external connections)
    vac = vfactory.add_var("vac_")    # AC voltage magnitude
    theta_ac = vfactory.add_var("theta_ac_")  # AC voltage angle
    vdc = vfactory.add_var("vdc_")    # DC voltage
    inputs = [vac, theta_ac, vdc]
    templ.block.in_vars = inputs

    # Algebraic variables to solve for
    pac = vfactory.add_var('pac')     # Active power on AC side
    qac = vfactory.add_var('qac')     # Reactive power on AC side
    alpha = vfactory.add_var('alpha') # Firing angle
    am = vfactory.add_var('am')       # Modulation index
    pdc = vfactory.add_var('pdc')       # Modulation index
    iac = vfactory.add_var('iac')     # AC current magnitude
    phi_ac = vfactory.add_var('phi_ac')  # AC current angle
    
    # Transformer parameters
    rT = vfactory.add_var('rT')       # Transformer resistance
    xT = vfactory.add_var('xT')       # Transformer reactance
    
    # Constants
    sqrt_38 = vfactory.add_const(np.sqrt(3.0 / 8.0))
    
    # Parameters
    event_dict = {
        rT: vfactory.add_const(0.01),     # Transformer resistance (pu)
        xT: vfactory.add_const(0.1),      # Transformer reactance (pu)
    }
    
    # Intermediate expressions for transformer admittance: gT + jbT = 1/(rT + jxT)
    gt_expr = rT / (rT**2 + xT**2)
    bt_expr = -xT / (rT**2 + xT**2)
    
    # Common terms
    am_vdc = am * vdc
    sqrt_term = sqrt_38 * am_vdc
    # From (18.9a) - pac equation
    eq1 = pac - (gt_expr * vac**2 - sqrt_term * vac * gt_expr * sym.cos(theta_ac - alpha) 
                 - sqrt_term * vac * bt_expr * sym.sin(theta_ac - alpha))
    eq2 = qac - (-bt_expr * vac**2 + sqrt_term * vac * bt_expr * sym.cos(theta_ac - alpha) 
                 - sqrt_term * vac * gt_expr * sym.sin(theta_ac - alpha))
    eq3 = gt_expr * sqrt_term**2 - sqrt_term * vac * gt_expr * sym.cos(theta_ac - alpha) \
          + sqrt_term * vac * bt_expr * sym.sin(theta_ac - alpha)
    eq4 = pdc - ( gt_expr*sqrt_term**2 - sqrt_term*vac*gt_expr*sym.cos(theta_ac - alpha) 
                 + sqrt_term*vdc*bt_expr*sym.sin(theta_ac - alpha))
    #AC current
    #eq4 = pac**2 + qac**2 - vac * iac
    #eq5 = pac * sym.sin(theta_ac - phi_ac) - qac * sym.cos(theta_ac - phi_ac)
    
    vsc_block = Block(
        algebraic_eqs=[eq1, eq2, eq3, eq4],
        algebraic_vars=[pac, qac, alpha, am, pdc],
    )
    
    vsc_block.event_dict = event_dict
    vsc_block.in_vars = [vac, theta_ac, vdc]
    vsc_block.out_vars = [pac, qac, alpha, am, iac, phi_ac]
    
    # External mapping for power flow integration
    vsc_block.external_mapping = {
        VarPowerFlowRefferenceType.Pt: pac,
        VarPowerFlowRefferenceType.Qt: qac,
        VarPowerFlowRefferenceType.Pf: pdc,
        VarPowerFlowRefferenceType.Vdc: vdc,
    }
    
    vsc_block.name = name
    templ.block = vsc_block
    
    return templ
