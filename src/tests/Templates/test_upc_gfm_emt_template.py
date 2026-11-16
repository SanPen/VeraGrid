# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the UPC EMT grid-forming converter template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.converters.vsc_gfm_upc_emt import get_vsc_gfm_upc_emt_template


def test_upc_gfm_emt_template_has_phase_current_outputs() -> None:
    """The UPC EMT GFM must expose its three AC and DC current outputs.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()

    # Construct the source model to protect its external network interface.
    template: EmtModelTemplate = get_vsc_gfm_upc_emt_template(vf=variable_factory)

    assert len(template.block.out_vars) == 4
