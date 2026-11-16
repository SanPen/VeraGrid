# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Compare saved ANDES and VeraGrid small-signal results.

The public case runners call ``compare_result_folders``.  The comparison then
loads the exported matrices, reconciles state labels, matches eigenvalues and
participation factors, and finally writes numerical summaries and figures.
Keeping this sequence here makes every case runner short while preserving one
consistent comparison method for all five networks.
"""

from __future__ import annotations

from contextlib import redirect_stderr
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import csv
import re
import warnings
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.table import Table
import numpy as np
from scipy.linalg import LinAlgWarning
from scipy.linalg import solve
from scipy.optimize import linear_sum_assignment



def _comparison_directory(case_label: str, output_dir: Path | None) -> Path:
    """Resolve the comparison folder for one small-signal case.

    :param case_label: Case label used for the default folder name.
    :param output_dir: Optional custom folder whose final name is retained.
    :return: Absolute comparison directory inside the small-signal folder.
    """
    small_signal_dir: Path = Path(__file__).resolve().parent
    if output_dir is None:
        if case_label == "KUNDUR_no_shunt":
            case_folder_name: str = "Kundur"
        else:
            case_folder_name = case_label
        comparison_dir: Path = small_signal_dir / case_folder_name / "results" / "comparison"
    else:
        comparison_dir = output_dir.resolve()
    return comparison_dir.resolve()


def _find_single_result_file(
    results_dir: Path,
    preferred_names: tuple[str, ...],
    glob_pattern: str,
) -> Path:
    """Find one result artifact using preferred names and a generic fallback.

    :param results_dir: Folder to inspect.
    :param preferred_names: Ordered exact filename candidates.
    :param glob_pattern: Fallback glob used when exact names are absent.
    :return: Discovered result file.
    :raises FileNotFoundError: If no unique artifact can be selected.
    """
    filename: str
    for filename in preferred_names:
        candidate: Path = results_dir / filename
        if candidate.is_file():
            return candidate
        else:
            pass

    matches: list[Path] = list(results_dir.glob(glob_pattern))
    if len(matches) == 1:
        return matches[0]
    else:
        raise FileNotFoundError(
            f"Could not select one '{glob_pattern}' artifact in {results_dir}. "
            f"Found {len(matches)} candidates."
        )


def _largest_difference_entries(
    difference: np.ndarray,
    row_labels: list[str],
    column_labels: list[str],
    top_n: int,
) -> tuple[np.ndarray, list[str]]:
    """Return magnitudes and readable labels for the largest matrix errors.

    :param difference: Matrix difference to rank.
    :param row_labels: Row labels.
    :param column_labels: Column labels.
    :param top_n: Maximum number of entries.
    :return: Descending magnitudes and ``row <- column`` labels.
    """
    magnitudes: np.ndarray = np.abs(np.asarray(difference, dtype=complex))
    count: int = min(top_n, int(magnitudes.size))
    flat_indexes: np.ndarray = np.argsort(magnitudes.ravel())[-count:][::-1]
    values: np.ndarray = magnitudes.ravel()[flat_indexes]
    labels: list[str] = list()
    flat_index: int
    for flat_index in flat_indexes.tolist():
        row_index: int
        column_index: int
        row_index, column_index = np.unravel_index(flat_index, magnitudes.shape)
        labels.append(f"{row_labels[row_index]} <- {column_labels[column_index]}")
    return values, labels


def _create_state_matrix_figure(
    andes_matrix: np.ndarray,
    veragrid_matrix: np.ndarray,
    difference: np.ndarray,
    row_labels: list[str],
    column_labels: list[str],
    case_label: str,
) -> Any:
    """Create the state-matrix visual audit figure.

    :param andes_matrix: Aligned ANDES matrix.
    :param veragrid_matrix: VeraGrid matrix.
    :param difference: VeraGrid-minus-ANDES matrix.
    :param row_labels: Common row labels.
    :param column_labels: Common column labels.
    :param case_label: Network label for the title.
    :return: Matplotlib figure.
    """
    error_values: np.ndarray
    error_labels: list[str]
    error_values, error_labels = _largest_difference_entries(
        difference=difference,
        row_labels=row_labels,
        column_labels=column_labels,
        top_n=15,
    )
    figure: Any
    axes: np.ndarray
    figure, axes = plt.subplots(2, 2, figsize=(17, 12))
    common_limit: float = float(
        max(
            np.max(np.abs(andes_matrix.real)),
            np.max(np.abs(veragrid_matrix.real)),
            1.0e-15,
        )
    )

    andes_image: Any = axes[0, 0].imshow(
        andes_matrix.real,
        aspect="auto",
        cmap="coolwarm",
        vmin=-common_limit,
        vmax=common_limit,
    )
    axes[0, 0].set_title("ANDES A (aligned)")
    axes[0, 0].set_xlabel("State column")
    axes[0, 0].set_ylabel("State equation")
    figure.colorbar(andes_image, ax=axes[0, 0], fraction=0.046, pad=0.04)

    veragrid_image: Any = axes[0, 1].imshow(
        veragrid_matrix.real,
        aspect="auto",
        cmap="coolwarm",
        vmin=-common_limit,
        vmax=common_limit,
    )
    axes[0, 1].set_title("VeraGrid A")
    axes[0, 1].set_xlabel("State column")
    axes[0, 1].set_ylabel("State equation")
    figure.colorbar(veragrid_image, ax=axes[0, 1], fraction=0.046, pad=0.04)

    log_error: np.ndarray = np.log10(np.maximum(np.abs(difference), 1.0e-16))
    error_image: Any = axes[1, 0].imshow(log_error, aspect="auto", cmap="magma")
    axes[1, 0].set_title("log10 |VeraGrid A - ANDES A|")
    axes[1, 0].set_xlabel("State column")
    axes[1, 0].set_ylabel("State equation")
    figure.colorbar(error_image, ax=axes[1, 0], fraction=0.046, pad=0.04)

    positions: np.ndarray = np.arange(error_values.size)
    axes[1, 1].barh(positions, error_values[::-1])
    axes[1, 1].set_yticks(positions)
    axes[1, 1].set_yticklabels(error_labels[::-1], fontsize=7)
    axes[1, 1].set_xscale("log")
    axes[1, 1].set_title("Largest |delta A| entries")
    axes[1, 1].set_xlabel("Absolute error")
    axes[1, 1].grid(True, axis="x", alpha=0.3)
    figure.suptitle(f"{case_label}: state-matrix comparison")
    figure.tight_layout()
    return figure


def _create_participation_figure(
    andes_participation: np.ndarray,
    veragrid_participation: np.ndarray,
    difference: np.ndarray,
    state_labels: list[str],
    case_label: str,
) -> Any:
    """Create the participation-factor visual audit figure.

    :param andes_participation: Aligned ANDES factors.
    :param veragrid_participation: Aligned VeraGrid factors.
    :param difference: VeraGrid-minus-ANDES factor matrix.
    :param state_labels: Common state labels.
    :param case_label: Network label for the title.
    :return: Matplotlib figure.
    """
    mode_labels: list[str] = list()
    mode_index: int
    for mode_index in range(difference.shape[1]):
        mode_labels.append(f"mode {mode_index + 1}")
    error_values: np.ndarray
    error_labels: list[str]
    error_values, error_labels = _largest_difference_entries(
        difference=difference,
        row_labels=state_labels,
        column_labels=mode_labels,
        top_n=15,
    )

    figure: Any
    axes: np.ndarray
    figure, axes = plt.subplots(2, 2, figsize=(17, 12))
    common_limit: float = float(
        max(
            np.max(andes_participation),
            np.max(veragrid_participation),
            1.0e-15,
        )
    )
    andes_image: Any = axes[0, 0].imshow(
        andes_participation,
        aspect="auto",
        cmap="viridis",
        vmin=0.0,
        vmax=common_limit,
    )
    axes[0, 0].set_title("ANDES participation factors")
    axes[0, 0].set_xlabel("Matched mode")
    axes[0, 0].set_ylabel("State")
    figure.colorbar(andes_image, ax=axes[0, 0], fraction=0.046, pad=0.04)

    veragrid_image: Any = axes[0, 1].imshow(
        veragrid_participation,
        aspect="auto",
        cmap="viridis",
        vmin=0.0,
        vmax=common_limit,
    )
    axes[0, 1].set_title("VeraGrid participation factors")
    axes[0, 1].set_xlabel("Matched mode")
    axes[0, 1].set_ylabel("State")
    figure.colorbar(veragrid_image, ax=axes[0, 1], fraction=0.046, pad=0.04)

    log_error: np.ndarray = np.log10(np.maximum(np.abs(difference), 1.0e-16))
    error_image: Any = axes[1, 0].imshow(log_error, aspect="auto", cmap="magma")
    axes[1, 0].set_title("log10 |delta participation factor|")
    axes[1, 0].set_xlabel("Matched mode")
    axes[1, 0].set_ylabel("State")
    figure.colorbar(error_image, ax=axes[1, 0], fraction=0.046, pad=0.04)

    positions: np.ndarray = np.arange(error_values.size)
    plotted_error_values: np.ndarray = np.maximum(error_values, 1.0e-16)
    axes[1, 1].barh(positions, plotted_error_values[::-1])
    axes[1, 1].set_yticks(positions)
    axes[1, 1].set_yticklabels(error_labels[::-1], fontsize=7)
    axes[1, 1].set_xscale("log")
    axes[1, 1].set_title("Largest participation-factor differences")
    axes[1, 1].set_xlabel("Absolute error")
    axes[1, 1].grid(True, axis="x", alpha=0.3)
    figure.suptitle(f"{case_label}: participation-factor comparison")
    figure.tight_layout()
    return figure


def _create_unaligned_state_matrix_figure(
    andes_matrix: np.ndarray,
    veragrid_matrix: np.ndarray,
    case_label: str,
) -> Any:
    """Create a structural matrix comparison when state spaces differ.

    :param andes_matrix: ANDES state matrix.
    :param veragrid_matrix: VeraGrid state matrix.
    :param case_label: Network label for the title.
    :return: Matplotlib figure.
    """
    andes_log_magnitude: np.ndarray = np.log10(np.maximum(np.abs(andes_matrix), 1.0e-16))
    veragrid_log_magnitude: np.ndarray = np.log10(np.maximum(np.abs(veragrid_matrix), 1.0e-16))
    common_minimum: float = float(min(np.min(andes_log_magnitude), np.min(veragrid_log_magnitude)))
    common_maximum: float = float(max(np.max(andes_log_magnitude), np.max(veragrid_log_magnitude)))
    andes_row_norms: np.ndarray = np.sort(np.linalg.norm(andes_matrix, axis=1))[::-1]
    veragrid_row_norms: np.ndarray = np.sort(np.linalg.norm(veragrid_matrix, axis=1))[::-1]
    andes_rank: np.ndarray = np.linspace(0.0, 1.0, andes_row_norms.size)
    veragrid_rank: np.ndarray = np.linspace(0.0, 1.0, veragrid_row_norms.size)
    state_counts: np.ndarray = np.asarray(
        list((andes_matrix.shape[0], veragrid_matrix.shape[0])),
        dtype=int,
    )
    andes_density: float = float(np.count_nonzero(np.abs(andes_matrix) > 1.0e-12) / andes_matrix.size)
    veragrid_density: float = float(np.count_nonzero(np.abs(veragrid_matrix) > 1.0e-12) / veragrid_matrix.size)

    figure: Any
    axes: np.ndarray
    figure, axes = plt.subplots(2, 2, figsize=(17, 12))
    andes_image: Any = axes[0, 0].imshow(
        andes_log_magnitude,
        aspect="auto",
        cmap="magma",
        vmin=common_minimum,
        vmax=common_maximum,
    )
    axes[0, 0].set_title(f"ANDES log10 |A| ({andes_matrix.shape[0]} states)")
    axes[0, 0].set_xlabel("State column")
    axes[0, 0].set_ylabel("State equation")
    figure.colorbar(andes_image, ax=axes[0, 0], fraction=0.046, pad=0.04)

    veragrid_image: Any = axes[0, 1].imshow(
        veragrid_log_magnitude,
        aspect="auto",
        cmap="magma",
        vmin=common_minimum,
        vmax=common_maximum,
    )
    axes[0, 1].set_title(f"VeraGrid log10 |A| ({veragrid_matrix.shape[0]} states)")
    axes[0, 1].set_xlabel("State column")
    axes[0, 1].set_ylabel("State equation")
    figure.colorbar(veragrid_image, ax=axes[0, 1], fraction=0.046, pad=0.04)

    axes[1, 0].semilogy(andes_rank, np.maximum(andes_row_norms, 1.0e-16), label="ANDES")
    axes[1, 0].semilogy(veragrid_rank, np.maximum(veragrid_row_norms, 1.0e-16), label="VeraGrid")
    axes[1, 0].set_title("Ranked state-equation row norms")
    axes[1, 0].set_xlabel("Normalized rank")
    axes[1, 0].set_ylabel("Row 2-norm")
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend()

    axes[1, 1].bar(
        list(("ANDES", "VeraGrid")),
        state_counts,
        color=list(("tab:blue", "tab:orange")),
    )
    axes[1, 1].set_title("State-space size and matrix density")
    axes[1, 1].set_ylabel("Differential states")
    axes[1, 1].text(0, state_counts[0] * 0.5, f"density={andes_density:.1%}", ha="center")
    axes[1, 1].text(1, state_counts[1] * 0.5, f"density={veragrid_density:.1%}", ha="center")
    axes[1, 1].grid(True, axis="y", alpha=0.3)
    figure.suptitle(
        f"{case_label}: structural state-matrix comparison\n"
        "Different state spaces: an entry-wise subtraction would not be physically meaningful."
    )
    figure.tight_layout()
    return figure


def _match_modal_indexes(
    andes_eigenvalues: np.ndarray,
    veragrid_eigenvalues: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return Hungarian modal indexes ordered by the ANDES index.

    :param andes_eigenvalues: ANDES eigenvalues.
    :param veragrid_eigenvalues: VeraGrid eigenvalues.
    :return: ANDES and VeraGrid index vectors for matched modes.
    """
    distance_matrix: np.ndarray = np.abs(
        andes_eigenvalues[:, np.newaxis] - veragrid_eigenvalues[np.newaxis, :]
    )
    andes_indexes: np.ndarray
    veragrid_indexes: np.ndarray
    andes_indexes, veragrid_indexes = linear_sum_assignment(distance_matrix)
    ordering: np.ndarray = np.argsort(andes_indexes)
    return andes_indexes[ordering], veragrid_indexes[ordering]


