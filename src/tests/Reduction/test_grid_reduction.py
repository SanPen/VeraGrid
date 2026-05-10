# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as gce
from VeraGridEngine.Topology.GridReduction.ptdf_grid_reduction import ptdf_reduction, ptdf_reduction_projected
from VeraGridEngine.Topology.GridReduction.ward_equivalents import ward_standard_reduction
from VeraGridEngine.Topology.GridReduction.di_shi_grid_reduction import di_shi_reduction


def get_total_generation(grid: gce.MultiCircuit) -> float:
    """
    Get total generation for snapshot
    :param grid: MultiCircuit instance
    :return: Total generation in MW
    """
    total = 0.0
    for gen in grid.generators:
        total += gen.P * gen.active
    for batt in grid.batteries:
        total += batt.P * batt.active
    for stagen in grid.static_generators:
        total += stagen.P * stagen.active
    return total


def get_total_load(grid: gce.MultiCircuit) -> float:
    """
    Get total load for snapshot
    :param grid: MultiCircuit instance
    :return: Total load in MW
    """
    total = 0.0
    for load in grid.loads:
        total += load.P * load.active
    return total


def get_total_generation_ts(grid: gce.MultiCircuit, time_indices: np.ndarray = None) -> np.ndarray:
    """
    Get total generation profile for time series
    :param grid: MultiCircuit instance
    :param time_indices: Optional array of time indices to select
    :return: Total generation profile in MW (nt,)
    """
    if time_indices is None:
        time_indices = grid.get_all_time_indices()
    
    nt = len(time_indices)
    total = np.zeros(nt, dtype=float)
    
    for gen in grid.generators:
        if gen.P_prof is not None:
            prof = gen.P_prof.toarray()[time_indices] * gen.active_prof.toarray()[time_indices]
            total += prof
    
    for batt in grid.batteries:
        if batt.P_prof is not None:
            prof = batt.P_prof.toarray()[time_indices] * batt.active_prof.toarray()[time_indices]
            total += prof
    
    for stagen in grid.static_generators:
        if stagen.P_prof is not None:
            prof = stagen.P_prof.toarray()[time_indices] * stagen.active_prof.toarray()[time_indices]
            total += prof
    
    return total


def get_total_load_ts(grid: gce.MultiCircuit, time_indices: np.ndarray = None) -> np.ndarray:
    """
    Get total load profile for time series
    :param grid: MultiCircuit instance
    :param time_indices: Optional array of time indices to select
    :return: Total load profile in MW (nt,)
    """
    if time_indices is None:
        time_indices = grid.get_all_time_indices()
    
    nt = len(time_indices)
    total = np.zeros(nt, dtype=float)
    
    for load in grid.loads:
        if load.P_prof is not None:
            prof = load.P_prof.toarray()[time_indices] * load.active_prof.toarray()[time_indices]
            total += prof
    
    return total


def test_ward_reduction():
    """
    Test to check the PTDF reduction
    :return:
    """
    fname = os.path.join('data', 'grids', 'Matpower', 'case89pegase.matpower')
    grid = gce.open_file(filename=fname)

    remove_bus_idx = np.array([21, 36, 44, 50, 53])
    expected_boundary_idx = np.sort(np.array([20, 77, 15, 32]))

    external, boundary, internal, boundary_branches, internal_branches = grid.get_reduction_sets(reduction_bus_indices=remove_bus_idx)

    assert np.equal(expected_boundary_idx, boundary).all()

    pf_options = gce.PowerFlowOptions(solver_type=gce.SolverType.Linear)

    pf_res = gce.power_flow(grid=grid, options=pf_options)

    # gce.ward_reduction(grid=grid, reduction_bus_indices=remove_bus_idx, pf_res=pf_res)
    nc = gce.compile_numerical_circuit_at(circuit=grid, t_idx=None)
    lin = gce.LinearAnalysis(nc=nc)

    P0 = grid.get_Pbus()
    Flows0 = lin.get_flows(P0)

    # if grid.has_time_series:
    #     lin_ts = gce.LinearAnalysisTs(grid=grid)
    # else:
    #     lin_ts = None

    grid2, logger = ptdf_reduction(grid=grid,
                                   reduction_bus_indices=remove_bus_idx)

    nc2 = gce.compile_numerical_circuit_at(circuit=grid2, t_idx=None)
    lin2 = gce.LinearAnalysis(nc=nc2)

    # proof that the flows are actually the same
    Pbus4 = grid.get_Pbus()
    Flows4 = lin2.PTDF @ Pbus4
    diff = Flows0[internal_branches] - Flows4

    ok = np.allclose(Flows4, Flows0[internal_branches], atol=1e-10)
    assert ok

    
def test_ptdf_projected_14_reduction():
    """
    Test to check the PTDF projected reduction
    :return:
    """
    remove_bus_idx_list = [np.array([8, 11]), 
                           np.array([9, 10]),
                           np.array([8, 11, 9, 10]),
                           np.array([0, 1, 2])]

    pf_options = gce.PowerFlowOptions(solver_type=gce.SolverType.NR)

    # Open a new grid instance every time
    # Check the reduction works with any combination of buses to remove
    for remove_bus_idx in remove_bus_idx_list:
        fname = os.path.join('data', 'grids', 'case14_to_reduce.veragrid')
        grid = gce.open_file(filename=fname)
        red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=remove_bus_idx)
        pf_res_reduced = gce.power_flow(grid=red_grid, options=pf_options)

        assert pf_res_reduced.converged

    return None

    
