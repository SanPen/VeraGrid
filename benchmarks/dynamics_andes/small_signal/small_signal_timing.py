# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Timing utilities for reproducible ANDES--VeraGrid RMS benchmarks."""

from __future__ import annotations

import csv
from pathlib import Path
import time

import numpy as np
import pandas as pd


def elapsed_seconds(start_time: float) -> float:
    """Return elapsed wall-clock seconds from a performance-counter sample.

    :param start_time: Value previously returned by ``time.perf_counter``.
    :return: Elapsed seconds.
    """
    return float(time.perf_counter() - start_time)


def veragrid_small_signal_timing_phase_names() -> tuple[str, ...]:
    """Return the fixed column order for VeraGrid small-signal repetitions.

    :return: Timing phase names aligned with every VeraGrid sample vector.
    """
    return (
        "case_and_model_build",
        "diagnostic_power_flow_warmup",
        "power_flow",
        "rms_problem_build_initialization_symbolic_to_numeric",
        "diagnostic_small_signal_warmup",
        "small_signal_total",
        "result_export",
        "normal_workflow_unattributed_overhead",
        "normal_workflow_total",
        "dynamic_problem_preparation",
        "dynamic_simulation_total",
        "dynamic_results_total",
    )


def andes_small_signal_timing_phase_names() -> tuple[str, ...]:
    """Return the fixed column order for ANDES small-signal repetitions.

    :return: Timing phase names aligned with every ANDES sample vector.
    """
    return (
        "case_and_model_build",
        "andes_system_setup",
        "diagnostic_power_flow_warmup",
        "power_flow",
        "dynamic_initialization",
        "benchmark_preprocessing",
        "diagnostic_small_signal_warmup",
        "small_signal_total",
        "result_export",
        "normal_workflow_unattributed_overhead",
        "normal_workflow_total",
        "dynamic_problem_preparation",
        "dynamic_simulation_total",
        "dynamic_results_total",
    )


def finalize_normal_workflow_timings(
    timings: dict[str, float],
    total_start: float,
    normal_component_names: tuple[str, ...],
    diagnostic_names: tuple[str, ...],
) -> None:
    """Complete one timing record with raw script overhead and wall-clock total.

    Diagnostic warm repeats happen during the measured wall-clock interval but
    are not operations performed twice by the normal simulation. Their duration
    is therefore removed from the raw case-to-results script total. The
    remaining difference between that diagnostic total and the explicitly timed
    components is retained as overhead instead of silently disappearing.

    :param timings: Mutable phase-to-seconds mapping for one benchmark run.
    :param total_start: Performance-counter sample taken at workflow entry.
    :param normal_component_names: Mutually exclusive normal workflow phases.
    :param diagnostic_names: Warm diagnostic phases excluded from the workflow.
    :return: None.
    """
    diagnostic_seconds: float = float(sum(timings[name] for name in diagnostic_names))
    normal_workflow_seconds: float = elapsed_seconds(total_start) - diagnostic_seconds
    attributed_seconds: float = float(sum(timings[name] for name in normal_component_names))

    # Preserve all normal elapsed time, including small Python-side gaps between
    # the explicit timers, so the displayed components reconcile to the total.
    unattributed_seconds: float = max(0.0, normal_workflow_seconds - attributed_seconds)
    timings["normal_workflow_unattributed_overhead"] = unattributed_seconds
    timings["normal_workflow_total"] = normal_workflow_seconds


