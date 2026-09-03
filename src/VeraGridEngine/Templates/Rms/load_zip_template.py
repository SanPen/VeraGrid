# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp
from VeraGridEngine.Utils.Symbolic.block import Block


class ZipLoadRmsTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(vf, params=[
            TemplateProp(name="Pl0", units="pu", descr="Initial active power at nominal voltage (pu).", tpe=float),
            TemplateProp(name="Ql0", units="pu", descr="Initial reactive power at nominal voltage (pu).", tpe=float),
            TemplateProp(name="name", units="", descr="Name of the rms model.", tpe=str),
        ])

    def eval(self) -> RmsModelTemplate:
        return ZIPLoadBuild(self.vf, self.get_value("name"), self.get_value("Pl0"), self.get_value("Ql0"))


def ZIPLoadBuild(vfactory: VarFactory, name: str = "ZIP model", Pl0=1.0, Ql0=0.1) -> RmsModelTemplate:
    """
    Builds an RMS model template for a ZIP load.
    
    ZIP load model represents load power consumption as a combination of constant impedance (Z),
    constant current (I), and constant power (P) components. The active and reactive power 
    are calculated as quadratic functions of voltage magnitude.
    
    The power equations are:
        P = P0 * (a1*(V/V0)^2 + a2*(V/V0) + a3)
        Q = Q0 * (a4*(V/V0)^2 + a5*(V/V0) + a6)
    
    Where coefficients must sum to 1.0 for both active (a1+a2+a3) and reactive (a4+a5+a6) power.
    
    Args:
        vfactory: VarFactory instance for creating variables
        name (str): Name of the load model
        Pl0 (float): Initial active power at nominal voltage (pu)
        Ql0 (float): Initial reactive power at nominal voltage (pu)
    
    Returns:
        RmsModelTemplate: Configured RMS model template for ZIP load simulation
    
    Raises:
        ValueError: If ZIP coefficients do not sum to 1.0 within tolerance
    """
    templ = RmsModelTemplate()
    templ.name = name
    templ.tpe = DeviceType.LoadDevice
    inputs = [vfactory.add_var("Vm")]

    # Vars:
    P = vfactory.add_var('P_zip', reference=VarPowerFlowReferenceType.P)
    Q = vfactory.add_var('Q_zip', reference=VarPowerFlowReferenceType.Q)

    # Parameters:
    P0 = vfactory.add_var('P0')
    Q0 = vfactory.add_var('Q0')
    V0 = vfactory.add_var('V0')
    a1 = vfactory.add_var('a1')
    a2 = vfactory.add_var('a2')
    a3 = vfactory.add_var('a3')
    a4 = vfactory.add_var('a4')
    a5 = vfactory.add_var('a5')
    a6 = vfactory.add_var('a6')

    # ZIP coefficients (classic formulation)
    event_dict = {
        P0: vfactory.add_const(Pl0),
        Q0: vfactory.add_const(Ql0),
        V0: inputs[0],

        # Active power ZIP
        a1: vfactory.add_const(0.1),  # Z
        a2: vfactory.add_const(0.1),  # I
        a3: vfactory.add_const(0.8),  # P

        # Reactive power ZIP
        a4: vfactory.add_const(0.1),  # Z
        a5: vfactory.add_const(0.1),  # I
        a6: vfactory.add_const(0.8),  # P
    }

    # --- Validation (fail fast) ---

    P_sum = event_dict[a1].value + event_dict[a2].value + event_dict[a3].value
    Q_sum = event_dict[a4].value + event_dict[a5].value + event_dict[a6].value

    tol = 1e-9

    if abs(P_sum - 1.0) > tol:
        raise ValueError(
            f"Invalid ZIP coefficients for active power: "
            f"a1 + a2 + a3 = {P_sum}, expected 1.0"
        )

    if abs(Q_sum - 1.0) > tol:
        raise ValueError(
            f"Invalid ZIP coefficients for reactive power: "
            f"a4 + a5 + a6 = {Q_sum}, expected 1.0"
        )

    init_eqs = {
        P: P0,
        Q: Q0,
    }
    templ.block = Block(
        algebraic_eqs=[
            P - P0 * (a1 * (inputs[0] / V0) ** 2 + a2 * inputs[0] / V0 + a3),
            Q - Q0 * (a4 * (inputs[0] / V0) ** 2 + a5 * inputs[0] / V0 + a6),
        ],
        algebraic_vars=[P, Q],
        init_eqs=init_eqs,
        event_dict=event_dict,
    )

    templ.block.name = 'ZIP Load'
    templ.block.external_mapping = {
        VarPowerFlowReferenceType.P: P,
        VarPowerFlowReferenceType.Q: Q,
        VarPowerFlowReferenceType.Vm: inputs[0],
    }

    templ.block.in_vars = inputs

    templ.comment = 'Load RMS ZIP voltage-dependent model'
    return templ
