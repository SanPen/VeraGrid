# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Sparse CLU analysis, factorization, refactorization, and solve in Numba."""

from enum import Enum

import numba
import numpy as np
import scipy.sparse as sp
from llvmlite import ir
from numba import types
from numba.extending import intrinsic
from numba.typed import List


class Ordering(Enum):
    """CLU symbolic column-ordering strategy."""

    NATURAL = 0
    APPROXIMATE_MINIMUM_DEGREE = 1


class Status(Enum):
    """Result codes used by the C++ CLU API."""

    SUCCESS = 0
    INVALID_INPUT = 1
    SINGULAR = 2
    NUMERICAL_FAILURE = 3
    OUT_OF_MEMORY = 4


class Options:
    """CLU ordering, block analysis, and pivot controls."""

    __slots__ = ("ordering", "use_block_triangular_form", "pivot_tolerance", "symmetric_pattern")

    def __init__(self, ordering: Ordering = Ordering.APPROXIMATE_MINIMUM_DEGREE,
                 use_block_triangular_form: bool = True,
                 pivot_tolerance: float = 1e-3,
                 symmetric_pattern: bool = False) -> None:
        """Create CLU analysis and numeric options.

        :param ordering: Column ordering strategy.
        :param use_block_triangular_form: Whether to compute BTF blocks.
        :param pivot_tolerance: Relative threshold for preferred pivots.
        :param symmetric_pattern: Caller guarantee of structural symmetry.
        :return: Nothing.
        """
        self.ordering: Ordering = ordering
        self.use_block_triangular_form: bool = use_block_triangular_form
        self.pivot_tolerance: float = pivot_tolerance
        self.symmetric_pattern: bool = symmetric_pattern


class Statistics:
    """Matrix and factor counts from CLU analysis or factorization."""

    __slots__ = ("order", "nonzeros", "blocks", "largest_block",
                 "lower_nonzeros", "upper_nonzeros")

    def __init__(self, order: int = 0, nonzeros: int = 0, blocks: int = 0,
                 largest_block: int = 0, lower_nonzeros: int = 0,
                 upper_nonzeros: int = 0) -> None:
        """Initialize all CLU counters.

        :param order: Matrix order.
        :param nonzeros: Stored CSC entries, including duplicates.
        :param blocks: Analyzed diagonal BTF blocks.
        :param largest_block: Largest BTF block order.
        :param lower_nonzeros: Strict L factor entries.
        :param upper_nonzeros: U factor entries including the diagonal.
        :return: Nothing.
        """
        self.order: int = order
        self.nonzeros: int = nonzeros
        self.blocks: int = blocks
        self.largest_block: int = largest_block
        self.lower_nonzeros: int = lower_nonzeros
        self.upper_nonzeros: int = upper_nonzeros


class Workspace:
    """Reusable order-bound numeric work buffer for CLU operations."""

    __slots__ = ("order", "work")

    def __init__(self, order: int) -> None:
        """Allocate dense scratch for one matrix order.

        :param order: Matrix order used by later refactor or solve calls.
        :return: Nothing.
        """
        if order < 0 or order > np.iinfo(np.int32).max:
            raise ValueError("workspace order must fit int32")
        else:
            pass
        self.order: int = order
        self.work: np.ndarray = np.empty(order, dtype=np.float64)


class Symbolic:
    """Reusable CLU matching, ordering, BTF, and fixed-pattern state."""

    __slots__ = ("_order", "_indptr", "_indices", "_column_order", "_preferred_rows",
                 "_block_offsets", "_fixed_positions",
                 "_lower_flat", "_lower_offsets", "_upper_flat", "_upper_offsets",
                 "_upper_block_starts", "_tiny_dense", "_diagonal_pattern",
                 "_fixed_pattern_ready", "_ordering_envelope", "_statistics", "_valid")

    def __init__(self) -> None:
        """Create invalid symbolic state, ready for :func:`analyze`.

        :return: Nothing.
        """
        self._order: int = 0
        self._indptr: np.ndarray = np.empty(0, dtype=np.int32)
        self._indices: np.ndarray = np.empty(0, dtype=np.int32)
        self._column_order: np.ndarray = np.empty(0, dtype=np.int32)
        self._preferred_rows: np.ndarray = np.empty(0, dtype=np.int32)
        self._block_offsets: np.ndarray = np.empty(0, dtype=np.int32)
        self._lower_flat: np.ndarray = np.empty(0, dtype=np.int32)
        self._lower_offsets: np.ndarray = np.empty(0, dtype=np.int32)
        self._upper_flat: np.ndarray = np.empty(0, dtype=np.int32)
        self._upper_offsets: np.ndarray = np.empty(0, dtype=np.int32)
        self._fixed_positions: np.ndarray = np.empty(0, dtype=np.int32)
        self._upper_block_starts: np.ndarray = np.empty(0, dtype=np.int32)
        self._tiny_dense: bool = False
        self._diagonal_pattern: bool = False
        self._fixed_pattern_ready: bool = False
        self._ordering_envelope: bool = False
        self._statistics: Statistics = Statistics()
        self._valid: bool = False

    def is_valid(self) -> bool:
        """Return whether structural analysis completed.

        :return: True for reusable symbolic state.
        """
        return self._valid

    @property
    def order(self) -> int:
        """Return the analyzed matrix order.

        :return: Matrix order, or zero before analysis.
        """
        return self._order

    @property
    def statistics(self) -> Statistics:
        """Return analysis counters.

        :return: CLU statistics for the saved structure.
        """
        return self._statistics

    @property
    def column_order(self) -> np.ndarray:
        """Return original columns in factor order.

        :return: Analyzed column permutation.
        """
        return self._column_order

    @property
    def preferred_rows(self) -> np.ndarray:
        """Return matched original rows in factor order.

        :return: Preferred row permutation.
        """
        return self._preferred_rows

    @property
    def block_offsets(self) -> np.ndarray:
        """Return the half-open BTF block boundaries.

        :return: Analyzed block offsets.
        """
        return self._block_offsets


def status_name(status: Status) -> str:
    """Return the stable CLU diagnostic name for a result code.

    :param status: CLU status value.
    :return: Lowercase diagnostic name, or ``unknown`` for another value.
    """
    if isinstance(status, Status):
        return status.name.lower()
    else:
        return "unknown"


@numba.njit(cache=True)
def _safe_reciprocal(divisor: float) -> float:
    """Return CLU's safe normal reciprocal or its division fallback marker.

    :param divisor: Nonzero finite divisor.
    :return: Normal finite reciprocal, or zero.
    """
    reciprocal: float = 1.0 / divisor
    if np.isfinite(reciprocal) and abs(reciprocal) >= np.finfo(np.float64).tiny:
        return reciprocal
    else:
        return 0.0


@numba.njit(cache=True)
def _valid_matrix(order: int, indptr: np.ndarray, indices: np.ndarray,
                  values: np.ndarray) -> tuple[bool, bool, bool]:
    """Port CLU's CSC preflight and diagonal pattern discovery.

    :param order: Matrix order.
    :param indptr: CSC column pointers.
    :param indices: CSC row indices.
    :param values: CSC numerical entries.
    :return: Validity, diagonal-only flag, and identity matching flag.
    """
    diagonal_pattern: bool = order > 0
    identity_matching_available: bool = True
    if order < 0 or indptr.size != order + 1 or indices.size != values.size or indptr[0] != 0 or indptr[order] != indices.size:
        return False, False, False
    else:
        pass
    column: int = 0
    entry: int = 0
    row: int = 0
    begin: int = 0
    end: int = 0
    diagonal_present: bool = False
    for column in range(order):
        begin = indptr[column]
        end = indptr[column + 1]
        if begin < 0 or end < begin or end > indices.size:
            return False, False, False
        else:
            pass
        diagonal_present = False
        for entry in range(begin, end):
            row = indices[entry]
            if row < 0 or row >= order:
                return False, False, False
            elif row == column:
                diagonal_present = True
            else:
                diagonal_pattern = False
        identity_matching_available = identity_matching_available and diagonal_present
        diagonal_pattern = diagonal_pattern and diagonal_present and end == begin + 1
    if not np.all(np.isfinite(values)):
        return False, False, False
    else:
        return True, diagonal_pattern, identity_matching_available


@numba.njit(cache=True)
def _valid_same_pattern(order: int, indptr: np.ndarray, indices: np.ndarray,
                        values: np.ndarray, symbolic_valid: bool,
                        symbolic_order: int, pattern_pointers: np.ndarray,
                        pattern_rows: np.ndarray) -> bool:
    """Port CLU's exact CSC pattern and finite-value replay preflight.

    :param order: Candidate matrix order.
    :param indptr: Candidate CSC offsets.
    :param indices: Candidate CSC rows.
    :param values: Candidate numerical entries.
    :param symbolic_valid: Whether saved analysis remains valid.
    :param symbolic_order: Saved analysis order.
    :param pattern_pointers: Saved CSC offsets.
    :param pattern_rows: Saved CSC rows.
    :return: Whether the candidate has the analyzed finite pattern.
    """
    if not symbolic_valid or order < 0 or order != symbolic_order or indptr.size != order + 1 or pattern_pointers.size != order + 1:
        return False
    else:
        pass
    nonzeros: int = indptr[order]
    if nonzeros < 0 or nonzeros > np.iinfo(np.int32).max or indices.size != nonzeros or values.size != nonzeros or pattern_rows.size != nonzeros:
        return False
    else:
        pass
    entry: int = 0
    for entry in range(order + 1):
        if indptr[entry] != pattern_pointers[entry]:
            return False
        else:
            pass
    for entry in range(nonzeros):
        if indices[entry] != pattern_rows[entry] or not np.isfinite(values[entry]):
            return False
        else:
            pass
    return True


@numba.njit(cache=True)
def _valid_options(pivot_tolerance: float) -> bool:
    """Validate the CLU pivot threshold.

    :param pivot_tolerance: Candidate relative pivot threshold.
    :return: Whether the threshold is finite and in the supported interval.
    """
    return np.isfinite(pivot_tolerance) and 0.0 < pivot_tolerance <= 1.0


