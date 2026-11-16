# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Evaluate RMS derivative history with a fixed-size native indexing kernel."""

from typing import Any

import numpy as np
from numba import njit, types

from VeraGridEngine.Utils.Symbolic.symbolic import Var


@njit(cache=True, fastmath=False, error_model="numpy")
def evaluate_derivative_history(values: np.ndarray, previous: np.ndarray,
                                previous_derivatives: np.ndarray, h: float,
                                state_indices: np.ndarray, parent_indices: np.ndarray,
                                output: np.ndarray) -> None:
    """Evaluate the existing RMS difference formulas in dependency order.

    :param values: Current global state and algebraic values.
    :param previous: Previous accepted global values.
    :param previous_derivatives: Derivative history in the original RMS order.
    :param h: Effective local time step.
    :param state_indices: Global base-variable index, or -1 for higher orders.
    :param parent_indices: Earlier derivative row used by a higher-order row.
    :param output: Fresh derivative storage owned by the caller.
    :return: None.
    """
    # Reuse earlier results instead of expanding the same derivative expression
    # repeatedly. Keep the historical lagdx[row] convention unchanged.
    row: int
    for row in range(state_indices.size):
        state_index: int = state_indices[row]
        if state_index >= 0:
            output[row] = (values[state_index] - previous[state_index]) / h
        else:
            output[row] = (output[parent_indices[row]] - previous_derivatives[row]) / h


class RmsDerivativeEvaluator:
    """Own derivative bindings while preserving independent returned histories."""

    __slots__ = ("_state_indices", "_parent_indices")

    def __init__(self, derivatives: list[Var], variable_indices: dict[int, int]) -> None:
        """Bind symbolic dependencies and eagerly prepare one generic Numba ABI.

        :param derivatives: Existing derivative order used by the RMS problem.
        :param variable_indices: Global state/algebraic UID to vector position.
        :return: None.
        :raises ValueError: A declaration lacks a base or precedes its derivative parent.
        """
        self._state_indices: np.ndarray = np.full(len(derivatives), -1, dtype=np.int64)
        self._parent_indices: np.ndarray = np.full(len(derivatives), -1, dtype=np.int64)
        derivative_positions: dict[int, int] = dict()
        row: int
        derivative: Var
        for row, derivative in enumerate(derivatives):
            base: Var | None = derivative.base_var
            if base is None:
                raise ValueError("RMS derivative has no base variable: " + derivative.name)
            elif derivative.diff_order == 1:
                self._state_indices[row] = variable_indices[base.uid]
            else:
                parent: int | None = derivative_positions.get(base.uid, None)
                if parent is None:
                    raise ValueError("RMS derivative parent must precede its child: " + derivative.name)
                else:
                    self._parent_indices[row] = parent
            derivative_positions[derivative.uid] = row

        # Arbitrary-stride, read-only input types also accept writable arrays
        # and memmap views. Compile before integration, under the benchmark's
        # existing Numba timer, without generating code proportional to the grid.
        vector: Any = types.Array(types.float64, 1, "A", readonly=True)
        indices: Any = types.Array(types.int64, 1, "C", readonly=True)
        signature: tuple[Any, ...] = (
            vector, vector, vector, types.float64, indices, indices, types.float64[::1],
        )
        if signature not in evaluate_derivative_history.overloads:
            evaluate_derivative_history.compile(signature)
        else:
            pass
        # Force compatible views through this prepared ABI rather than allowing
        # Numba to specialize again when mutability or array strides differ.
        evaluate_derivative_history.disable_compile()

    def __call__(self, values: np.ndarray, previous: np.ndarray,
                 previous_derivatives: np.ndarray, h: float) -> np.ndarray:
        """Return newly allocated derivatives without overwriting retained history.

        :param values: Current global candidate.
        :param previous: Previous accepted global values.
        :param previous_derivatives: Previous derivative history.
        :param h: Effective local step.
        :return: Independent float64 derivative vector.
        """
        # Solvers retain dx and dx_last simultaneously. Sharing a reusable
        # output would silently corrupt history across Newton iterations.
        output: np.ndarray = np.empty(self._state_indices.size, dtype=np.float64)
        evaluate_derivative_history(values, previous, previous_derivatives, h,
                                    self._state_indices, self._parent_indices, output)
        return output