def benchmark_timing_metadata(
    phase_name: str,
    engine_label: str,
) -> tuple[str, str]:
    """Return the total relationship and precise scope of one timing phase.

    :param phase_name: Stable phase identifier stored in timing artifacts.
    :param engine_label: Simulator name used to specialize unknown phase notes.
    :return: Relationship to the normal workflow total and human-readable scope.
    """
    metadata: dict[str, tuple[str, str]] = dict()
    metadata["case_and_model_build"] = (
        "excluded_prerequisite",
        "Load or construct the network, devices, and dynamic model instances.",
    )
    metadata["power_flow"] = (
        "excluded_prerequisite",
        "Second steady-state power-flow solve, with runtime caches and the initial voltage guess "
        "already warmed by one excluded solve.",
    )
    metadata["rms_problem_build_initialization_symbolic_to_numeric"] = (
        "engine_specific_workflow_component",
        "VeraGrid combined stage: build the RMS DAE problem, explicitly initialize dynamic states, "
        "and compile numerical RHS and Jacobian functions. ANDES loads pregenerated numerical "
        "functions before its timed preparation, so this is not an internally equivalent phase.",
    )
    metadata["andes_system_setup"] = (
        "engine_specific_workflow_component",
        "ANDES system setup: arrays, per-unit data, DAE addresses, sparse patterns, references, and "
        "connectivity; generated numerical calls are normally loaded during case_and_model_build.",
    )
    metadata["dynamic_initialization"] = (
        "engine_specific_workflow_component",
        "ANDES TDS initialization and initial iterative step; VeraGrid performs its dynamic "
        "initialization inside its combined RMS-problem stage.",
    )
    metadata["benchmark_preprocessing"] = (
        "engine_specific_workflow_component",
        "ANDES benchmark-only folding of zero-time-constant or unused auxiliary states.",
    )
    metadata["small_signal_total"] = (
        "comparable_calculation",
        "Second complete small-signal driver call on the same initialized problem after one "
        "excluded warm-up call, including state matrix, eigensolution, left/right eigenvectors, "
        "participation factors, modal post-processing and result assembly.",
    )
    metadata["dynamic_problem_preparation"] = (
        "engine_specific_workflow_component",
        "Complete engine-specific post-power-flow preparation. ANDES reuses pregenerated numerical "
        "functions; VeraGrid constructs and compiles its RMS problem at this point.",
    )
    metadata["dynamic_simulation_total"] = (
        "post_power_flow_workflow_total",
        "Engine-specific post-power-flow preparation plus the measured warm small-signal calculation.",
    )
    metadata["dynamic_results_total"] = (
        "post_power_flow_results_total",
        "Post-power-flow workflow total plus result-file export.",
    )
    metadata["result_export"] = (
        "result_export",
        "Write the engine numerical result artifacts used by the comparator.",
    )
    metadata["normal_workflow_unattributed_overhead"] = (
        "excluded_diagnostic",
        "Normal-workflow wall time between explicit timers, retained so components reconcile "
        "exactly to the total.",
    )
    metadata["normal_workflow_total"] = (
        "excluded_diagnostic",
        "Raw case-to-results script total after subtracting warm-up repeats; retained only as a "
        "diagnostic because the dynamic benchmark totals are assembled from explicit phases.",
    )
    metadata["diagnostic_small_signal_warmup"] = (
        "excluded_diagnostic",
        "First complete small-signal driver call used to initialize runtime and numerical-library "
        "caches before the measured second call; excluded from normal_workflow_total.",
    )
    metadata["diagnostic_power_flow_warmup"] = (
        "excluded_diagnostic",
        "First power-flow solve used only to warm runtime caches and provide the initial guess for "
        "the measured second solve; excluded from normal_workflow_total.",
    )
    selected_metadata: tuple[str, str] | None = metadata.get(phase_name, None)
    if selected_metadata is None:
        relation: str = "component"
        description: str = f"{engine_label} benchmark timing phase."
    else:
        relation, description = selected_metadata
    return relation, description


def save_benchmark_timings(
    output_directory: Path,
    engine_label: str,
    case_label: str,
    phase_names: tuple[str, ...],
    timing_samples: np.ndarray,
    state_count: int,
    mode_count: int,
) -> Path:
    """Write repeated timing samples, statistics and comparator means.

    :param output_directory: Existing or new benchmark result directory.
    :param engine_label: Simulator name used in filenames and table rows.
    :param case_label: Benchmark case label.
    :param phase_names: Timing phase names aligned with the sample columns.
    :param timing_samples: Repetitions by timing phase.
    :param state_count: Number of retained physical states.
    :param mode_count: Number of exported eigenvalues.
    :return: Written CSV path.
    """
    if timing_samples.ndim == 2 and timing_samples.shape[1] == len(phase_names):
        pass
    else:
        raise ValueError("Small-signal timing phases do not match the sample columns.")
    if timing_samples.shape[0] > 0:
        pass
    else:
        raise ValueError("At least one small-signal timing repetition is required.")

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
        statistics_writer: csv.writer = csv.writer(statistics_file)
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

    rows: list[tuple[str, str, str, float, float, str, str, int, int]] = list()
    phase_index: int
    for phase_index in range(len(phase_names)):
        phase_name: str = phase_names[phase_index]
        relation: str
        description: str
        relation, description = benchmark_timing_metadata(
            phase_name=phase_name,
            engine_label=engine_label,
        )
        rows.append(
            (
                engine_label,
                case_label,
                phase_name,
                float(means[phase_index]),
                float(standard_deviations[phase_index]),
                relation,
                description,
                int(state_count),
                int(mode_count),
            )
        )
    timing_table: pd.DataFrame = pd.DataFrame(
        rows,
        columns=list((
            "engine",
            "case",
            "phase",
            "seconds",
            "standard_deviation_seconds",
            "timing_role",
            "scope",
            "state_count",
            "mode_count",
        )),
    )
    csv_path: Path = output_directory / f"timings_results_{engine_label}_{case_label}.csv"
    json_path: Path = output_directory / f"timings_results_{engine_label}_{case_label}.json"
    timing_table.to_csv(csv_path, index=False, float_format="%.12g")
    timing_table.to_json(json_path, orient="records", indent=2)
    print("\nSmall-signal benchmark timings:")
    print(
        timing_table.loc[
            :, list(("timing_role", "phase", "seconds"))
        ].to_string(index=False)
    )
    print(f"Raw timing repetitions written to: {sample_path}")
    print(f"Timing statistics written to: {statistics_path}")
    print(f"Timing results written to: {csv_path}")
    return csv_path
