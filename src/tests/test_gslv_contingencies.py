# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.circuit_to_gslv import GSLV_AVAILABLE


def test_gslv_contingencies_snapshot():
    """

    :return:
    """

    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', "IEEE39_1W.gridcal")

    print(f"Testing: {fname}")

    grid_gc = vg.open_file(filename=fname)

    opts = vg.ContingencyAnalysisOptions(
        pf_options=vg.PowerFlowOptions(solver_type=vg.SolverType.NR),
        contingency_method=vg.ContingencyMethod.PowerFlow
    )

    # Native engine
    driver1 = vg.ContingencyAnalysisDriver(grid=grid_gc,
                                           options=opts,
                                           engine=vg.EngineType.VeraGrid)
    driver1.run()
    Pf1 = driver1.results.Sf.real

    driver2 = vg.ContingencyAnalysisDriver(grid=grid_gc,
                                           options=opts,
                                           engine=vg.EngineType.GSLV)
    driver2.run()
    Pf2 = driver2.results.Sf.real

    ok = np.allclose(Pf1, Pf2, atol=1e-4)
    assert ok


def test_gslv_contingencies_ts():
    """

    :return:
    """

    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', "IEEE39_1W.gridcal")

    print(f"Testing: {fname}")

    grid_gc = vg.open_file(filename=fname)

    opts = vg.ContingencyAnalysisOptions(
        pf_options=vg.PowerFlowOptions(solver_type=vg.SolverType.NR),
        contingency_method=vg.ContingencyMethod.PowerFlow
    )

    # Native engine
    driver1 = vg.ContingencyAnalysisTimeSeriesDriver(grid=grid_gc,
                                                     options=opts,
                                                     engine=vg.EngineType.VeraGrid)
    driver1.run()
    Pf1 = driver1.results.max_flows.real

    driver2 = vg.ContingencyAnalysisTimeSeriesDriver(grid=grid_gc,
                                                     options=opts,
                                                     engine=vg.EngineType.GSLV)
    driver2.run()
    Pf2 = driver2.results.max_flows.real

    print()
