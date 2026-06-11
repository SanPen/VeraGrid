# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from uuid import uuid4
import pandas as pd
import numpy as np
from PySide6.QtCore import QThread, Signal
from typing import Dict, Union, List, Tuple, Any, Generator
from collections.abc import Callable
from warnings import warn

from VeraGridEngine.Simulations.ATC.available_transfer_capacity_driver import (AvailableTransferCapacityDriver,
                                                                               AvailableTransferCapacityResults)
from VeraGridEngine.Simulations.ATC.available_transfer_capacity_ts_driver import (
    AvailableTransferCapacityTimeSeriesDriver, AvailableTransferCapacityTimeSeriesResults
)
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_driver import (ContingencyAnalysisDriver,
                                                                                        ContingencyAnalysisResults)
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_ts_driver import (
    ContingencyAnalysisTimeSeriesDriver, ContingencyAnalysisTimeSeriesResults
)
from VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow_driver import (
    ContinuationPowerFlowDriver, ContinuationPowerFlowResults
)
from VeraGridEngine.Simulations.LinearFactors.linear_analysis_driver import LinearAnalysisDriver, LinearAnalysisResults
from VeraGridEngine.Simulations.LinearFactors.linear_analysis_ts_driver import (LinearAnalysisTimeSeriesDriver,
                                                                                LinearAnalysisTimeSeriesResults)
from VeraGridEngine.Simulations.OPF.opf_driver import OptimalPowerFlowDriver, OptimalPowerFlowResults
from VeraGridEngine.Simulations.OPF.opf_ts_driver import (OptimalPowerFlowTimeSeriesDriver,
                                                          OptimalPowerFlowTimeSeriesResults)
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver, PowerFlowResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver_3ph import PowerFlowDriver3Ph, PowerFlowResults3Ph
from VeraGridEngine.Simulations.PowerFlow.power_flow_ts_driver import (PowerFlowTimeSeriesDriver,
                                                                       PowerFlowTimeSeriesResults)
from VeraGridEngine.Simulations.ShortCircuitStudies.short_circuit_driver import ShortCircuitDriver, ShortCircuitResults
from VeraGridEngine.Simulations.Stochastic.stochastic_power_flow_driver import (StochasticPowerFlowDriver,
                                                                                StochasticPowerFlowResults)
from VeraGridEngine.Simulations.Clustering.clustering_driver import ClusteringDriver, ClusteringResults
from VeraGridEngine.Simulations.Reliability.blackout_driver import CascadingResults, CascadingDriver
from VeraGridEngine.Simulations.InputsAnalysis.inputs_analysis_driver import InputsAnalysisResults, InputsAnalysisDriver
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_driver import (InvestmentsEvaluationDriver,
                                                                                            InvestmentsEvaluationResults)
from VeraGridEngine.Simulations.CatalogueOptimization.catalogue_optimization_driver import (
    CatalogueOptimizationDriver,
)
from VeraGridEngine.Simulations.SigmaAnalysis.sigma_analysis_driver import SigmaAnalysisResults
from VeraGridEngine.Simulations.NTC.ntc_driver import (OptimalNetTransferCapacityResults,
                                                       OptimalNetTransferCapacityDriver)
from VeraGridEngine.Simulations.NTC.ntc_ts_driver import (
    OptimalNetTransferCapacityTimeSeriesDriver,
    OptimalNetTransferCapacityTimeSeriesResults,
)
from VeraGridEngine.Simulations.NodalCapacity.nodal_capacity_ts_driver import (NodalCapacityTimeSeriesDriver,
                                                                               NodalCapacityTimeSeriesResults)
from VeraGridEngine.Simulations.Reliability.reliability_driver import ReliabilityStudyDriver, ReliabilityResults
from VeraGridEngine.Simulations.StateEstimation.state_stimation_driver import (StateEstimationDriver,
                                                                               StateEstimationResults)
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_driver import (SmallSignalStabilityRmsDriver,
                                                                                    SmallSignalStabilityRmsResults)
