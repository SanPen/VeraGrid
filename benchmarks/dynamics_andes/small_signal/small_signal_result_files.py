# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Write the numerical files compared by the small-signal benchmarks."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from VeraGridEngine import SmallSignalStabilityRmsResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults


def save_small_signal_result_files(
    results: SmallSignalStabilityRmsResults,
    power_flow_results: PowerFlowResults,
    output_directory: Path,
    state_labels: list[str] | None = None,
) -> None:
    """Save one VeraGrid operating point, spectrum and linearization as CSV.

    :param results: Completed VeraGrid RMS small-signal results.
    :param power_flow_results: Operating point used by the linearization.
    :param output_directory: Directory receiving the numerical result files.
    :param state_labels: Optional ANDES-compatible labels for matrix rows and columns.
    :return: None.
    """
    output_directory.mkdir(parents=True, exist_ok=True)

    # Preserve the operating point because equivalent dynamics are meaningful
    # only when both programs linearize around the same bus solution.
    power_flow_results.get_bus_df().to_csv(
        output_directory / "power_flow_buses.csv",
        index=True,
    )
    power_flow_results.get_branch_df().to_csv(
        output_directory / "power_flow_branches.csv",
        index=True,
    )

    # Store every eigenvalue together with its damping and frequency measures.
    eigenvalues: np.ndarray = np.asarray(results.eigenvalues, dtype=complex).ravel()
    damping_ratios: np.ndarray = np.asarray(results.damping_ratios, dtype=float).ravel()
    frequencies_hz: np.ndarray = np.asarray(results.conjugate_frequencies, dtype=float).ravel()
    mode_numbers: np.ndarray = np.arange(1, eigenvalues.size + 1, dtype=int)
    mode_table: np.ndarray = np.column_stack(
        (
            mode_numbers,
            eigenvalues.real,
            eigenvalues.imag,
            damping_ratios,
            frequencies_hz,
        )
    )
    np.savetxt(
        output_directory / "modes.csv",
        mode_table,
        delimiter=",",
        header="mode,real_rad_per_s,imag_rad_per_s,damping_ratio,oscillation_frequency_hz",
        comments="",
        fmt=["%d", "%.12e", "%.12e", "%.12e", "%.12e"],
    )

    # Select labels once and use the same physical ordering for the state
    # matrix and participation factors.
    state_matrix: np.ndarray = np.asarray(results.state_matrix, dtype=complex)
    if state_labels is None:
        differential_labels: list[str] = list(np.asarray(results.stat_vars_array).astype(str))
        algebraic_labels: list[str] = list(np.asarray(results.algebraic_vars_array).astype(str))
        if len(differential_labels) == state_matrix.shape[0]:
            selected_labels: list[str] = differential_labels
        elif len(differential_labels) + len(algebraic_labels) == state_matrix.shape[0]:
            selected_labels = differential_labels + algebraic_labels
        else:
            selected_labels = [
                f"State {state_index + 1}"
                for state_index in range(state_matrix.shape[0])
            ]
    elif len(state_labels) == state_matrix.shape[0]:
        selected_labels = list(state_labels)
    else:
        raise ValueError(
            f"Received {len(state_labels)} labels for a "
            f"{state_matrix.shape[0]}-state benchmark."
        )

    # Write matrices with explicit row and column labels so the comparator can
    # align states without depending on their internal array positions.
    participation_factors: np.ndarray = np.asarray(results.participation_factors, dtype=float)
    if participation_factors.shape[0] == len(selected_labels):
        pass
    else:
        raise ValueError(
            f"Received {participation_factors.shape[0]} participation rows for "
            f"{len(selected_labels)} state labels."
        )
    mode_labels: list[str] = [
        f"Mode {mode_index + 1}"
        for mode_index in range(participation_factors.shape[1])
    ]
    with (output_directory / "participation_factors.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as participation_file:
        participation_file.write("state," + ",".join(mode_labels) + "\n")
        row_index: int
        for row_index in range(participation_factors.shape[0]):
            row_values: str = ",".join(
                f"{float(value):.12e}"
                for value in participation_factors[row_index, :]
            )
            participation_file.write(f"{selected_labels[row_index]},{row_values}\n")

    with (output_directory / "state_matrix.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as matrix_file:
        matrix_file.write("equation," + ",".join(selected_labels) + "\n")
        matrix_row_index: int
        for matrix_row_index in range(state_matrix.shape[0]):
            complex_values: str = ",".join(
                f"{complex(value).real:.12e}{complex(value).imag:+.12e}j"
                for value in state_matrix[matrix_row_index, :]
            )
            matrix_file.write(
                f"{selected_labels[matrix_row_index]},{complex_values}\n"
            )