def _create_unaligned_participation_figure(
    andes_participation: np.ndarray,
    veragrid_participation: np.ndarray,
    case_label: str,
) -> Any:
    """Create a modal participation comparison for unequal state spaces.

    :param andes_participation: ANDES factors with matched modal columns.
    :param veragrid_participation: VeraGrid factors with matched modal columns.
    :param case_label: Network label for the title.
    :return: Matplotlib figure.
    """
    common_limit: float = float(
        max(np.max(andes_participation), np.max(veragrid_participation), 1.0e-15)
    )
    andes_maximum: np.ndarray = np.max(andes_participation, axis=0)
    veragrid_maximum: np.ndarray = np.max(veragrid_participation, axis=0)
    maximum_difference: np.ndarray = veragrid_maximum - andes_maximum
    mode_indexes: np.ndarray = np.arange(maximum_difference.size)
    top_count: int = min(15, maximum_difference.size)
    top_indexes: np.ndarray = np.argsort(np.abs(maximum_difference))[-top_count:][::-1]
    top_labels: list[str] = [f"matched mode {int(index) + 1}" for index in top_indexes]

    figure: Any
    axes: np.ndarray
    figure, axes = plt.subplots(2, 2, figsize=(17, 12))
    andes_image: Any = axes[0, 0].imshow(
        andes_participation,
        aspect="auto",
        cmap="viridis",
        vmin=0.0,
        vmax=common_limit,
    )
    axes[0, 0].set_title(f"ANDES PF ({andes_participation.shape[0]} states)")
    axes[0, 0].set_xlabel("Matched mode")
    axes[0, 0].set_ylabel("State")
    figure.colorbar(andes_image, ax=axes[0, 0], fraction=0.046, pad=0.04)

    veragrid_image: Any = axes[0, 1].imshow(
        veragrid_participation,
        aspect="auto",
        cmap="viridis",
        vmin=0.0,
        vmax=common_limit,
    )
    axes[0, 1].set_title(f"VeraGrid PF ({veragrid_participation.shape[0]} states)")
    axes[0, 1].set_xlabel("Matched mode")
    axes[0, 1].set_ylabel("State")
    figure.colorbar(veragrid_image, ax=axes[0, 1], fraction=0.046, pad=0.04)

    axes[1, 0].plot(mode_indexes + 1, andes_maximum, label="ANDES")
    axes[1, 0].plot(mode_indexes + 1, veragrid_maximum, label="VeraGrid")
    axes[1, 0].set_title("Largest state participation in each matched mode")
    axes[1, 0].set_xlabel("Matched mode")
    axes[1, 0].set_ylabel("Maximum participation factor")
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend()

    positions: np.ndarray = np.arange(top_count)
    axes[1, 1].barh(positions, maximum_difference[top_indexes][::-1])
    axes[1, 1].set_yticks(positions)
    axes[1, 1].set_yticklabels(top_labels[::-1], fontsize=8)
    axes[1, 1].set_title("Largest differences in peak modal participation")
    axes[1, 1].set_xlabel("VeraGrid - ANDES")
    axes[1, 1].grid(True, axis="x", alpha=0.3)
    figure.suptitle(
        f"{case_label}: participation-factor comparison\n"
        "Modes are eigenvalue-matched; state rows remain model-specific."
    )
    figure.tight_layout()
    return figure


def load_veragrid_eigenvalues(csv_path: Path) -> np.ndarray:
    """
    Load VeraGrid eigenvalues from the current ``modes.csv`` format.

    Expected columns:
        mode,
        real_rad_per_s,
        imag_rad_per_s,
        damping_ratio,
        oscillation_frequency_hz

    :param csv_path: VeraGrid modes.csv path.
    :return: Complex eigenvalue vector.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"VeraGrid eigenvalue file was not found:\n{csv_path}"
        )
    else:
        pass

    data = np.genfromtxt(
        csv_path,
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )

    if data.size == 0:
        raise ValueError(f"VeraGrid modes file is empty: {csv_path}")
    else:
        pass

    real_part = np.atleast_1d(data["real_rad_per_s"]).astype(float)
    imag_part = np.atleast_1d(data["imag_rad_per_s"]).astype(float)

    return real_part + 1j * imag_part


def load_andes_eigenvalues(csv_path: Path) -> np.ndarray:
    """
    Load ANDES eigenvalues from stability_andes.py output.

    The ANDES file contains one complex eigenvalue per row and has no header.

    :param csv_path: ANDES eigenvalue CSV path.
    :return: Complex eigenvalue vector.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"ANDES eigenvalue file was not found:\n{csv_path}"
        )
    else:
        pass

    values = np.genfromtxt(
        csv_path,
        delimiter=",",
        dtype=complex,
    )

    values = np.asarray(values, dtype=complex).reshape(-1)

    if values.size == 0:
        raise ValueError(f"ANDES eigenvalue file is empty: {csv_path}")
    else:
        pass

    return values


def compare_power_flow_buses(veragrid_csv: Path, andes_csv: Path) -> tuple[float, float]:
    """Compare solved bus magnitudes and angles.

    VeraGrid exports angles in degrees while ANDES stores radians.  Rows are
    matched by normalized bus name when names are unique. Large reference cases
    contain repeated display names, for which the common source-row order is the
    only unambiguous alignment.

    :param veragrid_csv: VeraGrid solved bus table.
    :param andes_csv: ANDES solved bus table.
    :return: Maximum magnitude and angle errors in pu and radians.
    """
    andes_values: dict[str, tuple[float, float]] = dict()
    andes_ordered_values: list[tuple[float, float]] = list()
    with andes_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader: Any = csv.DictReader(csv_file)
        row: dict[str, str]
        for row in reader:
            bus_name: str = str(row["name"]).strip().upper()
            bus_voltage: tuple[float, float] = (float(row["Vm"]), float(row["Va_rad"]))
            andes_values[bus_name] = bus_voltage
            andes_ordered_values.append(bus_voltage)
    use_ordered_alignment: bool = len(andes_values) != len(andes_ordered_values)

    magnitude_errors: list[float] = list()
    veragrid_angles: list[float] = list()
    andes_angles: list[float] = list()
    with veragrid_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        row_index: int = 0
        for row in reader:
            veragrid_name: str = str(row[""]).strip().upper()
            named_voltage: tuple[float, float] | None = andes_values.get(
                veragrid_name,
                None,
            )
            if use_ordered_alignment or named_voltage is None:
                andes_voltage: tuple[float, float] = andes_ordered_values[row_index]
            else:
                andes_voltage = named_voltage
            magnitude_errors.append(abs(float(row["Vm"]) - andes_voltage[0]))
            veragrid_angles.append(float(np.deg2rad(float(row["Va"]))))
            andes_angles.append(andes_voltage[1])
            row_index += 1

    # Voltage angles have an arbitrary additive reference. Align the first
    # matched bus before reporting physical angle differences.
    veragrid_angle_array: np.ndarray = np.asarray(veragrid_angles, dtype=float)
    andes_angle_array: np.ndarray = np.asarray(andes_angles, dtype=float)
    if veragrid_angle_array.size > 0:
        angle_reference_offset: float = float(
            veragrid_angle_array[0] - andes_angle_array[0]
        )
        angle_error_array: np.ndarray = np.abs(
            veragrid_angle_array - angle_reference_offset - andes_angle_array
        )
    else:
        angle_error_array = np.zeros(1, dtype=float)

    max_magnitude_error: float = float(np.max(np.asarray(magnitude_errors, dtype=float)))
    max_angle_error: float = float(np.max(angle_error_array))
    return max_magnitude_error, max_angle_error


