# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import os

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions, SolverType


def _build_ieee14_with_duplicate_generators() -> tuple[gce.MultiCircuit, list[int], list[int]]:
    """
    Load IEEE 14 and duplicate generators on generator buses.

    The duplicated units create the multi-generator-per-bus case needed to
    validate distributed-slack dispatch sharing.
    """
    # Reuse the existing IEEE 14 Matpower fixture instead of introducing a new grid.
    fname: str = os.path.join("data", "grids", "Matpower", "case14.matpower")
    grid: gce.MultiCircuit = FileOpen(fname).open()

    # Duplicate the slack-bus generator and the first PV-bus generator. This
    # keeps the test on a real network while covering the same-bus split logic.
    duplicate_indices: list[int] = list()
    duplicate_battery_indices: list[int] = list()
    source_indices: list[int] = [0, 1]
    source_index: int

    for source_index in source_indices:
        source_generator: gce.Generator = grid.generators[source_index]
        duplicate_generator: gce.Generator = gce.Generator(
            name=f"{source_generator.name} duplicate",
            P=source_generator.P,
            Q=source_generator.Q,
            vset=source_generator.Vset,
            control_mode=source_generator.control_mode,
            Qmin=source_generator.Qmin,
            Qmax=source_generator.Qmax,
            Snom=source_generator.Snom,
            Pmin=source_generator.Pmin,
            Pmax=source_generator.Pmax,
        )
        grid.add_generator(source_generator.bus, duplicate_generator)
        duplicate_indices.append(len(grid.generators) - 1)

    # Add two identical batteries on the same PV bus so battery_p is exercised
    # against the same distributed-slack split path as gen_p.
    pv_bus = grid.generators[1].bus
    first_battery: gce.Battery = gce.Battery(
        name="PV bus battery 1",
        P=12.0,
        Q=0.0,
        vset=grid.generators[1].Vset,
        control_mode=grid.generators[1].control_mode,
        Qmin=-20.0,
        Qmax=20.0,
        Snom=40.0,
        Pmin=0.0,
        Pmax=40.0,
        Enom=80.0,
    )
    second_battery: gce.Battery = gce.Battery(
        name="PV bus battery 2",
        P=12.0,
        Q=0.0,
        vset=grid.generators[1].Vset,
        control_mode=grid.generators[1].control_mode,
        Qmin=-20.0,
        Qmax=20.0,
        Snom=40.0,
        Pmin=0.0,
        Pmax=40.0,
        Enom=80.0,
    )
    grid.add_battery(bus=pv_bus, api_obj=first_battery)
    duplicate_battery_indices.append(len(grid.batteries) - 1)
    grid.add_battery(bus=pv_bus, api_obj=second_battery)
    duplicate_battery_indices.append(len(grid.batteries) - 1)

    return grid, duplicate_indices, duplicate_battery_indices


def _run_power_flow(grid: gce.MultiCircuit, distributed_slack: bool) -> PowerFlowDriver:
    """
    Solve the power flow with the requested slack-distribution mode.

    :param grid: Circuit to solve.
    :param distributed_slack: Distributed-slack flag.
    :return: Executed power-flow driver.
    """
    # Keep the solver settings identical between both runs so the test isolates
    # the effect of the distributed-slack option.
    options: PowerFlowOptions = PowerFlowOptions(
        solver_type=SolverType.NR,
        verbose=False,
        control_q=False,
        retry_with_other_methods=False,
        use_stored_guess=False,
        distributed_slack=distributed_slack,
    )
    driver: PowerFlowDriver = PowerFlowDriver(grid, options)
    driver.run()
    return driver


def test_distributed_slack_ieee14_multiple_generators_per_bus() -> None:
    """
    Distributed slack must share active-power mismatch across same-bus units.
    """
    # Build the real IEEE 14 case and add duplicated generators on the slack
    # bus and on one PV bus.
    grid: gce.MultiCircuit
    duplicate_indices: list[int]
    duplicate_battery_indices: list[int]
    grid, duplicate_indices, duplicate_battery_indices = _build_ieee14_with_duplicate_generators()

    # Solve both variants on the same topology so the assertions compare the
    # distributed-slack effect directly.
    fixed_driver: PowerFlowDriver = _run_power_flow(grid=grid, distributed_slack=False)
    distributed_driver: PowerFlowDriver = _run_power_flow(grid=grid, distributed_slack=True)

    assert fixed_driver.results.converged
    assert distributed_driver.results.converged

    # The duplicated units are identical and connected to the same bus, so the
    # distributed-slack split must allocate the same solved active power to each pair.
    original_indices: list[int] = [0, 1]
    pair_position: int

    for pair_position in range(len(original_indices)):
        original_index: int = original_indices[pair_position]
        duplicate_index: int = duplicate_indices[pair_position]
        assert np.isclose(
            distributed_driver.results.gen_p[original_index],
            distributed_driver.results.gen_p[duplicate_index],
            atol=1e-6,
        )

    # The duplicated PV-bus generators start from the same scheduled set point.
    # With fixed slack they stay there, while distributed slack must increase
    # both units because the mismatch is shared beyond the reference bus.
    pv_original_index: int = 1
    pv_duplicate_index: int = duplicate_indices[1]
    scheduled_pv_dispatch: float = grid.generators[pv_original_index].P

    assert np.isclose(fixed_driver.results.gen_p[pv_original_index], scheduled_pv_dispatch, atol=1e-9)
    assert np.isclose(fixed_driver.results.gen_p[pv_duplicate_index], scheduled_pv_dispatch, atol=1e-9)

    assert distributed_driver.results.gen_p[pv_original_index] > fixed_driver.results.gen_p[pv_original_index]
    assert distributed_driver.results.gen_p[pv_duplicate_index] > fixed_driver.results.gen_p[pv_duplicate_index]

    # The added batteries sit on the same PV bus with identical settings, so
    # fixed slack keeps their scheduled power while distributed slack must move
    # both equally.
    first_battery_index: int = duplicate_battery_indices[0]
    second_battery_index: int = duplicate_battery_indices[1]
    scheduled_battery_dispatch: float = grid.batteries[first_battery_index].P

    assert np.isclose(fixed_driver.results.battery_p[first_battery_index], scheduled_battery_dispatch, atol=1e-9)
    assert np.isclose(fixed_driver.results.battery_p[second_battery_index], scheduled_battery_dispatch, atol=1e-9)

    assert np.isclose(
        distributed_driver.results.battery_p[first_battery_index],
        distributed_driver.results.battery_p[second_battery_index],
        atol=1e-6,
    )
    assert distributed_driver.results.battery_p[first_battery_index] > fixed_driver.results.battery_p[first_battery_index]
    assert distributed_driver.results.battery_p[second_battery_index] > fixed_driver.results.battery_p[second_battery_index]
