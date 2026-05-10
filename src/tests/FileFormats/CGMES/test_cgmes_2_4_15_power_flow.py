# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Import-level CGMES tests that only validate loading and power-flow execution."""

import os

import VeraGridEngine.api as vg


def test_load_and_run_pf() -> None:
    """Load the selected public CGMES packages and verify each can complete a power flow cleanly."""

    cgmes_path = os.path.join("data", "grids", "CGMES_2_4_15", "20250605T1315Z_RT_SmallGridTestConfiguration_.zip")

    grid = vg.open_cgmes(cgmes_path, cgmes_version=vg.CGMESVersions.v2_4_15)

    if grid is not None:
        options = vg.PowerFlowOptions(ignore_single_node_islands=True)
        res = vg.power_flow(grid, options=options)

        assert res.converged
    else:
        raise Exception(f"CGMES file {cgmes_path} not found")