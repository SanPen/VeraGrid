# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Tuple

import numpy as np

from VeraGridEngine.Devices.Aggregation.investment import Investment
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.Clustering.clustering_results import ClusteringResults
from VeraGridEngine.Simulations.InvestmentsEvaluation.Problems.black_box_problem_template import BlackBoxProblemTemplate
from VeraGridEngine.Simulations.OPF.opf_options import OptimalPowerFlowOptions
from VeraGridEngine.Simulations.OPF.opf_ts_driver import OptimalPowerFlowTimeSeriesDriver
from VeraGridEngine.Simulations.OPF.opf_ts_results import OptimalPowerFlowTimeSeriesResults
from VeraGridEngine.basic_structures import BoolVec, IntVec, StrVec, Vec
from VeraGridEngine.enumerations import EngineType, SolverType


def correct_x(x: IntVec, lb: IntVec, ub: IntVec) -> None:
    """
    Correct the integer decision vector in place to the given bounds.

    :param x: Decision vector.
    :type x: IntVec
    :param lb: Lower bound vector.
    :type lb: IntVec
    :param ub: Upper bound vector.
    :type ub: IntVec
    :return: None
    :rtype: None
    """
    for idx in range(len(x)):
        if x[idx] < lb[idx]:
            x[idx] = lb[idx]
        else:
            if x[idx] > ub[idx]:
                x[idx] = ub[idx]
            else:
                pass


def determine_starting_index_of_every_year(index) -> IntVec:
    """
    Find the first profile index of each year in the selected horizon.

    :param index: Datetime-like index.
    :type index: any
    :return: Starting index of each year.
    :rtype: IntVec
    """
    indices: List[int] = list()
    previous_year: int = int(index[0].year)

    indices.append(0)

    for idx, entry in enumerate(index):
        current_year: int = int(entry.year)

        if current_year != previous_year:
            previous_year = current_year
            indices.append(idx)
        else:
            pass

    return np.array(indices, dtype=int)


def clone_linear_opf_options(opf_options: OptimalPowerFlowOptions | None) -> OptimalPowerFlowOptions:
    """
    Clone the external OPF options and force the linear OPF solver.

    :param opf_options: External OPF options.
    :type opf_options: OptimalPowerFlowOptions | None
    :return: OPF options configured for linear OPF.
    :rtype: OptimalPowerFlowOptions
    """
    local_options: OptimalPowerFlowOptions

    if opf_options is None:
        local_options = OptimalPowerFlowOptions(solver=SolverType.LINEAR_OPF)
    else:
        local_options = deepcopy(opf_options)
        local_options.solver = SolverType.LINEAR_OPF

    return local_options


def collect_device_states(investments_by_group: Dict[int, List[Investment]],
                          x: IntVec,
                          all_elements_dict: Dict[str, EditableDevice]) -> Dict[str, Tuple[EditableDevice, bool, BoolVec]]:
    """
    Store the original activation state of each device that may be modified.

    :param investments_by_group: Investments grouped by decision-variable index.
    :type investments_by_group: Dict[int, List[Investment]]
    :param x: Decision vector.
    :type x: IntVec
    :param all_elements_dict: Dictionary of all grid devices.
    :type all_elements_dict: Dict[str, EditableDevice]
    :return: Original state of every touched device.
    :rtype: Dict[str, Tuple[EditableDevice, bool, BoolVec]]
    """
    states: Dict[str, Tuple[EditableDevice, bool, BoolVec]] = dict()

    for group_index, entry_year_value in enumerate(x):
        if entry_year_value > 0:
            for investment in investments_by_group[group_index]:
                device = all_elements_dict[investment.device_idtag]

                if investment.device_idtag not in states:
                    active_profile = device.get_profile("active")

                    if active_profile is None:
                        pass
                    else:
                        states[investment.device_idtag] = (
                            device,
                            bool(device.active),
                            np.array(active_profile.toarray(), dtype=bool)
                        )
                else:
                    pass
        else:
            pass

    return states


