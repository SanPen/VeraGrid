# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Compare saved ANDES and VeraGrid RMS trajectories.

The comparison follows four visible stages: load and validate both result sets,
align their state labels and time samples, calculate error and timing metrics,
then write the report, CSV tables and figures.  Simulation remains outside this
module so that saved results can be inspected again without recalculation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from matplotlib import pyplot as plt
import numpy as np
import pandas as pd

from benchmarks.dynamics_andes.small_signal.small_signal_results_comparison import map_simple_veragrid_labels
from benchmarks.dynamics_andes.small_signal.small_signal_results_comparison import map_veragrid_labels_to_andes_style
from benchmarks.dynamics_andes.RMS.rms_simulation import case_label
from benchmarks.dynamics_andes.RMS.rms_simulation import engine_results_directory


def calculate_error_metrics(
    reference: np.ndarray,
    candidate: np.ndarray,
) -> tuple[float, float, float, float]:
    """Calculate maximum, mean, RMS and normalized RMS errors.

    :param reference: ANDES reference values.
    :param candidate: VeraGrid candidate values.
    :return: Maximum absolute, mean absolute, RMS and normalized RMS errors.
    """
    difference: np.ndarray = np.asarray(candidate, dtype=float) - np.asarray(reference, dtype=float)
    absolute_difference: np.ndarray = np.abs(difference)
    maximum_absolute: float = float(np.max(absolute_difference))
    mean_absolute: float = float(np.mean(absolute_difference))
    root_mean_square: float = float(np.sqrt(np.mean(difference * difference)))
    reference_scale: float = max(float(np.sqrt(np.mean(reference * reference))), 1.0e-15)
    normalized_root_mean_square: float = root_mean_square / reference_scale
    return maximum_absolute, mean_absolute, root_mean_square, normalized_root_mean_square


def comparison_directory(
    system_name: str,
    scenario_name: str = "base",
) -> Path:
    """Return the persistent RMS comparison directory for one case.

    :param system_name: Selected benchmark system.
    :param scenario_name: ``base`` or ``event``.
    :return: Absolute comparison directory.
    """
    case_directory: Path = engine_results_directory(
        system_name=system_name,
        engine_label="VeraGrid",
        scenario_name=scenario_name,
    ).parents[1]
    return case_directory / "comparison" / scenario_name


def format_report_float(value: float) -> str:
    """Format one floating-point table value for the text report.

    :param value: Numeric table value.
    :return: Scientific-notation text.
    """
    return f"{value:.6e}"


def load_key_value_table(input_path: Path) -> dict[str, str]:
    """Load one two-column metadata or timing CSV as strings.

    :param input_path: Source CSV file.
    :return: Metric-to-value map.
    """
    frame: pd.DataFrame = pd.read_csv(input_path, dtype=str)
    values: dict[str, str] = dict()
    row_index: int
    for row_index in range(frame.shape[0]):
        values[str(frame.iloc[row_index, 0])] = str(frame.iloc[row_index, 1])
    return values


def load_timing_standard_deviations(input_path: Path) -> dict[str, float]:
    """Load per-phase standard deviations from repeated timing statistics.

    :param input_path: ``timing_statistics.csv`` generated beside timings.csv.
    :return: Phase-to-standard-deviation mapping.
    """
    frame: pd.DataFrame = pd.read_csv(input_path)
    standard_deviations: dict[str, float] = dict()
    row_index: int
    for row_index in range(frame.shape[0]):
        phase_name: str = str(frame.iloc[row_index]["phase"])
        standard_deviation: float = float(
            frame.iloc[row_index]["standard_deviation_seconds"]
        )
        standard_deviations[phase_name] = standard_deviation
    return standard_deviations


def validate_numerical_configuration(
    andes_metadata: dict[str, str],
    veragrid_metadata: dict[str, str],
) -> list[str]:
    """Validate solver, fixed-step grid and horizon before comparing results.

    :param andes_metadata: ANDES metadata values.
    :param veragrid_metadata: VeraGrid metadata values.
    :return: Human-readable validation messages.
    """
    messages: list[str] = list()
    exact_keys: tuple[str, ...] = (
        "solver",
        "fixed_step",
        "adaptive_step_reduction",
        "sample_count",
        "perturbed_state",
    )
    if andes_metadata.get("scenario", None) is not None:
        exact_keys = exact_keys + (
            "scenario",
            "event_type",
        )
        if andes_metadata.get("event_type", "base") != "base":
            exact_keys = exact_keys + ("event_target_state",)
        else:
            pass
    else:
        pass
    exact_key: str
    for exact_key in exact_keys:
        andes_value: str | None = andes_metadata.get(exact_key, None)
        veragrid_value: str | None = veragrid_metadata.get(exact_key, None)
        if andes_value == veragrid_value and andes_value is not None:
            messages.append(f"PASS {exact_key}: {andes_value}")
        else:
            raise ValueError(
                f"Numerical configuration mismatch for {exact_key}: "
                f"ANDES={andes_value}, VeraGrid={veragrid_value}."
            )

    numeric_keys: tuple[str, ...] = (
        "time_step_s",
        "simulation_time_s",
        "integration_tolerance",
        "speed_perturbation_pu",
    )
    if andes_metadata.get("event_type", "base") != "base":
        numeric_keys = numeric_keys + (
            "event_time_s",
            "event_state_step_pu",
        )
    else:
        pass
    numeric_key: str
    for numeric_key in numeric_keys:
        andes_numeric: float = float(andes_metadata[numeric_key])
        veragrid_numeric: float = float(veragrid_metadata[numeric_key])
        if bool(np.isclose(andes_numeric, veragrid_numeric, rtol=0.0, atol=1.0e-15)):
            messages.append(f"PASS {numeric_key}: {andes_numeric:.12e}")
        else:
            raise ValueError(
                f"Numerical configuration mismatch for {numeric_key}: "
                f"ANDES={andes_numeric:.12e}, VeraGrid={veragrid_numeric:.12e}."
            )
    return messages


