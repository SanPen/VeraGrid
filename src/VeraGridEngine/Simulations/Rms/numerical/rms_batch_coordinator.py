# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Coordinate all scalar batches without linking their generated kernel bodies."""

from typing import Any

import numpy as np
from numba import njit, types
from numba.typed import List as NumbaList

from VeraGridEngine.Simulations.Rms.numerical.rms_numba_compile_worker import (
    KernelCompileJob, LoadedKernel, kernel_compile_job, prepare_kernel_group,
)


@njit(cache=True, fastmath=False, error_model="numpy")
def coordinate_residual(kernels: Any, values: np.ndarray, parameters: np.ndarray,
                        previous: np.ndarray, derivatives: np.ndarray, h: float,
                        output: np.ndarray, state_count: int) -> None:
    """Evaluate every scalar batch and optionally discretize its global rows.

    :param kernels: Explicitly typed native functions, passed at runtime.
    :param values: Current global candidate.
    :param parameters: Runtime and constant parameters.
    :param previous: Accepted preceding candidate.
    :param derivatives: Existing derivative inputs.
    :param h: Effective local step.
    :param output: Borrowed global residual storage.
    :param state_count: Differential rows to discretize, or -1 for raw equations.
    :return: None.
    """
    # FunctionType arguments deliberately hide kernel bodies from the compiler.
    # Indirect native calls keep LLVM work independent of symbolic batch size.
    index: int
    for index in range(len(kernels)):
        kernels[index](values, parameters, previous, derivatives, h, output, previous)
    if state_count >= 0:
        for index in range(state_count):
            output[index] = values[index] - previous[index] - h * output[index]
    else:
        pass


@njit(cache=True, fastmath=False, error_model="numpy")
def coordinate_jacobian(kernels: Any, colors: Any,
                        pointers: Any, rows: Any,
                        positions: Any, sizes: np.ndarray,
                        seeds: np.ndarray, values: np.ndarray, parameters: np.ndarray,
                        previous: np.ndarray, derivatives: np.ndarray, h: float,
                        work: np.ndarray, output: np.ndarray, csc_rows: np.ndarray,
                        diagonal: np.ndarray, state_count: int, newton: np.ndarray) -> None:
    """Run colors and scatter inside Numba while sharing one bounded JVP buffer.

    :param kernels: Native JVP functions with explicit signatures.
    :param colors: Global seed colors needed by each batch.
    :param pointers: Per-color ranges in each batch's scatter arrays.
    :param rows: Local JVP row indices.
    :param positions: Corresponding global CSC positions.
    :param sizes: Equation count in each batch.
    :param seeds: Shared global coloring seed matrix.
    :param values: Current global candidate.
    :param parameters: Runtime and constant parameters.
    :param previous: Accepted preceding candidate.
    :param derivatives: Existing derivative inputs.
    :param h: Effective local step.
    :param work: Shared batch-sized directional derivative buffer.
    :param output: Borrowed global CSC numeric storage.
    :param csc_rows: Global row of each CSC entry.
    :param diagonal: Differential identity positions.
    :param state_count: Differential row count, or -1 to retain raw derivatives.
    :param newton: Persistent implicit matrix numeric storage.
    :return: None.
    """
    # Sequential batches preserve bounded storage and overwrite structural zeros.
    batch: int
    color_index: int
    entry: int
    for batch in range(len(kernels)):
        for color_index in range(colors[batch].size):
            kernels[batch](values, seeds[colors[batch][color_index]], parameters,
                           previous, derivatives, h, work[:sizes[batch]], previous)
            for entry in range(pointers[batch][color_index], pointers[batch][color_index + 1]):
                output[positions[batch][entry]] = work[rows[batch][entry]]
    # Discretize only after every raw row has been overwritten. This keeps raw
    # diagnostics available without a second Python-to-Numba evaluation call.
    if state_count >= 0:
        for entry in range(output.size):
            if csc_rows[entry] < state_count:
                newton[entry] = -h * output[entry]
            else:
                newton[entry] = output[entry]
        for entry in range(diagonal.size):
            newton[diagonal[entry]] += 1.0
    else:
        pass


