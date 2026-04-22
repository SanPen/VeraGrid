# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import math

from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType, ParamPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import (Block, Var)
from VeraGridEngine.Templates.templates_common_functions import tf_to_block
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import ConverterControlType


def inverse_park_transform_block(vfactory: VarFactory,
                                 v_dq: list[Var],
                                 theta: Var,
                                 aux_vars = None,
                                 multilinear: bool = False,
                                 name:str =''):
    """
    Create a symbolic inverse Park transform (dq → abc) block for voltages.

    v_dq = [v_d_c, v_q_c]
    theta : grid angle (from PLL)
    multilinear : if True, use u_cos/u_sin auxiliary variables (for multilinearization)
    """

    v_d_c, v_q_c = v_dq

    # abc variables
    va_c = Var(name[0]+'a_'+name[-1])
    vb_c = Var(name[0]+'b_'+name[-1])
    vc_c = Var(name[0]+'c_'+name[-1])

    sqrt3 = vfactory.add_const(np.sqrt(3))
    reformulated_vars = []
    if not multilinear:
        # Non-multilinear form (explicit cos/sin)
        algebraic_eqs = [
            va_c - (v_d_c * sym.cos(theta) + v_q_c * sym.sin(theta)),

            vb_c - ((-vfactory.add_const(0.5) * v_d_c - (sqrt3 / vfactory.add_const(2)) * v_q_c) * sym.cos(theta)
                    + ((sqrt3 / vfactory.add_const(2)) * v_d_c - vfactory.add_const(0.5) * v_q_c) * sym.sin(theta)),

            vc_c - ((-vfactory.add_const(0.5) * v_d_c + (sqrt3 / vfactory.add_const(2)) * v_q_c) * sym.cos(theta)
                    + ((-sqrt3 / vfactory.add_const(2)) * v_d_c - vfactory.add_const(0.5) * v_q_c) * sym.sin(theta)),
        ]
        algebraic_vars = [va_c, vb_c, vc_c]
        trig_block = Block()
        aux_vars = None

    inv_park_block = Block(
        algebraic_eqs=algebraic_eqs,
        algebraic_vars=algebraic_vars,
        reformulated_vars = reformulated_vars
    )
    inv_park_block.add(trig_block)

    return inv_park_block, (va_c, vb_c, vc_c), aux_vars

def park_transform_block(vfactory: VarFactory, v_abc: list[Var], theta: Var, multilinear:bool = False, aux_vars = None, name:str = ''):
    """
    Create a symbolic Park transform (abc → dq) block for voltages and currents.

    i_abc = [i_a, i_b, i_c]
    v_abc = [v_a, v_b, v_c]
    theta : grid angle (from PLL)
    """

    v_a, v_b, v_c = v_abc

    # dq variables
    x_d = Var(name + '_d')
    x_q = Var(name + '_q')

    if not multilinear:
        algebraic_eqs = [
            # dq voltages
            x_d - (vfactory.add_const(1/3) * (
                (vfactory.add_const(2) * sym.cos(theta) * v_a)
                + (-sym.cos(theta) - vfactory.add_const(np.sqrt(3)) * sym.sin(theta)) * v_b
                + (-sym.cos(theta) + vfactory.add_const(np.sqrt(3)) * sym.sin(theta)) * v_c
            )),

            x_q - (vfactory.add_const(1/3) * (
                (vfactory.add_const(2) * sym.sin(theta) * v_a)
                + (-sym.sin(theta) + vfactory.add_const(np.sqrt(3)) * sym.cos(theta)) * v_b
                + (-sym.sin(theta) - vfactory.add_const(np.sqrt(3)) * sym.cos(theta)) * v_c
            )),
        ]
        algebraic_vars = [x_d, x_q]
        trig_block = Block()
        aux_vars = None


    park_block = Block(
        algebraic_eqs=algebraic_eqs,
        algebraic_vars=algebraic_vars
    )
    park_block.add(trig_block)

    return park_block, (x_d, x_q), aux_vars

