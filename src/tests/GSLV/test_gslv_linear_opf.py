# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.Gslv.activation import GSLV_AVAILABLE
from VeraGridEngine.Simulations.OPF.opf_ts_results import OptimalPowerFlowTimeSeriesResults


def set_unique_linear_cost_profiles(grid: vg.MultiCircuit) -> None:
    """
    Assign deterministic dense linear-cost profiles to generators and batteries.

    The IEEE39 weekly test grid contains repeated marginal costs. That allows
    multiple equivalent redispatch solutions, which makes cross-engine tests
    weaker than necessary. This helper perturbs the linear cost profile of each
    dispatchable injection just enough to keep the original merit-order groups
    while making every device unique.

    :param grid: Grid whose generator and battery cost profiles are updated.
    """
    time_count = max(grid.get_time_number(), 1)

    for k, generator in enumerate(grid.get_generators()):
        linear_cost = float(generator.Cost) + 0.01 * float(k + 1)
        generator.Cost_prof = np.full(time_count, linear_cost, dtype=float)

    generator_count = len(grid.get_generators())
    for k, battery in enumerate(grid.get_batteries()):
        linear_cost = float(battery.Cost) + 0.01 * float(generator_count + k + 1)
        battery.Cost_prof = np.full(time_count, linear_cost, dtype=float)


def get_total_linear_opf_cost_proxy(grid: vg.MultiCircuit,
                                    time_indices: np.ndarray | None,
                                    results: OptimalPowerFlowTimeSeriesResults) -> float:
    """
    Compute a battery-aware linear-OPF objective proxy over the simulated horizon.

    VeraGrid's ``system_total_energy_cost`` only aggregates generator and load
    shedding costs. The linear OPF formulation also prices battery discharge, so
    tests that compare engines need to add that missing contribution explicitly.

    :param grid: Grid used for the simulation.
    :param time_indices: Global time indices simulated by the results.
    :param results: OPF time-series results.
    :return: Battery-aware linear objective proxy over the horizon.
    """
    if time_indices is None:
        selected_time_indices = np.array(grid.get_all_time_indices(), dtype=int)
    else:
        selected_time_indices = np.array(time_indices, dtype=int)

    total_cost = float(np.sum(results.generator_cost))
    total_cost += float(np.sum(results.load_shedding_cost))
    total_cost += float(np.sum(results.overloads_cost))

    batteries = grid.get_batteries()
    for local_t_idx, global_t_idx in enumerate(selected_time_indices):
        for k, battery in enumerate(batteries):
            if battery.get_active_at(int(global_t_idx)) and battery.bus is not None:
                total_cost += float(battery.get_Cost0_at(int(global_t_idx)))
                total_cost += float(
                    battery.get_Cost_at(int(global_t_idx)) * max(results.battery_power[local_t_idx, k], 0.0)
                )

    return total_cost


def get_total_net_dispatch(results: OptimalPowerFlowTimeSeriesResults) -> np.ndarray:
    """
    Compute the net controllable active-power injection per time step.

    :param results: OPF time-series results.
    :return: Per-step total generator-plus-battery dispatch.
    """
    return np.sum(results.generator_power, axis=1) + np.sum(results.battery_power, axis=1)


def assert_linear_opf_results_compatible(grid: vg.MultiCircuit,
                                         time_indices: np.ndarray | None,
                                         native_results: OptimalPowerFlowTimeSeriesResults,
                                         gslv_results: OptimalPowerFlowTimeSeriesResults) -> None:
    """
    Check the invariant quantities of a linear OPF result pair.

    :param grid: Grid used for the simulation.
    :param time_indices: Global time indices simulated by the results.
    :param native_results: VeraGrid OPF results.
    :param gslv_results: GSLV OPF results.
    """
    assert np.all(native_results.converged)
    assert np.all(gslv_results.converged)
    assert np.allclose(native_results.load_shedding, gslv_results.load_shedding, atol=1e-9)
    assert np.allclose(native_results.overloads, gslv_results.overloads, atol=1e-9)
    assert np.allclose(native_results.Sf, gslv_results.Sf, atol=1e-8)
    assert np.allclose(native_results.St, gslv_results.St, atol=1e-8)
    assert np.allclose(get_total_net_dispatch(native_results),
                       get_total_net_dispatch(gslv_results),
                       atol=1e-6)
    assert np.isclose(get_total_linear_opf_cost_proxy(grid, time_indices, native_results),
                      get_total_linear_opf_cost_proxy(grid, time_indices, gslv_results),
                      atol=1e-5)


def test_gslv_linear_opf() -> None:
    """
    Linear OPF can have multiple equally optimal dispatches and branch flows.
    Compare objective-level and feasibility invariants instead of raw flows.
    """
    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', "IEEE39_1W.gridcal")

    print(f"Testing: {fname}")

    grid_gc = vg.open_file(filename=fname)
    set_unique_linear_cost_profiles(grid_gc)

    # Native engine
    driver1 = vg.OptimalPowerFlowTimeSeriesDriver(grid=grid_gc, engine=vg.EngineType.VeraGrid)
    driver1.run()

    driver2 = vg.OptimalPowerFlowTimeSeriesDriver(grid=grid_gc, engine=vg.EngineType.GSLV)
    driver2.run()

    assert_linear_opf_results_compatible(grid_gc, None, driver1.results, driver2.results)


def test_gslv_linear_opf_time_slices() -> None:
    """
    GSLV linear OPF must preserve the requested time slice selection.
    """
    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', "IEEE39_1W.gridcal")
    time_indices = np.array([30 + i for i in range(12)], dtype=int)
    grid_gc = vg.open_file(filename=fname)
    set_unique_linear_cost_profiles(grid_gc)

    driver1 = vg.OptimalPowerFlowTimeSeriesDriver(grid=grid_gc,
                                                  time_indices=time_indices,
                                                  engine=vg.EngineType.VeraGrid)
    driver1.run()

    driver2 = vg.OptimalPowerFlowTimeSeriesDriver(grid=grid_gc,
                                                  time_indices=time_indices,
                                                  engine=vg.EngineType.GSLV)
    driver2.run()

    assert driver1.results.Sf.shape == driver2.results.Sf.shape
    assert_linear_opf_results_compatible(grid_gc, time_indices, driver1.results, driver2.results)


def test_gslv_linear_opf_daily_grouping() -> None:
    """
    Daily grouping can still have alternative optimal dispatches.
    Compare feasibility invariants and the battery-aware objective proxy.
    """
    if not GSLV_AVAILABLE:
        return

    fname = os.path.join('data', 'grids', "IEEE39_1W.gridcal")
    grid_gc = vg.open_file(filename=fname)
    set_unique_linear_cost_profiles(grid_gc)
    options = vg.OptimalPowerFlowOptions(time_grouping=vg.TimeGrouping.Daily)

    driver1 = vg.OptimalPowerFlowTimeSeriesDriver(grid=grid_gc,
                                                  options=options,
                                                  engine=vg.EngineType.VeraGrid)
    driver1.run()

    driver2 = vg.OptimalPowerFlowTimeSeriesDriver(grid=grid_gc,
                                                  options=options,
                                                  engine=vg.EngineType.GSLV)
    driver2.run()

    assert_linear_opf_results_compatible(grid_gc, None, driver1.results, driver2.results)
