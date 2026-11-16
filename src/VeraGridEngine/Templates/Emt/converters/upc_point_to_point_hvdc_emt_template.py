# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib UPC point-to-point EMT HVDC assembly."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.dc_line.dc_line_emt_template import get_dc_line_emt_template
from VeraGridEngine.Templates.Emt.converters.vsc_gfl_emt import VscGflEmtBuild
from VeraGridEngine.Templates.Emt.converters.vsc_gfm_emt import get_gfm_emt_template


def get_upc_point_to_point_hvdc_emt_template(
        vf: VarFactory,
        name: str = 'UPC_P2P_HVDC',
) -> EmtModelTemplate:
    """Build the Colib UPC GFM--DC-line--GFL EMT composition.

    The stations and DC corridor remain independent children so the EMT
    assembler can bind each to its own AC and DC terminals. This preserves the
    Colib topology without forcing a private terminal naming convention.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique point-to-point assembly name.
    :return: Composite EMT template containing both stations and DC corridor.
    """
    gfm: EmtModelTemplate = get_gfm_emt_template(vf=vf, name=name + '_GFM')
    gfl: EmtModelTemplate = VscGflEmtBuild(vfactory=vf, name=name + '_GFL')
    dc_line: EmtModelTemplate = get_dc_line_emt_template(vf=vf, name=name + '_DC')
    template: EmtModelTemplate = EmtModelTemplate()
    template.name = name
    template.block.name = name
    template.block.children = list((gfm.block, dc_line.block, gfl.block))
    template.comment = 'Colib UPC point-to-point GFM--DC--GFL EMT composition'
    return template
