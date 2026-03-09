# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate

# --------------------------------------------------------------------------------------
# 1) ABC primitives (phase-decoupled) as EMT DAE blocks using vars + diff_vars
#    - Shunt R: algebraic i = -v/R
#    - Shunt L: state is i, with di/dt = -(1/L) * v   (injected current convention)
#    - Shunt C: state is v_cap, with dv_cap/dt driven by bus voltage (v_cap = v_bus),
#               and injected current i = -C * dv_cap/dt
# --------------------------------------------------------------------------------------

def get_shunt_r_3ph_emt_template( vf: VarFactory, name: str = "Shunt_R_3ph") -> EmtModelTemplate:
    """
    3-phase shunt resistor (wye to ground), phase-decoupled.
    Inputs:  vA, vB, vC  (instantaneous phase-to-ground voltages)
    Outputs: i_A, i_B, i_C (injected currents into the bus; negative for consumption)
    """

    templ = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    # Inputs (abc instantaneous voltages)
    v_A = vf.add_var("v_A_" + name)
    v_B = vf.add_var("v_B_" + name)
    v_C = vf.add_var("vC_" + name)
    templ.block.in_vars = [v_A, v_B, v_C]

    # Parameters
    R_A = vf.add_var("R_A_" + name)
    R_B = vf.add_var("R_B_" + name)
    R_C = vf.add_var("R_C_" + name)

    templ.block.event_dict[R_A] = vf.add_const(10.0)
    templ.block.event_dict[R_B] = vf.add_const(10.0)
    templ.block.event_dict[R_C] = vf.add_const(10.0)

    # Algebraic injected currents
    i_A = vf.add_var("iA_" + name)
    i_B = vf.add_var("iB_" + name)
    i_C = vf.add_var("iC_" + name)

    templ.block.algebraic_vars = [i_A, i_B, i_C]
    templ.block.algebraic_eqs = [
        i_A + v_A / R_A,   # i_inj = -v/R
        i_B + v_B / R_B,
        i_C + v_C / R_C,
    ]

    templ.block.external_mapping = {
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
        VarPowerFlowRefferenceType.theta: None,
    }

    templ.block.api_obj_mapping = {}
    return templ


def get_shunt_l_3ph_emt_template(vf: VarFactory, name: str = "Shunt_L_3ph") -> EmtModelTemplate:
    """
    3-phase shunt inductor (wye to ground), phase-decoupled, using a state current.

    Physics (drawn current):   v = L * d(i_draw)/dt
    Injected current:          i_inj = -i_draw  =>  d(i_inj)/dt = -(1/L) * v

    Inputs:  vA, vB, vC (instantaneous phase voltages)
    States:  iA, iB, iC (injected currents)
    """

    templ = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    v_A = vf.add_var("vA_" + name)
    v_B = vf.add_var("vB_" + name)
    v_C = vf.add_var("vC_" + name)
    templ.block.in_vars = [v_A, v_B, v_C]

    # Parameters
    L_A = vf.add_var("L_A_" + name)
    L_B = vf.add_var("L_B_" + name)
    L_C = vf.add_var("L_C_" + name)

    templ.block.event_dict[L_A] = vf.add_const(0.01)  # H
    templ.block.event_dict[L_B] = vf.add_const(0.01)
    templ.block.event_dict[L_C] = vf.add_const(0.01)

    # State vars (injected currents)
    i_A = vf.add_var("i_A_" + name)
    i_B = vf.add_var("i_B_" + name)
    i_C = vf.add_var("i_C_" + name)

    d_i_A = vf.add_diff_var(f"d_i_A_{name}", base_var=i_A)
    d_i_B = vf.add_diff_var(f"d_i_B_{name}", base_var=i_B)
    d_i_C = vf.add_diff_var(f"d_i_C_{name}", base_var=i_C)

    # You may need to rename these lists to match your Block implementation
    templ.block.state_vars = [i_A, i_B, i_C]
    templ.block.diff_vars = [d_i_A, d_i_B, d_i_C]
    templ.block.state_eqs = [ # di_inj/dt = -(1/L) v
        - v_A / L_A,   # d_i_A + v_A / L_A,
        - v_B / L_B,   # d_i_B + v_B / L_B,
        - v_C / L_C,   # d_i_C + v_C / L_C,
    ]

    templ.block.external_mapping = {
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
        VarPowerFlowRefferenceType.theta: None,
    }

    templ.block.api_obj_mapping = {}
    return templ


def get_shunt_c_3ph_emt_template(vf: VarFactory, name: str = "Shunt_C_3ph") -> EmtModelTemplate:
    """
    3-phase shunt capacitor (wye to ground), phase-decoupled, using a state voltage.

    Physics (drawn current): i_draw = C * dv/dt
    Injected current:        i_inj  = -i_draw = -C * dv/dt

    We do NOT differentiate the input voltage directly.
    Instead we introduce capacitor terminal voltages as states (vCapA/B/C) constrained to the bus:
        vCap - vBus = 0   (algebraic)
        dvCap/dt is a diff_var
        i_inj + C * dvCap/dt = 0  (algebraic)

    Inputs:  vA, vB, vC
    States:  vCapA, vCapB, vCapC
    Algebraic outputs: iA, iB, iC (injected currents)
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    v_A = vf.add_var("vA_" + name)
    v_B = vf.add_var("vB_" + name)
    v_C = vf.add_var("vC_" + name)
    templ.block.in_vars = [v_A, v_B, v_C]

    # Parameters
    C_A = vf.add_var("C_A_" + name)
    C_B = vf.add_var("C_B_" + name)
    C_C = vf.add_var("C_C_" + name)

    # Injected currents (algebraic vars)
    i_A = vf.add_var("i_A_" + name)
    i_B = vf.add_var("i_B_" + name)
    i_C = vf.add_var("i_C_" + name)

    templ.block.event_dict[C_A] = vf.add_const(10e-6)  # F
    templ.block.event_dict[C_B] = vf.add_const(10e-6)
    templ.block.event_dict[C_C] = vf.add_const(10e-6)

    # State voltages
    vCapA = vf.add_var("vCapA_" + name)
    vCapB = vf.add_var("vCapB_" + name)
    vCapC = vf.add_var("vCapC_" + name)

    dvCapA = vf.add_diff_var(f"dvCapA_{name}", base_var=vCapA)
    dvCapB = vf.add_diff_var(f"dvCapB_{name}", base_var=vCapB)
    dvCapC = vf.add_diff_var(f"dvCapC_{name}", base_var=vCapC)

    templ.block.state_vars = [vCapA, vCapB, vCapC]
    templ.block.diff_vars = [dvCapA, dvCapB, dvCapC]
    templ.block.state_eqs = [# i_inj = -C dv/dt  => i_inj + C dv/dt = 0
        - i_A / C_A,
        - i_B / C_B,
        - i_C / C_C,

    ]
    if not hasattr(templ.block, "differential_eqs") or templ.block.differential_eqs is None:
        templ.block.differential_eqs = []

    templ.block.algebraic_vars = [i_A, i_B, i_C]
    templ.block.algebraic_eqs = [
        vCapA - v_A,                 # capacitor voltage equals bus voltage
        vCapB - v_B,
        vCapC - v_C,
    ]

    templ.block.external_mapping = {
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
        VarPowerFlowRefferenceType.theta: None,
    }

    templ.block.api_obj_mapping = {}
    return templ
