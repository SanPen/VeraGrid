# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from typing import Callable, Tuple

from VeraGridEngine.basic_structures import Vec, IntVec


def random_trial(obj_func,
                 n_var: int,
                 lb: Vec | IntVec, ub: Vec | IntVec,
                 n_obj: int = 2,
                 max_evals: int = 3000,
                 cancel_checker: Callable[[], bool] | None = None) -> Tuple[np.ndarray, np.ndarray]:
    """

    :param obj_func:
    :param n_var:
    :param n_obj:
    :param max_evals:
    :param cancel_checker: Optional cancellation check.
    :return: Evaluated decision vectors and objective values.
    """

    # Generate sampling rule
    num_ones = np.linspace(0, n_var, max_evals, dtype=int)
    num_ones[-1] = n_var
    ones_into_array = np.zeros((max_evals, n_var), dtype=int)
    # Fill ones_into_array randomly
    for i, num in enumerate(num_ones):
        ones_into_array[i, :num] = 1
        np.random.shuffle(ones_into_array[i])

    # Init arrays to store results
    x = np.zeros((max_evals, n_var))
    f = np.zeros((max_evals, n_obj))

    # Compute objectives for each x combination
    actual_evals: int = 0
    for i, arr in enumerate(ones_into_array):
        if cancel_checker is not None and cancel_checker():
            break
        else:
            x[i, :] = arr
            f[i, :] = obj_func(arr)
            actual_evals += 1

    return x[:actual_evals, :], f[:actual_evals, :]