def load_veragrid_state_matrix(csv_path: Path) -> np.ndarray:
    """
    Load the VeraGrid state matrix from ``state_matrix.csv``.

    :param csv_path: VeraGrid state-matrix CSV path.
    :return: Complex state matrix.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"VeraGrid state-matrix file was not found:\n{csv_path}"
        )
    else:
        pass

    rows = list()
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            rows.append(row)

    if len(rows) <= 1:
        raise ValueError(f"VeraGrid state-matrix file is empty: {csv_path}")
    else:
        pass

    data_rows = rows[1:]
    matrix_rows = list()
    row_count = len(data_rows)
    row_index = 0
    while row_index < row_count:
        matrix_rows.append(data_rows[row_index][1:])
        row_index += 1

    matrix = np.asarray(matrix_rows, dtype=complex)
    return matrix


def load_veragrid_state_matrix_labels(csv_path: Path) -> tuple[list[str], list[str]]:
    """
    Load the VeraGrid state-matrix row and column labels.

    :param csv_path: VeraGrid state-matrix CSV path.
    :return: Row labels and column labels.
    """
    rows = list()
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            rows.append(row)

    header = list(rows[0][1:])
    row_labels = list()
    row_count = len(rows) - 1
    row_index = 0
    while row_index < row_count:
        row_labels.append(rows[row_index + 1][0])
        row_index += 1
    return row_labels, header


def load_andes_state_matrix(csv_path: Path) -> np.ndarray:
    """
    Load the ANDES state matrix from CSV.

    :param csv_path: ANDES state-matrix CSV path.
    :return: Real state matrix.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"ANDES state-matrix file was not found:\n{csv_path}"
        )
    else:
        pass

    rows = list()
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            rows.append(row)

    if len(rows) <= 1:
        raise ValueError(f"ANDES state-matrix file is empty: {csv_path}")
    else:
        pass

    data_rows = rows[1:]
    matrix_rows = list()
    row_count = len(data_rows)
    row_index = 0
    while row_index < row_count:
        matrix_rows.append(data_rows[row_index][1:])
        row_index += 1

    matrix = np.asarray(matrix_rows, dtype=complex)

    return matrix


def load_andes_state_matrix_labels(csv_path: Path) -> tuple[list[str], list[str]]:
    """
    Load the ANDES state-matrix row and column labels.

    :param csv_path: ANDES state-matrix CSV path.
    :return: Row labels and column labels.
    """
    rows = list()
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            rows.append(row)

    if len(rows) <= 1:
        raise ValueError(f"ANDES state-matrix file is empty: {csv_path}")
    else:
        pass

    header = list(rows[0][1:])
    row_labels = list()
    row_count = len(rows) - 1
    row_index = 0
    while row_index < row_count:
        row_labels.append(rows[row_index + 1][0])
        row_index += 1
    return row_labels, header


def normalize_state_label(label: str) -> str:
    """
    Normalize one state label for cross-tool comparison.

    :param label: Original label.
    :return: Normalized label.
    """
    text = str(label).strip()
    compact = re.sub(r"\s+", " ", text)
    return compact


def normalize_state_labels(labels: list[str]) -> list[str]:
    """
    Normalize a list of state labels.

    :param labels: Original labels.
    :return: Normalized labels.
    """
    normalized = list()
    label_count = len(labels)
    label_index = 0
    while label_index < label_count:
        normalized.append(normalize_state_label(labels[label_index]))
        label_index += 1
    return normalized


def _andes_auxiliary_state_reason(
    andes_label: str,
    veragrid_labels: list[str],
) -> str | None:
    """Explain why an ANDES-only implementation state is not comparable.

    :param andes_label: Candidate ANDES state label.
    :param veragrid_labels: State labels retained by VeraGrid.
    :return: Exclusion reason or ``None`` when the state must be retained.
    """
    normalized_label: str = normalize_state_label(andes_label)
    has_veragrid_bus_frequency: bool = any(
        "BusFreq" in normalize_state_label(label)
        or "BusFrequency" in normalize_state_label(label)
        or re.match(r"^L_y\s*\d+$", normalize_state_label(label)) is not None
        or ":L_y:" in normalize_state_label(label)
        for label in veragrid_labels
    )
    has_veragrid_ieeest: bool = any(
        "LL2_x" in normalize_state_label(label)
        for label in veragrid_labels
    )

    if "BusFreq" in normalized_label and not has_veragrid_bus_frequency:
        reason: str | None = (
            "unused ANDES BusFreq measurement; no dynamic model consumes it"
        )
    elif (
        has_veragrid_ieeest
        and (
            normalized_label.startswith("F1_y IEEEST")
            or normalized_label.startswith("F2_x2 IEEEST")
        )
    ):
        reason = (
            "zero-parameter IEEEST input-filter realization state; VeraGrid "
            "uses the exact algebraic pass-through"
        )
    else:
        reason = None
    return reason


def reduce_andes_to_common_physical_states(
    matrix: np.ndarray,
    row_labels: list[str],
    column_labels: list[str],
    veragrid_labels: list[str],
) -> tuple[np.ndarray, list[str], list[str], list[str]]:
    """Remove ANDES-only measurement and zero-parameter realization states.

    The operation creates the common physical-coordinate view used for direct
    state-matrix, modal and participation-factor comparisons. Every removed
    state and its reason is returned for the persistent human audit report.

    :param matrix: Full ANDES reduced state matrix.
    :param row_labels: Full ANDES row labels.
    :param column_labels: Full ANDES column labels.
    :param veragrid_labels: VeraGrid state labels defining the common model.
    :return: Reduced matrix, row labels, column labels and exclusion messages.
    """
    retained_row_indexes: list[int] = list()
    retained_column_indexes: list[int] = list()
    reduced_row_labels: list[str] = list()
    reduced_column_labels: list[str] = list()
    exclusion_messages: list[str] = list()

    row_index: int
    for row_index in range(len(row_labels)):
        row_reason: str | None = _andes_auxiliary_state_reason(
            andes_label=row_labels[row_index],
            veragrid_labels=veragrid_labels,
        )
        if row_reason is None:
            retained_row_indexes.append(row_index)
            reduced_row_labels.append(row_labels[row_index])
        else:
            exclusion_messages.append(f"{row_labels[row_index]}: {row_reason}")

    column_index: int
    for column_index in range(len(column_labels)):
        column_reason: str | None = _andes_auxiliary_state_reason(
            andes_label=column_labels[column_index],
            veragrid_labels=veragrid_labels,
        )
        if column_reason is None:
            retained_column_indexes.append(column_index)
            reduced_column_labels.append(column_labels[column_index])
        else:
            pass

    reduced_matrix: np.ndarray = matrix[np.ix_(
        np.asarray(retained_row_indexes, dtype=int),
        np.asarray(retained_column_indexes, dtype=int),
    )]
    return (
        reduced_matrix,
        reduced_row_labels,
        reduced_column_labels,
        exclusion_messages,
    )


def convert_veragrid_reduced_label_to_andes(label: str, occurrence_index: int | None = None) -> str:
    """Map one compiled VeraGrid reduced label to the ANDES reduced-state label."""
    text = str(label).strip()
    match = re.match(r"x:Generator\[(\d+(?:\.0)?)\]:(.+):uid=\d+$", text)
    if match is None:
        return text
    else:
        generator_index: int = int(float(match.group(1)))
        state_name: str = match.group(2)
        esst3a_id_by_generator: dict[int, int] = dict(((1, 2), (3, 3), (4, 4), (5, 5)))
        busfreq_id_by_generator: dict[int, int] = dict(((1, 1), (2, 2), (3, 3)))

        if state_name in ("delta", "omega", "e1q", "e1d", "e2d", "e2q"):
            converted_label: str = f"{state_name} GENROU {generator_index}"
        elif state_name == "LAG_y":
            converted_label = f"{state_name} TGOV1 {generator_index}"
        elif state_name == "LL_x":
            if occurrence_index == 0:
                converted_label = f"LL_x TGOV1 {generator_index}"
            elif generator_index == 2 and occurrence_index == 1:
                converted_label = "LL_x EXST1 1"
            elif generator_index in esst3a_id_by_generator and occurrence_index == 1:
                converted_label = f"LL_x ESST3A {esst3a_id_by_generator[generator_index]}"
            else:
                converted_label = text
        elif state_name in ("LR_y", "WF_x"):
            if generator_index == 2:
                converted_label = f"{state_name} EXST1 1"
            else:
                converted_label = text
        elif state_name in ("LG_y", "LAW2_y"):
            if generator_index == 2 and state_name == "LG_y":
                converted_label = "LG_y EXST1 1"
            elif generator_index in esst3a_id_by_generator:
                converted_label = f"{state_name} ESST3A {esst3a_id_by_generator[generator_index]}"
            else:
                converted_label = text
        elif state_name == "L_y" or state_name == "WO_x":
            if generator_index in busfreq_id_by_generator:
                converted_label = f"{state_name} BusFreq {busfreq_id_by_generator[generator_index]}"
            else:
                converted_label = text
        else:
            converted_label = text
        return converted_label


def map_veragrid_labels_to_andes_style(labels: list[str]) -> list[str]:
    """Convert VeraGrid compiled reduced labels into ANDES-style reduced labels."""
    llx_occurrence_by_generator: dict[int, int] = dict()
    converted: list[str] = list()

    for label in labels:
        occurrence_index: int | None = None
        match = re.match(r"x:Generator\[(\d+(?:\.0)?)\]:(.+):uid=\d+$", str(label).strip())
        if match is not None and match.group(2) == "LL_x":
            generator_index = int(float(match.group(1)))
            occurrence_index = llx_occurrence_by_generator.get(generator_index, 0)
            llx_occurrence_by_generator[generator_index] = occurrence_index + 1
        else:
            pass

        converted.append(convert_veragrid_reduced_label_to_andes(label, occurrence_index=occurrence_index))

    if len(set(converted)) != len(converted):
        duplicates = sorted({label for label in converted if converted.count(label) > 1})
        raise ValueError(f"Duplicate mapped VeraGrid labels found: {duplicates}")
    else:
        pass
    return converted


