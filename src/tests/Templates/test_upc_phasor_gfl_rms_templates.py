# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for reduced-order UPC RMS grid-following VSC templates."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.upc_phasor_gfl_rms_templates import (
    get_upc_phasor_i0_gfl_rms_template,
    get_upc_phasor_i1_gfl_rms_template,
    get_upc_phasor_pq1_gfl_rms_template,
)


def test_upc_phasor_gfl_variants_build_distinct_current_models() -> None:
    """I1 must retain more current-loop dynamics than I0 and PQ1.

    :return: ``None``.
    """
    i0_factory: VarFactory = VarFactory()
    i1_factory: VarFactory = VarFactory()
    pq1_factory: VarFactory = VarFactory()

    # Construct every published reduction before comparing their retained dynamics.
    i0_template: RmsModelTemplate = get_upc_phasor_i0_gfl_rms_template(vf=i0_factory)
    i1_template: RmsModelTemplate = get_upc_phasor_i1_gfl_rms_template(vf=i1_factory)
    pq1_template: RmsModelTemplate = get_upc_phasor_pq1_gfl_rms_template(vf=pq1_factory)

    assert len(i1_template.block.diff_vars) > len(i0_template.block.diff_vars)
    assert len(i1_template.block.diff_vars) > len(pq1_template.block.diff_vars)
