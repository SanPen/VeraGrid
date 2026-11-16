# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Run and export ANDES small-signal benchmarks for VeraGrid comparisons."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import time
from typing import Any

import andes
import numpy as np
import pandas as pd

from benchmarks.dynamics_andes.small_signal.small_signal_timing import andes_small_signal_timing_phase_names
from benchmarks.dynamics_andes.small_signal.small_signal_timing import elapsed_seconds
from benchmarks.dynamics_andes.small_signal.small_signal_timing import finalize_normal_workflow_timings
from benchmarks.dynamics_andes.small_signal.small_signal_timing import save_benchmark_timings


SYSTEM: str = "all"  # "Kundur", "IEEE14", "IEEE39", "NPCC140", "WECC179" or "all"


def main() -> None:
    """Generate the selected standard ANDES small-signal references.

    Change ``SYSTEM`` at the top of this file to select one system or all five.
    Results are always written into the matching system folder.

    :return: None.
    """
    repetitions: int = 10

    # Check the value here so a typo can never select a different case silently.
    valid_systems: tuple[str, ...] = (
        "Kundur",
        "IEEE14",
        "IEEE39",
        "NPCC140",
        "WECC179",
    )
    if SYSTEM == "all" or SYSTEM in valid_systems:
        pass
    else:
        raise ValueError(
            f"Unknown SYSTEM {SYSTEM!r}. Choose one of {valid_systems} or 'all'."
        )

    # Expand the visible selection into the systems that will be generated.
    if SYSTEM == "all":
        selected_systems: tuple[str, ...] = valid_systems
    else:
        selected_systems = (SYSTEM,)

    # Every standard case follows exactly the same load, solve and export path.
    script_directory: Path = Path(__file__).resolve().parent
    selected_system: str
    for selected_system in selected_systems:
        case_path: Path = _resolve_case_path(
            system_name=selected_system,
            script_dir=script_directory,
        )
        case_label: str = _case_label(system_name=selected_system)
        power_flow_tolerance: float = _power_flow_tolerance(system_name=selected_system)
        phase_names: tuple[str, ...] = andes_small_signal_timing_phase_names()
        timing_samples: np.ndarray = np.empty(
            (repetitions, len(phase_names)),
            dtype=float,
        )
        state_count: int = 0
        mode_count: int = 0
        repetition_index: int
        for repetition_index in range(repetitions):
            print(
                f"\nANDES {selected_system} small signal: "
                f"repetition {repetition_index + 1}/{repetitions}"
            )
            repetition_result: tuple[
                np.ndarray,
                np.ndarray,
                np.ndarray,
                np.ndarray,
                np.ndarray,
                np.ndarray,
            ] = run_andes_stability(
                case_path=case_path,
                case_label=case_label,
                output_dir=None,
                power_flow_tolerance=power_flow_tolerance,
            )
            timing_samples[repetition_index, :] = repetition_result[5]
            state_count = int(repetition_result[0].shape[0])
            mode_count = int(repetition_result[1].size)

        results_directory: Path = (
            script_directory / selected_system / "results" / "ANDES"
        )
        save_benchmark_timings(
            output_directory=results_directory,
            engine_label="Andes",
            case_label=case_label,
            phase_names=phase_names,
            timing_samples=timing_samples,
            state_count=state_count,
            mode_count=mode_count,
        )


def _case_label(system_name: str) -> str:
    """Return the result-folder label for a preset case.

    :param system_name: Selected benchmark system.
    :return: Stable result label.
    """
    if system_name == "Kundur":
        return "KUNDUR_no_shunt"
    elif system_name == "IEEE14":
        return "IEEE14"
    elif system_name == "IEEE39":
        return "IEEE39"
    elif system_name == "NPCC140":
        return "NPCC140"
    else:
        return "WECC179"


