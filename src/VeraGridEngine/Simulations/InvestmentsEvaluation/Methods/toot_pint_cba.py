# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
TOOT/PINT-based independent investment ranking for the investments evaluation framework.

This module implements a light-weight library function, :func:`TOOT_PINT_CBA`, that follows the same
calling style as the evolutionary search helpers used elsewhere in the package, such as
``NSGA_3(obj_func=..., n_var=..., lb=..., ub=..., n_obj=...)``. The goal is not to solve a generic
multi-objective search problem, but to build a deterministic project ranking and cumulative build-out
sequence inspired by the ENTSO-e cost-benefit-analysis workflow.

The implementation is designed around the existing black-box investment problems. In particular, it does
not fabricate surrogate metrics or replace the objective vectors defined by the active problem. Every
visible evaluation is still produced by the provided ``obj_func`` callback, which means that the result
tables, Pareto views and plots continue to display the exact objective names and values returned by the
problem instance used by the driver.

Method overview
===============

The procedure evaluates three types of combinations:

``reference``
    The baseline combination, built from the lower bounds of the investment decision vector.

``PINT``
    "Project in" evaluations. For each decision variable, one project is added to the reference
    combination and the marginal improvement is measured against the baseline objective vector.

``TOOT``
    "Take one out" evaluations. A target combination containing all candidate projects is built from
    the upper bounds. Then, for each decision variable, one project is removed from that target and the
    marginal degradation is measured against the target objective vector.

The PINT and TOOT marginal effects are normalized, combined into a scalar ranking score and used only to
sort the projects. Once the ranking is known, the function evaluates the cumulative build-out sequence by
calling ``obj_func`` again with progressively larger combinations in ranking order.

Design constraints
==================

The module intentionally stays independent from the driver class in order to behave as a reusable method
library. For that reason the public function receives only explicit arguments:

``obj_func``
    Callable used to evaluate combinations. It must accept the keyword arguments ``x`` and
    ``record_results``.

``lb`` and ``ub``
    Lower and upper decision-vector bounds. These are used to construct the reference and target
    combinations and to infer the canonical "project active" value for each decision variable.

``objective_names`` and ``variable_names``
    Metadata used to locate the CAPEX objective and to emit readable log messages.

