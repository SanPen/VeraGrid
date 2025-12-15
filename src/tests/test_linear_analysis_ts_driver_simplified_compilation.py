# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import os

import numpy as np
import VeraGridEngine as vg


def test_linear_analysis_ts_driver_simplified_compilation_matches_full_compilation():
    """
    The simplified compilation path must honor the LinearAnalysisOptions (especially distribute_slack),
    otherwise the resulting flows/injections can be inconsistent.
    """
    tests_dir = os.path.dirname(__file__)
    fname = os.path.join(tests_dir, "data", "grids", "IEEE39_1W.gridcal")
    grid = vg.open_file(fname)

    # Explicitly use the default behavior expected by LinearAnalysisOptions (distribute_slack=False)
    opts = vg.LinearAnalysisOptions(distribute_slack=False, correct_values=False)
    time_idx = grid.get_all_time_indices()[:10]

    drv_fast = vg.LinearAnalysisTimeSeriesDriver(
        grid=grid,
        options=opts,
        time_indices=time_idx,
        simplified_compilation=True,
    )
    drv_fast.run()

    drv_full = vg.LinearAnalysisTimeSeriesDriver(
        grid=grid,
        options=opts,
        time_indices=time_idx,
        simplified_compilation=False,
    )
    drv_full.run()

    assert np.allclose(drv_fast.results.Sf.real, drv_full.results.Sf.real, atol=1e-6, rtol=1e-6)


