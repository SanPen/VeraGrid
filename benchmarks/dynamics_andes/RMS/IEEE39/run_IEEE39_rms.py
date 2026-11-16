# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run the IEEE 39-bus VeraGrid RMS time-domain benchmark from PyCharm."""

from __future__ import annotations

import time

import numpy as np

from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
import VeraGridEngine.api as gce

from benchmarks.dynamics_andes.RMS.rms_simulation import engine_results_directory
from benchmarks.dynamics_andes.RMS.rms_simulation import rms_timing_phase_names
from benchmarks.dynamics_andes.RMS.rms_simulation import run_veragrid_rms_benchmark
from benchmarks.dynamics_andes.RMS.rms_simulation import save_rms_timing_repetitions
from benchmarks.dynamics_andes.RMS.rms_results_comparison import compare_rms_case
from benchmarks.dynamics_andes.fixtures import load_benchmark_grid
from benchmarks.dynamics_andes.small_signal.IEEE39.ieee39_dynamic_model import get_ieee39_andes_style_state_labels


def main() -> None:
    """Build, run and compare the IEEE39 base and event RMS scenarios.

    :return: None.
    """
    repetitions: int = 10

    # 1. Keep the complete power-flow setup visible in the executable file.
    power_flow_options: PowerFlowOptions = PowerFlowOptions(
        solver_type=gce.SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1.0e-12,
        max_iter=25,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=True,
        orthogonalize_controls=True,
        apply_temperature_correction=False,
        branch_impedance_tolerance_mode=gce.BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=False,
        generate_report=False,
    )

    # 2. Rebuild and simulate the base scenario ten independent times.
    phase_count: int = len(rms_timing_phase_names())
    state_labels: list[str] = get_ieee39_andes_style_state_labels()
    base_timing_samples: np.ndarray = np.empty((repetitions, phase_count), dtype=float)
    repetition_index: int
    for repetition_index in range(repetitions):
        print(f"\nIEEE39 base: repetition {repetition_index + 1}/{repetitions}")
        workflow_start: float = time.perf_counter()
        build_start: float = time.perf_counter()
        grid: gce.MultiCircuit = load_benchmark_grid("IEEE39")
        build_seconds: float = time.perf_counter() - build_start
        base_timing_samples[repetition_index, :] = run_veragrid_rms_benchmark(
            grid=grid,
            power_flow_options=power_flow_options,
            system_name="IEEE39",
            scenario_name="base",
            case_build_seconds=build_seconds,
            workflow_start=workflow_start,
            canonical_state_labels=state_labels,
        )
    save_rms_timing_repetitions(
        output_directory=engine_results_directory("IEEE39", "VeraGrid", "base"),
        timing_samples=base_timing_samples,
    )
    compare_rms_case(system_name="IEEE39", scenario_name="base")

    # 3. Repeat the event scenario with a fresh grid and solver every time.
    event_timing_samples: np.ndarray = np.empty((repetitions, phase_count), dtype=float)
    for repetition_index in range(repetitions):
        print(f"\nIEEE39 event: repetition {repetition_index + 1}/{repetitions}")
        workflow_start = time.perf_counter()
        build_start = time.perf_counter()
        grid = load_benchmark_grid("IEEE39")
        build_seconds = time.perf_counter() - build_start
        event_timing_samples[repetition_index, :] = run_veragrid_rms_benchmark(
            grid=grid,
            power_flow_options=power_flow_options,
            system_name="IEEE39",
            scenario_name="event",
            case_build_seconds=build_seconds,
            workflow_start=workflow_start,
            canonical_state_labels=state_labels,
            simulation_time=2.0,
            speed_perturbation_pu=0.0,
            event_time=0.2,
            event_state_step_pu=1.0e-4,
        )
    save_rms_timing_repetitions(
        output_directory=engine_results_directory("IEEE39", "VeraGrid", "event"),
        timing_samples=event_timing_samples,
    )
    compare_rms_case(system_name="IEEE39", scenario_name="event")


if __name__ == "__main__":
    main()
else:
    pass
