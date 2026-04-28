# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, Union

import numpy as np

from VeraGridEngine.basic_structures import Vec, IntVec, StrVec, Logger
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.black_box_problem_template import (
    BlackBoxProblemTemplate,
)
from VeraGridEngine.Utils.scores import (
    get_overload_score,
    get_voltage_phase_score,
    get_voltage_module_score,
    TechnoEconomicScores,
)
from VeraGridEngine.Simulations.CatalogueOptimization.catalogue_utils import (
    Branch,
    Template,
    LineSnapshot,
    TransformerSnapshot,
    build_catalogue_pool,
    take_snapshot,
    template_capex,
)


class CatalogueOptimizationProblem(BlackBoxProblemTemplate):
    """
    Multi-objective black-box problem that selects, for each user-pre-selected branch, a template
    from the grid's catalogue so as to minimise the six techno-economic scores
    (losses, overload, voltage module, voltage angle, financial, technical).

    The decision vector `x` is integer-valued: `x[i]` is the index of the chosen template within the
    pool associated with branch `branches[i]`.
    """

    def __init__(self,
                 grid: MultiCircuit,
                 pf_options: PowerFlowOptions,
                 selected_branches: List[Branch],
                 voltage_tolerance: float = 0.1) -> None:
        """
        Constructor.

        :param grid: MultiCircuit to be optimized (also the source of the template catalogues).
        :param pf_options: power flow options used to evaluate each candidate combination.
        :param selected_branches: branches the user has pre-selected on the schematic. Only AC `Line`
            and `Transformer2W` instances are considered; other branch types are ignored with a warning.
        :param voltage_tolerance: relative voltage tolerance used to match templates with branches
            (e.g. 0.1 for 10%).
        :raises ValueError: if no branch survives the categorization filter (every selection ends up
            with one or fewer compatible templates), in which case the problem has nothing to optimise.
        """
        # Build a private logger first so we can route the categorization warnings through it.
        # The base class would also create one, but we need it before super().__init__ runs.
        local_logger: Logger = Logger()

        # Filter the user selection: keep only branches with two or more compatible templates.
        kept_branches, kept_pools = build_catalogue_pool(grid=grid,
                                                         selected_branches=selected_branches,
                                                         voltage_tolerance=voltage_tolerance,
                                                         logger=local_logger)

        # If nothing survives there is nothing to optimise: surface the problem to the caller
        # who is responsible for showing a dialog to the user.
        if len(kept_branches) == 0:
            raise ValueError("No branch in the selection has two or more compatible templates: "
                             "the catalogue optimization has nothing to optimize.")
        else:
            pass

        # Initialise the black-box base. We use indices (4, 5) for plotting (financial vs technical),
        # mirroring the convention in `PowerFlowInvestmentProblem`.
        super().__init__(grid=grid,
                         x_dim=len(kept_branches),
                         plot_x_idx=4,
                         plot_y_idx=5)

        # Replace the base logger with the one already populated by `build_catalogue_pool`
        # so the warnings emitted there reach the caller.
        self.logger = local_logger

        # Store the survived branches and their per-branch template pools.
        # These two lists are kept in lock-step: index i is one decision slot.
        self.branches: List[Branch] = kept_branches
        self.pools: List[List[Template]] = kept_pools

        # Capture the baseline state of every branch that the optimization will mutate, so we can
        # restore it after each evaluation regardless of the chosen template.
        self.snapshots: List[Union[LineSnapshot, TransformerSnapshot]] = list()
        for branch in kept_branches:
            self.snapshots.append(take_snapshot(branch=branch))

        # Decision-variable bounds: integer index in [0, len(pool) - 1] for each slot.
        # We override the floats produced by the base class with proper integer bounds.
        self.x_min = np.zeros(self.x_dim, dtype=int)
        self.x_max = np.array([len(pool) - 1 for pool in kept_pools], dtype=int)

        # Power flow options (reused across every evaluation).
        self.pf_options: PowerFlowOptions = pf_options

        # Pre-compute the cost / threshold arrays used by the score functions.
        # These do not change between evaluations, so we compute them once.
        self.vm_cost: Vec = np.array([e.Vm_cost for e in grid.get_buses()], dtype=float)
        self.vm_max: Vec = np.array([e.Vmax for e in grid.get_buses()], dtype=float)
        self.vm_min: Vec = np.array([e.Vmin for e in grid.get_buses()], dtype=float)

        self.va_cost: Vec = np.array([e.angle_cost for e in grid.get_buses()], dtype=float)
        self.va_max: Vec = np.array([e.angle_max for e in grid.get_buses()], dtype=float)
        self.va_min: Vec = np.array([e.angle_min for e in grid.get_buses()], dtype=float)

        # Same branch list used by `PowerFlowInvestmentProblem` so the loading score has matching
        # branch order with the cost vector.
        self.branches_cost: Vec = np.array(
            [e.Cost for e in grid.get_branches(add_hvdc=False, add_vsc=False, add_switch=True)],
            dtype=float,
        )

        # Cache the system base power and frequency for `apply_template` calls.
        self.Sbase: float = float(grid.Sbase)
        self.fBase: float = float(grid.fBase)

        # TODO: extend to time-series evaluation (loop over the active time profile) once the
        # snapshot-only mode has been validated.

    def n_objectives(self) -> int:
        """
        Number of objectives in `f`.

        :return: 6 (losses, overload, voltage module, voltage angle, financial, technical).
        """
        return 6

    def n_vars(self) -> int:
        """
        Number of decision variables in `x`.

        :return: number of optimisable branch slots.
        """
        return self.x_dim

    def get_objectives_names(self) -> StrVec:
        """
        Get the human-readable names for the elements of `f`.

        :return: array of objective names matching the order of `objective_function`'s output.
        """
        return np.array([
            "losses score",
            "overload score",
            "voltage module_score",
            "voltage angle score",
            "financial score",
            "Technical score",
        ])

    def get_vars_names(self) -> StrVec:
        """
        Get the human-readable names for the elements of `x`.

        :return: array of branch names; one entry per decision slot.
        """
        return np.array([branch.name for branch in self.branches])

    def _apply_combination(self, x: IntVec) -> float:
        """
        Apply the chosen template to every branch of the problem and return the total capex.

        :param x: integer decision vector with `x[i]` indexing the template within `pools[i]`.
        :return: cumulative capex of all the applied templates (currency units).
        """
        # Sum of capex across every applied template; this is the financial objective.
        total_capex: float = 0.0

        # Walk through each slot; integer truncation guards against the optimizer passing floats.
        for i in range(self.x_dim):

            # Bound-check the index defensively: NSGA-3 may explore the boundary aggressively.
            slot_idx: int = int(x[i])
            if slot_idx < 0:
                slot_idx = 0
            elif slot_idx > len(self.pools[i]) - 1:
                slot_idx = len(self.pools[i]) - 1
            else:
                pass

            # Pick the chosen template and the corresponding branch.
            chosen_template: Template = self.pools[i][slot_idx]
            branch: Branch = self.branches[i]

            # Apply the template; the right overload is selected based on the branch type.
            if isinstance(branch, Line):
                branch.apply_template(obj=chosen_template,
                                      Sbase=self.Sbase,
                                      freq=self.fBase,
                                      logger=self.logger)
            elif isinstance(branch, Transformer2W):
                branch.apply_template(obj=chosen_template,
                                      Sbase=self.Sbase,
                                      logger=self.logger)
            else:
                # Should never happen: `build_catalogue_pool` already filtered unsupported branches.
                self.logger.add_error(msg="Unsupported branch type at evaluation time",
                                      device=branch.name,
                                      device_class=type(branch).__name__)

            # Accumulate the capex contribution of this slot.
            total_capex += template_capex(branch=branch, template=chosen_template)

        return total_capex

    def _restore_baseline(self) -> None:
        """
        Restore every branch to its baseline state captured at construction time.
        """
        # Iterate over the pre-computed snapshots and reapply the original values.
        for snapshot in self.snapshots:
            snapshot.restore()

    def _evaluate_power_flow(self) -> TechnoEconomicScores:
        """
        Run a power flow on the current grid state and return a `TechnoEconomicScores` populated
        with the four technical scores (capex/opex are filled in by the caller).

        :return: techno-economic scores with the technical fields populated.
        """
        # Run a fresh PF driver each time; reusing one across evaluations would risk stale state.
        driver = PowerFlowDriver(grid=self.grid, options=self.pf_options)
        driver.run()

        scores = TechnoEconomicScores()

        # Total real losses across the grid (already complex-aware).
        scores.losses_score = float(np.sum(driver.results.losses.real))

        # Branch loading penalty above 100% threshold weighted by the per-branch overload cost.
        scores.overload_score = get_overload_score(loading=driver.results.loading,
                                                   branches_cost=self.branches_cost)

        # Voltage module deviation outside [Vmin, Vmax] weighted by the per-bus penalty cost.
        scores.voltage_module_score = get_voltage_module_score(voltage=driver.results.voltage,
                                                               vm_cost=self.vm_cost,
                                                               vm_max=self.vm_max,
                                                               vm_min=self.vm_min)

        # Voltage angle deviation outside [angle_min, angle_max] weighted by the per-bus penalty cost.
        scores.voltage_angle_score = get_voltage_phase_score(voltage=driver.results.voltage,
                                                             va_cost=self.va_cost,
                                                             va_max=self.va_max,
                                                             va_min=self.va_min)

        return scores

    def objective_function(self, x: Vec | IntVec) -> Vec:
        """
        Evaluate the objective function `f(x)`.

        Strategy:
            1. Apply the chosen templates to every branch and compute the financial cost.
            2. Run a power flow on the modified grid and compute the four technical scores.
            3. Restore every branch to its baseline state, regardless of whether the PF succeeded.
            4. Return the six-objective vector.

        :param x: integer decision vector with `x[i]` indexing the template within `pools[i]`.
        :return: array of six objective values.
        """
        try:
            # Step 1: apply templates and accumulate capex.
            total_capex: float = self._apply_combination(x=x)

            # Step 2: run the power flow against the mutated grid.
            scores: TechnoEconomicScores = self._evaluate_power_flow()

            # Step 3: fill in the financial score; opex is not used at this stage.
            scores.capex_score = total_capex
            scores.opex_score = 0.0

            # Snapshot the result before reverting so we still hold the values.
            result: Vec = scores.arr()
        finally:
            # Always revert: leaking modified branches across evaluations would invalidate the search.
            self._restore_baseline()

        return result
