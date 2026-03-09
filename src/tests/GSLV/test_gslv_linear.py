# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.circuit_to_gslv import GSLV_AVAILABLE, pg, to_gslv, compare_nc, CheckArr


def test_gslv_linear():
    """

    :return:
    """

    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', "IEEE39_1W.gridcal")

    print(f"Testing: {fname}")

    grid_gc = vg.open_file(filename=fname)

    # Native engine
    driver1 = vg.LinearAnalysisDriver(grid=grid_gc, engine=vg.EngineType.VeraGrid)
    driver1.run()

    driver2 = vg.LinearAnalysisDriver(grid=grid_gc, engine=vg.EngineType.GSLV)
    driver2.run()

    ok_ptdf = np.allclose(driver1.results.PTDF, driver2.results.PTDF)
    ok_lodf = np.allclose(driver1.results.LODF, driver2.results.LODF)

    assert ok_ptdf
    assert ok_lodf
