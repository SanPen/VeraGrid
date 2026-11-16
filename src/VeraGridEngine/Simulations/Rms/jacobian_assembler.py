# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Fixed-pattern assembly of implicit RMS Jacobians.

The Backward Euler Newton matrix of an RMS DAE is::

    | I - h*J11   -h*J12 |
    | J21          J22   |

For a semi-explicit BDF residual, the same block pattern gives::

    | c*I - J11   -J12 |
    | J21          J22 |

The compiled block Jacobians reuse fixed CSC templates, so the packed pattern of
this matrix does not change between Newton corrections. The assembler builds that
pattern and the scatter maps once and afterwards only rewrites the values, using
the same floating-point operations as the SciPy expression it replaces. Whenever
reusing the pattern could produce a different matrix (non-canonical or malformed
blocks, other formats, or an exactly zero value in the I - h*J11 block, which the
SciPy subtraction would drop), the SciPy expression itself is evaluated instead.

Midpoint and trapezoidal assemble directly from raw blocks on the same cached
pattern. Compatibility transforms also accept a complete Backward Euler matrix.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from numba import njit
from scipy.sparse import csc_matrix, spmatrix

from VeraGridEngine.Utils.Sparse.csc import pack_4_by_4_scipy


@njit(cache=True, fastmath=False)
def _fill_implicit_raw_direct(raw: np.ndarray, rows: np.ndarray,
                              diagonal: np.ndarray, h: float, n_states: int,
                              output: np.ndarray) -> None:
    """Fill identical CSC layouts without clearing or scattering entries."""
    for entry in range(raw.size):
        output[entry] = -h * raw[entry] if rows[entry] < n_states else raw[entry]
    for entry in range(diagonal.size):
        output[diagonal[entry]] += 1.0


@njit(cache=True, fastmath=False)
def _fill_implicit_raw(raw: np.ndarray, rows: np.ndarray, destinations: np.ndarray,
                       diagonal: np.ndarray, h: float, n_states: int,
                       output: np.ndarray) -> None:
    """Apply the Backward Euler chain to a cached full CSC pattern."""
    output[:] = 0.0
    for entry in range(raw.size):
        if rows[entry] < n_states:
            output[destinations[entry]] = -h * raw[entry]
        else:
            output[destinations[entry]] = raw[entry]
    for entry in range(diagonal.size):
        output[diagonal[entry]] += 1.0


@njit(cache=True, fastmath=False)
def _half_step_newton_data(data: np.ndarray, indices: np.ndarray, indptr: np.ndarray,
                           n_states: int, scale_algebraic: bool, output: np.ndarray) -> bool:
    """Transform a Backward Euler CSC matrix without changing its sparse pattern."""
    for column in range(indptr.size - 1):
        diagonal_found = column >= n_states
        for position in range(indptr[column], indptr[column + 1]):
            row = indices[position]
            if row < n_states or scale_algebraic:
                output[position] = 0.5 * data[position]
            else:
                output[position] = data[position]
            if column < n_states and row == column:
                output[position] += 0.5
                diagonal_found = True
        if not diagonal_found:
            return False
    return True


@njit(cache=True, fastmath=False)
def _fill_midpoint_blocks(base: np.ndarray, output: np.ndarray, half_h: float,
                          map_j11: np.ndarray, map_j12: np.ndarray,
                          map_j21: np.ndarray, map_j22: np.ndarray,
                          j11: np.ndarray, j12: np.ndarray,
                          j21: np.ndarray, j22: np.ndarray) -> None:
    """Fill midpoint CSC data from the cached block scatter positions."""
    output[:] = base
    for entry in range(j11.size):
        position = map_j11[entry]
        output[position] = base[position] - half_h * j11[entry]
    for entry in range(j12.size):
        output[map_j12[entry]] = -half_h * j12[entry]
    for entry in range(j21.size):
        output[map_j21[entry]] = 0.5 * j21[entry]
    for entry in range(j22.size):
        output[map_j22[entry]] = 0.5 * j22[entry]


@njit(cache=True, fastmath=False)
def _fill_trapezoidal_blocks(base: np.ndarray, output: np.ndarray, half_h: float,
                             map_j11: np.ndarray, map_j12: np.ndarray,
                             map_j21: np.ndarray, map_j22: np.ndarray,
                             j11: np.ndarray, j12: np.ndarray,
                             j21: np.ndarray, j22: np.ndarray) -> None:
    """Fill trapezoidal CSC data from the cached block scatter positions."""
    output[:] = base
    for entry in range(j11.size):
        position = map_j11[entry]
        output[position] = base[position] - half_h * j11[entry]
    for entry in range(j12.size):
        output[map_j12[entry]] = -half_h * j12[entry]
    for entry in range(j21.size):
        output[map_j21[entry]] = j21[entry]
    for entry in range(j22.size):
        output[map_j22[entry]] = j22[entry]


