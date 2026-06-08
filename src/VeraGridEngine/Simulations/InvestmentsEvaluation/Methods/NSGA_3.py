# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.population import Population
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.core.mixed import MixedVariableSampling
from pymoo.core.sampling import Sampling
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.core.termination import Termination
from pymoo.core.mutation import Mutation
from VeraGridEngine.basic_structures import Vec, IntVec, IntMat, Mat


def finalize_seed_population(seed_population: IntMat,
                             seed_objectives: Mat | None,
                             lb: Vec | IntVec,
                             ub: Vec | IntVec) -> tuple[IntMat, Mat | None]:
    """
    Clip, round and deduplicate a user-provided seed population.

    :param seed_population: Candidate initial population.
    :type seed_population: IntMat
    :param seed_objectives: Optional objective matrix aligned with ``seed_population``.
    :type seed_objectives: Mat | None
    :param lb: Lower decision-vector bounds.
    :type lb: Vec | IntVec
    :param ub: Upper decision-vector bounds.
    :type ub: Vec | IntVec
    :return: Clean seed population and aligned objective matrix.
    :rtype: tuple[IntMat, Mat | None]
    """
    lb_arr: IntVec = np.asarray(lb, dtype=int)
    ub_arr: IntVec = np.asarray(ub, dtype=int)
    clipped_population: IntMat = np.asarray(np.rint(seed_population), dtype=int)
    clipped_population = np.atleast_2d(clipped_population)
    clipped_population = np.clip(clipped_population, lb_arr, ub_arr)

    if clipped_population.shape[1] == len(lb_arr):
        pass
    else:
        raise ValueError("The seed population does not match the problem dimension")

    objective_matrix: Mat | None
    if seed_objectives is None:
        objective_matrix = None
    else:
        objective_matrix = np.asarray(seed_objectives, dtype=float)
        objective_matrix = np.atleast_2d(objective_matrix)

        if len(objective_matrix) == len(clipped_population):
            pass
        else:
            raise ValueError("The seed population and objective arrays must have the same row count")

    # Preserve the first occurrence of each point so the caller controls the seed priority order.
    unique_rows: list[IntVec] = list()
    unique_objective_rows: list[Vec] = list()
    row_idx: int

    for row_idx in range(len(clipped_population)):
        current_row: IntVec = clipped_population[row_idx, :]
        is_duplicate: bool = False
        existing_row: IntVec

        for existing_row in unique_rows:
            if np.array_equal(existing_row, current_row):
                is_duplicate = True
            else:
                pass

        if is_duplicate:
            pass
        else:
            unique_rows.append(current_row.copy())

            if objective_matrix is None:
                pass
            else:
                unique_objective_rows.append(objective_matrix[row_idx, :].copy())

    if len(unique_rows) > 0:
        unique_population: IntMat = np.asarray(unique_rows, dtype=int)
    else:
        unique_population = np.zeros((0, len(lb_arr)), dtype=int)

    if objective_matrix is None:
        unique_objectives: Mat | None = None
    elif len(unique_objective_rows) > 0:
        unique_objectives = np.asarray(unique_objective_rows, dtype=float)
    else:
        unique_objectives = np.zeros((0, 0), dtype=float)

    return unique_population, unique_objectives


def get_nsga3_initial_population(problem: ElementwiseProblem,
                                 pop_size: int,
                                 initial_population: IntMat,
                                 initial_objectives: Mat | None) -> Population:
    """
    Build an optional pymoo initial population from plain NumPy arrays.

    :param problem: pymoo problem instance.
    :type problem: ElementwiseProblem
    :param pop_size: Requested NSGA3 population size.
    :type pop_size: int
    :param initial_population: Seed decision vectors.
    :type initial_population: IntMat
    :param initial_objectives: Optional objective vectors aligned with ``initial_population``.
    :type initial_objectives: Mat | None
    :return: pymoo population object with optional pre-evaluated individuals.
    :rtype: Population
    """
    fallback_sampling: Sampling = SkewedIntegerSamplingRange()
    n_seed: int = min(len(initial_population), pop_size)
    samples: IntMat = np.zeros((pop_size, int(problem.n_var)), dtype=int)

    # Copy the externally-provided combinations first so NSGA3 starts from the intended warm-start population.
    if n_seed > 0:
        samples[:n_seed, :] = initial_population[:n_seed, :]
    else:
        pass

    remaining_samples: int = pop_size - n_seed

    # Fill the remaining rows with the original sampler so the warm-start stays optional and non-invasive.
    if remaining_samples > 0:
        fallback_population: IntMat = fallback_sampling._do(problem=problem, n_samples=remaining_samples)
        samples[n_seed:, :] = np.asarray(fallback_population, dtype=int)
    else:
        pass

    population: Population = Population.new(X=samples)

    # Mark the provided objective values as already evaluated so pymoo does not call the objective function again.
    if initial_objectives is None:
        pass
    else:
        population[:n_seed].set("F", initial_objectives[:n_seed, :])

        for row_idx in range(n_seed):
            population[row_idx].evaluated.update({"F", "G", "H"})

    return population