def align_state_trajectories(
    andes_frame: pd.DataFrame,
    veragrid_frame: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[str], list[str]]:
    """Align timestamps and common physical state columns between both tools.

    :param andes_frame: ANDES state trajectory table.
    :param veragrid_frame: VeraGrid state trajectory table.
    :return: Time, ANDES values, VeraGrid values, matched labels and unmatched labels.
    """
    andes_time: np.ndarray = andes_frame["time_s"].to_numpy(dtype=float)
    veragrid_time: np.ndarray = veragrid_frame["time_s"].to_numpy(dtype=float)
    if andes_time.shape == veragrid_time.shape and bool(
        np.allclose(andes_time, veragrid_time, rtol=0.0, atol=1.0e-12)
    ):
        pass
    else:
        raise ValueError("ANDES and VeraGrid do not use the same stored time grid.")

    andes_labels: list[str] = list(str(label) for label in andes_frame.columns[1:])
    veragrid_labels: list[str] = list(str(label) for label in veragrid_frame.columns[1:])
    converted_labels: list[str] = map_veragrid_labels_to_andes_style(veragrid_labels)
    mapped_labels: list[str] = map_simple_veragrid_labels(converted_labels, andes_labels)
    andes_index_by_label: dict[str, int] = dict()
    andes_index: int
    for andes_index in range(len(andes_labels)):
        andes_index_by_label[andes_labels[andes_index]] = andes_index

    matched_andes_indexes: list[int] = list()
    matched_veragrid_indexes: list[int] = list()
    matched_labels: list[str] = list()
    unmatched_veragrid: list[str] = list()
    veragrid_index: int
    for veragrid_index in range(len(mapped_labels)):
        mapped_label: str = mapped_labels[veragrid_index]
        source_index: int | None = andes_index_by_label.get(mapped_label, None)
        if source_index is None:
            unmatched_veragrid.append(veragrid_labels[veragrid_index])
        else:
            matched_andes_indexes.append(source_index)
            matched_veragrid_indexes.append(veragrid_index)
            matched_labels.append(mapped_label)
    if len(matched_labels) > 0:
        pass
    else:
        raise ValueError("No common physical RMS states could be aligned.")

    matched_label_set: set[str] = set(matched_labels)
    unmatched_andes: list[str] = list()
    andes_label: str
    for andes_label in andes_labels:
        if andes_label in matched_label_set:
            pass
        else:
            unmatched_andes.append(andes_label)

    andes_values: np.ndarray = andes_frame.iloc[:, 1:].to_numpy(dtype=float)[
        :, np.asarray(matched_andes_indexes, dtype=int)
    ]
    veragrid_values: np.ndarray = veragrid_frame.iloc[:, 1:].to_numpy(dtype=float)[
        :, np.asarray(matched_veragrid_indexes, dtype=int)
    ]
    return andes_time, andes_values, veragrid_values, matched_labels, unmatched_andes, unmatched_veragrid


def calculate_segment_rows(
    time_values: np.ndarray,
    andes_values: np.ndarray,
    veragrid_values: np.ndarray,
) -> list[tuple[str, float, float, float, float, float, int]]:
    """Calculate total and four non-overlapping equal-duration error segments.

    :param time_values: Shared timestamps.
    :param andes_values: Aligned ANDES states.
    :param veragrid_values: Aligned VeraGrid states.
    :return: Segment rows with bounds, metrics and sample counts.
    """
    rows: list[tuple[str, float, float, float, float, float, int]] = list()
    total_maximum: float
    total_mean: float
    total_rmse: float
    total_normalized_rmse: float
    total_maximum, total_mean, total_rmse, total_normalized_rmse = calculate_error_metrics(
        andes_values,
        veragrid_values,
    )
    rows.append((
        "TOTAL",
        float(time_values[0]),
        float(time_values[-1]),
        total_maximum,
        total_mean,
        total_rmse,
        int(time_values.size),
    ))

    boundaries: np.ndarray = np.linspace(float(time_values[0]), float(time_values[-1]), 5)
    segment_index: int
    for segment_index in range(4):
        start_time: float = float(boundaries[segment_index])
        end_time: float = float(boundaries[segment_index + 1])
        if segment_index < 3:
            mask: np.ndarray = (time_values >= start_time) & (time_values < end_time)
        else:
            mask = (time_values >= start_time) & (time_values <= end_time)
        segment_maximum: float
        segment_mean: float
        segment_rmse: float
        segment_normalized_rmse: float
        segment_maximum, segment_mean, segment_rmse, segment_normalized_rmse = calculate_error_metrics(
            andes_values[mask, :],
            veragrid_values[mask, :],
        )
        rows.append((
            f"SEGMENT_{segment_index + 1}",
            start_time,
            end_time,
            segment_maximum,
            segment_mean,
            segment_rmse,
            int(np.count_nonzero(mask)),
        ))
    return rows


