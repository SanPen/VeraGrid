# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run the complete IEEE39 ANDES-versus-VeraGrid small-signal benchmark."""

from __future__ import annotations

from pathlib import Path
import time

import numpy as np

from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.enumerations import RmsInitializationMethod
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_driver import SmallSignalStabilityRmsDriver
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_options import RmsSmallSignalStabilityOptions
import VeraGridEngine.api as gce

from benchmarks.dynamics_andes.fixtures import load_benchmark_grid
from benchmarks.dynamics_andes.small_signal.small_signal_result_files import save_small_signal_result_files
from benchmarks.dynamics_andes.small_signal.small_signal_results_comparison import compare_result_folders
from benchmarks.dynamics_andes.small_signal.small_signal_timing import save_benchmark_timings
from benchmarks.dynamics_andes.small_signal.small_signal_timing import veragrid_small_signal_timing_phase_names


def run_ieee39_small_signal_repetition() -> tuple[np.ndarray, int, int]:
    """Calculate and export one IEEE39 small-signal timing repetition.

    :return: Timing vector, state count and mode count.
    """
    workflow_start: float = time.perf_counter()
    timings: dict[str, float] = dict()

    # 1. Build the physical network and attach its RMS dynamic models.
    build_start: float = time.perf_counter()
    grid: gce.MultiCircuit = load_benchmark_grid("IEEE39")
    timings["case_and_model_build"] = time.perf_counter() - build_start

    # 2. Solve the operating point used to initialize the dynamic equations.
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
    # The first solve initializes reusable numerical code and is not compared.
    power_flow: PowerFlowDriver = PowerFlowDriver(grid, power_flow_options)
    power_flow_warmup_start: float = time.perf_counter()
    power_flow.run()
    timings["diagnostic_power_flow_warmup"] = (
        time.perf_counter() - power_flow_warmup_start
    )
    if bool(power_flow.results.converged):
        pass
    else:
        raise RuntimeError("The IEEE39 power-flow warm-up did not converge.")

    # Only the second solve is retained as the comparable warm power flow.
    power_flow = PowerFlowDriver(grid, power_flow_options)
    power_flow_start: float = time.perf_counter()
    power_flow.run()
    timings["power_flow"] = time.perf_counter() - power_flow_start
    if bool(power_flow.results.converged):
        pass
    else:
        raise RuntimeError("The warm IEEE39 power flow did not converge.")

    # 3. Initialize the RMS problem and calculate its complete modal spectrum.
    rms_options: RmsOptions = RmsOptions(
        time_step=0.001,
        simulation_time=10.0,
        tolerance=1.0e-6,
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        initialization_method=RmsInitializationMethod.Explicit,
        use_init_values=False,
        max_iter=1000,
        verbose=0,
    )
    small_signal_options: RmsSmallSignalStabilityOptions = RmsSmallSignalStabilityOptions(
        ss_assessment_time=0.0
    )
    initialization_start: float = time.perf_counter()
    driver: SmallSignalStabilityRmsDriver = SmallSignalStabilityRmsDriver(
        grid=grid,
        rms_options=rms_options,
        sss_options=small_signal_options,
        pf_results=power_flow.results,
    )
    timings["rms_problem_build_initialization_symbolic_to_numeric"] = (
        time.perf_counter() - initialization_start
    )
    # Run the complete driver once before measurement so Numba and numerical-
    # library caches have the same warm status as in the measured ANDES call.
    # This first call is recorded separately and excluded from both totals.
    warmup_start: float = time.perf_counter()
    driver.run()
    timings["diagnostic_small_signal_warmup"] = time.perf_counter() - warmup_start

    # Measure the second complete driver call on the same initialized problem.
    # Its results are the values exported and compared against ANDES.
    calculation_start: float = time.perf_counter()
    driver.run()
    timings["small_signal_total"] = time.perf_counter() - calculation_start

    # 4. Save the numerical artifacts used by the comparison.
    results_directory: Path = (
        Path(__file__).resolve().parent / "results" / "VeraGrid"
    )
    export_start: float = time.perf_counter()
    save_small_signal_result_files(
        results=driver.results,
        power_flow_results=power_flow.results,
        output_directory=results_directory,
    )
    timings["result_export"] = time.perf_counter() - export_start
    timings["normal_workflow_total"] = (
        time.perf_counter()
        - workflow_start
        - timings["diagnostic_power_flow_warmup"]
        - timings["diagnostic_small_signal_warmup"]
    )
    timings["normal_workflow_unattributed_overhead"] = max(
        0.0,
        timings["normal_workflow_total"]
        - timings["case_and_model_build"]
        - timings["power_flow"]
        - timings["rms_problem_build_initialization_symbolic_to_numeric"]
        - timings["small_signal_total"]
        - timings["result_export"],
    )
    timings["dynamic_problem_preparation"] = timings[
        "rms_problem_build_initialization_symbolic_to_numeric"
    ]
    timings["dynamic_simulation_total"] = (
        timings["dynamic_problem_preparation"] + timings["small_signal_total"]
    )
    timings["dynamic_results_total"] = (
        timings["dynamic_simulation_total"] + timings["result_export"]
    )
    phase_names: tuple[str, ...] = veragrid_small_signal_timing_phase_names()
    timing_values: np.ndarray = np.asarray(
        tuple(timings[phase_name] for phase_name in phase_names),
        dtype=float,
    )
    return (
        timing_values,
        int(driver.results.state_matrix.shape[0]),
        int(driver.results.eigenvalues.size),
    )


def run_ieee39_small_signal(show_figures: bool = False) -> None:
    """Run ten IEEE39 repetitions, save their means and compare the result.

    :param show_figures: Display figures after the PNG files have been saved.
    :return: None.
    """
    repetitions: int = 10
    phase_names: tuple[str, ...] = veragrid_small_signal_timing_phase_names()
    timing_samples: np.ndarray = np.empty(
        (repetitions, len(phase_names)),
        dtype=float,
    )
    state_count: int = 0
    mode_count: int = 0
    repetition_index: int
    for repetition_index in range(repetitions):
        print(f"\nIEEE39 small signal: repetition {repetition_index + 1}/{repetitions}")
        repetition_result: tuple[np.ndarray, int, int] = (
            run_ieee39_small_signal_repetition()
        )
        timing_samples[repetition_index, :] = repetition_result[0]
        state_count = repetition_result[1]
        mode_count = repetition_result[2]

    results_directory: Path = Path(__file__).resolve().parent / "results" / "VeraGrid"
    save_benchmark_timings(
        output_directory=results_directory,
        engine_label="VeraGrid",
        case_label="IEEE39",
        phase_names=phase_names,
        timing_samples=timing_samples,
        state_count=state_count,
        mode_count=mode_count,
    )

    # Compare once, after the last numerical result and all timing samples exist.
    compare_result_folders(
        veragrid_results_dir=results_directory,
        andes_results_dir=results_directory.parent / "ANDES",
        case_label="IEEE39",
        output_dir=results_directory.parent / "comparison",
        show_figures=show_figures,
    )


if __name__ == "__main__":
    run_ieee39_small_signal()
else:
    pass