def apply_investments_by_year(investments_by_group: Dict[int, List[Investment]],
                              x: IntVec,
                              all_elements_dict: Dict[str, EditableDevice],
                              years_starts_indices: IntVec) -> None:
    """
    Apply the selected investments to the devices active profiles.

    :param investments_by_group: Investments grouped by decision-variable index.
    :type investments_by_group: Dict[int, List[Investment]]
    :param x: Decision vector where ``0`` means not invested and ``1..N`` is the year of entry.
    :type x: IntVec
    :param all_elements_dict: Dictionary of all grid devices.
    :type all_elements_dict: Dict[str, EditableDevice]
    :param years_starts_indices: First time-step index of each year.
    :type years_starts_indices: IntVec
    :return: None
    :rtype: None
    """
    for group_index, entry_year_value in enumerate(x):
        if entry_year_value > 0:
            start_index: int = int(years_starts_indices[int(entry_year_value) - 1])

            for investment in investments_by_group[group_index]:
                device = all_elements_dict[investment.device_idtag]
                active_profile = device.get_profile("active")

                if active_profile is None:
                    pass
                else:
                    active_array: BoolVec = np.array(active_profile.toarray(), dtype=bool)

                    if investment.status:
                        active_array[start_index:] = True
                    else:
                        active_array[start_index:] = False

                    active_profile.set(active_array)
                    device.active = bool(active_array[0])
        else:
            pass


def restore_device_states(states: Dict[str, Tuple[EditableDevice, bool, BoolVec]]) -> None:
    """
    Restore the original activation state of the devices after an evaluation.

    :param states: Original device activation states.
    :type states: Dict[str, Tuple[EditableDevice, bool, BoolVec]]
    :return: None
    :rtype: None
    """
    for device_idtag, values in states.items():
        device: EditableDevice = values[0]
        active_value: bool = values[1]
        active_profile_array: BoolVec = values[2]
        active_profile = device.get_profile("active")

        device.active = active_value

        if active_profile is None:
            pass
        else:
            active_profile.set(active_profile_array)


def force_investment_candidates_off(investments_by_group: Dict[int, List[Investment]],
                                    all_elements_dict: Dict[str, EditableDevice],
                                    logger) -> None:
    """
    Force activation-type investment candidates to be off before the optimization starts.

    :param investments_by_group: Investments grouped by decision-variable index.
    :type investments_by_group: Dict[int, List[Investment]]
    :param all_elements_dict: Dictionary of all grid devices.
    :type all_elements_dict: Dict[str, EditableDevice]
    :param logger: Problem logger.
    :type logger: any
    :return: None
    :rtype: None
    """
    processed_devices: set[str] = set()

    for group_index, investments in investments_by_group.items():
        for investment in investments:
            if investment.status:
                if investment.device_idtag not in processed_devices:
                    device = all_elements_dict.get(investment.device_idtag, None)

                    if device is None:
                        logger.add_warning("Investment device not found",
                                           device=investment.device_idtag)
                    else:
                        active_profile = device.get_profile("active")
                        device.active = False

                        if active_profile is None:
                            logger.add_info(msg="Forced investment candidate off",
                                            device=investment.name,
                                            device_class="Investment")
                        else:
                            active_profile.fill(False)
                            logger.add_info(msg="Forced investment candidate off",
                                            device=investment.name,
                                            device_class="Investment")

                        processed_devices.add(investment.device_idtag)
                else:
                    pass
            else:
                pass


def get_objective_vector(results: OptimalPowerFlowTimeSeriesResults,
                         capex: float) -> Vec:
    """
    Aggregate the linear OPF results into the investment objective vector.

    :param results: Time-series OPF results.
    :type results: OptimalPowerFlowTimeSeriesResults
    :param capex: Total CAPEX of the selected investment groups.
    :type capex: float
    :return: Objective vector.
    :rtype: Vec
    """
    nodal_price_per_time: Vec = np.mean(results.bus_shadow_prices, axis=1)
    served_load_per_time: Vec = np.sum(results.load_power, axis=1)
    shedding_mask = results.load_shedding > 0.0

    if np.any(shedding_mask):
        shedding_price = np.divide(results.load_shedding_cost,
                                   results.load_shedding,
                                   out=np.zeros_like(results.load_shedding_cost, dtype=float),
                                   where=shedding_mask)
        price_cap: float = float(np.max(shedding_price))
        nodal_price_per_time = np.clip(nodal_price_per_time, a_min=None, a_max=price_cap)
    else:
        pass

    if np.sum(served_load_per_time) > 0.0:
        average_nodal_price: float = float(np.average(nodal_price_per_time, weights=served_load_per_time))
    else:
        average_nodal_price = float(np.mean(nodal_price_per_time))

    opex: float = float(np.sum(results.system_total_energy_cost))
    load_shedding: float = float(np.sum(results.load_shedding))
    generation_shedding: float = float(np.sum(results.generator_shedding))
    fuel_usage: float = float(np.sum(results.system_fuel))

    return np.array([average_nodal_price,
                     capex,
                     opex,
                     load_shedding,
                     generation_shedding,
                     fuel_usage], dtype=float)