The implementation assumes a minimization problem, which matches the investments evaluation framework.
Positive deltas therefore represent improvements.
"""
from __future__ import annotations

import timeit
from typing import Callable

import numpy as np

from VeraGridEngine.basic_structures import IntVec, IntMat, StrVec, Vec, Mat, Logger


def get_reference_combination(lb: Vec | IntVec) -> IntVec:
    """
    Get the reference-grid combination used as the baseline of the CBA evaluations.

    :param lb: Lower bound vector.
    :type lb: Vec | IntVec
    :return: Reference combination.
    :rtype: IntVec
    """
    return np.array(lb, dtype=int)


def get_candidate_activation_value(ub: Vec | IntVec, idx: int) -> int:
    """
    Get the canonical "project present" value for one decision variable.

    For binary problems this is ``1``. For year-of-entry problems this is the first entry year.

    :param ub: Upper bound vector.
    :type ub: Vec | IntVec
    :param idx: Decision-variable index.
    :type idx: int
    :return: Activation value for the project.
    :rtype: int
    """
    max_value: int = int(ub[idx])

    if max_value >= 1:
        return 1
    else:
        return max_value


def get_target_combination(n_var: int, lb: Vec | IntVec, ub: Vec | IntVec) -> IntVec:
    """
    Get the "all candidate projects included" combination used for the TOOT ranking proxy.

    :param n_var: Number of decision variables.
    :type n_var: int
    :param lb: Lower bound vector.
    :type lb: Vec | IntVec
    :param ub: Upper bound vector.
    :type ub: Vec | IntVec
    :return: Target combination.
    :rtype: IntVec
    """
    combination: IntVec = get_reference_combination(lb=lb)

    for idx in range(n_var):
        combination[idx] = get_candidate_activation_value(ub=ub, idx=idx)

    return combination


def get_capex_objective_index(objective_names: StrVec) -> int:
    """
    Locate the CAPEX-like objective index.

    :param objective_names: Objective names of the active problem.
    :type objective_names: StrVec
    :return: Objective index or ``-1`` if it is not found.
    :rtype: int
    """
    for idx, name in enumerate(objective_names):
        name_txt: str = str(name).strip().lower()

        if "capex" in name_txt:
            return idx
        else:
            pass

    for idx, name in enumerate(objective_names):
        name_txt = str(name).strip().lower()

        if "financial" in name_txt:
            return idx
        else:
            pass

    return -1


def get_objective_scale(baseline: Vec, target: Vec) -> Vec:
    """
    Build a scale vector to normalize marginal benefits across objectives.

    :param baseline: Objective vector of the reference combination.
    :type baseline: Vec
    :param target: Objective vector of the target combination.
    :type target: Vec
    :return: Normalization scale vector.
    :rtype: Vec
    """
    scale: Vec = np.maximum(np.abs(baseline), np.abs(target))
    scale = np.maximum(scale, 1.0)
    return scale


def get_normalized_cba_score(delta_objectives: Vec,
                             capex_delta: float,
                             capex_idx: int,
                             scale: Vec) -> float:
    """
    Convert a multi-objective marginal improvement into a scalar ranking score.

    Positive deltas mean the candidate improves the objective because all objectives are minimized.

    :param delta_objectives: Marginal improvement vector.
    :type delta_objectives: Vec
    :param capex_delta: Marginal CAPEX contribution.
    :type capex_delta: float
    :param capex_idx: CAPEX objective index.
    :type capex_idx: int
    :param scale: Objective normalization scale.
    :type scale: Vec
    :return: Scalar CBA-like ranking score.
    :rtype: float
    """
    benefit_score: float = 0.0

    for idx, delta_value in enumerate(delta_objectives):
        if idx != capex_idx:
            benefit_score += float(delta_value) / float(scale[idx])
        else:
            pass

    if capex_idx > -1:
        capex_scale: float = float(scale[capex_idx])
        normalized_capex: float

        if capex_scale > 0.0:
            normalized_capex = capex_delta / capex_scale
        else:
            normalized_capex = capex_delta

        if normalized_capex > 0.0:
            return benefit_score / normalized_capex
        else:
            return benefit_score
    else:
        return benefit_score


def get_sorted_project_indices(scores: Vec, capex_values: Vec) -> IntVec:
    """
    Sort projects by descending score and ascending CAPEX for deterministic tie-breaking.

    :param scores: Ranking scores.
    :type scores: Vec
    :param capex_values: Project CAPEX values.
    :type capex_values: Vec
    :return: Sorted project indices.
    :rtype: IntVec
    """
    indices: IntVec = np.arange(len(scores), dtype=int)
    return np.lexsort((indices, capex_values, -scores)).astype(int)


def get_toot_pint_seed_population(obj_func: Callable,
                                  n_var: int,
                                  lb: Vec | IntVec,
                                  ub: Vec | IntVec,
                                  n_obj: int,
                                  objective_names: StrVec,
                                  variable_names: StrVec,
                                  pop_size: int,
                                  report_text: Callable | None = None,
                                  logger: Logger | None = None,
                                  record_results: bool = False) -> tuple[IntMat, Mat]:
    """
    Build an optional NSGA3 warm-start population from the direct PINT and TOOT evaluations.

    The returned arrays are plain NumPy matrices so they can be passed to :func:`NSGA_3` without introducing a
    dependency between the CBA helper and the evolutionary wrapper.

    :param obj_func: Objective function with signature ``obj_func(x=..., record_results=...)``.
    :type obj_func: Callable
    :param n_var: Number of decision variables.
    :type n_var: int
    :param lb: Lower bound vector.
    :type lb: Vec | IntVec
    :param ub: Upper bound vector.
    :type ub: Vec | IntVec
    :param n_obj: Number of objectives.
    :type n_obj: int
    :param objective_names: Objective names of the active problem.
    :type objective_names: StrVec
    :param variable_names: Variable names of the active problem.
    :type variable_names: StrVec
    :param pop_size: Requested warm-start population size.
    :type pop_size: int
    :param report_text: Optional progress text callback.
    :type report_text: Callable | None
    :param logger: Optional logger.
    :type logger: Logger | None
    :param record_results: Record the evaluated seed points in the results object.
    :type record_results: bool
    :return: Seed decision vectors and aligned objective vectors.
    :rtype: tuple[IntMat, Mat]
    """
    if pop_size > 0:
        pass
    else:
        return np.zeros((0, n_var), dtype=int), np.zeros((0, n_obj), dtype=float)

    reference_combination: IntVec = get_reference_combination(lb=lb)
    target_combination: IntVec = get_target_combination(n_var=n_var, lb=lb, ub=ub)
    baseline_objectives: Vec = obj_func(x=reference_combination.copy(), record_results=record_results)
    target_objectives: Vec = obj_func(x=target_combination.copy(), record_results=record_results)

    if len(baseline_objectives) == n_obj:
        pass
    else:
        raise ValueError("The baseline objective vector size does not match n_obj")

    capex_idx: int = get_capex_objective_index(objective_names=objective_names)
    objective_scale: Vec = get_objective_scale(baseline=baseline_objectives, target=target_objectives)
    project_scores: Vec = np.zeros(n_var, dtype=float)
    project_capex: Vec = np.zeros(n_var, dtype=float)
    pint_combinations: IntMat = np.zeros((n_var, n_var), dtype=int)
    pint_objectives: Mat = np.zeros((n_var, n_obj), dtype=float)
    toot_combinations: IntMat = np.zeros((n_var, n_var), dtype=int)
    toot_objectives: Mat = np.zeros((n_var, n_obj), dtype=float)

    for idx in range(n_var):
        if report_text is None:
            pass
        else:
            report_text(f"Evaluating project {idx} with PINT/TOOT warm-start logic...")

        activation_value: int = get_candidate_activation_value(ub=ub, idx=idx)
        pint_combination: IntVec = reference_combination.copy()
        pint_combination[idx] = activation_value
        pint_combinations[idx, :] = pint_combination

        # PINT gives the single-project "project in" combinations used for the hybrid warm-start.
        pint_objective_vector: Vec = obj_func(x=pint_combination.copy(), record_results=record_results)
        pint_objectives[idx, :] = pint_objective_vector
        pint_delta: Vec = baseline_objectives - pint_objective_vector

        toot_combination: IntVec = target_combination.copy()
        toot_combination[idx] = reference_combination[idx]
        toot_combinations[idx, :] = toot_combination

        # TOOT gives complementary "take one out" combinations that broaden the first NSGA3 generation.
        toot_objective_vector: Vec = obj_func(x=toot_combination.copy(), record_results=record_results)
        toot_objectives[idx, :] = toot_objective_vector
        toot_delta: Vec = toot_objective_vector - target_objectives

        if capex_idx > -1:
            pint_capex: float = float(pint_objective_vector[capex_idx] - baseline_objectives[capex_idx])
            toot_capex: float = float(target_objectives[capex_idx] - toot_objective_vector[capex_idx])
            project_capex[idx] = pint_capex
        else:
            pint_capex = 0.0
            toot_capex = 0.0
            project_capex[idx] = 0.0

        pint_score: float = get_normalized_cba_score(delta_objectives=pint_delta,
                                                     capex_delta=pint_capex,
                                                     capex_idx=capex_idx,
                                                     scale=objective_scale)
        toot_score: float = get_normalized_cba_score(delta_objectives=toot_delta,
                                                     capex_delta=toot_capex,
                                                     capex_idx=capex_idx,
                                                     scale=objective_scale)
        project_scores[idx] = 0.5 * (pint_score + toot_score)

        if logger is None:
            pass
        else:
            logger.add_info(msg="PINT/TOOT NSGA3 warm-start score",
                            device=str(variable_names[idx]),
                            value=f"{project_scores[idx]:.6f}",
                            expected_value=f"PINT {pint_score:.6f} / TOOT {toot_score:.6f}")

    sorted_indices: IntVec = get_sorted_project_indices(scores=project_scores,
                                                        capex_values=project_capex)
    candidate_population: IntMat = np.zeros((2 * n_var + 2, n_var), dtype=int)
    candidate_objectives: Mat = np.zeros((2 * n_var + 2, n_obj), dtype=float)
    candidate_count: int = 0
    candidate_population[candidate_count, :] = reference_combination
    candidate_objectives[candidate_count, :] = baseline_objectives
    candidate_count += 1

    for project_idx in sorted_indices:
        project_pos: int = int(project_idx)
        candidate_population[candidate_count, :] = pint_combinations[project_pos, :]
        candidate_objectives[candidate_count, :] = pint_objectives[project_pos, :]
        candidate_count += 1
        candidate_population[candidate_count, :] = toot_combinations[project_pos, :]
        candidate_objectives[candidate_count, :] = toot_objectives[project_pos, :]
        candidate_count += 1

    candidate_population[candidate_count, :] = target_combination
    candidate_objectives[candidate_count, :] = target_objectives
    candidate_count += 1

    unique_population_rows: list[IntVec] = list()
    unique_objective_rows: list[Vec] = list()
    row_idx: int

    for row_idx in range(candidate_count):
        current_row: IntVec = candidate_population[row_idx, :]
        is_duplicate: bool = False
        existing_row: IntVec

        for existing_row in unique_population_rows:
            if np.array_equal(existing_row, current_row):
                is_duplicate = True
            else:
                pass

        if is_duplicate:
            pass
        else:
            unique_population_rows.append(current_row.copy())
            unique_objective_rows.append(candidate_objectives[row_idx, :].copy())

        if len(unique_population_rows) < pop_size:
            pass
        else:
            break

    if len(unique_population_rows) > 0:
        seed_population: IntMat = np.asarray(unique_population_rows, dtype=int)
        seed_objectives: Mat = np.asarray(unique_objective_rows, dtype=float)
    else:
        seed_population = np.zeros((0, n_var), dtype=int)
        seed_objectives = np.zeros((0, n_obj), dtype=float)

    return seed_population, seed_objectives


def TOOT_PINT_CBA(obj_func: Callable,
                  n_var: int,
                  lb: Vec | IntVec,
                  ub: Vec | IntVec,
                  n_obj: int,
                  objective_names: StrVec,
                  variable_names: StrVec,
                  report_text: Callable | None = None,
                  logger: Logger | None = None) -> IntVec:
    """
    Run a CBA-like independent project ranking based on PINT and TOOT evaluations.

    The function uses the provided objective function directly, like ``NSGA_3`` does. The displayed metrics remain
    the objectives of the passed problem because this function never fabricates alternative objective vectors.

    :param obj_func: Objective function with signature ``obj_func(x=..., record_results=...)``.
    :type obj_func: Callable
    :param n_var: Number of decision variables.
    :type n_var: int
    :param lb: Lower bound vector.
    :type lb: Vec | IntVec
    :param ub: Upper bound vector.
    :type ub: Vec | IntVec
    :param n_obj: Number of objectives.
    :type n_obj: int
    :param objective_names: Objective names of the active problem.
    :type objective_names: StrVec
    :param variable_names: Variable names of the active problem.
    :type variable_names: StrVec
    :param report_text: Optional progress text callback.
    :type report_text: Callable | None
    :param logger: Optional logger.
    :type logger: Logger | None
    :return: Best-ranked combination according to the CBA sequence.
    :rtype: IntVec
    """
    reference_combination: IntVec = get_reference_combination(lb=lb)
    target_combination: IntVec = get_target_combination(n_var=n_var, lb=lb, ub=ub)

    # The reference case is the baseline used in the PINT logic.
    baseline_objectives: Vec = obj_func(x=reference_combination.copy(), record_results=True)

    # The target case is only used as the TOOT comparison basis and is not added to the visible results.
    target_objectives: Vec = obj_func(x=target_combination.copy(), record_results=False)

    if len(baseline_objectives) == n_obj:
        pass
    else:
        raise ValueError("The baseline objective vector size does not match n_obj")

    capex_idx: int = get_capex_objective_index(objective_names=objective_names)
    objective_scale: Vec = get_objective_scale(baseline=baseline_objectives, target=target_objectives)

    project_scores: Vec = np.zeros(n_var, dtype=float)
    project_capex: Vec = np.zeros(n_var, dtype=float)
    st: float = timeit.default_timer()

    for idx in range(n_var):
        if report_text is None:
            pass
        else:
            report_text(f"Evaluating project {idx} with PINT/TOOT logic...")

        activation_value: int = get_candidate_activation_value(ub=ub, idx=idx)
        pint_combination: IntVec = reference_combination.copy()
        pint_combination[idx] = activation_value

        # PINT adds one project to the reference grid.
        pint_objectives: Vec = obj_func(x=pint_combination, record_results=True)
        pint_delta: Vec = baseline_objectives - pint_objectives

        # TOOT removes one project from the target grid to estimate its marginal contribution there.
        toot_combination: IntVec = target_combination.copy()
        toot_combination[idx] = reference_combination[idx]
        toot_objectives: Vec = obj_func(x=toot_combination, record_results=False)
        toot_delta: Vec = toot_objectives - target_objectives

        if capex_idx > -1:
            pint_capex: float = float(pint_objectives[capex_idx] - baseline_objectives[capex_idx])
            toot_capex: float = float(target_objectives[capex_idx] - toot_objectives[capex_idx])
            project_capex[idx] = pint_capex
        else:
            pint_capex = 0.0
            toot_capex = 0.0
            project_capex[idx] = 0.0

        pint_score: float = get_normalized_cba_score(delta_objectives=pint_delta,
                                                     capex_delta=pint_capex,
                                                     capex_idx=capex_idx,
                                                     scale=objective_scale)

        toot_score: float = get_normalized_cba_score(delta_objectives=toot_delta,
                                                     capex_delta=toot_capex,
                                                     capex_idx=capex_idx,
                                                     scale=objective_scale)

        project_scores[idx] = 0.5 * (pint_score + toot_score)

        if logger is None:
            pass
        else:
            logger.add_info(msg="Independent CBA project score",
                            device=str(variable_names[idx]),
                            value=f"{project_scores[idx]:.6f}",
                            expected_value=f"PINT {pint_score:.6f} / TOOT {toot_score:.6f}")

    sorted_indices: IntVec = get_sorted_project_indices(scores=project_scores,
                                                        capex_values=project_capex)

    cumulative_combination: IntVec = reference_combination.copy()

    # The first ranked project has already been evaluated as a PINT case above, so only new cumulative
    # combinations are added from the second project onwards.
    for position, project_idx in enumerate(sorted_indices):
        activation_value: int = get_candidate_activation_value(ub=ub, idx=int(project_idx))
        cumulative_combination[int(project_idx)] = activation_value

        if position > 0:
            if report_text is None:
                pass
            else:
                report_text(f"Evaluating cumulative combination ranked up to project {project_idx}...")

            obj_func(x=cumulative_combination.copy(), record_results=True)
        else:
            pass

    et: float = timeit.default_timer()

    if logger is None:
        pass
    else:
        logger.add_info(msg="Independent CBA sequence time (s)",
                        value=f"{et - st:.6f}")

    if len(sorted_indices) > 0:
        best_combination: IntVec = reference_combination.copy()
        best_combination[int(sorted_indices[0])] = get_candidate_activation_value(ub=ub,
                                                                                  idx=int(sorted_indices[0]))
        return best_combination
    else:
        return reference_combination
