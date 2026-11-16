# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Internal converter and DC source for a one-terminal DGS RMS injection."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def build_complete_injection_template(
    vfactory: VarFactory,
    base_template: RmsModelTemplate,
    name: str,
) -> RmsModelTemplate:
    """Enclose an imported AC injection, VSC loss law, DC link, and DC source.

    The base template retains its exported controller equations and AC P/Q
    mapping.  The DC source's power command is sampled at the initialized
    operating point; subsequent converter-power changes charge or discharge
    the internal capacitor.  No synthetic network DC bus is required.

    :param vfactory: Circuit factory owning newly allocated symbols.
    :param base_template: Reusable controller declaration enclosed by the wrapper.
    :param name: Display name of the complete injection template.
    :return: Complete injection wrapper containing the selected controller graph.
    """
    base: Block = base_template.block
    mapping = base.external_mapping
    try:
        p_ac = mapping[VarPowerFlowReferenceType.P]
        q_ac = mapping[VarPowerFlowReferenceType.Q]
        vm_ac = mapping[VarPowerFlowReferenceType.Vm]
    except KeyError as exc:
        raise ValueError("Complete DGS injection requires AC P, Q, and Vm mappings") from exc

    vdc = vfactory.add_var("Vdc_internal")
    pdc = vfactory.add_var("Pdc_internal")
    idc_converter = vfactory.add_var("Idc_converter")
    idc_source = vfactory.add_var("Idc_source")
    pdc_source = vfactory.add_var("Pdc_source_command")
    capacitance = vfactory.add_var("Cdc_internal")
    conductance = vfactory.add_var("Gdc_internal")
    epsilon = vfactory.add_var("Vdc_epsilon")
    alpha1 = vfactory.add_var("vsc_alpha1")
    alpha2 = vfactory.add_var("vsc_alpha2")
    alpha3 = vfactory.add_var("vsc_alpha3")

    current = sym.sqrt(p_ac * p_ac + q_ac * q_ac + epsilon) / (vm_ac + epsilon)
    converter_loss = alpha1 + alpha2 * current + alpha3 * current * current
    dc_block = Block(
        name="Internal VSC, DC link, and DC source",
        in_vars=[p_ac, q_ac, vm_ac],
        out_vars=[vdc, pdc, idc_converter, idc_source],
        state_vars=[vdc],
        state_eqs=[(idc_source - idc_converter - conductance * vdc) / capacitance],
        algebraic_vars=[pdc, idc_converter, idc_source],
        algebraic_eqs=[
            pdc - p_ac - converter_loss,
            idc_converter - pdc / (vdc + epsilon),
            idc_source - pdc_source / (vdc + epsilon),
        ],
        event_dict={
            capacitance: vfactory.add_const(0.05),
            conductance: vfactory.add_const(0.01),
            epsilon: vfactory.add_const(1e-9),
            alpha1: vfactory.add_const(0.0),
            alpha2: vfactory.add_const(0.0),
            alpha3: vfactory.add_const(0.0),
            pdc_source: p_ac + converter_loss + conductance * (1 + epsilon),
        },
        init_eqs={
            vdc: vfactory.add_const(1.0),
            pdc: p_ac + converter_loss,
            idc_converter: pdc / (vdc + epsilon),
            idc_source: pdc_source / (vdc + epsilon),
        },
    )

    template = RmsModelTemplate(name=name)
    template.tpe = base_template.tpe
    template.block = Block(
        name=name,
        in_vars=list(base.in_vars),
        out_vars=list(base.out_vars),
        children=[base, dc_block],
        external_mapping=dict(mapping),
    )
    template.comment = "One-terminal DGS injection with internal VSC and DC source"
    return template
