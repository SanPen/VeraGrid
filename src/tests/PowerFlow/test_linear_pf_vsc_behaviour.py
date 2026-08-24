# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as gce
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import multi_island_pf_nc


def test_linear_pf_vsc_matches_the_ac_power_flow() -> None:
    """
    The reference is the full AC power flow of the same grid, which models the converters
    exactly. Ignoring the converters used to leave a mean flow error above 10 MW on this
    grid.
    """
    fname = os.path.join('data', 'grids', 'test_ieee_14_VSC.veragrid')
    grid = gce.open_file(fname)
    nc = compile_numerical_circuit_at(grid, t_idx=None)
    assert nc.vsc_data.nelm > 0, "the fixture must contain converters"

    ac_res = multi_island_pf_nc(nc=nc, options=gce.PowerFlowOptions(solver_type=gce.SolverType.NR,
                                                                    max_iter=40,
                                                                    tolerance=1e-8,
                                                                    control_q=False))
    assert bool(np.all(ac_res.converged)), "the AC reference power flow must converge"

    lin_res = multi_island_pf_nc(nc=nc, options=gce.PowerFlowOptions(solver_type=gce.SolverType.Linear))

    # compare on the active AC branches, where the DC approximation is meaningful
    is_ac = (~nc.passive_branch_data.dc.astype(bool)) & nc.passive_branch_data.active.astype(bool)
    usable = is_ac & np.isfinite(lin_res.Sf.real) & np.isfinite(ac_res.Sf.real)
    mean_error = float(np.mean(np.abs(lin_res.Sf.real - ac_res.Sf.real)[usable]))
    assert mean_error < 5.0, f"the linear power flow is {mean_error} MW away from the AC one"

    # the converters must carry their scheduled power, with the sign of the AC solution
    for m in range(nc.vsc_data.nelm):
        p_linear = float(lin_res.Pfp_vsc[m])
        p_ac = float(np.real(ac_res.Pfp_vsc[m]))
        assert abs(p_linear - p_ac) < 1.0, (f"converter {nc.vsc_data.names[m]} carries {p_linear} MW "
                                            f"while the AC power flow gives {p_ac} MW")


def test_linear_pf_droop_converter_saturates_at_its_rate() -> None:
    """
    A Pmode3 converter follows its droop law only up to its rating.
    """
    fname = os.path.join('data', 'grids', 'NTC_8_bus_2pmode3_dc_bottleneck.veragrid')
    grid = gce.open_file(fname)
    nc = compile_numerical_circuit_at(grid, t_idx=None)

    lin_res = multi_island_pf_nc(nc=nc, options=gce.PowerFlowOptions(solver_type=gce.SolverType.Linear))

    for m in range(nc.vsc_data.nelm):
        if nc.vsc_data.active[m]:
            power = abs(float(lin_res.Pfp_vsc[m]))
            rate = float(nc.vsc_data.rates[m])
            assert power <= rate + 1e-6, (f"converter {nc.vsc_data.names[m]} carries {power} MW "
                                          f"beyond its {rate} MW rating")
        else:
            pass  # an inactive converter carries nothing
