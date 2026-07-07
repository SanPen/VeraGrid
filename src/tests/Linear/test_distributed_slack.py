# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Regression tests for distributed-slack PTDF.

There was a historical bug where make_ptdf, make_acdc_ptdfand  make_ac_ptdf
used a participation vector (-1/(n-1) on the n-1 other buses, but
0 on the column bus itself instead of a single uniform participation
factor (1/n on every bus). For a balanced injection, sum(P)=0, this
scaled the resulting flows by n/(n-1) compared to the fixed-slack
solution, so the reconstructed bus injections did not fully match the
input. The fix uses the standard convention dP[i, j] = delta_ij - 1/n.
"""
import numpy as np
import pytest
import VeraGridEngine.api as gce
from VeraGridEngine import LinearAnalysis


def _build_balanced_5bus_grid() -> gce.MultiCircuit:
    """
    5-bus mesh, all reactances equal, with slack at bus 0
    """
    grid = gce.MultiCircuit(Sbase=100.0)

    buses = [
        gce.Bus(name=f"B{i}", is_slack=(i == 0)) for i in range(5)
    ]

    for b in buses:
        grid.add_bus(b)

    # mesh: 0-1, 1-2, 2-3, 3-4, 0-4, 1-3
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4), (1, 3)]
    for f, t in edges:
        grid.add_line(gce.Line(bus_from=buses[f], bus_to=buses[t],
                               name=f"Line {f}-{t}", r=1e-6, x=0.1, rate=9999.0))

    # balanced injection: 100 MW gen at bus 0, 60 MW load at bus 2, 40 MW load at bus 4
    grid.add_generator(buses[0], gce.Generator(name="G0", P=100.0, vset=1.0))
    grid.add_load(buses[2], gce.Load(name="L2", P=60.0))
    grid.add_load(buses[4], gce.Load(name="L4", P=40.0))

    return grid


def test_distributed_slack_matches_fixed_on_balanced_grid():
    """
    On a balanced grid where sum(P)=0 to begin with, distributed and fixed 
    slack must produce identical branch flows
    """
    grid = _build_balanced_5bus_grid()
    nc = gce.compile_numerical_circuit_at(grid)

    Sbus = nc.get_power_injections_pu().real * nc.Sbase
    assert abs(Sbus.sum()) < 1e-9, "test grid is not balanced"

    lin_fixed = LinearAnalysis(nc=nc, distributed_slack=False)
    lin_dist = LinearAnalysis(nc=nc, distributed_slack=True)

    flow_fixed = lin_fixed.get_flows(Sbus)
    flow_dist = lin_dist.get_flows(Sbus)

    assert np.allclose(flow_fixed, flow_dist, atol=1e-6), (
        f"Different flows, fixed = {flow_fixed},  dist  = {flow_dist}"
    )


def test_distributed_slack_kcl_balanced_grid():
    """
    Branch flows from distributed-slack PTDF must satisfy Kirchhoff at every
    bus on a balanced grid: (Cf - Ct).T @ flow == Sbus.
    """
    grid = _build_balanced_5bus_grid()
    nc = gce.compile_numerical_circuit_at(grid)

    Sbus = nc.get_power_injections_pu().real * nc.Sbase

    lin_dist = LinearAnalysis(nc=nc, distributed_slack=True)
    flow = lin_dist.get_flows(Sbus)

    Cft = (nc.passive_branch_data.Cf - nc.passive_branch_data.Ct).tocsc()
    reconstructed = Cft.T @ flow

    assert np.allclose(reconstructed, Sbus, atol=1e-6), (
        f"KCL violated under distributed slack:\n"
        f"  Sbus           = {Sbus}\n"
        f"  C^T @ flow_dist = {reconstructed}"
    )


@pytest.mark.skip()
def test_ptdf_columns_sum_to_zero_distributed_slack():
    """
    With uniform-participation distributed slack, every PTDF column
    represents an injection vector with zero net power, so the column
    induces no net imbalance.
    """
    grid = _build_balanced_5bus_grid()
    nc = gce.compile_numerical_circuit_at(grid)

    lin = LinearAnalysis(nc=nc, distributed_slack=True)
    n = nc.nbus
    uniform_injection = np.ones(n)
    flow = lin.PTDF @ uniform_injection

    assert np.allclose(flow, 0.0, atol=1e-9), (
        f"PTDF @ 1 should be zero with distributed slack, got {flow}"
    )