@numba.njit(cache=True)
def _compute_row_scales(order: int, indices: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Port CLU's maximum magnitude row equilibration.

    :param order: Matrix order.
    :param indices: CSC row indices.
    :param values: CSC numerical values.
    :return: Row maxima and safe reciprocals.
    """
    scales: np.ndarray = np.zeros(order, dtype=np.float64)
    reciprocals: np.ndarray = np.empty(order, dtype=np.float64)
    entry: int = 0
    row: int = 0
    reciprocal: float = 0.0
    for entry in range(values.size):
        row = indices[entry]
        scales[row] = max(scales[row], abs(values[entry]))
    for row in range(order):
        if scales[row] == 0.0:
            scales[row] = 1.0
            reciprocals[row] = 1.0
        else:
            reciprocal = 1.0 / scales[row]
            if np.isfinite(reciprocal) and reciprocal >= np.finfo(np.float64).tiny:
                reciprocals[row] = reciprocal
            else:
                reciprocals[row] = 0.0
    return scales, reciprocals


@numba.njit(cache=True, inline="always")
def _equilibrated_value(value: float, row: int, scales: np.ndarray, reciprocals: np.ndarray) -> float:
    """Apply CLU's row scaling with a safe division fallback.

    :param value: Input matrix or right-hand side value.
    :param row: Original row index.
    :param scales: Row maxima.
    :param reciprocals: Safe reciprocals, or zero markers.
    :return: Scaled value.
    """
    if reciprocals[row] != 0.0:
        return value * reciprocals[row]
    else:
        return value / scales[row]


@numba.njit(cache=True, inline="always")
def _add_work_value(row: int, value: float, stamp: int, marks: np.ndarray,
                    work: np.ndarray, touched: np.ndarray, touched_count: int) -> int:
    """Accumulate one row in CLU's stamped sparse-column workspace.

    :param row: Input row index.
    :param value: Contribution to add.
    :param stamp: Current column mark.
    :param marks: Last touched stamp for each row.
    :param work: Dense numerical scratch.
    :param touched: Rows reached in this column.
    :param touched_count: Number of occupied touched slots.
    :return: Updated touched count.
    """
    if marks[row] != stamp:
        marks[row] = stamp
        work[row] = value
        touched[touched_count] = row
        return touched_count + 1
    else:
        work[row] += value
        return touched_count


@numba.njit(cache=True)
def _scatter_column(indptr: np.ndarray, indices: np.ndarray, values: np.ndarray,
                    original_column: int, scales: np.ndarray, reciprocals: np.ndarray,
                    stamp: int, marks: np.ndarray, work: np.ndarray,
                    touched: np.ndarray) -> int:
    """Scatter one scaled CSC column into CLU's stamped workspace.

    :param indptr: CSC column pointers.
    :param indices: CSC row indices.
    :param values: CSC numerical entries.
    :param original_column: Input column to scatter.
    :param scales: Original row maxima.
    :param reciprocals: Safe reciprocal scales.
    :param stamp: Current column mark.
    :param marks: Row visit marks.
    :param work: Dense numerical scratch.
    :param touched: Reached input rows.
    :return: Number of reached rows.
    """
    touched_count: int = 0
    entry: int = 0
    row: int = 0
    for entry in range(indptr[original_column], indptr[original_column + 1]):
        row = indices[entry]
        touched_count = _add_work_value(row, _equilibrated_value(values[entry], row, scales, reciprocals),
                                        stamp, marks, work, touched, touched_count)
    return touched_count


@numba.njit(cache=True)
def _scatter_replay_column(indptr: np.ndarray, indices: np.ndarray, values: np.ndarray,
                           original_column: int, row_positions: np.ndarray,
                           scales: np.ndarray, reciprocals: np.ndarray,
                           work: np.ndarray) -> None:
    """Scatter a changed-value CSC column into fixed pivot positions.

    :param indptr: CSC column pointers.
    :param indices: CSC row indices.
    :param values: Changed numerical entries.
    :param original_column: Input column to replay.
    :param row_positions: Original-row to pivot-position map.
    :param scales: New row maxima.
    :param reciprocals: Safe reciprocal scales.
    :param work: Zeroed pivot-order numerical scratch.
    :return: Nothing.
    """
    entry: int = 0
    original_row: int = 0
    for entry in range(indptr[original_column], indptr[original_column + 1]):
        original_row = indices[entry]
        work[row_positions[original_row]] += _equilibrated_value(values[entry], original_row, scales, reciprocals)


@numba.njit(cache=True)
def _sort_pattern_slice(values: np.ndarray, begin: int, end: int) -> None:
    """Sort a pattern slice using CLU's short-column insertion path.

    :param values: Integer pattern storage modified in place.
    :param begin: First included position.
    :param end: Exclusive position limit.
    :return: Nothing.
    """
    sort_index: int = 0
    value: int = 0
    insertion: int = 0
    if end - begin <= 16:
        for sort_index in range(begin + 1, end):
            value = values[sort_index]
            insertion = sort_index
            while insertion > begin and values[insertion - 1] > value:
                values[insertion] = values[insertion - 1]
                insertion -= 1
            values[insertion] = value
    else:
        values[begin:end].sort()


@numba.njit(cache=True)
def _collect_candidates(column: int, block_begin: int, touched: np.ndarray,
                        touched_count: int, lower_indices: np.ndarray,
                        lower_offsets: np.ndarray, row_positions: np.ndarray,
                        candidate_marks: np.ndarray, stamp: int,
                        candidates: np.ndarray) -> int:
    """Collect sorted previous factor columns in CLU's sparse reach.

    :param column: Current factor column.
    :param block_begin: First column in this BTF block.
    :param touched: Initially reached original rows.
    :param touched_count: Number of initially reached rows.
    :param lower_indices: Earlier strict L original-row indices in flat storage.
    :param lower_offsets: Strict L column boundaries.
    :param row_positions: Current original-row to pivot-position map.
    :param candidate_marks: Prior-column visit marks.
    :param stamp: Current candidate mark.
    :param candidates: Preallocated candidate scratch.
    :return: Number of sorted reached factor columns in ``candidates``.
    """
    candidate_count: int = 0
    row_index: int = 0
    row: int = 0
    position: int = 0
    candidate_index: int = 0
    previous_column: int = 0
    lower_index: int = 0
    for row_index in range(touched_count):
        row = touched[row_index]
        position = row_positions[row]
        if 0 <= position < column and candidate_marks[position] != stamp:
            candidate_marks[position] = stamp
            candidates[candidate_count] = position
            candidate_count += 1
        else:
            pass
    candidate_index = 0
    while candidate_index < candidate_count:
        previous_column = candidates[candidate_index]
        if previous_column >= block_begin:
            for lower_index in range(lower_offsets[previous_column], lower_offsets[previous_column + 1]):
                row = lower_indices[lower_index]
                position = row_positions[row]
                if block_begin <= position < column and candidate_marks[position] != stamp:
                    candidate_marks[position] = stamp
                    candidates[candidate_count] = position
                    candidate_count += 1
                else:
                    pass
        else:
            pass
        candidate_index += 1
    _sort_pattern_slice(candidates, 0, candidate_count)
    return candidate_count


@numba.njit(cache=True)
def _tiny_dense_pattern(order: int, indptr: np.ndarray, indices: np.ndarray) -> bool:
    """Recognize CLU's complete order-one-through-three CSC fast path.

    :param order: Matrix order.
    :param indptr: CSC column pointers.
    :param indices: CSC row indices.
    :return: Whether every column has all rows in ascending order.
    """
    column: int = 0
    row: int = 0
    if order < 1 or order > 3 or indices.size != order * order:
        return False
    else:
        pass
    for column in range(order + 1):
        if indptr[column] != column * order:
            return False
        else:
            pass
    for column in range(order):
        for row in range(order):
            if indices[column * order + row] != row:
                return False
            else:
                pass
    return True


@numba.njit(cache=True)
def _factorize_tiny(values: np.ndarray, order: int, tolerance: float, replay: bool,
                    factors: np.ndarray, scales: np.ndarray, rows: np.ndarray) -> None:
    """Port CLU's inline complete tiny LU, preserving rows during replay.

    :param values: Canonical full CSC values.
    :param order: Matrix order from one to three.
    :param tolerance: Relative pivot threshold.
    :param replay: Keep the saved pivot permutation.
    :param factors: Column-major LU storage modified in place.
    :param scales: Row maxima modified in place.
    :param rows: Pivot-position to original-row map modified on first factorization.
    :return: Nothing.
    """
    row: int = 0
    column: int = 0
    next_column: int = 0
    pivot: int = 0
    preferred: int = 0
    maximum: float = 0.0
    magnitude: float = 0.0
    diagonal: float = 0.0
    temporary: float = 0.0
    for row in range(order):
        scales[row] = 0.0
        for column in range(order):
            scales[row] = max(scales[row], abs(values[column * order + row]))
        if scales[row] == 0.0:
            scales[row] = 1.0
        else:
            pass
        if not replay:
            rows[row] = row
        else:
            pass
    for column in range(order):
        for row in range(order):
            factors[column * order + row] = values[column * order + rows[row]] / scales[rows[row]]
    for column in range(order):
        if not replay:
            pivot = column
            preferred = column
            maximum = 0.0
            for row in range(column, order):
                magnitude = abs(factors[column * order + row])
                if magnitude > maximum:
                    maximum = magnitude
                    pivot = row
                else:
                    pass
                if rows[row] == column:
                    preferred = row
                else:
                    pass
            if factors[column * order + preferred] != 0.0 and abs(factors[column * order + preferred]) >= tolerance * maximum:
                pivot = preferred
            else:
                pass
            if pivot != column:
                temporary = rows[pivot]
                rows[pivot] = rows[column]
                rows[column] = int(temporary)
                for next_column in range(order):
                    temporary = factors[next_column * order + pivot]
                    factors[next_column * order + pivot] = factors[next_column * order + column]
                    factors[next_column * order + column] = temporary
            else:
                pass
        else:
            pass
        diagonal = factors[column * order + column]
        if not np.isfinite(diagonal) or diagonal == 0.0:
            raise np.linalg.LinAlgError("tiny CLU pivot failed")
        else:
            pass
        for row in range(column + 1, order):
            factors[column * order + row] /= diagonal
            if not np.isfinite(factors[column * order + row]):
                raise FloatingPointError("non-finite tiny L factor")
            else:
                pass
            for next_column in range(column + 1, order):
                factors[next_column * order + row] -= factors[column * order + row] * factors[next_column * order + column]
                if not np.isfinite(factors[next_column * order + row]):
                    raise FloatingPointError("non-finite tiny U factor")
                else:
                    pass


@numba.njit(cache=True)
def _solve_tiny(factors: np.ndarray, scales: np.ndarray, rows: np.ndarray,
                rhs: np.ndarray) -> np.ndarray:
    """Port CLU's tiny pivoted triangular solve.

    :param factors: Column-major inline LU factors.
    :param scales: Original row maxima.
    :param rows: Original rows in pivot order.
    :param rhs: Original right-hand side.
    :return: Solution vector.
    """
    order: int = rhs.size
    work: np.ndarray = np.empty(order, dtype=np.float64)
    row: int = 0
    column: int = 0
    next_column: int = 0
    for row in range(order):
        work[row] = rhs[rows[row]] / scales[rows[row]]
    for column in range(order):
        for row in range(column + 1, order):
            work[row] -= factors[column * order + row] * work[column]
    for column in range(order - 1, -1, -1):
        for next_column in range(column + 1, order):
            work[column] -= factors[next_column * order + column] * work[next_column]
        work[column] /= factors[column * order + column]
    return work


@numba.njit(cache=True)
def _factorize_diagonal(values: np.ndarray, scales: np.ndarray,
                        scale_reciprocals: np.ndarray, diagonal: np.ndarray,
                        diagonal_reciprocals: np.ndarray,
                        solve_rhs_reciprocals: np.ndarray) -> bool:
    """Port CLU's canonical one-entry-per-column diagonal kernel.

    :param values: Canonical CSC diagonal entries.
    :param scales: Destination row scales.
    :param scale_reciprocals: Destination safe reciprocal scales.
    :param diagonal: Destination scaled U diagonal.
    :param diagonal_reciprocals: Destination safe U reciprocals.
    :param solve_rhs_reciprocals: Destination RHS multipliers or scale reciprocals.
    :return: Whether a direct multiplication solve is safe for all rows.
    """
    order: int = values.size
    column: int = 0
    value: float = 0.0
    scale: float = 0.0
    reciprocal_scale: float = 0.0
    pivot: float = 0.0
    pivot_reciprocal: float = 0.0
    all_safe: bool = True
    for column in range(order):
        value = values[column]
        scale = 1.0 if value == 0.0 else abs(value)
        reciprocal_scale = _safe_reciprocal(scale)
        scales[column] = scale
        scale_reciprocals[column] = reciprocal_scale
        pivot = value * reciprocal_scale if reciprocal_scale != 0.0 else value / scale
        if not np.isfinite(pivot) or pivot == 0.0:
            raise np.linalg.LinAlgError("diagonal CLU pivot failed")
        else:
            pass
        pivot_reciprocal = _safe_reciprocal(pivot)
        diagonal[column] = pivot
        diagonal_reciprocals[column] = pivot_reciprocal
        solve_rhs_reciprocals[column] = reciprocal_scale
        all_safe = all_safe and reciprocal_scale != 0.0 and pivot_reciprocal != 0.0
    if all_safe:
        for column in range(order):
            solve_rhs_reciprocals[column] *= diagonal_reciprocals[column]
    else:
        pass
    return all_safe


@numba.njit(cache=True)
def _solve_diagonal(rhs: np.ndarray, scales: np.ndarray,
                    scale_reciprocals: np.ndarray, diagonal: np.ndarray,
                    diagonal_reciprocals: np.ndarray,
                    solve_rhs_reciprocals: np.ndarray, all_safe: bool) -> np.ndarray:
    """Solve CLU's canonical diagonal factors.

    :param rhs: Original right-hand side.
    :param scales: Original row scales.
    :param scale_reciprocals: Safe reciprocal scales.
    :param diagonal: Scaled diagonal factors.
    :param diagonal_reciprocals: Safe diagonal reciprocals.
    :param solve_rhs_reciprocals: Combined direct multipliers when safe.
    :param all_safe: Whether every combined multiplier is valid.
    :return: Solution vector.
    """
    result: np.ndarray = np.empty(rhs.size, dtype=np.float64)
    row: int = 0
    value: float = 0.0
    for row in range(rhs.size):
        if all_safe:
            result[row] = rhs[row] * solve_rhs_reciprocals[row]
        else:
            value = rhs[row] * scale_reciprocals[row] if scale_reciprocals[row] != 0.0 else rhs[row] / scales[row]
            result[row] = value * diagonal_reciprocals[row] if diagonal_reciprocals[row] != 0.0 else value / diagonal[row]
    return result


@numba.njit(cache=True)
def _find_augmenting_path(indptr: np.ndarray, indices: np.ndarray, column: int,
                          row_match: np.ndarray, seen_rows: np.ndarray,
                          cheap_cursors: np.ndarray, column_match: np.ndarray,
                          stack_columns: np.ndarray, stack_entries: np.ndarray) -> bool:
    """Port CLU's iterative matching DFS for one input column.

    :param indptr: CSC column offsets.
    :param indices: CSC row indices.
    :param column: Root column seeking a row.
    :param row_match: Current row-to-column matching.
    :param seen_rows: Root-column visit stamps.
    :param cheap_cursors: Next free-row search offsets.
    :param column_match: Current column-to-row matching.
    :param stack_columns: Suspended DFS columns.
    :param stack_entries: Continuation offsets.
    :return: Whether the root received a row.
    """
    depth: int = 0
    active_column: int = column
    entry: int = indptr[active_column]
    end: int = indptr[active_column + 1]
    cheap_entry: int = 0
    free_row: int = -1
    row: int = 0
    previous_column: int = 0
    matched_row: int = 0
    while depth >= 0:
        cheap_entry = cheap_cursors[active_column]
        free_row = -1
        while cheap_entry < end and free_row < 0:
            row = indices[cheap_entry]
            cheap_entry += 1
            if row_match[row] < 0:
                free_row = row
            else:
                pass
        cheap_cursors[active_column] = cheap_entry
        if free_row >= 0:
            row_match[free_row] = active_column
            column_match[active_column] = free_row
            while depth > 0:
                depth -= 1
                matched_row = indices[stack_entries[depth] - 1]
                row_match[matched_row] = stack_columns[depth]
                column_match[stack_columns[depth]] = matched_row
            return True
        else:
            pass
        while entry < end and seen_rows[indices[entry]] == column:
            entry += 1
        if entry == end:
            depth -= 1
            if depth >= 0:
                active_column = stack_columns[depth]
                entry = stack_entries[depth]
                end = indptr[active_column + 1]
            else:
                pass
        else:
            row = indices[entry]
            seen_rows[row] = column
            previous_column = row_match[row]
            stack_columns[depth] = active_column
            stack_entries[depth] = entry + 1
            depth += 1
            active_column = previous_column
            entry = indptr[active_column]
            end = indptr[active_column + 1]
    return False


@numba.njit(cache=True)
def _compute_matching(indptr: np.ndarray, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray, bool]:
    """Port CLU's full structural bipartite matching.

    :param indptr: CSC column offsets.
    :param indices: CSC row indices.
    :return: Row matches, column matches, and full-rank flag.
    """
    order: int = indptr.size - 1
    row_match: np.ndarray = np.full(order, -1, dtype=np.int32)
    column_match: np.ndarray = np.full(order, -1, dtype=np.int32)
    seen_rows: np.ndarray = np.full(order, -1, dtype=np.int32)
    cheap_cursors: np.ndarray = indptr[:-1].copy()
    stack_columns: np.ndarray = np.empty(order, dtype=np.int32)
    stack_entries: np.ndarray = np.empty(order, dtype=np.int32)
    matched_columns: int = 0
    column: int = 0
    for column in range(order):
        if _find_augmenting_path(indptr, indices, column, row_match, seen_rows,
                                 cheap_cursors, column_match, stack_columns, stack_entries):
            matched_columns += 1
        else:
            pass
    return row_match, column_match, matched_columns == order


@numba.njit(cache=True)
def _compute_btf_blocks(indptr: np.ndarray, indices: np.ndarray,
                        row_match: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Port CLU's iterative Tarjan decomposition into upper triangular blocks.

    :param indptr: CSC column offsets.
    :param indices: CSC row indices.
    :param row_match: Row-to-column structural matching.
    :return: Flat block vertices and offsets.
    """
    order: int = indptr.size - 1
    component_sizes: np.ndarray = np.empty(order, dtype=np.int32)
    visit_index: np.ndarray = np.full(order, -1, dtype=np.int32)
    low_link: np.ndarray = np.empty(order, dtype=np.int32)
    component: np.ndarray = np.full(order, -1, dtype=np.int32)
    component_stack: np.ndarray = np.empty(order, dtype=np.int32)
    dfs_vertices: np.ndarray = np.empty(order, dtype=np.int32)
    dfs_next_entries: np.ndarray = np.empty(order, dtype=np.int32)
    component_count: int = 0
    component_stack_count: int = 0
    dfs_stack_count: int = 0
    next_visit_index: int = 0
    root: int = 0
    top_index: int = 0
    vertex: int = 0
    edge_end: int = 0
    entry: int = 0
    neighbor: int = 0
    member: int = 0
    count: int = 0
    parent: int = 0
    for root in range(order):
        if visit_index[root] < 0:
            visit_index[root] = next_visit_index
            low_link[root] = next_visit_index
            next_visit_index += 1
            component_stack[component_stack_count] = root
            component_stack_count += 1
            dfs_vertices[dfs_stack_count] = root
            dfs_next_entries[dfs_stack_count] = indptr[root]
            dfs_stack_count += 1
            while dfs_stack_count > 0:
                top_index = dfs_stack_count - 1
                vertex = dfs_vertices[top_index]
                edge_end = indptr[vertex + 1]
                entry = dfs_next_entries[top_index]
                if entry < edge_end:
                    dfs_next_entries[top_index] = entry + 1
                    neighbor = row_match[indices[entry]]
                    if neighbor >= 0 and neighbor != vertex:
                        if visit_index[neighbor] < 0:
                            visit_index[neighbor] = next_visit_index
                            low_link[neighbor] = next_visit_index
                            next_visit_index += 1
                            component_stack[component_stack_count] = neighbor
                            component_stack_count += 1
                            dfs_vertices[dfs_stack_count] = neighbor
                            dfs_next_entries[dfs_stack_count] = indptr[neighbor]
                            dfs_stack_count += 1
                        elif component[neighbor] < 0:
                            low_link[vertex] = min(low_link[vertex], visit_index[neighbor])
                        else:
                            pass
                    else:
                        pass
                else:
                    dfs_stack_count -= 1
                    if low_link[vertex] == visit_index[vertex]:
                        count = 0
                        member = -1
                        while member != vertex:
                            component_stack_count -= 1
                            member = component_stack[component_stack_count]
                            component[member] = component_count
                            count += 1
                        component_sizes[component_count] = count
                        component_count += 1
                    else:
                        pass
                    if dfs_stack_count > 0:
                        parent = dfs_vertices[dfs_stack_count - 1]
                        low_link[parent] = min(low_link[parent], low_link[vertex])
                    else:
                        pass
        else:
            pass
    if component_stack_count != 0 or next_visit_index != order:
        raise ValueError("invalid BTF component decomposition")
    else:
        pass
    block_offsets: np.ndarray = np.empty(component_count + 1, dtype=np.int32)
    block_vertices: np.ndarray = np.empty(order, dtype=np.int32)
    offset: int = 0
    block_index: int = 0
    size: int = 0
    for block_index in range(component_count):
        block_offsets[block_index] = offset
        size = component_sizes[block_index]
        component_sizes[block_index] = offset
        offset += size
    block_offsets[component_count] = offset
    for vertex in range(order):
        block_index = component[vertex]
        if block_index < 0:
            raise ValueError("unassigned BTF vertex")
        else:
            block_vertices[component_sizes[block_index]] = vertex
            component_sizes[block_index] += 1
    return block_vertices, block_offsets


@numba.njit(cache=True)
def _compute_symmetric_btf_blocks(indptr: np.ndarray, indices: np.ndarray,
                                  row_match: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Port CLU's connected-component BTF path for symmetric structure.

    :param indptr: CSC column offsets.
    :param indices: CSC row indices.
    :param row_match: Identity or explicit structural row matching.
    :return: Flat block vertices and offsets.
    """
    order: int = indptr.size - 1
    component: np.ndarray = np.full(order, -1, dtype=np.int32)
    component_sizes: np.ndarray = np.empty(order, dtype=np.int32)
    stack: np.ndarray = np.empty(order, dtype=np.int32)
    component_count: int = 0
    root: int = 0
    count: int = 0
    stack_count: int = 0
    vertex: int = 0
    entry: int = 0
    neighbor: int = 0
    block: int = 0
    offset: int = 0
    size: int = 0
    for root in range(order):
        if component[root] < 0:
            count = 0
            component[root] = component_count
            stack_count = 1
            stack[0] = root
            while stack_count > 0:
                stack_count -= 1
                vertex = stack[stack_count]
                count += 1
                for entry in range(indptr[vertex], indptr[vertex + 1]):
                    neighbor = row_match[indices[entry]] if row_match.size > 0 else indices[entry]
                    if neighbor >= 0 and component[neighbor] < 0:
                        component[neighbor] = component_count
                        stack[stack_count] = neighbor
                        stack_count += 1
                    else:
                        pass
            component_sizes[component_count] = count
            component_count += 1
        else:
            pass
    block_offsets: np.ndarray = np.empty(component_count + 1, dtype=np.int32)
    block_vertices: np.ndarray = np.empty(order, dtype=np.int32)
    for block in range(component_count):
        block_offsets[block] = offset
        size = component_sizes[block]
        component_sizes[block] = offset
        offset += size
    block_offsets[component_count] = offset
    for vertex in range(order):
        block = component[vertex]
        if block < 0 or block >= component_count:
            raise ValueError("invalid symmetric BTF component")
        else:
            block_vertices[component_sizes[block]] = vertex
            component_sizes[block] += 1
    return block_vertices, block_offsets


@numba.njit(cache=True)
def _count_set_bits(value: np.uint64) -> int:
    """Count bits with CLU's portable integer loop.

    :param value: Packed graph word.
    :return: Number of set bits.
    """
    count: int = 0
    while value != 0:
        value &= value - np.uint64(1)
        count += 1
    return count


@numba.njit(cache=True)
def _first_set_bit(value: np.uint64) -> int:
    """Find the lowest set bit of a nonzero graph word.

    :param value: Nonzero packed graph word.
    :return: Bit position.
    """
    bit_index: int = 0
    while (value & np.uint64(1)) == 0:
        value >>= np.uint64(1)
        bit_index += 1
    return bit_index


@numba.njit(cache=True)
def _minimum_degree_order_bitset(indptr: np.ndarray, indices: np.ndarray,
                                 vertices: np.ndarray, row_match: np.ndarray,
                                 local_index: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Port CLU's bitset minimum-degree elimination for one BTF block.

    :param indptr: CSC column offsets.
    :param indices: CSC row indices.
    :param vertices: Original column IDs in this block.
    :param row_match: Row-to-column matching.
    :param local_index: Reusable inverse block map, restored to minus one.
    :return: Fill-reducing order and exact filled lower counts.
    """
    block_size: int = vertices.size
    word_count: int = (block_size + 63) // 64
    adjacency: np.ndarray = np.zeros((block_size, word_count), dtype=np.uint64)
    degree: np.ndarray = np.zeros(block_size, dtype=np.int32)
    bucket_heads: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    bucket_previous: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    bucket_next: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    live_neighbors: np.ndarray = np.empty(block_size, dtype=np.int32)
    active: np.ndarray = np.ones(block_size, dtype=np.uint8)
    clique_ready: np.ndarray = np.zeros(block_size, dtype=np.uint8)
    result: np.ndarray = np.empty(block_size, dtype=np.int32)
    lower_counts: np.ndarray = np.empty(block_size, dtype=np.int32)
    neighbor_words: np.ndarray = np.zeros(word_count, dtype=np.uint64)
    nonzero_neighbor_words: np.ndarray = np.empty(word_count, dtype=np.int32)
    local_column: int = 0
    entry: int = 0
    matched_column: int = 0
    row_index: int = 0
    bit: np.uint64 = np.uint64(0)
    for local_column in range(block_size):
        local_index[vertices[local_column]] = local_column
    for local_column in range(block_size):
        for entry in range(indptr[vertices[local_column]], indptr[vertices[local_column] + 1]):
            matched_column = row_match[indices[entry]]
            row_index = local_index[matched_column] if matched_column >= 0 else local_index[indices[entry]]
            if row_index >= 0 and row_index != local_column:
                bit = np.uint64(1) << np.uint64(row_index & 63)
                if (adjacency[local_column, row_index // 64] & bit) == 0:
                    adjacency[local_column, row_index // 64] |= bit
                    adjacency[row_index, local_column // 64] |= np.uint64(1) << np.uint64(local_column & 63)
                    degree[local_column] += 1
                    degree[row_index] += 1
                else:
                    pass
            else:
                pass
    old_head: int = 0
    for local_column in range(block_size - 1, -1, -1):
        old_head = bucket_heads[degree[local_column]]
        bucket_next[local_column] = old_head
        if old_head >= 0:
            bucket_previous[old_head] = local_column
        else:
            pass
        bucket_heads[degree[local_column]] = local_column
    minimum_degree: int = 0
    step: int = 0
    selected: int = -1
    next_vertex: int = 0
    target_degree: int = 0
    neighbor_count: int = 0
    nonzero_word_count: int = 0
    word_index: int = 0
    word: np.uint64 = np.uint64(0)
    remaining: np.uint64 = np.uint64(0)
    neighbor: int = 0
    selected_bit: np.uint64 = np.uint64(0)
    selected_word: int = 0
    neighbor_index: int = 0
    new_degree: int = 0
    own_word: int = 0
    own_bit: np.uint64 = np.uint64(0)
    twin_candidate: bool = False
    expected: np.uint64 = np.uint64(0)
    actual: np.uint64 = np.uint64(0)
    fill_word: int = 0
    old_word: np.uint64 = np.uint64(0)
    clique_word: np.uint64 = np.uint64(0)
    additions: np.uint64 = np.uint64(0)
    merged: np.uint64 = np.uint64(0)
    previous: int = 0
    selected_is_clique_ready: bool = False
    for step in range(block_size):
        selected = -1
        while selected < 0 and minimum_degree < block_size:
            selected = bucket_heads[minimum_degree]
            if selected < 0:
                minimum_degree += 1
            else:
                next_vertex = bucket_next[selected]
                bucket_heads[minimum_degree] = next_vertex
                if next_vertex >= 0:
                    bucket_previous[next_vertex] = -1
                else:
                    pass
                bucket_previous[selected] = -1
                bucket_next[selected] = -1
        if selected < 0:
            raise ValueError("minimum degree buckets are empty")
        else:
            pass
        selected_is_clique_ready = clique_ready[selected] != 0
        clique_ready[selected] = 0
        target_degree = degree[selected]
        neighbor_count = 0
        nonzero_word_count = 0
        for word_index in range(word_count):
            if neighbor_count < target_degree:
                word = adjacency[selected, word_index]
                if word != 0:
                    neighbor_words[word_index] = word
                    nonzero_neighbor_words[nonzero_word_count] = word_index
                    nonzero_word_count += 1
                    remaining = word
                    while remaining != 0:
                        neighbor = word_index * 64 + _first_set_bit(remaining)
                        if neighbor < block_size and active[neighbor] != 0:
                            live_neighbors[neighbor_count] = neighbor
                            neighbor_count += 1
                        else:
                            pass
                        remaining &= remaining - np.uint64(1)
                else:
                    pass
            else:
                pass
        selected_bit = np.uint64(1) << np.uint64(selected & 63)
        selected_word = selected // 64
        active[selected] = 0
        for neighbor_index in range(neighbor_count):
            neighbor = live_neighbors[neighbor_index]
            adjacency[neighbor, selected_word] &= ~selected_bit
            new_degree = degree[neighbor] - 1
            own_word = neighbor // 64
            own_bit = np.uint64(1) << np.uint64(neighbor & 63)
            twin_candidate = not selected_is_clique_ready and degree[neighbor] == degree[selected]
            if twin_candidate:
                for word_index in range(nonzero_word_count):
                    fill_word = nonzero_neighbor_words[word_index]
                    expected = neighbor_words[fill_word]
                    if fill_word == own_word:
                        expected &= ~own_bit
                    else:
                        pass
                    actual = adjacency[neighbor, fill_word]
                    if (expected & ~actual) != 0:
                        twin_candidate = False
                    else:
                        pass
            else:
                pass
            if selected_is_clique_ready or twin_candidate:
                if twin_candidate:
                    clique_ready[neighbor] = 1
                else:
                    pass
            else:
                for word_index in range(nonzero_word_count):
                    fill_word = nonzero_neighbor_words[word_index]
                    old_word = adjacency[neighbor, fill_word]
                    clique_word = neighbor_words[fill_word]
                    additions = clique_word & ~old_word
                    merged = old_word | clique_word
                    if fill_word == own_word:
                        additions &= ~own_bit
                        merged &= ~own_bit
                    else:
                        pass
                    adjacency[neighbor, fill_word] = merged
                    new_degree += _count_set_bits(additions)
            previous = bucket_previous[neighbor]
            next_vertex = bucket_next[neighbor]
            if previous >= 0:
                bucket_next[previous] = next_vertex
            else:
                bucket_heads[degree[neighbor]] = next_vertex
            if next_vertex >= 0:
                bucket_previous[next_vertex] = previous
            else:
                pass
            degree[neighbor] = new_degree
            old_head = bucket_heads[new_degree]
            bucket_previous[neighbor] = -1
            bucket_next[neighbor] = old_head
            if old_head >= 0:
                bucket_previous[old_head] = neighbor
            else:
                pass
            bucket_heads[new_degree] = neighbor
            minimum_degree = min(minimum_degree, new_degree)
        result[step] = vertices[selected]
        lower_counts[step] = neighbor_count
    for local_column in range(block_size):
        local_index[vertices[local_column]] = -1
    return result, lower_counts


@numba.njit(cache=True)
def _build_ordering_adjacency(indptr: np.ndarray, indices: np.ndarray,
                              vertices: np.ndarray, row_match: np.ndarray,
                              local_index: np.ndarray) -> tuple:
    """Build CLU's deduplicated undirected sparse ordering graph.

    :param indptr: CSC column offsets.
    :param indices: CSC row indices.
    :param vertices: Original columns in one BTF block.
    :param row_match: Input-row to matched-column map.
    :param local_index: Reusable original-column to block-local map.
    :return: Flat adjacency, offsets, live counts, and edge totals.
    """
    block_size: int = vertices.size
    adjacency: np.ndarray
    adjacency_offsets: np.ndarray = np.empty(block_size + 1, dtype=np.int32)
    local_column: int = 0
    entry: int = 0
    row: int = 0
    matched_column: int = 0
    row_index: int = 0
    existing_index: int = 0
    adjacency_entries: int = 0
    adjacency_marks: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    adjacency_capacity: np.ndarray = np.zeros(block_size, dtype=np.int32)
    adjacency_counts: np.ndarray = np.zeros(block_size, dtype=np.int32)
    for local_column in range(block_size):
        local_index[vertices[local_column]] = local_column
    for local_column in range(block_size):
        for entry in range(indptr[vertices[local_column]], indptr[vertices[local_column] + 1]):
            row = indices[entry]
            matched_column = row_match[row] if row_match.size > 0 else row
            row_index = local_index[matched_column] if matched_column >= 0 else local_index[row]
            if row_index >= 0 and row_index != local_column:
                adjacency_capacity[local_column] += 1
                adjacency_capacity[row_index] += 1
            else:
                pass
    adjacency_offsets[0] = 0
    for local_column in range(block_size):
        adjacency_offsets[local_column + 1] = adjacency_offsets[local_column] + adjacency_capacity[local_column]
    adjacency = np.empty(adjacency_offsets[block_size], dtype=np.int32)
    for local_column in range(block_size):
        for existing_index in range(adjacency_counts[local_column]):
            adjacency_marks[adjacency[adjacency_offsets[local_column] + existing_index]] = local_column
        for entry in range(indptr[vertices[local_column]], indptr[vertices[local_column] + 1]):
            row = indices[entry]
            matched_column = row_match[row] if row_match.size > 0 else row
            row_index = local_index[matched_column] if matched_column >= 0 else local_index[row]
            if row_index >= 0 and row_index != local_column and adjacency_marks[row_index] != local_column:
                adjacency_marks[row_index] = local_column
                adjacency[adjacency_offsets[local_column] + adjacency_counts[local_column]] = row_index
                adjacency_counts[local_column] += 1
                adjacency[adjacency_offsets[row_index] + adjacency_counts[row_index]] = local_column
                adjacency_counts[row_index] += 1
                adjacency_entries += 2
            else:
                pass
    estimated_entries: int = 0
    for local_column in range(block_size):
        estimated_entries += adjacency_capacity[local_column]
    return adjacency, adjacency_offsets, adjacency_counts, adjacency_entries, estimated_entries


@numba.njit(cache=True)
def _refresh_degree_bucket(neighbor: int, adjacency_counts: np.ndarray,
                           degree: np.ndarray, bucket_heads: np.ndarray,
                           bucket_previous: np.ndarray, bucket_next: np.ndarray,
                           minimum_degree: int) -> int:
    """Move one changed sparse-ordering vertex to its current degree bucket.

    :param neighbor: Vertex whose live adjacency changed.
    :param adjacency_counts: Current live neighbor counts.
    :param degree: Previous bucket degree per vertex.
    :param bucket_heads: First vertex in each degree bucket.
    :param bucket_previous: Previous vertex in its bucket.
    :param bucket_next: Next vertex in its bucket.
    :param minimum_degree: Current minimum nonempty bucket estimate.
    :return: Updated minimum degree estimate.
    """
    old_degree: int = degree[neighbor]
    previous: int = bucket_previous[neighbor]
    next_vertex: int = bucket_next[neighbor]
    if previous >= 0:
        bucket_next[previous] = next_vertex
    else:
        bucket_heads[old_degree] = next_vertex
    if next_vertex >= 0:
        bucket_previous[next_vertex] = previous
    else:
        pass
    neighbor_degree: int = adjacency_counts[neighbor]
    degree[neighbor] = neighbor_degree
    new_head: int = bucket_heads[neighbor_degree]
    bucket_previous[neighbor] = -1
    bucket_next[neighbor] = new_head
    if new_head >= 0:
        bucket_previous[new_head] = neighbor
    else:
        pass
    bucket_heads[neighbor_degree] = neighbor
    return min(minimum_degree, neighbor_degree)


@numba.njit(cache=True)
def _find_representative(vertex: int, parent: np.ndarray) -> int:
    """Port CLU's weighted-twin representative lookup with path compression.

    :param vertex: Local ordering vertex.
    :param parent: Quotient representative forest.
    :return: Current representative vertex.
    """
    previous_parent: int = 0
    while parent[vertex] != vertex:
        previous_parent = parent[vertex]
        parent[vertex] = parent[previous_parent]
        vertex = parent[vertex]
    return vertex


@numba.njit(cache=True)
def _quotient_minimum_degree_order(vertices: np.ndarray, adjacency: np.ndarray,
                                   adjacency_offsets: np.ndarray,
                                   adjacency_counts: np.ndarray,
                                   local_index: np.ndarray,
                                   input_adjacency_entries: int,
                                   emitted_rows: np.ndarray, emitted_count: int,
                                   emit_complete: bool) -> tuple:
    """Order a sparse block with CLU's quotient cliques and weighted twins.

    :param vertices: Original columns represented by graph vertices.
    :param adjacency: Flat unique undirected input graph.
    :param adjacency_offsets: Per-vertex graph buffer boundaries.
    :param adjacency_counts: Live edge counts for adjacency rows.
    :param local_index: Original-to-local scratch cleared on return.
    :param input_adjacency_entries: Directed adjacency entry count.
    :param emitted_rows: Bounded original-row output for filled neighborhoods.
    :param emitted_count: Number of filled output entries already used.
    :param emit_complete: Whether previous emission remains within the bound.
    :return: Elimination order, lower counts, output length, and completion flag.
    """
    block_size: int = vertices.size
    degree: np.ndarray = adjacency_counts.copy()
    bucket_heads: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    bucket_previous: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    bucket_next: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    element_size: np.ndarray = np.zeros(block_size, dtype=np.int32)
    outside_count: np.ndarray = np.zeros(block_size, dtype=np.int32)
    outside_stamp: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    neighbor_stamp: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    edge_stamp: np.ndarray = np.zeros(block_size, dtype=np.int32)
    parent: np.ndarray = np.arange(block_size, dtype=np.int32)
    weight: np.ndarray = np.ones(block_size, dtype=np.int32)
    group_next: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    group_tail: np.ndarray = np.arange(block_size, dtype=np.int32)
    neighbors: np.ndarray = np.empty(block_size, dtype=np.int32)
    membership_counts: np.ndarray = np.zeros(block_size, dtype=np.int32)
    membership_offsets: np.ndarray = np.empty(block_size + 1, dtype=np.int32)
    membership_offsets[0] = 0
    for vertex in range(block_size):
        membership_offsets[vertex + 1] = membership_offsets[vertex] + adjacency_counts[vertex]
    # Input graph degree bounds incident quotient elements, as in native CLU.
    memberships: np.ndarray = np.empty(input_adjacency_entries, dtype=np.int32)
    element_offsets: np.ndarray = np.zeros(block_size, dtype=np.int32)
    element_vertex_counts: np.ndarray = np.zeros(block_size, dtype=np.int32)
    element_vertices: np.ndarray = np.empty(max(1, input_adjacency_entries + block_size * 2), dtype=np.int32)
    active: np.ndarray = np.ones(block_size, dtype=np.uint8)
    element_active: np.ndarray = np.zeros(block_size, dtype=np.uint8)
    result: np.ndarray = np.empty(block_size, dtype=np.int32)
    lower_counts: np.ndarray = np.empty(block_size, dtype=np.int32)
    hash_bucket_count: int = 1
    while hash_bucket_count < block_size:
        hash_bucket_count *= 2
    hash_heads: np.ndarray = np.empty(hash_bucket_count, dtype=np.int32)
    hash_stamps: np.ndarray = np.full(hash_bucket_count, -1, dtype=np.int32)
    hash_next: np.ndarray = np.empty(block_size, dtype=np.int32)
    fingerprints: np.ndarray = np.empty(block_size, dtype=np.uint64)
    low_index_ties: bool = input_adjacency_entries <= block_size * 10
    vertex: int = 0
    old_head: int = 0
    if low_index_ties:
        for vertex in range(block_size - 1, -1, -1):
            old_head = bucket_heads[degree[vertex]]
            bucket_next[vertex] = old_head
            if old_head >= 0:
                bucket_previous[old_head] = vertex
            else:
                pass
            bucket_heads[degree[vertex]] = vertex
    else:
        for vertex in range(block_size):
            old_head = bucket_heads[degree[vertex]]
            bucket_next[vertex] = old_head
            if old_head >= 0:
                bucket_previous[old_head] = vertex
            else:
                pass
            bucket_heads[degree[vertex]] = vertex
    result_count: int = 0
    minimum_degree: int = 0
    step: int = 0
    selected: int = 0
    next_selected: int = 0
    group_begin: int = 0
    group_vertex: int = 0
    neighbor_count: int = 0
    original: int = 0
    representative: int = 0
    entry: int = 0
    element: int = 0
    element_index: int = 0
    element_end: int = 0
    neighbor_index: int = 0
    clique_size: int = 0
    member_index: int = 0
    used: int = 0
    edge_token: int = 0
    edge_generation: int = 0
    other: int = 0
    previous: int = 0
    next_vertex: int = 0
    same_twin: bool = False
    candidate: int = 0
    hash_bucket: int = 0
    fingerprint: np.uint64 = np.uint64(0)
    edge_fingerprint: np.uint64 = np.uint64(0)
    element_fingerprint: np.uint64 = np.uint64(0)
    estimate: int = 0
    element_vertices_count: int = 0
    group_size: int = 0
    required: int = 0
    output_position: int = 0
    member: int = 0
    neighbor_member: int = 0
    while result_count < block_size:
        while minimum_degree < block_size and bucket_heads[minimum_degree] < 0:
            minimum_degree += 1
        if minimum_degree >= block_size:
            raise ValueError("quotient degree buckets are empty")
        else:
            selected = bucket_heads[minimum_degree]
        next_selected = bucket_next[selected]
        bucket_heads[minimum_degree] = next_selected
        if next_selected >= 0:
            bucket_previous[next_selected] = -1
        else:
            pass
        active[selected] = 0
        group_begin = result_count
        group_vertex = selected
        while group_vertex >= 0:
            result[result_count] = vertices[group_vertex]
            result_count += 1
            group_vertex = group_next[group_vertex]
        if minimum_degree == 0:
            for member_index in range(group_begin, result_count):
                lower_counts[member_index] = result_count - 1 - member_index
            if emit_complete:
                group_size = result_count - group_begin
                required = group_size * (group_size - 1) // 2
                if required <= emitted_rows.size - emitted_count:
                    output_position = emitted_count
                    for member in range(group_begin, result_count):
                        for neighbor_member in range(member + 1, result_count):
                            emitted_rows[output_position] = result[neighbor_member]
                            output_position += 1
                    emitted_count = output_position
                else:
                    emit_complete = False
            else:
                pass
        else:
            neighbor_count = 0
            neighbor_stamp[selected] = step
            for entry in range(adjacency_counts[selected]):
                original = adjacency[adjacency_offsets[selected] + entry]
                vertex = _find_representative(original, parent)
                if active[vertex] != 0 and neighbor_stamp[vertex] != step:
                    neighbor_stamp[vertex] = step
                    neighbors[neighbor_count] = vertex
                    neighbor_count += 1
                else:
                    pass
            for member_index in range(membership_counts[selected]):
                element = memberships[membership_offsets[selected] + member_index]
                if element_active[element] != 0:
                    element_end = element_offsets[element] + element_vertex_counts[element]
                    for element_index in range(element_offsets[element], element_end):
                        original = element_vertices[element_index]
                        vertex = _find_representative(original, parent)
                        if active[vertex] != 0 and neighbor_stamp[vertex] != step:
                            neighbor_stamp[vertex] = step
                            neighbors[neighbor_count] = vertex
                            neighbor_count += 1
                        else:
                            pass
                    element_active[element] = 0
                else:
                    pass
            clique_size = 0
            for neighbor_index in range(neighbor_count):
                vertex = neighbors[neighbor_index]
                clique_size += weight[vertex]
                for member_index in range(membership_counts[vertex]):
                    element = memberships[membership_offsets[vertex] + member_index]
                    if element_active[element] != 0:
                        if outside_stamp[element] != step:
                            outside_stamp[element] = step
                            outside_count[element] = element_size[element]
                        else:
                            pass
                        outside_count[element] -= weight[vertex]
                    else:
                        pass
            for member_index in range(group_begin, result_count):
                lower_counts[member_index] = clique_size + result_count - 1 - member_index
            if emit_complete:
                group_size = result_count - group_begin
                required = group_size * clique_size + group_size * (group_size - 1) // 2
                if required <= emitted_rows.size - emitted_count:
                    output_position = emitted_count
                    for member in range(group_begin, result_count):
                        for neighbor_index in range(neighbor_count):
                            neighbor_member = neighbors[neighbor_index]
                            while neighbor_member >= 0:
                                emitted_rows[output_position] = vertices[neighbor_member]
                                output_position += 1
                                neighbor_member = group_next[neighbor_member]
                        for neighbor_member in range(member + 1, result_count):
                            emitted_rows[output_position] = result[neighbor_member]
                            output_position += 1
                    emitted_count = output_position
                else:
                    emit_complete = False
            else:
                pass
            element_offsets[selected] = element_vertices_count
            element_vertex_counts[selected] = neighbor_count
            if neighbor_count > 1:
                if element_vertices_count + neighbor_count > element_vertices.size:
                    expanded: np.ndarray = np.empty(max(element_vertices.size * 2, element_vertices_count + neighbor_count), dtype=np.int32)
                    expanded[:element_vertices_count] = element_vertices[:element_vertices_count]
                    element_vertices = expanded
                else:
                    pass
                element_vertices[element_vertices_count:element_vertices_count + neighbor_count] = neighbors[:neighbor_count]
                element_vertices_count += neighbor_count
            else:
                pass
            element_size[selected] = clique_size
            element_active[selected] = 1 if neighbor_count > 1 else 0
            for neighbor_index in range(neighbor_count):
                vertex = neighbors[neighbor_index]
                previous = bucket_previous[vertex]
                next_vertex = bucket_next[vertex]
                if previous >= 0:
                    bucket_next[previous] = next_vertex
                else:
                    bucket_heads[degree[vertex]] = next_vertex
                if next_vertex >= 0:
                    bucket_previous[next_vertex] = previous
                else:
                    pass
                edge_generation += 1
                edge_token = edge_generation
                used = 0
                edge_fingerprint = np.uint64(0)
                for entry in range(adjacency_counts[vertex]):
                    other = _find_representative(adjacency[adjacency_offsets[vertex] + entry], parent)
                    if active[other] != 0 and neighbor_stamp[other] != step and edge_stamp[other] != edge_token:
                        edge_stamp[other] = edge_token
                        adjacency[adjacency_offsets[vertex] + used] = other
                        edge_fingerprint += np.uint64(other + 1) * np.uint64(0x9e3779b97f4a7c15)
                        used += 1
                    else:
                        pass
                adjacency_counts[vertex] = used
                used = 0
                element_fingerprint = np.uint64(0)
                for member_index in range(membership_counts[vertex]):
                    element = memberships[membership_offsets[vertex] + member_index]
                    if element_active[element] != 0 and outside_count[element] > 0:
                        memberships[membership_offsets[vertex] + used] = element
                        element_fingerprint += np.uint64(element + 1) * np.uint64(0xd6e8feb86659fd93)
                        used += 1
                    else:
                        element_active[element] = 0
                membership_counts[vertex] = used
                fingerprint = np.uint64(adjacency_counts[vertex]) * np.uint64(1099511628211)
                fingerprint += edge_fingerprint
                fingerprint = (fingerprint * np.uint64(1099511628211)) ^ np.uint64(0xffffffff)
                fingerprint += element_fingerprint
                hash_bucket = int(fingerprint & np.uint64(hash_bucket_count - 1))
                if hash_stamps[hash_bucket] != step:
                    hash_stamps[hash_bucket] = step
                    hash_heads[hash_bucket] = -1
                else:
                    pass
                representative = -1
                candidate = hash_heads[hash_bucket]
                while candidate >= 0:
                    same_twin = fingerprints[candidate] == fingerprint and adjacency_counts[vertex] == adjacency_counts[candidate] and membership_counts[vertex] == membership_counts[candidate]
                    if same_twin:
                        for member_index in range(membership_counts[vertex]):
                            if memberships[membership_offsets[vertex] + member_index] != memberships[membership_offsets[candidate] + member_index]:
                                same_twin = False
                                break
                            else:
                                pass
                    else:
                        pass
                    if same_twin:
                        for entry in range(adjacency_counts[candidate]):
                            if edge_stamp[adjacency[adjacency_offsets[candidate] + entry]] != edge_token:
                                same_twin = False
                                break
                            else:
                                pass
                    else:
                        pass
                    if same_twin:
                        representative = candidate
                        break
                    else:
                        candidate = hash_next[candidate]
                if representative >= 0:
                    weight[representative] += weight[vertex]
                    parent[vertex] = representative
                    active[vertex] = 0
                    group_next[group_tail[representative]] = vertex
                    group_tail[representative] = group_tail[vertex]
                else:
                    fingerprints[vertex] = fingerprint
                    hash_next[vertex] = hash_heads[hash_bucket]
                    hash_heads[hash_bucket] = vertex
            for neighbor_index in range(neighbor_count - 1, -1, -1):
                vertex = neighbors[neighbor_index]
                if active[vertex] != 0:
                    estimate = clique_size - weight[vertex]
                    for entry in range(adjacency_counts[vertex]):
                        estimate += weight[adjacency[adjacency_offsets[vertex] + entry]]
                    for member_index in range(membership_counts[vertex]):
                        estimate += outside_count[memberships[membership_offsets[vertex] + member_index]]
                    if neighbor_count > 1:
                        if membership_counts[vertex] >= membership_offsets[vertex + 1] - membership_offsets[vertex]:
                            raise OverflowError("quotient membership capacity")
                        else:
                            pass
                        memberships[membership_offsets[vertex] + membership_counts[vertex]] = selected
                        membership_counts[vertex] += 1
                    else:
                        pass
                    estimate = min(estimate, block_size - result_count - weight[vertex])
                    if estimate < 0:
                        raise ValueError("negative quotient degree")
                    else:
                        pass
                    degree[vertex] = estimate
                    old_head = bucket_heads[estimate]
                    bucket_previous[vertex] = -1
                    bucket_next[vertex] = old_head
                    if old_head >= 0:
                        bucket_previous[old_head] = vertex
                    else:
                        pass
                    bucket_heads[estimate] = vertex
                    minimum_degree = min(minimum_degree, estimate)
                else:
                    pass
        step += 1
    for vertex in range(block_size):
        local_index[vertices[vertex]] = -1
    return result, lower_counts, emitted_count, emit_complete


@numba.njit(cache=True, inline="always")
def _reserve_adjacency_row(adjacency: np.ndarray, offsets: np.ndarray,
                           capacities: np.ndarray, counts: np.ndarray,
                           vertex: int, required: int, maximum: int,
                           cursor: int) -> int:
    """Move a growing row into unused space in the preallocated graph arena.

    :param adjacency: Flat mutable graph arena.
    :param offsets: Current row starting positions.
    :param capacities: Allocated slots per row.
    :param counts: Live neighbors per row.
    :param vertex: Row receiving the edge.
    :param required: Needed row length.
    :param maximum: Largest valid row length.
    :param cursor: First unused arena position.
    :return: Updated first unused position.
    """
    if required > capacities[vertex]:
        new_capacity: int = min(max(required, capacities[vertex] * 2), maximum)
        if cursor + new_capacity > adjacency.size:
            raise OverflowError("explicit adjacency arena")
        else:
            pass
        adjacency[cursor:cursor + counts[vertex]] = adjacency[offsets[vertex]:offsets[vertex] + counts[vertex]]
        offsets[vertex] = cursor
        capacities[vertex] = new_capacity
        cursor += new_capacity
    else:
        pass
    return cursor


@numba.njit(cache=True)
def _minimum_degree_order_sparse_explicit(vertices: np.ndarray, input_adjacency: np.ndarray,
                                          input_offsets: np.ndarray,
                                          adjacency_counts: np.ndarray,
                                          local_index: np.ndarray,
                                          symmetric_identity_matching: bool,
                                          emitted_rows: np.ndarray, emitted_count: int,
                                          emit_complete: bool,
                                          capacity_multiplier: int) -> tuple:
    """Port CLU's explicit-neighbor sparse minimum-degree elimination.

    :param vertices: Original column IDs in one BTF block.
    :param input_adjacency: Flat deduplicated input graph.
    :param input_offsets: Input graph row boundaries.
    :param adjacency_counts: Live graph row lengths.
    :param local_index: Original-to-local map cleared before return.
    :param symmetric_identity_matching: Whether to quotient-order a dense residual.
    :param emitted_rows: Bounded original-row output for filled neighborhoods.
    :param emitted_count: Number of filled output entries already used.
    :param emit_complete: Whether previous emission remains within the bound.
    :param capacity_multiplier: Preallocated arena reserve per input edge.
    :return: Elimination order, lower counts, output length, and completion flag.
    """
    block_size: int = vertices.size
    initial_counts: np.ndarray = adjacency_counts
    adjacency_counts = initial_counts.copy()
    adjacency_offsets: np.ndarray = np.empty(block_size + 1, dtype=np.int64)
    adjacency_capacities: np.ndarray = np.empty(block_size, dtype=np.int32)
    adjacency_offsets[0] = 0
    vertex: int = 0
    for vertex in range(block_size):
        adjacency_capacities[vertex] = min(block_size - 1, max(4, adjacency_counts[vertex] * 2))
        adjacency_offsets[vertex + 1] = adjacency_offsets[vertex] + adjacency_capacities[vertex]
    arena_cursor: int = adjacency_offsets[block_size]
    adjacency: np.ndarray = np.empty(arena_cursor + max(arena_cursor,
                                 input_adjacency.size * capacity_multiplier), dtype=np.int32)
    for vertex in range(block_size):
        adjacency[adjacency_offsets[vertex]:adjacency_offsets[vertex] + adjacency_counts[vertex]] = (
            input_adjacency[input_offsets[vertex]:input_offsets[vertex] + adjacency_counts[vertex]])
    active: np.ndarray = np.ones(block_size, dtype=np.uint8)
    clique_ready: np.ndarray = np.zeros(block_size, dtype=np.uint8)
    degree: np.ndarray = adjacency_counts.copy()
    bucket_heads: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    bucket_previous: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    bucket_next: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    live_neighbors: np.ndarray = np.empty(block_size, dtype=np.int32)
    live_neighbor_marks: np.ndarray = np.full(block_size, -1, dtype=np.int32)
    membership_marks: np.ndarray = np.zeros(block_size, dtype=np.int32)
    result: np.ndarray = np.empty(block_size, dtype=np.int32)
    lower_counts: np.ndarray = np.empty(block_size, dtype=np.int32)
    old_head: int = 0
    for vertex in range(block_size):
        old_head = bucket_heads[degree[vertex]]
        bucket_next[vertex] = old_head
        if old_head >= 0:
            bucket_previous[old_head] = vertex
        else:
            pass
        bucket_heads[degree[vertex]] = vertex
    minimum_degree: int = 0
    step: int = 0
    selected: int = -1
    next_vertex: int = -1
    selected_is_clique_ready: bool = False
    neighbor_count: int = 0
    neighbor_index: int = 0
    neighbor: int = 0
    entry: int = 0
    remove_index: int = 0
    current_count: int = 0
    last_index: int = 0
    first: int = 0
    second: int = 0
    fill_index: int = 0
    fill_vertex: int = 0
    membership_stamp: int = 0
    twin_candidate: bool = False
    existing_neighbor: int = 0
    for step in range(block_size):
        selected = -1
        while selected < 0 and minimum_degree < block_size:
            selected = bucket_heads[minimum_degree]
            if selected < 0:
                minimum_degree += 1
            else:
                next_vertex = bucket_next[selected]
                bucket_heads[minimum_degree] = next_vertex
                if next_vertex >= 0:
                    bucket_previous[next_vertex] = -1
                else:
                    pass
                bucket_previous[selected] = -1
                bucket_next[selected] = -1
        if selected < 0:
            raise ValueError("sparse degree buckets are empty")
        else:
            pass
        remaining: int = block_size - step
        if symmetric_identity_matching and step >= block_size // 2 and remaining >= 1024 and minimum_degree >= 3:
            residual_vertices: np.ndarray = np.empty(remaining, dtype=np.int32)
            residual_original: np.ndarray = np.empty(remaining, dtype=np.int32)
            residual_index: np.ndarray = np.full(block_size, -1, dtype=np.int32)
            residual_position: int = 0
            for vertex in range(block_size):
                if active[vertex] != 0:
                    residual_vertices[residual_position] = vertices[vertex]
                    residual_original[residual_position] = vertex
                    residual_index[vertex] = residual_position
                    residual_position += 1
                else:
                    pass
            residual_adjacency: List = List([np.empty(0, dtype=np.int32) for _ in range(remaining)])
            residual_counts: np.ndarray = np.empty(remaining, dtype=np.int32)
            residual_entries: int = 0
            for vertex in range(remaining):
                original_vertex: int = residual_original[vertex]
                live_row: np.ndarray = np.empty(adjacency_counts[original_vertex], dtype=np.int32)
                used: int = 0
                for entry in range(adjacency_counts[original_vertex]):
                    neighbor = adjacency[adjacency_offsets[original_vertex] + entry]
                    if active[neighbor] != 0:
                        live_row[used] = residual_index[neighbor]
                        used += 1
                    else:
                        pass
                residual_adjacency[vertex] = live_row[:used].copy()
                residual_counts[vertex] = used
                residual_entries += used
            suffix: np.ndarray
            suffix_counts: np.ndarray
            residual_flat: np.ndarray
            residual_offsets: np.ndarray
            residual_flat, residual_offsets = _flatten_pattern_columns(residual_adjacency)
            suffix, suffix_counts, emitted_count, emit_complete = _quotient_minimum_degree_order(
                residual_vertices, residual_flat, residual_offsets, residual_counts, local_index,
                residual_entries, emitted_rows, emitted_count, emit_complete)
            result[step:] = suffix
            lower_counts[step:] = suffix_counts
            for vertex in range(block_size):
                local_index[vertices[vertex]] = -1
            return result, lower_counts, emitted_count, emit_complete
        else:
            pass
        selected_is_clique_ready = clique_ready[selected] != 0
        clique_ready[selected] = 0
        active[selected] = 0
        neighbor_count = 0
        for entry in range(adjacency_counts[selected]):
            neighbor = adjacency[adjacency_offsets[selected] + entry]
            if active[neighbor] != 0:
                live_neighbors[neighbor_count] = neighbor
                live_neighbor_marks[neighbor] = step + 1
                neighbor_count += 1
            else:
                pass
        if not selected_is_clique_ready and neighbor_count > 2:
            for neighbor_index in range(neighbor_count):
                neighbor = live_neighbors[neighbor_index]
                arena_cursor = _reserve_adjacency_row(
                    adjacency, adjacency_offsets, adjacency_capacities, adjacency_counts,
                    neighbor, min(block_size - 1, adjacency_counts[neighbor] + neighbor_count - 1),
                    block_size - 1, arena_cursor)
        else:
            pass
        if neighbor_count == 2:
            first = live_neighbors[0]
            second = live_neighbors[1]
            for neighbor_index in range(2):
                neighbor = live_neighbors[neighbor_index]
                current_count = adjacency_counts[neighbor]
                remove_index = 0
                while remove_index < current_count and adjacency[adjacency_offsets[neighbor] + remove_index] != selected:
                    remove_index += 1
                if remove_index < current_count:
                    adjacency[adjacency_offsets[neighbor] + remove_index] = adjacency[adjacency_offsets[neighbor] + current_count - 1]
                    adjacency_counts[neighbor] -= 1
                else:
                    pass
            current_count = adjacency_counts[first]
            entry = 0
            while entry < current_count and adjacency[adjacency_offsets[first] + entry] != second:
                entry += 1
            if entry == current_count:
                arena_cursor = _reserve_adjacency_row(
                    adjacency, adjacency_offsets, adjacency_capacities, adjacency_counts,
                    first, current_count + 1, block_size - 1, arena_cursor)
                arena_cursor = _reserve_adjacency_row(
                    adjacency, adjacency_offsets, adjacency_capacities, adjacency_counts,
                    second, adjacency_counts[second] + 1, block_size - 1, arena_cursor)
                adjacency[adjacency_offsets[first] + adjacency_counts[first]] = second
                adjacency_counts[first] += 1
                adjacency[adjacency_offsets[second] + adjacency_counts[second]] = first
                adjacency_counts[second] += 1
            else:
                pass
            if not selected_is_clique_ready:
                if degree[first] == degree[selected] and adjacency_counts[first] + 1 == degree[selected] and adjacency_counts[first] == 1 and adjacency[adjacency_offsets[first]] == second:
                    clique_ready[first] = 1
                else:
                    pass
                if degree[second] == degree[selected] and adjacency_counts[second] + 1 == degree[selected] and adjacency_counts[second] == 1 and adjacency[adjacency_offsets[second]] == first:
                    clique_ready[second] = 1
                else:
                    pass
            else:
                pass
            minimum_degree = _refresh_degree_bucket(first, adjacency_counts, degree, bucket_heads,
                                                    bucket_previous, bucket_next, minimum_degree)
            minimum_degree = _refresh_degree_bucket(second, adjacency_counts, degree, bucket_heads,
                                                    bucket_previous, bucket_next, minimum_degree)
        else:
            for neighbor_index in range(neighbor_count):
                neighbor = live_neighbors[neighbor_index]
                current_count = adjacency_counts[neighbor]
                remove_index = 0
                while remove_index < current_count and adjacency[adjacency_offsets[neighbor] + remove_index] != selected:
                    remove_index += 1
                if remove_index < current_count:
                    adjacency[adjacency_offsets[neighbor] + remove_index] = adjacency[adjacency_offsets[neighbor] + current_count - 1]
                    adjacency_counts[neighbor] -= 1
                else:
                    pass
                if not selected_is_clique_ready and neighbor_count > 1:
                    membership_stamp += 1
                    twin_candidate = degree[neighbor] == degree[selected] and adjacency_counts[neighbor] + 1 == degree[selected]
                    for entry in range(adjacency_counts[neighbor]):
                        existing_neighbor = adjacency[adjacency_offsets[neighbor] + entry]
                        membership_marks[existing_neighbor] = membership_stamp
                        if live_neighbor_marks[existing_neighbor] != step + 1:
                            twin_candidate = False
                        else:
                            pass
                    if twin_candidate:
                        clique_ready[neighbor] = 1
                    else:
                        for fill_index in range(neighbor_index + 1, neighbor_count):
                            fill_vertex = live_neighbors[fill_index]
                            if membership_marks[fill_vertex] != membership_stamp:
                                arena_cursor = _reserve_adjacency_row(
                                    adjacency, adjacency_offsets, adjacency_capacities, adjacency_counts,
                                    neighbor, adjacency_counts[neighbor] + 1, block_size - 1,
                                    arena_cursor)
                                arena_cursor = _reserve_adjacency_row(
                                    adjacency, adjacency_offsets, adjacency_capacities, adjacency_counts,
                                    fill_vertex, adjacency_counts[fill_vertex] + 1, block_size - 1,
                                    arena_cursor)
                                adjacency[adjacency_offsets[neighbor] + adjacency_counts[neighbor]] = fill_vertex
                                adjacency_counts[neighbor] += 1
                                adjacency[adjacency_offsets[fill_vertex] + adjacency_counts[fill_vertex]] = neighbor
                                adjacency_counts[fill_vertex] += 1
                                membership_marks[fill_vertex] = membership_stamp
                            else:
                                pass
                else:
                    pass
                minimum_degree = _refresh_degree_bucket(neighbor, adjacency_counts, degree, bucket_heads,
                                                        bucket_previous, bucket_next, minimum_degree)
        lower_counts[step] = neighbor_count
        if emit_complete:
            if neighbor_count <= emitted_rows.size - emitted_count:
                for neighbor_index in range(neighbor_count):
                    emitted_rows[emitted_count] = vertices[live_neighbors[neighbor_index]]
                    emitted_count += 1
            else:
                emit_complete = False
        else:
            pass
        result[step] = vertices[selected]
    for vertex in range(block_size):
        local_index[vertices[vertex]] = -1
    return result, lower_counts, emitted_count, emit_complete


@numba.njit(cache=True)
def _finalize_emitted_patterns(indptr: np.ndarray, indices: np.ndarray,
                               block_offsets: np.ndarray, column_order: np.ndarray,
                               counts: np.ndarray, emitted_rows: np.ndarray,
                               complete: bool) -> tuple:
    """Transpose CLU's emitted filled neighborhoods into fixed L/U patterns.

    :param indptr: Original CSC column offsets.
    :param indices: Original CSC row indices.
    :param block_offsets: BTF block boundaries.
    :param column_order: Original columns in factor order.
    :param counts: Emitted strict-L count per factor column.
    :param emitted_rows: Original row identifiers emitted during ordering.
    :param complete: Whether bounded ordering emission finished.
    :return: Readiness, flat L/U patterns and offsets, inverse order, and U block starts.
    """
    order: int = column_order.size
    total: int = 0
    column: int = 0
    entry: int = 0
    row: int = 0
    block: int = 0
    begin: int = 0
    end: int = 0
    offset: int = 0
    coupling_count: int = 0
    row_positions: np.ndarray = np.empty(order, dtype=np.int32)
    upper_block_starts: np.ndarray = np.zeros(order, dtype=np.int32)
    for column in range(counts.size):
        total += counts[column]
    if not complete or counts.size != order or total > np.iinfo(np.int32).max or total != emitted_rows.size:
        return (False, np.empty(0, dtype=np.int32), np.zeros(order + 1, dtype=np.int32),
                np.empty(0, dtype=np.int32), np.zeros(order + 1, dtype=np.int32),
                row_positions, upper_block_starts)
    else:
        pass
    for column in range(order):
        row_positions[column_order[column]] = column
    lower_flat: np.ndarray = np.empty(total, dtype=np.int32)
    lower_offsets: np.ndarray = np.empty(order + 1, dtype=np.int32)
    upper_offsets: np.ndarray = np.zeros(order + 1, dtype=np.int32)
    for column in range(order):
        lower_offsets[column] = offset
        end = offset + counts[column]
        for entry in range(offset, end):
            row = row_positions[emitted_rows[entry]]
            lower_flat[entry] = row
            upper_offsets[row + 1] += 1
        _sort_pattern_slice(lower_flat, offset, end)
        offset = end
    lower_offsets[order] = offset
    coupling_offsets: np.ndarray = np.zeros(order + 1, dtype=np.int32)
    couplings: np.ndarray = np.empty(indices.size if block_offsets.size > 2 else 0, dtype=np.int32)
    if block_offsets.size > 2:
        marks: np.ndarray = np.full(order, -1, dtype=np.int32)
        for column in range(order):
            while column >= block_offsets[block + 1]:
                block += 1
            begin = coupling_count
            for entry in range(indptr[column_order[column]], indptr[column_order[column] + 1]):
                row = row_positions[indices[entry]]
                if row < block_offsets[block] and marks[row] != column:
                    marks[row] = column
                    couplings[coupling_count] = row
                    coupling_count += 1
                else:
                    pass
            upper_offsets[column + 1] += coupling_count - begin
            coupling_offsets[column + 1] = coupling_count
            upper_block_starts[column] = coupling_count - begin
            _sort_pattern_slice(couplings, begin, coupling_count)
    else:
        pass
    for column in range(order):
        upper_offsets[column + 1] += upper_offsets[column]
        if upper_offsets[column + 1] > np.iinfo(np.int32).max:
            return (False, np.empty(0, dtype=np.int32), np.zeros(order + 1, dtype=np.int32),
                    np.empty(0, dtype=np.int32), np.zeros(order + 1, dtype=np.int32),
                    row_positions, upper_block_starts)
        else:
            pass
    upper_flat: np.ndarray = np.empty(upper_offsets[order], dtype=np.int32)
    cursors: np.ndarray = upper_offsets[:order].copy()
    if block_offsets.size > 2:
        for column in range(order):
            for entry in range(coupling_offsets[column], coupling_offsets[column + 1]):
                upper_flat[cursors[column]] = couplings[entry]
                cursors[column] += 1
    else:
        pass
    for column in range(order):
        for entry in range(lower_offsets[column], lower_offsets[column + 1]):
            row = lower_flat[entry]
            upper_flat[cursors[row]] = column
            cursors[row] += 1
    return True, lower_flat, lower_offsets, upper_flat, upper_offsets, row_positions, upper_block_starts


@numba.njit(cache=True)
def _build_symbolic_patterns(indptr: np.ndarray, indices: np.ndarray,
                             column_order: np.ndarray, block_offsets: np.ndarray,
                             preferred_rows: np.ndarray) -> tuple:
    """Port CLU's nonsymmetric fixed-pivot structural reach construction.

    :param indptr: CSC column offsets.
    :param indices: CSC row indices.
    :param column_order: Original columns in symbolic order.
    :param block_offsets: BTF boundaries in factor order.
    :param preferred_rows: Matched input rows in factor order.
    :return: Strict L and U patterns, inverse pivot map, and in-block U starts.
    """
    order: int = column_order.size
    row_positions: np.ndarray = np.full(order, -1, dtype=np.int32)
    lower_rows: List = List([np.empty(0, dtype=np.int32) for _ in range(order)])
    upper_columns: List = List([np.empty(0, dtype=np.int32) for _ in range(order)])
    upper_block_starts: np.ndarray = np.zeros(order, dtype=np.int32)
    position_marks: np.ndarray = np.zeros(order, dtype=np.int32)
    prune_ends: np.ndarray = np.zeros(order, dtype=np.int32)
    candidates: np.ndarray = np.empty(order, dtype=np.int32)
    current_lower: np.ndarray = np.empty(order, dtype=np.int32)
    current_upper: np.ndarray = np.empty(order, dtype=np.int32)
    column: int = 0
    row: int = 0
    block_index: int = 0
    block_begin: int = 0
    stamp: int = 0
    candidate_count: int = 0
    lower_count: int = 0
    upper_count: int = 0
    upper_block_begin: int = 0
    entry: int = 0
    position: int = 0
    previous_column: int = 0
    previous_lower: np.ndarray
    lower_index: int = 0
    lower_end: int = 0
    can_prune: bool = False
    for column in range(order):
        row = preferred_rows[column]
        if row < 0 or row >= order or row_positions[row] >= 0:
            raise ValueError("fixed pattern needs a full row matching")
        else:
            row_positions[row] = column
    for column in range(order):
        while block_index + 1 < block_offsets.size and column >= block_offsets[block_index + 1]:
            block_index += 1
        block_begin = block_offsets[block_index]
        stamp = column + 1
        lower_count = 0
        upper_count = 0
        candidate_count = 0
        for entry in range(indptr[column_order[column]], indptr[column_order[column] + 1]):
            row = indices[entry]
            position = row_positions[row]
            if position_marks[position] != stamp:
                position_marks[position] = stamp
                if position > column:
                    current_lower[lower_count] = position
                    lower_count += 1
                elif position < column:
                    if position >= block_begin:
                        candidates[candidate_count] = position
                        candidate_count += 1
                    else:
                        current_upper[upper_count] = position
                        upper_count += 1
                else:
                    pass
            else:
                pass
        upper_block_begin = upper_count
        while candidate_count > 0:
            candidate_count -= 1
            previous_column = candidates[candidate_count]
            current_upper[upper_count] = previous_column
            upper_count += 1
            previous_lower = lower_rows[previous_column]
            lower_end = prune_ends[previous_column]
            can_prune = lower_end == previous_lower.size
            lower_index = 0
            while lower_index < lower_end and previous_lower[lower_index] < column:
                position = previous_lower[lower_index]
                if position_marks[position] != stamp:
                    position_marks[position] = stamp
                    candidates[candidate_count] = position
                    candidate_count += 1
                else:
                    pass
                lower_index += 1
            if lower_index < lower_end and previous_lower[lower_index] == column:
                if can_prune:
                    prune_ends[previous_column] = lower_index + 1
                else:
                    pass
                lower_index += 1
            else:
                pass
            while lower_index < lower_end:
                position = previous_lower[lower_index]
                if position_marks[position] != stamp:
                    position_marks[position] = stamp
                    current_lower[lower_count] = position
                    lower_count += 1
                else:
                    pass
                lower_index += 1
        ordered_lower: np.ndarray = current_lower[:lower_count].copy()
        _sort_pattern_slice(ordered_lower, 0, lower_count)
        lower_rows[column] = ordered_lower
        upper_block_starts[column] = upper_block_begin
        _sort_pattern_slice(current_upper, 0, upper_block_begin)
        _sort_pattern_slice(current_upper, upper_block_begin, upper_count)
        upper_columns[column] = current_upper[:upper_count].copy()
        prune_ends[column] = lower_count
    return lower_rows, upper_columns, row_positions, upper_block_starts


@numba.njit(cache=True)
def _build_symmetric_tree_patterns(indptr: np.ndarray, indices: np.ndarray,
                                   column_order: np.ndarray,
                                   counts: np.ndarray) -> tuple:
    """Port CLU's elimination-tree reach for symmetric structure.

    :param indptr: CSC column offsets.
    :param indices: CSC row indices.
    :param column_order: Ordered original columns.
    :param counts: Exact filled degrees from minimum-degree ordering.
    :return: Flat strict L/U patterns, offsets, and inverse column permutation.
    """
    order: int = column_order.size
    row_positions: np.ndarray = np.empty(order, dtype=np.int32)
    parents: np.ndarray = np.full(order, -1, dtype=np.int32)
    ancestors: np.ndarray = np.full(order, -1, dtype=np.int32)
    marks: np.ndarray = np.full(order, -1, dtype=np.int32)
    cursors: np.ndarray = np.empty(order, dtype=np.int32)
    lower_offsets: np.ndarray = np.empty(order + 1, dtype=np.int32)
    upper_offsets: np.ndarray = np.empty(order + 1, dtype=np.int32)
    lower_offsets[0] = 0
    upper_offsets[0] = 0
    column: int = 0
    total: int = 0
    for column in range(order):
        row_positions[column_order[column]] = column
        cursors[column] = total
        total += counts[column]
        if total > np.iinfo(np.int32).max:
            raise OverflowError("symmetric factor pattern exceeds int32")
        else:
            lower_offsets[column + 1] = total
    lower_flat: np.ndarray = np.empty(total, dtype=np.int32)
    upper_flat: np.ndarray = np.empty(total, dtype=np.int32)
    entries: int = 0
    original: int = 0
    entry: int = 0
    seed: int = 0
    row: int = 0
    next_row: int = 0
    for column in range(order):
        marks[column] = column
        original = column_order[column]
        for entry in range(indptr[original], indptr[original + 1]):
            seed = row_positions[indices[entry]]
            row = seed
            while row >= 0 and row < column:
                next_row = ancestors[row]
                ancestors[row] = column
                if next_row < 0:
                    parents[row] = column
                else:
                    pass
                row = next_row
            row = seed
            if row < column:
                while marks[row] != column:
                    marks[row] = column
                    if cursors[row] >= lower_offsets[row + 1]:
                        raise ValueError("symmetric lower count was too small")
                    else:
                        lower_flat[cursors[row]] = column
                        cursors[row] += 1
                    entries += 1
                    row = parents[row]
                    if row < 0:
                        raise ValueError("missing elimination-tree parent")
                    else:
                        pass
            else:
                pass
        upper_offsets[column + 1] = entries
    for column in range(order):
        if cursors[column] != lower_offsets[column + 1]:
            raise ValueError("symmetric lower count was too large")
        else:
            pass
    ancestors[:order] = upper_offsets[:order]
    for column in range(order):
        for entry in range(lower_offsets[column], lower_offsets[column + 1]):
            row = lower_flat[entry]
            upper_flat[ancestors[row]] = column
            ancestors[row] += 1
    return lower_flat, lower_offsets, upper_flat, upper_offsets, row_positions


@numba.njit(cache=True)
def _lower_run_length_cutoff(order: int) -> int:
    """Return CLU's minimum lower-column length for cached row runs.

    :param order: Matrix order.
    :return: Entry cutoff used by the fixed-pattern factorization.
    """
    return 128 if order >= 100000 or order <= 16000 else 512


@numba.njit(cache=True)
def _flatten_pattern_columns(columns: List) -> tuple[np.ndarray, np.ndarray]:
    """Pre-size one flat factor-pattern stream from analyzed columns.

    :param columns: Strict factor positions per column.
    :return: Flat positions and their half-open column offsets.
    """
    order: int = len(columns)
    offsets: np.ndarray = np.empty(order + 1, dtype=np.int32)
    offsets[0] = 0
    column: int = 0
    for column in range(order):
        offsets[column + 1] = offsets[column] + columns[column].size
    flat: np.ndarray = np.empty(offsets[order], dtype=np.int32)
    for column in range(order):
        flat[offsets[column]:offsets[column + 1]] = columns[column]
    return flat, offsets


@numba.njit(cache=True)
def _build_lower_runs(lower_positions: np.ndarray,
                      lower_offsets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Cache contiguous pivot-position spans in long strict-L columns.

    :param lower_positions: Flat strict-L pivot positions.
    :param lower_offsets: Column offsets into strict L.
    :return: Per-column run offsets and half-open local entry spans.
    """
    order: int = lower_offsets.size - 1
    cutoff: int = _lower_run_length_cutoff(order)
    run_count: int = 0
    column: int = 0
    lower_index: int = 0
    run_limit: int = 0
    first_row: int = 0
    for column in range(order):
        if lower_offsets[column + 1] - lower_offsets[column] > cutoff:
            lower_index = 0
            while lower_index < lower_offsets[column + 1] - lower_offsets[column]:
                first_row = lower_positions[lower_offsets[column] + lower_index]
                run_limit = lower_index + 1
                while run_limit < lower_offsets[column + 1] - lower_offsets[column] and lower_positions[lower_offsets[column] + run_limit] == first_row + run_limit - lower_index:
                    run_limit += 1
                if run_limit - lower_index >= 4:
                    run_count += 1
                else:
                    pass
                lower_index = run_limit
        else:
            pass
    if run_count == 0:
        return np.empty(0, dtype=np.int32), np.empty((0, 2), dtype=np.int32)
    else:
        pass
    run_offsets: np.ndarray = np.empty(order + 1, dtype=np.int32)
    runs: np.ndarray = np.empty((run_count, 2), dtype=np.int32)
    run_count = 0
    for column in range(order):
        run_offsets[column] = run_count
        if lower_offsets[column + 1] - lower_offsets[column] > cutoff:
            lower_index = 0
            while lower_index < lower_offsets[column + 1] - lower_offsets[column]:
                first_row = lower_positions[lower_offsets[column] + lower_index]
                run_limit = lower_index + 1
                while run_limit < lower_offsets[column + 1] - lower_offsets[column] and lower_positions[lower_offsets[column] + run_limit] == first_row + run_limit - lower_index:
                    run_limit += 1
                if run_limit - lower_index >= 4:
                    runs[run_count, 0] = lower_index
                    runs[run_count, 1] = run_limit
                    run_count += 1
                else:
                    pass
                lower_index = run_limit
        else:
            pass
    run_offsets[order] = run_count
    return run_offsets, runs


def _scatter_four_codegen(context: object, builder: object,
                          signature: object, arguments: tuple) -> None:
    """Emit four contiguous multiply-subtracts as one unaligned vector update.

    :param context: Numba lowering context.
    :param builder: LLVM IR builder.
    :param signature: Typed intrinsic signature.
    :param arguments: Lowered array, offset, and multiplier arguments.
    :return: Nothing.
    """
    # LLVM vector loads keep the work and factor streams in their native flat storage.
    work_array: object = context.make_array(signature.args[0])(context, builder, value=arguments[0])
    value_array: object = context.make_array(signature.args[1])(context, builder, value=arguments[1])
    vector_type: ir.VectorType = ir.VectorType(ir.DoubleType(), 4)
    work_ptr: object = builder.gep(work_array.data, [arguments[2]])
    value_ptr: object = builder.gep(value_array.data, [arguments[3]])
    vector_ptr_type: ir.PointerType = ir.PointerType(vector_type)
    old: object = builder.load(builder.bitcast(work_ptr, vector_ptr_type), align=1)
    factors: object = builder.load(builder.bitcast(value_ptr, vector_ptr_type), align=1)
    multiplier: object = ir.Constant(vector_type, ir.Undefined)
    lane: int = 0
    for lane in range(4):
        multiplier = builder.insert_element(multiplier, arguments[4],
                                            ir.Constant(ir.IntType(32), lane))
    result: object = builder.fsub(old, builder.fmul(factors, multiplier))
    builder.store(result, builder.bitcast(work_ptr, vector_ptr_type), align=1)


@intrinsic
def _scatter_four(typing_context: object, work: types.Array,
                  values: types.Array, work_offset: types.Integer,
                  value_offset: types.Integer, multiplier: types.Float) -> tuple | None:
    """Type one four-lane contiguous CLU update.

    :param typing_context: Numba typing context.
    :param work: Writable work-array type.
    :param values: Factor-value array type.
    :param work_offset: Work starting-position type.
    :param value_offset: Value starting-position type.
    :param multiplier: Upper coefficient type.
    :return: Intrinsic signature and LLVM code generator, or ``None`` for other types.
    """
    if (not isinstance(work, types.Array) or work.ndim != 1 or work.layout != "C"
            or work.dtype != types.float64 or not isinstance(values, types.Array)
            or values.ndim != 1 or values.layout != "C" or values.dtype != types.float64
            or not isinstance(work_offset, types.Integer)
            or not isinstance(value_offset, types.Integer)
            or multiplier != types.float64):
        return None
    else:
        return types.void(work, values, work_offset, value_offset, multiplier), _scatter_four_codegen


@numba.njit(cache=True)
def _scatter_lower_runs_flat(work: np.ndarray, rows: np.ndarray,
                              values: np.ndarray, lower_offsets: np.ndarray,
                              column: int, multiplier: float,
                              run_offsets: np.ndarray, runs: np.ndarray) -> None:
    """Scatter one flat L column through its cached contiguous runs.

    :param work: Pivot-position numeric workspace.
    :param rows: Flat strict L pivot positions.
    :param values: Flat strict L factors.
    :param lower_offsets: Strict L column boundaries.
    :param column: Dependency column.
    :param multiplier: Upper coefficient multiplying this L column.
    :param run_offsets: Per-column run boundaries.
    :param runs: Half-open local entry spans.
    :return: Nothing.
    """
    begin: int = lower_offsets[column]
    lower_index: int = 0
    run_index: int = 0
    run_begin: int = 0
    run_limit: int = 0
    first_row: int = 0
    offset: int = 0
    for run_index in range(run_offsets[column], run_offsets[column + 1]):
        run_begin = runs[run_index, 0]
        run_limit = runs[run_index, 1]
        for lower_index in range(lower_index, run_begin):
            work[rows[begin + lower_index]] -= values[begin + lower_index] * multiplier
        first_row = rows[begin + run_begin]
        offset = 0
        while offset + 4 <= run_limit - run_begin:
            _scatter_four(work, values, first_row + offset,
                          begin + run_begin + offset, multiplier)
            offset += 4
        while offset < run_limit - run_begin:
            work[first_row + offset] -= values[begin + run_begin + offset] * multiplier
            offset += 1
        lower_index = run_limit
    for lower_index in range(lower_index, lower_offsets[column + 1] - begin):
        work[rows[begin + lower_index]] -= values[begin + lower_index] * multiplier


@numba.njit(cache=True)
def _factorize_fixed_pattern_flat(indptr: np.ndarray, indices: np.ndarray,
                                   values: np.ndarray, column_order: np.ndarray,
                                   block_offsets: np.ndarray, row_positions: np.ndarray,
                                   lower_rows: np.ndarray, lower_offsets: np.ndarray,
                                   upper_columns: np.ndarray, upper_offsets: np.ndarray,
                                   upper_block_starts: np.ndarray,
                                   run_offsets: np.ndarray, runs: np.ndarray,
                                   scales: np.ndarray, reciprocals: np.ndarray,
                                   tolerance: float) -> tuple:
    """Factor a saved CLU pattern using pre-sized flat value streams.

    :param indptr: CSC column pointers.
    :param indices: CSC row indices.
    :param values: CSC numerical entries.
    :param column_order: Original columns in factor order.
    :param block_offsets: Analyzed BTF boundaries.
    :param row_positions: Matched input row to factor position.
    :param lower_rows: Flat strict L factor-position pattern.
    :param lower_offsets: Strict L column boundaries.
    :param upper_columns: Flat strict U factor-column pattern.
    :param upper_offsets: Strict U column boundaries.
    :param upper_block_starts: Absolute first in-block U entry per column.
    :param run_offsets: Cached lower-run boundaries.
    :param runs: Cached contiguous lower-entry spans.
    :param scales: Original input row maxima.
    :param reciprocals: Safe reciprocal row maxima.
    :param tolerance: Relative pivot acceptance threshold.
    :return: Acceptance, flat L values, flat U values, and U diagonal.
    """
    order: int = column_order.size
    work: np.ndarray = np.zeros(order, dtype=np.float64)
    diagonal: np.ndarray = np.empty(order, dtype=np.float64)
    lower_values: np.ndarray = np.empty(lower_rows.size, dtype=np.float64)
    upper_values: np.ndarray = np.empty(upper_columns.size, dtype=np.float64)
    run_cutoff: int = _lower_run_length_cutoff(order)
    column: int = 0
    block_index: int = 0
    block_begin: int = 0
    original_column: int = 0
    entry: int = 0
    row: int = 0
    previous_column: int = 0
    multiplier: float = 0.0
    pivot: float = 0.0
    pivot_reciprocal: float = 0.0
    maximum: float = 0.0
    for column in range(order):
        while block_index + 1 < block_offsets.size and column >= block_offsets[block_index + 1]:
            block_index += 1
        block_begin = block_offsets[block_index]
        original_column = column_order[column]
        for entry in range(indptr[original_column], indptr[original_column + 1]):
            row = indices[entry]
            work[row_positions[row]] += _equilibrated_value(values[entry], row, scales, reciprocals)
        for entry in range(upper_block_starts[column], upper_offsets[column + 1]):
            previous_column = upper_columns[entry]
            if previous_column >= block_begin:
                multiplier = work[previous_column]
                if run_offsets.size > 0 and lower_offsets[previous_column + 1] - lower_offsets[previous_column] > run_cutoff:
                    _scatter_lower_runs_flat(work, lower_rows, lower_values, lower_offsets,
                                              previous_column, multiplier, run_offsets, runs)
                else:
                    for row in range(lower_offsets[previous_column], lower_offsets[previous_column + 1]):
                        work[lower_rows[row]] -= lower_values[row] * multiplier
            else:
                pass
        pivot = work[column]
        maximum = abs(pivot)
        if not np.isfinite(pivot):
            raise FloatingPointError("non-finite fixed pivot")
        else:
            pass
        for entry in range(lower_offsets[column], lower_offsets[column + 1]):
            maximum = max(maximum, abs(work[lower_rows[entry]]))
        if maximum == 0.0:
            raise np.linalg.LinAlgError("matrix is singular")
        elif not np.isfinite(maximum):
            raise FloatingPointError("non-finite fixed factor")
        elif abs(pivot) < tolerance * maximum:
            return False, lower_values, upper_values, diagonal
        else:
            pass
        diagonal[column] = pivot
        pivot_reciprocal = _safe_reciprocal(pivot)
        for entry in range(upper_offsets[column], upper_offsets[column + 1]):
            row = upper_columns[entry]
            upper_values[entry] = work[row]
            if not np.isfinite(upper_values[entry]):
                raise FloatingPointError("non-finite fixed factor values")
            else:
                pass
            work[row] = 0.0
        for entry in range(lower_offsets[column], lower_offsets[column + 1]):
            row = lower_rows[entry]
            lower_values[entry] = work[row] * pivot_reciprocal if pivot_reciprocal != 0.0 else work[row] / pivot
            if not np.isfinite(lower_values[entry]):
                raise FloatingPointError("non-finite fixed factor values")
            else:
                pass
            work[row] = 0.0
        work[column] = 0.0
    return True, lower_values, upper_values, diagonal


@numba.njit(cache=True)
def _factorize_dynamic(indptr: np.ndarray, indices: np.ndarray, values: np.ndarray,
                       column_order: np.ndarray, preferred_rows: np.ndarray,
                       block_offsets: np.ndarray, scales: np.ndarray,
                       reciprocals: np.ndarray, tolerance: float,
                       capacity: int) -> tuple:
    """Port CLU's dynamic left-looking column factorization.

    :param indptr: CSC offsets.
    :param indices: CSC rows.
    :param values: CSC values.
    :param column_order: Original columns in factor order.
    :param preferred_rows: Matched row for each factor column.
    :param block_offsets: BTF block boundaries.
    :param scales: Original row maxima.
    :param reciprocals: Safe row reciprocal scales.
    :param tolerance: Threshold for retaining matched pivots.
    :param capacity: Preallocated entry count for each factor stream.
    :return: Lower and upper columns, diagonals, and pivot row maps.
    """
    order: int = column_order.size
    lower_indices: np.ndarray = np.empty(capacity, dtype=np.int32)
    lower_numbers: np.ndarray = np.empty(capacity, dtype=np.float64)
    upper_indices: np.ndarray = np.empty(capacity, dtype=np.int32)
    upper_numbers: np.ndarray = np.empty(capacity, dtype=np.float64)
    lower_offsets: np.ndarray = np.zeros(order + 1, dtype=np.int32)
    upper_offsets: np.ndarray = np.zeros(order + 1, dtype=np.int32)
    diagonal: np.ndarray = np.empty(order, dtype=np.float64)
    pivot_rows: np.ndarray = np.full(order, -1, dtype=np.int32)
    row_positions: np.ndarray = np.full(order, -1, dtype=np.int32)
    work: np.ndarray = np.zeros(order, dtype=np.float64)
    marks: np.ndarray = np.zeros(order, dtype=np.int32)
    touched: np.ndarray = np.empty(order, dtype=np.int32)
    candidate_marks: np.ndarray = np.zeros(order, dtype=np.int32)
    candidates: np.ndarray = np.empty(order, dtype=np.int32)
    column: int = 0
    block_index: int = 0
    block_begin: int = 0
    stamp: int = 0
    count: int = 0
    candidate_count: int = 0
    candidate_index: int = 0
    previous_column: int = 0
    entry: int = 0
    row: int = 0
    multiplier: float = 0.0
    maximum: float = 0.0
    maximum_row: int = -1
    preferred: int = 0
    pivot_row: int = 0
    pivot: float = 0.0
    pivot_reciprocal: float = 0.0
    lower_count: int = 0
    upper_count: int = 0
    required: int = 0
    for column in range(order):
        while block_index + 1 < block_offsets.size and column >= block_offsets[block_index + 1]:
            block_index += 1
        block_begin = block_offsets[block_index]
        stamp = column + 1
        count = _scatter_column(indptr, indices, values, column_order[column], scales,
                                reciprocals, stamp, marks, work, touched)
        candidate_count = _collect_candidates(
            column, block_begin, touched, count, lower_indices, lower_offsets, row_positions,
            candidate_marks, stamp, candidates)
        for candidate_index in range(candidate_count):
            previous_column = candidates[candidate_index]
            if previous_column >= block_begin:
                row = pivot_rows[previous_column]
                multiplier = work[row] if marks[row] == stamp else 0.0
                for entry in range(lower_offsets[previous_column], lower_offsets[previous_column + 1]):
                    row = lower_indices[entry]
                    count = _add_work_value(row, -lower_numbers[entry] * multiplier,
                                            stamp, marks, work, touched, count)
            else:
                pass
        maximum = 0.0
        maximum_row = -1
        for entry in range(count):
            row = touched[entry]
            if not np.isfinite(work[row]):
                raise FloatingPointError("non-finite factor value")
            elif row_positions[row] < 0 and abs(work[row]) > maximum:
                maximum = abs(work[row])
                maximum_row = row
            else:
                pass
        if maximum_row < 0:
            raise np.linalg.LinAlgError("matrix is singular")
        else:
            pass
        preferred = preferred_rows[column]
        if preferred >= 0 and row_positions[preferred] < 0 and marks[preferred] == stamp and abs(work[preferred]) >= tolerance * maximum:
            pivot_row = preferred
        else:
            pivot_row = maximum_row
        pivot_rows[column] = pivot_row
        row_positions[pivot_row] = column
        pivot = work[pivot_row]
        pivot_reciprocal = _safe_reciprocal(pivot)
        diagonal[column] = pivot
        upper_offsets[column] = upper_count
        required = upper_count + candidate_count
        if required > capacity:
            raise OverflowError("dynamic factor capacity")
        else:
            pass
        for entry in range(candidate_count):
            previous_column = candidates[entry]
            upper_indices[upper_count] = previous_column
            row = pivot_rows[previous_column]
            upper_numbers[upper_count] = work[row] if marks[row] == stamp else 0.0
            upper_count += 1
        upper_offsets[column + 1] = upper_count
        lower_offsets[column] = lower_count
        required = lower_count + count
        if required > capacity:
            raise OverflowError("dynamic factor capacity")
        else:
            pass
        for entry in range(count):
            row = touched[entry]
            if row_positions[row] < 0:
                lower_indices[lower_count] = row
                lower_numbers[lower_count] = work[row] * pivot_reciprocal if pivot_reciprocal != 0.0 else work[row] / pivot
                if not np.isfinite(lower_numbers[lower_count]):
                    raise FloatingPointError("non-finite lower factor")
                else:
                    pass
                lower_count += 1
            else:
                pass
        lower_offsets[column + 1] = lower_count
    # The reach uses original rows, then CLU stores pivot positions for replay and solve.
    for entry in range(lower_count):
        lower_indices[entry] = row_positions[lower_indices[entry]]
    return (lower_indices[:lower_count], lower_numbers[:lower_count], lower_offsets,
            upper_indices[:upper_count], upper_numbers[:upper_count], upper_offsets,
            diagonal, pivot_rows, row_positions)


@numba.njit(cache=True)
def _refactor_numeric_flat(indptr: np.ndarray, indices: np.ndarray, values: np.ndarray,
                           column_order: np.ndarray, block_offsets: np.ndarray,
                           lower_positions: np.ndarray, lower_values: np.ndarray,
                           lower_offsets: np.ndarray, upper_columns: np.ndarray,
                           upper_values: np.ndarray, upper_offsets: np.ndarray,
                           diagonal: np.ndarray, row_positions: np.ndarray,
                           scales: np.ndarray, reciprocals: np.ndarray,
                           work: np.ndarray) -> None:
    """Replay dynamic CLU factors held in contiguous C++ style arrays.

    :param indptr: CSC offsets for the analyzed pattern.
    :param indices: CSC row indices.
    :param values: Changed CSC values.
    :param column_order: Saved original columns in factor order.
    :param block_offsets: Analyzed BTF boundaries.
    :param lower_positions: Strict L pivot positions.
    :param lower_values: Mutable strict L factor values.
    :param lower_offsets: Strict L column boundaries.
    :param upper_columns: Strict U factor columns.
    :param upper_values: Mutable strict U factor values.
    :param upper_offsets: Strict U column boundaries.
    :param diagonal: Mutable U diagonal.
    :param row_positions: Original row to pivot position map.
    :param scales: New row maxima.
    :param reciprocals: New safe row reciprocals.
    :param work: Caller-owned zeroed pivot-order scratch.
    :return: Nothing.
    """
    order: int = column_order.size
    work.fill(0.0)
    block_index: int = 0
    block_begin: int = 0
    column: int = 0
    entry: int = 0
    dependency: int = 0
    row: int = 0
    multiplier: float = 0.0
    pivot: float = 0.0
    reciprocal: float = 0.0
    for column in range(order):
        while block_index + 1 < block_offsets.size and column >= block_offsets[block_index + 1]:
            block_index += 1
        block_begin = block_offsets[block_index]
        _scatter_replay_column(indptr, indices, values, column_order[column],
                               row_positions, scales, reciprocals, work)
        for entry in range(upper_offsets[column], upper_offsets[column + 1]):
            dependency = upper_columns[entry]
            if dependency >= block_begin:
                multiplier = work[dependency]
                upper_values[entry] = multiplier
                work[dependency] = 0.0
                for row in range(lower_offsets[dependency], lower_offsets[dependency + 1]):
                    work[lower_positions[row]] -= lower_values[row] * multiplier
            else:
                upper_values[entry] = work[dependency]
                work[dependency] = 0.0
        pivot = work[column]
        if not np.isfinite(pivot):
            raise FloatingPointError("non-finite replay pivot")
        elif pivot == 0.0:
            column_finite: bool = True
            for entry in range(upper_offsets[column], upper_offsets[column + 1]):
                column_finite = column_finite and np.isfinite(upper_values[entry])
            for entry in range(lower_offsets[column], lower_offsets[column + 1]):
                column_finite = column_finite and np.isfinite(work[lower_positions[entry]])
            if not column_finite:
                raise FloatingPointError("non-finite replay column")
            else:
                raise np.linalg.LinAlgError("saved pivot is singular")
        else:
            diagonal[column] = pivot
        for entry in range(upper_offsets[column], upper_offsets[column + 1]):
            if not np.isfinite(upper_values[entry]):
                raise FloatingPointError("non-finite replay U factor")
            else:
                pass
        reciprocal = _safe_reciprocal(pivot)
        for entry in range(lower_offsets[column], lower_offsets[column + 1]):
            row = lower_positions[entry]
            lower_values[entry] = work[row] * reciprocal if reciprocal != 0.0 else work[row] / pivot
            if not np.isfinite(lower_values[entry]):
                raise FloatingPointError("non-finite replay factor")
            else:
                pass
            work[row] = 0.0
        work[column] = 0.0


@numba.njit(cache=True)
def _prepare_solve_rhs_reciprocals(pivot_rows: np.ndarray,
                                    row_scale_reciprocals: np.ndarray) -> tuple[np.ndarray, bool]:
    """Arrange safe row-scale reciprocals in CLU pivot order.

    :param pivot_rows: Original input rows in factor order.
    :param row_scale_reciprocals: Safe row-scale reciprocals or zero markers.
    :return: Pivot-ordered reciprocals and whether all are safe.
    """
    order: int = pivot_rows.size
    reciprocals: np.ndarray = np.empty(order, dtype=np.float64)
    all_safe: bool = True
    position: int = 0
    for position in range(order):
        reciprocals[position] = row_scale_reciprocals[pivot_rows[position]]
        all_safe = all_safe and reciprocals[position] != 0.0
    return reciprocals, all_safe


@numba.njit(cache=True)
def _prepare_upper_block_starts_flat(upper_columns: np.ndarray,
                                      upper_offsets: np.ndarray,
                                      block_offsets: np.ndarray) -> np.ndarray:
    """Locate each flat strict U column's first within-block entry.

    :param upper_columns: Strict U factor positions.
    :param upper_offsets: Strict U column boundaries.
    :param block_offsets: Analyzed BTF boundaries.
    :return: Absolute first within-block strict U entry per column.
    """
    order: int = upper_offsets.size - 1
    starts: np.ndarray = np.empty(order, dtype=np.int32)
    block_index: int = 0
    block_begin: int = 0
    column: int = 0
    entry: int = 0
    for column in range(order):
        while block_index + 1 < block_offsets.size and column >= block_offsets[block_index + 1]:
            block_index += 1
        block_begin = block_offsets[block_index]
        entry = upper_offsets[column]
        while entry < upper_offsets[column + 1] and upper_columns[entry] < block_begin:
            entry += 1
        starts[column] = entry
    return starts


@numba.njit(cache=True)
def _has_two_hub_triangular_pattern_flat(lower_positions: np.ndarray,
                                          lower_offsets: np.ndarray,
                                          upper_columns: np.ndarray,
                                          upper_offsets: np.ndarray) -> bool:
    """Recognize CLU's two-hub arrow pattern in flat factor storage.

    :param lower_positions: Strict L pivot positions.
    :param lower_offsets: Strict L column boundaries.
    :param upper_columns: Strict U factor positions.
    :param upper_offsets: Strict U column boundaries.
    :return: Whether the specialized triangular solve applies.
    """
    order: int = lower_offsets.size - 1
    if order < 3 or order > 256:
        return False
    else:
        pass
    first_hub: int = order - 2
    second_hub: int = order - 1
    column: int = 0
    entry: int = 0
    for column in range(first_hub):
        if (lower_offsets[column + 1] - lower_offsets[column] != 1
                or upper_offsets[column + 1] != upper_offsets[column]
                or lower_positions[lower_offsets[column]] != first_hub):
            return False
        else:
            pass
    if (lower_offsets[first_hub + 1] - lower_offsets[first_hub] != 1
            or lower_positions[lower_offsets[first_hub]] != second_hub
            or lower_offsets[second_hub + 1] != lower_offsets[second_hub]
            or upper_offsets[first_hub + 1] - upper_offsets[first_hub] != first_hub
            or upper_offsets[second_hub + 1] - upper_offsets[second_hub] != 1):
        return False
    else:
        pass
    for entry in range(first_hub):
        if upper_columns[upper_offsets[first_hub] + entry] != entry:
            return False
        else:
            pass
    return upper_columns[upper_offsets[second_hub]] == first_hub


@numba.njit(cache=True)
def _solve_btf_blocks(work: np.ndarray, block_offsets: np.ndarray,
                      lower_positions: List, lower_values: List,
                      upper_columns: List, upper_values: List,
                      upper_block_starts: np.ndarray, diagonal: np.ndarray,
                      diagonal_reciprocals: np.ndarray) -> None:
    """Solve CLU's triangular factors in reverse BTF block order.

    :param work: Pivot-order right-hand side modified in place.
    :param block_offsets: Block boundaries.
    :param lower_positions: Strict-L pivot positions.
    :param lower_values: Strict-L factors.
    :param upper_columns: Strict-U factor positions.
    :param upper_values: Strict-U factors.
    :param upper_block_starts: First within-block U entry per column.
    :param diagonal: U diagonal.
    :param diagonal_reciprocals: Safe U diagonal reciprocals or zero markers.
    :return: Nothing.
    """
    block_index: int = 0
    block_begin: int = 0
    block_end: int = 0
    column: int = 0
    entry: int = 0
    reciprocal: float = 0.0
    value: float = 0.0
    for block_index in range(block_offsets.size - 2, -1, -1):
        block_begin = block_offsets[block_index]
        block_end = block_offsets[block_index + 1]
        if block_end == block_begin + 1:
            column = block_begin
            reciprocal = diagonal_reciprocals[column]
            work[column] = work[column] * reciprocal if reciprocal != 0.0 else work[column] / diagonal[column]
            value = work[column]
            for entry in range(upper_columns[column].size):
                work[upper_columns[column][entry]] -= upper_values[column][entry] * value
        else:
            for column in range(block_begin, block_end):
                value = work[column]
                for entry in range(lower_positions[column].size):
                    work[lower_positions[column][entry]] -= lower_values[column][entry] * value
            for column in range(block_end - 1, block_begin - 1, -1):
                reciprocal = diagonal_reciprocals[column]
                work[column] = work[column] * reciprocal if reciprocal != 0.0 else work[column] / diagonal[column]
                value = work[column]
                for entry in range(upper_block_starts[column], upper_columns[column].size):
                    work[upper_columns[column][entry]] -= upper_values[column][entry] * value
            for column in range(block_begin, block_end):
                value = work[column]
                for entry in range(upper_block_starts[column]):
                    work[upper_columns[column][entry]] -= upper_values[column][entry] * value


@numba.njit(cache=True)
def _solve_btf_blocks_flat(work: np.ndarray, block_offsets: np.ndarray,
                            lower_positions: np.ndarray, lower_values: np.ndarray,
                            lower_offsets: np.ndarray, upper_columns: np.ndarray,
                            upper_values: np.ndarray, upper_offsets: np.ndarray,
                            upper_block_starts: np.ndarray, diagonal: np.ndarray,
                            diagonal_reciprocals: np.ndarray) -> None:
    """Solve CLU's reverse BTF traversal using contiguous factor streams.

    :param work: Pivot-order right-hand side modified in place.
    :param block_offsets: Analyzed BTF boundaries.
    :param lower_positions: Strict L pivot positions.
    :param lower_values: Strict L factors.
    :param lower_offsets: Strict L column boundaries.
    :param upper_columns: Strict U factor positions.
    :param upper_values: Strict U factors.
    :param upper_offsets: Strict U column boundaries.
    :param upper_block_starts: First within-block U entry per column.
    :param diagonal: U diagonal.
    :param diagonal_reciprocals: Safe U reciprocals or zero markers.
    :return: Nothing.
    """
    block_index: int = 0
    block_begin: int = 0
    block_end: int = 0
    column: int = 0
    entry: int = 0
    reciprocal: float = 0.0
    value: float = 0.0
    for block_index in range(block_offsets.size - 2, -1, -1):
        block_begin = block_offsets[block_index]
        block_end = block_offsets[block_index + 1]
        if block_end == block_begin + 1:
            column = block_begin
            reciprocal = diagonal_reciprocals[column]
            work[column] = work[column] * reciprocal if reciprocal != 0.0 else work[column] / diagonal[column]
            value = work[column]
            for entry in range(upper_offsets[column], upper_offsets[column + 1]):
                work[upper_columns[entry]] -= upper_values[entry] * value
        else:
            for column in range(block_begin, block_end):
                value = work[column]
                for entry in range(lower_offsets[column], lower_offsets[column + 1]):
                    work[lower_positions[entry]] -= lower_values[entry] * value
            for column in range(block_end - 1, block_begin - 1, -1):
                reciprocal = diagonal_reciprocals[column]
                work[column] = work[column] * reciprocal if reciprocal != 0.0 else work[column] / diagonal[column]
                value = work[column]
                for entry in range(upper_block_starts[column], upper_offsets[column + 1]):
                    work[upper_columns[entry]] -= upper_values[entry] * value
            for column in range(block_begin, block_end):
                value = work[column]
                for entry in range(upper_offsets[column], upper_block_starts[column]):
                    work[upper_columns[entry]] -= upper_values[entry] * value


@numba.njit(cache=True)
def _solve_numeric_flat(lower_positions: np.ndarray, lower_values: np.ndarray,
                         lower_offsets: np.ndarray, upper_columns: np.ndarray,
                         upper_values: np.ndarray, upper_offsets: np.ndarray,
                         diagonal: np.ndarray, pivot_rows: np.ndarray,
                         column_order: np.ndarray, block_offsets: np.ndarray,
                         upper_block_starts: np.ndarray, scales: np.ndarray,
                         rhs_reciprocals: np.ndarray,
                         all_rhs_reciprocals_safe: bool,
                         rhs: np.ndarray, work: np.ndarray) -> np.ndarray:
    """Solve CLU's flat dynamic factors for one original-order right-hand side.

    :param lower_positions: Strict L pivot positions.
    :param lower_values: Strict L factor values.
    :param lower_offsets: Strict L column boundaries.
    :param upper_columns: Strict U factor positions.
    :param upper_values: Strict U factor values.
    :param upper_offsets: Strict U column boundaries.
    :param diagonal: U diagonal.
    :param pivot_rows: Original rows in factor order.
    :param column_order: Original columns in factor order.
    :param block_offsets: Analyzed BTF boundaries.
    :param upper_block_starts: First in-block strict U entry per column.
    :param scales: Original row maxima.
    :param rhs_reciprocals: Pivot-order safe scale reciprocals.
    :param all_rhs_reciprocals_safe: Whether all row-scale reciprocals are safe.
    :param rhs: Original right-hand side.
    :param work: Caller-owned pivot-order scratch.
    :return: Solution in original column order.
    """
    order: int = diagonal.size
    result: np.ndarray = np.empty(order, dtype=np.float64)
    diagonal_reciprocals: np.ndarray = np.empty(order, dtype=np.float64)
    column: int = 0
    entry: int = 0
    row: int = 0
    if all_rhs_reciprocals_safe:
        for column in range(order):
            row = pivot_rows[column]
            work[column] = rhs[row] * rhs_reciprocals[column]
            diagonal_reciprocals[column] = _safe_reciprocal(diagonal[column])
    else:
        for column in range(order):
            row = pivot_rows[column]
            work[column] = rhs[row] * rhs_reciprocals[column] if rhs_reciprocals[column] != 0.0 else rhs[row] / scales[row]
            diagonal_reciprocals[column] = _safe_reciprocal(diagonal[column])
    if (block_offsets.size == 2 and np.all(diagonal_reciprocals != 0.0)
            and _has_two_hub_triangular_pattern_flat(lower_positions, lower_offsets,
                                                       upper_columns, upper_offsets)):
        first_hub: int = order - 2
        second_hub: int = order - 1
        first_hub_value: float = work[first_hub]
        for column in range(first_hub):
            first_hub_value -= lower_values[lower_offsets[column]] * work[column]
        work[first_hub] = first_hub_value
        work[second_hub] -= lower_values[lower_offsets[first_hub]] * work[first_hub]
        work[second_hub] *= diagonal_reciprocals[second_hub]
        work[first_hub] -= upper_values[upper_offsets[second_hub]] * work[second_hub]
        work[first_hub] *= diagonal_reciprocals[first_hub]
        for entry in range(upper_offsets[first_hub], upper_offsets[first_hub + 1]):
            work[upper_columns[entry]] -= upper_values[entry] * work[first_hub]
        for column in range(first_hub - 1, -1, -1):
            work[column] *= diagonal_reciprocals[column]
    elif block_offsets.size > 2:
        _solve_btf_blocks_flat(work, block_offsets, lower_positions, lower_values,
                                lower_offsets, upper_columns, upper_values,
                                upper_offsets, upper_block_starts, diagonal,
                                diagonal_reciprocals)
    else:
        for column in range(order):
            for entry in range(lower_offsets[column], lower_offsets[column + 1]):
                row = lower_positions[entry]
                work[row] -= lower_values[entry] * work[column]
        for column in range(order - 1, -1, -1):
            if diagonal_reciprocals[column] != 0.0:
                work[column] *= diagonal_reciprocals[column]
            else:
                work[column] /= diagonal[column]
            for entry in range(upper_offsets[column], upper_offsets[column + 1]):
                work[upper_columns[entry]] -= upper_values[entry] * work[column]
    for column in range(order):
        result[column_order[column]] = work[column]
    return result


def analyze(A: sp.spmatrix, options: Options, symbolic: Symbolic,
            statistics: Statistics) -> Status:
    """Analyze the CSC structure without touching numerical pivots.

    :param A: Real square CSC-compatible matrix.
    :param options: CLU analysis controls.
    :param symbolic: Destination for reusable symbolic state.
    :param statistics: Destination for analysis counters.
    :return: CLU status.
    """
    if not isinstance(options, Options) or not isinstance(symbolic, Symbolic) or not isinstance(statistics, Statistics):
        return Status.INVALID_INPUT
    else:
        pass
    symbolic.__init__()
    statistics.__init__()
    if not isinstance(options.ordering, Ordering) or not _valid_options(options.pivot_tolerance):
        return Status.INVALID_INPUT
    else:
        pass
    if np.iscomplexobj(A.data if sp.issparse(A) else A):
        return Status.INVALID_INPUT
    else:
        pass
    try:
        matrix: sp.csc_matrix = sp.csc_matrix(A, dtype=np.float64)
    except (ValueError, TypeError, OverflowError):
        return Status.INVALID_INPUT
    try:
        order: int = matrix.shape[0]
        if order != matrix.shape[1] or order > np.iinfo(np.int32).max or matrix.nnz > np.iinfo(np.int32).max:
            return Status.INVALID_INPUT
        else:
            pass
        indptr: np.ndarray = np.asarray(matrix.indptr, dtype=np.int32)
        indices: np.ndarray = np.asarray(matrix.indices, dtype=np.int32)
        values: np.ndarray = np.asarray(matrix.data, dtype=np.float64)
        valid: bool
        diagonal_pattern: bool
        identity_matching_available: bool
        valid, diagonal_pattern, identity_matching_available = _valid_matrix(order, indptr, indices, values)
        if not valid:
            return Status.INVALID_INPUT
        else:
            pass
        symbolic._order = order
        symbolic._indptr = indptr.copy()
        symbolic._indices = indices.copy()
        statistics.order = order
        statistics.nonzeros = values.size
        symbolic._tiny_dense = _tiny_dense_pattern(order, indptr, indices)
        symbolic._diagonal_pattern = diagonal_pattern
        if symbolic._tiny_dense:
            statistics.blocks = 1
            statistics.largest_block = order
            symbolic._valid = True
        elif diagonal_pattern:
            symbolic._column_order = np.arange(order, dtype=np.int32)
            symbolic._preferred_rows = symbolic._column_order.copy()
            symbolic._block_offsets = np.arange(order + 1, dtype=np.int32)
            symbolic._fixed_pattern_ready = True
            statistics.blocks = order
            statistics.largest_block = 1 if order > 0 else 0
            symbolic._valid = True
        else:
            row_match: np.ndarray
            column_match: np.ndarray
            full_rank: bool
            if identity_matching_available:
                row_match = np.arange(order, dtype=np.int32)
                column_match = row_match.copy()
                full_rank = True
            else:
                row_match, column_match, full_rank = _compute_matching(indptr, indices)
            symbolic._column_order = np.arange(order, dtype=np.int32)
            symbolic._block_offsets = np.array([0, order], dtype=np.int32)
            matched_identity: bool = full_rank and np.array_equal(row_match, np.arange(order, dtype=np.int32))
            symmetric_identity_matching: bool = options.symmetric_pattern and matched_identity
            if full_rank and options.use_block_triangular_form and not ((symmetric_identity_matching and order >= 4000) or order >= 20000):
                if symmetric_identity_matching:
                    symbolic._column_order, symbolic._block_offsets = _compute_symmetric_btf_blocks(indptr, indices, row_match)
                else:
                    symbolic._column_order, symbolic._block_offsets = _compute_btf_blocks(indptr, indices, row_match)
            else:
                pass
            use_envelope: bool = matched_identity and not symmetric_identity_matching and options.ordering is Ordering.APPROXIMATE_MINIMUM_DEGREE
            has_sparse_block: bool = False
            block_index: int = 0
            block_begin: int = 0
            block_end: int = 0
            block_size: int = 0
            for block_index in range(symbolic._block_offsets.size - 1):
                block_size = symbolic._block_offsets[block_index + 1] - symbolic._block_offsets[block_index]
                if block_size > 1:
                    sparse_block: bool = block_size > 10000 or 3500 <= block_size <= 4000
                    use_envelope = use_envelope and sparse_block
                    has_sparse_block = has_sparse_block or sparse_block
                else:
                    pass
                statistics.largest_block = max(statistics.largest_block, block_size)
            statistics.blocks = symbolic._block_offsets.size - 1
            use_envelope = use_envelope and has_sparse_block
            emitted_limit: int = min(np.iinfo(np.int32).max, values.size * 8 + order) if use_envelope else 0
            emitted_rows: np.ndarray = np.empty(emitted_limit, dtype=np.int32)
            emitted_count: int = 0
            emitted_complete: bool = use_envelope
            lower_counts: np.ndarray = np.zeros(order, dtype=np.int32)
            local_index: np.ndarray = np.full(order, -1, dtype=np.int32)
            for block_index in range(symbolic._block_offsets.size - 1):
                block_begin = symbolic._block_offsets[block_index]
                block_end = symbolic._block_offsets[block_index + 1]
                block_size = block_end - block_begin
                if options.ordering is Ordering.APPROXIMATE_MINIMUM_DEGREE and 1 < block_size <= 10000 and (symmetric_identity_matching or block_size < 3500 or block_size > 4000):
                    ordered_block: np.ndarray
                    block_counts: np.ndarray
                    ordered_block, block_counts = _minimum_degree_order_bitset(
                        indptr, indices, symbolic._column_order[block_begin:block_end], row_match, local_index)
                    symbolic._column_order[block_begin:block_end] = ordered_block
                    lower_counts[block_begin:block_end] = block_counts
                elif options.ordering is Ordering.APPROXIMATE_MINIMUM_DEGREE and block_size >= 3500:
                    adjacency: np.ndarray
                    adjacency_offsets: np.ndarray
                    adjacency_counts: np.ndarray
                    adjacency_entries: int
                    estimated_entries: int
                    adjacency, adjacency_offsets, adjacency_counts, adjacency_entries, estimated_entries = _build_ordering_adjacency(
                        indptr, indices, symbolic._column_order[block_begin:block_end], row_match, local_index)
                    if use_envelope and adjacency_entries * 4 > estimated_entries * 3:
                        emitted_complete = False
                    else:
                        pass
                    if adjacency_entries < block_size * 5:
                        capacity_multiplier: int = 4
                        while True:
                            try:
                                ordered_block, block_counts, emitted_count, emitted_complete = _minimum_degree_order_sparse_explicit(
                                    symbolic._column_order[block_begin:block_end], adjacency,
                                    adjacency_offsets, adjacency_counts, local_index,
                                    symmetric_identity_matching, emitted_rows, emitted_count,
                                    emitted_complete, capacity_multiplier)
                                break
                            except OverflowError:
                                if capacity_multiplier >= block_size:
                                    raise
                                else:
                                    capacity_multiplier = min(block_size, capacity_multiplier * 2)
                    else:
                        ordered_block, block_counts, emitted_count, emitted_complete = _quotient_minimum_degree_order(
                            symbolic._column_order[block_begin:block_end], adjacency,
                            adjacency_offsets,
                            adjacency_counts, local_index, adjacency_entries,
                            emitted_rows, emitted_count, emitted_complete)
                    symbolic._column_order[block_begin:block_end] = ordered_block
                    lower_counts[block_begin:block_end] = block_counts
                else:
                    pass
            if full_rank:
                symbolic._preferred_rows = column_match[symbolic._column_order]
            else:
                symbolic._preferred_rows = np.full(order, -1, dtype=np.int32)
            if full_rank:
                lower_pattern: List
                upper_pattern: List
                fixed_positions: np.ndarray
                upper_block_starts: np.ndarray
                if symmetric_identity_matching and options.ordering is Ordering.APPROXIMATE_MINIMUM_DEGREE:
                    (symbolic._lower_flat, symbolic._lower_offsets,
                     symbolic._upper_flat, symbolic._upper_offsets,
                     fixed_positions) = _build_symmetric_tree_patterns(
                        indptr, indices, symbolic._column_order, lower_counts)
                    upper_block_starts = np.zeros(order, dtype=np.int32)
                elif use_envelope:
                    envelope_ready: bool
                    (envelope_ready, symbolic._lower_flat, symbolic._lower_offsets,
                     symbolic._upper_flat, symbolic._upper_offsets,
                     fixed_positions, upper_block_starts) = _finalize_emitted_patterns(
                        indptr, indices, symbolic._block_offsets, symbolic._column_order,
                        lower_counts, emitted_rows[:emitted_count], emitted_complete)
                    symbolic._ordering_envelope = envelope_ready
                    if not envelope_ready:
                        lower_pattern, upper_pattern, fixed_positions, upper_block_starts = _build_symbolic_patterns(
                            indptr, indices, symbolic._column_order, symbolic._block_offsets,
                            symbolic._preferred_rows)
                        symbolic._lower_flat, symbolic._lower_offsets = _flatten_pattern_columns(lower_pattern)
                        symbolic._upper_flat, symbolic._upper_offsets = _flatten_pattern_columns(upper_pattern)
                    else:
                        pass
                else:
                    lower_pattern, upper_pattern, fixed_positions, upper_block_starts = _build_symbolic_patterns(
                        indptr, indices, symbolic._column_order, symbolic._block_offsets,
                        symbolic._preferred_rows)
                    symbolic._lower_flat, symbolic._lower_offsets = _flatten_pattern_columns(lower_pattern)
                    symbolic._upper_flat, symbolic._upper_offsets = _flatten_pattern_columns(upper_pattern)
                symbolic._fixed_positions = fixed_positions
                symbolic._upper_block_starts = upper_block_starts
                symbolic._fixed_pattern_ready = True
            else:
                pass
            symbolic._valid = True
        symbolic._statistics = Statistics(statistics.order, statistics.nonzeros,
                                          statistics.blocks, statistics.largest_block)
        return Status.SUCCESS
    except MemoryError:
        symbolic.__init__()
        statistics.__init__()
        return Status.OUT_OF_MEMORY
    except (ValueError, TypeError, RuntimeError, OverflowError):
        symbolic.__init__()
        statistics.__init__()
        return Status.NUMERICAL_FAILURE


class _FactoredMatrix:
    """Retain CLU-style symbolic and numeric data for repeated sparse solves."""

    __slots__ = ("_order", "_indptr", "_indices", "_column_order", "_block_offsets",
                 "_lower_run_offsets", "_lower_runs", "_upper_block_starts", "_fixed_pattern_used",
                 "_flat_lower_positions", "_flat_lower_values", "_flat_lower_offsets",
                 "_flat_upper_columns", "_flat_upper_values", "_flat_upper_offsets",
                 "_diagonal", "_pivot_rows", "_row_positions", "_scales",
                 "_reciprocals", "_solve_rhs_reciprocals", "_all_solve_rhs_reciprocals_safe", "_ordering_envelope", "_valid", "_tiny_dense", "_tiny_lu", "_tiny_scales", "_tiny_rows",
                 "_diagonal_pattern", "_diagonal_scales", "_diagonal_scale_reciprocals",
                 "_diagonal_values", "_diagonal_reciprocals", "_diagonal_rhs_reciprocals",
                 "_diagonal_all_safe")

    def __init__(self, A: sp.spmatrix, pivot_tolerance: float = 1e-3,
                 ordering: Ordering = Ordering.APPROXIMATE_MINIMUM_DEGREE,
                 use_block_triangular_form: bool = True,
                 symmetric_pattern: bool = False,
                 symbolic: Symbolic | None = None) -> None:
        """Analyze and factor a real CSC matrix.

        :param A: Square sparse input matrix.
        :param pivot_tolerance: Relative pivot acceptance threshold.
        :param ordering: CLU symbolic ordering strategy.
        :param use_block_triangular_form: Whether to decompose the matched graph.
        :param symmetric_pattern: Caller guarantee of symmetric CSC structure.
        :return: Nothing.
        """
        if np.iscomplexobj(A.data if sp.issparse(A) else A):
            raise ValueError("matrix must be real")
        else:
            pass
        matrix: sp.csc_matrix = sp.csc_matrix(A, dtype=np.float64)
        if matrix.shape[0] != matrix.shape[1] or matrix.shape[0] > np.iinfo(np.int32).max or matrix.nnz > np.iinfo(np.int32).max:
            raise ValueError("matrix must be real, finite, and square")
        else:
            pass
        if not _valid_options(pivot_tolerance):
            raise ValueError("pivot_tolerance must be finite and in (0, 1]")
        else:
            pass
        if not isinstance(ordering, Ordering):
            raise ValueError("ordering must be a CLU Ordering")
        else:
            pass
        options: Options = Options(ordering, use_block_triangular_form,
                                   pivot_tolerance, symmetric_pattern)
        if symbolic is None:
            symbolic = Symbolic()
            analysis_statistics: Statistics = Statistics()
            status: Status = analyze(matrix, options, symbolic, analysis_statistics)
            if status is not Status.SUCCESS:
                raise ValueError(f"CLU analysis failed: {status_name(status)}")
            else:
                pass
        else:
            if not symbolic.is_valid() or not _valid_same_pattern(
                    matrix.shape[0], matrix.indptr, matrix.indices, matrix.data,
                    True, symbolic._order, symbolic._indptr, symbolic._indices):
                raise ValueError("factorize requires the analyzed finite CSC pattern")
            else:
                pass
        self._order: int = symbolic._order
        self._indptr: np.ndarray = symbolic._indptr
        self._indices: np.ndarray = symbolic._indices
        values: np.ndarray = np.asarray(matrix.data, dtype=np.float64)
        self._ordering_envelope: bool = symbolic._ordering_envelope
        self._tiny_dense: bool = symbolic._tiny_dense
        if self._tiny_dense:
            self._tiny_lu: np.ndarray = np.empty(self._order * self._order, dtype=np.float64)
            self._tiny_scales: np.ndarray = np.empty(self._order, dtype=np.float64)
            self._tiny_rows: np.ndarray = np.empty(self._order, dtype=np.int32)
            _factorize_tiny(values, self._order, pivot_tolerance, False,
                            self._tiny_lu, self._tiny_scales, self._tiny_rows)
            self._valid: bool = True
            return
        else:
            pass
        self._diagonal_pattern: bool = symbolic._diagonal_pattern
        if self._diagonal_pattern:
            self._diagonal_scales: np.ndarray = np.empty(self._order, dtype=np.float64)
            self._diagonal_scale_reciprocals: np.ndarray = np.empty(self._order, dtype=np.float64)
            self._diagonal_values: np.ndarray = np.empty(self._order, dtype=np.float64)
            self._diagonal_reciprocals: np.ndarray = np.empty(self._order, dtype=np.float64)
            self._diagonal_rhs_reciprocals: np.ndarray = np.empty(self._order, dtype=np.float64)
            self._diagonal_all_safe: bool = _factorize_diagonal(
                values, self._diagonal_scales, self._diagonal_scale_reciprocals,
                self._diagonal_values, self._diagonal_reciprocals,
                self._diagonal_rhs_reciprocals)
            self._valid = True
            return
        else:
            pass
        self._column_order: np.ndarray = symbolic._column_order
        self._block_offsets: np.ndarray = symbolic._block_offsets
        preferred_rows: np.ndarray = symbolic._preferred_rows
        self._scales: np.ndarray
        self._reciprocals: np.ndarray
        self._scales, self._reciprocals = _compute_row_scales(self._order, self._indices, values)
        self._diagonal: np.ndarray
        self._pivot_rows: np.ndarray
        self._row_positions: np.ndarray
        self._fixed_pattern_used: bool = False
        self._flat_lower_positions: np.ndarray = np.empty(0, dtype=np.int32)
        self._flat_lower_values: np.ndarray = np.empty(0, dtype=np.float64)
        self._flat_lower_offsets: np.ndarray = np.empty(0, dtype=np.int32)
        self._flat_upper_columns: np.ndarray = np.empty(0, dtype=np.int32)
        self._flat_upper_values: np.ndarray = np.empty(0, dtype=np.float64)
        self._flat_upper_offsets: np.ndarray = np.empty(0, dtype=np.int32)
        fixed_accepted: bool = False
        if symbolic._fixed_pattern_ready:
            lower_pattern: np.ndarray = symbolic._lower_flat
            lower_offsets: np.ndarray = symbolic._lower_offsets
            upper_pattern: np.ndarray = symbolic._upper_flat
            upper_offsets: np.ndarray = symbolic._upper_offsets
            fixed_positions: np.ndarray = symbolic._fixed_positions
            upper_block_starts: np.ndarray = _prepare_upper_block_starts_flat(
                upper_pattern, upper_offsets, self._block_offsets)
            self._lower_run_offsets: np.ndarray
            self._lower_runs: np.ndarray
            self._lower_run_offsets, self._lower_runs = _build_lower_runs(lower_pattern, lower_offsets)
            fixed_accepted, fixed_lower_values, fixed_upper_values, fixed_diagonal = _factorize_fixed_pattern_flat(
                self._indptr, self._indices, values, self._column_order,
                self._block_offsets, fixed_positions, lower_pattern, lower_offsets,
                upper_pattern, upper_offsets,
                upper_block_starts, self._lower_run_offsets, self._lower_runs,
                self._scales, self._reciprocals, pivot_tolerance)
            if fixed_accepted:
                self._flat_lower_positions = lower_pattern
                self._flat_lower_values = fixed_lower_values
                self._flat_lower_offsets = lower_offsets
                self._flat_upper_columns = upper_pattern
                self._flat_upper_values = fixed_upper_values
                self._flat_upper_offsets = upper_offsets
                self._diagonal = fixed_diagonal
                self._pivot_rows = preferred_rows
                self._row_positions = fixed_positions
                self._fixed_pattern_used = True
            else:
                pass
        else:
            pass
        if not fixed_accepted:
            self._lower_run_offsets = np.empty(0, dtype=np.int32)
            self._lower_runs = np.empty((0, 2), dtype=np.int32)
            capacity: int = max(16, values.size * 4)
            maximum_capacity: int = max(capacity, self._order * (self._order + 1) // 2)
            while True:
                try:
                    (self._flat_lower_positions, self._flat_lower_values, self._flat_lower_offsets,
                     self._flat_upper_columns, self._flat_upper_values, self._flat_upper_offsets,
                     self._diagonal, self._pivot_rows, self._row_positions) = _factorize_dynamic(
                        self._indptr, self._indices, values, self._column_order, preferred_rows,
                        self._block_offsets, self._scales, self._reciprocals, pivot_tolerance,
                        capacity)
                    break
                except OverflowError:
                    if capacity >= maximum_capacity:
                        raise
                    else:
                        capacity = min(maximum_capacity, capacity * 2)
        else:
            pass
        self._upper_block_starts: np.ndarray = _prepare_upper_block_starts_flat(
            self._flat_upper_columns, self._flat_upper_offsets, self._block_offsets)
        self._solve_rhs_reciprocals, self._all_solve_rhs_reciprocals_safe = _prepare_solve_rhs_reciprocals(
            self._pivot_rows, self._reciprocals)
        self._valid: bool = True

    def refactor(self, A: sp.spmatrix, workspace: Workspace | None = None) -> None:
        """Replay factors for values with exactly the saved CSC pattern.

        :param A: Same-pattern square CSC matrix with new finite values.
        :param workspace: Optional reusable numeric scratch.
        :return: Nothing.
        """
        if workspace is not None and (not isinstance(workspace, Workspace) or workspace.order != self._order):
            raise ValueError("workspace order must match matrix order")
        else:
            pass
        matrix: sp.csc_matrix = sp.csc_matrix(A, dtype=np.float64)
        if matrix.shape != (self._order, self._order) or not _valid_same_pattern(
                matrix.shape[0], matrix.indptr, matrix.indices, matrix.data,
                self._valid, self._order, self._indptr, self._indices):
            raise ValueError("refactor requires the original finite CSC pattern")
        else:
            pass
        if self._tiny_dense:
            try:
                _factorize_tiny(matrix.data, self._order, 0.0, True,
                                self._tiny_lu, self._tiny_scales, self._tiny_rows)
            except (FloatingPointError, np.linalg.LinAlgError):
                self._valid = False
                raise
            else:
                return
        else:
            pass
        if self._diagonal_pattern:
            try:
                self._diagonal_all_safe = _factorize_diagonal(
                    matrix.data, self._diagonal_scales, self._diagonal_scale_reciprocals,
                    self._diagonal_values, self._diagonal_reciprocals,
                    self._diagonal_rhs_reciprocals)
            except (FloatingPointError, np.linalg.LinAlgError):
                self._valid = False
                raise
            else:
                return
        else:
            pass
        self._scales, self._reciprocals = _compute_row_scales(self._order, self._indices, matrix.data)
        self._solve_rhs_reciprocals, self._all_solve_rhs_reciprocals_safe = _prepare_solve_rhs_reciprocals(
            self._pivot_rows, self._reciprocals)
        work: np.ndarray = workspace.work if workspace is not None else np.empty(self._order, dtype=np.float64)
        try:
            _refactor_numeric_flat(
                self._indptr, self._indices, matrix.data, self._column_order,
                self._block_offsets, self._flat_lower_positions, self._flat_lower_values,
                self._flat_lower_offsets, self._flat_upper_columns, self._flat_upper_values,
                self._flat_upper_offsets, self._diagonal, self._row_positions,
                self._scales, self._reciprocals, work)
        except (FloatingPointError, np.linalg.LinAlgError):
            self._valid = False
            raise
        else:
            pass

    def solve(self, b: np.ndarray, workspace: Workspace | None = None) -> np.ndarray:
        """Solve with retained factors.

        :param b: Finite right-hand side of factor order.
        :param workspace: Optional reusable pivot-order scratch.
        :return: Original-column-order solution.
        """
        if workspace is not None and (not isinstance(workspace, Workspace) or workspace.order != self._order):
            raise ValueError("workspace order must match factor order")
        else:
            pass
        if np.iscomplexobj(b):
            raise ValueError("right-hand side must be real")
        else:
            pass
        try:
            rhs: np.ndarray = np.asarray(b, dtype=np.float64)
        except (ValueError, TypeError, OverflowError):
            raise ValueError("right-hand side must be numeric")
        if rhs.shape != (self._order,) or not np.all(np.isfinite(rhs)):
            raise ValueError("right-hand side must be finite and match matrix order")
        else:
            pass
        if not self._valid:
            raise RuntimeError("factors are invalid")
        else:
            pass
        if self._tiny_dense:
            return _solve_tiny(self._tiny_lu, self._tiny_scales, self._tiny_rows, rhs)
        else:
            pass
        if self._diagonal_pattern:
            return _solve_diagonal(rhs, self._diagonal_scales,
                                   self._diagonal_scale_reciprocals,
                                   self._diagonal_values, self._diagonal_reciprocals,
                                   self._diagonal_rhs_reciprocals,
                                   self._diagonal_all_safe)
        else:
            pass
        work: np.ndarray = workspace.work if workspace is not None else np.empty(self._order, dtype=np.float64)
        return _solve_numeric_flat(
            self._flat_lower_positions, self._flat_lower_values,
            self._flat_lower_offsets, self._flat_upper_columns, self._flat_upper_values,
            self._flat_upper_offsets, self._diagonal, self._pivot_rows,
            self._column_order, self._block_offsets, self._upper_block_starts,
            self._scales, self._solve_rhs_reciprocals,
            self._all_solve_rhs_reciprocals_safe, rhs, work)


class Numeric:
    """CLU numeric factors tied to one analyzed CSC pattern."""

    __slots__ = ("_factorizer", "_statistics")

    def __init__(self) -> None:
        """Create invalid numeric state.

        :return: Nothing.
        """
        self._factorizer: _FactoredMatrix | None = None
        self._statistics: Statistics = Statistics()

    def is_valid(self) -> bool:
        """Return whether reusable factors exist.

        :return: Factor validity.
        """
        if self._factorizer is None:
            return False
        else:
            return self._factorizer._valid

    @property
    def statistics(self) -> Statistics:
        """Return factor counts and inherited analysis counters.

        :return: CLU statistics.
        """
        return self._statistics

    def lowerIndices(self) -> np.ndarray:
        """Return strict L row positions in factor order.

        :return: Flat strict L indices, or an empty array without sparse factors.
        """
        factors: _FactoredMatrix | None = self._factorizer
        if factors is None or factors._tiny_dense or factors._diagonal_pattern:
            return np.empty(0, dtype=np.int32)
        else:
            return factors._flat_lower_positions

    def lowerOffsets(self) -> np.ndarray:
        """Return half-open strict L column boundaries.

        :return: Order-plus-one offsets, or an empty array for tiny factors.
        """
        factors: _FactoredMatrix | None = self._factorizer
        if factors is None or factors._tiny_dense:
            return np.empty(0, dtype=np.int32)
        elif factors._diagonal_pattern:
            return np.zeros(factors._order + 1, dtype=np.int32)
        else:
            return factors._flat_lower_offsets

    def upperIndices(self) -> np.ndarray:
        """Return strict U row positions in factor order.

        :return: Flat strict U indices, or an empty array without sparse factors.
        """
        factors: _FactoredMatrix | None = self._factorizer
        if factors is None or factors._tiny_dense or factors._diagonal_pattern:
            return np.empty(0, dtype=np.int32)
        else:
            return factors._flat_upper_columns

    def upperOffsets(self) -> np.ndarray:
        """Return half-open strict U column boundaries.

        :return: Order-plus-one offsets, or an empty array for tiny factors.
        """
        factors: _FactoredMatrix | None = self._factorizer
        if factors is None or factors._tiny_dense:
            return np.empty(0, dtype=np.int32)
        elif factors._diagonal_pattern:
            return np.zeros(factors._order + 1, dtype=np.int32)
        else:
            return factors._flat_upper_offsets

    def upperBlockOffsets(self) -> np.ndarray:
        """Return the first within-block strict U entry per factor column.

        :return: Absolute entry offsets, or an empty array for direct factors.
        """
        factors: _FactoredMatrix | None = self._factorizer
        if factors is None or factors._tiny_dense or factors._diagonal_pattern:
            return np.empty(0, dtype=np.int32)
        elif factors._fixed_pattern_used and factors._block_offsets.size <= 2:
            return np.empty(0, dtype=np.int32)
        else:
            starts: np.ndarray = np.empty(factors._order + 1, dtype=np.int32)
            starts[:-1] = factors._upper_block_starts
            starts[-1] = factors._flat_upper_offsets[-1]
            return starts

    def pivotRows(self) -> np.ndarray:
        """Return the original row selected at each factor position.

        :return: Pivot permutation, or an empty array for tiny factors.
        """
        factors: _FactoredMatrix | None = self._factorizer
        if factors is None or factors._tiny_dense:
            return np.empty(0, dtype=np.int32)
        elif factors._diagonal_pattern:
            return np.arange(factors._order, dtype=np.int32)
        else:
            return factors._pivot_rows

    def rowPositions(self) -> np.ndarray:
        """Return the inverse original-row to factor-position map.

        :return: Inverse pivot permutation, or an empty array for tiny factors.
        """
        factors: _FactoredMatrix | None = self._factorizer
        if factors is None or factors._tiny_dense:
            return np.empty(0, dtype=np.int32)
        elif factors._diagonal_pattern:
            return np.arange(factors._order, dtype=np.int32)
        else:
            return factors._row_positions


def factorize(A: sp.spmatrix, symbolic: Symbolic, options: Options,
              numeric: Numeric) -> Status:
    """Factor values against saved analysis, choosing fresh pivots if needed.

    :param A: Matrix with the exact analyzed CSC pattern.
    :param symbolic: Successful structural analysis.
    :param options: Numerical pivot controls.
    :param numeric: Destination factors.
    :return: CLU status.
    """
    if not isinstance(symbolic, Symbolic) or not isinstance(options, Options) or not isinstance(numeric, Numeric):
        return Status.INVALID_INPUT
    else:
        pass
    numeric.__init__()
    try:
        matrix: sp.csc_matrix = sp.csc_matrix(A, dtype=np.float64)
        if not symbolic.is_valid() or not _valid_options(options.pivot_tolerance) or not isinstance(options.ordering, Ordering):
            return Status.INVALID_INPUT
        else:
            pass
        if not _valid_same_pattern(matrix.shape[0], matrix.indptr, matrix.indices,
                                   matrix.data, True, symbolic._order,
                                   symbolic._indptr, symbolic._indices):
            return Status.INVALID_INPUT
        else:
            pass
        factors: _FactoredMatrix = _FactoredMatrix(matrix, options.pivot_tolerance,
                                         options.ordering, options.use_block_triangular_form,
                                         options.symmetric_pattern, symbolic)
        statistics: Statistics = symbolic.statistics
        lower_count: int = 0
        upper_count: int = 0
        if factors._tiny_dense:
            lower_count = symbolic.order * (symbolic.order - 1) // 2
            upper_count = symbolic.order * (symbolic.order + 1) // 2
        elif factors._diagonal_pattern:
            upper_count = symbolic.order
        else:
            lower_count = factors._flat_lower_positions.size
            upper_count = symbolic.order + factors._flat_upper_columns.size
        numeric._factorizer = factors
        numeric._statistics = Statistics(statistics.order, statistics.nonzeros,
                                         statistics.blocks, statistics.largest_block,
                                         lower_count, upper_count)
        return Status.SUCCESS
    except MemoryError:
        return Status.OUT_OF_MEMORY
    except np.linalg.LinAlgError:
        return Status.SINGULAR
    except (FloatingPointError, ZeroDivisionError):
        return Status.NUMERICAL_FAILURE
    except (ValueError, TypeError, OverflowError):
        return Status.INVALID_INPUT
    except RuntimeError:
        return Status.NUMERICAL_FAILURE


def refactor(A: sp.spmatrix, symbolic: Symbolic, numeric: Numeric,
             workspace: Workspace | None = None) -> Status:
    """Replay saved pivots and factor structure with new matrix values.

    :param A: Matrix with the exact analyzed CSC pattern.
    :param symbolic: Analysis used for the original factorization.
    :param numeric: Factors to update in place.
    :param workspace: Optional order-bound caller scratch.
    :return: CLU status.
    """
    if not isinstance(symbolic, Symbolic) or not isinstance(numeric, Numeric) or not numeric.is_valid():
        return Status.INVALID_INPUT
    else:
        pass
    if workspace is not None and (not isinstance(workspace, Workspace) or workspace.order != symbolic.order):
        return Status.INVALID_INPUT
    else:
        pass
    try:
        matrix: sp.csc_matrix = sp.csc_matrix(A, dtype=np.float64)
        if not _valid_same_pattern(matrix.shape[0], matrix.indptr, matrix.indices,
                                   matrix.data, symbolic.is_valid(), symbolic._order,
                                   symbolic._indptr, symbolic._indices):
            return Status.INVALID_INPUT
        else:
            pass
        factors: _FactoredMatrix = numeric._factorizer
        factors.refactor(matrix, workspace)
        return Status.SUCCESS
    except MemoryError:
        numeric._factorizer = None
        return Status.OUT_OF_MEMORY
    except np.linalg.LinAlgError:
        numeric._factorizer = None
        return Status.SINGULAR
    except (FloatingPointError, ZeroDivisionError):
        numeric._factorizer = None
        return Status.NUMERICAL_FAILURE
    except (ValueError, TypeError, OverflowError):
        return Status.INVALID_INPUT
    except RuntimeError:
        numeric._factorizer = None
        return Status.NUMERICAL_FAILURE


def solve(A: sp.spmatrix | Numeric, b: np.ndarray,
          output: np.ndarray | float | None = None,
          workspace: Workspace | None = None,
          pivot_tolerance: float = 1e-3) -> np.ndarray | Status:
    """Solve a sparse system directly, or solve into an output using CLU factors.

    :param A: Sparse matrix or completed numeric factorization.
    :param b: Finite right-hand side.
    :param output: Writable output for numeric factors, or direct pivot tolerance.
    :param workspace: Optional order-bound scratch for numeric factors.
    :param pivot_tolerance: Relative pivot threshold for the direct form.
    :return: Solution for the direct form; status for the numeric form.
    """
    if isinstance(A, Numeric):
        if not A.is_valid() or not isinstance(output, np.ndarray):
            return Status.INVALID_INPUT
        else:
            pass
        factors: _FactoredMatrix = A._factorizer
        if np.iscomplexobj(b):
            return Status.INVALID_INPUT
        else:
            pass
        try:
            rhs: np.ndarray = np.asarray(b, dtype=np.float64)
        except (ValueError, TypeError, OverflowError):
            return Status.INVALID_INPUT
        if workspace is not None and (not isinstance(workspace, Workspace) or workspace.order != factors._order):
            return Status.INVALID_INPUT
        else:
            pass
        if (rhs.shape != (factors._order,) or output.shape != rhs.shape
                or output.dtype != np.float64 or not output.flags.writeable
                or not np.all(np.isfinite(rhs))):
            return Status.INVALID_INPUT
        else:
            pass
        try:
            result: np.ndarray = factors.solve(rhs, workspace)
            output[:] = result
            return Status.SUCCESS if np.all(np.isfinite(result)) else Status.NUMERICAL_FAILURE
        except (FloatingPointError, np.linalg.LinAlgError):
            return Status.NUMERICAL_FAILURE
    else:
        direct_tolerance: float = pivot_tolerance if output is None else float(output)
        factorizer: _FactoredMatrix = _FactoredMatrix(A, direct_tolerance)
        return factorizer.solve(b)


class BasicFactorizer:
    """Resident CLU solver with the C++ factorize, replay, and repivot lifecycle."""

    __slots__ = ("_matrix", "_options", "_symbolic", "_numeric", "_workspace")

    def __init__(self, A: sp.spmatrix | None = None,
                 options: Options | None = None) -> None:
        """Bind a matrix without analyzing or factoring it.

        :param A: Matrix whose CSC buffers remain bound until replaced.
        :param options: CLU ordering and pivot controls.
        :return: Nothing.
        """
        self._matrix: sp.csc_matrix | None = None if A is None else sp.csc_matrix(A)
        source: Options = Options() if options is None else options
        self._options: Options = Options(source.ordering, source.use_block_triangular_form,
                                        source.pivot_tolerance, source.symmetric_pattern)
        self._symbolic: Symbolic = Symbolic()
        self._numeric: Numeric = Numeric()
        self._workspace: Workspace = Workspace(0)

    def factorize(self, A: sp.spmatrix | None = None) -> Status:
        """Factor bound values, replaying old pivots before fresh pivoting.

        :param A: Optional same-pattern matrix with current values.
        :return: CLU status; failure invalidates resident factors.
        """
        if A is not None:
            try:
                self._matrix = sp.csc_matrix(A)
            except (ValueError, TypeError, OverflowError):
                self._numeric = Numeric()
                return Status.INVALID_INPUT
        else:
            pass
        if self._matrix is None:
            self._numeric = Numeric()
            return Status.INVALID_INPUT
        else:
            pass
        status: Status = Status.SUCCESS
        if not self._symbolic.is_valid():
            statistics: Statistics = Statistics()
            status = analyze(self._matrix, self._options, self._symbolic, statistics)
            if status is Status.SUCCESS:
                self._workspace = Workspace(self._matrix.shape[0])
            else:
                pass
        else:
            pass
        if status is Status.SUCCESS:
            if self._numeric.is_valid():
                status = refactor(self._matrix, self._symbolic, self._numeric,
                                  self._workspace)
                if status is Status.SINGULAR or status is Status.NUMERICAL_FAILURE:
                    status = factorize(self._matrix, self._symbolic, self._options,
                                       self._numeric)
                else:
                    pass
            else:
                status = factorize(self._matrix, self._symbolic, self._options,
                                   self._numeric)
        else:
            pass
        if status is not Status.SUCCESS:
            self._numeric = Numeric()
        else:
            pass
        return status

    def repivot(self, A: sp.spmatrix) -> Status:
        """Choose fresh pivots while retaining successful symbolic analysis.

        :param A: Same-pattern matrix with current values.
        :return: CLU status.
        """
        self._numeric = Numeric()
        return self.factorize(A)

    def refactor(self, A: sp.spmatrix | None = None) -> Status:
        """Replay retained pivots and invalidate factors after any failure.

        :param A: Optional same-pattern matrix with current values.
        :return: CLU status.
        """
        if A is not None:
            try:
                self._matrix = sp.csc_matrix(A)
            except (ValueError, TypeError, OverflowError):
                self._numeric = Numeric()
                return Status.INVALID_INPUT
        else:
            pass
        if self._matrix is None:
            self._numeric = Numeric()
            return Status.INVALID_INPUT
        else:
            pass
        status: Status = refactor(self._matrix, self._symbolic, self._numeric,
                                  self._workspace)
        if status is not Status.SUCCESS:
            self._numeric = Numeric()
        else:
            pass
        return status

    def solve(self, b: np.ndarray, output: np.ndarray) -> Status:
        """Solve with resident factors and scratch, permitting RHS aliasing.

        :param b: Finite right-hand side.
        :param output: Writable float64 solution array.
        :return: CLU status.
        """
        result: np.ndarray | Status = solve(self._numeric, b, output, self._workspace)
        if isinstance(result, Status):
            return result
        else:
            return Status.NUMERICAL_FAILURE

    def is_valid(self) -> bool:
        """Return whether a successful factorization is resident.

        :return: Factor validity.
        """
        return self._numeric.is_valid()

    @property
    def order(self) -> int:
        """Return the bound matrix order.

        :return: Number of rows in the bound CSC matrix.
        """
        if self._matrix is None:
            return 0
        else:
            return self._matrix.shape[0]

    @property
    def statistics(self) -> Statistics:
        """Return resident factor statistics.

        :return: Current numeric counters, or zeros before factorization.
        """
        return self._numeric.statistics


class Factorizer(BasicFactorizer):
    """Native CLU ``Factorizer`` alias with lazy resident semantics."""

    __slots__ = ()