def pll_transform_rms(vfactory: VarFactory, Vm, Va, name:str = ''):
    suffix = f"_{name}" if name else ""

    # Variables
    theta = vfactory.add_var(f'theta{suffix}')
    vd = vfactory.add_var(f'vd{suffix}')
    vq = vfactory.add_var(f'vq{suffix}')

    # Parameters
    Kp_pll = vfactory.add_var(f'Kp_pll{suffix}')
    Ki_pll = vfactory.add_var(f'Ki_pll{suffix}')
    fn = vfactory.add_var(f'fn{suffix}')

    event_dict = {
        fn: vfactory.add_const(50),
        Kp_pll: vfactory.add_const(0.001),
        Ki_pll: vfactory.add_const(0.1),
    }
    PI_block, omega = tf_to_block(vfactory,
        num=[Ki_pll, Kp_pll],
        den=[0, 1],
        x= (Vm*sym.sin(Va - theta)),
        name='PLL_integrator'
    )

    res_block = Block(
        state_eqs=[2*math.pi*fn*(omega-1)],
        state_vars=[theta],
        algebraic_eqs= [
            vd - Vm*sym.sin(Va - theta),
            vq - Vm*sym.cos(Va - theta),
        ],
        algebraic_vars = [vd,vq],
        event_dict = event_dict,
        init_eqs={
            theta: Va,
            vd: Vm * sym.sin(Va - theta),
            vq: Vm * sym.cos(Va - theta),
        },
        children = [PI_block]
    )

    outputs = [vd, vq, theta, omega]
    return res_block, outputs


def pll_transform(vfactory: VarFactory, v_abc, multilinear:bool = False, name:str = ''):
    theta = Var('theta')
    omega = Var('omega')
    omega_nom = vfactory.add_const(2*math.pi*50)
    Kp_pll = vfactory.add_const(0.001)      # proportional gain
    Ki_pll = vfactory.add_const(0.1)      # integral gain

    park_block, v_dq, aux_vars = park_transform_block(vfactory, v_abc, theta, multilinear=multilinear, name = name) 
    v_d, v_q = v_dq
    res_block = Block()

    pi_block, _ = tf_to_block(vfactory,
        num=[Ki_pll, Kp_pll],
        den=[0, 1],
        x= v_d,
        y = omega,
        name='PLL_pi'
    )
    integrator, _ = tf_to_block(vfactory,
        num=[1],
        den=[0, 1],
        x= (omega),
        y = theta,
        name='PLL_integrator'
    )

    res_block.add(pi_block)
    res_block.add(integrator)
    res_block.add(park_block)
    return res_block, v_dq, omega, theta, aux_vars