def map_simple_veragrid_labels(
    veragrid_labels: list[str],
    andes_labels: list[str],
) -> list[str]:
    """Map compact labels such as ``delta1`` to an ANDES state label.

    This convention is used by the generic VeraGrid CSV exporter in Kundur and
    IEEE39.  The ANDES model name is selected only when state name and device
    ordinal identify exactly one candidate.

    :param veragrid_labels: VeraGrid labels after compiled-label conversion.
    :param andes_labels: Labels read from the ANDES state matrix.
    :return: Labels mapped where an unambiguous candidate exists.
    """
    mapped_labels: list[str] = list()
    occurrence_by_state: dict[str, int] = dict()
    veragrid_label: str
    for veragrid_label in veragrid_labels:
        compact_match: re.Match[str] | None = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*?)(\d+)$",
            str(veragrid_label).strip(),
        )
        if compact_match is None:
            mapped_labels.append(veragrid_label)
        else:
            state_name: str = compact_match.group(1)
            # The numeric suffix exported by VeraGrid is a symbolic-variable
            # UID, not a device number. Device order is therefore recovered
            # from each state's occurrence order in the matrix.
            state_occurrence: int = occurrence_by_state.get(state_name, 0) + 1
            occurrence_by_state[state_name] = state_occurrence
            device_ordinal: str = str(state_occurrence)
            candidates: list[str] = list()
            andes_label: str
            for andes_label in andes_labels:
                label_parts: list[str] = str(andes_label).strip().split()
                if (
                    len(label_parts) >= 3
                    and label_parts[0] == state_name
                    and label_parts[-1] == device_ordinal
                ):
                    candidates.append(andes_label)
                else:
                    pass
            if len(candidates) == 1:
                mapped_labels.append(candidates[0])
            else:
                mapped_labels.append(veragrid_label)
    return mapped_labels


def reorder_andes_state_matrix_to_veragrid(
    andes_state_matrix: np.ndarray,
    andes_row_labels: list[str],
    andes_column_labels: list[str],
    veragrid_row_labels: list[str],
    veragrid_column_labels: list[str],
) -> tuple[np.ndarray | None, list[str]]:
    """
    Reorder the ANDES state matrix to the VeraGrid label order.

    :param andes_state_matrix: ANDES state matrix.
    :param andes_row_labels: ANDES row labels.
    :param andes_column_labels: ANDES column labels.
    :param veragrid_row_labels: VeraGrid row labels.
    :param veragrid_column_labels: VeraGrid column labels.
    :return: Reordered matrix and missing-label list.
    """
    missing_labels = list()
    andes_row_index_map = dict()
    andes_column_index_map = dict()

    row_count = len(andes_row_labels)
    row_index = 0
    while row_index < row_count:
        andes_row_index_map[andes_row_labels[row_index]] = row_index
        row_index += 1

    column_count = len(andes_column_labels)
    column_index = 0
    while column_index < column_count:
        andes_column_index_map[andes_column_labels[column_index]] = column_index
        column_index += 1

    reordered = np.zeros(
        (len(veragrid_row_labels), len(veragrid_column_labels)),
        dtype=complex,
    )

    target_row_count = len(veragrid_row_labels)
    target_row_index = 0
    while target_row_index < target_row_count:
        target_row_label = veragrid_row_labels[target_row_index]
        source_row_index = andes_row_index_map.get(target_row_label, None)

        if source_row_index is None:
            missing_labels.append(target_row_label)
        else:
            target_column_count = len(veragrid_column_labels)
            target_column_index = 0
            while target_column_index < target_column_count:
                target_column_label = veragrid_column_labels[target_column_index]
                source_column_index = andes_column_index_map.get(target_column_label, None)

                if source_column_index is None:
                    if target_column_label not in missing_labels:
                        missing_labels.append(target_column_label)
                    else:
                        pass
                else:
                    reordered[target_row_index, target_column_index] = andes_state_matrix[source_row_index, source_column_index]

                target_column_index += 1

        target_row_index += 1

    if len(missing_labels) > 0:
        return None, missing_labels
    else:
        return reordered, missing_labels