from VeraGridEngine.Simulations.Rms.rms_driver import RmsSimulationDriver, RmsResults
from VeraGridEngine.Simulations.EMT.emt_driver import EmtSimulationDriver, EmtResults
from VeraGridEngine.Simulations.Topology.node_groups_driver import NodeGroupsDriver
from VeraGridEngine.Simulations.Topology.node_groups_results import NodeGroupsResults
from VeraGridEngine.Simulations.driver_template import DriverTemplate, DriverToSave
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import ResultTypes, SimulationTypes
from VeraGridEngine.Simulations.driver_handler import create_driver
from VeraGridEngine.Simulations.types import DRIVER_OBJECTS, RESULTS_OBJECTS
from VeraGridEngine.basic_structures import Logger
from VeraGrid.Gui.results_model import ResultsModel


class GcThread(QThread):
    """
    Generic VeraGrid Thread
    this is used as a template for a Qt Thread
    """
    progress_signal = Signal(float)
    progress_text = Signal(str)
    done_signal = Signal()

    def __init__(self, driver: DriverTemplate):
        QThread.__init__(self)

        # assign the driver and set the driver's reporting functions
        self.driver: DriverTemplate = driver
        self.driver.progress_signal = self.progress_signal
        self.driver.progress_text = self.progress_text
        self.driver.done_signal = self.done_signal
        self.tpe = driver.tpe

        self.results = None

        self.elapsed = 0

        self.logger = Logger()

        self.__cancel__ = False

    def get_steps(self) -> List[Any]:
        """

        :return:
        """
        return list()

    def run(self) -> None:
        """
        Run driver
        """
        self.progress_signal.emit(0.0)

        self.driver.run()

        self.progress_signal.emit(0.0)
        if self.__cancel__:
            self.progress_text.emit('Cancelled!')
        else:
            self.progress_text.emit('Done!')
        self.done_signal.emit()

    def cancel(self) -> None:
        """
        Cancel the simulation
        """
        self.__cancel__ = True
        self.driver.cancel()


