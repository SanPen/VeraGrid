# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from math import comb
from typing import Tuple, Union

import numpy as np

from VeraGridEngine.basic_structures import IntVec, Vec
from VeraGridEngine.enumerations import DeviceType, SimulationTypes
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_results import (
    InvestmentsEvaluationResults,
)
from VeraGridEngine.Simulations.CatalogueOptimization.nsga3_integer import NSGA_3_integer
from VeraGridEngine.Simulations.CatalogueOptimization.Problems.catalogue_problem import (
    CatalogueOptimizationProblem,
)


class CatalogueOptimizationOptions(OptionsTemplate):
    """
    Options for the catalogue optimization driver.

    Mirrors the relevant subset of `InvestmentsEvaluationOptions`: only the controls that the GUI
    currently exposes for catalogue optimization (max evaluations + power flow options).
    """

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="max_eval", tpe=int),
        GCProp(key="pf_options", tpe=DeviceType.SimulationOptionsDevice),
    )

    def __init__(self,
                 max_eval: int,
                 pf_options: Union[PowerFlowOptions, None] = None) -> None:
        """
        Constructor.

        :param max_eval: maximum number of black-box objective evaluations the optimizer may perform.
        :param pf_options: power flow options used by the inner power-flow evaluations. When `None`
            a default `PowerFlowOptions` is created.
        """
        OptionsTemplate.__init__(self, name='CatalogueOptimizationOptions')

        # Maximum number of objective-function evaluations (NSGA-3 termination criterion).
        self.max_eval: int = int(max_eval)

        # Power flow options reused by the inner PF runs. We instantiate a default one if the caller
        # did not pass anything, so the driver never has to handle a `None` afterwards.
        if pf_options is None:
            self.pf_options: PowerFlowOptions = PowerFlowOptions()
        else:
            self.pf_options = pf_options