def build_gfl_converter_model(vfactory: VarFactory, inputs, 
                              control1: ConverterControlType = ConverterControlType.Pac, 
                              control2: ConverterControlType = ConverterControlType.Qac,
                              multilinear:bool = False):
    """
    Build power control loop model for Grid Following Converter.
    Supports multiple control modes via ConverterControlType.

    Args:
        inputs: [Vm, Va, Vdc] - AC voltage mag/angle, DC voltage
        control1: First control mode (typically active power or DC voltage related)
        control2: Second control mode (typically reactive power or AC voltage related)
        multilinear: Use multilinearization for Park transforms

    Returns:
        gfl_block: The complete converter block
        i_d, i_q: Current references
        P, Q: Active and reactive power measurements
    """
    Vm     = inputs[0]  
    Va     = inputs[1]  
    v_dc   = inputs[2]  # DC voltage for DC voltage control mode
    Pt_vsc = inputs[3]  # DC voltage for DC voltage control mode
    Qt_vsc = inputs[4]  # DC voltage for DC voltage control mode

    algebraic_eqs = []
    algebraic_vars = []
    gfl_block = Block()
    control_blocks = []
    
    # ==============================
    # Inputs and variables
    # ==============================

    pll_block, outputs = pll_transform_rms(vfactory, Vm, Va, name = 'vg')
    v_d_g = outputs[0]
    v_q_g = outputs[1]
    theta = outputs[2]
    omega = outputs[3]

    # Parameters
    Kp_icl = vfactory.add_var('Kp_icl')     # proportional gain for inner current loop
    Ki_icl = vfactory.add_var('Ki_icl')     # integral gain for inner current loop
    Kp_pol = vfactory.add_var('Kp_pol')     # proportional gain for outer power loop
    Ki_pol = vfactory.add_var('Ki_pol')     # integral gain for outer power loop
    Kp_vdc = vfactory.add_var('Kp_vdc')     # proportional gain for DC voltage control
    Ki_vdc = vfactory.add_var('Ki_vdc')     # integral gain for DC voltage control
    Kp_vac = vfactory.add_var('Kp_vac')     # proportional gain for AC voltage control
    Ki_vac = vfactory.add_var('Ki_vac')     # integral gain for AC voltage control
    R = vfactory.add_var('R') 
    L = vfactory.add_var('L') 

    # VARS
    i_d = vfactory.add_var('i_d')
    i_q = vfactory.add_var('i_q')
    i_d_ref = vfactory.add_var('i_d_ref')
    i_q_ref = vfactory.add_var('i_q_ref')
    
    # POWER LOOP 
    P = vfactory.add_var('P')
    Q = vfactory.add_var('Q') 
    P_ref = vfactory.add_var('P_ref') 
    Q_ref = vfactory.add_var('Q_ref') 
    
    # Voltage references for control modes
    Vdc_ref = vfactory.add_var('Vdc_ref')
    Vm_ac_ref = vfactory.add_var('Vm_ac_ref')
    
    v_d_c = vfactory.add_var('v_d_c')
    v_q_c = vfactory.add_var('v_q_c')

    event_dict = {
        Kp_icl: vfactory.add_const(0.05),
        Ki_icl: vfactory.add_const(1.0),
        Kp_pol: vfactory.add_const(0.05),
        Ki_pol: vfactory.add_const(1.0),
        Kp_vdc: vfactory.add_const(0.01),
        Ki_vdc: vfactory.add_const(0.1),
        Kp_vac: vfactory.add_const(0.1),
        Ki_vac: vfactory.add_const(1.0),
        R: vfactory.add_const(0.01),
        L: vfactory.add_const(0.05),
        P_ref: vfactory.add_const(None),
        Q_ref: vfactory.add_const(None),
        Vdc_ref: vfactory.add_const(None),
        Vm_ac_ref: vfactory.add_const(None),
    }

    # P and Q at the point of common coupling
    algebraic_eqs.append(P - (v_q_g * i_q + v_d_g * i_d))
    algebraic_eqs.append(Q - (v_q_g * i_d - v_d_g * i_q))
    algebraic_vars.append(P)
    algebraic_vars.append(Q)

    # ==============================
    # CONTROL 1: Active Power Axis (i_q_ref)
    # ==============================
    # Control1 maps to i_q_ref (q-axis current controls active power)
    
    if control1 == ConverterControlType.Pac:
        # Active power control at AC side
        control_block_1, _ = tf_to_block(vfactory,
            num=[Ki_pol, Kp_pol],
            den=[0, 1],
            x= P_ref - P,
            y = i_q_ref,
            name='Pac_ctrl'
        )
        control_blocks.append(control_block_1)
        
    elif control1 == ConverterControlType.Pdc:
        # Active power control at DC side (Pdc ~ Pac in steady state)
        # For simplicity, we control Pac which is approximately Pdc
        control_block_1, _ = tf_to_block(vfactory,
            num=[Ki_pol, Kp_pol],
            den=[0, 1],
            x= P_ref - P,  # P_ref represents desired Pdc
            y = i_q_ref,
            name='Pdc_ctrl'
        )
        control_blocks.append(control_block_1)
        
    elif control1 == ConverterControlType.Vm_dc:
        # DC voltage control - regulates v_dc to Vdc_ref
        # With current sign convention, more negative i_q_ref increases
        # power transfer from DC to AC, reducing v_dc.
        control_block_1, _ = tf_to_block(vfactory,
            num=[Ki_vdc, Kp_vdc],
            den=[0, 1],
            x= (v_dc - Vdc_ref),
            y = i_q_ref,
            name='Vdc_ctrl'
        )
        control_blocks.append(control_block_1)
    else:
        raise ValueError(f"Control1 type {control1} not supported for GFL converter. "
                        f"Supported: Pac, Pdc, Vm_dc")

    # ==============================
    # CONTROL 2: Reactive Power Axis (i_d_ref)
    # ==============================
    # Control2 maps to i_d_ref (d-axis current controls reactive power)
    
    if control2 == ConverterControlType.Qac:
        # Reactive power control
        control_block_2, _ = tf_to_block(vfactory,
            num=[Ki_pol, Kp_pol],
            den=[0, 1],
            x= Q_ref - Q,
            y = i_d_ref,
            name='Qac_ctrl'
        )
        control_blocks.append(control_block_2)
        
    elif control2 == ConverterControlType.Vm_ac:
        # AC voltage magnitude control
        # Use v_q_g as the measured voltage magnitude in dq frame (vd ~ 0)
        control_block_2, _ = tf_to_block(vfactory,
            num=[Ki_vac, Kp_vac],
            den=[0, 1],
            x= Vm_ac_ref - v_q_g,  # v_q_g is approximately Vm in dq frame
            y = i_d_ref,
            name='Vac_ctrl'
        )
        control_blocks.append(control_block_2)
    else:
        raise ValueError(f"Control2 type {control2} not supported for GFL converter. "
                        f"Supported: Qac, Vm_ac")

    # Physical Current Limits, TODO add AntiWindup
    I_max = vfactory.add_const(1.2)
    operation = 'normal'
    if operation == 'normal':
        id_max = sym.sqrt(sym.max(I_max**2 - sym.max(i_q, i_q_ref)**2, vfactory.add_const(1e-5)))     
        i_d_ref_sat = sym.hard_sat(i_d_ref, -id_max, id_max)
        i_q_ref_sat = sym.hard_sat(i_q_ref, -I_max, I_max)

    i_d_ref_sat_var = vfactory.add_var('i_d_ref_sat')
    i_q_ref_sat_var = vfactory.add_var('i_q_ref_sat')
    algebraic_eqs.append(i_d_ref_sat_var - i_d_ref_sat)
    algebraic_eqs.append(i_q_ref_sat_var - i_q_ref_sat)
    algebraic_vars.extend([i_d_ref_sat_var, i_q_ref_sat_var])

    # Voltage Control Loop (Inner Current Loop)
    control_block_iq , vq_hat = tf_to_block(vfactory,
        num=[Ki_icl, Kp_icl],
        den=[0, 1],
        x= i_q - i_q_ref_sat,
        name='vq_hat'
    )
    control_block_id , vd_hat = tf_to_block(vfactory,
        num=[Ki_icl, Kp_icl],
        den=[0, 1],
        x= i_d - i_d_ref_sat,
        name='vd_hat'
    )

    # EMT block (differential equations for currents)
    dt_id = vfactory.add_diff_var('dt_id', base_var= i_d)
    dt_iq = vfactory.add_diff_var('dt_iq', base_var= i_q)
    EMT_block=Block(
        algebraic_eqs = [
            v_d_c - v_d_g + ( R*i_d + L*dt_id - omega*L*i_q),
            v_q_c - v_q_g + (-R*i_q + L*dt_iq - omega*L*i_d),
        ],
        diff_vars= [dt_id, dt_iq]
    )

    algebraic_eqs.append(v_d_c - (vd_hat + v_d_g - L*(omega)*i_q))
    algebraic_eqs.append(v_q_c - (vq_hat + v_q_g + L*(omega)*i_d))
    algebraic_vars.extend([v_q_c, v_d_c, i_d, i_q])

    # Build initialization equations based on control modes
    # P and Q are initialized from power flow results via external mapping
    init_eqs = {
        P: -Pt_vsc,
        Q: -Qt_vsc,
        theta: Va,
        omega: vfactory.add_const(1),
        v_d_g: vfactory.add_const(0),
        v_q_g: Vm,
        i_q: P / v_q_g,
        i_d: Q / v_q_g,
        i_q_ref: i_q,
        i_d_ref: i_d,
        i_d_ref_sat_var: i_d_ref_sat,
        i_q_ref_sat_var: i_q_ref_sat,
        v_d_c: v_d_g - (R * i_d - omega * L * i_q),
        v_q_c: v_q_g - (-R * i_q - omega * L * i_d),
        vd_hat: v_d_c - (v_d_g - L * omega * i_q),
        vq_hat: v_q_c - (v_q_g + L * omega * i_d),
        Vdc_ref: v_dc,
        Vm_ac_ref: Vm,
        Q_ref: Q,
        P_ref: P,
    }
    
    # Add control-specific initialization
    if control1 in [ConverterControlType.Pac, ConverterControlType.Pdc]:
        init_eqs[P_ref] = P
    elif control1 == ConverterControlType.Vm_dc:
        init_eqs[Vdc_ref] = v_dc
        # For DC voltage control, initialize i_q_ref based on initial power flow
        init_eqs[i_q_ref] = P / v_q_g
    
    if control2 == ConverterControlType.Qac:
        init_eqs[Q_ref] = Q
    elif control2 == ConverterControlType.Vm_ac:
        init_eqs[Vm_ac_ref] = Vm
        # For AC voltage control, initialize i_d_ref based on initial reactive power
        init_eqs[i_d_ref] = Q / v_q_g

    gfl_block_aux = Block(
        algebraic_eqs=algebraic_eqs,
        algebraic_vars=algebraic_vars,
        event_dict= event_dict,
        init_eqs=init_eqs,
        external_mapping={
            VarPowerFlowRefferenceType.P:P,
            VarPowerFlowRefferenceType.Q:Q,
        }
    )
    gfl_block.add(gfl_block_aux)

    # Add all control blocks
    for ctrl_block in control_blocks:
        gfl_block.add(ctrl_block)
    gfl_block.add(control_block_id)
    gfl_block.add(control_block_iq)

    gfl_block.add(pll_block)
    gfl_block.add(EMT_block)
    gfl_block.unify_blocks()

    internals = {
        "theta": theta,
        "v_d_c": v_d_c,
        "v_q_c": v_q_c,
        "vd_hat": vd_hat,
        "vq_hat": vq_hat,
        "R": R,
        "L": L,
    }
    return gfl_block, i_d, i_q, P, Q, internals


