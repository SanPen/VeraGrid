# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import math
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType, ParamPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block


class ShuntTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(vf, params=[
            TemplateProp(name="phasor", units="", descr="Select the phasor shunt model when True.", tpe=bool),
            TemplateProp(name="name", units="", descr="Name of the rms model.", tpe=str),
        ])

    def eval(self) -> RmsModelTemplate:
        return get_shunt_template(self.vf, self.get_value("name"), self.get_value("phasor"))


def ShuntLoadBuild(vfactory: VarFactory, name: str = "Shunt RMS template") -> RmsModelTemplate:
    """Build the polar-voltage constant-admittance shunt model.

    :param vfactory: Factory that owns the model's symbolic variables.
    :param name: Name assigned to the generated RMS model template.
    :return: Configured polar shunt RMS model template.
    """
    templ = RmsModelTemplate(name=name)
    templ.tpe = DeviceType.ShuntDevice
    templ.name = name
    res_block = Block()
    pi = math.pi
    # Inputs:
    inputs = [vfactory.add_var('Vm', VarPowerFlowReferenceType.Vm),
              vfactory.add_var('Va', VarPowerFlowReferenceType.Va)]
    Vm = inputs[0]
    Va = inputs[1]
    # Variables:
    P = vfactory.add_var('P')
    Q = vfactory.add_var('Q')
    g = vfactory.add_var('g')
    b = vfactory.add_var('b')

    events_dict = {
        g: vfactory.add_const(0.0),
        b: vfactory.add_const(0.4),
    }

    res_block = Block(
        algebraic_eqs=[
            P + g * Vm ** 2,
            Q - b * Vm ** 2,
        ],
        algebraic_vars=[P, Q],
        init_eqs={
            P: vfactory.add_const(0.0),
            Q: vfactory.add_const(0.1),
        },
        api_obj_mapping={
            ParamPowerFlowReferenceType.g: g,
            ParamPowerFlowReferenceType.b: b,
        }
    )

    res_block.event_dict = events_dict
    res_block.external_mapping = {
        VarPowerFlowReferenceType.Vm: inputs[0],
        VarPowerFlowReferenceType.Va: inputs[1],
        VarPowerFlowReferenceType.P: P,
        VarPowerFlowReferenceType.Q: Q,
    }
    res_block.in_vars = inputs

    templ.block = res_block
    templ.comment = 'Shunt RMS constant-admittance polar model'
    return templ

def ShuntPhasorBuild(vfactory: VarFactory, name: str = "Shunt phasor RMS template") -> RmsModelTemplate:
    """Build the rectangular-phasor constant-admittance shunt model.

    :param vfactory: Factory that owns the model's symbolic variables.
    :param name: Name assigned to the generated RMS model template.
    :return: Configured phasor-current shunt RMS model template.
    """
    templ = RmsModelTemplate(name=name)
    templ.tpe = DeviceType.ShuntDevice
    templ.name = name
    res_block = Block()
    # Inputs:
    inputs = [
        vfactory.add_var('Vr_' + name, VarPowerFlowReferenceType.Vr),
        vfactory.add_var('Vi_' + name, VarPowerFlowReferenceType.Vi),
    ]
    Vr = inputs[0]
    Vi = inputs[1]

    # Variables:
    Ir = vfactory.add_var('Ir_shunt')
    Ii = vfactory.add_var('Ii_shunt')

    #Parameters:
    g = vfactory.add_var('g')
    b = vfactory.add_var('b')
    parameters = {
        g: vfactory.add_const(0.2),
        b: vfactory.add_const(0.2),
    }

    res_block = Block(
        algebraic_eqs=[
            Ir - (-g*Vr + b*Vi),
            Ii - (-g*Vi - b*Vr),
        ],
        algebraic_vars=[Ir, Ii],
        external_mapping={
            VarPowerFlowReferenceType.Vr: inputs[0],
            VarPowerFlowReferenceType.Vi: inputs[1],
            VarPowerFlowReferenceType.Ir: Ir,
            VarPowerFlowReferenceType.Ii: Ii,
            },
        init_eqs={
            Ir: -(g*Vr - b*Vi),
            Ii: -(g*Vi + b*Vr),
        },
        api_obj_mapping={
            ParamPowerFlowReferenceType.g: g,
            ParamPowerFlowReferenceType.b: b,
        }
    )

    res_block.parameters = parameters
    res_block.in_vars = inputs

    templ.block = res_block
    templ.comment = 'Shunt RMS constant-admittance phasor-current model'
    return templ

def get_shunt_template(
        vfactory: VarFactory,
        name: str = "Shunt phasor RMS template",
        phasor: bool = True,
) -> RmsModelTemplate:
    """Select and build the requested shunt formulation.

    :param vfactory: Factory that owns the model's symbolic variables.
    :param name: Name assigned to the generated RMS model template.
    :param phasor: Select the rectangular-phasor model when ``True`` or the
        polar-voltage model when ``False``.
    :return: Configured shunt RMS model template.
    """
    if phasor:
        return ShuntPhasorBuild(vfactory, name)
    else:
        return ShuntLoadBuild(vfactory, name)
