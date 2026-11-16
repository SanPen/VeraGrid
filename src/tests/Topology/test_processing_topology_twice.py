# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine as vg

def test_processing_topology_twice():

    fname = os.path.join('data', 'grids', 'CGMES_3_0', '20250605T1315Z_RT_SmallGridTestConfiguration_.zip')
    grid = vg.open_cgmes(filenames=[fname], cgmes_version=vg.CGMESVersions.v3_0_0)

    if grid is not None:
        nc = vg.compile_numerical_circuit_at(grid, t_idx=None)
        nc.process_reducible_branches()
        mapping1 = nc.get_reduction_bus_mapping()
        print(mapping1)

        nc.process_reducible_branches()
        mapping2 = nc.get_reduction_bus_mapping()
        print(mapping2)

        ok = np.isclose(mapping1, mapping2).all()
        print("same:", ok)
        assert ok