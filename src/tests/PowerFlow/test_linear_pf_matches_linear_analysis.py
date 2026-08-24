# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as gce
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import multi_island_pf_nc
from VeraGridEngine.Simulations.LinearFactors.linear_analysis import LinearAnalysis
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import TapPhaseControl


def test_linear_pf_matches_linear_analysis_with_tap_control() -> None:
    """
    The linear power flow and the linear analysis are the same DC model, so fed with the
    same specified injections they must produce the same branch flows.
    """
    fname = os.path.join('data', 'grids', 'IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal')
    grid = gce.open_file(fname)

    # a controlled phase shifter is what routes the solve to the AC/DC linear formulation
    grid.transformers2w[6].tap_phase_control_mode = TapPhaseControl.Pf

    nc = compile_numerical_circuit_at(grid, t_idx=None)
    assert bool(nc.active_branch_data.any_pf_control), "the fixture must have tap controls"
    assert np.any(np.abs(nc.bus_data.Vbus) != 1.0), "the fixture must have non flat seed voltages"

    pf_res = multi_island_pf_nc(nc=nc, options=gce.PowerFlowOptions(solver_type=gce.SolverType.Linear))

    lin = LinearAnalysis(nc=nc, distributed_slack=False, correct_values=False, logger=Logger())

    # feed the linear analysis exactly what its driver feeds it
    s_hvdc, losses_hvdc, pf_hvdc, pt_hvdc, load_hvdc, n_free = nc.hvdc_data.get_power(
        Sbase=nc.Sbase,
        theta=np.zeros(nc.nbus)
    )
    injections = nc.get_linear_power_injections().real
    lin_flows = lin.get_flows(Sbus=injections, P_hvdc=-pf_hvdc * nc.Sbase)

    # the two models differ only by the fake converter admittances of the PTDF network,
    # which is just a few MW
    diff = np.abs(pf_res.Sf.real - lin_flows)
    assert np.max(diff) < 5.0, f"linear PF and linear analysis disagree by {np.max(diff)} MW"

    # no branch can carry a flow that its rating cannot explain
    rates = nc.passive_branch_data.rates
    loading = np.abs(pf_res.Sf.real) / (rates + 1e-9)
    assert np.max(loading) < 10.0, f"implausible branch loading of {np.max(loading) * 100} %"