@njit(cache=True, fastmath=False)
def _fill_bdf_blocks(base: np.ndarray, output: np.ndarray, c: float,
                     region: np.ndarray, map_j11: np.ndarray,
                     map_j12: np.ndarray, map_j21: np.ndarray,
                     map_j22: np.ndarray, j11: np.ndarray, j12: np.ndarray,
                     j21: np.ndarray, j22: np.ndarray) -> bool:
    """Fill BDF CSC data on the cached pattern and detect dropped diagonals."""
    for entry in range(region.size):
        position = region[entry]
        output[position] = c * base[position]
    for entry in range(j11.size):
        position = map_j11[entry]
        output[position] = c * base[position] - j11[entry]
    for entry in range(j12.size):
        output[map_j12[entry]] = -j12[entry]
    for entry in range(j21.size):
        output[map_j21[entry]] = j21[entry]
    for entry in range(j22.size):
        output[map_j22[entry]] = j22[entry]
    for entry in range(region.size):
        if output[region[entry]] == 0.0:
            return False
    return True


@njit(cache=True, fastmath=False)
def _fill_projected_block(direct: np.ndarray, direct_destinations: np.ndarray,
                          derivative: np.ndarray, derivative_sources: np.ndarray,
                          derivative_destinations: np.ndarray, chain_positions: np.ndarray,
                          chain_values: np.ndarray, derivative_scale: float,
                          output: np.ndarray) -> None:
    """Fill one cached raw block plus its derivative-column contributions."""
    output[:] = 0.0
    for entry in range(direct.size):
        output[direct_destinations[entry]] += direct[entry]
    for entry in range(derivative_sources.size):
        output[derivative_destinations[entry]] += (
            derivative_scale * derivative[derivative_sources[entry]]
            * chain_values[chain_positions[entry]])


def _assemble_half_step_from_newton(n_states: int, newton: csc_matrix,
                                    scale_algebraic: bool) -> csc_matrix:
    """Derive a midpoint or trapezoidal Newton matrix from the full BE matrix."""
    if not sp.isspmatrix_csc(newton):
        newton = newton.tocsc()
    if n_states < 0 or n_states > min(newton.shape):
        raise ValueError("Invalid state count for the Newton matrix")
    if (newton.dtype == np.float64 and
            _csc_storage_is_consistent(newton.indptr, newton.indices, newton.data, newton.shape) and
            _csc_pattern_is_canonical(newton.indptr, newton.indices, newton.shape[0])):
        data = np.empty_like(newton.data)
        if _half_step_newton_data(newton.data, newton.indices, newton.indptr,
                                  n_states, scale_algebraic, data):
            return csc_matrix((data, newton.indices.copy(), newton.indptr.copy()), shape=newton.shape)

    # Missing identity positions or irregular CSC storage need sparse addition.
    result = newton.copy()
    if scale_algebraic:
        result.data *= 0.5
    else:
        result.data[result.indices < n_states] *= 0.5
    if n_states:
        result += sp.diags(
            np.r_[np.full(n_states, 0.5), np.zeros(result.shape[0] - n_states)],
            format="csc",
        )
    return result.tocsc()


def _csc_storage_is_consistent(indptr: np.ndarray, indices: np.ndarray, data: np.ndarray, shape: tuple[int, int]) -> bool:
    """
    Check that CSC arrays describe exactly nnz stored entries of the given shape.

    :param indptr: Column pointer array.
    :param indices: Row index array.
    :param data: Value array.
    :param shape: Matrix shape (rows, columns).
    :return: True when len(indptr) == columns + 1, indptr[0] == 0 and data and indices hold indptr[-1] entries.
    """
    consistent: bool = int(indptr.shape[0]) == int(shape[1]) + 1
    if consistent:
        consistent = int(indptr[0]) == 0 and int(data.shape[0]) == int(indices.shape[0]) == int(indptr[-1])
    else:
        pass
    return consistent


def _csc_pattern_is_canonical(indptr: np.ndarray, indices: np.ndarray, n_rows: int) -> bool:
    """
    Check from the arrays that a CSC pattern is canonical and in range.

    SciPy's cached has_canonical_format flag is not used because it does not follow
    in-place rewrites of the index arrays.

    :param indptr: Column pointer array (storage already checked as consistent).
    :param indices: Row index array.
    :param n_rows: Number of rows.
    :return: True when indptr is non-decreasing, every row index is within [0, n_rows)
        and row indices strictly increase inside every column.
    """
    canonical: bool = bool(np.all(np.diff(indptr) >= 0))
    nnz: int = int(indptr[-1])
    if canonical and nnz > 0:
        canonical = int(indices.min()) >= 0 and int(indices.max()) < n_rows
    else:
        pass
    if canonical and nnz > 1:
        # A non-increasing step between consecutive entries is only allowed where a new column starts.
        column_start: np.ndarray = np.zeros(nnz - 1, dtype=bool)
        starts: np.ndarray = indptr[1:-1]
        inner_starts: np.ndarray = starts[(starts > 0) & (starts < nnz)]
        column_start[inner_starts - 1] = True
        canonical = bool(np.all((np.diff(indices) > 0) | column_start))
    else:
        pass
    return canonical


