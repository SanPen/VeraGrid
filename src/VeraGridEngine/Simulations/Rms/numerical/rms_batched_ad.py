# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Bound scalar RMS code generation while preserving one global CSC Jacobian."""

from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from scipy.sparse import csc_matrix

from VeraGridEngine.Utils.Symbolic.jit_compiler_rms_numba_comp import RmsEagerEquationCompiler
from VeraGridEngine.Utils.Symbolic.sparse_ad_jacobian import greedy_color_columns
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Expr, Func, Func2, UnOp, Var
from VeraGridEngine.Simulations.Rms.numerical.rms_batch_codegen import compile_batch_pair
from VeraGridEngine.Simulations.Rms.numerical.rms_batch_coordinator import RmsBatchCoordinator
from VeraGridEngine.Simulations.Rms.numerical.rms_numba_compile_worker import (
    KernelCompileJob, LoadedKernel, kernel_compile_job, prepare_kernel_group,
)


def analyze_equation(equation: Expr, variable_positions: dict[int, int],
                     independent_derivatives: bool = False) -> tuple[set[int], int]:
    """Find structural columns and count DAG nodes without expanding shared trees.

    :param equation: One global scalar f/g equation.
    :param variable_positions: Candidate-variable UID to global column mapping.
    :return: Dependent columns and unique expression-node count.
    """
    pending: list[Expr] = list((equation,))
    seen: set[int] = set()
    columns: set[int] = set()
    while pending:
        node: Expr = pending.pop()
        identity: int = id(node)
        if identity not in seen:
            seen.add(identity)
            if isinstance(node, Var):
                if independent_derivatives:
                    column = variable_positions.get(node.uid)
                    if column is not None:
                        columns.add(column)
                    continue
                # RMS dt(...) values are inputs, but their tangents depend on
                # every candidate base in the derivative chain through 1/h.
                base: Var | None = node
                while base is not None:
                    column: int | None = variable_positions.get(base.uid, None)
                    if column is not None:
                        columns.add(column)
                    else:
                        pass
                    base = base.base_var
            elif isinstance(node, BinOp):
                pending.append(node.left)
                pending.append(node.right)
            elif isinstance(node, UnOp):
                pending.append(node.operand)
            elif isinstance(node, Func2):
                pending.append(node.arg1)
                pending.append(node.arg2)
            elif isinstance(node, Func):
                pending.append(node.arg)
            else:
                pass
        else:
            pass
    return columns, len(seen)


def resident_mib() -> float | None:
    """Read current Linux resident memory for compilation progress diagnostics.

    :return: Resident MiB, or None when procfs is unavailable.
    """
    status: Path = Path("/proc/self/status")
    if status.is_file():
        line: str
        for line in status.read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
            else:
                pass
    else:
        pass
    return None