def trafo_gfl_converter_model(vfactory: VarFactory,
                              inputs,
                              control1: ConverterControlType = ConverterControlType.Pac,
                              control2: ConverterControlType = ConverterControlType.Qac):
    """
    GFL converter model for transformer-coupled setup.

    Inputs order:
      [Vm_f, Va_f, Vm_t, Va_t, Vdc, Pt_vsc, Qt_vsc]

    - from side (f): AC internal converter bus
    - to side   (t): AC grid bus
    """
    Vm_f = inputs[0]
    Va_f = inputs[1]
    Vm_t = inputs[2]
    Va_t = inputs[3]
    Vdc = inputs[4]
    Pt_vsc = inputs[5]
    Qt_vsc = inputs[6]

    gfl_block, i_d, i_q, P, Q, internals = build_gfl_converter_model(
        vfactory=vfactory,
        inputs=[Vm_t, Va_t, Vdc, Pt_vsc, Qt_vsc],
        control1=control1,
        control2=control2,
    )

    # Enforce converter dq voltages on the internal AC bus side.
    theta = internals["theta"]
    v_d_c = internals["v_d_c"]
    v_q_c = internals["v_q_c"]
    vd_hat = internals["vd_hat"]
    vq_hat = internals["vq_hat"]

    gfl_block.algebraic_eqs.append(v_d_c - Vm_f * sym.sin(Va_f - theta))
    gfl_block.algebraic_eqs.append(v_q_c - Vm_f * sym.cos(Va_f - theta))
    #gfl_block.init_eqs[v_d_c] = Vm_f * sym.sin(Va_f - theta)
    #gfl_block.init_eqs[v_q_c] = Vm_f * sym.cos(Va_f - theta)

    gfl_block.unify_blocks()
    return gfl_block, i_d, i_q, P, Q, internals

