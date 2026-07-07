# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""UPC-style grid-forming VSC EMT template.

This entry point is intentionally separated from ``vsc_gfm_emt`` so the UPC
model can evolve independently from the simpler droop EMT model. The first EMT
version keeps the same averaged voltage-source-behind-RL formulation used by
``get_gfm_emt_template``; the explicit LCL filter is represented by EMT network
elements in the validation grid, matching the two-line RMS setup.
"""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.vsc_gfm_emt import get_gfm_emt_template


def get_vsc_emt_upc_template(vf: VarFactory, name: str = "VSC_EMT_UPC") -> EmtModelTemplate:
    """Build the UPC grid-forming VSC EMT model.

    The model exposes the same EMT external mapping as the existing GFM VSC:
    three AC phase currents, one DC current, positive-sequence PF initialization
    references, and droop/event parameters. The static filter should be modeled
    explicitly with EMT lines/shunts outside the converter.
    """
    templ = get_gfm_emt_template(vf=vf, name=name)
    templ.name = name
    templ.block.name = name
    return templ
