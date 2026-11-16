# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Compiled RMS equations and colored AD, with a legacy Backward Euler transform."""

from typing import List

import numpy as np
from numba import types
from scipy.sparse import csc_matrix

from VeraGridEngine.Simulations.Rms.numerical.rms_batched_ad import RmsBatchedAd
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import (
    discretize_residual, discretize_jacobian, project_derivative_columns,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
from VeraGridEngine.Simulations.Rms.numerical.rms_numba_compile_worker import kernel_compile_job, prepare_kernel_group


class RmsEquationAdEvaluator:
    """Own compiled raw equations and fixed buffers for scalar residual/JVP batches."""

    __slots__ = ("_backend", "_parameters", "_residual", "_newton", "_diagonal",
                 "_discretize_residual", "_discretize_jacobian", "_helper_compile_seconds",
                 "_runtime_count", "_constant_count", "_state_count",
                 "_projected", "_projection_destinations", "_projection_orders",
                 "_project_derivative_columns")

    def __init__(self, state_vars: List[Var], algebraic_vars: List[Var],
                 state_equations: List[Expr], algebraic_equations: List[Expr],
                 diff_vars: List[Var], runtime_parameters: List[Var],
                 constant_parameters: List[Var], batch_size: int = 128,
                 batch_max_nodes: int = 1000) -> None:
        """Compile raw f/g batches for the exact RMS Backward Euler equations.

        :param state_vars: Differential variables in solver order.
        :param algebraic_vars: Algebraic variables following the states.
        :param state_equations: Differential right-hand sides.
        :param algebraic_equations: Algebraic residual equations.
        :param diff_vars: Derivative vector bindings used by the existing RMS solver.
        :param runtime_parameters: Variable parameter vector bindings.
        :param constant_parameters: Constant parameter vector bindings.
        :param batch_size: Maximum scalar equations in each compiled row batch.
        :param batch_max_nodes: Target expression-node budget per batch.
        :return: None.
        """
        assert len(state_equations) == len(state_vars), "Each differential state requires one equation"
        self._runtime_count: int = len(runtime_parameters)
        self._constant_count: int = len(constant_parameters)
        self._state_count: int = len(state_vars)
        variables: List[Var] = list(state_vars)
        variables.extend(algebraic_vars)
        parameters: List[Var] = list(runtime_parameters)
        parameters.extend(constant_parameters)
        # Compile f/g once. Initial projection and continuous-time diagnostics
        # reuse these raw equations instead of generating enormous legacy kernels.
        equations: List[Expr] = list(state_equations)
        equations.extend(algebraic_equations)
        self._parameters: np.ndarray = np.zeros(len(parameters), dtype=np.float64)
        self._residual: np.ndarray = np.zeros(len(equations), dtype=np.float64)

        self._backend: RmsBatchedAd = RmsBatchedAd(
            equations, variables, parameters, diff_vars, max_rows=batch_size, max_nodes=batch_max_nodes,
            identity_rows=self._state_count, independent_derivatives=True,
        )
        raw_pattern: csc_matrix = self._backend.matrix
        if diff_vars:
            n_vars = len(variables)
            variable_positions = {variable.uid: index for index, variable in enumerate(variables)}
            column_targets = np.arange(n_vars + len(diff_vars), dtype=np.int64)
            column_orders = np.zeros(column_targets.size, dtype=np.int64)
            for index, derivative in enumerate(diff_vars):
                origin = derivative
                while origin.base_var is not None:
                    origin = origin.base_var
                    column_orders[n_vars + index] += 1
                if origin.uid not in variable_positions:
                    raise ValueError("RMS derivative base is not a problem variable")
                column_targets[n_vars + index] = variable_positions[origin.uid]
            raw_columns = np.repeat(np.arange(raw_pattern.shape[1]), np.diff(raw_pattern.indptr))
            row_indices = raw_pattern.indices
            target_columns = column_targets[raw_columns]
            self._projected = csc_matrix(
                (np.ones(raw_pattern.nnz), (row_indices, target_columns)),
                shape=(len(equations), n_vars))
            self._projected.data[:] = 0.0
            self._projection_destinations = np.empty(raw_pattern.nnz, dtype=np.int64)
            self._projection_orders = column_orders[raw_columns]
            for entry in range(raw_pattern.nnz):
                target = int(target_columns[entry])
                start, stop = self._projected.indptr[target:target + 2]
                position = int(np.searchsorted(self._projected.indices[start:stop], row_indices[entry]))
                self._projection_destinations[entry] = start + position
        else:
            self._projected = raw_pattern
            self._projection_destinations = None
            self._projection_orders = None
        self._newton: csc_matrix = self._projected.copy()
        self._diagonal: np.ndarray = np.empty(self._state_count, dtype=np.int64)
        column: int
        for column in range(self._state_count):
            first: int = int(self._newton.indptr[column])
            last: int = int(self._newton.indptr[column + 1])
            self._diagonal[column] = first + int(np.searchsorted(self._newton.indices[first:last], column))
        # Prepare helper signatures in an auxiliary process too: all evaluation
        # paths enter native code from cache, including the first Newton step.
        vector = types.float64[::1]
        helper_jobs = [
            kernel_compile_job(discretize_residual, types.void(vector, vector, types.float64, types.int64, vector)),
            kernel_compile_job(discretize_jacobian, types.void(
                vector, types.int32[::1], types.int64[::1], types.float64, types.int64, vector,
            )),
        ]
        if diff_vars:
            helper_jobs.append(kernel_compile_job(project_derivative_columns, types.void(
                vector, types.int64[::1], types.int64[::1], types.float64, vector)))
        helpers = prepare_kernel_group(tuple(helper_jobs))
        self._discretize_residual = helpers[0].dispatcher
        self._discretize_jacobian = helpers[1].dispatcher
        self._project_derivative_columns = helpers[2].dispatcher if diff_vars else None
        self._helper_compile_seconds: float = sum(helper.compile_seconds for helper in helpers)

    def _fill_parameters(self, runtime_values: np.ndarray, constant_values: np.ndarray) -> None:
        """Refresh the fixed-size kernel input buffer without changing symbolic bindings.

        :param runtime_values: Current variable parameters.
        :param constant_values: Current constant parameters.
        :return: None.
        """
        constant_end: int = self._runtime_count + self._constant_count
        self._parameters[:self._runtime_count] = runtime_values
        self._parameters[self._runtime_count:constant_end] = constant_values

    def evaluate_residual(self, values: np.ndarray, derivatives: np.ndarray,
                          previous_values: np.ndarray, runtime_values: np.ndarray,
                          constant_values: np.ndarray, h: float) -> np.ndarray:
        """Evaluate the global residual into a reusable buffer.

        :param values: Current Newton candidate.
        :param derivatives: Existing RMS derivative values for this candidate.
        :param previous_values: Previous accepted state and algebraic values.
        :param runtime_values: Current runtime parameters.
        :param constant_values: Current constant parameters.
        :param h: Effective local step.
        :return: Borrowed residual vector, overwritten by the next evaluation.
        """
        self._fill_parameters(runtime_values, constant_values)
        self._backend.evaluate_residual(values, self._parameters, previous_values, derivatives, h, self._residual)
        self._discretize_residual(values, previous_values, h, self._state_count, self._residual)
        return self._residual

    def evaluate_jacobian(self, values: np.ndarray, derivatives: np.ndarray,
                          previous_values: np.ndarray, runtime_values: np.ndarray,
                          constant_values: np.ndarray, h: float) -> csc_matrix:
        """Refresh the numeric data of the reusable global CSC Jacobian.

        :param values: Current Newton candidate.
        :param derivatives: Existing RMS derivative values for this candidate.
        :param previous_values: Previous accepted state and algebraic values.
        :param runtime_values: Current runtime parameters.
        :param constant_values: Current constant parameters.
        :param h: Effective local step.
        :return: Borrowed global Jacobian, overwritten by the next evaluation.
        """
        raw: csc_matrix = self.evaluate_raw_jacobian(values, derivatives, runtime_values, constant_values, h)
        self._discretize_jacobian(raw.data, raw.indices, self._diagonal, h, self._state_count, self._newton.data)
        return self._newton

    def evaluate_raw_residual(self, values: np.ndarray, derivatives: np.ndarray,
                              runtime_values: np.ndarray, constant_values: np.ndarray) -> np.ndarray:
        """Expose raw f/g values for initial projection and legacy callers.

        :param values: Global candidate.
        :param derivatives: RMS derivative values.
        :param runtime_values: Current runtime parameters.
        :param constant_values: Constant parameters.
        :return: Borrowed raw state/algebraic residual buffer.
        """
        self._fill_parameters(runtime_values, constant_values)
        self._backend.evaluate_residual(values, self._parameters, values, derivatives, 1.0, self._residual)
        return self._residual

    def evaluate_raw_jacobian(self, values: np.ndarray, derivatives: np.ndarray,
                              runtime_values: np.ndarray, constant_values: np.ndarray, h: float) -> csc_matrix:
        """Expose raw f/g derivatives without generating a second family of kernels.

        :param values: Global candidate.
        :param derivatives: RMS derivative values.
        :param runtime_values: Current runtime parameters.
        :param constant_values: Constant parameters.
        :param h: Existing derivative chain step, including legacy CT calls.
        :return: Borrowed raw CSC matrix.
        """
        self._fill_parameters(runtime_values, constant_values)
        raw = self._backend.evaluate_jacobian(values, self._parameters, values, derivatives, h)
        if self._project_derivative_columns is not None:
            self._project_derivative_columns(raw.data, self._projection_destinations,
                                             self._projection_orders, h,
                                             self._projected.data)
        return self._projected

    def evaluate_independent_partials(self, values: np.ndarray, derivatives: np.ndarray,
                                      runtime_values: np.ndarray,
                                      constant_values: np.ndarray) -> csc_matrix:
        """Return raw equation partials in ``[x, y, dx]`` column order."""
        self._fill_parameters(runtime_values, constant_values)
        return self._backend.evaluate_jacobian(
            values, self._parameters, values, derivatives, 1.0)

    def get_color_count(self) -> int:
        """Report the number of directional sweeps used for one Jacobian.

        :return: Number of graph colors.
        """
        color_count: int = self._backend.n_colors
        return color_count

    def get_batch_statistics(self) -> tuple[tuple[int, int, int, float], ...]:
        """Report compiled scalar row ranges and their Numba compilation times.

        :return: First row, exclusive last row, expression nodes and seconds.
        """
        return self._backend.get_statistics()

    def get_worker_compile_seconds(self) -> float:
        """Report actual compilation time from all disposable scalar compilers.

        :return: Residual, AD and helper Numba seconds outside the numerical process.
        """
        return self._helper_compile_seconds + self._backend.get_worker_compile_seconds()