def align_rotor_angle_reference(
    labels: list[str],
    andes_values: np.ndarray,
    veragrid_values: np.ndarray,
) -> tuple[np.ndarray, float]:
    """Remove the single physically arbitrary rotor-angle reference offset.

    :param labels: Common state labels.
    :param andes_values: Aligned ANDES state trajectories.
    :param veragrid_values: Aligned VeraGrid state trajectories.
    :return: Reference-aligned VeraGrid values and applied offset in radians.
    """
    delta_indexes: list[int] = list()
    label_index: int
    for label_index in range(len(labels)):
        if labels[label_index].startswith("delta "):
            delta_indexes.append(label_index)
        else:
            pass
    corrected_values: np.ndarray = np.asarray(veragrid_values, dtype=float).copy()
    if len(delta_indexes) > 0:
        initial_offsets: np.ndarray = (
            corrected_values[0, np.asarray(delta_indexes, dtype=int)]
            - andes_values[0, np.asarray(delta_indexes, dtype=int)]
        )
        angle_offset: float = float(np.median(initial_offsets))
        corrected_values[:, np.asarray(delta_indexes, dtype=int)] -= angle_offset
    else:
        angle_offset = 0.0
    return corrected_values, angle_offset


def calculate_per_state_frame(
    labels: list[str],
    time_values: np.ndarray,
    andes_values: np.ndarray,
    veragrid_values: np.ndarray,
) -> pd.DataFrame:
    """Calculate full-horizon numerical errors for every matched state.

    :param labels: Common state labels.
    :param time_values: Shared time grid.
    :param andes_values: Aligned ANDES states.
    :param veragrid_values: Aligned VeraGrid states.
    :return: Per-state error table sorted by maximum error.
    """
    records: list[dict[str, Any]] = list()
    state_index: int
    for state_index in range(len(labels)):
        maximum_error: float
        mean_error: float
        rms_error: float
        normalized_rms_error: float
        maximum_error, mean_error, rms_error, normalized_rms_error = calculate_error_metrics(
            andes_values[:, state_index],
            veragrid_values[:, state_index],
        )
        record: dict[str, Any] = dict()
        record["state"] = labels[state_index]
        record["max_abs_error"] = maximum_error
        record["mean_abs_error"] = mean_error
        record["rmse"] = rms_error
        record["normalized_rmse"] = normalized_rms_error
        absolute_error: np.ndarray = np.abs(
            veragrid_values[:, state_index] - andes_values[:, state_index]
        )
        peak_index: int = int(np.argmax(absolute_error))
        record["initial_abs_error"] = float(absolute_error[0])
        record["final_abs_error"] = float(absolute_error[-1])
        record["peak_error_time_s"] = float(time_values[peak_index])
        records.append(record)
    frame: pd.DataFrame = pd.DataFrame(records)
    return frame.sort_values("max_abs_error", ascending=False, ignore_index=True)


def parse_optional_timing(timings: dict[str, str], metric_name: str) -> float | None:
    """Parse one timing value while retaining explicit unavailable phases.

    :param timings: Timing key-value map.
    :param metric_name: Requested timing metric.
    :return: Timing in seconds or ``None`` when not exposed.
    """
    raw_value: str | None = timings.get(metric_name, None)
    if raw_value is None or raw_value.startswith("N/A"):
        value: float | None = None
    else:
        value = float(raw_value)
    return value