def _resolve_case_path(system_name: str, script_dir: Path) -> Path:
    """Resolve the physical file for a preset case.

    :param system_name: Selected benchmark system.
    :param script_dir: Directory containing this script.
    :return: Absolute ANDES case path.
    """
    if system_name == "Kundur":
        case_path: Path = script_dir.parent / "kundur_ieee_no_shunt.json"
    elif system_name == "IEEE14":
        case_path = Path(andes.get_case("ieee14/ieee14_full.xlsx"))
    elif system_name == "IEEE39":
        case_path = Path(andes.get_case("ieee39/ieee39_full.xlsx"))
    elif system_name == "NPCC140":
        case_path = Path(andes.get_case("npcc/npcc.xlsx"))
    else:
        case_path = Path(andes.get_case("wecc/wecc_full.xlsx"))
    return case_path.resolve()


def _power_flow_tolerance(system_name: str) -> float:
    """Return the strictest convergent ANDES tolerance for one preset.

    The WECC 179 starting point converges in ANDES 2.0 down to ``1e-10`` but
    not to ``1e-13``.  The other repository benchmarks retain the tighter
    common tolerance.

    :param system_name: Selected benchmark system.
    :return: ANDES power-flow tolerance.
    """
    if system_name == "WECC179":
        return 1.0e-10
    else:
        return 1.0e-13


def _format_complex(value: complex, decimals: int = 15) -> str:
    """Format one complex matrix value without discarding precision.

    :param value: Complex value to serialize.
    :param decimals: Scientific-notation decimal places.
    :return: CSV-safe complex representation.
    """
    number: complex = complex(value)
    return f"{number.real:.{decimals}e}{number.imag:+.{decimals}e}j"


def _write_state_matrix(
    output_path: Path,
    state_matrix: np.ndarray,
    state_names: list[str],
) -> None:
    """Write a square state matrix with state names on both axes.

    :param output_path: Destination CSV path.
    :param state_matrix: Reduced ANDES state matrix.
    :param state_names: Reduced ANDES state labels.
    :return: None.
    """
    matrix: np.ndarray = np.asarray(state_matrix, dtype=complex)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer: Any = csv.writer(csv_file)
        writer.writerow(list(("equation", *state_names)))
        row_index: int
        for row_index in range(matrix.shape[0]):
            row_values: list[str] = list()
            column_index: int
            for column_index in range(matrix.shape[1]):
                row_values.append(_format_complex(matrix[row_index, column_index]))
            writer.writerow(list((state_names[row_index], *row_values)))


def _write_static_tables(system: Any, results_dir: Path, case_label: str) -> None:
    """Write solved static-device tables for operating-point auditing.

    :param system: Solved ANDES system.
    :param results_dir: Destination result directory.
    :param case_label: Filename-safe case label.
    :return: None.
    """
    table_names: tuple[str, ...] = ("Bus", "Slack", "PV", "PQ", "Shunt", "Line")
    table_name: str
    for table_name in table_names:
        model: Any = system.models[table_name]
        table: pd.DataFrame = model.as_df().reset_index(drop=True)
        table.to_csv(
            results_dir / f"{table_name.lower()}_table_Andes_{case_label}.csv",
            index=False,
        )

    # Bus.as_df() contains workbook guesses.  The DAE variables below contain
    # the actual solved voltage operating point used by EIG.
    bus_model: Any = system.models["Bus"]
    solved_bus_table: pd.DataFrame = pd.DataFrame(
        dict(
            name=np.asarray(bus_model.name.v, dtype=str),
            Vm=np.asarray(bus_model.v.v, dtype=float),
            Va_rad=np.asarray(bus_model.a.v, dtype=float),
        )
    )
    solved_bus_table.to_csv(
        results_dir / f"solved_bus_Andes_{case_label}.csv",
        index=False,
    )


