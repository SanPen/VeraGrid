# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from VeraGridEngine.Devices.Aggregation.investment import Investment
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.Clustering.clustering_results import ClusteringResults
from VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.black_box_problem_template import BlackBoxProblemTemplate
from VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.linear_opf_ts_problem import (
    apply_investments_by_year,
    clone_linear_opf_options,
    collect_device_states,
    correct_x,
    determine_starting_index_of_every_year,
    force_investment_candidates_off,
    get_objective_vector,
    restore_device_states,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.power_flow_ts_problem import power_flow_ts_function
from VeraGridEngine.Simulations.OPF.opf_options import OptimalPowerFlowOptions
from VeraGridEngine.Simulations.OPF.opf_ts_driver import OptimalPowerFlowTimeSeriesDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Utils.scores import TechnoEconomicScores
from VeraGridEngine.basic_structures import BoolVec, IntVec, StrVec, Vec
from VeraGridEngine.enumerations import EngineType


class TimeSeriesOptimalPowerFlowThenPowerFlowInvestmentProblem(BlackBoxProblemTemplate):
    """
    Investment problem that dispatches with linear OPF and validates with power flow time series.
    """

    __slots__ = (
        "opf_options",
        "pf_options",
        "time_indices",
        "clustering_results",
        "engine",
        "years_starts_indices",
        "inv_group_capex",
        "all_elements_dict",
        "vm_cost",
        "vm_max",
        "vm_min",
        "va_cost",
        "va_max",
        "va_min",
        "branches_cost",
    )

    def __init__(self,
                 grid: MultiCircuit,
                 opf_options: OptimalPowerFlowOptions | None,
                 pf_options: PowerFlowOptions,
                 time_indices: IntVec | None,
                 clustering_results: ClusteringResults | None = None,
                 engine: EngineType = EngineType.VeraGrid) -> None:
        """
        Build the sequential OPF to power flow investment problem.

        :param grid: Grid to evaluate.
        :type grid: MultiCircuit
        :param opf_options: OPF options provided externally.
        :type opf_options: OptimalPowerFlowOptions | None
        :param pf_options: Power flow options provided externally.
        :type pf_options: PowerFlowOptions
        :param time_indices: Time indices to evaluate.
        :type time_indices: IntVec | None
        :param clustering_results: Optional clustering results.
        :type clustering_results: ClusteringResults | None
        :param engine: Engine used by the OPF and power flow drivers.
        :type engine: EngineType
        """
        super().__init__(grid=grid,
                         x_dim=len(grid.investments_groups),
                         plot_x_idx=4,
                         plot_y_idx=1)

        # The first stage is always the linear OPF dispatch used as PF time-series input.
        self.opf_options: OptimalPowerFlowOptions = clone_linear_opf_options(opf_options=opf_options)
        self.pf_options: PowerFlowOptions = pf_options

        # The selected horizon defines the admissible year-of-entry values of the optimizer.
        if time_indices is None:
            self.time_indices: IntVec = grid.get_all_time_indices()
        else:
            self.time_indices = np.array(time_indices, dtype=int)

        self.clustering_results: ClusteringResults | None = clustering_results
        self.engine: EngineType = engine
        local_year_indices: IntVec = determine_starting_index_of_every_year(
            index=self.grid.time_profile[self.time_indices]
        )
        self.years_starts_indices: IntVec = self.time_indices[local_year_indices]
        self.x_max *= len(self.years_starts_indices)
        self.inv_group_capex: Vec = self.grid.get_capex_by_investment_group()

        # The device lookup is reused at every evaluation to avoid repeated scans of the grid.
        all_elements_dict: Dict[str, EditableDevice]
        dict_ok: bool
        all_elements_dict, dict_ok = self.grid.get_all_elements_dict()
        self.all_elements_dict = all_elements_dict

        if dict_ok:
            pass
        else:
            self.logger.add_warning("Some investment devices are missing from the grid element dictionary")

        # Candidate assets that are activated by the investments must start disabled in the baseline case.
        force_investment_candidates_off(investments_by_group=self.investments_by_group,
                                        all_elements_dict=self.all_elements_dict,
                                        logger=self.logger)

        # These arrays are static over the optimization and are reused by the PF scoring stage.
        self.vm_cost: Vec = np.array([bus.Vm_cost for bus in grid.get_buses()], dtype=float)
        self.vm_max: Vec = np.array([bus.Vmax for bus in grid.get_buses()], dtype=float)
        self.vm_min: Vec = np.array([bus.Vmin for bus in grid.get_buses()], dtype=float)
        self.va_cost: Vec = np.array([bus.angle_cost for bus in grid.get_buses()], dtype=float)
        self.va_max: Vec = np.array([bus.angle_max for bus in grid.get_buses()], dtype=float)
        self.va_min: Vec = np.array([bus.angle_min for bus in grid.get_buses()], dtype=float)
        self.branches_cost: Vec = np.array(
            [branch.Cost for branch in grid.get_branches(add_hvdc=False, add_vsc=False, add_switch=True)],
            dtype=float
        )

    def n_objectives(self) -> int:
        """
        Number of objectives.

        :return: Objective vector length.
        :rtype: int
        """
        return 11

    def n_vars(self) -> int:
        """
        Number of decision variables.

        :return: Decision vector length.
        :rtype: int
        """
        return self.x_dim

    def get_objectives_names(self) -> StrVec:
        """
        Get the objective names.

        :return: Objective names.
        :rtype: StrVec
        """
        return np.array(["Average nodal price",
                         "CAPEX",
                         "OPEX",
                         "Load shedding",
                         "Generation shedding",
                         "Fuel usage",
                         "losses score",
                         "overload score",
                         "voltage module_score",
                         "voltage angle score",
                         "financial score"])

    def get_vars_names(self) -> StrVec:
        """
        Get the variable names.

        :return: Variable names.
        :rtype: StrVec
        """
        return np.array([group.name for group in self.grid.investments_groups])

    def objective_function(self, x: Vec | IntVec) -> Vec:
        """
        Evaluate one investment combination with OPF dispatch followed by power flow time series.

        :param x: Decision vector encoded as year of entry.
        :type x: Vec | IntVec
        :return: Objective vector.
        :rtype: Vec
        """
        x_int: IntVec = np.array(x, dtype=int)
        x_min: IntVec = np.array(self.x_min, dtype=int)
        x_max: IntVec = np.array(self.x_max, dtype=int)
        inv_list: List[Investment] = list()
        penalty: Vec = np.full(11, 1e12, dtype=float)

        # The optimizer may propose out-of-range entry years, so bounds are enforced before profile edits.
        correct_x(x=x_int, lb=x_min, ub=x_max)
        x_bin: Vec = x_int.astype(bool).astype(float)
        capex: float = float(np.sum(self.inv_group_capex * x_bin))

        # The OPF and PF stages must see the same investment activation profiles.
        for group_index, entry_year_value in enumerate(x_int):
            if entry_year_value > 0:
                for investment in self.investments_by_group[group_index]:
                    inv_list.append(investment)
            else:
                pass

        states: Dict[str, Tuple[EditableDevice, bool, BoolVec]] = collect_device_states(
            investments_by_group=self.investments_by_group,
            x=x_int,
            all_elements_dict=self.all_elements_dict)

        apply_investments_by_year(investments_by_group=self.investments_by_group,
                                  x=x_int,
                                  all_elements_dict=self.all_elements_dict,
                                  years_starts_indices=self.years_starts_indices)

        try:
            opf_driver: OptimalPowerFlowTimeSeriesDriver = OptimalPowerFlowTimeSeriesDriver(
                grid=self.grid,
                options=self.opf_options,
                time_indices=self.time_indices,
                clustering_results=self.clustering_results,
                engine=self.engine)
            opf_driver.run()

            if np.all(opf_driver.results.converged):
                opf_objectives: Vec = get_objective_vector(results=opf_driver.results, capex=capex)
                scores: TechnoEconomicScores = power_flow_ts_function(inv_list=inv_list,
                                                                      grid=self.grid,
                                                                      pf_options=self.pf_options,
                                                                      time_indices=self.time_indices,
                                                                      opf_time_series_results=opf_driver.results,
                                                                      clustering_results=self.clustering_results,
                                                                      engine=self.engine,
                                                                      branches_cost=self.branches_cost,
                                                                      vm_cost=self.vm_cost,
                                                                      vm_max=self.vm_max,
                                                                      vm_min=self.vm_min,
                                                                      va_cost=self.va_cost,
                                                                      va_max=self.va_max,
                                                                      va_min=self.va_min)
                pf_objectives: Vec = np.array([scores.losses_score,
                                               scores.overload_score,
                                               scores.voltage_module_score,
                                               scores.voltage_angle_score,
                                               scores.financial_score],
                                              dtype=float)

                return np.r_[opf_objectives, pf_objectives]
            else:
                self.logger.add_error(msg="Linear OPF investment evaluation did not converge")
                return penalty
        except Exception as err:
            self.logger.add_error(msg="Sequential OPF and power flow investment evaluation failed",
                                  comment=str(err))
            return penalty
        finally:
            restore_device_states(states=states)