class CatalogueOptimizationDriver(DriverTemplate):
    """
    Driver that optimises the per-branch template selection from the grid catalogue using NSGA-3.

    The driver is a thin orchestrator: the heavy lifting (apply / evaluate / revert) lives in the
    `CatalogueOptimizationProblem`, while the optimization loop is delegated to `NSGA_3`.
    """
    __slots__ = (
        "options",
        "problem",
    )

    name = 'Catalogue optimization'
    tpe = SimulationTypes.CatalogueOptimization_run

    def __init__(self,
                 grid: MultiCircuit,
                 options: CatalogueOptimizationOptions,
                 problem: CatalogueOptimizationProblem) -> None:
        """
        Constructor.

        :param grid: MultiCircuit being optimized.
        :param options: catalogue optimization options.
        :param problem: pre-built `CatalogueOptimizationProblem`. Building the problem is left to the
            caller because it can fail (no compatible templates), and we want that failure handled
            in the GUI layer with a user-facing dialog rather than inside the driver.
        """
        super().__init__(grid=grid)

        # Store options and problem.
        self.options: CatalogueOptimizationOptions = options
        self.problem: CatalogueOptimizationProblem = problem

        # Inherit the warnings emitted while building the problem (unsupported branches, dropped
        # degenerate slots, ...) so they reach the user via the driver's logger.
        if problem is not None:
            self.logger += problem.logger
        else:
            pass

        # Build the results container with the proper shapes.
        # `+1` slot accommodates the explicit baseline evaluation that we run before the optimization.
        if problem is not None:
            self.results: InvestmentsEvaluationResults = InvestmentsEvaluationResults(
                f_names=self.problem.get_objectives_names(),
                x_names=self.problem.get_vars_names(),
                plot_x_idx=self.problem.plot_x_idx,
                plot_y_idx=self.problem.plot_y_idx,
                max_eval=self.options.max_eval + 1,
            )
        else:
            self.results = InvestmentsEvaluationResults(
                f_names=np.array([]),
                x_names=np.array([]),
                plot_x_idx=0,
                plot_y_idx=0,
                max_eval=self.options.max_eval + 1,
            )

    def get_steps(self):
        """
        Get the list of evaluation indices used by the GUI to display progress.

        :return: list of step labels.
        """
        return self.results.get_index()

    def objective_function(self, x: IntVec, record_results: bool = True) -> Vec:
        """
        Evaluate the catalogue problem at `x` and (optionally) record the result.

        :param x: integer decision vector with `x[i]` indexing the template within the i-th pool.
        :param record_results: when True the result is appended to the results container.
        :return: six-objective vector returned by `CatalogueOptimizationProblem.objective_function`.
        """
        # Delegate evaluation to the problem (apply templates, run PF, revert).
        objectives: Vec = self.problem.objective_function(x)

        if record_results:
            # Store both the decision vector and the objective vector for later inspection.
            self.results.add(x_vec=x, f_vec=objectives)
        else:
            pass

        # Push a progress update to the GUI based on the running evaluation counter.
        self.report_progress2(self.results.current_evaluation, self.results.max_eval)

        return objectives

    def _run_nsga3(self) -> None:
        """
        Execute the NSGA-3 optimization loop on the catalogue problem.

        The population size is sized to the number of decision slots, and the number of Das-Dennis
        partitions is grown to use as many reference directions as the population allows.
        """
        self.report_text("Evaluating catalogue templates with NSGA-3...")

        # Decision-space dimensionality (number of optimisable branch slots).
        dim: int = self.problem.n_vars()

        # Number of objectives is fixed by the problem (no need to wait for the baseline run).
        n_obj: int = self.problem.n_objectives()

        # Minimum Das-Dennis reference set, which is the floor for pop_size:
        # ref_dirs(n_partitions=1) = C(1 + n_obj - 1, n_obj - 1) = n_obj.
        # NSGA-3 emits a warning when pop_size < ref_dirs, so we lift the population to at least
        # `n_obj` even when the user only selected a handful of branches.
        min_ref_dirs: int = n_obj

        # Population size: proportional to dimensionality, but never below the reference-set floor.
        pop_size: int = max(int(round(dim)), min_ref_dirs)

        # Baseline evaluation at x = zero index for every slot. Two purposes:
        #  - It provides a reference point in the results matrix.
        #  - It makes sure the snapshot/restore logic is exercised at least once before NSGA-3.
        baseline_x: IntVec = np.zeros(dim, dtype=int)
        self.objective_function(x=baseline_x)

        # Find the largest n_partitions such that the Das-Dennis reference set still fits in pop_size.
        # ref_dirs cardinality = C(n_partitions + n_obj - 1, n_obj - 1).
        n_partitions: int = 1
        while comb(n_partitions + 1 + n_obj - 1, n_obj - 1) <= pop_size:
            n_partitions += 1

        # Run the integer-aware NSGA-3. The integer bounds (lb / ub) come straight from the
        # problem. We use `NSGA_3_integer` (PolynomialMutation) instead of the investments
        # `NSGA_3` (BitflipMutation) because our slot indices live in `[0, len(pool) - 1]` rather
        # than `{0, 1}`.
        X, obj_values = NSGA_3_integer(
            obj_func=self.objective_function,
            n_partitions=n_partitions,
            n_var=dim,
            lb=self.problem.x_min,
            ub=self.problem.x_max,
            n_obj=n_obj,
            max_evals=self.options.max_eval,
            pop_size=pop_size,
            crossover_prob=0.8,
            mutation_probability=0.1,
            eta_crossover=30.0,
            eta_mutation=20.0,
        )

        # Record the best Pareto member (row 0) as the "selected" combination for the GUI.
        # `X` is shape (n_pareto, n_var) from pymoo, so we want the full decision vector of the
        # first Pareto member, not the first decision variable across all members.
        self.results.set_best_combination(combination=X[0, :])

    def _log_best_combination(self) -> None:
        """
        Append a logger entry per branch describing which catalogue template was selected as best.
        """
        # `f_best` holds the integer indices for the best Pareto member.
        best_x: IntVec = self.results.f_best

        # Walk through every decision slot and report the chosen template.
        for i in range(self.problem.n_vars()):

            slot_idx: int = int(best_x[i])
            if slot_idx < 0:
                slot_idx = 0
            elif slot_idx > len(self.problem.pools[i]) - 1:
                slot_idx = len(self.problem.pools[i]) - 1
            else:
                pass

            branch = self.problem.branches[i]
            chosen_template = self.problem.pools[i][slot_idx]

            self.logger.add_info(msg="Best catalogue template",
                                 device=branch.name,
                                 device_property=type(chosen_template).__name__,
                                 value=chosen_template.name)

    def run(self) -> None:
        """
        Entry point invoked by the session thread; runs NSGA-3 and finalises the results.
        """
        self.tic()
        self.report_text("Compiling and configuring...")

        self.logger.add_info(msg="Solver", value="NSGA-3")
        self.logger.add_info(msg="Max evaluations", value=f"{self.options.max_eval}")
        self.logger.add_info(msg="Decision slots", value=f"{self.problem.n_vars()}")

        # TODO: when time-series support is added, branch on a method enum here.
        self._run_nsga3()

        # Compress the recorded data into the final form expected by the GUI viewer.
        self.report_text("Finalizing the results object...")
        self.results.finalize()

        # Emit a per-slot summary of the chosen templates for traceability.
        self._log_best_combination()

        self.toc()
        self.report_done()
