# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Preserve scalar f/g block interfaces using the single batched evaluator."""

from enum import IntEnum

import numpy as np
from scipy.sparse import csc_matrix

from VeraGridEngine.Simulations.Rms.numerical.rms_ad_backend_numba_comp import RmsEquationAdEvaluator


class RmsScalarRows(IntEnum):
    """Select differential or algebraic rows/columns in global ordering."""

    STATE = 0
    ALGEBRAIC = 1


class RmsScalarResidualView:
    """Supply the legacy four-argument residual interface without recompilation."""

    __slots__ = ("_evaluator", "_slice", "_output")

    def __init__(self, evaluator: RmsEquationAdEvaluator, state_count: int,
                 algebraic_count: int, rows: RmsScalarRows) -> None:
        """Reserve one stable output for the selected raw f/g row range.

        :param evaluator: Shared batched scalar owner.
        :param state_count: Number of differential equations.
        :param algebraic_count: Number of algebraic equations.
        :param rows: Row family to expose.
        :return: None.
        """
        self._evaluator: RmsEquationAdEvaluator = evaluator
        self._slice: slice = slice(0, state_count) if rows == RmsScalarRows.STATE else slice(state_count, None)
        self._output: np.ndarray = np.empty(state_count if rows == RmsScalarRows.STATE else algebraic_count)

    def __call__(self, values: np.ndarray, derivatives: np.ndarray,
                 runtime: np.ndarray, constants: np.ndarray) -> np.ndarray:
        """Evaluate raw equations into the view's persistent output.

        :param values: Candidate state/algebraic values.
        :param derivatives: RMS derivative values.
        :param runtime: Runtime parameters.
        :param constants: Constant parameters.
        :return: Selected f or g vector.
        """
        self._output[:] = self._evaluator.evaluate_raw_residual(values, derivatives, runtime, constants)[self._slice]
        return self._output


class RmsScalarJacobianView:
    """Expose one raw Jacobian block for projection and existing diagnostics."""

    __slots__ = ("_evaluator", "_rows", "_columns")

    def __init__(self, evaluator: RmsEquationAdEvaluator, state_count: int,
                 rows: RmsScalarRows, columns: RmsScalarRows) -> None:
        """Record the two global ranges without owning compiled functions.

        :param evaluator: Shared batched scalar owner.
        :param state_count: Number of differential coordinates.
        :param rows: Selected equation family.
        :param columns: Selected variable family.
        :return: None.
        """
        self._evaluator: RmsEquationAdEvaluator = evaluator
        self._rows: slice = slice(0, state_count) if rows == RmsScalarRows.STATE else slice(state_count, None)
        self._columns: slice = slice(0, state_count) if columns == RmsScalarRows.STATE else slice(state_count, None)

    def __call__(self, values: np.ndarray, derivatives: np.ndarray,
                 runtime: np.ndarray, constants: np.ndarray, h: float) -> csc_matrix:
        """Return a CSC block of the shared raw Jacobian.

        :param values: Candidate state/algebraic values.
        :param derivatives: RMS derivative values.
        :param runtime: Runtime parameters.
        :param constants: Constant parameters.
        :param h: Existing RMS derivative-chain step.
        :return: Selected raw Jacobian block.
        """
        matrix: csc_matrix = self._evaluator.evaluate_raw_jacobian(values, derivatives, runtime, constants, h)
        return matrix[self._rows, self._columns]
