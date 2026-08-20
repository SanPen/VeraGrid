# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.Gslv.activation import GSLV_AVAILABLE, pg
from VeraGridEngine.Compilers.Gslv.compare import compare_nc, CheckArr
from VeraGridEngine.Compilers.Gslv.conversion import to_gslv

def test_gslv_power_flow_slices():
    """

    :return:
    """

    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', "IEEE39_1W.gridcal")

    print(f"Testing: {fname}")

    grid_gc = vg.open_file(filename=fname)

    options = vg.PowerFlowOptions()

    time_indices = np.array([30 + i for i  in range(40)], dtype=int)

    # Native engine
    driver1 = vg.PowerFlowTimeSeriesDriver(grid=grid_gc,
                                           time_indices=time_indices,
                                           options=options,
                                           engine=vg.EngineType.VeraGrid)
    driver1.run()

    driver2 = vg.PowerFlowTimeSeriesDriver(grid=grid_gc,
                                           time_indices=time_indices,
                                           options=options,
                                           engine=vg.EngineType.GSLV)
    driver2.run()

    ok_v = np.allclose(driver1.results.voltage, driver2.results.voltage)
    ok_sf = np.allclose(driver1.results.Sf, driver2.results.Sf)

    assert ok_v
    assert ok_sf