class TimeSeriesLinearOptimalPowerFlowInvestmentProblem(BlackBoxProblemTemplate):
    """
    Investment problem based on a time-series linear OPF evaluation.
    """

    __slots__ = (
        "opf_options",
        "time_indices",
        "clustering_results",
        "engine",
        "years_starts_indices",
        "inv_group_capex",
        "all_elements_dict",
    )

    def __init__(self,
                 grid: MultiCircuit,
                 opf_options: OptimalPowerFlowOptions | None,
                 time_indices: IntVec,
                 clustering_results: ClusteringResults | None = None,
                 engine: EngineType = EngineType.VeraGrid) -> None:
        """
        Build the linear OPF investment problem.

        :param grid: Grid to evaluate.
        :type grid: MultiCircuit
        :param opf_options: OPF options provided externally.
        :type opf_options: OptimalPowerFlowOptions | None
        :param time_indices: Time indices to evaluate.
        :type time_indices: IntVec
        :param clustering_results: Optional clustering results.
        :type clustering_results: ClusteringResults | None
        :param engine: Engine used by the OPF driver.
        :type engine: EngineType
        """
        super().__init__(grid=grid,
                         x_dim=len(grid.investments_groups),
                         plot_x_idx=1,
                         plot_y_idx=0)

        # The GUI provides the OPF options, but this problem always runs the linear formulation.
        self.opf_options: OptimalPowerFlowOptions = clone_linear_opf_options(opf_options=opf_options)

        # The selected horizon defines the admissible year-of-entry values of the GA.
        self.time_indices: IntVec = np.array(time_indices, dtype=int)
        self.clustering_results: ClusteringResults | None = clustering_results
        self.engine: EngineType = engine
        self.years_starts_indices: IntVec = determine_starting_index_of_every_year(
            index=self.grid.time_profile[self.time_indices]
        )
        self.x_max *= len(self.years_starts_indices)
        self.inv_group_capex = self.grid.get_capex_by_investment_group()

        # The device lookup is reused at every evaluation to avoid repeated scans of the grid.
        self.all_elements_dict, dict_ok = self.grid.get_all_elements_dict()

        if dict_ok:
            pass
        else:
            self.logger.add_warning("Some investment devices are missing from the grid element dictionary")

        # Candidate assets that are activated by the investments must start disabled in the baseline case.
        force_investment_candidates_off(investments_by_group=self.investments_by_group,
                                        all_elements_dict=self.all_elements_dict,
                                        logger=self.logger)

    def n_objectives(self) -> int:
        """
        Number of objectives.

        :return: Objective vector length.
        :rtype: int
        """
        return 6

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
                         "Fuel usage"])

    def get_vars_names(self) -> StrVec:
        """
        Get the variable names.

        :return: Variable names.
        :rtype: StrVec
        """
        return np.array([group.name for group in self.grid.investments_groups])

    def objective_function(self, x: Vec | IntVec) -> Vec:
        """
        Evaluate one investment combination.

        :param x: Decision vector encoded as year of entry.
        :type x: Vec | IntVec
        :return: Objective vector.
        :rtype: Vec
        """
        x_int: IntVec = np.array(x, dtype=int)
        x_min: IntVec = np.array(self.x_min, dtype=int)
        x_max: IntVec = np.array(self.x_max, dtype=int)
        x_bin: Vec = x_int.astype(bool).astype(float)
        capex: float = float(np.sum(self.inv_group_capex * x_bin))
        penalty: Vec = np.full(6, 1e12, dtype=float)

        # The optimizer may propose out-of-range values, so the vector is corrected before touching the grid.
        correct_x(x=x_int, lb=x_min, ub=x_max)

        # The OPF modifies the active state seen by the compiler, so the original profiles must be restored afterwards.
        states = collect_device_states(investments_by_group=self.investments_by_group,
                                       x=x_int,
                                       all_elements_dict=self.all_elements_dict)

        apply_investments_by_year(investments_by_group=self.investments_by_group,
                                  x=x_int,
                                  all_elements_dict=self.all_elements_dict,
                                  years_starts_indices=self.years_starts_indices)

        try:
            driver = OptimalPowerFlowTimeSeriesDriver(grid=self.grid,
                                                      options=self.opf_options,
                                                      time_indices=self.time_indices,
                                                      clustering_results=self.clustering_results,
                                                      engine=self.engine)
            driver.run()

            if np.all(driver.results.converged):
                return get_objective_vector(results=driver.results, capex=capex)
            else:
                return penalty
        except Exception as err:
            self.logger.add_error(msg="Linear OPF investment evaluation failed",
                                  comment=str(err))
            return penalty
        finally:
            restore_device_states(states=states)
