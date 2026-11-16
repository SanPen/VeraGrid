# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib UPC EMT grid-following VSC template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.converters.vsc_gfl_emt import VscGflEmtBuild
from VeraGridEngine.enumerations import ConverterControlType, VarPowerFlowReferenceType


def get_upc_gfl_emt_template(
        vf: VarFactory,
        name: str = 'UPC EMT GFL VSC',
) -> EmtModelTemplate:
    """Build the UPC balanced EMT grid-following VSC.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: EMT grid-following VSC with active/reactive power controls.
    """
    # The UPC AC-side controller uses active and reactive power references.
    template: EmtModelTemplate = VscGflEmtBuild(
        vfactory=vf,
        name=name,
        control1=ConverterControlType.Pac,
        control2=ConverterControlType.Qac,
    )
    # Expose the controlled AC injection and DC-link current as terminal outputs.
    template.block.out_vars = [
        template.block.external_mapping[VarPowerFlowReferenceType.i_A],
        template.block.external_mapping[VarPowerFlowReferenceType.i_B],
        template.block.external_mapping[VarPowerFlowReferenceType.i_C],
        template.block.external_mapping[VarPowerFlowReferenceType.Idc],
    ]
    template.comment = 'Colib UPC EMT grid-following VSC realization'
    return template
