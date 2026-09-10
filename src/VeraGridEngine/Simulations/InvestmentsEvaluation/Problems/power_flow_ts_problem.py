# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List, Union
import numpy as np
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.black_box_problem_template import BlackBoxProblemTemplate
from VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.linear_opf_ts_problem import (
    apply_investments_by_year,
    collect_device_states,
    correct_x,
    determine_starting_index_of_every_year,
    force_investment_candidates_off,
    restore_device_states,
)
from VeraGridEngine.Utils.scores import (get_overload_score, get_voltage_phase_score, get_voltage_module_score,
                                         TechnoEconomicScores)
from VeraGridEngine.Simulations.PowerFlow.power_flow_ts_driver import PowerFlowTimeSeriesDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.OPF.opf_ts_results import OptimalPowerFlowTimeSeriesResults
from VeraGridEngine.Simulations.Clustering.clustering_results import ClusteringResults
from VeraGridEngine.Devices.Aggregation.investment import Investment
from VeraGridEngine.enumerations import EngineType
from VeraGridEngine.basic_structures import IntVec, Vec, StrVec


def power_flow_ts_function(inv_list: List[Investment],
                           grid: MultiCircuit,
                           pf_options: PowerFlowOptions,
                           time_indices: IntVec,
                           opf_time_series_results: Union[None, OptimalPowerFlowTimeSeriesResults],
                           clustering_results: Union[ClusteringResults, None],
                           engine: EngineType,
                           branches_cost,
                           vm_cost: Vec,
                           vm_max: Vec,
                           vm_min: Vec,
                           va_cost: Vec,
                           va_max: Vec,
                           va_min: Vec) -> TechnoEconomicScores:
    """
    Compute the power flow of the grid given an investments group
    :param inv_list: list of Investments
    :param grid: MultiCircuit grid
    :param pf_options: Power flow options
    :param time_indices: Time indices of the investments
    :param opf_time_series_results: Optimal power flow results
    :param clustering_results: Clustering results
    :param engine: Engine type
    :param branches_cost: Array with all overloading cost for the branches
    :param vm_cost: Array with all the bus voltage module violation costs
    :param vm_max: Array with the Vm min values
    :param vm_min: Array with the Vm max values
    :param va_cost: Array with all the bus voltage angles violation costs
    :param va_max: Array with the Va max values
    :param va_min: Array with the Va min values
    :return: InvestmentScores
    """
    driver = PowerFlowTimeSeriesDriver(grid=grid,
                                       options=pf_options,
                                       time_indices=time_indices,
                                       opf_time_series_results=opf_time_series_results,
                                       clustering_results=clustering_results,
                                       engine=engine)
    driver.run()

    scores = TechnoEconomicScores()

    # compute scores
    scores.losses_score = np.sum(driver.results.losses.real)
    scores.overload_score = get_overload_score(loading=driver.results.loading,
                                               branches_cost=branches_cost)
    # scores.overload_score = 0
    scores.voltage_module_score = get_voltage_module_score(voltage=driver.results.voltage,
                                                           vm_cost=vm_cost,
                                                           vm_max=vm_max,
                                                           vm_min=vm_min)

    scores.voltage_angle_score = get_voltage_phase_score(voltage=driver.results.voltage,
                                                         va_cost=va_cost,
                                                         va_max=va_max,
                                                         va_min=va_min)

    scores.capex_score = sum([inv.CAPEX for inv in inv_list])
    scores.opex_score = 0.0

    return scores