def _fold_zero_ieeest_input_filter_states(system: Any) -> list[str]:
    """Reclassify exact IEEEST input-filter pass-through states as algebraic.

    ANDES represents the second-order ``F1`` and ``F2`` blocks with two state
    variables even when every denominator and numerator coefficient is zero.
    One state per block already has a zero mass coefficient; the other must be
    folded as well to obtain the exact algebraic pass-through used by the
    physical reduced model.

    :param system: Initialized ANDES system with populated DAE state names.
    :return: Names of the additional states assigned a zero mass coefficient.
    """
    ieeest_model: Any | None = system.models.get("IEEEST", None)
    folded_state_names: list[str] = list()
    if ieeest_model is None or int(ieeest_model.n) == 0:
        pass
    else:
        device_index: int
        for device_index in range(int(ieeest_model.n)):
            coefficients: np.ndarray = np.asarray(
                (
                    ieeest_model.A1.v[device_index],
                    ieeest_model.A2.v[device_index],
                    ieeest_model.A3.v[device_index],
                    ieeest_model.A4.v[device_index],
                    ieeest_model.A5.v[device_index],
                    ieeest_model.A6.v[device_index],
                ),
                dtype=float,
            )
            if bool(np.all(np.abs(coefficients) <= 1.0e-15)):
                device_ordinal: int = device_index + 1
                folded_state_names.append(f"F1_y IEEEST {device_ordinal}")
                folded_state_names.append(f"F2_x2 IEEEST {device_ordinal}")
            else:
                pass

    dae_state_names: np.ndarray = np.asarray(system.dae.x_name, dtype=str)
    folded_state_name: str
    for folded_state_name in folded_state_names:
        state_indexes: np.ndarray = np.flatnonzero(dae_state_names == folded_state_name)
        if state_indexes.size == 1:
            system.dae.Tf[int(state_indexes[0])] = 0.0
        else:
            raise ValueError(
                f"Expected one ANDES state named {folded_state_name!r}; "
                f"found {state_indexes.size}."
            )
    return folded_state_names


def _fold_unused_bus_frequency_states(system: Any) -> list[str]:
    """Fold BusFreq devices that no enabled controller consumes.

    Some published workbooks instantiate one BusFreq device per generator even
    though every stabilizer is configured for rotor speed or electrical power.
    Their decoupled filter poles are measurement-implementation modes, not
    physical network modes. Folding them before EIG makes the exported spectrum
    exactly the common physical model while retaining every consumed BusFreq.

    :param system: Initialized ANDES system.
    :return: Folded BusFreq state names.
    """
    busfreq_model: Any | None = system.models.get("BusFreq", None)
    folded_state_names: list[str] = list()
    if busfreq_model is None or int(busfreq_model.n) == 0:
        return folded_state_names
    else:
        pass
    referenced_indexes: set[str] = set()
    controller_name: str
    for controller_name in ("IEEEST", "ST2CUT"):
        controller: Any | None = system.models.get(controller_name, None)
        if controller is None or int(controller.n) == 0:
            pass
        else:
            device_index: int
            for device_index in range(int(controller.n)):
                if int(controller.MODE.v[device_index]) == 2:
                    referenced_indexes.add(str(controller.busf.v[device_index]))
                else:
                    pass
                if controller_name == "ST2CUT" and int(controller.MODE2.v[device_index]) == 2:
                    referenced_indexes.add(str(controller.busf2.v[device_index]))
                else:
                    pass
    busfreq_index: int
    for busfreq_index in range(int(busfreq_model.n)):
        model_index: str = str(busfreq_model.idx.v[busfreq_index])
        if model_index in referenced_indexes:
            pass
        else:
            device_ordinal: int = busfreq_index + 1
            folded_state_names.append(f"L_y BusFreq {device_ordinal}")
            folded_state_names.append(f"WO_x BusFreq {device_ordinal}")
    dae_state_names: np.ndarray = np.asarray(system.dae.x_name, dtype=str)
    state_name: str
    for state_name in folded_state_names:
        state_indexes: np.ndarray = np.flatnonzero(dae_state_names == state_name)
        if state_indexes.size == 1:
            system.dae.Tf[int(state_indexes[0])] = 0.0
        else:
            raise ValueError(
                f"Expected one ANDES state named {state_name!r}; found {state_indexes.size}."
            )
    return folded_state_names


