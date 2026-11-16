# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Shared chord-Newton refresh decisions used by implicit dynamic integrators."""

import numba as nb
from VeraGridEngine.basic_structures import Vec


def get_adaptive_recompute_threshold(last_macro_newton_iterations: int) -> float:
    """
    Return the Newton contraction ratio above which a retained Jacobian factorization is refreshed.

    Substeps that converged in few iterations tolerate a slower contraction before paying a new
    Jacobian evaluation and factorization.

    :param last_macro_newton_iterations: Newton iterations of the last accepted substep.
    :return: Residual-norm ratio threshold.
    """
    if last_macro_newton_iterations <= 2:
        threshold: float = 0.8
    elif last_macro_newton_iterations <= 4:
        threshold = 0.6
    else:
        threshold = 0.5
    return threshold


def needs_confirming_correction(use_dense_solver: bool, confirming_correction_done: bool, newton_index: int,
                                newton_max_iter: int) -> bool:
    """
    Return whether a substep whose residual just passed must take one confirming correction before acceptance.

    The sparse path runs chord Newton with factors retained across iterations and substeps, and stops as soon
    as the residual infinity norm passes; on weakly scaled rows that can accept a state error far above the
    tolerance. One more correction (with fresh factors when the last contraction was slow, see
    _confirms_with_fresh_factors) removes most of it; it is discarded if it does not keep the residual within the
    tolerance. An iterate that passes before any correction, and dense solves, are accepted directly.

    :param use_dense_solver: Whether the substep solves with dense LU factors.
    :param confirming_correction_done: Whether the confirming correction already ran.
    :param newton_index: Current Newton iteration (number of corrections applied so far).
    :param newton_max_iter: Newton correction budget.
    :return: True when one more correction is required.
    """
    result: bool = (not use_dense_solver and not confirming_correction_done and 0 < newton_index < newton_max_iter)
    return result


def confirms_with_fresh_factors(res_norm: float, last_res_norm: float) -> bool:
    """
    Return whether the confirming correction must use a freshly evaluated Jacobian.

    A correction with the retained factors shrinks the remaining error only by the observed contraction, so when
    the last correction reduced the residual by less than a factor of ten the confirming correction is a Newton
    correction from the passing iterate instead.

    :param res_norm: Residual infinity norm of the passing iterate.
    :param last_res_norm: Residual infinity norm before the last correction.
    :return: True when the confirming correction refreshes the factors.
    """
    result: bool = res_norm > 0.1 * (last_res_norm + 1e-16)
    return result


def factorization_inputs_changed(has_snapshot: bool, compare_parameters: bool, full_params: Vec, parameter_snapshot: Vec,
                                 step: float, factorization_step: float) -> bool:
    """
    Return whether the step size, or on aligned substeps the parameters, moved since the retained factors were computed.

    Parameters that move on ordinary substeps (held outputs, time-varying sources) are left to the refresh rules and the
    retry, so they do not force a factorization on every substep; aligned substeps exist because of an event and compare
    them, as StructuralCompiledSolver did before.

    :param has_snapshot: Whether a snapshot of the factorization inputs exists.
    :param compare_parameters: Whether the parameters are compared (aligned substeps).
    :param full_params: Current full parameter vector.
    :param parameter_snapshot: Parameters at the last factorization.
    :param step: Current substep size.
    :param factorization_step: Substep size at the last factorization.
    :return: True when the retained factors must be invalidated.
    """
    if has_snapshot:
        # Grid-time rounding stays far below a relative step change of 1e-6, up to t / h of about 4e9.
        step_changed: bool = abs(step - factorization_step) > 1.0e-6 * abs(factorization_step)
        if compare_parameters:
            result: bool = step_changed or _max_abs_diff_vectors(full_params, parameter_snapshot) > 1.0e-14
        else:
            result = step_changed
    else:
        result = True
    return result


def needs_factor_refresh(newton_index: int, res_norm: float, last_res_norm: float, refresh_threshold: float,
                         newton_tolerance: float, remaining_corrections: int) -> bool:
    """
    Return whether the retained factors must be refreshed before the next correction.

    They are refreshed when the last correction contracted the residual by less than the adaptive threshold, or
    when that observed linear contraction cannot bring the residual below the tolerance within the corrections
    left in the budget, which a slow chord contraction would otherwise exhaust.

    :param newton_index: Current Newton iteration (corrections applied so far).
    :param res_norm: Current residual infinity norm.
    :param last_res_norm: Residual infinity norm before the last correction.
    :param refresh_threshold: Adaptive contraction threshold.
    :param newton_tolerance: Residual tolerance.
    :param remaining_corrections: Corrections left in the budget.
    :return: True when the factors must be refreshed.
    """
    if newton_index > 0:
        ratio: float = res_norm / (last_res_norm + 1e-16)
        result: bool = ratio > refresh_threshold or res_norm * ratio ** remaining_corrections >= newton_tolerance
    else:
        result = False
    return result


@nb.jit(cache=True, fastmath=True)
def _max_abs_diff_vectors(left_values: Vec, right_values: Vec) -> float:
    """
    Return the maximum absolute difference between two vectors.

    :param left_values: Left vector.
    :type left_values: Vec
    :param right_values: Right vector.
    :type right_values: Vec
    :return: Maximum absolute difference.
    :rtype: float
    """
    max_value: float = 0.0
    index: int = 0

    while index < left_values.shape[0]:
        diff_value: float = left_values[index] - right_values[index]

        if diff_value < 0.0:
            diff_value = -diff_value
        else:
            diff_value = diff_value

        if diff_value > max_value:
            max_value = diff_value
        else:
            max_value = max_value

        index += 1

    return max_value

