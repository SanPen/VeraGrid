# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_definiton import TemplateDefinition, TemplateProp
from VeraGridEngine.Utils.Symbolic.block import Block


class DynamicTapLoadRmsTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(vf, params=[
            TemplateProp(name="Pl0", units="pu", descr="Initial active power at nominal voltage (pu).", tpe=float),
            TemplateProp(name="Ql0", units="pu", descr="Initial reactive power at nominal voltage (pu).", tpe=float),
            TemplateProp(name="name", units="", descr="Name of the rms model.", tpe=str),
        ])

    def eval(self) -> RmsModelTemplate:
        return DynamicTapLoadBuild(self.vf, self.get_value("name"), self.get_value("Pl0"), self.get_value("Ql0"))


def DynamicTapLoadBuild(vfactory: VarFactory, name: str = "", Pl0=1.0, Ql0=0.1) -> RmsModelTemplate:
    """
    Builds an RMS model template for a dynamic tap-changing load with PI voltage control.

    This load model represents a load equipped with an on-load tap changer (OLTC) or similar
    voltage regulation device. A PI controller adjusts the effective voltage ratio (m) to
    maintain the load voltage within desired bounds.

    The model includes:
    - State equation for tap position/ratio (m) controlled by PI regulator
    - Algebraic equations for active and reactive power with exponential voltage dependency
    - Power equations: P = P0*(V/m)^alpha_p, Q = Q0*(V/m)^alpha_q

    The PI controller adjusts m based on voltage deviation from reference:
        dm/dt = -Kd*m + Ki*(V/m - 1 + Kd/Ki*V0)

    Args:
        vfactory: VarFactory instance for creating variables
        name (str): Name of the load model
        Pl0 (float): Initial active power at nominal voltage (pu)
        Ql0 (float): Initial reactive power at nominal voltage (pu)

    Returns:
        RmsModelTemplate: Configured RMS model template for dynamic tap load simulation
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    inputs = [vfactory.add_var("Vm_")]

    # Vars:
    m = vfactory.add_var('m')
    P = vfactory.add_var('P')
    Q = vfactory.add_var('Q')

    # Parameters:
    P0 = vfactory.add_var('Pl0')
    Q0 = vfactory.add_var('Ql0')
    V0 = vfactory.add_var('V0')
    Kd = vfactory.add_var('Kd')
    Ki = vfactory.add_var('Ki')
    alpha_p = vfactory.add_var('alpha_p')
    alpha_q = vfactory.add_var('alpha_q')
    m_max = vfactory.add_var('m_max')
    m_min = vfactory.add_var('m_min')

    # ZIP coefficients (classic formulation)
    event_dict = {
        P0: vfactory.add_const(Pl0),
        Q0: vfactory.add_const(Ql0),
        V0: vfactory.add_const(None),

        # Exponential Parameters
        alpha_p: vfactory.add_const(1.2),
        alpha_q: vfactory.add_const(1.2),

        # PI parameters
        Kd: vfactory.add_const(0.1),
        Ki: vfactory.add_const(0.1),
    }

    init_eqs = {
        V0: inputs[0],
        m: V0,
        P: P0,
        Q: Q0,
    }
    templ.block = Block(
        state_eqs=[
            -Kd * m + Ki(inputs[0] / m - vfactory.add_const(1) + Kd / Ki * V0)
        ],
        state_vars=[m],
        algebraic_eqs=[
            P - P0 * (inputs[0] / m) ** alpha_p,
            Q - Q0 * (inputs[0] / m) ** alpha_q,
        ],
        algebraic_vars=[P, Q],
        init_eqs=init_eqs,
        event_dict=event_dict,
    )

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.P: P,
        VarPowerFlowReferenceType.Q: Q,
        VarPowerFlowReferenceType.Vm: inputs[0],
    }

    templ.block.in_vars = inputs

    return templ