def build_timing_comparison(
    andes_timings: dict[str, str],
    veragrid_timings: dict[str, str],
    andes_standard_deviations: dict[str, float],
    veragrid_standard_deviations: dict[str, float],
) -> pd.DataFrame:
    """Build a phase-by-phase timing table with faster-tool factors.

    :param andes_timings: ANDES timing values.
    :param veragrid_timings: VeraGrid timing values.
    :param andes_standard_deviations: ANDES per-phase sample deviations.
    :param veragrid_standard_deviations: VeraGrid per-phase sample deviations.
    :return: Comparable timing table.
    """
    # Build the benchmark total whose boundary starts at dynamic-problem
    # preparation. The export-inclusive aggregate remains internal because it
    # is needed only to derive unattributed script overhead. Case construction
    # and power flow provide inputs and are excluded from the benchmark total.
    grouped_andes_timings: dict[str, str] = dict(andes_timings)
    grouped_veragrid_timings: dict[str, str] = dict(veragrid_timings)
    engine_timings: dict[str, str]
    for engine_timings in (grouped_andes_timings, grouped_veragrid_timings):
        process_total: float | None = parse_optional_timing(engine_timings, "process_wall_total_s")
        cold_power_flow: float | None = parse_optional_timing(
            engine_timings,
            "power_flow_cold_excluded_s",
        )
        dynamic_initialization: float | None = parse_optional_timing(
            engine_timings,
            "dynamic_initialization_and_symbolic_numeric_s",
        )
        andes_system_setup: float | None = parse_optional_timing(
            engine_timings,
            "andes_system_setup_s",
        )
        solver_setup: float | None = parse_optional_timing(
            engine_timings,
            "solver_setup_s",
        )
        rms_integration: float | None = parse_optional_timing(
            engine_timings,
            "rms_integration_s",
        )
        result_export: float | None = parse_optional_timing(
            engine_timings,
            "result_export_excluded_s",
        )
        if dynamic_initialization is not None and rms_integration is not None:
            dynamic_simulation_total: float = dynamic_initialization + rms_integration
            if andes_system_setup is not None:
                dynamic_simulation_total += andes_system_setup
            else:
                pass
            if solver_setup is not None:
                dynamic_simulation_total += solver_setup
            else:
                pass
            engine_timings["dynamic_simulation_total_s"] = f"{dynamic_simulation_total:.12e}"
        else:
            dynamic_simulation_total = np.nan
            engine_timings["dynamic_simulation_total_s"] = "N/A: dynamic phases unavailable"
        if (
            np.isfinite(dynamic_simulation_total)
            and result_export is not None
        ):
            dynamic_results_total: float = dynamic_simulation_total + result_export
            engine_timings["dynamic_results_total_s"] = f"{dynamic_results_total:.12e}"
        else:
            dynamic_results_total = np.nan
            engine_timings["dynamic_results_total_s"] = "N/A: dynamic phases unavailable"
        case_build: float | None = parse_optional_timing(
            engine_timings,
            "case_and_model_build_s",
        )
        warm_power_flow: float | None = parse_optional_timing(
            engine_timings,
            "power_flow_warm_analyzed_s",
        )
        saved_workflow_overhead: float | None = parse_optional_timing(
            engine_timings,
            "workflow_overhead_s",
        )
        if saved_workflow_overhead is not None:
            pass
        else:
            if (
                process_total is not None
                and cold_power_flow is not None
                and case_build is not None
                and warm_power_flow is not None
                and np.isfinite(dynamic_results_total)
            ):
                workflow_overhead: float = max(
                    0.0,
                    process_total
                    - cold_power_flow
                    - case_build
                    - warm_power_flow
                    - dynamic_results_total,
                )
                engine_timings["workflow_overhead_s"] = f"{workflow_overhead:.12e}"
            else:
                engine_timings["workflow_overhead_s"] = (
                    "N/A: workflow components unavailable"
                )

    phase_specs: tuple[
        tuple[str, tuple[str, ...], tuple[str, ...], str, str], ...
    ] = (
        (
            "Case/model preparation",
            ("case_and_model_build_s",),
            ("case_and_model_build_s",),
            "ANDES case loading and model construction versus VeraGrid fixture loading",
            "EXCLUDED PREREQUISITE",
        ),
        (
            "Warm power flow",
            ("power_flow_warm_analyzed_s",),
            ("power_flow_warm_analyzed_s",),
            "Authoritative converged operating point used to initialize the RMS equations",
            "EXCLUDED PREREQUISITE",
        ),
        (
            "Engine-specific post-power-flow preparation",
            ("dynamic_problem_preparation_s",),
            ("dynamic_problem_preparation_s",),
            "Architecture-dependent time from the solved power flow to a simulation-ready problem: ANDES reuses pregenerated numerical functions during system.setup and TDS.init, whereas VeraGrid constructs, initializes and compiles RmsProblemDae and allocates the solver",
            "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)",
        ),
        (
            "ANDES system setup",
            ("andes_system_setup_s",),
            ("not_available_s",),
            "ANDES-only subcomponent of engine-specific post-power-flow preparation: arrays, DAE addresses, references and sparse patterns",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
        ),
        (
            "ANDES TDS initialization",
            ("dynamic_initialization_and_symbolic_numeric_s",),
            ("not_available_s",),
            "ANDES-only subcomponent of engine-specific post-power-flow preparation: TDS initialization, DAE expansion and mass matrix",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
        ),
        (
            "VeraGrid RMS problem build and initialization",
            ("not_available_s",),
            ("dynamic_initialization_and_symbolic_numeric_s",),
            "VeraGrid-only subcomponent already included in dynamic preparation",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
        ),
        (
            "VeraGrid solver and time-grid allocation",
            ("not_available_s",),
            ("solver_setup_s",),
            "VeraGrid-only subcomponent; ANDES includes it inside TDS.init",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
        ),
        (
            "RMS integration",
            ("rms_integration_s",),
            ("rms_integration_s",),
            "All fixed Backward Euler steps over the common horizon",
            "COMPARABLE CALCULATION",
        ),
        (
            "VeraGrid integration RHS evaluation",
            ("integration_rhs_s",),
            ("integration_rhs_s",),
            "VeraGrid-only integration diagnostic; ANDES does not expose it",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
        ),
        (
            "VeraGrid integration Jacobian assembly",
            ("integration_jacobian_s",),
            ("integration_jacobian_s",),
            "VeraGrid-only integration diagnostic; ANDES does not expose it",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
        ),
        (
            "VeraGrid integration linear solver",
            ("integration_linear_solver_s",),
            ("integration_linear_solver_s",),
            "VeraGrid-only integration diagnostic; ANDES does not expose it",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
        ),
        (
            "Result export",
            ("result_export_excluded_s",),
            ("result_export_excluded_s",),
            "Write trajectory files consumed by the comparator",
            "RESULT EXPORT",
        ),
        (
            "Workflow overhead",
            ("workflow_overhead_s",),
            ("workflow_overhead_s",),
            "Measured normal-workflow wall time between explicit timers",
            "EXCLUDED DIAGNOSTIC",
        ),
        (
            "Post-power-flow workflow total",
            ("dynamic_simulation_total_s",),
            ("dynamic_simulation_total_s",),
            "Engine-specific post-power-flow preparation + RMS integration; useful as elapsed workflow time but not an internal phase-equivalence comparison",
            "POST-POWER-FLOW WORKFLOW TOTAL (architecture-dependent sum)",
        ),
    )
    records: list[dict[str, Any]] = list()
    phase_spec: tuple[str, tuple[str, ...], tuple[str, ...], str, str]
    for phase_spec in phase_specs:
        andes_seconds: float = 0.0
        veragrid_seconds: float = 0.0
        andes_variance: float = 0.0
        veragrid_variance: float = 0.0
        andes_available: bool = True
        veragrid_available: bool = True
        metric_name: str
        for metric_name in phase_spec[1]:
            andes_value: float | None = parse_optional_timing(grouped_andes_timings, metric_name)
            if andes_value is None:
                andes_available = False
            else:
                andes_seconds += andes_value
                andes_standard_deviation: float = andes_standard_deviations.get(
                    metric_name,
                    0.0,
                )
                andes_variance += andes_standard_deviation * andes_standard_deviation
        for metric_name in phase_spec[2]:
            veragrid_value: float | None = parse_optional_timing(grouped_veragrid_timings, metric_name)
            if veragrid_value is None:
                veragrid_available = False
            else:
                veragrid_seconds += veragrid_value
                veragrid_standard_deviation: float = veragrid_standard_deviations.get(
                    metric_name,
                    0.0,
                )
                veragrid_variance += (
                    veragrid_standard_deviation * veragrid_standard_deviation
                )

        timing_role: str = phase_spec[4]
        if timing_role == (
            "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)"
        ):
            # Both values remain visible as workflow costs, but a speed ratio
            # would incorrectly imply equivalent internal preparation work.
            andes_over_veragrid: float = np.nan
            faster_engine: str = "N/A: phases differ"
            speed_factor: float = np.nan
        else:
            if andes_available and veragrid_available and veragrid_seconds > 0.0:
                andes_over_veragrid = andes_seconds / veragrid_seconds
            else:
                andes_over_veragrid = np.nan

            if (
                andes_available
                and veragrid_available
                and andes_seconds > 0.0
                and veragrid_seconds > 0.0
            ):
                if andes_seconds < veragrid_seconds:
                    faster_engine = "ANDES"
                    speed_factor = veragrid_seconds / andes_seconds
                else:
                    faster_engine = "VeraGrid"
                    speed_factor = andes_seconds / veragrid_seconds
            else:
                faster_engine = "N/A"
                speed_factor = np.nan
        record: dict[str, Any] = dict()
        record["phase"] = phase_spec[0]
        record["what_it_contains"] = phase_spec[3]
        record["andes_s"] = andes_seconds if andes_available else np.nan
        record["veragrid_s"] = veragrid_seconds if veragrid_available else np.nan
        record["andes_std_s"] = np.sqrt(andes_variance) if andes_available else np.nan
        record["veragrid_std_s"] = (
            np.sqrt(veragrid_variance) if veragrid_available else np.nan
        )
        record["andes_over_veragrid"] = andes_over_veragrid
        record["faster_engine"] = faster_engine
        record["speed_factor_x"] = speed_factor
        record["included_in_post_power_flow_workflow_total"] = (
            timing_role in (
                "COMPARABLE CALCULATION",
                "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)",
            )
        )
        record["timing_role"] = timing_role
        records.append(record)
    return pd.DataFrame(records)


