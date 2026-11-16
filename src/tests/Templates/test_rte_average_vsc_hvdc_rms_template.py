# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construction checks for the Colib RTE average VSC-HVDC template."""

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.dc_line.rte_average_vsc_hvdc_rms_template import (
    get_rte_average_vsc_hvdc_rms_template,
)


def test_rte_average_vsc_hvdc_has_converter_and_dc_link() -> None:
    """Ensure the terminal contains both required physical subsystems."""
    template = get_rte_average_vsc_hvdc_rms_template(vf=VarFactory())

    assert len(template.block.children) == 2
