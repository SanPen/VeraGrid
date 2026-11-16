# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run VeraGrid RMS benchmarks and save their numerical results.

The public ``run_<case>_rms.py`` scripts provide the readable entry points.  This
module contains only the machinery shared by those scripts: benchmark options,
power-flow initialization, RMS execution and CSV persistence.  Plotting and
comparison against ANDES are kept in ``rms_results_comparison.py``.
"""

from __future__ import annotations

import csv
from pathlib import Path
import time
from typing import Any, Tuple, Dict, List

import numpy as np
import pandas as pd

from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.enumerations import RmsInitializationMethod
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
import VeraGridEngine.api as gce


def rms_timing_phase_names() -> tuple[str, ...]:
    """Return the fixed column order used by repeated RMS timings.

    :return: Timing phase names aligned with every RMS sample vector.
    """
    return (
        "case_and_model_build_s",
        "andes_system_setup_s",
        "power_flow_cold_excluded_s",
        "power_flow_warm_analyzed_s",
        "dynamic_initialization_and_symbolic_numeric_s",
        "solver_setup_s",
        "dynamic_problem_preparation_s",
        "rms_integration_s",
        "result_export_excluded_s",
        "dynamic_simulation_total_s",
        "dynamic_results_total_s",
        "process_wall_total_s",
        "workflow_overhead_s",
        "integration_rhs_s",
        "integration_jacobian_s",
        "integration_linear_solver_s",
    )


def case_label(system_name: str) -> str:
    """Return the stable report label for one benchmark case.

    :param system_name: Benchmark system name.
    :return: Stable case label.
    """
    if system_name == "Kundur":
        label: str = "KUNDUR_no_shunt"
    else:
        label = system_name
    return label


def engine_results_directory(
        system_name: str,
        engine_label: str,
        scenario_name: str = "base",
) -> Path:
    """Return one engine-specific RMS dynamic result directory.

    :param system_name: Benchmark system name.
    :param engine_label: Engine name used in the folder name.
    :param scenario_name: Dynamic scenario represented by the results.
    :return: Absolute result directory.
    """
    script_directory: Path = Path(__file__).resolve().parent
    case_directory: Path = script_directory / system_name / "results"
    return case_directory / engine_label / scenario_name


def perturbation_state_label(system_name: str) -> str:
    """Return the common physical rotor-speed state perturbed in both tools.

    :param system_name: Selected benchmark system.
    :return: ANDES-style state label.
    """
    if system_name == "Kundur":
        label: str = "omega GENCLS 1"
    elif system_name == "NPCC140":
        label = "omega GENROU 22"
    else:
        label = "omega GENROU 1"
    return label


def build_rms_options(
        time_step: float,
        simulation_time: float,
        integration_tolerance: float,
        maximum_iterations: int,
) -> RmsOptions:
    """Build the VeraGrid options equivalent to ANDES Backward Euler.

    :param time_step: Fixed integration step in seconds.
    :param simulation_time: Final simulation time in seconds.
    :param integration_tolerance: Nonlinear integration tolerance.
    :param maximum_iterations: Maximum nonlinear iterations per step.
    :return: VeraGrid RMS options.
    """
    return RmsOptions(
        time_step=time_step,
        simulation_time=simulation_time,
        tolerance=integration_tolerance,
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        initialization_method=RmsInitializationMethod.Explicit,
        use_init_values=False,
        max_iter=maximum_iterations,
        verbose=0,
    )


def build_unique_variable_labels(variables: list[Any]) -> list[str]:
    """Build deterministic labels from symbolic variable names and occurrence order.

    :param variables: Ordered VeraGrid symbolic variables.
    :return: Unique labels suitable for trajectory CSV columns.
    """
    occurrence_by_name: dict[str, int] = dict()
    labels: list[str] = list()
    variable: Any
    for variable in variables:
        variable_name: str = str(variable.name)
        occurrence: int | None = occurrence_by_name.get(variable_name, None)
        if occurrence is None:
            occurrence = 1
        else:
            occurrence += 1
        occurrence_by_name[variable_name] = occurrence
        labels.append(f"{variable_name}{occurrence}")
    return labels


def write_trajectory_csv(
        output_path: Path,
        time_values: np.ndarray,
        values: np.ndarray,
        labels: list[str],
) -> None:
    """Write one time-aligned state or algebraic trajectory table.

    :param output_path: Destination CSV file.
    :param time_values: Simulation timestamps in seconds.
    :param values: Two-dimensional trajectory matrix.
    :param labels: Variable labels aligned with matrix columns.
    :return: None.
    """
    if values.ndim == 2 and values.shape[1] == len(labels):
        pass
    else:
        raise ValueError("Trajectory values and labels are not dimensionally aligned.")
    data: dict[str, np.ndarray] = dict()
    data["time_s"] = np.asarray(time_values, dtype=float)
    label_index: int
    for label_index in range(len(labels)):
        data[labels[label_index]] = np.asarray(values[:, label_index], dtype=float)
    pd.DataFrame(data).to_csv(output_path, index=False, float_format="%.12e")


def write_key_value_csv(output_path: Path, values: list[tuple[str, str]]) -> None:
    """Write an ordered key-value table without losing unavailable values.

    :param output_path: Destination CSV file.
    :param values: Ordered key-value rows.
    :return: None.
    """
    frame: pd.DataFrame = pd.DataFrame(values, columns=list(("metric", "value")))
    frame.to_csv(output_path, index=False)


def save_rms_timing_repetitions(
        output_directory: Path,
        timing_samples: np.ndarray,
) -> None:
    """Save all RMS repetitions and expose their means to the comparator.

    ``timing_samples.csv`` and ``timing_statistics.csv`` preserve the complete
    measurement set. ``timings.csv`` retains the existing key-value interface,
    but its values are now the arithmetic means of all repetitions.

    :param output_directory: Engine and scenario result directory.
    :param timing_samples: Repetitions by timing phase.
    :return: None.
    """
    phase_names: tuple[str, ...] = rms_timing_phase_names()
    if timing_samples.ndim == 2 and timing_samples.shape[1] == len(phase_names):
        pass
    else:
        raise ValueError("RMS timing phases do not match the sample columns.")
    if timing_samples.shape[0] > 0:
        pass
    else:
        raise ValueError("At least one RMS timing repetition is required.")

    output_directory.mkdir(parents=True, exist_ok=True)
    sample_path: Path = output_directory / "timing_samples.csv"
    statistics_path: Path = output_directory / "timing_statistics.csv"

    # Save every measurement before calculating the statistics used by the
    # comparator. The long format is directly readable and filterable.
    with sample_path.open("w", encoding="utf-8", newline="") as sample_file:
        sample_writer: csv.writer = csv.writer(sample_file)
        sample_writer.writerow(list(("repetition", "phase", "seconds")))
        repetition_index: int
        for repetition_index in range(timing_samples.shape[0]):
            phase_index: int
            for phase_index in range(timing_samples.shape[1]):
                sample_writer.writerow(
                    list((
                        repetition_index + 1,
                        phase_names[phase_index],
                        float(timing_samples[repetition_index, phase_index]),
                    ))
                )

    phase_count: int = len(phase_names)
    means: np.ndarray = np.full(phase_count, np.nan, dtype=float)
    standard_deviations: np.ndarray = np.full(phase_count, np.nan, dtype=float)
    medians: np.ndarray = np.full(phase_count, np.nan, dtype=float)
    minimums: np.ndarray = np.full(phase_count, np.nan, dtype=float)
    maximums: np.ndarray = np.full(phase_count, np.nan, dtype=float)
    sample_counts: np.ndarray = np.zeros(phase_count, dtype=int)

    # NaN identifies a phase unavailable in one engine. Calculate each phase
    # independently so those unavailable values are never interpreted as zero.
    phase_index = 0
    while phase_index < phase_count:
        phase_values: np.ndarray = timing_samples[:, phase_index]
        finite_values: np.ndarray = phase_values[np.isfinite(phase_values)]
        sample_counts[phase_index] = int(finite_values.size)
        if finite_values.size > 0:
            means[phase_index] = float(np.mean(finite_values))
            medians[phase_index] = float(np.median(finite_values))
            minimums[phase_index] = float(np.min(finite_values))
            maximums[phase_index] = float(np.max(finite_values))
            if finite_values.size > 1:
                standard_deviations[phase_index] = float(
                    np.std(finite_values, ddof=1)
                )
            else:
                standard_deviations[phase_index] = 0.0
        else:
            pass
        phase_index += 1

    with statistics_path.open("w", encoding="utf-8", newline="") as statistics_file:
        statistics_writer = csv.writer(statistics_file)
        statistics_writer.writerow(
            list((
                "phase",
                "sample_count",
                "mean_seconds",
                "standard_deviation_seconds",
                "median_seconds",
                "minimum_seconds",
                "maximum_seconds",
            ))
        )
        for phase_index in range(phase_count):
            statistics_writer.writerow(
                list((
                    phase_names[phase_index],
                    int(sample_counts[phase_index]),
                    means[phase_index],
                    standard_deviations[phase_index],
                    medians[phase_index],
                    minimums[phase_index],
                    maximums[phase_index],
                ))
            )

    # Keep the established file consumed by rms_results_comparison.py.
    # Engine-specific unavailable phases remain explicit rather than becoming zeros.
    timing_rows: List[Tuple[str, str]] = list()
    phase_index: int
    for phase_index in range(len(phase_names)):
        mean_seconds: float = float(means[phase_index])
        if np.isfinite(mean_seconds):
            timing_rows.append((phase_names[phase_index], f"{mean_seconds:.12e}"))
        else:
            timing_rows.append((phase_names[phase_index], "N/A: phase unavailable"))
    write_key_value_csv(output_directory / "timings.csv", timing_rows)
    print(f"RMS timing samples written to: {sample_path}")
    print(f"RMS timing statistics written to: {statistics_path}")


def run_power_flow_twice(
        grid: gce.MultiCircuit,
        options: PowerFlowOptions,
) -> tuple[PowerFlowResults, float, float]:
    """Run a cold and a warm VeraGrid power flow and retain only the second result.

    :param grid: RMS-ready VeraGrid network.
    :param options: Deterministic Newton power-flow options.
    :return: Authoritative warm result, cold time and warm time.
    """
    # The first solve triggers cold numerical compilation and is measured only
    # to document warm-up cost; it is excluded from the comparison total.
    cold_driver: PowerFlowDriver = PowerFlowDriver(grid, options)
    cold_start: float = time.perf_counter()
    cold_driver.run()
    cold_seconds: float = time.perf_counter() - cold_start
    if bool(cold_driver.results.converged):
        pass
    else:
        raise RuntimeError("The cold VeraGrid power flow did not converge.")

    # A fresh driver avoids reusing result containers while the process keeps
    # compiled numerical kernels warm. This second solution feeds the RMS DAE.
    warm_driver: PowerFlowDriver = PowerFlowDriver(grid, options)
    warm_start: float = time.perf_counter()
    warm_driver.run()
    warm_seconds: float = time.perf_counter() - warm_start
    if bool(warm_driver.results.converged):
        pass
    else:
        raise RuntimeError("The authoritative warm VeraGrid power flow did not converge.")
    return warm_driver.results, cold_seconds, warm_seconds


def perturb_first_veragrid_speed_state(
        problem: RmsProblemDae,
        perturbation_pu: float,
        target_label: str,
        canonical_state_labels: list[str] | None,
) -> str:
    """Apply the common initial speed perturbation to the first machine state.

    :param problem: Initialized VeraGrid RMS DAE.
    :param perturbation_pu: Additive rotor-speed perturbation in per unit.
    :param target_label: Common ANDES-style physical state label.
    :param canonical_state_labels: Labels aligned with VeraGrid state order.
    :return: Perturbed symbolic state label.
    """
    perturbation_applied: bool = False
    perturbed_label: str = ""
    state_index: int
    for state_index in range(len(problem.state_vars)):
        state_variable: Any = problem.state_vars[state_index]
        if canonical_state_labels is None:
            is_target_state: bool = not perturbation_applied and str(state_variable.name) == "omega"
        else:
            is_target_state = canonical_state_labels[state_index] == target_label
        if not perturbation_applied and is_target_state:
            initial_values: np.ndarray = problem.get_x0()
            problem.init_guess[state_variable.uid] = float(initial_values[state_index]) + perturbation_pu
            perturbed_label = target_label
            perturbation_applied = True
        else:
            pass
    if perturbation_applied:
        pass
    else:
        raise ValueError("No VeraGrid omega state is available for the RMS perturbation.")
    return perturbed_label


def set_veragrid_initial_vector(problem: RmsProblemDae, values: np.ndarray) -> None:
    """Replace the DAE initial vector with one accepted integration snapshot.

    :param problem: Initialized VeraGrid RMS problem.
    :param values: State-then-algebraic snapshot in solver order.
    :return: None.
    """
    expected_size: int = problem.get_all_vars_number()
    if values.size == expected_size:
        pass
    else:
        raise ValueError("The accepted RMS snapshot does not match the DAE variable count.")
    state_index: int
    for state_index in range(len(problem.state_vars)):
        state_variable: Any = problem.state_vars[state_index]
        problem.init_guess[state_variable.uid] = float(values[state_index])
    algebraic_index: int
    state_count: int = len(problem.state_vars)
    for algebraic_index in range(len(problem.algebraic_vars)):
        algebraic_variable: Any = problem.algebraic_vars[algebraic_index]
        problem.init_guess[algebraic_variable.uid] = float(values[state_count + algebraic_index])


def combine_solver_timings(
        first_solver: BackEulerImplicitIntegration,
        second_solver: BackEulerImplicitIntegration,
) -> dict[str, float]:
    """Add internal timing accumulators from two consecutive solver segments.

    :param first_solver: Pre-event Backward Euler segment.
    :param second_solver: Post-event Backward Euler segment.
    :return: Summed timing values by internal phase.
    """
    combined: dict[str, float] = dict()
    timing_name: str
    for timing_name in first_solver._timings:
        combined[timing_name] = (
                float(first_solver._timings[timing_name])
                + float(second_solver._timings[timing_name])
        )
    return combined


def run_veragrid_rms_benchmark(
        grid: gce.MultiCircuit,
        power_flow_options: PowerFlowOptions,
        system_name: str,
        scenario_name: str,
        case_build_seconds: float,
        workflow_start: float,
        canonical_state_labels: list[str] | None = None,
        time_step: float = 0.001,
        simulation_time: float = 1.0,
        integration_tolerance: float = 1.0e-6,
        maximum_iterations: int = 1000,
        speed_perturbation_pu: float = 1.0e-4,
        event_time: float = 0.2,
        event_state_step_pu: float = 1.0e-4,
) -> np.ndarray:
    """Run, time and persist one VeraGrid RMS time-domain benchmark.

    :param grid: Fully configured VeraGrid RMS network.
    :param power_flow_options: Case-specific static solver options.
    :param system_name: Benchmark system name.
    :param scenario_name: ``base`` or ``event``.
    :param case_build_seconds: Measured network and model construction time.
    :param workflow_start: Wall-clock counter captured before case construction.
    :param canonical_state_labels: Optional ANDES-style labels aligned with VeraGrid states.
    :param time_step: Fixed integration step in seconds.
    :param simulation_time: Final simulation time in seconds.
    :param integration_tolerance: Nonlinear integration tolerance.
    :param maximum_iterations: Maximum nonlinear iterations per step.
    :param speed_perturbation_pu: Initial speed perturbation for the base scenario.
    :param event_time: Event application time in seconds.
    :param event_state_step_pu: Event speed-state step in p.u.
    :return: One timing sample aligned with :func:`rms_timing_phase_names`.
    """
    pf_results: PowerFlowResults
    cold_pf_seconds: float
    warm_pf_seconds: float
    pf_results, cold_pf_seconds, warm_pf_seconds = run_power_flow_twice(
        grid=grid,
        options=power_flow_options,
    )

    # Constructing RmsProblemDae performs explicit dynamic initialization and
    # compiles the symbolic residuals and Jacobians into numerical functions.
    rms_options: RmsOptions = build_rms_options(
        time_step=time_step,
        simulation_time=simulation_time,
        integration_tolerance=integration_tolerance,
        maximum_iterations=maximum_iterations,
    )
    initialization_start: float = time.perf_counter()
    problem: RmsProblemDae = RmsProblemDae(
        grid=grid,
        options=rms_options,
        pf_results=pf_results,
    )
    # The benchmark state event is applied between two solver segments, so the
    # compiled DAE itself remains the same before and after the instantaneous
    # state jump.
    events_group: RmsEventsGroup = RmsEventsGroup(name="benchmark_scenario")
    problem.set_events_group(events_group)
    problem.reset_boundary_update_state(0.0)
    target_state_label: str = perturbation_state_label(system_name)

    if scenario_name == "base" and speed_perturbation_pu != 0.0:
        perturbed_state_label: str = perturb_first_veragrid_speed_state(
            problem=problem,
            perturbation_pu=speed_perturbation_pu,
            target_label=target_state_label,
            canonical_state_labels=canonical_state_labels,
        )
    else:
        perturbed_state_label = "none"

    initialization_seconds: float = time.perf_counter() - initialization_start

    # Solver construction allocates the fixed time grid and trajectory arrays;
    # no integration step is executed in this phase.
    solver_setup_start: float = time.perf_counter()
    if scenario_name == "base":
        solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
            problem=problem,
            t0=0.0,
            t_end=simulation_time,
            h=time_step,
            max_iter=maximum_iterations,
            tolerance=integration_tolerance,
        )
        pre_event_solver: BackEulerImplicitIntegration | None = None
        post_event_solver: BackEulerImplicitIntegration | None = None
    else:
        pre_event_solver = BackEulerImplicitIntegration(
            problem=problem,
            t0=0.0,
            t_end=event_time,
            h=time_step,
            max_iter=maximum_iterations,
            tolerance=integration_tolerance,
        )
        post_event_solver = BackEulerImplicitIntegration(
            problem=problem,
            t0=event_time,
            t_end=simulation_time,
            h=time_step,
            max_iter=maximum_iterations,
            tolerance=integration_tolerance,
        )
        solver = pre_event_solver
    solver_setup_seconds: float = time.perf_counter() - solver_setup_start

    integration_start: float = time.perf_counter()
    if scenario_name == "base":
        simulation_output: tuple[np.ndarray, np.ndarray, bool, bool] = solver.simulate()
        time_values: np.ndarray = np.asarray(simulation_output[0], dtype=float)
        all_values: np.ndarray = np.asarray(simulation_output[1], dtype=float)
        well_initialized: bool = bool(simulation_output[2])
        converged: bool = bool(simulation_output[3])
        solver_timings: Dict[str, float] = solver.get_timings()
    else:
        if pre_event_solver is not None and post_event_solver is not None:
            pass
        else:
            raise RuntimeError("The event benchmark solver segments were not constructed.")
        pre_event_output: tuple[np.ndarray, np.ndarray, bool, bool] = pre_event_solver.simulate()
        pre_event_values: np.ndarray = np.asarray(pre_event_output[1], dtype=float)
        set_veragrid_initial_vector(problem=problem, values=pre_event_values[-1, :])
        perturbed_state_label = perturb_first_veragrid_speed_state(
            problem=problem,
            perturbation_pu=event_state_step_pu,
            target_label=target_state_label,
            canonical_state_labels=canonical_state_labels,
        )
        post_event_output: tuple[np.ndarray, np.ndarray, bool, bool] = post_event_solver.simulate()
        time_values = np.concatenate((
            np.asarray(pre_event_output[0], dtype=float)[:-1],
            np.asarray(post_event_output[0], dtype=float),
        ))
        all_values = np.vstack((
            pre_event_values[:-1, :],
            np.asarray(post_event_output[1], dtype=float),
        ))
        well_initialized = bool(pre_event_output[2]) and bool(post_event_output[2])
        converged = bool(pre_event_output[3]) and bool(post_event_output[3])
        solver_timings = combine_solver_timings(
            first_solver=pre_event_solver,
            second_solver=post_event_solver,
        )
    integration_seconds: float = time.perf_counter() - integration_start
    if converged:
        pass
    else:
        raise RuntimeError("The VeraGrid RMS integration did not converge.")

    state_count: int = problem.get_states_number()
    state_values: np.ndarray = all_values[:, :state_count]
    algebraic_values: np.ndarray = all_values[:, state_count:]
    if canonical_state_labels is None:
        state_labels: list[str] = build_unique_variable_labels(list(problem.state_vars))
    elif len(canonical_state_labels) == state_count:
        state_labels = list(canonical_state_labels)
    else:
        raise ValueError(
            "Canonical state-label count does not match the VeraGrid RMS state count."
        )
    algebraic_labels: list[str] = build_unique_variable_labels(list(problem.algebraic_vars))

    output_directory: Path = engine_results_directory(
        system_name,
        "VeraGrid",
        scenario_name,
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    export_start: float = time.perf_counter()
    write_trajectory_csv(
        output_path=output_directory / "state_trajectory.csv",
        time_values=time_values,
        values=state_values,
        labels=state_labels,
    )
    write_trajectory_csv(
        output_path=output_directory / "algebraic_trajectory.csv",
        time_values=time_values,
        values=algebraic_values,
        labels=algebraic_labels,
    )
    export_seconds: float = time.perf_counter() - export_start

    dynamic_problem_preparation_seconds: float = (
            initialization_seconds + solver_setup_seconds
    )
    dynamic_simulation_total_seconds: float = (
            dynamic_problem_preparation_seconds + integration_seconds
    )
    dynamic_results_total_seconds: float = dynamic_simulation_total_seconds + export_seconds
    process_total_seconds: float = time.perf_counter() - workflow_start
    workflow_overhead_seconds: float = max(
        0.0,
        process_total_seconds
        - case_build_seconds
        - cold_pf_seconds
        - warm_pf_seconds
        - dynamic_results_total_seconds,
    )
    metadata_rows: list[tuple[str, str]] = list()
    metadata_rows.append(("engine", "VeraGrid"))
    metadata_rows.append(("case", case_label(system_name)))
    metadata_rows.append(("scenario", scenario_name))
    metadata_rows.append(("solver", "Backward Euler"))
    metadata_rows.append(("fixed_step", "True"))
    metadata_rows.append(("adaptive_step_reduction", "False"))
    metadata_rows.append(("time_step_s", f"{time_step:.12e}"))
    metadata_rows.append(("simulation_time_s", f"{simulation_time:.12e}"))
    metadata_rows.append(("integration_tolerance", f"{integration_tolerance:.12e}"))
    metadata_rows.append(("perturbation", scenario_name))
    metadata_rows.append(("perturbed_state", perturbed_state_label))
    metadata_rows.append(("speed_perturbation_pu", f"{speed_perturbation_pu:.12e}"))
    metadata_rows.append(("event_type", scenario_name))
    metadata_rows.append(("event_time_s", f"{event_time:.12e}"))
    metadata_rows.append(("event_state_step_pu", f"{event_state_step_pu:.12e}"))
    metadata_rows.append(("event_target_state", target_state_label))
    metadata_rows.append(("sample_count", str(time_values.size)))
    metadata_rows.append(("state_count", str(state_count)))
    metadata_rows.append(("algebraic_count", str(algebraic_values.shape[1])))
    metadata_rows.append(("power_flow_source", "second warm solve"))
    metadata_rows.append(("well_initialized", str(well_initialized)))
    metadata_rows.append(("converged", str(converged)))
    write_key_value_csv(output_directory / "metadata.csv", metadata_rows)
    print(f"VeraGrid RMS results written to: {output_directory}")
    return np.asarray(
        (
            case_build_seconds,
            np.nan,
            cold_pf_seconds,
            warm_pf_seconds,
            initialization_seconds,
            solver_setup_seconds,
            dynamic_problem_preparation_seconds,
            integration_seconds,
            export_seconds,
            dynamic_simulation_total_seconds,
            dynamic_results_total_seconds,
            process_total_seconds,
            workflow_overhead_seconds,
            float(solver_timings["rhs_time"]),
            float(solver_timings["jacobian_time"]),
            float(solver_timings["linear_solver_time"]),
        ),
        dtype=float,
    )