class SimulationSession:
    """
    The simulation session is the simulation manager
    it serves to orchestrate the threads and to store the drivers and their results
    """

    def __init__(self, name: str = 'Session', idtag: str = None):
        """
        Constructor
        :param name: Session name
        :param idtag: Unique identifier
        """
        self.idtag: str = uuid4().hex if idtag is None else idtag

        # name of the session
        self.name: str = name

        # dictionary of drivers
        self._drivers: Dict[SimulationTypes, DRIVER_OBJECTS] = dict()
        self.threads: Dict[SimulationTypes, GcThread] = dict()

    @property
    def drivers(self) -> Dict[SimulationTypes, DRIVER_OBJECTS]:
        """
        get the drivers dictionary
        :return: Dict[SimulationTypes, DRIVER_OBJECTS]
        """
        return self._drivers

    @drivers.setter
    def drivers(self, value: Dict[SimulationTypes, DRIVER_OBJECTS]):
        """
        set the drivers
        :param value: Dict[SimulationTypes, DRIVER_OBJECTS]
        """
        self._drivers: Dict[SimulationTypes, DRIVER_OBJECTS] = value

    def __str__(self):
        return self.name

    def clear(self) -> None:
        """
        Delete all the drivers
        """
        self.drivers = dict()

    def register(self, driver: DRIVER_OBJECTS):
        """
        Register driver
        :param driver: driver to register (must have a tpe variable in it)
        """
        # register
        self.drivers[driver.tpe] = driver

    def get_save_data(self) -> List[DriverToSave]:
        """
        Get data to be saved
        :return: List[DriverToSave]
        """
        data = list()
        for tpe, drv in self.drivers.items():
            data.append(drv.get_save_data())
        return data

    def run(self,
            driver: DRIVER_OBJECTS,
            post_func: Union[None, Callable] = None,
            prog_func: Union[None, Callable] = None,
            text_func: Union[None, Callable] = None):
        """
        Register driver
        :param driver: driver to register (must have a tpe variable in it)
        :param post_func: Function to run after it is done
        :param prog_func: Function to display the progress
        :param text_func: Function to display text
        """

        # create a process
        thr = GcThread(driver)
        thr.progress_signal.connect(prog_func)
        thr.progress_text.connect(text_func)
        thr.done_signal.connect(post_func)

        # check and kill
        if driver.tpe in self.drivers.keys():
            del self.drivers[driver.tpe]
            if self.threads[driver.tpe].isRunning():
                self.threads[driver.tpe].terminate()
            del self.threads[driver.tpe]

        # register
        self.drivers[driver.tpe] = driver
        self.threads[driver.tpe] = thr

        # run!
        thr.start()

    def register_driver(self, driver: DRIVER_OBJECTS):
        """
        Register driver
        :param driver:
        :return:
        """
        self.drivers[driver.tpe] = driver

    def get_available_drivers(self):
        """
        Get a list of the available driver objects
        :return: List[Driver]
        """
        return [drv for driver_type, drv in self.drivers.items() if drv is not None]

    def drivers_results_iter(self) -> Generator[Tuple[DRIVER_OBJECTS | None, RESULTS_OBJECTS | None]]:
        """
        Iterator returning driver and result types
        :return: driver, result (both can be None)
        """
        for driver_type, drv in self.drivers.items():
            if hasattr(drv, 'results'):
                yield drv, drv.results
            else:
                yield drv, None

    def exists(self, driver_type: SimulationTypes):
        """
        Get the results of the driver
        :param driver_type: driver type to look for
        :return: True / False
        """
        return driver_type in self.drivers.keys()

    def get_driver_results(
            self,
            driver_type: SimulationTypes
    ) -> Tuple[Union[None, DRIVER_OBJECTS], Union[None, RESULTS_OBJECTS]]:
        """
        Get the results of the driver
        :param driver_type: driver type
        :return: driver, results (None, None if not found)
        """

        drv: DRIVER_OBJECTS = self.drivers.get(driver_type, None)

        if drv is not None:
            if hasattr(drv, 'results'):
                return drv, drv.results
            else:
                return drv, None
        else:
            return None, None

    def get_results(self, driver_type: SimulationTypes) -> RESULTS_OBJECTS | None:
        """
        Get the results of the driver
        :param driver_type: driver type
        :return: driver, results (None, None if not found)
        """
        if driver_type in self.drivers.keys():
            drv = self.drivers[driver_type]
            if hasattr(drv, 'results'):
                return drv.results
            else:
                return None
        else:
            return None

    def delete_driver(self, driver_type: SimulationTypes) -> None:
        """
        Get the results of the driver
        :param driver_type: driver type to delete_with_dialogue
        """
        if driver_type in self.drivers.keys():
            del self.drivers[driver_type]

    def delete_driver_by_name(self, study_name: str) -> None:
        """
        Delete the driver by it's name
        :param study_name: driver name
        """
        for driver_type, drv in self.drivers.items():
            if study_name == drv.tpe.value:
                del self.drivers[driver_type]
                return
            if study_name == drv.name:
                del self.drivers[driver_type]
                return

    def get_driver_by_name(self,
                           study_name: str) -> Union[DRIVER_OBJECTS, None]:
        """
        Get the driver by it's name
        :param study_name: driver name
        """
        for driver_type, drv in self.drivers.items():
            if study_name == drv.name:
                return self.drivers[driver_type]
            if study_name == drv.tpe.value:
                return self.drivers[driver_type]
        return None

    def get_results_model_by_name(self,
                                  study_name: str,
                                  study_type: ResultTypes) -> Union[ResultsModel, None]:
        """
        Get the results model given the study name and study type
        :param study_name: name of the study
        :param study_type: name of the study type
        :return: ResultsModel instance or None if not found
        """
        for driver_type, drv in self.drivers.items():
            if study_name == drv.tpe.value or study_name == drv.name:
                if drv.results is not None:
                    tbl = drv.results.mdl(result_type=study_type)
                    if tbl is None:
                        return None
                    else:
                        return ResultsModel(tbl)
                else:
                    print('There seem to be no results :(')
                    return None

        return None

    def register_driver_from_disk_data(self,
                                       grid: MultiCircuit,
                                       study_name: str,
                                       data_dict: Dict[str, pd.DataFrame]) -> Logger:
        """
        Create driver with the results
        :param grid: MultiCircuit instance
        :param study_name: name of the study (i.e. Power Flow)
        :param data_dict: dictionary of data coming from the file
        """
        logger = Logger()

        time_indices = data_dict.get('time_indices', grid.get_all_time_indices())

        driver_tpe = SimulationTypes(study_name)

        pf_results = None
        if driver_tpe == SimulationTypes.RmsSmallSignal_run:
            _, pf_results = self.power_flow
            if pf_results is None:
                logger.add_warning(
                    msg="Power Flow results must be loaded before RMS Small Signal stability results",
                    device=study_name,
                )
                return logger
        else:
            pass

        drv: DRIVER_OBJECTS | None = create_driver(
            grid=grid,
            driver_tpe=driver_tpe,
            time_indices=time_indices,
            pf_results=pf_results,
        )

        if drv is not None:
            if drv.results is None:
                if driver_tpe == SimulationTypes.RmsDynamic_run:
                    drv.results = RmsResults(
                        time_array=pd.DatetimeIndex([]),
                        rms_events_group_names=np.array([], dtype=str),
                        rms_events_group_idtags=np.array([], dtype=str),
                        variables=list(),
                        uid2idx=dict(),
                        vars_glob_name2uid=dict(),
                        devices_vars_info=dict(),
                        parameter_value_maps=list(),
                        has_event_group_results=np.array([], dtype=bool),
                    )
                elif driver_tpe == SimulationTypes.EmtDynamic_run:
                    drv.results = EmtResults(
                        time_array=pd.DatetimeIndex([]),
                        emt_events_group_names=np.array([], dtype=str),
                        emt_events_group_idtags=np.array([], dtype=str),
                        variables=list(),
                        diff_variables=list(),
                        uid2idx_vars=dict(),
                        uid2idx_diff=dict(),
                        vars_glob_name2uid=dict(),
                        devices_vars_info=dict(),
                        parameter_value_maps=list(),
                        has_event_group_results=np.array([], dtype=bool),
                    )
                elif driver_tpe == SimulationTypes.StateEstimation_run:
                    drv.results = StateEstimationResults(
                        n=grid.get_bus_number(),
                        m=grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True),
                        n_hvdc=grid.get_hvdc_number(),
                        n_vsc=grid.get_vsc_number(),
                        n_gen=grid.get_generation_like_number(),
                        n_batt=grid.get_batteries_number(),
                        n_sh=grid.get_shunt_like_device_number(),
                        bus_names=grid.get_bus_names(),
                        branch_names=grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
                        hvdc_names=grid.get_hvdc_names(),
                        vsc_names=grid.get_vsc_names(),
                        gen_names=grid.get_generation_like_names(),
                        batt_names=grid.get_battery_names(),
                        sh_names=grid.get_shunt_like_devices_names(),
                        bus_types=np.ones(grid.get_bus_number(), dtype=int),
                    )
                elif driver_tpe == SimulationTypes.SigmaAnalysis_run:
                    drv.results = SigmaAnalysisResults(n=grid.get_bus_number())
                elif driver_tpe == SimulationTypes.OPF_NTC_run:
                    drv.results = OptimalNetTransferCapacityResults(
                        bus_names=grid.get_bus_names(),
                        branch_names=grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
                        hvdc_names=grid.get_hvdc_names(),
                        vsc_names=grid.get_vsc_names(),
                        contingency_group_names=grid.get_contingency_group_names(),
                    )
                elif (
                        driver_tpe == SimulationTypes.OptimalNetTransferCapacityTimeSeries_run
                        or driver_tpe == SimulationTypes.OPF_NTC_TS_run
                ):
                    drv.results = OptimalNetTransferCapacityTimeSeriesResults(
                        branch_names=grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
                        bus_names=grid.get_bus_names(),
                        hvdc_names=grid.get_hvdc_names(),
                        vsc_names=grid.get_vsc_names(),
                        contingency_group_names=grid.get_contingency_group_names(),
                        time_array=pd.DatetimeIndex([]),
                        time_indices=np.zeros(0, dtype=int),
                        clustering_results=None,
                    )
                else:
                    pass

            # fill in the saved results
            drv.results.parse_saved_data(grid=grid, data_dict=data_dict, logger=logger)

            if driver_tpe == SimulationTypes.RmsDynamic_run:
                drv.results.restore_dynamic_metadata(grid=grid)
            elif driver_tpe == SimulationTypes.EmtDynamic_run:
                drv.results.restore_dynamic_metadata(grid=grid)
            else:
                pass

            # perform whatever operations are needed after loading
            drv.results.consolidate_after_loading()

            # parse the logger if available
            logger_data = data_dict.get('logger', None)
            if logger_data is not None:
                drv.logger.parse_df(df=logger_data)

            # register the driver
            self.register(drv)
        else:
            warn(f"Session {study_name} not implemented for disk retrieval :/")

        return logger

    def is_this_running(self, sim_tpe: SimulationTypes) -> bool:
        """
        Check if a simulation type is running
        :param sim_tpe: SimulationTypes
        :return: True / False
        """
        for driver_type, drv in self.threads.items():
            if drv is not None:
                if drv.isRunning():
                    if driver_type == sim_tpe:
                        return True
        return False

    def is_anything_running(self) -> bool:
        """
        Check if anything is running
        :return: True / False
        """

        for driver_type, drv in self.threads.items():
            if drv is not None:
                if drv.isRunning():
                    return True
        return False

    @property
    def clustering(self) -> Tuple[ClusteringDriver, ClusteringResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.ClusteringAnalysis_run)
        return drv, results

    @property
    def power_flow(self) -> Tuple[PowerFlowDriver, PowerFlowResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.PowerFlow_run)
        return drv, results

    @property
    def power_flow_3ph(self) -> Tuple[PowerFlowDriver3Ph, PowerFlowResults3Ph]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.PowerFlow3ph_run)
        return drv, results

    @property
    def state_estimation(self) -> Tuple[StateEstimationDriver, StateEstimationResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.StateEstimation_run)
        return drv, results

    @property
    def power_flow_ts(self) -> Tuple[PowerFlowTimeSeriesDriver, PowerFlowTimeSeriesResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.PowerFlowTimeSeries_run)
        return drv, results

    @property
    def optimal_power_flow(self) -> Tuple[OptimalPowerFlowDriver, OptimalPowerFlowResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.OPF_run)
        return drv, results

    @property
    def optimal_power_flow_ts(self) -> Tuple[OptimalPowerFlowTimeSeriesDriver, OptimalPowerFlowTimeSeriesResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.OPFTimeSeries_run)
        return drv, results

    @property
    def short_circuit(self) -> Tuple[ShortCircuitDriver, ShortCircuitResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.ShortCircuit_run)
        return drv, results

    @property
    def linear_power_flow(self) -> Tuple[LinearAnalysisDriver, LinearAnalysisResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.LinearAnalysis_run)
        return drv, results

    @property
    def linear_power_flow_ts(self) -> Tuple[LinearAnalysisTimeSeriesDriver, LinearAnalysisTimeSeriesResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.LinearAnalysis_TS_run)
        return drv, results

    @property
    def contingency(self) -> Tuple[ContingencyAnalysisDriver, ContingencyAnalysisResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.ContingencyAnalysis_run)
        return drv, results

    @property
    def contingency_ts(self) -> Tuple[ContingencyAnalysisTimeSeriesDriver, ContingencyAnalysisTimeSeriesResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.ContingencyAnalysisTS_run)
        return drv, results

    @property
    def continuation_power_flow(self) -> Tuple[ContinuationPowerFlowDriver, ContinuationPowerFlowResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.ContinuationPowerFlow_run)
        return drv, results

    @property
    def net_transfer_capacity(self) -> Tuple[AvailableTransferCapacityDriver, AvailableTransferCapacityResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.NetTransferCapacity_run)
        return drv, results

    @property
    def net_transfer_capacity_ts(self) -> Tuple[AvailableTransferCapacityTimeSeriesDriver,
    AvailableTransferCapacityTimeSeriesResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.NetTransferCapacityTS_run)
        return drv, results

    @property
    def optimal_net_transfer_capacity(self) -> Tuple[
        OptimalNetTransferCapacityDriver, OptimalNetTransferCapacityResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.OPF_NTC_run)
        return drv, results

    @property
    def optimal_net_transfer_capacity_ts(self) -> Tuple[
        OptimalNetTransferCapacityDriver, OptimalNetTransferCapacityResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.OPF_NTC_TS_run)
        return drv, results

    @property
    def nodal_capacity_optimization_ts(self) -> Tuple[NodalCapacityTimeSeriesDriver, NodalCapacityTimeSeriesResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.NodalCapacityTimeSeries_run)
        return drv, results

    @property
    def reliability_analysis(self) -> Tuple[ReliabilityStudyDriver, ReliabilityResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.Reliability_run)
        return drv, results

    @property
    def rms_dynamic_simulation(self) -> Tuple[RmsSimulationDriver, RmsResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.RmsDynamic_run)
        return drv, results

    @property
    def emt_dynamic_simulation(self) -> Tuple[EmtSimulationDriver, EmtResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.EmtDynamic_run)
        return drv, results

    @property
    def stochastic_power_flow(self) -> Tuple[StochasticPowerFlowDriver, StochasticPowerFlowResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.StochasticPowerFlow)
        return drv, results

    @property
    def sigma_analysis(self) -> Tuple[ShortCircuitDriver, SigmaAnalysisResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.SigmaAnalysis_run)
        return drv, results

    @property
    def cascade(self) -> Tuple[CascadingDriver, CascadingResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.Cascade_run)
        return drv, results

    @property
    def inputs_analysis(self) -> Tuple[InputsAnalysisDriver, InputsAnalysisResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.InputsAnalysis_run)
        return drv, results

    @property
    def investments_evaluation(self) -> Tuple[InvestmentsEvaluationDriver, InvestmentsEvaluationResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.InvestmentsEvaluation_run)
        return drv, results

    @property
    def catalogue_optimization(self) -> Tuple[CatalogueOptimizationDriver, InvestmentsEvaluationResults]:
        """
        Catalogue optimization driver / results pair (results reuse the InvestmentsEvaluationResults
        container because both produce the same Pareto-front shape).

        :return: tuple (driver, results) or (None, None) if the simulation has not run.
        """
        drv, results = self.get_driver_results(SimulationTypes.CatalogueOptimization_run)
        return drv, results

    @property
    def node_groups_driver(self) -> Tuple[NodeGroupsDriver, NodeGroupsResults | None]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.NodeGrouping_run)
        return drv, results

    @property
    def small_signal_stability_simulation(self) -> Tuple[SmallSignalStabilityRmsDriver, SmallSignalStabilityRmsResults]:
        """

        :return:
        """
        drv, results = self.get_driver_results(SimulationTypes.RmsSmallSignal_run)
        return drv, results