class JacobianAssembler:
    """
    Assemble RMS DAE Jacobians as sparse CSC matrices.

    Block-based Backward Euler, BDF, midpoint and trapezoidal assembly cache the
    packed CSC pattern. Compatibility transforms accept a complete matrix.
    Block indices are checked on every call, so in-place pattern changes rebuild
    the scatter maps.
    Full raw matrices may opt into immutable structure per matrix object to
    avoid repeated pattern checks; a new object triggers validation again.
    """

    __slots__ = (
        "_has_pattern",
        "_block_shapes",
        "_block_indices",
        "_block_indptr",
        "_shape",
        "_indices",
        "_indptr",
        "_map_j11",
        "_map_j12",
        "_map_j21",
        "_map_j22",
        "_region",
        "_base",
        "_values",
        "_pattern_builds",
        "_fast_assemblies",
        "_fallback_assemblies",
        "_projection_patterns",
        "_projection_specs",
        "_projection_matrices",
        "_projection_builds",
        "_projection_fills",
        "_raw_implicit_pattern",
        "_raw_implicit_indices",
        "_raw_implicit_indptr",
        "_raw_implicit_matrix",
        "_raw_implicit_destinations",
        "_raw_implicit_diagonal",
        "_raw_implicit_states",
        "_raw_implicit_direct",
        "_raw_implicit_fixed",
    )

    def __init__(self) -> None:
        """
        Create an assembler without a pattern; the first eligible call builds it.
        """
        self._has_pattern: bool = False
        self._raw_implicit_pattern = None
        self._raw_implicit_indices = None
        self._raw_implicit_indptr = None
        self._raw_implicit_matrix = None
        self._raw_implicit_destinations = None
        self._raw_implicit_diagonal = None
        self._raw_implicit_states = None
        self._raw_implicit_direct = False
        self._raw_implicit_fixed = False
        self._block_shapes: list[tuple[int, int]] = list()
        self._block_indices: list[np.ndarray] = list()
        self._block_indptr: list[np.ndarray] = list()
        self._shape: tuple[int, int] = (0, 0)
        self._indices: np.ndarray = np.zeros(0, dtype=np.int32)
        self._indptr: np.ndarray = np.zeros(1, dtype=np.int32)
        self._map_j11: np.ndarray = np.zeros(0, dtype=np.int64)
        self._map_j12: np.ndarray = np.zeros(0, dtype=np.int64)
        self._map_j21: np.ndarray = np.zeros(0, dtype=np.int64)
        self._map_j22: np.ndarray = np.zeros(0, dtype=np.int64)
        self._region: np.ndarray = np.zeros(0, dtype=np.int64)
        self._base: np.ndarray = np.zeros(0, dtype=np.float64)
        self._values: np.ndarray = np.zeros(0, dtype=np.float64)
        self._pattern_builds: int = 0
        self._fast_assemblies: int = 0
        self._fallback_assemblies: int = 0
        self._projection_patterns = None
        self._projection_specs = None
        self._projection_matrices = None
        self._projection_builds = 0
        self._projection_fills = 0

    def assemble_jacobian_implicit_raw(self, n_states: int, h: float,
                                       raw: csc_matrix, *, fixed_pattern: bool = False) -> csc_matrix:
        """Discretize raw derivatives on cached CSC storage.

        With fixed_pattern, callers guarantee immutable structure for each
        matrix object and supply a new object for any structural change.
        """
        if (fixed_pattern and self._raw_implicit_fixed and
                raw is self._raw_implicit_pattern and
                n_states == self._raw_implicit_states):
            if self._raw_implicit_direct:
                _fill_implicit_raw_direct(raw.data, raw.indices, self._raw_implicit_diagonal,
                                          h, n_states, self._raw_implicit_matrix.data)
            else:
                _fill_implicit_raw(raw.data, raw.indices, self._raw_implicit_destinations,
                                   self._raw_implicit_diagonal, h, n_states,
                                   self._raw_implicit_matrix.data)
            self._fast_assemblies += 1
            return self._raw_implicit_matrix
        if not sp.isspmatrix_csc(raw):
            raw = raw.tocsc()
        if not 0 <= n_states <= min(raw.shape):
            raise ValueError("Invalid state count for the raw equation Jacobian")
        if not raw.has_canonical_format:
            raw = raw.copy()
            raw.sum_duplicates()
            raw.sort_indices()
        cached = self._raw_implicit_pattern
        if (cached is None or cached.shape != raw.shape or
                self._raw_implicit_states != n_states or
                self._raw_implicit_matrix is None or
                not np.array_equal(raw.indices, self._raw_implicit_indices) or
                not np.array_equal(raw.indptr, self._raw_implicit_indptr)):
            pattern = raw.copy()
            pattern.data[:] = 1.0
            if n_states:
                positions = np.arange(n_states)
                identity = csc_matrix((np.ones(n_states), (positions, positions)),
                                      shape=raw.shape)
                pattern = (pattern + identity).tocsc()
            pattern.data[:] = 0.0
            destinations = np.empty(raw.nnz, dtype=np.int64)
            for column in range(raw.shape[1]):
                start, stop = pattern.indptr[column:column + 2]
                rows = pattern.indices[start:stop]
                for entry in range(raw.indptr[column], raw.indptr[column + 1]):
                    destinations[entry] = start + np.searchsorted(rows, raw.indices[entry])
            diagonal = np.empty(n_states, dtype=np.int64)
            for column in range(n_states):
                start, stop = pattern.indptr[column:column + 2]
                diagonal[column] = start + np.searchsorted(pattern.indices[start:stop], column)
            self._raw_implicit_pattern = raw
            self._raw_implicit_indices = raw.indices.copy()
            self._raw_implicit_indptr = raw.indptr.copy()
            self._raw_implicit_matrix = pattern
            self._raw_implicit_destinations = destinations
            self._raw_implicit_diagonal = diagonal
            self._raw_implicit_states = n_states
            self._raw_implicit_direct = pattern.nnz == raw.nnz
            self._pattern_builds += 1
        self._raw_implicit_pattern = raw
        self._raw_implicit_fixed = fixed_pattern
        if self._raw_implicit_direct:
            _fill_implicit_raw_direct(raw.data, raw.indices, self._raw_implicit_diagonal,
                                      h, n_states, self._raw_implicit_matrix.data)
        else:
            _fill_implicit_raw(raw.data, raw.indices, self._raw_implicit_destinations,
                               self._raw_implicit_diagonal, h, n_states,
                               self._raw_implicit_matrix.data)
        self._fast_assemblies += 1
        return self._raw_implicit_matrix

    def get_projection_build_count(self) -> int:
        """Return the number of derivative-column map builds."""
        return self._projection_builds

    def get_projection_fill_count(self) -> int:
        """Return the number of evaluations using the cached projection map."""
        return self._projection_fills

    def get_pattern_build_count(self) -> int:
        """
        Return how many times the packed pattern and scatter maps were built.

        :return: Number of pattern builds.
        """
        return self._pattern_builds

    def get_fast_assembly_count(self) -> int:
        """
        Return how many matrices were assembled on the reusable pattern.

        :return: Number of fast assemblies.
        """
        return self._fast_assemblies

    def get_fallback_assembly_count(self) -> int:
        """
        Return how many matrices were assembled with the SciPy expression.

        :return: Number of fallback assemblies.
        """
        return self._fallback_assemblies

    @staticmethod
    def assemble_jacobian_midpoint(n_states: int, newton: csc_matrix) -> csc_matrix:
        """Return the midpoint matrix from a complete Backward Euler Newton matrix."""
        return _assemble_half_step_from_newton(n_states, newton, scale_algebraic=True)

    @staticmethod
    def assemble_jacobian_trapezoidal(n_states: int, newton: csc_matrix) -> csc_matrix:
        """Return the trapezoidal matrix, retaining the endpoint algebraic rows."""
        return _assemble_half_step_from_newton(n_states, newton, scale_algebraic=False)

    def assemble_jacobian_midpoint_blocks(self, ns: int, h: float, j11: spmatrix,
                                          j12: spmatrix, j21: spmatrix,
                                          j22: spmatrix) -> csc_matrix:
        """Assemble midpoint directly from equation blocks on the cached pattern."""
        return self._assemble_half_step_blocks(ns, h, j11, j12, j21, j22, midpoint=True)

    def assemble_jacobian_trapezoidal_blocks(self, ns: int, h: float, j11: spmatrix,
                                             j12: spmatrix, j21: spmatrix,
                                             j22: spmatrix) -> csc_matrix:
        """Assemble the trapezoidal endpoint matrix on the cached pattern."""
        return self._assemble_half_step_blocks(ns, h, j11, j12, j21, j22, midpoint=False)

    def _assemble_half_step_blocks(self, ns: int, h: float, j11: spmatrix,
                                   j12: spmatrix, j21: spmatrix, j22: spmatrix,
                                   midpoint: bool) -> csc_matrix:
        """Use one native fill on the cached pattern, with a sparse fallback."""
        if self._blocks_are_eligible(ns, j11, j12, j21, j22):
            ready = self._pattern_matches(j11, j12, j21, j22)
            if not ready:
                ready = self._build_pattern(ns, j11, j12, j21, j22)
            if ready:
                fill = _fill_midpoint_blocks if midpoint else _fill_trapezoidal_blocks
                fill(self._base, self._values, 0.5 * h,
                     self._map_j11, self._map_j12, self._map_j21, self._map_j22,
                     j11.data, j12.data, j21.data, j22.data)
                if not bool(np.any(self._values[self._region] == 0.0)):
                    self._fast_assemblies += 1
                    return csc_matrix((self._values.copy(), self._indices.copy(),
                                       self._indptr.copy()), shape=self._shape)
        self._fallback_assemblies += 1
        identity = sp.eye(ns, format="csc")
        half_h = 0.5 * h
        if midpoint:
            return pack_4_by_4_scipy((identity - half_h * j11).tocsc(),
                                      -half_h * j12, 0.5 * j21, 0.5 * j22)
        return pack_4_by_4_scipy((identity - half_h * j11).tocsc(),
                                  -half_h * j12, j21, j22)

    def assemble_jacobian_implicit(self, ns: int, h: float, j11: spmatrix, j12: spmatrix,
                                   j21: spmatrix, j22: spmatrix) -> csc_matrix:
        """
        Assemble [[I - h*J11, -h*J12], [J21, J22]].

        The result is identical to pack_4_by_4_scipy((sp.eye(ns) - h*J11).tocsc(), -h*J12, J21, J22):
        same canonical pattern, int32 index arrays and the same bits in every value.

        :param ns: Number of states, which is the size of the square J11 block.
        :param h: Integration step.
        :param j11: State-equation Jacobian with respect to the states.
        :param j12: State-equation Jacobian with respect to the algebraic variables.
        :param j21: Algebraic-equation Jacobian with respect to the states.
        :param j22: Algebraic-equation Jacobian with respect to the algebraic variables.
        :return: New CSC matrix owning its data, indices and indptr.
        """
        result: csc_matrix
        if self._blocks_are_eligible(ns, j11, j12, j21, j22):
            # Reuse the stored pattern when every block still has it; otherwise verify the
            # blocks from their arrays and build a new pattern for them.
            pattern_ready: bool = self._pattern_matches(j11, j12, j21, j22)
            if pattern_ready:
                pass
            else:
                pattern_ready = self._build_pattern(ns, j11, j12, j21, j22)
            if pattern_ready:
                result = self._assemble_on_pattern(ns, h, j11, j12, j21, j22)
            else:
                result = self._assemble_with_scipy(ns, h, j11, j12, j21, j22)
        else:
            result = self._assemble_with_scipy(ns, h, j11, j12, j21, j22)
        return result

    def assemble_jacobian_implicit_partials(
            self, ns: int, h: float, j11: spmatrix, j12: spmatrix,
            j13: spmatrix, j21: spmatrix, j22: spmatrix,
            j23: spmatrix, derivative_chain: spmatrix) -> csc_matrix:
        """Project independent derivative columns, then assemble Backward Euler.

        ``derivative_chain`` holds d(dx)/d(x_next), including each derivative's
        inverse step factor. The existing four-block CSC pattern cache remains
        responsible for the final Newton matrix.
        """
        j11, j12, j21, j22 = self.project_derivative_partials(
            ns, j11, j12, j13, j21, j22, j23, derivative_chain)
        if ns == 0:
            return j22
        return self.assemble_jacobian_implicit(ns, h, j11, j12, j21, j22)

    def project_derivative_partials(
            self, ns: int, j11: spmatrix, j12: spmatrix, j13: spmatrix,
            j21: spmatrix, j22: spmatrix, j23: spmatrix,
            derivative_chain: spmatrix, derivative_scale: float = 1.0
    ) -> tuple[csc_matrix, csc_matrix, csc_matrix, csc_matrix]:
        """Project raw partials using cached CSC positions when patterns are stable.

        Cached results are borrowed matrices; a later projection overwrites their
        numeric data. Irregular sparse inputs use ordinary sparse multiplication.
        """
        inputs = (j11, j12, j13, j21, j22, j23, derivative_chain)
        n_vars = j11.shape[1] + j12.shape[1]
        valid = (j11.shape == (ns, ns) and j12.shape[0] == ns
                 and j21.shape[1] == ns
                 and j22.shape == (j21.shape[0], j12.shape[1])
                 and j13.shape == (ns, derivative_chain.shape[0])
                 and j23.shape == (j21.shape[0], derivative_chain.shape[0])
                 and derivative_chain.shape[1] == n_vars)
        for matrix in inputs:
            if not valid:
                break
            valid = (sp.isspmatrix_csc(matrix) and matrix.dtype == np.float64
                     and _csc_storage_is_consistent(matrix.indptr, matrix.indices,
                                                    matrix.data, matrix.shape)
                     and _csc_pattern_is_canonical(matrix.indptr, matrix.indices,
                                                   matrix.shape[0]))
        if valid:
            patterns = tuple((matrix.shape, matrix.indices, matrix.indptr)
                             for matrix in inputs)
            matches = self._projection_patterns is not None and all(
                shape == old_shape and np.array_equal(indices, old_indices)
                and np.array_equal(indptr, old_indptr)
                for (shape, indices, indptr), (old_shape, old_indices, old_indptr)
                in zip(patterns, self._projection_patterns))
            if not matches:
                self._build_derivative_projection(ns, inputs)
            direct_blocks = (j11, j12, j21, j22)
            derivative_blocks = (j13, j13, j23, j23)
            for direct, derivative, spec, projected in zip(
                    direct_blocks, derivative_blocks,
                    self._projection_specs, self._projection_matrices):
                direct_dest, derivative_sources, derivative_dest, chain_positions = spec
                _fill_projected_block(
                    direct.data, direct_dest, derivative.data, derivative_sources,
                    derivative_dest, chain_positions, derivative_chain.data,
                    derivative_scale, projected.data)
            self._projection_fills += 1
            return self._projection_matrices
        scaled_chain = derivative_scale * derivative_chain
        state_chain = (j13 @ scaled_chain).tocsc()
        algebraic_chain = (j23 @ scaled_chain).tocsc()
        return ((j11 + state_chain[:, :ns]).tocsc(),
                (j12 + state_chain[:, ns:]).tocsc(),
                (j21 + algebraic_chain[:, :ns]).tocsc(),
                (j22 + algebraic_chain[:, ns:]).tocsc())

    def _build_derivative_projection(self, ns: int, inputs: tuple[spmatrix, ...]) -> None:
        """Build maps from six raw CSC blocks to four projected CSC blocks."""
        j11, j12, j13, j21, j22, j23, chain = inputs
        targets = [[] for _ in range(chain.shape[0])]
        for column in range(chain.shape[1]):
            for position in range(chain.indptr[column], chain.indptr[column + 1]):
                targets[int(chain.indices[position])].append((column, position))
        specs = []
        matrices = []
        for direct, derivative, first_column, last_column in (
                (j11, j13, 0, ns), (j12, j13, ns, chain.shape[1]),
                (j21, j23, 0, ns), (j22, j23, ns, chain.shape[1])):
            n_rows, n_columns = direct.shape
            direct_columns = np.repeat(np.arange(n_columns, dtype=np.int64),
                                       np.diff(direct.indptr))
            direct_keys = direct_columns * n_rows + direct.indices
            derivative_sources = []
            chain_positions = []
            derivative_keys = []
            for derivative_column in range(derivative.shape[1]):
                for source in range(derivative.indptr[derivative_column],
                                    derivative.indptr[derivative_column + 1]):
                    row = int(derivative.indices[source])
                    for column, chain_position in targets[derivative_column]:
                        if first_column <= column < last_column:
                            derivative_sources.append(source)
                            chain_positions.append(chain_position)
                            derivative_keys.append((column - first_column) * n_rows + row)
            keys = np.unique(np.concatenate((direct_keys,
                                             np.asarray(derivative_keys, dtype=np.int64))))
            indices = (keys % n_rows).astype(np.int32) if n_rows else np.empty(0, dtype=np.int32)
            indptr = np.zeros(n_columns + 1, dtype=np.int32)
            if n_rows:
                indptr[1:] = np.cumsum(np.bincount(keys // n_rows,
                                                  minlength=n_columns)).astype(np.int32)
            matrices.append(csc_matrix((np.zeros(keys.size), indices, indptr),
                                       shape=direct.shape))
            specs.append((np.searchsorted(keys, direct_keys),
                          np.asarray(derivative_sources, dtype=np.int64),
                          np.searchsorted(keys, derivative_keys),
                          np.asarray(chain_positions, dtype=np.int64)))
        self._projection_patterns = tuple(
            (matrix.shape, matrix.indices.copy(), matrix.indptr.copy())
            for matrix in inputs)
        self._projection_specs = tuple(specs)
        self._projection_matrices = tuple(matrices)
        self._projection_builds += 1

    def assemble_jacobian_midpoint_partials(
            self, ns: int, h: float, j11: spmatrix, j12: spmatrix,
            j13: spmatrix, j21: spmatrix, j22: spmatrix, j23: spmatrix,
            derivative_chain: spmatrix) -> csc_matrix:
        """Midpoint halves direct state dependence but not derivative input dependence."""
        blocks = self.project_derivative_partials(
            ns, j11, j12, j13, j21, j22, j23, derivative_chain, 2.0)
        if ns == 0:
            return (0.5 * blocks[3]).tocsc()
        return self.assemble_jacobian_midpoint_blocks(ns, h, *blocks)

    def assemble_jacobian_trapezoidal_partials(
            self, ns: int, h: float, j11: spmatrix, j12: spmatrix,
            j13: spmatrix, j21: spmatrix, j22: spmatrix, j23: spmatrix,
            derivative_chain: spmatrix) -> csc_matrix:
        """Project endpoint derivative inputs before trapezoidal assembly."""
        blocks = self.project_derivative_partials(
            ns, j11, j12, j13, j21, j22, j23, derivative_chain)
        if ns == 0:
            return blocks[3]
        return self.assemble_jacobian_trapezoidal_blocks(ns, h, *blocks)

    def assemble_jacobian_bdf_partials(
            self, ns: int, alpha: float, j11: spmatrix, j12: spmatrix,
            j13: spmatrix, j21: spmatrix, j22: spmatrix, j23: spmatrix,
            derivative_chain: spmatrix) -> csc_matrix:
        """Project BDF derivative inputs using the current trial coefficient."""
        blocks = self.project_derivative_partials(
            ns, j11, j12, j13, j21, j22, j23, derivative_chain, alpha)
        if ns == 0:
            return blocks[3]
        return self.assemble_jacobian_bdf(ns, alpha, *blocks)

    def assemble_jacobian_bdf(self, ns: int, c: float, j11: spmatrix, j12: spmatrix,
                              j21: spmatrix, j22: spmatrix) -> csc_matrix:
        """Assemble the semi-explicit DAE Newton matrix for a BDF step.

        The blocks are ``[[c*I - J11, -J12], [J21, J22]]``. ``c`` is the
        coefficient of the current trial state in the BDF derivative.
        Existing block-pattern checks and scatter maps are reused.
        """
        if self._blocks_are_eligible(ns, j11, j12, j21, j22):
            ready = self._pattern_matches(j11, j12, j21, j22)
            if not ready:
                ready = self._build_pattern(ns, j11, j12, j21, j22)
            if ready:
                values = self._values
                if _fill_bdf_blocks(self._base, values, c, self._region,
                                    self._map_j11, self._map_j12, self._map_j21,
                                    self._map_j22, j11.data, j12.data,
                                    j21.data, j22.data):
                    self._fast_assemblies += 1
                    return csc_matrix((values.copy(), self._indices.copy(),
                                       self._indptr.copy()), shape=self._shape)
        self._fallback_assemblies += 1
        return pack_4_by_4_scipy(
            (c * sp.eye(ns, format="csc") - j11).tocsc(),
            -j12, j21, j22,
        )

    def _blocks_are_eligible(self, ns: int, j11: spmatrix, j12: spmatrix, j21: spmatrix, j22: spmatrix) -> bool:
        """
        Check the formats, value types, shapes and storage consistency required by the fast path.

        :param ns: Number of states.
        :param j11: State/state block.
        :param j12: State/algebraic block.
        :param j21: Algebraic/state block.
        :param j22: Algebraic/algebraic block.
        :return: True when the four blocks can be read as CSC arrays of the expected shapes.
        """
        eligible: bool = ns >= 1
        block: spmatrix
        for block in (j11, j12, j21, j22):
            if eligible and sp.isspmatrix_csc(block) and block.dtype == np.float64:
                eligible = _csc_storage_is_consistent(block.indptr, block.indices, block.data, block.shape)
            else:
                eligible = False
        if eligible:
            # The blocks must tile the packed matrix exactly, as pack_4_by_4_scipy requires.
            eligible = (j11.shape == (ns, ns) and j12.shape[0] == ns and j21.shape[1] == ns
                        and j22.shape == (j21.shape[0], j12.shape[1]))
        else:
            pass
        return eligible

    def _pattern_matches(self, j11: csc_matrix, j12: csc_matrix, j21: csc_matrix, j22: csc_matrix) -> bool:
        """
        Compare the current block patterns element-wise with the verified stored copies.

        :param j11: State/state block.
        :param j12: State/algebraic block.
        :param j21: Algebraic/state block.
        :param j22: Algebraic/algebraic block.
        :return: True when a pattern exists and every block shape, indices and indptr are unchanged.
        """
        matches: bool = self._has_pattern
        position: int
        block: csc_matrix
        for position, block in enumerate((j11, j12, j21, j22)):
            if matches:
                matches = (block.shape == self._block_shapes[position]
                           and np.array_equal(block.indptr, self._block_indptr[position])
                           and np.array_equal(block.indices, self._block_indices[position]))
            else:
                pass
        return matches

    def _build_pattern(self, ns: int, j11: csc_matrix, j12: csc_matrix, j21: csc_matrix, j22: csc_matrix) -> bool:
        """
        Build the packed canonical pattern and the scatter maps of the four blocks.

        :param ns: Number of states.
        :param j11: State/state block.
        :param j12: State/algebraic block.
        :param j21: Algebraic/state block.
        :param j22: Algebraic/algebraic block.
        :return: True when the blocks are canonical and the pattern was built; False to use the SciPy expression.
        """
        blocks: tuple[csc_matrix, csc_matrix, csc_matrix, csc_matrix] = (j11, j12, j21, j22)
        canonical: bool = True
        block: csc_matrix
        for block in blocks:
            if canonical:
                canonical = _csc_pattern_is_canonical(block.indptr, block.indices, int(block.shape[0]))
            else:
                pass
        built: bool
        if canonical:
            n_rows: int = ns + int(j21.shape[0])
            n_cols: int = ns + int(j12.shape[1])

            # Global (row, column) coordinates of every stored block entry plus the identity diagonal,
            # encoded as column-major keys so that sorted unique keys give the canonical CSC order.
            row_offsets: tuple[int, int, int, int] = (0, 0, ns, ns)
            col_offsets: tuple[int, int, int, int] = (0, ns, 0, ns)
            key_parts: list[np.ndarray] = list()
            position: int
            for position, block in enumerate(blocks):
                columns: np.ndarray = np.repeat(np.arange(int(block.shape[1]), dtype=np.int64), np.diff(block.indptr))
                rows: np.ndarray = block.indices.astype(np.int64)
                key_parts.append((columns + col_offsets[position]) * n_rows + (rows + row_offsets[position]))
            diagonal: np.ndarray = np.arange(ns, dtype=np.int64)
            key_parts.append(diagonal * n_rows + diagonal)
            keys: np.ndarray = np.unique(np.concatenate(key_parts))

            # Canonical packed pattern with the int32 index arrays produced by pack_4_by_4_scipy.
            self._indices = (keys % n_rows).astype(np.int32)
            self._indptr = np.zeros(n_cols + 1, dtype=np.int32)
            self._indptr[1:] = np.cumsum(np.bincount(keys // n_rows, minlength=n_cols)).astype(np.int32)
            self._shape = (n_rows, n_cols)

            # Position of each block entry in the packed value array.
            self._map_j11 = np.searchsorted(keys, key_parts[0])
            self._map_j12 = np.searchsorted(keys, key_parts[1])
            self._map_j21 = np.searchsorted(keys, key_parts[2])
            self._map_j22 = np.searchsorted(keys, key_parts[3])
            diagonal_positions: np.ndarray = np.searchsorted(keys, key_parts[4])

            # The I - h*J11 block: 1.0 on the diagonal and 0.0 elsewhere before subtracting h*J11,
            # exactly the operands of the SciPy subtraction.
            self._region = np.union1d(self._map_j11, diagonal_positions)
            self._base = np.zeros(keys.shape[0], dtype=np.float64)
            self._base[diagonal_positions] = 1.0
            self._values = np.zeros(keys.shape[0], dtype=np.float64)

            # Verified copies of the block patterns for the element-wise reuse check.
            self._block_shapes = [(int(b.shape[0]), int(b.shape[1])) for b in blocks]
            self._block_indices = [b.indices.copy() for b in blocks]
            self._block_indptr = [b.indptr.copy() for b in blocks]
            self._has_pattern = True
            self._pattern_builds += 1
            built = True
        else:
            built = False
        return built

    def _assemble_on_pattern(self, ns: int, h: float, j11: csc_matrix, j12: csc_matrix,
                             j21: csc_matrix, j22: csc_matrix) -> csc_matrix:
        """
        Write the values on the stored pattern, or use the SciPy expression if it would drop a zero.

        :param ns: Number of states.
        :param h: Integration step.
        :param j11: State/state block.
        :param j12: State/algebraic block.
        :param j21: Algebraic/state block.
        :param j22: Algebraic/algebraic block.
        :return: Assembled matrix.
        """
        values: np.ndarray = self._values

        # I - h*J11 with SciPy's operations: 1.0 - h*a on the diagonal, 0.0 - h*a elsewhere,
        # and 1.0 on diagonal positions without a J11 entry.
        values[self._region] = self._base[self._region]
        values[self._map_j11] = self._base[self._map_j11] - h * j11.data

        # -h*J12 is evaluated as (-h)*J12 by the expression it replaces; J21 and J22 are copied.
        values[self._map_j12] = (-h) * j12.data
        values[self._map_j21] = j21.data
        values[self._map_j22] = j22.data

        result: csc_matrix
        if bool(np.any(values[self._region] == 0.0)):
            # SciPy would drop this exact zero from the I - h*J11 block, changing the pattern.
            result = self._assemble_with_scipy(ns, h, j11, j12, j21, j22)
        else:
            result = csc_matrix((values.copy(), self._indices.copy(), self._indptr.copy()), shape=self._shape)
            self._fast_assemblies += 1
        return result

    def _assemble_with_scipy(self, ns: int, h: float, j11: spmatrix, j12: spmatrix,
                             j21: spmatrix, j22: spmatrix) -> csc_matrix:
        """
        Evaluate the original SciPy expression unchanged.

        :param ns: Number of states.
        :param h: Integration step.
        :param j11: State/state block.
        :param j12: State/algebraic block.
        :param j21: Algebraic/state block.
        :param j22: Algebraic/algebraic block.
        :return: Assembled matrix, or the exception the expression raises.
        """
        self._fallback_assemblies += 1
        identity: sp.dia_matrix = sp.eye(m=ns, n=ns)
        return pack_4_by_4_scipy((identity - h * j11).tocsc(), - h * j12, j21, j22)