def test_ptdf_projected_14_complex_reduction():
    """
    Test to check the PTDF projected reduction
    :return:
    """
    remove_bus_idx_list = [np.array([8, 11]), 
                           np.array([9, 10]),
                           np.array([8, 11, 9, 10]),
                           np.array([0, 1, 2]),
                           np.array([21]),
                           np.array([14, 17]),
                           np.array([14, 17, 21]),
                           np.array([21, 14, 17, 0, 3])]

    pf_options = gce.PowerFlowOptions(solver_type=gce.SolverType.NR)

    # Open a new grid instance every time
    # Check the reduction works with any combination of buses to remove
    for remove_bus_idx in remove_bus_idx_list:
        fname = os.path.join('data', 'grids', 'case14_complex_to_reduce.veragrid')
        # fname = os.path.join('src', 'tests', 'data', 'grids', 'case14_complex_to_reduce.veragrid')
        grid = gce.open_file(filename=fname)
        red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=remove_bus_idx)
        pf_res_reduced = gce.power_flow(grid=red_grid, options=pf_options)

        assert pf_res_reduced.converged


def test_ptdf_projected_14_complex_inactive_reduction():
    """
    Test to check the PTDF projected reduction
    :return:
    """
    remove_bus_idx_list = [np.array([8, 11]), 
                           np.array([9, 10]),
                           np.array([8, 11, 9, 10]),
                           np.array([0, 1, 2]),
                           np.array([21]),
                           np.array([14, 17]),
                           np.array([14, 17, 21]),
                           np.array([21, 14, 17, 0, 3]),
                           np.array([22]),
                           np.array([22, 21]),
                           np.array([22, 21, 14, 17]),
                           np.array([22, 21, 14, 4])]

    pf_options = gce.PowerFlowOptions(solver_type=gce.SolverType.NR)

    # Open a new grid instance every time
    # Check the reduction works with any combination of buses to remove
    for remove_bus_idx in remove_bus_idx_list:
        fname = os.path.join('data', 'grids', 'case14_to_reduce_inactive.veragrid')
        # fname = os.path.join('src', 'tests', 'data', 'grids', 'case14_to_reduce_inactive.veragrid')
        grid = gce.open_file(filename=fname)
        red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=remove_bus_idx)
        pf_res_reduced = gce.power_flow(grid=red_grid, options=pf_options)

        assert pf_res_reduced.converged

        
