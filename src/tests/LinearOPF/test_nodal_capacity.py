# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import copy
import os
import VeraGridEngine.api as gce
from VeraGridEngine.Simulations.OPF.Formulations.linear_opf_ts import run_linear_opf_ts
from VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_driver import NodalCapacityDriver
from VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_options import NodalCapacityOptions
from VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_ts_driver import NodalCapacityTimeSeriesDriver
import numpy as np


def test_linear_ncap_load_hosting_snapshot():
    """
    IEEE14
    """
    fname = os.path.join('data', 'grids', 'IEEE 14 zip costs.gridcal')

    grid = gce.FileOpen(fname).open()

    # Linear OPF
    res, model = run_linear_opf_ts(grid=grid,
                                   dispatch_mode=gce.OpfDispatchMode.NodalCapacity,
                                   time_indices=None,
                                   nodal_capacity_sign=-1.0,
                                   capacity_nodes_idx=np.array([10, 11]))

    print('P nodal capacity: ', res.nodal_capacity_vars.P)
    print('P generators: ', res.gen_vars.p)
    print('P loads: ', res.load_vars.shedding)
    print('P slacks pos: ', res.branch_vars.flow_slacks_pos)
    print('P slacks neg: ', res.branch_vars.flow_slacks_neg)
    print('')

    assert np.all(res.nodal_capacity_vars.P[0, :] > 0.0)


def test_linear_ncap_is_invariant_to_slack_choice():
    fname = os.path.join('data', 'grids', 'IEEE 14 zip costs.gridcal')
    grid = gce.FileOpen(fname).open()
    alt_grid = copy.deepcopy(grid)
    alt_grid.buses[0].is_slack = False
    alt_grid.buses[1].is_slack = True

    base_res, model = run_linear_opf_ts(grid=grid,
                                        dispatch_mode=gce.OpfDispatchMode.NodalCapacity,
                                        time_indices=None,
                                        nodal_capacity_sign=-1.0,
                                        capacity_nodes_idx=np.array([10, 11]))
    alt_res, model = run_linear_opf_ts(grid=alt_grid,
                                       dispatch_mode=gce.OpfDispatchMode.NodalCapacity,
                                       time_indices=None,
                                       nodal_capacity_sign=-1.0,
                                       capacity_nodes_idx=np.array([10, 11]))

    assert np.allclose(base_res.nodal_capacity_vars.P, alt_res.nodal_capacity_vars.P, rtol=1e-5, atol=1e-5)


def test_linear_ncap_sign_controls_injection_vs_load():
    fname = os.path.join('data', 'grids', 'IEEE 14 zip costs.gridcal')
    grid = gce.FileOpen(fname).open()

    load_res, model = run_linear_opf_ts(grid=grid,
                                        dispatch_mode=gce.OpfDispatchMode.NodalCapacity,
                                        time_indices=None,
                                        nodal_capacity_sign=-1.0,
                                        capacity_nodes_idx=np.array([10, 11]))
    gen_res, model = run_linear_opf_ts(grid=grid,
                                       dispatch_mode=gce.OpfDispatchMode.NodalCapacity,
                                       time_indices=None,
                                       nodal_capacity_sign=1.0,
                                       capacity_nodes_idx=np.array([10, 11]))

    assert np.all(load_res.nodal_capacity_vars.P > 0.0)
    assert np.all(gen_res.nodal_capacity_vars.P > 0.0)
    assert np.sum(load_res.gen_vars.p) > np.sum(gen_res.gen_vars.p)


def test_linear_ncap_three_selected_buses_have_generation_and_load_hosting():
    fname = os.path.join('data', 'grids', 'New.England_solar_case_OPF.gridcal')
    grid = gce.FileOpen(fname).open()

    cap_buses = np.array([1, 4, 5])

    gen_drv = NodalCapacityDriver(
        grid=grid,
        options=NodalCapacityOptions(capacity_nodes_idx=cap_buses, nodal_capacity_sign=1.0),
    )
    load_drv = NodalCapacityDriver(
        grid=grid,
        options=NodalCapacityOptions(capacity_nodes_idx=cap_buses, nodal_capacity_sign=-1.0),
    )

    gen_res = gen_drv.linear_opf(remote=True)
    load_res = load_drv.linear_opf(remote=True)

    assert np.all(gen_res.nodal_capacity > 0.0)
    assert np.all(load_res.nodal_capacity <= 0.0)
    assert np.any(load_res.nodal_capacity < 0.0)
    assert len(np.unique(np.round(gen_res.nodal_capacity, 6))) > 1
    assert len(np.unique(np.round(load_res.nodal_capacity[load_res.nodal_capacity < 0.0], 6))) >= 1


def test_linear_ncap_time_series_reports_per_bus_values():
    fname = os.path.join('data', 'grids', 'New.England_solar_case_OPF.gridcal')
    grid = gce.FileOpen(fname).open()

    cap_buses = np.array([1, 4, 5])
    gen_drv = NodalCapacityTimeSeriesDriver(
        grid=grid,
        options=NodalCapacityOptions(capacity_nodes_idx=cap_buses, nodal_capacity_sign=1.0),
        time_indices=np.array([0]),
    )
    load_drv = NodalCapacityTimeSeriesDriver(
        grid=grid,
        options=NodalCapacityOptions(capacity_nodes_idx=cap_buses, nodal_capacity_sign=-1.0),
        time_indices=np.array([0]),
    )

    gen_res = gen_drv.linear_opf(remote=True)
    load_res = load_drv.linear_opf(remote=True)

    assert gen_res.nodal_capacity.shape == (1, 3)
    assert load_res.nodal_capacity.shape == (1, 3)
    assert np.all(gen_res.nodal_capacity[0, :] > 0.0)
    assert np.all(load_res.nodal_capacity[0, :] <= 0.0)
    assert np.any(load_res.nodal_capacity[0, :] < 0.0)
    assert len(np.unique(np.round(gen_res.nodal_capacity[0, :], 6))) > 1


if __name__ == "__main__":
    test_linear_ncap_load_hosting_snapshot()