def run_andes_stability(
    case_path: Path,
    case_label: str,
    output_dir: Path | None = None,
    power_flow_tolerance: float = 1.0e-13,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Solve and export one ANDES small-signal case.

    :param case_path: ANDES-readable case file.
    :param case_label: Filename-safe label used for exported artifacts.
    :param output_dir: Optional explicit destination directory.
    :param power_flow_tolerance: Newton power-flow convergence tolerance.
    :return: State matrix, eigenvalues, right vectors, left vectors,
        participation factors and one timing vector.
    """
    total_start: float = time.perf_counter()
    timings: dict[str, float] = dict()

    # Stage 1: identify the exact source and prepare a deterministic destination.
    resolved_case_path: Path = case_path.resolve()
    source_hash: str = hashlib.sha256(resolved_case_path.read_bytes()).hexdigest()
    script_dir: Path = Path(__file__).resolve().parent
    if output_dir is None:
        if case_label == "KUNDUR_no_shunt":
            case_folder_name: str = "Kundur"
        elif case_label == "IEEE14":
            case_folder_name = "IEEE14"
        elif case_label == "IEEE39":
            case_folder_name = "IEEE39"
        elif case_label == "NPCC140":
            case_folder_name = "NPCC140"
        elif case_label == "WECC179":
            case_folder_name = "WECC179"
        else:
            case_folder_name = case_label
        results_dir: Path = script_dir / case_folder_name / "results" / "ANDES"
    else:
        results_dir = output_dir.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    np.set_printoptions(precision=15, suppress=False)
    print(f"Loading case: {resolved_case_path}")
    print(f"ANDES package: {Path(andes.__file__).resolve()}")
    print(f"ANDES version: {andes.__version__}")
    print(f"Case SHA-256: {source_hash}")

    # Stage 2: solve a constant-power operating point using a strict tolerance.
    model_start: float = time.perf_counter()
    system: Any = andes.load(
        str(resolved_case_path),
        default_config=True,
        setup=False,
    )
    system.files.no_output = True
    system.PQ.config.p2p = 1.0
    system.PQ.config.p2i = 0
    system.PQ.config.p2z = 0
    system.PQ.config.q2q = 1.0
    system.PQ.config.q2i = 0
    system.PQ.config.q2z = 0
    system.PFlow.config.tol = power_flow_tolerance
    timings["case_and_model_build"] = elapsed_seconds(model_start)
    setup_start: float = time.perf_counter()
    setup_success: bool = bool(system.setup())
    timings["andes_system_setup"] = elapsed_seconds(setup_start)
    if setup_success:
        pass
    else:
        raise RuntimeError(
            f"ANDES symbolic-to-numeric setup failed for {resolved_case_path}."
        )
    # The first solve initializes reusable numerical code and is not compared.
    power_flow_warmup_start: float = time.perf_counter()
    power_flow_warmup_success: bool = bool(system.PFlow.run())
    timings["diagnostic_power_flow_warmup"] = elapsed_seconds(
        power_flow_warmup_start
    )
    if power_flow_warmup_success:
        pass
    else:
        raise RuntimeError(
            f"ANDES power-flow warm-up did not converge for {resolved_case_path} "
            f"with tolerance {power_flow_tolerance:.3e}."
        )

    # The second solve supplies the warm operating point used by the benchmark.
    power_flow_start: float = time.perf_counter()
    power_flow_success: bool = bool(system.PFlow.run())
    timings["power_flow"] = elapsed_seconds(power_flow_start)
    if power_flow_success:
        pass
    else:
        raise RuntimeError(
            f"Warm ANDES power flow did not converge for {resolved_case_path} "
            f"with tolerance {power_flow_tolerance:.3e}."
        )

    # Stage 3: initialize the DAE, canonicalize exact zero-parameter IEEEST
    # pass-throughs, then let ANDES fold all zero-mass states and calculate EIG.
    eig: Any = system.EIG
    initialization_start: float = time.perf_counter()
    system.TDS.init()
    system.TDS.itm_step()
    timings["dynamic_initialization"] = elapsed_seconds(initialization_start)
    preprocessing_start: float = time.perf_counter()
    folded_ieeest_states: list[str] = _fold_zero_ieeest_input_filter_states(system)
    folded_bus_frequency_states: list[str] = _fold_unused_bus_frequency_states(system)
    timings["benchmark_preprocessing"] = elapsed_seconds(preprocessing_start)
    # Execute the same complete EIG call once before measurement so runtime
    # caches and numerical-library initialization have identical warm status
    # to the measured VeraGrid call. This first call is recorded but excluded
    # from both benchmark totals.
    warmup_start: float = time.perf_counter()
    eig.run()
    timings["diagnostic_small_signal_warmup"] = elapsed_seconds(warmup_start)

    # Measure a second complete EIG call on the same initialized problem. The
    # resulting matrices and modal quantities are the exported benchmark result.
    small_signal_start: float = time.perf_counter()
    eig.run()
    timings["small_signal_total"] = elapsed_seconds(small_signal_start)
    state_names: list[str] = list(eig.x_name)
    state_matrix: np.ndarray = np.asarray(eig.As, dtype=complex)
    eigenvalues: np.ndarray = np.asarray(eig.mu, dtype=complex)
    right_eigenvectors: np.ndarray = np.asarray(eig.N, dtype=complex)
    left_eigenvectors: np.ndarray = np.asarray(eig.W, dtype=complex)
    participation_factors: np.ndarray = np.asarray(eig.pfactors, dtype=float)

    print(f"\nReduced differential states: {len(state_names)}")
    print(f"Zero-time-constant states folded as constraints: {len(eig.zstate_idx)}")
    if len(folded_ieeest_states) > 0:
        print("Canonical zero-parameter IEEEST states folded as constraints:")
        folded_ieeest_state: str
        for folded_ieeest_state in folded_ieeest_states:
            print(f"  - {folded_ieeest_state}")
    else:
        pass
    if len(folded_bus_frequency_states) > 0:
        print("Unused BusFreq states folded as constraints:")
        folded_bus_frequency_state: str
        for folded_bus_frequency_state in folded_bus_frequency_states:
            print(f"  - {folded_bus_frequency_state}")
    else:
        pass

    # Stage 4: export the common inputs consumed by the visual comparator.
    export_start: float = time.perf_counter()
    pd.DataFrame(eigenvalues).to_csv(
        results_dir / f"Eigenvalues_results_Andes_{case_label}.csv",
        index=False,
        header=False,
    )
    pd.DataFrame(participation_factors.T).to_csv(
        results_dir / f"pfactors_results_Andes_{case_label}.csv",
        index=False,
        header=False,
        float_format="%.10f",
    )
    _write_state_matrix(
        output_path=results_dir / f"state_matrix_results_Andes_{case_label}.csv",
        state_matrix=state_matrix,
        state_names=state_names,
    )
    pd.DataFrame(
        list(enumerate(state_names)),
        columns=list(("index", "state")),
    ).to_csv(results_dir / f"state_names_Andes_{case_label}.csv", index=False)
    _write_static_tables(system=system, results_dir=results_dir, case_label=case_label)
    timings["result_export"] = elapsed_seconds(export_start)
    normal_component_names: tuple[str, ...] = (
        "case_and_model_build",
        "andes_system_setup",
        "power_flow",
        "dynamic_initialization",
        "benchmark_preprocessing",
        "small_signal_total",
        "result_export",
    )
    diagnostic_names: tuple[str, ...] = (
        "diagnostic_power_flow_warmup",
        "diagnostic_small_signal_warmup",
    )
    finalize_normal_workflow_timings(
        timings=timings,
        total_start=total_start,
        normal_component_names=normal_component_names,
        diagnostic_names=diagnostic_names,
    )
    timings["dynamic_problem_preparation"] = (
        timings["andes_system_setup"]
        + timings["dynamic_initialization"]
        + timings["benchmark_preprocessing"]
    )
    timings["dynamic_simulation_total"] = (
        timings["dynamic_problem_preparation"] + timings["small_signal_total"]
    )
    timings["dynamic_results_total"] = (
        timings["dynamic_simulation_total"] + timings["result_export"]
    )
    phase_names: tuple[str, ...] = andes_small_signal_timing_phase_names()
    timing_values: np.ndarray = np.asarray(
        tuple(timings[phase_name] for phase_name in phase_names),
        dtype=float,
    )

    print("\nEigenvalues:")
    print(eigenvalues)
    print(f"\nANDES {case_label} results written to: {results_dir}")
    return (
        state_matrix,
        eigenvalues,
        right_eigenvectors,
        left_eigenvectors,
        participation_factors,
        timing_values,
    )


if __name__ == "__main__":
    main()
else:
    pass