class IntegerRandomSamplingVeraGrid(Sampling):
    def _do(self, problem, n_samples, **kwargs):
        xl = np.asarray(problem.xl, dtype=int)
        xu = np.asarray(problem.xu, dtype=int)

        n_var = len(xl)
        X = np.zeros((n_samples, n_var), dtype=int)

        for j in range(n_var):
            values = np.arange(xl[j], xu[j] + 1)
            for i in range(n_samples):
                X[i, j] = np.random.choice(values)

        return X


class UniformBinarySampling(Sampling):
    """
    UniformBinarySampling
    """

    def _do(self, problem, n_samples, **kwargs):
        num_ones = np.linspace(0, problem.n_var, n_samples, dtype=int)
        num_ones[-1] = problem.n_var
        ones_into_array = np.zeros((n_samples, problem.n_var), dtype=int)
        # Fill ones_into_array randomly
        for i, num in enumerate(num_ones):
            ones_into_array[i, :num] = 1
            np.random.shuffle(ones_into_array[i])

        return ones_into_array


class SkewedBinarySampling(Sampling):
    """
    SkewedBinarySampling
    """

    def _do(self, problem, n_samples, **kwargs):
        max_ones = int(problem.n_var * 1)
        num_ones = (np.linspace(0, 1, n_samples) ** 3 * max_ones).astype(int)
        num_ones[-1] = max_ones
        ones_into_array = np.zeros((n_samples, problem.n_var), dtype=int)

        # Fill ones_into_array randomly
        for i, num in enumerate(num_ones):
            ones_into_array[i, :num] = 1
            np.random.shuffle(ones_into_array[i])

        # # Add rows with only one '1'
        # additional_rows = 100
        # for _ in range(additional_rows):
        #     row = np.zeros(problem.n_var, dtype=int)
        #     row[np.random.randint(0, problem.n_var)] = 1
        #     ones_into_array = np.vstack([ones_into_array, row])

        return ones_into_array


class SkewedIntegerSamplingRange(Sampling):
    """
    SkewedIntegerSampling generates samples skewed toward the lower bounds
    but spread across the full lb–ub range. Works for integer variables.
    """

    def _do(self, problem, n_samples, **kwargs):
        xl = np.asarray(problem.xl, dtype=int)
        xu = np.asarray(problem.xu, dtype=int)

        n_var = len(xl)
        X = np.zeros((n_samples, n_var), dtype=int)

        # Generate skewed samples per variable
        for j in range(n_var):
            # Create skewed samples in [0, 1]
            skewed = (np.linspace(0, 1, n_samples) ** 3)

            # Scale to range [xl[j], xu[j]]
            range_j = xu[j] - xl[j]
            values = (skewed * range_j + xl[j]).astype(int)

            # Shuffle for diversity
            np.random.shuffle(values)
            X[:, j] = values

        return X


class QuadBinarySampling(Sampling):
    """
    QuadBinarySampling
    """

    def _do(self, problem, n_samples, **kwargs):
        max_ones = int(problem.n_var * 1)
        half_samples = n_samples // 2
        # Adjust the num_ones calculation to create a distribution that is quadratic in the first half
        num_ones = (np.linspace(0, 1, half_samples) * max_ones).astype(int)
        # Fill the rest of the array with 0s quadratically
        num_zeros = (np.linspace(1, 0, n_samples - half_samples) ** 3 * max_ones).astype(int)
        num_ones = np.concatenate([num_ones, num_zeros])
        ones_into_array = np.zeros((n_samples, problem.n_var), dtype=int)
        # Fill ones_into_array randomly
        for i, num in enumerate(num_ones):
            ones_into_array[i, :num] = 1
            np.random.shuffle(ones_into_array[i])

        return ones_into_array


