# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
NSGA-3 wrapper specialised for the catalogue optimization problem.

Differs from `VeraGridEngine.Simulations.InvestmentsEvaluation.Methods.NSGA_3` only in the mutation
operator: catalogue indices are integer variables in `[0, len(pool) - 1]` and the pools can hold
many templates (well above {0, 1}). The investments NSGA-3 uses `BitflipMutation` (designed for
binary variables) which produces `1 - x`; for x>=2 that gives a negative value that then has to be
clipped to the boundary, biasing the search toward the lower bound. Here we use
`PolynomialMutation` (bounded by `[xl, xu]`) plus `RoundingRepair` so each mutation stays within
the valid integer range and actually explores neighbouring slots.
"""
from __future__ import annotations

from typing import Callable, Tuple

from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PolynomialMutation
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions

from VeraGridEngine.basic_structures import Vec, IntVec
from VeraGridEngine.Simulations.InvestmentsEvaluation.Methods.NSGA_3 import (
    GridNsga,
    SkewedIntegerSamplingRange,
)


def NSGA_3_integer(obj_func: Callable[[IntVec], Vec],
                   n_var: int,
                   lb: IntVec,
                   ub: IntVec,
                   n_obj: int,
                   n_partitions: int = 100,
                   max_evals: int = 30,
                   pop_size: int = 1,
                   crossover_prob: float = 0.05,
                   mutation_probability: float = 0.5,
                   mutation_per_var_prob: float = 0.4,
                   eta_crossover: float = 30.0,
                   eta_mutation: float = 20.0) -> Tuple[IntVec, Vec]:
    """
    NSGA-3 for problems whose decision vector is an integer index in `[lb, ub]` per slot.

    The configuration matches `NSGA_3` from the investments evaluation module except for the
    mutation operator (`PolynomialMutation` instead of `BitflipMutation`), which is the right
    choice here because our variables are not binary.

    :param obj_func: black-box objective function `f(x)` returning a vector of `n_obj` values.
    :param n_var: number of decision variables.
    :param lb: integer lower bound array (length `n_var`).
    :param ub: integer upper bound array (length `n_var`).
    :param n_obj: number of objectives.
    :param n_partitions: Das-Dennis partition count for the reference directions.
    :param max_evals: maximum number of objective-function evaluations.
    :param pop_size: population size.
    :param crossover_prob: per-individual crossover probability.
    :param mutation_probability: per-individual mutation probability.
    :param mutation_per_var_prob: per-variable mutation probability inside an individual.
    :param eta_crossover: distribution index for SBX crossover (higher = closer to parents).
    :param eta_mutation: distribution index for polynomial mutation (higher = smaller jumps).
    :return: tuple `(X, F)` where `X` is the Pareto-set decision vectors (shape `(n_pareto, n_var)`)
        and `F` is the corresponding objective values (shape `(n_pareto, n_obj)`).
    """
    # Wrap the user objective into pymoo's elementwise problem; lb/ub become problem.xl/xu.
    problem = GridNsga(obj_func=obj_func, n_var=n_var, n_obj=n_obj, lb=lb, ub=ub)

    # Das-Dennis reference directions (same scheme as the investments NSGA-3).
    ref_dirs = get_reference_directions("das-dennis", n_obj, n_partitions=n_partitions)

    # Build the NSGA-3 algorithm with integer-aware operators.
    # - SBX crossover with RoundingRepair: produces real-valued children that are snapped to ints.
    # - PolynomialMutation: bounded distribution within [xl, xu]; never goes out of range.
    #   RoundingRepair rounds the (real-valued) PM output to the nearest valid integer.
    algorithm = NSGA3(pop_size=pop_size,
                      sampling=SkewedIntegerSamplingRange(),
                      crossover=SBX(prob=crossover_prob,
                                    eta=eta_crossover,
                                    vtype=float,
                                    repair=RoundingRepair()),
                      mutation=PolynomialMutation(prob=mutation_probability,
                                                  prob_var=mutation_per_var_prob,
                                                  eta=eta_mutation,
                                                  vtype=float,
                                                  repair=RoundingRepair()),
                      eliminate_duplicates=True,
                      ref_dirs=ref_dirs)

    # Run the optimisation; termination is on the evaluation count budget.
    res = minimize(problem=problem,
                   algorithm=algorithm,
                   termination=('n_eval', max_evals),
                   seed=1,
                   verbose=True,
                   save_history=False)

    return res.X, res.F