def save_comparison_figures(
    output_directory: Path,
    time_values: np.ndarray,
    andes_values: np.ndarray,
    veragrid_values: np.ndarray,
    segment_frame: pd.DataFrame,
    timing_frame: pd.DataFrame,
    labels: list[str],
    event_time: float | None,
    show_figures: bool,
) -> None:
    """Save trajectory-error and timing figures for human inspection.

    :param output_directory: Comparison result directory.
    :param time_values: Shared timestamps.
    :param andes_values: Aligned ANDES state values.
    :param veragrid_values: Aligned VeraGrid state values.
    :param segment_frame: Total and segment error table.
    :param timing_frame: Phase timing table.
    :param labels: Physical state labels aligned with both trajectories.
    :param event_time: Optional event time drawn on trajectory figures.
    :param show_figures: Display figures after saving them.
    :return: None.
    """
    absolute_error: np.ndarray = np.abs(veragrid_values - andes_values)
    error_envelope: np.ndarray = np.max(absolute_error, axis=1)
    error_rms: np.ndarray = np.sqrt(np.mean(absolute_error * absolute_error, axis=1))
    trajectory_figure: Any
    trajectory_axis: Any
    trajectory_figure, trajectory_axis = plt.subplots(figsize=(10.0, 5.0))
    trajectory_axis.plot(time_values, error_envelope, label="Maximum absolute state error")
    trajectory_axis.plot(time_values, error_rms, label="RMS state error")
    trajectory_axis.set_xlabel("Time [s]")
    trajectory_axis.set_ylabel("Absolute error")
    trajectory_axis.set_title("ANDES versus VeraGrid RMS trajectory error")
    trajectory_axis.grid(True, alpha=0.3)
    trajectory_axis.legend()
    trajectory_figure.tight_layout()
    trajectory_figure.savefig(output_directory / "trajectory_error_over_time.png", dpi=180)

    segment_only: pd.DataFrame = segment_frame.iloc[1:, :]
    segment_figure: Any
    segment_axis: Any
    segment_figure, segment_axis = plt.subplots(figsize=(9.0, 5.0))
    segment_positions: np.ndarray = np.arange(segment_only.shape[0], dtype=float)
    segment_axis.bar(segment_positions - 0.18, segment_only["max_abs_error"], width=0.36, label="Max abs")
    segment_axis.bar(segment_positions + 0.18, segment_only["rmse"], width=0.36, label="RMSE")
    segment_axis.set_xticks(segment_positions, list(segment_only["segment"]))
    segment_axis.set_ylabel("Error")
    segment_axis.set_title("Numerical error by time segment")
    segment_axis.grid(True, axis="y", alpha=0.3)
    segment_axis.legend()
    segment_figure.tight_layout()
    segment_figure.savefig(output_directory / "segment_error_comparison.png", dpi=180)

    # Plot the directly comparable calculation beside the architecture-
    # dependent workflow total. Engine-specific preparation subcomponents are
    # kept out so they cannot be mistaken for equivalent internal operations.
    timing_plot_frame: pd.DataFrame = timing_frame.loc[
        timing_frame["timing_role"].isin(list((
            "COMPARABLE CALCULATION",
            "POST-POWER-FLOW WORKFLOW TOTAL (architecture-dependent sum)",
        ))),
        :,
    ].dropna(subset=list(("andes_s", "veragrid_s")))
    timing_figure: Any
    timing_axis: Any
    timing_figure, timing_axis = plt.subplots(figsize=(11.0, 6.0))
    timing_positions: np.ndarray = np.arange(timing_plot_frame.shape[0], dtype=float)
    andes_errors: np.ndarray = np.minimum(
        timing_plot_frame["andes_std_s"].to_numpy(dtype=float),
        0.999 * timing_plot_frame["andes_s"].to_numpy(dtype=float),
    )
    veragrid_errors: np.ndarray = np.minimum(
        timing_plot_frame["veragrid_std_s"].to_numpy(dtype=float),
        0.999 * timing_plot_frame["veragrid_s"].to_numpy(dtype=float),
    )
    timing_axis.barh(
        timing_positions - 0.18,
        timing_plot_frame["andes_s"],
        height=0.36,
        xerr=andes_errors,
        capsize=3.0,
        label="ANDES mean ± sample standard deviation",
    )
    timing_axis.barh(
        timing_positions + 0.18,
        timing_plot_frame["veragrid_s"],
        height=0.36,
        xerr=veragrid_errors,
        capsize=3.0,
        label="VeraGrid mean ± sample standard deviation",
    )
    timing_axis.set_yticks(timing_positions, list(timing_plot_frame["phase"]))
    timing_axis.set_xscale("log")
    timing_axis.set_xlabel("Wall-clock time [s], logarithmic scale")
    timing_axis.set_title("RMS benchmark timing by phase (10 repetitions)")
    timing_axis.grid(True, axis="x", alpha=0.3)
    timing_axis.legend()
    timing_figure.tight_layout()
    timing_figure.savefig(output_directory / "timing_comparison.png", dpi=180)

    # The numerical envelope can hide which physical models dominate. Plot the
    # four largest-error states directly so initialization offsets, divergence
    # and post-event response can be distinguished by eye.
    state_error: np.ndarray = np.max(np.abs(veragrid_values - andes_values), axis=0)
    interesting_count: int = min(4, len(labels))
    interesting_indexes: np.ndarray = np.argsort(state_error)[-interesting_count:][::-1]
    state_figure: Any
    state_axes: Any
    state_figure, state_axes = plt.subplots(
        interesting_count,
        1,
        figsize=(11.0, 2.8 * interesting_count),
        sharex=True,
        squeeze=False,
    )
    plot_position: int
    for plot_position in range(interesting_count):
        state_index: int = int(interesting_indexes[plot_position])
        state_axis: Any = state_axes[plot_position, 0]
        state_axis.plot(time_values, andes_values[:, state_index], label="ANDES", linewidth=1.4)
        state_axis.plot(
            time_values,
            veragrid_values[:, state_index],
            label="VeraGrid",
            linewidth=1.1,
            linestyle="--",
        )
        if event_time is not None:
            state_axis.axvline(event_time, color="black", linewidth=0.8, linestyle=":", label="Event")
        else:
            pass
        state_axis.set_ylabel(labels[state_index])
        state_axis.grid(True, alpha=0.3)
        if plot_position == 0:
            state_axis.legend(loc="best")
        else:
            pass
    state_axes[interesting_count - 1, 0].set_xlabel("Time [s]")
    state_figure.suptitle("Representative physical state trajectories")
    state_figure.tight_layout()
    state_figure.savefig(output_directory / "representative_state_trajectories.png", dpi=180)

    if show_figures:
        plt.show(block=False)
    else:
        plt.close("all")