class BitflipMutation(Mutation):
    """
    BitflipMutation
    """

    def _do(self, problem, x, **kwargs):
        mask = np.random.random(x.shape) < self.get_prob_var(problem)
        x[mask] = 1 - x[mask]
        return x


class GridNsga(ElementwiseProblem):
    """
    Problem formulation packaging to use the pymoo library
    """

    def __init__(self, obj_func, n_var, n_obj, lb: Vec | IntVec, ub: Vec | IntVec):
        """

        :param obj_func:
        :param n_var:
        :param n_obj:
        """
        super().__init__(n_var=n_var,
                         n_obj=n_obj,
                         n_ieq_constr=0,
                         xl=lb,
                         xu=ub,
                         vtype=int)
        self.obj_func = obj_func

    def _evaluate(self, x, out, *args, **kwargs):
        """

        :param x:
        :param out:
        :param args:
        :param kwargs:
        :return:
        """
        out["F"] = self.obj_func(x)


def NSGA_3(obj_func,
           n_var: int, lb: Vec | IntVec, ub: Vec | IntVec,
           n_obj: int,
           n_partitions: int = 100,
           max_evals: int = 30,
           pop_size: int = 1,
           crossover_prob: float = 0.05,
           mutation_probability=0.5,
           eta: float = 3.0,
           initial_population: IntMat | None = None,
           initial_objectives: Mat | None = None):
    """
    NSGA3 designed for pareto investments
    :param obj_func: Objective function pointer [f(x)]
    :param n_partitions: Number of partitions
    :param n_var: Number of variables
    :param lb: Array of x lower boundaries
    :param ub: Array of x upper boundaries
    :param n_obj: Number of objectives
    :param max_evals: Maximum number of evaluations
    :param pop_size: Population size
    :param crossover_prob: Crossover probability
    :param mutation_probability: Mutation probability
    :param eta: eta parameter for the SBX crossover
    :param initial_population: Optional integer population used to seed the first NSGA3 generation.
    :type initial_population: IntMat | None
    :param initial_objectives: Optional objective vectors aligned with ``initial_population``.
    :type initial_objectives: Mat | None
    :return: X, f
    """
    problem = GridNsga(obj_func, n_var, n_obj, lb=lb, ub=ub)

    ref_dirs = get_reference_directions("das-dennis", n_obj, n_partitions=n_partitions) # ref_dirs = get_reference_directions("reduction", n_obj, n_partitions, seed=1)
    sampling: Sampling | Population

    # Keep warm-starting entirely optional. When nothing is passed, NSGA3 behaves exactly as before.
    if initial_population is None:
        sampling = SkewedIntegerSamplingRange()
    else:
        seed_population: IntMat
        seed_objectives: Mat | None
        seed_population, seed_objectives = finalize_seed_population(seed_population=initial_population,
                                                                    seed_objectives=initial_objectives,
                                                                    lb=lb,
                                                                    ub=ub)
        sampling = get_nsga3_initial_population(problem=problem,
                                                pop_size=pop_size,
                                                initial_population=seed_population,
                                                initial_objectives=seed_objectives)

    algorithm = NSGA3(pop_size=pop_size,
                      sampling=sampling,
                      # IntegerRandomSamplingVeraGrid(), # SkewedBinarySampling(),
                      crossover=SBX(prob=crossover_prob,
                                    eta=eta,
                                    vtype=float,
                                    repair=RoundingRepair()),
                      mutation=BitflipMutation(prob=mutation_probability,
                                               prob_var=0.4,
                                               repair=RoundingRepair()),
                      eliminate_duplicates=True,
                      ref_dirs=ref_dirs)

    # term = Termination()

    res = minimize(problem=problem,
                   algorithm=algorithm,
                   termination=('n_eval', max_evals),
                   seed=1,
                   verbose=True,
                   save_history=False)

    return res.X, res.F
