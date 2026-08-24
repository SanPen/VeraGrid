# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as gce
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import multi_island_pf_nc


def test_linear_analysis_models_the_droop_and_its_saturation() -> None:
    """
    The linear analysis must represent the converters by the power they actually move,
    including the P-mode 3 droop law and the rating that limits it, instead of replacing
    them by an equivalent admittance which does not account for potential saturation.
    """
    fname = os.path.join('data', 'grids', 'NTC_8_bus_2pmode3_dc_bottleneck.veragrid')
    grid = gce.open_file(fname)

    driver = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions())
    driver.run()
    lin_flows = driver.results.Sf.real if np.iscomplexobj(driver.results.Sf) else driver.results.Sf

    nc = compile_numerical_circuit_at(grid, t_idx=None)
    assert nc.vsc_data.nelm > 0, "must contain converters"
    pf_res = multi_island_pf_nc(nc=nc, options=gce.PowerFlowOptions(solver_type=gce.SolverType.Linear))

    usable = (nc.passive_branch_data.active.astype(bool)
              & np.isfinite(lin_flows)
              & np.isfinite(pf_res.Sf.real))
    max_error = float(np.max(np.abs(pf_res.Sf.real - lin_flows)[usable]))
    assert max_error < 5.0, f"the linear analysis is {max_error} MW away from the linear power flow"

    # no converter may exceed its rating, which is what the saturation is about
    for m in range(nc.vsc_data.nelm):
        if nc.vsc_data.active[m]:
            power = abs(float(pf_res.Pfp_vsc[m]))
            assert power <= float(nc.vsc_data.rates[m]) + 1e-6
        else:
            pass  # an inactive converter carries nothing