class RmsBatchCoordinator:
    """Bind global native dispatch to fixed kernels, scatter metadata and cache jobs."""

    __slots__ = ("_residual", "_jacobian", "_residual_kernels", "_ad_kernels", "_colors",
                 "_pointers", "_rows", "_positions", "_sizes", "compile_seconds")

    def __init__(self, residual_kernels: tuple[Any, ...], ad_kernels: tuple[Any, ...],
                 residual_signature: Any, ad_signature: Any, colors: tuple[np.ndarray, ...],
                 pointers: tuple[np.ndarray, ...], rows: tuple[np.ndarray, ...],
                 positions: tuple[np.ndarray, ...], sizes: np.ndarray) -> None:
        """Compile generic coordination in an auxiliary and require cache-only loading.

        :param residual_kernels: Cache-loaded generated value kernels.
        :param ad_kernels: Cache-loaded generated JVP kernels.
        :param residual_signature: Common generated value-kernel ABI.
        :param ad_signature: Common generated JVP-kernel ABI.
        :param colors: Global colors per batch.
        :param pointers: Per-color scatter offsets.
        :param rows: Local row indices per batch.
        :param positions: Global CSC positions per batch.
        :param sizes: Equation count per batch.
        :return: None.
        """
        vector: Any = types.float64[::1]
        integer_arrays: Any = types.ListType(types.int64[::1])
        residual_functions: Any = types.ListType(types.FunctionType(residual_signature))
        ad_functions: Any = types.ListType(types.FunctionType(ad_signature))
        # Passing typed functions at runtime prevents Numba/LLVM from expanding
        # generated code into this reusable coordinator or embedding addresses
        # in its persistent cache. Typed lists keep the ABI independent of the
        # number of batches, including the metadata used by the scatter loop.
        jobs: tuple[KernelCompileJob, ...] = (
            kernel_compile_job(coordinate_residual, types.void(
                residual_functions,
                vector, vector, vector, vector, types.float64, vector, types.int64,
            )),
            kernel_compile_job(coordinate_jacobian, types.void(
                ad_functions,
                types.ListType(types.int32[::1]), integer_arrays,
                integer_arrays, integer_arrays, types.int64[::1], types.float64[:, ::1],
                vector, vector, vector, vector, types.float64, vector, vector,
                types.int32[::1], types.int64[::1], types.int64, vector,
            )),
        )
        loaded: tuple[LoadedKernel, ...] = prepare_kernel_group(jobs)
        self._residual: Any = loaded[0].dispatcher
        self._jacobian: Any = loaded[1].dispatcher
        # Bind function addresses once; constructing a giant tuple-specialized
        # adapter would make compilation grow with the total network size.
        self._residual_kernels: Any = NumbaList.empty_list(types.FunctionType(residual_signature))
        self._ad_kernels: Any = NumbaList.empty_list(types.FunctionType(ad_signature))
        kernel: Any
        for kernel in residual_kernels:
            self._residual_kernels.append(kernel)
        for kernel in ad_kernels:
            self._ad_kernels.append(kernel)
        self._colors: Any = NumbaList.empty_list(types.int32[::1])
        self._pointers: Any = NumbaList.empty_list(types.int64[::1])
        self._rows: Any = NumbaList.empty_list(types.int64[::1])
        self._positions: Any = NumbaList.empty_list(types.int64[::1])
        index: int
        for index in range(len(colors)):
            self._colors.append(colors[index])
            self._pointers.append(pointers[index])
            self._rows.append(rows[index])
            self._positions.append(positions[index])
        self._sizes: np.ndarray = sizes
        self.compile_seconds: float = sum(kernel.compile_seconds for kernel in loaded)

    def evaluate_residual(self, values: np.ndarray, parameters: np.ndarray,
                          previous: np.ndarray, derivatives: np.ndarray,
                          h: float, output: np.ndarray, state_count: int = -1) -> None:
        """Dispatch one group using bound kernels and caller-owned residual storage.

        :param values: Current candidate.
        :param parameters: Global parameters.
        :param previous: Preceding candidate.
        :param derivatives: Derivative inputs.
        :param h: Effective step.
        :param output: Global residual storage.
        :param state_count: Differential rows, or -1 for raw evaluation.
        :return: None.
        """
        self._residual(self._residual_kernels, values, parameters, previous, derivatives, h, output, state_count)

    def evaluate_jacobian(self, seeds: np.ndarray, values: np.ndarray, parameters: np.ndarray,
                          previous: np.ndarray, derivatives: np.ndarray, h: float,
                          work: np.ndarray, output: np.ndarray, csc_rows: np.ndarray,
                          diagonal: np.ndarray, state_count: int, newton: np.ndarray) -> None:
        """Dispatch all group colors and scatter through one native call.

        :param seeds: Global coloring seeds.
        :param values: Current candidate.
        :param parameters: Global parameters.
        :param previous: Preceding candidate.
        :param derivatives: Derivative inputs.
        :param h: Effective step.
        :param work: Shared JVP scratch.
        :param output: Global CSC numeric storage.
        :param csc_rows: Global row indices.
        :param diagonal: Differential identity slots.
        :param state_count: Differential rows, or -1 for raw derivatives.
        :param newton: Implicit CSC numeric storage.
        :return: None.
        """
        self._jacobian(self._ad_kernels, self._colors, self._pointers, self._rows,
                       self._positions, self._sizes, seeds, values, parameters,
                       previous, derivatives, h, work, output, csc_rows, diagonal, state_count, newton)