def report_top_matrix_mismatches(
    andes_matrix: np.ndarray,
    veragrid_matrix: np.ndarray,
    row_labels: list[str],
    column_labels: list[str],
    top_n: int = 30,
) -> None:
    """Print the largest absolute matrix-entry mismatches with aligned labels."""
    difference = veragrid_matrix - andes_matrix
    flat_abs = np.abs(difference).ravel()
    if flat_abs.size == 0:
        return
    else:
        pass

    top_indexes = np.argsort(flat_abs)[::-1][:top_n]
    n_cols = difference.shape[1]

    print("\nLargest state-matrix entry mismatches:")
    print(
        f"{'Rank':>4}  {'Row label':<24}  {'Column label':<24}  "
        f"{'ANDES':>18}  {'VeraGrid':>18}  {'Difference':>18}"
    )
    print("-" * 120)

    for rank, flat_index in enumerate(top_indexes, start=1):
        row_index = int(flat_index // n_cols)
        column_index = int(flat_index % n_cols)
        print(
            f"{rank:4d}  "
            f"{row_labels[row_index]:<24.24}  "
            f"{column_labels[column_index]:<24.24}  "
            f"{andes_matrix[row_index, column_index].real:+18.10e}  "
            f"{veragrid_matrix[row_index, column_index].real:+18.10e}  "
            f"{difference[row_index, column_index].real:+18.10e}"
        )


def match_eigenvalues(
    reference: np.ndarray,
    candidate: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Match ANDES and VeraGrid eigenvalues by globally minimum total distance.

    Matching by nearest point in the complex s-plane is more robust than sorting
    only by eigenvalue magnitude, particularly for conjugate modes and modes with
    similar absolute value.

    ANDES is treated as the reference set.

    :param reference: ANDES eigenvalues.
    :param candidate: VeraGrid eigenvalues.
    :return: Tuple with matched ANDES values, matched VeraGrid values and errors.
    """
    reference = np.asarray(reference, dtype=complex).reshape(-1)
    candidate = np.asarray(candidate, dtype=complex).reshape(-1)

    if candidate.size < reference.size:
        print(
            "Warning: VeraGrid has fewer eigenvalues than ANDES. "
            f"VeraGrid={candidate.size}, ANDES={reference.size}. "
            "Only the available VeraGrid modes will be matched."
        )
    else:
        pass

    distance_matrix: np.ndarray = np.abs(reference[:, np.newaxis] - candidate[np.newaxis, :])
    reference_indexes: np.ndarray
    candidate_indexes: np.ndarray
    reference_indexes, candidate_indexes = linear_sum_assignment(distance_matrix)
    ordering: np.ndarray = np.argsort(reference_indexes)
    reference_indexes = reference_indexes[ordering]
    candidate_indexes = candidate_indexes[ordering]
    matched_reference: np.ndarray = reference[reference_indexes]
    matched_candidate: np.ndarray = candidate[candidate_indexes]
    absolute_errors: np.ndarray = distance_matrix[reference_indexes, candidate_indexes]

    return (
        np.asarray(matched_reference, dtype=complex),
        np.asarray(matched_candidate, dtype=complex),
        np.asarray(absolute_errors, dtype=float),
    )


def compute_andes_participation_factors(
    state_matrix: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute biorthogonal state participation normalized per mode.

    Both matrices are evaluated with the same state-by-mode definition.  Each
    modal column sums to one before five-decimal rounding.  This avoids the
    index-coupled transpose normalization in ANDES 2.0.0, which can associate a
    state column with an unrelated modal normalization factor.

    :param state_matrix: Reduced state matrix in a common state order.
    :return: Eigenvalues and the state-by-mode participation-factor matrix.
    """
    matrix: np.ndarray = np.asarray(state_matrix, dtype=float)
    eigenvalues: np.ndarray
    right_eigenvectors: np.ndarray
    eigenvalues, right_eigenvectors = np.linalg.eig(matrix)
    identity: np.ndarray = np.eye(eigenvalues.size, dtype=float)

    # The six repeated -50 modes make the eigenvector basis ill-conditioned.
    # This is expected for this benchmark and ANDES uses the same direct solve.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", LinAlgWarning)
        inverse_transpose: np.ndarray = solve(
            right_eigenvectors,
            identity,
            overwrite_b=False,
        ).T

    raw_participation: np.ndarray = (
        np.abs(inverse_transpose) * np.abs(right_eigenvectors)
    )
    normalization: np.ndarray = np.sum(
        raw_participation,
        axis=0,
        keepdims=True,
    )
    normalized_participation: np.ndarray = raw_participation / normalization

    return eigenvalues, np.round(normalized_participation, decimals=5)


def identify_basis_degenerate_modes(eigenvalues: np.ndarray) -> np.ndarray:
    """Identify modes whose individual eigenvector basis is not unique.

    :param eigenvalues: Eigenvalues in the current modal order.
    :return: Boolean mask for repeated or numerically indistinguishable modes.
    """
    values: np.ndarray = np.asarray(eigenvalues, dtype=complex)
    degenerate_mask: np.ndarray = np.zeros(values.size, dtype=bool)
    first_index: int
    second_index: int
    for first_index in range(values.size):
        for second_index in range(first_index + 1, values.size):
            tolerance: float = max(
                1.0e-6,
                1.0e-8 * max(abs(values[first_index]), abs(values[second_index])),
            )
            if abs(values[first_index] - values[second_index]) <= tolerance:
                degenerate_mask[first_index] = True
                degenerate_mask[second_index] = True
            else:
                pass
    return degenerate_mask


def save_participation_difference(
    output_path: Path,
    state_labels: list[str],
    difference: np.ndarray,
) -> None:
    """Save the aligned participation-factor difference matrix.

    :param output_path: Destination CSV path.
    :param state_labels: State labels in the common matrix order.
    :param difference: VeraGrid-minus-ANDES state-by-mode matrix.
    :return: None.
    """
    mode_labels: list[str] = list()
    mode_index: int
    for mode_index in range(difference.shape[1]):
        mode_labels.append(f"matched_mode_{mode_index + 1}")

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer: csv.writer = csv.writer(csv_file)
        writer.writerow(list(("state", *mode_labels)))
        row_index: int
        for row_index in range(difference.shape[0]):
            row: list[object] = list((state_labels[row_index],))
            row.extend(difference[row_index, :].tolist())
            writer.writerow(row)


def _load_timing_samples(timing_csv: Path) -> dict[str, float]:
    """Load one engine timing CSV keyed by benchmark phase.

    :param timing_csv: Timing artifact produced beside numerical results.
    :return: Phase-to-seconds mapping.
    """
    samples: dict[str, float] = dict()
    with timing_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader: csv.DictReader = csv.DictReader(csv_file)
        row: dict[str, str]
        for row in reader:
            samples[str(row["phase"])] = float(row["seconds"])
    return samples


def _load_timing_standard_deviations(timing_csv: Path) -> dict[str, float]:
    """Load one engine's per-phase sample standard deviations.

    :param timing_csv: Mean timing artifact containing deviation columns.
    :return: Phase-to-standard-deviation mapping.
    """
    standard_deviations: dict[str, float] = dict()
    with timing_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader: csv.DictReader = csv.DictReader(csv_file)
        row: dict[str, str]
        for row in reader:
            standard_deviations[str(row["phase"])] = float(
                row["standard_deviation_seconds"]
            )
    return standard_deviations


def _timing_factor_summary(
    andes_seconds: float,
    veragrid_seconds: float,
) -> tuple[float, str, float]:
    """Calculate an explicit timing ratio and winning-engine description.

    :param andes_seconds: Measured ANDES phase duration.
    :param veragrid_seconds: Measured VeraGrid phase duration.
    :return: ANDES/VeraGrid ratio, faster-engine label, and speedup factor.
    """
    valid_samples: bool = bool(
        np.isfinite(andes_seconds)
        and np.isfinite(veragrid_seconds)
        and andes_seconds > 0.0
        and veragrid_seconds > 0.0
    )
    if valid_samples:
        andes_over_veragrid: float = andes_seconds / veragrid_seconds
        if abs(andes_over_veragrid - 1.0) <= 5.0e-4:
            faster_engine: str = "Tie"
            speedup_factor: float = 1.0
        elif andes_over_veragrid > 1.0:
            faster_engine = "VeraGrid"
            speedup_factor = andes_over_veragrid
        else:
            faster_engine = "ANDES"
            speedup_factor = 1.0 / andes_over_veragrid
    else:
        andes_over_veragrid = float("nan")
        faster_engine = "--"
        speedup_factor = float("nan")
    return andes_over_veragrid, faster_engine, speedup_factor


def _create_timing_comparison(
    veragrid_results_directory: Path,
    andes_results_directory: Path,
    comparison_directory: Path,
    case_label: str,
) -> Figure | None:
    """Create CSV and visual tables for comparable small-signal timings.

    :param veragrid_results_directory: VeraGrid result directory.
    :param andes_results_directory: ANDES result directory.
    :param comparison_directory: Destination for comparison artifacts.
    :param case_label: Benchmark case label.
    :return: Generated Matplotlib figure, or ``None`` when timing data is absent.
    """
    veragrid_candidates: list[Path] = sorted(
        veragrid_results_directory.glob("timings_results_VeraGrid_*.csv")
    )
    andes_candidates: list[Path] = sorted(
        andes_results_directory.glob("timings_results_Andes_*.csv")
    )
    if len(veragrid_candidates) == 1 and len(andes_candidates) == 1:
        pass
    else:
        print(
            "\nTiming comparison unavailable: expected exactly one timing CSV "
            f"per engine, found VeraGrid={len(veragrid_candidates)} and "
            f"ANDES={len(andes_candidates)}."
        )
        return None

    veragrid_samples: dict[str, float] = _load_timing_samples(veragrid_candidates[0])
    andes_samples: dict[str, float] = _load_timing_samples(andes_candidates[0])
    veragrid_standard_deviations: dict[str, float] = (
        _load_timing_standard_deviations(veragrid_candidates[0])
    )
    andes_standard_deviations: dict[str, float] = (
        _load_timing_standard_deviations(andes_candidates[0])
    )

    # Group the engine-specific preparation timers so that the normal elapsed
    # post-power-flow workflow can be reported. The internal work differs by
    # architecture, so this grouped phase is not a like-for-like benchmark.
    grouped_andes_samples: dict[str, float] = dict(andes_samples)
    grouped_veragrid_samples: dict[str, float] = dict(veragrid_samples)
    grouped_andes_samples["dynamic_problem_preparation"] = float(sum((
        andes_samples.get("andes_system_setup", float("nan")),
        andes_samples.get("dynamic_initialization", float("nan")),
        andes_samples.get("benchmark_preprocessing", float("nan")),
    )))
    grouped_veragrid_samples["dynamic_problem_preparation"] = veragrid_samples.get(
        "rms_problem_build_initialization_symbolic_to_numeric",
        float("nan"),
    )
    grouped_andes_samples["dynamic_simulation_total"] = float(sum((
        grouped_andes_samples["dynamic_problem_preparation"],
        andes_samples.get("small_signal_total", float("nan")),
    )))
    grouped_veragrid_samples["dynamic_simulation_total"] = float(sum((
        grouped_veragrid_samples["dynamic_problem_preparation"],
        veragrid_samples.get("small_signal_total", float("nan")),
    )))
    andes_export: float = andes_samples.get("result_export", float("nan"))
    veragrid_export: float = veragrid_samples.get("result_export", float("nan"))
    grouped_andes_samples["dynamic_results_total"] = (
        grouped_andes_samples["dynamic_simulation_total"] + andes_export
    )
    grouped_veragrid_samples["dynamic_results_total"] = (
        grouped_veragrid_samples["dynamic_simulation_total"] + veragrid_export
    )
    grouped_andes_samples["workflow_overhead"] = andes_samples.get(
        "normal_workflow_unattributed_overhead",
        float("nan"),
    )
    grouped_veragrid_samples["workflow_overhead"] = veragrid_samples.get(
        "normal_workflow_unattributed_overhead",
        float("nan"),
    )

    phase_specs: tuple[
        tuple[str, str, str, str], ...
    ] = (
        (
            "case_and_model_preparation",
            "Case/model preparation",
            "EXCLUDED PREREQUISITE",
            "Load or construct the network, devices and dynamic model instances before the dynamic benchmark boundary.",
        ),
        (
            "power_flow",
            "Warm power flow",
            "EXCLUDED PREREQUISITE",
            "Second steady-state solve after one excluded warm-up; it provides the operating point but is not part of the dynamic benchmark.",
        ),
        (
            "dynamic_problem_preparation",
            "Engine-specific post-power-flow preparation",
            "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)",
            "Architecture-dependent time from the solved power flow to a calculation-ready problem: ANDES reuses pregenerated numerical functions during system.setup, TDS.init and state folding, whereas VeraGrid constructs, initializes and compiles RmsProblemDae.",
        ),
        (
            "small_signal_calculation",
            "Small-signal calculation",
            "COMPARABLE CALCULATION",
            "Second complete EIG.run or SmallSignalStabilityRmsDriver.run call on the same initialized problem after one excluded warm-up call: state matrix, eigensolution, left/right eigenvectors, participation factors, modal post-processing and result assembly.",
        ),
        (
            "result_export",
            "Result export",
            "RESULT EXPORT",
            "Write the numerical result files consumed by the comparator.",
        ),
        (
            "workflow_overhead",
            "Workflow overhead",
            "EXCLUDED DIAGNOSTIC",
            "Measured script time between explicit phase timers; excluded because it is benchmark-harness work rather than simulator work.",
        ),
        (
            "dynamic_simulation_total",
            "Post-power-flow workflow total",
            "POST-POWER-FLOW WORKFLOW TOTAL",
            "Engine-specific post-power-flow preparation + warm small-signal calculation. This is a workflow elapsed time, not an internal phase-equivalence comparison.",
        ),
        (
            "andes_system_setup",
            "ANDES system setup",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
            "ANDES-only part of engine-specific post-power-flow preparation: arrays, DAE addresses, references, connectivity and sparse patterns.",
        ),
        (
            "dynamic_initialization",
            "ANDES TDS initialization",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
            "ANDES-only part of engine-specific post-power-flow preparation: TDS initialization and initial iterative step.",
        ),
        (
            "benchmark_preprocessing",
            "ANDES benchmark state folding",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
            "ANDES-only benchmark folding of zero-time-constant or unused auxiliary states.",
        ),
        (
            "rms_problem_build_initialization_symbolic_to_numeric",
            "VeraGrid RMS problem preparation",
            "DIAGNOSTIC SUBCOMPONENT (already included)",
            "VeraGrid-only part of engine-specific post-power-flow preparation: RmsProblemDae build, explicit initialization and numerical compilation.",
        ),
        (
            "diagnostic_power_flow_warmup",
            "Excluded first power flow (warm-up)",
            "EXCLUDED DIAGNOSTIC",
            "First power-flow solve used to warm runtime caches and provide the initial guess for the second solve.",
        ),
        (
            "diagnostic_small_signal_warmup",
            "Excluded first calculation (warm-up)",
            "EXCLUDED DIAGNOSTIC",
            "First complete EIG.run or SmallSignalStabilityRmsDriver.run call used to initialize runtime and numerical-library caches; the measured second call uses the same initialized problem and this first call is excluded from the workflow total.",
        ),
    )

    comparison_csv: Path = comparison_directory / "timing_comparison.csv"
    table_rows: list[
        tuple[str, str, float, float, float, float, float, str, float, str]
    ] = list()
    with comparison_csv.open("w", encoding="utf-8", newline="") as csv_file:
        writer: csv.writer = csv.writer(csv_file)
        writer.writerow(
            list((
                "timing_role",
                "phase",
                "phase_label",
                "andes_seconds",
                "andes_standard_deviation_seconds",
                "veragrid_seconds",
                "veragrid_standard_deviation_seconds",
                "andes_over_veragrid",
                "faster_engine",
                "speedup_factor",
                "scope",
            ))
        )
        phase_spec: tuple[str, str, str, str]
        for phase_spec in phase_specs:
            phase_name: str = phase_spec[0]
            phase_label: str = phase_spec[1]
            relation: str = phase_spec[2]
            scope: str = phase_spec[3]
            source_phase_name: str
            if phase_name == "case_and_model_preparation":
                source_phase_name = "case_and_model_build"
            elif phase_name == "small_signal_calculation":
                source_phase_name = "small_signal_total"
            elif phase_name == "workflow_overhead":
                source_phase_name = "normal_workflow_unattributed_overhead"
            else:
                source_phase_name = phase_name
            andes_seconds: float = grouped_andes_samples.get(source_phase_name, float("nan"))
            veragrid_seconds: float = grouped_veragrid_samples.get(source_phase_name, float("nan"))
            andes_standard_deviation: float = andes_standard_deviations.get(
                source_phase_name,
                float("nan"),
            )
            veragrid_standard_deviation: float = veragrid_standard_deviations.get(
                source_phase_name,
                float("nan"),
            )
            andes_over_veragrid: float
            faster_engine: str
            speedup_factor: float
            if relation == (
                "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)"
            ):
                # Show both workflow costs without implying that the engines
                # execute equivalent preparation operations.
                andes_over_veragrid = float("nan")
                faster_engine = "N/A: phases differ"
                speedup_factor = float("nan")
            else:
                andes_over_veragrid, faster_engine, speedup_factor = _timing_factor_summary(
                    andes_seconds=andes_seconds,
                    veragrid_seconds=veragrid_seconds,
                )
            writer.writerow(
                list((
                    relation,
                    phase_name,
                    phase_label,
                    andes_seconds,
                    andes_standard_deviation,
                    veragrid_seconds,
                    veragrid_standard_deviation,
                    andes_over_veragrid,
                    faster_engine,
                    speedup_factor,
                    scope,
                ))
            )
            table_rows.append(
                (
                    relation,
                    phase_label,
                    andes_seconds,
                    andes_standard_deviation,
                    veragrid_seconds,
                    veragrid_standard_deviation,
                    andes_over_veragrid,
                    faster_engine,
                    speedup_factor,
                    scope,
                )
            )

    print("\nSmall-signal timing comparison:")
    print(
        "  Relation      Phase                                                    "
        "ANDES mean±std [s]      VeraGrid mean±std [s]   ANDES/VG       Faster by"
    )
    print("  " + "-" * 174)
    table_relation: str
    table_phase_name: str
    table_andes_seconds: float
    table_andes_standard_deviation: float
    table_veragrid_seconds: float
    table_veragrid_standard_deviation: float
    table_andes_over_veragrid: float
    table_faster_engine: str
    table_speedup_factor: float
    table_scope: str
    for (
        table_relation,
        table_phase_name,
        table_andes_seconds,
        table_andes_standard_deviation,
        table_veragrid_seconds,
        table_veragrid_standard_deviation,
        table_andes_over_veragrid,
        table_faster_engine,
        table_speedup_factor,
        table_scope,
    ) in table_rows:
        if table_relation == "COMPARABLE CALCULATION":
            relation_text: str = "CALCULATION"
        elif table_relation == "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)":
            relation_text = "PREPARATION"
        elif table_relation == "RESULT EXPORT":
            relation_text = "EXPORT"
        elif table_relation == "POST-POWER-FLOW WORKFLOW TOTAL":
            relation_text = "WORKFLOW"
        elif table_relation == "DIAGNOSTIC SUBCOMPONENT (already included)":
            relation_text = "SUBCOMP"
        else:
            relation_text = "EXCLUDED"
        andes_text: str = (
            "--"
            if not np.isfinite(table_andes_seconds)
            else f"{table_andes_seconds:.6f}±{table_andes_standard_deviation:.6f}"
        )
        veragrid_text: str = (
            "--"
            if not np.isfinite(table_veragrid_seconds)
            else f"{table_veragrid_seconds:.6f}±{table_veragrid_standard_deviation:.6f}"
        )
        ratio_text: str = (
            "--"
            if not np.isfinite(table_andes_over_veragrid)
            else f"{table_andes_over_veragrid:.3f}x"
        )
        faster_text: str = (
            "--"
            if not np.isfinite(table_speedup_factor)
            else f"{table_faster_engine} {table_speedup_factor:.2f}x"
        )
        print(
            f"  {relation_text:12s} {table_phase_name:56s} "
            f"{andes_text:>23s} {veragrid_text:>26s} "
            f"{ratio_text:>11s} {faster_text:>16s}"
        )
    print("\n  CALCULATION is the directly comparable warm small-signal stage.")
    print("  PREPARATION is engine-specific and is not an internal phase-equivalence comparison.")
    print("  WORKFLOW = engine-specific preparation + comparable calculation.")
    print("  EXPORT is diagnostic and is outside the workflow total.")
    print("  SUBCOMP rows are already included and must not be added again.")
    print("  EXCLUDED rows are prerequisites or diagnostics outside the workflow total.")
    print("  ANDES/VG above 1 means VeraGrid is faster; below 1 means ANDES is faster.")
    print("\n  Timing phase scopes:")
    for (
        table_relation,
        table_phase_name,
        table_andes_seconds,
        table_andes_standard_deviation,
        table_veragrid_seconds,
        table_veragrid_standard_deviation,
        table_andes_over_veragrid,
        table_faster_engine,
        table_speedup_factor,
        table_scope,
    ) in table_rows:
        print(f"  - {table_phase_name}: {table_scope}")

    # Keep one compact, readable timing artifact at the system results root.
    timing_summary_lines: list[str] = list()
    timing_summary_lines.append(f"SMALL-SIGNAL TIMING SUMMARY: {case_label}")
    timing_summary_lines.append("=" * 78)
    timing_summary_lines.append("ANDES/VG = ANDES seconds / VeraGrid seconds")
    timing_summary_lines.append("Above 1: VeraGrid faster. Below 1: ANDES faster.")
    timing_summary_lines.append("")
    timing_summary_lines.append("PHASE DEFINITIONS")
    for (
        table_relation,
        table_phase_name,
        table_andes_seconds,
        table_andes_standard_deviation,
        table_veragrid_seconds,
        table_veragrid_standard_deviation,
        table_andes_over_veragrid,
        table_faster_engine,
        table_speedup_factor,
        table_scope,
    ) in table_rows:
        timing_summary_lines.append(
            f"- {table_phase_name}: {table_scope} [{table_relation}]"
        )
    timing_summary_lines.append("")
    timing_summary_lines.append(
        "Relation     Phase                                           "
        "ANDES mean±std [s]      VeraGrid mean±std [s]   ANDES/VG"
    )
    for (
        table_relation,
        table_phase_name,
        table_andes_seconds,
        table_andes_standard_deviation,
        table_veragrid_seconds,
        table_veragrid_standard_deviation,
        table_andes_over_veragrid,
        table_faster_engine,
        table_speedup_factor,
        table_scope,
    ) in table_rows:
        if table_relation == "COMPARABLE CALCULATION":
            summary_relation: str = "CALCULATION"
        elif table_relation == "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)":
            summary_relation = "PREPARATION"
        elif table_relation == "RESULT EXPORT":
            summary_relation = "EXPORT"
        elif table_relation == "POST-POWER-FLOW WORKFLOW TOTAL":
            summary_relation = "WORKFLOW"
        elif table_relation == "DIAGNOSTIC SUBCOMPONENT (already included)":
            summary_relation = "SUBCOMP"
        else:
            summary_relation = "EXCLUDED"
        summary_andes: str = (
            "--"
            if not np.isfinite(table_andes_seconds)
            else f"{table_andes_seconds:.6f}±{table_andes_standard_deviation:.6f}"
        )
        summary_veragrid: str = (
            "--"
            if not np.isfinite(table_veragrid_seconds)
            else f"{table_veragrid_seconds:.6f}±{table_veragrid_standard_deviation:.6f}"
        )
        summary_ratio: str = (
            "--"
            if not np.isfinite(table_andes_over_veragrid)
            else f"{table_andes_over_veragrid:.3f}"
        )
        timing_summary_lines.append(
            f"{summary_relation:12s} {table_phase_name:47s} "
            f"{summary_andes:>23s} {summary_veragrid:>26s} {summary_ratio:>11s}"
        )
    (comparison_directory.parent / "timing_summary.txt").write_text(
        "\n".join(timing_summary_lines) + "\n",
        encoding="utf-8",
    )

    visual_table_rows: list[
        tuple[str, str, float, float, float, float, float, str, float, str]
    ] = list()
    table_row: tuple[str, str, float, float, float, float, float, str, float, str]
    for table_row in table_rows:
        if table_row[0] in (
            "COMPARABLE CALCULATION",
            "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)",
            "RESULT EXPORT",
            "POST-POWER-FLOW WORKFLOW TOTAL",
        ):
            visual_table_rows.append(table_row)
        else:
            pass

    figure: Figure
    axis: Axes
    figure, axis = plt.subplots(figsize=(20.0, 0.55 * len(visual_table_rows) + 3.2))
    axis.axis("off")
    visual_rows: list[list[str]] = list()
    for (
        table_relation,
        table_phase_name,
        table_andes_seconds,
        table_andes_standard_deviation,
        table_veragrid_seconds,
        table_veragrid_standard_deviation,
        table_andes_over_veragrid,
        table_faster_engine,
        table_speedup_factor,
        table_scope,
    ) in visual_table_rows:
        if table_relation == "COMPARABLE CALCULATION":
            relation_text = "CALCULATION"
        elif table_relation == "ENGINE-SPECIFIC WORKFLOW COMPONENT (not internally comparable)":
            relation_text = "PREPARATION"
        elif table_relation == "RESULT EXPORT":
            relation_text = "EXPORT"
        elif table_relation == "POST-POWER-FLOW WORKFLOW TOTAL":
            relation_text = "WORKFLOW"
        else:
            relation_text = "N/A"
        visual_rows.append(list((
            relation_text,
            table_phase_name,
            (
                "--"
                if not np.isfinite(table_andes_seconds)
                else f"{table_andes_seconds:.6f} ± {table_andes_standard_deviation:.6f}"
            ),
            (
                "--"
                if not np.isfinite(table_veragrid_seconds)
                else f"{table_veragrid_seconds:.6f} ± {table_veragrid_standard_deviation:.6f}"
            ),
            (
                "--"
                if not np.isfinite(table_andes_over_veragrid)
                else f"{table_andes_over_veragrid:.3f}x"
            ),
            (
                "--"
                if not np.isfinite(table_speedup_factor)
                else f"{table_faster_engine} {table_speedup_factor:.2f}x"
            ),
        )))
    timing_table: Table = axis.table(
        cellText=visual_rows,
        colLabels=list(("Relation", "Phase", "ANDES mean ± std [s]", "VeraGrid mean ± std [s]", "ANDES/VG", "Faster by")),
        cellLoc="right",
        colLoc="center",
        loc="center",
        colWidths=list((0.10, 0.40, 0.12, 0.13, 0.11, 0.14)),
    )
    timing_table.auto_set_font_size(False)
    timing_table.set_fontsize(8.5)
    timing_table.scale(1.0, 1.35)
    row_index: int
    for row_index in range(len(visual_table_rows)):
        table_relation = visual_table_rows[row_index][0]
        column_index: int
        if table_relation in (
            "POST-POWER-FLOW WORKFLOW TOTAL",
        ):
            row_color: str = "#c6efce"
        else:
            row_color = "#ffffff"
        for column_index in range(6):
            timing_table[(row_index + 1, column_index)].set_facecolor(row_color)
    axis.set_title(
        f"{case_label}: small-signal wall-clock timing comparison (10 repetitions)\n"
        "Green = architecture-dependent post-power-flow workflow total.\n"
        "CALCULATION is directly comparable; PREPARATION is engine-specific.\n"
        "Case construction, power flow, warm-ups and script overhead are excluded.",
        pad=16.0,
    )
    figure.tight_layout()
    figure.savefig(comparison_directory / "timing_comparison_table.png", dpi=200, bbox_inches="tight")
    print(f"Timing comparison CSV written to: {comparison_csv}")
    return figure


def _run_andes_vs_veragrid_stability(
    veragrid_csv: Path,
    andes_csv: Path,
    case_label: str | None = None,
    output_dir: Path | None = None,
    show_figures: bool = False,
) -> None:
    """
    Compare VeraGrid and ANDES small-signal eigenvalues.

    :param veragrid_csv: VeraGrid modes.csv.
    :param andes_csv: ANDES eigenvalue CSV.
    :param case_label: Optional network label used in titles and filenames.
    :param output_dir: Optional folder for comparison figures and CSV files.
    :param show_figures: Display all generated figures interactively.
    :return: None.
    """
    # Derive every artifact path from explicit inputs, keeping the comparison
    # free of mutable module-level configuration.
    if case_label is None:
        inferred_label: str = andes_csv.stem.replace("Eigenvalues_results_Andes_", "")
    else:
        inferred_label = case_label
    comparison_dir: Path = _comparison_directory(
        case_label=inferred_label,
        output_dir=output_dir,
    )
    comparison_dir.mkdir(parents=True, exist_ok=True)

    veragrid_state_matrix_csv: Path = _find_single_result_file(
        results_dir=veragrid_csv.parent,
        preferred_names=(
            "state_matrix.csv",
            f"state_matrix_compiled_labeled_VeraGrid_{inferred_label}.csv",
            "state_matrix_benchmark_labeled.csv",
        ),
        glob_pattern="state_matrix*.csv",
    )
    andes_state_matrix_csv: Path = _find_single_result_file(
        results_dir=andes_csv.parent,
        preferred_names=(f"state_matrix_results_Andes_{inferred_label}.csv",),
        glob_pattern="state_matrix_results_Andes_*.csv",
    )
    state_matrix_comparison_png: Path = comparison_dir / "state_matrix_differences.png"
    participation_comparison_png: Path = comparison_dir / "participation_factor_differences.png"
    sdomain_comparison_png: Path = comparison_dir / "sdomain_eigenvalues.png"
    participation_difference_csv: Path = comparison_dir / "participation_factor_difference.csv"
    veragrid_bus_csv: Path = veragrid_csv.parent / "power_flow_buses.csv"
    andes_bus_csv: Path = andes_csv.parent / f"solved_bus_Andes_{inferred_label}.csv"
    generated_figures: list[Any] = list()
    timing_figure: Any | None = _create_timing_comparison(
        veragrid_results_directory=veragrid_csv.parent,
        andes_results_directory=andes_csv.parent,
        comparison_directory=comparison_dir,
        case_label=inferred_label,
    )
    if timing_figure is None:
        pass
    else:
        generated_figures.append(timing_figure)

    # Load and canonicalize state spaces before modal matching. ANDES may retain
    # unused measurement devices or zero-parameter block-realization states
    # that do not belong to VeraGrid's physical consumer-owned model.
    veragrid_state_matrix: np.ndarray | None = None
    andes_state_matrix: np.ndarray | None = None
    veragrid_row_labels: list[str] = list()
    veragrid_column_labels: list[str] = list()
    andes_row_labels: list[str] = list()
    andes_column_labels: list[str] = list()
    excluded_andes_states: list[str] = list()
    if veragrid_state_matrix_csv.is_file() and andes_state_matrix_csv.is_file():
        veragrid_state_matrix = load_veragrid_state_matrix(veragrid_state_matrix_csv)
        andes_state_matrix = load_andes_state_matrix(andes_state_matrix_csv)
        veragrid_row_labels, veragrid_column_labels = load_veragrid_state_matrix_labels(
            veragrid_state_matrix_csv
        )
        andes_row_labels, andes_column_labels = load_andes_state_matrix_labels(
            andes_state_matrix_csv
        )
        (
            andes_state_matrix,
            andes_row_labels,
            andes_column_labels,
            excluded_andes_states,
        ) = reduce_andes_to_common_physical_states(
            matrix=andes_state_matrix,
            row_labels=andes_row_labels,
            column_labels=andes_column_labels,
            veragrid_labels=veragrid_row_labels,
        )
        if len(excluded_andes_states) > 0:
            print("ANDES-only states excluded from the common physical view:")
            excluded_state: str
            for excluded_state in excluded_andes_states:
                print(f"  - {excluded_state}")
        else:
            pass
    else:
        pass

    # Verify the static voltage operating point before comparing dynamics.
    if veragrid_bus_csv.is_file() and andes_bus_csv.is_file():
        max_voltage_error: float
        max_angle_error: float
        max_voltage_error, max_angle_error = compare_power_flow_buses(
            veragrid_csv=veragrid_bus_csv,
            andes_csv=andes_bus_csv,
        )
        print("Power-flow bus comparison:")
        print(f"  Maximum voltage-magnitude error: {max_voltage_error:.6e} pu")
        print(f"  Maximum voltage-angle error: {max_angle_error:.6e} rad")
    else:
        print("Power-flow bus comparison skipped because one solved bus table is missing.")

    veragrid_eig = load_veragrid_eigenvalues(veragrid_csv)
    andes_eig = load_andes_eigenvalues(andes_csv)

    if andes_state_matrix is not None and len(excluded_andes_states) > 0:
        # Recompute modes after canonicalization so the plotted eigenvalues and
        # participation factors describe the same retained state coordinates.
        andes_eig = np.linalg.eigvals(andes_state_matrix.real)
        print(
            "ANDES eigenvalues recomputed from the common physical-state "
            "matrix after exclusions."
        )
    else:
        pass

    # Remove non-finite values before matching.
    veragrid_valid = (
        np.isfinite(veragrid_eig.real)
        & np.isfinite(veragrid_eig.imag)
    )
    andes_valid = (
        np.isfinite(andes_eig.real)
        & np.isfinite(andes_eig.imag)
    )

    veragrid_eig = veragrid_eig[veragrid_valid]
    andes_eig = andes_eig[andes_valid]

    print(f"VeraGrid eigenvalue file: {veragrid_csv}")
    print(f"ANDES eigenvalue file:    {andes_csv}")

    print(f"\nVeraGrid modes loaded: {len(veragrid_eig)}")
    print(f"ANDES modes loaded:    {len(andes_eig)}")

    andes_matched, veragrid_matched, absolute_error = match_eigenvalues(
        reference=andes_eig,
        candidate=veragrid_eig,
    )

    denominator = np.abs(andes_matched)

    relative_error = np.full(
        andes_matched.shape,
        np.inf,
        dtype=float,
    )

    nonzero = denominator > 1e-10
    relative_error[nonzero] = (
        absolute_error[nonzero] / denominator[nonzero] * 100.0
    )

    print("\nMatched modes:")
    print(
        f"{'Mode':>5}  "
        f"{'ANDES eigenvalue':>32}  "
        f"{'VeraGrid eigenvalue':>32}  "
        f"{'|d_lambda|':>14}  "
        f"{'Rel. err [%]':>14}"
    )
    print("-" * 108)

    for idx, (
        andes_value,
        veragrid_value,
        abs_error,
        rel_error,
    ) in enumerate(
        zip(
            andes_matched,
            veragrid_matched,
            absolute_error,
            relative_error,
        ),
        start=1,
    ):
        print(
            f"{idx:5d}  "
            f"{andes_value.real:+14.7e}{andes_value.imag:+14.7e}j  "
            f"{veragrid_value.real:+14.7e}{veragrid_value.imag:+14.7e}j  "
            f"{abs_error:14.7e}  "
            f"{rel_error:14.7e}"
        )

    finite_relative_error = relative_error[np.isfinite(relative_error)]

    if finite_relative_error.size > 0:
        print("\nComparison summary:")
        print(
            f"  Mean relative eigenvalue error: "
            f"{np.mean(finite_relative_error):.6f} %"
        )
        print(
            f"  Maximum relative eigenvalue error: "
            f"{np.max(finite_relative_error):.6f} %"
        )
        print(
            f"  Mean absolute eigenvalue error: "
            f"{np.mean(absolute_error):.6e} rad/s"
        )
    else:
        print("\nComparison summary unavailable: no finite relative eigenvalue errors.")

    if veragrid_state_matrix is not None and andes_state_matrix is not None:

        print("\nState-matrix dimensions:")
        print(f"  VeraGrid: {veragrid_state_matrix.shape}")
        print(f"  ANDES:    {andes_state_matrix.shape}")

        mapped_veragrid_row_labels = map_veragrid_labels_to_andes_style(veragrid_row_labels)
        mapped_veragrid_column_labels = map_veragrid_labels_to_andes_style(veragrid_column_labels)
        mapped_veragrid_row_labels = map_simple_veragrid_labels(
            veragrid_labels=mapped_veragrid_row_labels,
            andes_labels=andes_row_labels,
        )
        mapped_veragrid_column_labels = map_simple_veragrid_labels(
            veragrid_labels=mapped_veragrid_column_labels,
            andes_labels=andes_column_labels,
        )
        normalized_veragrid_row_labels = normalize_state_labels(mapped_veragrid_row_labels)
        normalized_veragrid_column_labels = normalize_state_labels(mapped_veragrid_column_labels)
        normalized_andes_row_labels = normalize_state_labels(andes_row_labels)
        normalized_andes_column_labels = normalize_state_labels(andes_column_labels)

        row_labels_match = normalized_veragrid_row_labels == normalized_andes_row_labels
        column_labels_match = normalized_veragrid_column_labels == normalized_andes_column_labels
        row_label_sets_match: bool = set(normalized_veragrid_row_labels) == set(normalized_andes_row_labels)
        column_label_sets_match: bool = set(normalized_veragrid_column_labels) == set(normalized_andes_column_labels)

        print("\nState-matrix labels:")
        print(f"  Same row-label set:     {row_label_sets_match}")
        print(f"  Same column-label set:  {column_label_sets_match}")
        print(f"  Same row order:         {row_labels_match}")
        print(f"  Same column order:      {column_labels_match}")

        if veragrid_state_matrix.shape == andes_state_matrix.shape:
            reordered_andes_state_matrix, missing_labels = reorder_andes_state_matrix_to_veragrid(
                andes_state_matrix=andes_state_matrix,
                andes_row_labels=normalized_andes_row_labels,
                andes_column_labels=normalized_andes_column_labels,
                veragrid_row_labels=normalized_veragrid_row_labels,
                veragrid_column_labels=normalized_veragrid_column_labels,
            )

            if reordered_andes_state_matrix is None:
                print("\nState-matrix comparison summary:")
                print("  The ANDES matrix could not be reordered to the VeraGrid variable order.")
                print(f"  Missing labels: {missing_labels}")
            else:
                if len(missing_labels) > 0:
                    print(
                        "  Warning: state labels could not be mapped completely; "
                        "using positional alignment for visual inspection."
                    )
                    print(f"  Unmapped labels: {missing_labels}")
                else:
                    pass
                difference_matrix = veragrid_state_matrix - reordered_andes_state_matrix
                fro_norm = float(np.linalg.norm(difference_matrix, ord="fro"))
                andes_fro_norm = float(np.linalg.norm(reordered_andes_state_matrix, ord="fro"))
                relative_fro_norm = fro_norm / andes_fro_norm
                max_abs_difference = float(np.max(np.abs(difference_matrix)))

                print("\nState-matrix comparison summary:")
                print("  ANDES matrix reordered to VeraGrid label order before comparison.")
                print(f"  Frobenius norm of dA: {fro_norm:.6e}")
                print(f"  Relative Frobenius norm of dA: {relative_fro_norm:.6e}")
                print(f"  Maximum absolute entry error: {max_abs_difference:.6e}")

                # Recompute both participation matrices with the same
                # state-by-mode definition, then align modal columns.
                andes_pf_eigenvalues, andes_participation = compute_andes_participation_factors(
                    reordered_andes_state_matrix.real
                )
                veragrid_pf_eigenvalues, veragrid_participation = compute_andes_participation_factors(
                    veragrid_state_matrix.real
                )
                pf_distance_matrix = np.abs(
                    andes_pf_eigenvalues[:, np.newaxis]
                    - veragrid_pf_eigenvalues[np.newaxis, :]
                )
                andes_pf_indexes, veragrid_pf_indexes = linear_sum_assignment(pf_distance_matrix)
                pf_ordering = np.argsort(andes_pf_indexes)
                andes_pf_indexes = andes_pf_indexes[pf_ordering]
                veragrid_pf_indexes = veragrid_pf_indexes[pf_ordering]
                participation_difference = (
                    veragrid_participation[:, veragrid_pf_indexes]
                    - andes_participation[:, andes_pf_indexes]
                )
                matched_andes_pf_eigenvalues: np.ndarray = andes_pf_eigenvalues[andes_pf_indexes]
                degenerate_mode_mask: np.ndarray = identify_basis_degenerate_modes(
                    matched_andes_pf_eigenvalues
                )
                comparable_participation_difference: np.ndarray = participation_difference[
                    :, ~degenerate_mode_mask
                ]
                pf_fro_norm = float(np.linalg.norm(comparable_participation_difference, ord="fro"))
                pf_reference_norm = float(
                    np.linalg.norm(
                        andes_participation[:, andes_pf_indexes][:, ~degenerate_mode_mask],
                        ord="fro",
                    )
                )
                pf_relative_fro_norm = pf_fro_norm / pf_reference_norm
                pf_max_abs_difference = float(
                    np.max(np.abs(comparable_participation_difference))
                )
                visual_participation_difference: np.ndarray = participation_difference.copy()
                visual_participation_difference[:, degenerate_mode_mask] = np.nan
                print("\nParticipation-factor comparison summary:")
                print("  Both matrices use biorthogonal state-by-mode factors normalized per mode.")
                print("  Factors are rounded to five decimals after normalization.")
                print(
                    "  Individually basis-dependent repeated modes excluded from dPF norms: "
                    f"{int(np.count_nonzero(degenerate_mode_mask))}."
                )
                print("  Every eigenvalue remains included in the eigenvalue comparison.")
                print(f"  Frobenius norm of dPF: {pf_fro_norm:.6e}")
                print(f"  Relative Frobenius norm of dPF: {pf_relative_fro_norm:.6e}")
                print(f"  Maximum absolute factor error: {pf_max_abs_difference:.6e}")
                save_participation_difference(
                    output_path=participation_difference_csv,
                    state_labels=normalized_veragrid_row_labels,
                    difference=visual_participation_difference,
                )
                report_top_matrix_mismatches(
                    andes_matrix=reordered_andes_state_matrix,
                    veragrid_matrix=veragrid_state_matrix,
                    row_labels=normalized_veragrid_row_labels,
                    column_labels=normalized_veragrid_column_labels,
                    top_n=30,
                )
                fig_matrix: Any = _create_state_matrix_figure(
                    andes_matrix=reordered_andes_state_matrix,
                    veragrid_matrix=veragrid_state_matrix,
                    difference=difference_matrix,
                    row_labels=normalized_veragrid_row_labels,
                    column_labels=normalized_veragrid_column_labels,
                    case_label=inferred_label,
                )
                fig_matrix.savefig(state_matrix_comparison_png, dpi=200, bbox_inches="tight")
                generated_figures.append(fig_matrix)

                aligned_andes_participation: np.ndarray = andes_participation[:, andes_pf_indexes]
                aligned_veragrid_participation: np.ndarray = veragrid_participation[:, veragrid_pf_indexes]
                plotted_participation_difference: np.ndarray = np.nan_to_num(
                    visual_participation_difference,
                    nan=0.0,
                )
                fig_participation: Any = _create_participation_figure(
                    andes_participation=aligned_andes_participation,
                    veragrid_participation=aligned_veragrid_participation,
                    difference=plotted_participation_difference,
                    state_labels=normalized_veragrid_row_labels,
                    case_label=inferred_label,
                )
                fig_participation.savefig(
                    participation_comparison_png,
                    dpi=200,
                    bbox_inches="tight",
                )
                generated_figures.append(fig_participation)
        else:
            print("\nState-matrix comparison summary:")
            print("  The state matrices do not have the same dimensions, so no direct entry-wise subtraction was performed.")
            print("  Structural heatmaps, row norms, state counts and matrix densities were plotted instead.")
            andes_pf_eigenvalues, andes_participation = compute_andes_participation_factors(
                andes_state_matrix.real
            )
            veragrid_pf_eigenvalues, veragrid_participation = compute_andes_participation_factors(
                veragrid_state_matrix.real
            )
            andes_pf_indexes: np.ndarray
            veragrid_pf_indexes: np.ndarray
            andes_pf_indexes, veragrid_pf_indexes = _match_modal_indexes(
                andes_eigenvalues=andes_pf_eigenvalues,
                veragrid_eigenvalues=veragrid_pf_eigenvalues,
            )
            aligned_andes_participation: np.ndarray = andes_participation[:, andes_pf_indexes]
            aligned_veragrid_participation: np.ndarray = veragrid_participation[:, veragrid_pf_indexes]
            peak_pf_difference: np.ndarray = (
                np.max(aligned_veragrid_participation, axis=0)
                - np.max(aligned_andes_participation, axis=0)
            )
            print("\nParticipation-factor comparison summary:")
            print("  Modes were matched by eigenvalue; state rows remain model-specific.")
            print(
                "  Maximum peak-participation difference across matched modes: "
                f"{np.max(np.abs(peak_pf_difference)):.6e}"
            )

            fig_matrix: Any = _create_unaligned_state_matrix_figure(
                andes_matrix=andes_state_matrix,
                veragrid_matrix=veragrid_state_matrix,
                case_label=inferred_label,
            )
            fig_matrix.savefig(state_matrix_comparison_png, dpi=200, bbox_inches="tight")
            generated_figures.append(fig_matrix)
            fig_participation: Any = _create_unaligned_participation_figure(
                andes_participation=aligned_andes_participation,
                veragrid_participation=aligned_veragrid_participation,
                case_label=inferred_label,
            )
            fig_participation.savefig(
                participation_comparison_png,
                dpi=200,
                bbox_inches="tight",
            )
            generated_figures.append(fig_participation)
    else:
        print("\nState-matrix CSV files were not found for comparison.")

    # --------------------------------------------------------------------------
    # S-domain comparison plot
    # --------------------------------------------------------------------------

    fig, ax = plt.subplots(figsize=(9, 7))

    # Correct 5% damping-ratio lines.
    zeta = 0.05
    slope = np.sqrt(1.0 - zeta ** 2) / zeta

    all_values = np.concatenate(
        (andes_matched, veragrid_matched)
    )

    real_values = all_values.real
    imag_values = all_values.imag

    real_span = float(np.ptp(real_values))
    imag_span = float(np.ptp(imag_values))

    margin_x = max(real_span * 0.10, 0.1)
    margin_y = max(imag_span * 0.10, 0.1)

    x_min = float(real_values.min() - margin_x)
    x_max = float(real_values.max() + margin_x)
    y_min = float(imag_values.min() - margin_y)
    y_max = float(imag_values.max() + margin_y)

    x_z = np.linspace(min(-200.0, x_min), 0.0, 500)
    y_z = slope * x_z

    ax.plot(
        x_z,
        y_z,
        "--",
        linewidth=0.8,
        color="grey",
        label=r"$\zeta = 5\%$",
    )
    ax.plot(
        x_z,
        -y_z,
        "--",
        linewidth=0.8,
        color="grey",
    )

    ax.scatter(
        andes_matched.real,
        andes_matched.imag,
        marker="o",
        label="ANDES",
    )
    ax.scatter(
        veragrid_matched.real,
        veragrid_matched.imag,
        marker="x",
        label="VeraGrid",
    )

    # Connect each matched pair so discrepancies are visible.
    for andes_value, veragrid_value in zip(
        andes_matched,
        veragrid_matched,
    ):
        ax.plot(
            list((andes_value.real, veragrid_value.real)),
            list((andes_value.imag, veragrid_value.imag)),
            linewidth=0.5,
            alpha=0.5,
            color="grey",
        )

    ax.set_xlabel("Real [rad/s]")
    ax.set_ylabel("Imaginary [rad/s]")
    ax.set_title(f"{inferred_label} small-signal stability: ANDES vs VeraGrid")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.axhline(0.0, linewidth=1.0, color="black")
    ax.axvline(0.0, linewidth=1.0, color="black")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(sdomain_comparison_png, dpi=200, bbox_inches="tight")
    generated_figures.append(fig)

    print(f"\nComparison figures and CSV files written to: {comparison_dir}")
    if show_figures:
        plt.show(block=False)
    else:
        generated_figure: Any
        for generated_figure in generated_figures:
            plt.close(generated_figure)


def andes_vs_veragrid_stability(
    veragrid_csv: Path,
    andes_csv: Path,
    case_label: str | None = None,
    output_dir: Path | None = None,
    show_figures: bool = False,
) -> None:
    """Run a comparison while mirroring all console output to a text report.

    :param veragrid_csv: VeraGrid modes CSV.
    :param andes_csv: ANDES eigenvalue CSV.
    :param case_label: Optional network label used in titles and filenames.
    :param output_dir: Optional folder name below the small-signal directory.
    :param show_figures: Display all generated figures interactively.
    :return: None.
    """
    if case_label is None:
        inferred_label: str = andes_csv.stem.replace("Eigenvalues_results_Andes_", "")
    else:
        inferred_label = case_label
    comparison_dir: Path = _comparison_directory(
        case_label=inferred_label,
        output_dir=output_dir,
    )
    comparison_dir.mkdir(parents=True, exist_ok=True)
    report_path: Path = comparison_dir / "comparison_report.txt"

    # Capture the diagnostics once, then write the same readable text to the
    # terminal and beside the generated plots.
    report_buffer: StringIO = StringIO()
    with redirect_stdout(report_buffer), redirect_stderr(report_buffer):
        print(f"Comparison case: {inferred_label}")
        print(f"VeraGrid results: {veragrid_csv.parent.resolve()}")
        print(f"ANDES results:    {andes_csv.parent.resolve()}")
        _run_andes_vs_veragrid_stability(
            veragrid_csv=veragrid_csv,
            andes_csv=andes_csv,
            case_label=inferred_label,
            output_dir=comparison_dir,
            show_figures=show_figures,
        )
        print(f"Comparison report written to: {report_path}")
    report_text: str = report_buffer.getvalue()
    print(report_text, end="")
    report_path.write_text(report_text, encoding="utf-8")


def compare_result_folders(
    veragrid_results_dir: Path,
    andes_results_dir: Path,
    case_label: str,
    output_dir: Path | None = None,
    show_figures: bool = False,
) -> None:
    """Compare one arbitrary pair of VeraGrid and ANDES result folders.

    :param veragrid_results_dir: Folder containing VeraGrid ``modes.csv`` and A.
    :param andes_results_dir: Folder containing ANDES eigenvalues and A.
    :param case_label: Network label used to discover files and title figures.
    :param output_dir: Optional destination for visual comparison artifacts.
    :param show_figures: Display generated figures interactively.
    :return: None.
    """
    veragrid_csv: Path = _find_single_result_file(
        results_dir=veragrid_results_dir.resolve(),
        preferred_names=("modes.csv",),
        glob_pattern="*modes*.csv",
    )
    andes_csv: Path = _find_single_result_file(
        results_dir=andes_results_dir.resolve(),
        preferred_names=(f"Eigenvalues_results_Andes_{case_label}.csv",),
        glob_pattern="Eigenvalues_results_Andes_*.csv",
    )
    andes_vs_veragrid_stability(
        veragrid_csv=veragrid_csv,
        andes_csv=andes_csv,
        case_label=case_label,
        output_dir=output_dir,
        show_figures=show_figures,
    )