def build_text_report(
    system_name: str,
    scenario_name: str,
    validation_messages: list[str],
    matched_labels: list[str],
    unmatched_andes: list[str],
    unmatched_veragrid: list[str],
    segment_frame: pd.DataFrame,
    per_state_frame: pd.DataFrame,
    timing_frame: pd.DataFrame,
    angle_offset_rad: float,
) -> str:
    """Build the persistent human-readable RMS comparison report.

    :param system_name: Compared system.
    :param scenario_name: ``base`` or ``event``.
    :param validation_messages: Numerical configuration checks.
    :param matched_labels: Common state labels.
    :param unmatched_andes: ANDES-only states.
    :param unmatched_veragrid: VeraGrid-only states.
    :param segment_frame: Error metrics by horizon segment.
    :param per_state_frame: Error metrics for every common physical state.
    :param timing_frame: Timing comparison by workflow phase.
    :param angle_offset_rad: Common rotor-angle reference removed from VeraGrid.
    :return: Complete report text.
    """
    lines: list[str] = list()
    lines.append(f"RMS DYNAMIC BENCHMARK: {case_label(system_name)} [{scenario_name}]")
    lines.append("=" * 78)
    lines.append("")
    lines.append("NUMERICAL CONFIGURATION VALIDATION")
    lines.extend(validation_messages)
    lines.append("")
    lines.append("POWER-FLOW INPUT")
    lines.append("The reported power-flow phase is the converged solution used to initialize RMS.")
    lines.append("")
    lines.append("STATE ALIGNMENT")
    lines.append(f"Common physical states compared: {len(matched_labels)}")
    lines.append(f"Rotor-angle gauge offset removed from VeraGrid delta states: {angle_offset_rad:.12e} rad")
    lines.append(f"ANDES-only implementation/measurement states: {len(unmatched_andes)}")
    lines.append(f"VeraGrid-only or unmapped states: {len(unmatched_veragrid)}")
    if len(unmatched_andes) > 0:
        lines.append("ANDES-only states: " + ", ".join(unmatched_andes))
    else:
        lines.append("ANDES-only states: none")
    if len(unmatched_veragrid) > 0:
        lines.append("VeraGrid-only/unmapped states: " + ", ".join(unmatched_veragrid))
    else:
        lines.append("VeraGrid-only/unmapped states: none")
    lines.append("")
    lines.append("NUMERICAL RESULTS: TOTAL AND FOUR EQUAL TIME SEGMENTS")
    lines.append(segment_frame.to_string(index=False, float_format=format_report_float))
    lines.append("")
    lines.append("FIVE PHYSICAL STATES WITH THE LARGEST ABSOLUTE DIFFERENCE")
    lines.append(per_state_frame.iloc[:5, :].to_string(index=False, float_format=format_report_float))
    lines.append("")
    lines.append("TIMING PHASE DEFINITIONS")
    definition_index: int
    for definition_index in range(timing_frame.shape[0]):
        lines.append(
            f"- {timing_frame.iloc[definition_index]['phase']}: "
            f"{timing_frame.iloc[definition_index]['what_it_contains']} "
            f"[{timing_frame.iloc[definition_index]['timing_role']}]"
        )
    lines.append("")
    lines.append("TIMING COMPARISON BY PHASE")
    lines.append(timing_frame.to_string(index=False, float_format=format_report_float))
    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("RMS integration is the direct calculation-stage comparison.")
    lines.append("The post-power-flow workflow total adds each engine's own preparation stage.")
    lines.append("That preparation is architecture-dependent: ANDES reuses pregenerated numerical")
    lines.append("functions, while VeraGrid constructs and compiles its RMS problem at this point.")
    lines.append("Result-file export is reported only as a diagnostic phase and is outside the total.")
    lines.append("Case/model preparation, power flow, script overhead, comparison and figure")
    lines.append("generation remain outside the reported measures. Values are wall-clock times, not CPU time.")
    lines.append("Internal RHS/Jacobian/linear-solver timings are exported only for VeraGrid because")
    lines.append("ANDES 2.0 does not expose equivalent phase accumulators without instrumenting its engine.")
    return "\n".join(lines) + "\n"