class RmsAdBatch:
    """Keep one row range's native kernels and immutable global scatter bindings."""

    __slots__ = ("start", "stop", "node_count", "colors", "pointers", "rows", "positions",
                 "residual_kernel", "ad_kernel", "compile_seconds", "load_seconds", "jobs")

    def __init__(self, start: int, stop: int, node_count: int,
                 entries: list[tuple[int, int, int]], equations: list[Expr],
                 compiler: RmsEagerEquationCompiler) -> None:
        """Generate only this row range while retaining all global input slots.

        :param start: First global residual row.
        :param stop: Exclusive final global row.
        :param node_count: Sum of per-equation DAG node counts.
        :param entries: Global color, batch-local row and CSC-position triples.
        :param equations: Original global scalar equations.
        :param compiler: Shared compiler with unchanged global input bindings.
        :return: None.
        """
        self.start: int = start
        self.stop: int = stop
        self.node_count: int = node_count
        ordered: list[tuple[int, int, int]] = sorted(entries)
        self.colors: np.ndarray = np.unique(np.array([entry[0] for entry in ordered], dtype=np.int32))
        self.pointers: np.ndarray = np.zeros(self.colors.size + 1, dtype=np.int64)
        self.rows: np.ndarray = np.empty(len(ordered), dtype=np.int64)
        self.positions: np.ndarray = np.empty(len(ordered), dtype=np.int64)
        index: int
        entry: tuple[int, int, int]
        for index, entry in enumerate(ordered):
            self.rows[index] = entry[1]
            self.positions[index] = entry[2]
            self.pointers[int(np.searchsorted(self.colors, entry[0])) + 1] += 1
        np.cumsum(self.pointers, out=self.pointers)
        local_equations: list[Expr] = equations[start:stop]
        python_kernel: Any
        signature: Any
        python_ad: Any
        ad_signature: Any
        # Only Python source generation occurs here. The worker receives file
        # references/signatures, never this batch's equations or compiler maps.
        python_kernel, signature, python_ad, ad_signature = compile_batch_pair(compiler, local_equations, start)
        self.jobs: tuple[KernelCompileJob, KernelCompileJob] = (
            kernel_compile_job(python_kernel, signature), kernel_compile_job(python_ad, ad_signature),
        )
        self.residual_kernel: Any = None
        self.ad_kernel: Any = None
        self.compile_seconds: float = 0.0
        self.load_seconds: float = 0.0

    def bind_kernels(self, residual: LoadedKernel, ad: LoadedKernel) -> None:
        """Bind verified cache hits after the disposable compiler has exited.

        :param residual: Cache-loaded value kernel and worker timing.
        :param ad: Cache-loaded JVP kernel and worker timing.
        :return: None.
        """
        self.residual_kernel = residual.dispatcher
        self.ad_kernel = ad.dispatcher
        self.compile_seconds = residual.compile_seconds + ad.compile_seconds
        self.load_seconds = residual.load_seconds + ad.load_seconds


