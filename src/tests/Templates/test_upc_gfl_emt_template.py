# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib UPC EMT grid-following VSC template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.converters.upc_gfl_emt_template import get_upc_gfl_emt_template


def test_upc_gfl_emt_template_has_three_phase_and_dc_outputs() -> None:
    """The UPC EMT GFL must expose three AC currents and one DC current.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: EmtModelTemplate = get_upc_gfl_emt_template(vf=variable_factory)

    assert len(template.block.out_vars) == 4
