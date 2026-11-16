# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construction checks for the Colib UPC point-to-point EMT HVDC template."""

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.converters.upc_point_to_point_hvdc_emt_template import (
    get_upc_point_to_point_hvdc_emt_template,
)


def test_upc_point_to_point_has_two_stations_and_dc_corridor() -> None:
    """Ensure the Colib topology is retained by the composed template."""
    template = get_upc_point_to_point_hvdc_emt_template(vf=VarFactory())

    assert len(template.block.children) == 3
