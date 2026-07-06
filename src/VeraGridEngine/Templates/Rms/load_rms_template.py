# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType, VarPowerFlowReferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block


class LoadRmsTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(vf, params=[
            TemplateProp(name="pl0_init", units="pu", descr="Initial active power at nominal voltage.", tpe=float | None),
            TemplateProp(name="ql0_init", units="pu", descr="Initial reactive power at nominal voltage.", tpe=float | None),
            TemplateProp(name="name", units="", descr="Name of the rms model.", tpe=str),
        ])

    def eval(self) -> RmsModelTemplate:
        return get_load_rms_template(self.vf, self.get_value("name"), self.get_value("pl0_init"), self.get_value("ql0_init"))


def get_load_rms_template(
        vfactory: VarFactory,
        name="Load rms template",
        pl0_init: float | None = None,
        ql0_init: float | None = None,
) -> RmsModelTemplate:
    """
    Get the RMS template model of the Load
    :return: RmsModelTemplate
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    inputs = [
        vfactory.add_var("Vm_" + name, reference=VarPowerFlowReferenceType.Vm),
        vfactory.add_var("Va_" + name, reference=VarPowerFlowReferenceType.Va)
    ]

    Pl0 = vfactory.add_var("Pl0")
    Ql0 = vfactory.add_var("Ql0")
    Pl = vfactory.add_var("Pl", reference=VarPowerFlowReferenceType.P)
    Ql = vfactory.add_var("Ql", reference=VarPowerFlowReferenceType.Q)

    block = Block()

    block.event_dict[Pl0] = Pl
    block.event_dict[Ql0] = Ql

    block.algebraic_vars = [Pl, Ql]


    block.algebraic_eqs = [Pl - Pl0, Ql - Ql0]

    block.in_vars = inputs
    block.out_vars = [Pl, Ql]

    block.name = name

    templ.block.children.append(block)

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.Va: inputs[1],
        VarPowerFlowReferenceType.Vm: inputs[0],
        VarPowerFlowReferenceType.P: Pl,
        VarPowerFlowReferenceType.Q: Ql
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.Pl0: Pl0,
        ParamPowerFlowReferenceType.Ql0: Ql0,
    }

    #templ.block.init_eqs = {
    #    Pl0: Pl,
    #    Ql0: Ql,
    #}
    templ.block.in_vars = inputs
    templ.block.out_vars = [Pl, Ql]

    return templ