def compare_rms_case(
    system_name: str,
    show_figures: bool = True,
    scenario_name: str = "base",
) -> None:
    """Compare one already-generated ANDES/VeraGrid RMS result pair.

    :param system_name: Benchmark system to compare.
    :param show_figures: Display figures as well as saving them.
    :param scenario_name: ``base`` or ``event``.
    :return: None.
    """
    andes_directory: Path = engine_results_directory(system_name, "ANDES", scenario_name)
    veragrid_directory: Path = engine_results_directory(system_name, "VeraGrid", scenario_name)
    output_directory: Path = comparison_directory(system_name, scenario_name)
    output_directory.mkdir(parents=True, exist_ok=True)

    andes_metadata: dict[str, str] = load_key_value_table(andes_directory / "metadata.csv")
    veragrid_metadata: dict[str, str] = load_key_value_table(veragrid_directory / "metadata.csv")
    validation_messages: list[str] = validate_numerical_configuration(
        andes_metadata=andes_metadata,
        veragrid_metadata=veragrid_metadata,
    )
    andes_frame: pd.DataFrame = pd.read_csv(andes_directory / "state_trajectory.csv")
    veragrid_frame: pd.DataFrame = pd.read_csv(veragrid_directory / "state_trajectory.csv")
    alignment_output: tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[str], list[str]] = (
        align_state_trajectories(andes_frame=andes_frame, veragrid_frame=veragrid_frame)
    )
    time_values: np.ndarray = alignment_output[0]
    andes_values: np.ndarray = alignment_output[1]
    veragrid_values: np.ndarray = alignment_output[2]
    matched_labels: list[str] = alignment_output[3]
    unmatched_andes: list[str] = alignment_output[4]
    unmatched_veragrid: list[str] = alignment_output[5]
    angle_offset_rad: float
    veragrid_values, angle_offset_rad = align_rotor_angle_reference(
        labels=matched_labels,
        andes_values=andes_values,
        veragrid_values=veragrid_values,
    )

    segment_rows: list[tuple[str, float, float, float, float, float, int]] = calculate_segment_rows(
        time_values=time_values,
        andes_values=andes_values,
        veragrid_values=veragrid_values,
    )
    segment_frame: pd.DataFrame = pd.DataFrame(
        segment_rows,
        columns=list((
            "segment",
            "start_s",
            "end_s",
            "max_abs_error",
            "mean_abs_error",
            "rmse",
            "sample_count",
        )),
    )
    per_state_frame: pd.DataFrame = calculate_per_state_frame(
        labels=matched_labels,
        time_values=time_values,
        andes_values=andes_values,
        veragrid_values=veragrid_values,
    )
    andes_timings: dict[str, str] = load_key_value_table(andes_directory / "timings.csv")
    veragrid_timings: dict[str, str] = load_key_value_table(veragrid_directory / "timings.csv")
    andes_standard_deviations: dict[str, float] = load_timing_standard_deviations(
        andes_directory / "timing_statistics.csv"
    )
    veragrid_standard_deviations: dict[str, float] = load_timing_standard_deviations(
        veragrid_directory / "timing_statistics.csv"
    )
    timing_frame: pd.DataFrame = build_timing_comparison(
        andes_timings=andes_timings,
        veragrid_timings=veragrid_timings,
        andes_standard_deviations=andes_standard_deviations,
        veragrid_standard_deviations=veragrid_standard_deviations,
    )

    segment_frame.to_csv(output_directory / "segment_error_metrics.csv", index=False, float_format="%.12e")
    per_state_frame.to_csv(output_directory / "per_state_error_metrics.csv", index=False, float_format="%.12e")
    timing_frame.to_csv(output_directory / "timing_comparison.csv", index=False, float_format="%.12e")

    # Rebuild one readable timing summary at the system results root. Reading
    # the saved scenario CSV files keeps repeated comparisons deterministic.
    results_directory: Path = output_directory.parent.parent
    timing_summary_lines: list[str] = list()
    timing_summary_lines.append(f"RMS TIMING SUMMARY: {case_label(system_name)}")
    timing_summary_lines.append("=" * 78)
    timing_summary_lines.append("ANDES/VG = ANDES seconds / VeraGrid seconds")
    timing_summary_lines.append("Above 1: VeraGrid faster. Below 1: ANDES faster.")
    timing_summary_lines.append("")
    timing_summary_lines.append("PHASE DEFINITIONS")
    definition_index: int
    for definition_index in range(timing_frame.shape[0]):
        timing_summary_lines.append(
            f"- {timing_frame.iloc[definition_index]['phase']}: "
            f"{timing_frame.iloc[definition_index]['what_it_contains']} "
            f"[{timing_frame.iloc[definition_index]['timing_role']}]"
        )
    summary_scenario: str
    for summary_scenario in ("base", "event"):
        scenario_timing_path: Path = (
            results_directory / "comparison" / summary_scenario / "timing_comparison.csv"
        )
        if scenario_timing_path.is_file():
            scenario_timing_frame: pd.DataFrame = pd.read_csv(scenario_timing_path)
            if "andes_over_veragrid" in scenario_timing_frame.columns:
                pass
            else:
                # Older result folders stored the inverse ratio. Reconstruct
                # the current presentation while base and event are refreshed.
                scenario_timing_frame["andes_over_veragrid"] = (
                    scenario_timing_frame["andes_s"]
                    / scenario_timing_frame["veragrid_s"]
                )
            standard_deviation_column: str
            for standard_deviation_column in ("andes_std_s", "veragrid_std_s"):
                if standard_deviation_column in scenario_timing_frame.columns:
                    pass
                else:
                    # A scenario from the earlier single-observation format
                    # can coexist briefly while the two scenarios are being
                    # regenerated in sequence.
                    scenario_timing_frame[standard_deviation_column] = np.nan
            summary_columns: list[str] = list((
                "phase",
                "andes_s",
                "andes_std_s",
                "veragrid_s",
                "veragrid_std_s",
                "andes_over_veragrid",
                "timing_role",
            ))
            timing_summary_lines.append("")
            timing_summary_lines.append(summary_scenario.upper())
            timing_summary_lines.append("-" * 78)
            timing_summary_lines.append(
                scenario_timing_frame.loc[:, summary_columns].to_string(
                    index=False,
                    float_format=format_report_float,
                )
            )
        else:
            pass
    (results_directory / "timing_summary.txt").write_text(
        "\n".join(timing_summary_lines) + "\n",
        encoding="utf-8",
    )

    report_text: str = build_text_report(
        system_name=system_name,
        scenario_name=scenario_name,
        validation_messages=validation_messages,
        matched_labels=matched_labels,
        unmatched_andes=unmatched_andes,
        unmatched_veragrid=unmatched_veragrid,
        segment_frame=segment_frame,
        per_state_frame=per_state_frame,
        timing_frame=timing_frame,
        angle_offset_rad=angle_offset_rad,
    )
    (output_directory / "comparison_report.txt").write_text(report_text, encoding="utf-8")
    print(report_text)
    if scenario_name == "event":
        event_time: float | None = float(andes_metadata["event_time_s"])
    else:
        event_time = None
    save_comparison_figures(
        output_directory=output_directory,
        time_values=time_values,
        andes_values=andes_values,
        veragrid_values=veragrid_values,
        segment_frame=segment_frame,
        timing_frame=timing_frame,
        labels=matched_labels,
        event_time=event_time,
        show_figures=show_figures,
    )