def test_ptdf_projected():
    """
    Test to check the PTDF projected reduction in a very simple grid
    :return:
    """
    fname = os.path.join('data', 'grids', '5bus_linear.veragrid')
    # fname = os.path.join('src', 'tests', 'data', 'grids', '5bus_linear.veragrid')
    grid = gce.open_file(filename=fname)

    # First run basic linear analysis
    flows_dr = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr.run()
    flows_branches = flows_dr.results.Sf

    # Then reduce the network
    bus_to_remove = np.array([1])
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    flows_dr_red = gce.LinearAnalysisDriver(grid=red_grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr_red.run()
    flows_branches_red = flows_dr_red.results.Sf

    # print(flows_branches[[2, 3, 4, 5, 6]])
    # print(flows_branches_red)

    assert np.allclose(flows_branches[[2, 3, 4, 5, 6]], flows_branches_red, atol=1e-5)

    
def test_ptdf_projected_slack_remove():
    """
    Test to check the PTDF projected reduction in a very simple grid where we remove the slack
    :return:
    """
    fname = os.path.join('data', 'grids', '5bus_linear.veragrid')
    # fname = os.path.join('src', 'tests', 'data', 'grids', '5bus_linear.veragrid')
    grid = gce.open_file(filename=fname)

    P_original_gen = 0.0
    for gen in grid.generators:
        P_original_gen += gen.P

    P_original_load = 0.0
    for load in grid.loads:
        P_original_load += load.P

    # First run basic linear analysis
    flows_dr = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr.run()
    flows_branches = flows_dr.results.Sf

    # Then reduce the network
    bus_to_remove = np.array([0])
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    flows_dr_red = gce.LinearAnalysisDriver(grid=red_grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr_red.run()
    flows_branches_red = flows_dr_red.results.Sf

    P_reduced_gen = 0.0
    for gen in red_grid.generators:
        P_reduced_gen += gen.P

    P_reduced_load = 0.0
    for load in red_grid.loads:
        P_reduced_load += load.P

    net_original = P_original_gen - P_original_load
    net_reduced = P_reduced_gen - P_reduced_load

    # print(flows_branches[[1, 2, 3, 7]])
    # print(flows_branches_red)

    assert abs(net_reduced) < 1e-4
    assert abs(net_original - net_reduced) < 1e-4

    assert np.allclose(flows_branches[[1, 2, 3, 7]], flows_branches_red, atol=1e-5)


def test_ptdf_projected_slack_remove_with_load():
    """
    Test to check the PTDF projected reduction in a very simple grid where we remove the slack
    :return:
    """
    fname = os.path.join('data', 'grids', '5bus_linear_load.veragrid')
    # fname = os.path.join('src', 'tests', 'data', 'grids', '5bus_linear_load.veragrid')
    grid = gce.open_file(filename=fname)

    P_original_gen = 0.0
    for gen in grid.generators:
        P_original_gen += gen.P

    P_original_load = 0.0
    for load in grid.loads:
        P_original_load += load.P

    # First run basic linear analysis
    flows_dr = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr.run()
    flows_branches = flows_dr.results.Sf

    # Then reduce the network
    bus_to_remove = np.array([0])
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    flows_dr_red = gce.LinearAnalysisDriver(grid=red_grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr_red.run()
    flows_branches_red = flows_dr_red.results.Sf

    P_reduced_gen = 0.0
    for gen in red_grid.generators:
        P_reduced_gen += gen.P

    P_reduced_load = 0.0
    for load in red_grid.loads:
        P_reduced_load += load.P

    net_original = P_original_gen - P_original_load
    net_reduced = P_reduced_gen - P_reduced_load

    # print(flows_branches[[1, 2, 3, 7]])
    # print(flows_branches_red)

    assert abs(net_reduced) < 1e-4
    assert abs(net_original - net_reduced) < 1e-4

    assert np.allclose(flows_branches[[1, 2, 3, 7]], flows_branches_red, atol=1e-5)

    
def test_reduction_flows():
    """
    Test to check the reduction flows
    :return:
    """
    # fname = os.path.join('data', 'grids', 'Matpower', 'case14.matpower')
    fname = os.path.join('data', 'grids', 'Matpower', 'case14.matpower')
    grid = gce.open_file(filename=fname)
    pf_options = gce.PowerFlowOptions(solver_type=gce.SolverType.NR)

    # Original power flow
    pf_original_res = gce.power_flow(grid=grid, options=pf_options)

    reduction_buses = np.array([10, 13])

    # Reduced grid with ward equivalent
    fname = os.path.join('data', 'grids', 'Matpower', 'case14.matpower')
    grid = gce.open_file(filename=fname)
    red_grid, logger = ward_standard_reduction(grid=grid,
                                               reduction_bus_indices=reduction_buses,
                                               V0=pf_original_res.voltage)
    pf_reduced_res = gce.power_flow(grid=red_grid, options=pf_options)
    Vabs_ward = np.array([1.06, 1.045, 1.01, 1.01756835, 1.01944961, 1.07, 1.06120408, 1.09, 1.0553105, 1.05036322, 1.05532085, 1.05064385])
    assert np.allclose(abs(pf_reduced_res.voltage), Vabs_ward, atol=1e-4)

    # Reduced grid with di-shi equivalent
    fname = os.path.join('data', 'grids', 'Matpower', 'case14.matpower')
    grid = gce.open_file(filename=fname)
    red_grid, logger = di_shi_reduction(grid=grid,
                                        reduction_bus_indices=reduction_buses,
                                        V0=pf_original_res.voltage)
    pf_reduced_res = gce.power_flow(grid=red_grid, options=pf_options)
    Vabs_dishi = np.array([1.06, 1.045, 1.01, 1.01767086, 1.01951387, 1.07, 1.06151954, 1.09, 1.05593173, 1.05098464, 1.05518856, 1.05038172])
    assert np.allclose(abs(pf_reduced_res.voltage), Vabs_dishi, atol=1e-4)

    # Reduced grid with ptdf equivalent
    fname = os.path.join('data', 'grids', 'Matpower', 'case14.matpower')
    grid = gce.open_file(filename=fname)
    red_grid, logger = ptdf_reduction(grid=grid,
                                        reduction_bus_indices=reduction_buses)
    pf_reduced_res = gce.power_flow(grid=red_grid, options=pf_options)
    Vabs_ptdf = np.array([1.06, 1.045, 1.01, 1.01681086, 1.01909534, 1.07, 1.05882555, 1.09, 1.05065242, 1.04419659, 1.05618558, 1.05230889])
    assert np.allclose(abs(pf_reduced_res.voltage), Vabs_ptdf, atol=1e-4)


def test_ptdf_projected_balances():
    """
    Test to check the reduction flows and check 3 things:
    1. Flows that match in the before and after reduction
    2. Generation being added and load being added is as close as 0 as possible
    3. Total generation and demand are roughly the same
    :return:
    """

    fname = os.path.join('data', 'grids', 'ptdf_red_many_buses.veragrid')
    # fname = os.path.join('src', 'tests', 'data', 'grids', 'ptdf_red_many_buses.veragrid')
    grid = gce.open_file(filename=fname)

    P_original_gen = 0.0
    for gen in grid.generators:
        P_original_gen += gen.P

    P_original_load = 0.0
    for load in grid.loads:
        P_original_load += load.P

    # First run basic linear analysis
    flows_dr = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr.run()
    flows_branches = flows_dr.results.Sf

    # Then reduce the network
    bus_to_remove = np.array([6, 8])
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    flows_dr_red = gce.LinearAnalysisDriver(grid=red_grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr_red.run()
    flows_branches_red = flows_dr_red.results.Sf

    P_reduced_gen = 0.0
    for gen in red_grid.generators:
        P_reduced_gen += gen.P

    P_reduced_load = 0.0
    for load in red_grid.loads:
        P_reduced_load += load.P

    # Check net balance instead of gross balance, as reduction adds compensation power
    net_original = P_original_gen - P_original_load
    net_reduced = P_reduced_gen - P_reduced_load
    
    assert np.allclose(flows_branches[[0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13]], flows_branches_red, atol=1e-4)
    
    assert abs(net_reduced) < 1e-4
    assert abs(P_original_gen - P_reduced_gen) < 1e-4
    assert abs(P_original_load - P_reduced_load) < 1e-4


def test_ptdf_projected_antena():
    """
    Test to check if only the necessary injection is added
    :return:
    """

    fname = os.path.join('data', 'grids', '6bus_antena.veragrid')
    # fname = os.path.join('src', 'tests', 'data', 'grids', '6bus_antena.veragrid')
    grid = gce.open_file(filename=fname)

    grid.buses[0].is_slack = True

    P_original_gen = 0.0
    for gen in grid.generators:
        P_original_gen += gen.P

    P_original_load = 0.0
    for load in grid.loads:
        P_original_load += load.P

    # First run basic linear analysis
    flows_dr = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr.run()
    flows_branches = flows_dr.results.Sf

    # Then reduce the network
    bus_to_remove = np.array([1])
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    flows_dr_red = gce.LinearAnalysisDriver(grid=red_grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr_red.run()
    flows_branches_red = flows_dr_red.results.Sf

    P_reduced_gen = 0.0
    for gen in red_grid.generators:
        P_reduced_gen += gen.P

    P_reduced_load = 0.0
    for load in red_grid.loads:
        P_reduced_load += load.P

    # Check net balance instead of gross balance, as reduction adds compensation power
    net_original = P_original_gen - P_original_load
    net_reduced = P_reduced_gen - P_reduced_load
    
    assert np.allclose(flows_branches[[1, 2, 3, 4, 5]], flows_branches_red, atol=1e-4)
    
    assert abs(net_reduced) < 1e-4
    assert abs(P_original_gen - P_reduced_gen) < 1e-4
    assert abs(P_original_load - P_reduced_load) < 1e-4

    assert abs(red_grid.loads[3].P - 10.0) < 1e-4


def test_ptdf_projected_gb():
    """
    Test to check if only the necessary injection is added
    :return:
    """

    fname = os.path.join('data', 'grids', 'gb_t0.veragrid')
    # fname = os.path.join('src', 'tests', 'data', 'grids', 'gb_t0.veragrid')
    grid = gce.open_file(filename=fname)

    # First run basic linear analysis
    flows_dr = gce.LinearAnalysisDriver(grid=grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr.run()
    flows_branches = flows_dr.results.Sf

    # Then reduce the network
    bus_to_remove = []
    bus_idx_dict = grid.get_bus_index_dict()
    for bus in grid.buses:
        if bus.Vnom < 400:
            bus_remove_idx = bus_idx_dict[bus]
            bus_to_remove.append(bus_remove_idx)

    bus_to_remove = np.array(bus_to_remove)

    # Determine internal branches before reduction
    external, boundary, internal, boundary_branches, internal_branches = grid.get_reduction_sets(reduction_bus_indices=bus_to_remove)

    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    flows_dr_red = gce.LinearAnalysisDriver(grid=red_grid, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr_red.run()
    flows_branches_red = flows_dr_red.results.Sf

    # Check that flows on remaining branches match
    assert np.allclose(flows_branches[internal_branches], flows_branches_red, atol=1e-4)

    # Check power balance: total generation and demand should not change
    P_orig_gen_total = get_total_generation(grid)
    P_orig_load_total = get_total_load(grid)
    P_red_gen_total = get_total_generation(red_grid)
    P_red_load_total = get_total_load(red_grid)
    
    assert abs(P_orig_gen_total - P_red_gen_total) < 1e-4, \
        "Total generation should not change after reduction"
    assert abs(P_orig_load_total - P_red_load_total) < 1e-4, \
        "Total demand should not change after reduction"


def test_ptdf_projected_ts():
    """
    Test to check the reduction flows with time series and check:
    1. Flows that match in the before and after reduction for all time steps
    2. Compensation elements have correct profiles
    :return:
    """

    # fname = os.path.join('src', 'tests', 'data', 'grids', 'ptdf_ts.veragrid')
    fname = os.path.join('data', 'grids', 'ptdf_ts.veragrid')
        
    grid = gce.open_file(filename=fname)

    # First run time series linear analysis
    lin_ts = gce.LinearAnalysisTs(grid=grid, distributed_slack=False)
    P_orig = grid.get_Pbus_prof()
    Flows_orig = lin_ts.get_flows_ts(P=P_orig)

    # Then reduce the network
    bus_to_remove = np.array([6, 8])
    
    # Get internal branches before reduction to compare later
    external, boundary, internal, boundary_branches, internal_branches = grid.get_reduction_sets(reduction_bus_indices=bus_to_remove)
    
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    
    # Run time series linear analysis on reduced grid
    lin_ts_red = gce.LinearAnalysisTs(grid=red_grid, distributed_slack=False)
    P_red = red_grid.get_Pbus_prof()
    Flows_red = lin_ts_red.get_flows_ts(P=P_red)

    # Compare flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]
    
    # Check if dimensions match
    assert Flows_red.shape[1] == len(internal_branches)

    # Compare flows
    assert np.allclose(Flows_orig_internal, Flows_red, atol=1e-4)


def test_ptdf_projected_ts_gb_full():
    """
    Test to check the reduction flows with time series and check:
    1. Flows that match in the before and after reduction for all time steps
    2. Compensation elements have correct profiles
    :return:
    """

    # fname = os.path.join('src', 'tests', 'data', 'grids', 'GB Network.veragrid')
    fname = os.path.join('data', 'grids', 'GB Network.gridcal')
        
    grid = gce.open_file(filename=fname)

    # First run time series linear analysis
    lin_ts = gce.LinearAnalysisTs(grid=grid, distributed_slack=False)
    P_orig = grid.get_Pbus_prof()
    Flows_orig = lin_ts.get_flows_ts(P=P_orig)

    # Then reduce the network
    bus_to_remove = []
    bus_idx_dict = grid.get_bus_index_dict()
    for bus in grid.buses:
        if bus.Vnom < 400:
            bus_remove_idx = bus_idx_dict[bus]
            bus_to_remove.append(bus_remove_idx)

    bus_to_remove = np.array(bus_to_remove)
    
    # Get internal branches before reduction to compare later
    external, boundary, internal, boundary_branches, internal_branches = grid.get_reduction_sets(reduction_bus_indices=bus_to_remove)
    
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    
    # Run time series linear analysis on reduced grid
    lin_ts_red = gce.LinearAnalysisTs(grid=red_grid, distributed_slack=False)
    P_red = red_grid.get_Pbus_prof()
    Flows_red = lin_ts_red.get_flows_ts(P=P_red)

    # Compare flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]
    
    # Check if dimensions match
    assert Flows_red.shape[1] == len(internal_branches)

    # Compare flows
    assert np.allclose(Flows_orig_internal, Flows_red, atol=1e-4)
    
    # Check power balance for all time steps: total generation and demand should not change
    all_time_indices = grid.get_all_time_indices()
    P_orig_gen_ts = get_total_generation_ts(grid, time_indices=all_time_indices)
    P_orig_load_ts = get_total_load_ts(grid, time_indices=all_time_indices)
    P_red_gen_ts = get_total_generation_ts(red_grid, time_indices=all_time_indices)
    P_red_load_ts = get_total_load_ts(red_grid, time_indices=all_time_indices)
    
    assert np.allclose(P_orig_gen_ts, P_red_gen_ts, atol=1e-4), \
        "Total generation should not change after reduction at any time step"
    assert np.allclose(P_orig_load_ts, P_red_load_ts, atol=1e-4), \
        "Total demand should not change after reduction at any time step"


def test_ptdf_projected_ts_gb_selected_middle_steps():
    """
    Test to check the reduction flows with time series for selected time steps in the middle of the year.
    Performs grid reduction for 3 hours that are neither the first nor the last ones.
    :return:
    """
    fname = os.path.join('data', 'grids', 'GB Network.gridcal')
    grid = gce.open_file(filename=fname)

    # Get all available time indices
    all_time_indices = grid.get_all_time_indices()
    n_times = len(all_time_indices)
    
    # Select 3 time steps in the middle (not first, not last)
    middle_idx = n_times // 2
    selected_time_indices = np.array([
        middle_idx - 1,
        middle_idx,
        middle_idx + 1
    ])
    
    # Ensure indices are valid and not at the boundaries
    assert selected_time_indices[0] > 0
    assert selected_time_indices[-1] < n_times - 1
    
    # First run time series linear analysis for selected time steps only
    lin_ts = gce.LinearAnalysisTs(grid=grid, distributed_slack=False, time_indices=selected_time_indices)
    P_orig_full = grid.get_Pbus_prof()
    P_orig = P_orig_full[selected_time_indices, :]  # Select only the time steps we're testing
    Flows_orig = lin_ts.get_flows_ts(P=P_orig)

    # Then reduce the network
    bus_to_remove = []
    bus_idx_dict = grid.get_bus_index_dict()
    for bus in grid.buses:
        if bus.Vnom < 400:
            bus_remove_idx = bus_idx_dict[bus]
            bus_to_remove.append(bus_remove_idx)

    bus_to_remove = np.array(bus_to_remove)
    
    # Get internal branches before reduction to compare later
    external, boundary, internal, boundary_branches, internal_branches = grid.get_reduction_sets(reduction_bus_indices=bus_to_remove)
    
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    
    # Run time series linear analysis on reduced grid for the same selected time steps
    lin_ts_red = gce.LinearAnalysisTs(grid=red_grid, distributed_slack=False, time_indices=selected_time_indices)
    P_red_full = red_grid.get_Pbus_prof()
    P_red = P_red_full[selected_time_indices, :]  # Select only the time steps we're testing
    Flows_red = lin_ts_red.get_flows_ts(P=P_red)

    # Compare flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]
    
    # Check if dimensions match
    assert Flows_red.shape[0] == len(selected_time_indices)
    assert Flows_red.shape[1] == len(internal_branches)

    # Compare flows for the selected time steps
    assert np.allclose(Flows_orig_internal, Flows_red, atol=1e-4)
    
    # Check power balance for selected time steps: total generation and demand should not change
    P_orig_gen_ts = get_total_generation_ts(grid, time_indices=selected_time_indices)
    P_orig_load_ts = get_total_load_ts(grid, time_indices=selected_time_indices)
    P_red_gen_ts = get_total_generation_ts(red_grid, time_indices=selected_time_indices)
    P_red_load_ts = get_total_load_ts(red_grid, time_indices=selected_time_indices)
    
    assert np.allclose(P_orig_gen_ts, P_red_gen_ts, atol=1e-4), \
        "Total generation should not change after reduction at selected time steps"
    assert np.allclose(P_orig_load_ts, P_red_load_ts, atol=1e-4), \
        "Total demand should not change after reduction at selected time steps"


def test_ptdf_projected_ts_slack_remove():
    """
    Test to check the reduction flows with time series and remove the slack
    :return:
    """

    # fname = os.path.join('src', 'tests', 'data', 'grids', 'ptdf_ts.veragrid')
    fname = os.path.join('data', 'grids', 'ptdf_ts.veragrid')
        
    grid = gce.open_file(filename=fname)

    # First run time series linear analysis
    lin_ts = gce.LinearAnalysisTs(grid=grid, distributed_slack=False)
    P_orig = grid.get_Pbus_prof()
    Flows_orig = lin_ts.get_flows_ts(P=P_orig)

    # Then reduce the network
    bus_to_remove = np.array([0, 1])
    
    # Get internal branches before reduction to compare later
    external, boundary, internal, boundary_branches, internal_branches = grid.get_reduction_sets(reduction_bus_indices=bus_to_remove)
    
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    
    # Run time series linear analysis on reduced grid
    lin_ts_red = gce.LinearAnalysisTs(grid=red_grid, distributed_slack=False)
    P_red = red_grid.get_Pbus_prof()
    Flows_red = lin_ts_red.get_flows_ts(P=P_red)

    # Compare flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]
    
    # Check if dimensions match
    assert Flows_red.shape[1] == len(internal_branches)

    # Compare flows
    assert np.allclose(Flows_orig_internal, Flows_red, atol=1e-4)

    
def test_ptdf_projected_ts_simple_ree():
    """
    Test to check the reduction flows with time series (6-bus grid REE provided)
    :return:
    """

    # fname = os.path.join('src', 'tests', 'data', 'grids', 'red_test_6bus.veragrid')
    fname = os.path.join('data', 'grids', 'red_test_6bus.veragrid')
        
    grid = gce.open_file(filename=fname)

    # First run time series linear analysis
    lin_ts = gce.LinearAnalysisTs(grid=grid, distributed_slack=False)
    P_orig = grid.get_Pbus_prof()
    Flows_orig = lin_ts.get_flows_ts(P=P_orig)

    # Then reduce the network
    bus_to_remove = np.array([0, 3, 4])
    
    # Get internal branches before reduction to compare later
    external, boundary, internal, boundary_branches, internal_branches = grid.get_reduction_sets(reduction_bus_indices=bus_to_remove)
    
    red_grid, logger = ptdf_reduction_projected(grid=grid, reduction_bus_indices=bus_to_remove, distribute_slack=False)
    
    # Run time series linear analysis on reduced grid
    lin_ts_red = gce.LinearAnalysisTs(grid=red_grid, distributed_slack=False)
    P_red = red_grid.get_Pbus_prof()
    Flows_red = lin_ts_red.get_flows_ts(P=P_red)

    # Compare flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]

    # Check if dimensions match
    assert Flows_red.shape[1] == len(internal_branches)

    # Compare flows
    assert np.allclose(Flows_orig_internal, Flows_red, atol=1e-4)


def test_grid_reduction_with_multiple_islands_after():
    """
    This test checks that the reduction is perfect even when the original system is split into more than one island
    """

    fname = os.path.join('data', 'grids', 'grid_reduction_1_island.veragrid')

    grid = gce.open_file(filename=fname)

    # First run time series linear analysis
    lin_ts = gce.LinearAnalysisTs(grid=grid, distributed_slack=False)
    P_orig = grid.get_Pbus_prof()
    Flows_orig = lin_ts.get_flows_ts(P=P_orig)

    # Then reduce the network
    bus_to_remove = np.array([3, 4])

    # Get internal branches before reduction to compare later
    (external, boundary,
     internal, boundary_branches,
     internal_branches) = grid.get_reduction_sets(reduction_bus_indices=bus_to_remove)

    red_grid, logger = ptdf_reduction_projected(grid=grid,
                                                reduction_bus_indices=bus_to_remove,
                                                distribute_slack=False)

    # Run time series linear analysis on reduced grid
    lin_ts_red = gce.LinearAnalysisTs(grid=red_grid, distributed_slack=False)
    P_red = red_grid.get_Pbus_prof()
    Flows_red = lin_ts_red.get_flows_ts(P=P_red)

    # Compare flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]

    # Check if dimensions match
    assert (Flows_red.shape[1] == len(internal_branches))

    # Compare flows
    assert np.allclose(Flows_orig_internal, Flows_red, atol=1e-4)

    # Check power balance for all time steps: total generation and demand should not change
    all_time_indices = grid.get_all_time_indices()
    P_orig_gen_ts = get_total_generation_ts(grid, time_indices=all_time_indices)
    P_orig_load_ts = get_total_load_ts(grid, time_indices=all_time_indices)
    P_red_gen_ts = get_total_generation_ts(red_grid, time_indices=all_time_indices)
    P_red_load_ts = get_total_load_ts(red_grid, time_indices=all_time_indices)

    assert np.allclose(P_orig_gen_ts, P_red_gen_ts, atol=1e-4)
    assert np.allclose(P_orig_load_ts, P_red_load_ts, atol=1e-4)

    return None


def test_grid_reduction_with_multiple_islands_before():
    """
    This test checks that the reduction is perfect even when the original system has more than one island
    """
    fname = os.path.join('data', 'grids', 'grid_reduction_2_island.veragrid')

    grid_ = gce.open_file(filename=fname)

    # First run time series linear analysis
    lin_ts = gce.LinearAnalysisTs(grid=grid_, distributed_slack=False)
    P_orig = grid_.get_Pbus_prof()
    Flows_orig = lin_ts.get_flows_ts(P=P_orig)

    # Then reduce the network
    bus_to_remove = list()
    bus_idx_dict = grid_.get_bus_index_dict()
    for bus in grid_.buses:
        if bus.Vnom < 400:
            bus_remove_idx = bus_idx_dict[bus]
            bus_to_remove.append(bus_remove_idx)

    # Get internal branches before reduction to compare later
    (external, boundary,
     internal, boundary_branches,
     internal_branches) = grid_.get_reduction_sets(reduction_bus_indices=bus_to_remove)

    red_grid, logger = ptdf_reduction_projected(grid=grid_,
                                                reduction_bus_indices=bus_to_remove,
                                                distribute_slack=False)

    # Run time series linear analysis on reduced grid
    lin_ts_red = gce.LinearAnalysisTs(grid=red_grid, distributed_slack=False)
    P_red = red_grid.get_Pbus_prof()
    Flows_red = lin_ts_red.get_flows_ts(P=P_red)

    # Compare flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]

    # Check if dimensions match
    assert (Flows_red.shape[1] == len(internal_branches))

    # Compare flows
    assert np.allclose(Flows_orig_internal, Flows_red, atol=1e-4)

    # Check power balance for all time steps: total generation and demand should not change
    all_time_indices = grid_.get_all_time_indices()
    P_orig_gen_ts = get_total_generation_ts(grid_, time_indices=all_time_indices)
    P_orig_load_ts = get_total_load_ts(grid_, time_indices=all_time_indices)
    P_red_gen_ts = get_total_generation_ts(red_grid, time_indices=all_time_indices)
    P_red_load_ts = get_total_load_ts(red_grid, time_indices=all_time_indices)

    assert np.allclose(P_orig_gen_ts, P_red_gen_ts, atol=1e-4)
    assert np.allclose(P_orig_load_ts, P_red_load_ts, atol=1e-4)


def test_compact_devices_reduces_device_count():
    """
    Test that compact_devices=True results in fewer loads and generators
    compared to compact_devices=False, while maintaining the same power flows.

    Uses a scenario that removes the slack bus to ensure device relocation
    occurs, which creates multiple devices per bus that can be compacted.
    """
    # Use the time-series grid with slack removal - this creates multiple
    # compensation devices and relocated devices per bus
    fname = os.path.join('data', 'grids', 'ptdf_ts.veragrid')

    # Remove buses including the slack (bus 0) to trigger relocation
    bus_to_remove = np.array([0, 1])

    # ---- Run with compact_devices=False ----
    grid_no_compact = gce.open_file(filename=fname)

    # Get internal branches before reduction
    external, boundary, internal, boundary_branches, internal_branches = \
        grid_no_compact.get_reduction_sets(reduction_bus_indices=bus_to_remove)

    # Run linear analysis on original grid
    lin_ts_orig = gce.LinearAnalysisTs(grid=grid_no_compact, distributed_slack=False)
    P_orig = grid_no_compact.get_Pbus_prof()
    Flows_orig = lin_ts_orig.get_flows_ts(P=P_orig)

    # Reduce without compaction
    red_grid_no_compact, _ = ptdf_reduction_projected(
        grid=grid_no_compact,
        reduction_bus_indices=bus_to_remove,
        distribute_slack=False,
        compact_devices=False
    )

    n_loads_no_compact = len(red_grid_no_compact.loads)
    n_gens_no_compact = len(red_grid_no_compact.generators)

    # ---- Run with compact_devices=True ----
    grid_compact = gce.open_file(filename=fname)

    # Reduce with compaction
    red_grid_compact, _ = ptdf_reduction_projected(
        grid=grid_compact,
        reduction_bus_indices=bus_to_remove,
        distribute_slack=False,
        compact_devices=True
    )

    n_loads_compact = len(red_grid_compact.loads)
    n_gens_compact = len(red_grid_compact.generators)

    # ---- Verify compaction reduces device count ----
    assert n_loads_compact <= n_loads_no_compact, \
        f"Compacted grid should have <= loads: {n_loads_compact} vs {n_loads_no_compact}"
    assert n_gens_compact <= n_gens_no_compact, \
        f"Compacted grid should have <= generators: {n_gens_compact} vs {n_gens_no_compact}"

    # At least one category should be strictly less (otherwise compaction did nothing)
    assert (n_loads_compact < n_loads_no_compact) or (n_gens_compact < n_gens_no_compact), \
        f"Compaction should reduce at least one device category: " \
        f"loads {n_loads_compact} vs {n_loads_no_compact}, " \
        f"gens {n_gens_compact} vs {n_gens_no_compact}"

    # ---- Verify power flows are unchanged ----
    lin_ts_compact = gce.LinearAnalysisTs(grid=red_grid_compact, distributed_slack=False)
    P_compact = red_grid_compact.get_Pbus_prof()
    Flows_compact = lin_ts_compact.get_flows_ts(P=P_compact)

    lin_ts_no_compact = gce.LinearAnalysisTs(grid=red_grid_no_compact, distributed_slack=False)
    P_no_compact = red_grid_no_compact.get_Pbus_prof()
    Flows_no_compact = lin_ts_no_compact.get_flows_ts(P=P_no_compact)

    # Both should match original flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]
    assert np.allclose(Flows_orig_internal, Flows_compact, atol=1e-4), \
        "Compacted grid flows should match original"
    assert np.allclose(Flows_orig_internal, Flows_no_compact, atol=1e-4), \
        "Non-compacted grid flows should match original"

    # ---- Verify total generation and load are unchanged ----
    all_time_indices = grid_compact.get_all_time_indices()

    P_compact_gen_ts = get_total_generation_ts(red_grid_compact, time_indices=all_time_indices)
    P_compact_load_ts = get_total_load_ts(red_grid_compact, time_indices=all_time_indices)
    P_no_compact_gen_ts = get_total_generation_ts(red_grid_no_compact, time_indices=all_time_indices)
    P_no_compact_load_ts = get_total_load_ts(red_grid_no_compact, time_indices=all_time_indices)

    assert np.allclose(P_compact_gen_ts, P_no_compact_gen_ts, atol=1e-4), \
        "Total generation should be same with and without compaction"
    assert np.allclose(P_compact_load_ts, P_no_compact_load_ts, atol=1e-4), \
        "Total load should be same with and without compaction"


def ptdf_projected_large_real_syst_snapshot():
    """
    Test to check if the snapshot reduction works well in a large grid
    :return:
    """

    # fname = '/Users/josep/Documents/Grids/100h_nohvdc_noshunts.gridcal'
    # fname = '/Users/josep/Documents/Grids/100h_nohvdc.gridcal'
    fname = '/Users/josep/Documents/Grids/100h.gridcal'

    # Determine buses to remove (Vnom < 400)
    grid_orig = gce.open_file(filename=fname)
    bus_to_remove = []
    bus_idx_dict = grid_orig.get_bus_index_dict()
    for bus in grid_orig.buses:
        if bus.Vnom < 400:
            bus_to_remove.append(bus_idx_dict[bus])
    bus_to_remove = np.array(bus_to_remove)

    # Determine internal branches before reduction
    _, _, _, _, internal_branches = grid_orig.get_reduction_sets(reduction_bus_indices=bus_to_remove)

    # First run basic linear analysis on original grid
    flows_dr = gce.LinearAnalysisDriver(grid=grid_orig, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr.run()
    flows_branches = flows_dr.results.Sf

    # ---- Reduce WITHOUT compaction ----
    grid_no_compact = gce.open_file(filename=fname)
    red_grid_no_compact, _ = ptdf_reduction_projected(
        grid=grid_no_compact,
        reduction_bus_indices=bus_to_remove,
        distribute_slack=False,
        compact_devices=False
    )
    n_loads_no_compact = len(red_grid_no_compact.loads)
    n_gens_no_compact = len(red_grid_no_compact.generators)

    # ---- Reduce WITH compaction ----
    grid_compact = gce.open_file(filename=fname)
    red_grid_compact, _ = ptdf_reduction_projected(
        grid=grid_compact,
        reduction_bus_indices=bus_to_remove,
        distribute_slack=False,
        compact_devices=True
    )
    n_loads_compact = len(red_grid_compact.loads)
    n_gens_compact = len(red_grid_compact.generators)

    # Print device counts comparison
    print(f"\n{'='*60}")
    print(f"SNAPSHOT REDUCTION - Device Count Comparison")
    print(f"{'='*60}")
    print(f"WITHOUT compaction: {n_loads_no_compact} loads, {n_gens_no_compact} generators")
    print(f"WITH compaction:    {n_loads_compact} loads, {n_gens_compact} generators")
    print(f"Reduction:          {n_loads_no_compact - n_loads_compact} loads, "
          f"{n_gens_no_compact - n_gens_compact} generators")
    print(f"{'='*60}\n")

    # Verify flows on compacted grid
    flows_dr_red = gce.LinearAnalysisDriver(grid=red_grid_compact, options=gce.LinearAnalysisOptions(distribute_slack=False))
    flows_dr_red.run()
    flows_branches_red = flows_dr_red.results.Sf

    # Check that flows on remaining branches match
    assert np.allclose(flows_branches[internal_branches], flows_branches_red, atol=1e-4)

    # Check power balance: total generation and demand should not change
    P_orig_gen_total = get_total_generation(grid_orig)
    P_orig_load_total = get_total_load(grid_orig)
    P_red_gen_total = get_total_generation(red_grid_compact)
    P_red_load_total = get_total_load(red_grid_compact)

    assert abs(P_orig_gen_total - P_red_gen_total) < 1e-4, \
        "Total generation should not change after reduction"
    assert abs(P_orig_load_total - P_red_load_total) < 1e-4, \
        "Total demand should not change after reduction"


def ptdf_projected_large_real_syst_time_series():
    """
    Test to check if the time series reduction works well in a large grid
    """
    # fname = '/Users/josep/Documents/Grids/100h.gridcal'
    fname = '/Users/josep/Documents/Grids/6000h.gridcal'

    # Determine buses to remove (Vnom < 400)
    grid_orig = gce.open_file(filename=fname)
    bus_to_remove = []
    bus_idx_dict = grid_orig.get_bus_index_dict()
    for bus in grid_orig.buses:
        if bus.Vnom < 400:
            bus_to_remove.append(bus_idx_dict[bus])
    bus_to_remove = np.array(bus_to_remove)

    # Get internal branches before reduction to compare later
    _, _, _, _, internal_branches = grid_orig.get_reduction_sets(reduction_bus_indices=bus_to_remove)

    # First run time series linear analysis on original grid
    lin_ts = gce.LinearAnalysisTs(grid=grid_orig, distributed_slack=False)
    P_orig = grid_orig.get_Pbus_prof()
    Flows_orig = lin_ts.get_flows_ts(P=P_orig)

    # ---- Reduce WITHOUT compaction ----
    grid_no_compact = gce.open_file(filename=fname)
    red_grid_no_compact, _ = ptdf_reduction_projected(
        grid=grid_no_compact,
        reduction_bus_indices=bus_to_remove,
        distribute_slack=False,
        compact_devices=False
    )
    n_loads_no_compact = len(red_grid_no_compact.loads)
    n_gens_no_compact = len(red_grid_no_compact.generators)

    # ---- Reduce WITH compaction ----
    grid_compact = gce.open_file(filename=fname)
    red_grid_compact, _ = ptdf_reduction_projected(
        grid=grid_compact,
        reduction_bus_indices=bus_to_remove,
        distribute_slack=False,
        compact_devices=True
    )
    n_loads_compact = len(red_grid_compact.loads)
    n_gens_compact = len(red_grid_compact.generators)

    # Print device counts comparison
    print(f"\n{'='*60}")
    print(f"TIME SERIES REDUCTION - Device Count Comparison")
    print(f"{'='*60}")
    print(f"WITHOUT compaction: {n_loads_no_compact} loads, {n_gens_no_compact} generators")
    print(f"WITH compaction:    {n_loads_compact} loads, {n_gens_compact} generators")
    print(f"Reduction:          {n_loads_no_compact - n_loads_compact} loads, "
          f"{n_gens_no_compact - n_gens_compact} generators")
    print(f"{'='*60}\n")

    # Run time series linear analysis on compacted reduced grid
    lin_ts_red = gce.LinearAnalysisTs(grid=red_grid_compact, distributed_slack=False)
    P_red = red_grid_compact.get_Pbus_prof()
    Flows_red = lin_ts_red.get_flows_ts(P=P_red)

    # Compare flows on internal branches
    Flows_orig_internal = Flows_orig[:, internal_branches]

    # Check if dimensions match
    assert (Flows_red.shape[1] == len(internal_branches))

    # Compare flows
    assert np.allclose(Flows_orig_internal, Flows_red, atol=1e-4)

    # Check power balance for all time steps: compacted should match non-compacted
    all_time_indices = grid_orig.get_all_time_indices()
    P_no_compact_gen_ts = get_total_generation_ts(red_grid_no_compact, time_indices=all_time_indices)
    P_no_compact_load_ts = get_total_load_ts(red_grid_no_compact, time_indices=all_time_indices)
    P_compact_gen_ts = get_total_generation_ts(red_grid_compact, time_indices=all_time_indices)
    P_compact_load_ts = get_total_load_ts(red_grid_compact, time_indices=all_time_indices)

    assert np.allclose(P_no_compact_gen_ts, P_compact_gen_ts, atol=1e-4), \
        "Compacted generation should match non-compacted"
    assert np.allclose(P_no_compact_load_ts, P_compact_load_ts, atol=1e-4), \
        "Compacted load should match non-compacted"


if __name__ == '__main__':
    # test_ward_reduction()
    # test_ptdf_projected_14_reduction()
    # test_ptdf_projected_14_complex_reduction()
    # test_ptdf_projected_14_complex_inactive_reduction()
    # test_reduction_flows()
    # test_ptdf_projected()
    # test_ptdf_projected_balances()
    # test_ptdf_projected_antena()
    # test_ptdf_projected_gb()
    # test_ptdf_projected_ts()
    # test_ptdf_projected_slack_remove()
    # test_ptdf_projected_ts_slack_remove()
    # test_ptdf_projected_ts_gb_full()
    ptdf_projected_large_real_syst_snapshot()
    ptdf_projected_large_real_syst_time_series()