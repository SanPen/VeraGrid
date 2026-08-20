# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType, VarPowerFlowReferenceType, DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


class LoadRmsTemplate(TemplateDefinition):
    """Definition of the editable RMS constant-power load."""

    __slots__ = ()

    def __init__(self, vf: VarFactory) -> None:
        """Create the editable RMS load template definition.

        :param vf: Variable factory used to build the model.
        :return: None.
        """
        properties: list[TemplateProp] = list([
            TemplateProp(name="pl0_init", units="pu", descr="Initial active power at nominal voltage.",
                         tpe=float | None, value=None),
            TemplateProp(name="ql0_init", units="pu", descr="Initial reactive power at nominal voltage.",
                         tpe=float | None, value=None),
            TemplateProp(name="name", units="", descr="Name of the rms model.", tpe=str,
                         value="Load rms template"),
        ])
        TemplateDefinition.__init__(self, vf, properties)

    def eval(self) -> RmsModelTemplate:
        """Build the RMS load with optional user-provided initial powers.

        :return: Constructed RMS load template.
        """
        return get_load_rms_template(
            vfactory=self.vf,
            name=str(self.get_value("name")),
            pl0_init=self.get_value("pl0_init"),
            ql0_init=self.get_value("ql0_init"),
        )


def get_load_rms_template(
        vfactory: VarFactory,
        name: str = "Load rms template",
        pl0_init: float | None = None,
        ql0_init: float | None = None,
) -> RmsModelTemplate:
    """Build the RMS constant-power load model.

    ``Pl0`` and ``Ql0`` remain runtime event parameters. When their optional
    values are unset, explicit initialization copies the solved operating point
    from ``Pl`` and ``Ql``. A numeric value supplied by General options replaces
    that automatic starting value while preserving event support.

    :param vfactory: Variable factory used by the symbolic model.
    :param name: Model name.
    :param pl0_init: Optional active-power override in p.u.
    :param ql0_init: Optional reactive-power override in p.u.
    :return: RMS load template.
    """
    templ: RmsModelTemplate = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    inputs: list[Var] = list([
        vfactory.add_var("Vm", reference=VarPowerFlowReferenceType.Vm),
        vfactory.add_var("Va", reference=VarPowerFlowReferenceType.Va)
    ])

    Pl0: Var = vfactory.add_var("Pl0")
    Ql0: Var = vfactory.add_var("Ql0")
    Pl: Var = vfactory.add_var("Pl", reference=VarPowerFlowReferenceType.P)
    Ql: Var = vfactory.add_var("Ql", reference=VarPowerFlowReferenceType.Q)

    block: Block = Block()

    # Event parameters must be represented by constants so General options can
    # stage a numeric override. ``None`` intentionally means "derive at t=0";
    # the explicit initialization equations below provide that derivation.
    block.event_dict[Pl0] = vfactory.add_const(pl0_init)
    block.event_dict[Ql0] = vfactory.add_const(ql0_init)
    block.init_eqs = dict({
        Pl0: Pl,
        Ql0: Ql,
    })

    block.algebraic_vars = list([Pl, Ql])
    block.algebraic_eqs = list([Pl - Pl0, Ql - Ql0])

    block.in_vars = inputs
    block.out_vars = list([Pl, Ql])

    block.name = name

    templ.block.children.append(block)

    templ.block.external_mapping = dict({
        VarPowerFlowReferenceType.Va: inputs[1],
        VarPowerFlowReferenceType.Vm: inputs[0],
        VarPowerFlowReferenceType.P: Pl,
        VarPowerFlowReferenceType.Q: Ql
    })

    templ.block.api_obj_mapping = dict({
        ParamPowerFlowReferenceType.Pl0: Pl0,
        ParamPowerFlowReferenceType.Ql0: Ql0,
    })

    templ.block.in_vars = inputs
    templ.block.out_vars = list([Pl, Ql])

    return templ