class TimeSeriesPowerFlowInvestmentProblem(BlackBoxProblemTemplate):

    def __init__(self, grid: MultiCircuit,
                 pf_options: PowerFlowOptions,
                 time_indices: Union[IntVec, None],
                 clustering_results: Union[ClusteringResults, None] = None,
                 opf_time_series_results: Union[None, OptimalPowerFlowTimeSeriesResults] = None,
                 engine: EngineType = EngineType.VeraGrid):
        """
        Constructor
        :param grid: MultiCircuit
        :param pf_options: PowerFlowOptions
        :param time_indices: Time indices of the investments
        :param clustering_results: Clustering results
        :param opf_time_series_results: Optimal power flow results
        :param engine: Engine to run the simulations
        """
        # The Pareto plot shows the CAPEX (objective 4) against the overload cost (objective 1).
        super().__init__(grid=grid,
                         x_dim=len(grid.investments_groups),
                         plot_x_idx=4,
                         plot_y_idx=1)

        # options object
        self.pf_options = pf_options
        if time_indices is None:
            self.time_indices = grid.get_all_time_indices()
        else:
            self.time_indices = np.array(time_indices, dtype=int)

        self.opf_time_series_results = opf_time_series_results
        self.clustering_results = clustering_results
        self.engine = engine
        local_year_indices: IntVec = determine_starting_index_of_every_year(
            index=self.grid.time_profile[self.time_indices]
        )
        self.years_starts_indices = self.time_indices[local_year_indices]
        self.x_max *= len(self.years_starts_indices)

        # gather a dictionary of all the elements, this serves for the investments generation
        self.get_all_elements_dict, dict_ok = self.grid.get_all_elements_dict()

        if dict_ok:
            pass
        else:
            self.logger.add_warning("Some investment devices are missing from the grid element dictionary")

        force_investment_candidates_off(investments_by_group=self.investments_by_group,
                                        all_elements_dict=self.get_all_elements_dict,
                                        logger=self.logger)

        # compose useful arrays
        self.vm_cost = np.array([e.Vm_cost for e in grid.get_buses()], dtype=float)
        self.vm_max = np.array([e.Vmax for e in grid.get_buses()], dtype=float)
        self.vm_min = np.array([e.Vmin for e in grid.get_buses()], dtype=float)

        self.va_cost = np.array([e.angle_cost for e in grid.get_buses()], dtype=float)
        self.va_max = np.array([e.angle_max for e in grid.get_buses()], dtype=float)
        self.va_min = np.array([e.angle_min for e in grid.get_buses()], dtype=float)

        self.branches_cost = np.array([e.Cost for e in
                                       grid.get_branches(add_hvdc=False, add_vsc=False, add_switch=True)],
                                      dtype=float)

    def n_objectives(self) -> int:
        """
        Number of objectives (size of f)
        :return:
        """
        return 6

    def n_vars(self) -> int:
        """
        Number of variables (size of x)
        :return:
        """
        return self.x_dim

    def get_objectives_names(self) -> StrVec:
        """
        Get a list of names for the elements of f
        :return:
        """
        return np.array(["losses score", "overload score",
                         "voltage module_score", "voltage angle score",
                         "CAPEX", "OPEX"])

    def get_vars_names(self) -> StrVec:
        """
        Get a list of names for the elements of x
        :return:
        """
        return np.array([e.name for e in self.grid.investments_groups])

    def objective_function(self, x: Vec | IntVec) -> Vec:
        """
        Evaluate x and return f(x)
        :param x: array of variable values
        :return: array of objectives
        """
        x_int: IntVec = np.array(x, dtype=int)
        x_min: IntVec = np.array(self.x_min, dtype=int)
        x_max: IntVec = np.array(self.x_max, dtype=int)
        inv_list: List[Investment] = list()

        # The optimizer may propose out-of-range entry years, so the vector is corrected before touching profiles.
        correct_x(x=x_int, lb=x_min, ub=x_max)

        for group_index, entry_year_value in enumerate(x_int):
            if entry_year_value > 0:
                inv_list += self.investments_by_group[group_index]
            else:
                pass

        states = collect_device_states(investments_by_group=self.investments_by_group,
                                       x=x_int,
                                       all_elements_dict=self.get_all_elements_dict)

        apply_investments_by_year(investments_by_group=self.investments_by_group,
                                  x=x_int,
                                  all_elements_dict=self.get_all_elements_dict,
                                  years_starts_indices=self.years_starts_indices)

        try:
            scores = power_flow_ts_function(inv_list=inv_list,
                                            grid=self.grid,
                                            pf_options=self.pf_options,
                                            time_indices=self.time_indices,
                                            opf_time_series_results=self.opf_time_series_results,
                                            clustering_results=self.clustering_results,
                                            engine=self.engine,
                                            branches_cost=self.branches_cost,
                                            vm_cost=self.vm_cost,
                                            vm_max=self.vm_max,
                                            vm_min=self.vm_min,
                                            va_cost=self.va_cost,
                                            va_max=self.va_max,
                                            va_min=self.va_min)

            return np.array([scores.losses_score,
                             scores.overload_score,
                             scores.voltage_module_score,
                             scores.voltage_angle_score,
                             scores.capex_score,
                             scores.opex_score])
        finally:
            restore_device_states(states=states)