def VscGflBuild(vfactory: VarFactory, name: str = "",
                control1: ConverterControlType = ConverterControlType.Pac,
                control2: ConverterControlType = ConverterControlType.Qac) -> RmsModelTemplate:
    """
    VSC GFL (Grid Following) model
    with from side the DC bus and to side the AC bus
    
    Args:
        name: Model name
        control1: First control mode (Pac, Pdc, or Vm_dc)
        control2: Second control mode (Qac or Vm_ac)
    
    Supported control combinations:
        - Pac + Qac: Active and reactive power control
        - Pac + Vm_ac: Active power and AC voltage control
        - Pdc + Qac: DC power and reactive power control
        - Pdc + Vm_ac: DC power and AC voltage control
        - Vm_dc + Qac: DC voltage and reactive power control
        - Vm_dc + Vm_ac: DC voltage and AC voltage control
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.VscDevice
    # Inputs: Vm, Va, Vdc (Pt_vsc and Qt_vsc come from power flow initialization)
    inputs = [vfactory.add_var("Vm_"), vfactory.add_var("Va_"), vfactory.add_var("Vdc_")]
    Vm = inputs[0]
    Va = inputs[1]
    v_dc = inputs[2]

    # Vars:
    Pt_vsc = vfactory.add_var('Pt_vsc')
    Qt_vsc = vfactory.add_var('Qt_vsc')
    Pf_vsc = vfactory.add_var('Pf_vsc')

    # Parameters:
    bt = vfactory.add_var('bt')
    gt = vfactory.add_var('gt')
    Qf = vfactory.add_var('Qf')
    a0 = vfactory.add_var('a0')
    a1 = vfactory.add_var('a1')
    a2 = vfactory.add_var('a2')
    
    # Build the converter model with specified control modes
    gfl_block, i_d, i_q, P, Q, internals = build_gfl_converter_model(
        vfactory = vfactory,
        inputs=[Vm, Va, v_dc, Pt_vsc, Qt_vsc],
        control1=control1,
        control2=control2
    )

    event_dict = {
        Qf: vfactory.add_const(0.0),
        bt: vfactory.add_const(0.0),
        gt: vfactory.add_const(0.1),
        a0: vfactory.add_const(0.0),
        a1: vfactory.add_const(0.0),
        a2: vfactory.add_const(0.0),
    }
    
    Im = sym.sqrt(i_d**2 + i_q**2 + vfactory.add_const(1e-11))
    vsc_block = Block(
        algebraic_eqs=[
            Pf_vsc + P - (a0 + a1*Im + a2*Im**2),
            Pt_vsc + P,
            Qt_vsc + Q,
        ],
        algebraic_vars=[Pt_vsc, Qt_vsc, Pf_vsc],
        init_eqs={
            # vsh: sym.sqrt((exp1**2 + exp2**2)/(gt**2 + bt**2))/Vm,
            # ash: sym.atan((-gt*exp1 - bt*exp2)/(bt*exp1 - gt*exp2)),
        },
        event_dict= event_dict,
        external_mapping={
            VarPowerFlowRefferenceType.P: P,
            VarPowerFlowRefferenceType.Q: Q,
        },
        in_vars= inputs,
        out_vars = [Pt_vsc, Qt_vsc, Pf_vsc]
    )
    vsc_block.external_mapping = {
        VarPowerFlowRefferenceType.Vmt: inputs[0],
        VarPowerFlowRefferenceType.Vat: inputs[1],
        VarPowerFlowRefferenceType.Vdc: inputs[2],
        VarPowerFlowRefferenceType.Pt: Pt_vsc,
        VarPowerFlowRefferenceType.Qt: Qt_vsc,
        VarPowerFlowRefferenceType.Pf: Pf_vsc,
        VarPowerFlowRefferenceType.Qf: Qf,
    }
    vsc_block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.R1: internals["R"],
        ParamPowerFlowRefferenceType.X1: internals["L"],
        ParamPowerFlowRefferenceType.alpha1: a0,
        ParamPowerFlowRefferenceType.alpha2: a1,
        ParamPowerFlowRefferenceType.alpha3: a2,
    }

    vsc_block.add(gfl_block)
    vsc_block.name = 'gfl_block'

    templ._block = vsc_block
    return templ


def TrafoGflBuild(vfactory: VarFactory, name: str = "",
                  control1: ConverterControlType = ConverterControlType.Pac,
                  control2: ConverterControlType = ConverterControlType.Qac) -> RmsModelTemplate:
    """
    Transformer-coupled GFL model where AC-from side is internal converter bus
    and AC-to side is grid bus.
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.VscDevice

    Vm_f = vfactory.add_var("Vmf_")
    Va_f = vfactory.add_var("Vaf_")
    Vm_t = vfactory.add_var("Vmt_")
    Va_t = vfactory.add_var("Vat_")
    Vdc = vfactory.add_var("Vdc_")
    inputs = [Vm_f, Va_f, Vm_t, Va_t, Vdc]

    Pt_vsc = vfactory.add_var('Pt_vsc_control')
    Qt_vsc = vfactory.add_var('Qt_vsc_control')
    Pf_vsc = vfactory.add_var('Pf_vsc_control')
    Qf_vsc = vfactory.add_var('Qf_vsc_control')

    Qf = vfactory.add_var('Qf')
    a0 = vfactory.add_var('a0')
    a1 = vfactory.add_var('a1')
    a2 = vfactory.add_var('a2')

    gfl_block, i_d, i_q, P, Q, internals = trafo_gfl_converter_model(
        vfactory=vfactory,
        inputs=[Vm_f, Va_f, Vm_t, Va_t, Vdc, Pt_vsc, Qt_vsc],
        control1=control1,
        control2=control2,
    )
    gfl_block.init_eqs[P] = -Pt_vsc
    gfl_block.init_eqs[Q] = -Qt_vsc

    event_dict = {
        Qf: vfactory.add_const(0.0),
        a0: vfactory.add_const(0.0),
        a1: vfactory.add_const(0.0),
        a2: vfactory.add_const(0.0),
    }

    #Im = sym.sqrt(i_d**2 + i_q**2 + vfactory.add_const(1e-11))
    Im = sym.sqrt(Pt_vsc * Pt_vsc + Qt_vsc * Qt_vsc) / (Vm_t)
    Im_out = vfactory.add_var('Im_vsc_control')

    vsc_block = Block(
        algebraic_eqs=[
            Pf_vsc + Pt_vsc - internals["R"]*(Im ** 2),
            Pt_vsc + P,
            Qt_vsc + Q,
            Qf_vsc - Qf,
            Im_out - Im,
        ],
        algebraic_vars=[Pf_vsc, Pt_vsc, Qt_vsc, Qf_vsc,Im_out],
        init_eqs={
            Im_out: Im,
            Qf_vsc: Qf,
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[Pf_vsc, Pt_vsc, Qt_vsc, Im_out],
    )

    vsc_block.external_mapping = {
        VarPowerFlowRefferenceType.Vmf: Vm_f,
        VarPowerFlowRefferenceType.Vaf: Va_f,
        VarPowerFlowRefferenceType.Vmt: Vm_t,
        VarPowerFlowRefferenceType.Vat: Va_t,
        VarPowerFlowRefferenceType.Vdc: Vdc,
        VarPowerFlowRefferenceType.Pt: Pt_vsc,
        VarPowerFlowRefferenceType.Qt: Qt_vsc,
        VarPowerFlowRefferenceType.Pf: Pf_vsc,
        VarPowerFlowRefferenceType.Qf: Qf_vsc,
    }
    vsc_block.api_obj_mapping = {
        ParamPowerFlowRefferenceType.R1: internals["R"],
        ParamPowerFlowRefferenceType.X1: internals["L"],
        ParamPowerFlowRefferenceType.alpha1: a0,
        ParamPowerFlowRefferenceType.alpha2: a1,
        ParamPowerFlowRefferenceType.alpha3: a2,
    }

    vsc_block.add(gfl_block)
    vsc_block.name = 'trafo_gfl_block'

    templ._block = vsc_block
    return templ
