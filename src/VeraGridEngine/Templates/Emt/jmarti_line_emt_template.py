# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import List

from VeraGridEngine.Utils.Symbolic.block import Var
from VeraGridEngine.enumerations import DeviceType, EmtLineTypes, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Templates.template_definition import TemplateDefinition, TemplateProp


class JmartiLineEmtTemplate(TemplateDefinition):

    def __init__(self, vf):
        super().__init__(vf, params=[
            TemplateProp(name="phN", units="", descr="True if the line has neutral, else False.", tpe=bool),
            TemplateProp(name="phA", units="", descr="True if phase A is active, else False.", tpe=bool),
            TemplateProp(name="phB", units="", descr="True if phase B is active, else False.", tpe=bool),
            TemplateProp(name="phC", units="", descr="True if phase C is active, else False.", tpe=bool),
            TemplateProp(name="name", units="", descr="Name of the emt model.", tpe=str),
        ])

    def eval(self) -> EmtModelTemplate:
        return get_jmarti_line_emt_template(
            self.vf,
            self.get_value("phN"),
            self.get_value("phA"),
            self.get_value("phB"),
            self.get_value("phC"),
            self.get_value("name"),
        )


def get_jmarti_line_emt_template(vf: VarFactory,
                                 phN: bool = False,
                                 phA: bool = True,
                                 phB: bool = True,
                                 phC: bool = True,
                                 name: str | None = "J_Marti") -> EmtModelTemplate:
    """
    Create the symbolic EMT template shell for a JMARTI line.

    The active JMARTI runtime computes the effective Norton injections and writes
    them into retained history parameters, exactly like the Bergeron workflow.
    The symbolic template therefore only exposes terminal voltages and the
    phase-domain history current parameters used by the runtime companion.

    :param vf: EMT variable factory.
    :param phN: True if the line has neutral, else False.
    :param phA: True if phase A is active, else False.
    :param phB: True if phase B is active, else False.
    :param phC: True if phase C is active, else False.
    :param name: Symbolic model name.
    :return: EMT JMARTI line template.
    """
    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.LineDevice
    templ.name = name
    templ.block.name = EmtLineTypes.J_Marti.value

    phase_labels: List[str] = list(["N", "A", "B", "C"])
    phase_mask = [phN, phA, phB, phC]
    active_phases: List[str] = list()
    phase_index: int = 0
    vf_keys = dict({
        "N": VarPowerFlowReferenceType.vf_N,
        "A": VarPowerFlowReferenceType.vf_A,
        "B": VarPowerFlowReferenceType.vf_B,
        "C": VarPowerFlowReferenceType.vf_C,
    })
    vt_keys = dict({
        "N": VarPowerFlowReferenceType.vt_N,
        "A": VarPowerFlowReferenceType.vt_A,
        "B": VarPowerFlowReferenceType.vt_B,
        "C": VarPowerFlowReferenceType.vt_C,
    })
    vf_vars: List[Var] = list()
    vt_vars: List[Var] = list()
    ih_f: List[Var] = list()
    ih_t: List[Var] = list()
    phase_label: str

    while phase_index < len(phase_labels):
        if phase_mask[phase_index]:
            active_phases.append(phase_labels[phase_index])
        else:
            pass

        phase_index += 1

    for phase_label in active_phases:
        vf_vars.append(vf.add_var(name=f"vf_{phase_label}_{name}", reference=vf_keys[phase_label]))
        vt_vars.append(vf.add_var(name=f"vt_{phase_label}_{name}", reference=vt_keys[phase_label]))
        ih_f.append(vf.add_var(name=f"Ih_f_{name}_{phase_label}"))
        ih_t.append(vf.add_var(name=f"Ih_t_{name}_{phase_label}"))

    templ.block.in_vars = vf_vars + vt_vars
    templ.block.event_dict = dict({parameter: vf.add_const(0.0) for parameter in (ih_f + ih_t)})

    return templ