class RmsBatchedAd:
    """Evaluate bounded scalar kernels into fixed global residual/CSC buffers."""

    __slots__ = ("matrix", "n_colors", "_batches", "_seeds", "_work", "_coordinator", "_empty_indices")

    def __init__(self, equations: list[Expr], variables: list[Var], parameters: list[Var],
                 derivatives: list[Var], max_rows: int = 128, max_nodes: int = 1000,
                 identity_rows: int = 0, compile_group_size: int = 8,
                 independent_derivatives: bool = False) -> None:
        """Discover the global pattern once and compile bounded row groups.

        :param equations: Raw state right-hand sides and algebraic residuals.
        :param variables: Candidate variables in unchanged global order.
        :param parameters: Runtime, constant, history and step parameters.
        :param derivatives: Existing RMS derivative input order.
        :param max_rows: Maximum number of equations per native kernel.
        :param max_nodes: Target maximum expression complexity per kernel.
        :param identity_rows: State diagonal slots reserved for Backward Euler.
        :param compile_group_size: Maximum batches in each disposable compiler process.
        :return: None.
        """
        assert max_rows > 0 and max_nodes > 0 and compile_group_size > 0
        print(f"RMS scalar batches: analyzing {len(equations)} equations, "
              f"{len(variables)} variables; limits={max_rows} rows/{max_nodes} nodes", flush=True)
        column_count = len(variables) + (len(derivatives) if independent_derivatives else 0)
        column_rows: list[list[int]] = list(list() for _ in range(column_count))
        variable_positions: dict[int, int] = dict((variable.uid, index) for index, variable in enumerate(variables))
        if independent_derivatives:
            variable_positions.update((derivative.uid, len(variables) + index)
                                      for index, derivative in enumerate(derivatives))
        ranges: list[tuple[int, int, int]] = list()
        row_batches: np.ndarray = np.empty(len(equations), dtype=np.int64)
        start: int = 0
        nodes: int = 0
        row: int
        equation: Expr
        for row, equation in enumerate(equations):
            columns: set[int]
            count: int
            columns, count = analyze_equation(equation, variable_positions,
                                              independent_derivatives)
            if row < identity_rows:
                columns.add(row)
            else:
                pass
            if row > start and (row - start >= max_rows or nodes + count > max_nodes):
                ranges.append((start, row, nodes))
                start = row
                nodes = 0
            else:
                pass
            row_batches[row] = len(ranges)
            nodes += count
            column: int
            for column in columns:
                column_rows[column].append(row)
        if start < len(equations):
            ranges.append((start, len(equations), nodes))
        else:
            pass

        # Ordered rows per column yield canonical CSC, including structural
        # zeros that can become nonzero when a limiter changes branch.
        pointers: np.ndarray = np.zeros(column_count + 1, dtype=np.int32)
        for column in range(column_count):
            pointers[column + 1] = pointers[column] + len(column_rows[column])
        indices: np.ndarray = np.empty(int(pointers[-1]), dtype=np.int32)
        for column in range(column_count):
            indices[pointers[column]:pointers[column + 1]] = column_rows[column]
        self.matrix: csc_matrix = csc_matrix(
            (np.zeros(indices.size), indices, pointers), shape=(len(equations), column_count),
        )
        colors: np.ndarray
        colors, self.n_colors = greedy_color_columns(column_rows, len(equations))
        self._seeds: np.ndarray = np.zeros((self.n_colors, column_count), dtype=float)
        for column in range(column_count):
            self._seeds[colors[column], column] = 1.0
        entries: list[list[tuple[int, int, int]]] = list(list() for _ in ranges)
        position: int
        for column in range(column_count):
            for position in range(int(pointers[column]), int(pointers[column + 1])):
                row = int(indices[position])
                batch_index: int = int(row_batches[row])
                entries[batch_index].append((int(colors[column]), row - ranges[batch_index][0], position))
        self._work: np.ndarray = np.empty(max((stop - first for first, stop, _ in ranges), default=0))
        compiler: RmsEagerEquationCompiler = RmsEagerEquationCompiler(
            variables, parameters, derivatives,
            independent_derivatives=independent_derivatives)
        print(f"RMS scalar batches: global CSC={self.matrix.shape}, stored nnz={self.matrix.nnz}, "
              f"colors={self.n_colors}, batches={len(ranges)}, JVP workspace={self._work.nbytes} bytes", flush=True)
        batches: list[RmsAdBatch] = list()
        batch_index: int
        group_start: int
        for group_start in range(0, len(ranges), compile_group_size):
            began: float = perf_counter()
            group_stop: int = min(group_start + compile_group_size, len(ranges))
            jobs: list[KernelCompileJob] = list()
            for batch_index in range(group_start, group_stop):
                first: int
                stop: int
                complexity: int
                first, stop, complexity = ranges[batch_index]
                batch: RmsAdBatch = RmsAdBatch(first, stop, complexity, entries[batch_index], equations, compiler)
                batches.append(batch)
                jobs.extend(batch.jobs)
            print(f"RMS scalar batches {group_start + 1}-{group_stop}/{len(ranges)}: "
                  "preparing cache in disposable compiler if needed", flush=True)
            loaded: tuple[LoadedKernel, ...] = prepare_kernel_group(tuple(jobs))
            for batch_index in range(group_start, group_stop):
                local_index: int = 2 * (batch_index - group_start)
                batch = batches[batch_index]
                batch.bind_kernels(loaded[local_index], loaded[local_index + 1])
            print(f"RMS scalar batches {group_start + 1}-{group_stop}/{len(ranges)} ready: "
                  f"Numba_worker={sum(kernel.compile_seconds for kernel in loaded):.3f}s "
                  f"cache_load={sum(kernel.load_seconds for kernel in loaded):.3f}s "
                  f"preparation={perf_counter() - began:.3f}s RSS_MiB={resident_mib()}", flush=True)
        self._batches: tuple[RmsAdBatch, ...] = tuple(batches)
        self._empty_indices: np.ndarray = np.empty(0, dtype=np.int64)
        self._coordinator: RmsBatchCoordinator | None = None
        # Compilation groups bound worker memory only. Runtime uses a single
        # coordinator whose typed-list ABI is independent of the batch count.
        if len(batches) > 0:
            self._coordinator = RmsBatchCoordinator(
                tuple(batch.residual_kernel for batch in batches),
                tuple(batch.ad_kernel for batch in batches),
                batches[0].jobs[0].signature, batches[0].jobs[1].signature,
                tuple(batch.colors for batch in batches),
                tuple(batch.pointers for batch in batches),
                tuple(batch.rows for batch in batches),
                tuple(batch.positions for batch in batches),
                np.array([batch.stop - batch.start for batch in batches], dtype=np.int64),
            )
        else:
            pass

    def evaluate_residual(self, values: np.ndarray, parameters: np.ndarray, previous: np.ndarray,
                          derivatives: np.ndarray, h: float, output: np.ndarray,
                          state_count: int = -1) -> None:
        """Write disjoint global row ranges without allocating intermediate residuals.

        :param values: Current global Newton candidate.
        :param parameters: Prepared global parameter buffer.
        :param previous: Preceding accepted candidate.
        :param derivatives: Current RMS derivative inputs.
        :param h: Effective local step.
        :param output: Persistent global residual buffer.
        :param state_count: Differential rows to discretize, or -1 for raw equations.
        :return: None.
        """
        if self._coordinator is not None:
            self._coordinator.evaluate_residual(values, parameters, previous, derivatives, h, output, state_count)
        else:
            pass

    def evaluate_jacobian(self, values: np.ndarray, parameters: np.ndarray, previous: np.ndarray,
                          derivatives: np.ndarray, h: float) -> csc_matrix:
        """Refresh every stored derivative with one reusable batch-sized JVP buffer.

        :param values: Current global Newton candidate.
        :param parameters: Prepared global parameter buffer.
        :param previous: Preceding accepted candidate.
        :param derivatives: Current RMS derivative inputs.
        :param h: Effective local step.
        :return: Borrowed global CSC matrix, with unchanged storage identities.
        """
        if self._coordinator is not None:
            self._coordinator.evaluate_jacobian(self._seeds, values, parameters, previous, derivatives,
                                            h, self._work, self.matrix.data, self.matrix.indices,
                                            self._empty_indices, -1, self.matrix.data)
        else:
            pass
        return self.matrix

    def evaluate_newton(self, values: np.ndarray, parameters: np.ndarray, previous: np.ndarray,
                        derivatives: np.ndarray, h: float, diagonal: np.ndarray,
                        state_count: int, output: np.ndarray) -> None:
        """Evaluate all batches and discretize the global matrix in one native entry.

        :param values: Current global candidate.
        :param parameters: Prepared parameter buffer.
        :param previous: Previous accepted values.
        :param derivatives: Derivative history.
        :param h: Effective local step.
        :param diagonal: Differential identity positions.
        :param state_count: Number of differential rows.
        :param output: Persistent implicit CSC numeric storage.
        :return: None.
        """
        if self._coordinator is not None:
            self._coordinator.evaluate_jacobian(self._seeds, values, parameters, previous, derivatives,
                                            h, self._work, self.matrix.data, self.matrix.indices,
                                            diagonal, state_count, output)
        else:
            pass

    def get_statistics(self) -> tuple[tuple[int, int, int, float], ...]:
        """Describe row ranges, complexity and observed compilation per batch.

        :return: First row, exclusive last row, DAG nodes and Numba seconds.
        """
        return tuple((batch.start, batch.stop, batch.node_count, batch.compile_seconds) for batch in self._batches)

    def get_worker_compile_seconds(self) -> float:
        """Aggregate actual Numba events reported by exited compiler processes.

        :return: Worker compilation seconds, excluding imports, waiting and cache loads.
        """
        coordinator_seconds: float = 0.0 if self._coordinator is None else self._coordinator.compile_seconds
        return coordinator_seconds + sum(batch.compile_seconds for batch in self._batches)
