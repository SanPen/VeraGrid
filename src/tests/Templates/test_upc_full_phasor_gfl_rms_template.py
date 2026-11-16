# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construction checks for the Colib UPC full-phasor GFL VSC."""

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.upc_full_phasor_gfl_rms_template import (
    get_upc_full_phasor_gfl_rms_template,
)


def test_upc_full_phasor_gfl_has_a_dynamic_controller() -> None:
    """Ensure the named Colib model builds a non-empty RMS controller."""
    template = get_upc_full_phasor_gfl_rms_template(vf=VarFactory())

    assert len(template.block.children) > 0
