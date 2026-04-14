# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import numba as nb
from typing import Union

from VeraGridEngine.basic_structures import IntVec, StrVec, Mat, Vec, CxMat, CxVec
from VeraGridEngine.enumerations import EngineType, ContingencyMethod
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.LinearFactors.linear_analysis import LinearMultiContingencies, LinearAnalysisTs
from VeraGridEngine.Simulations.LinearFactors.linear_analysis_options import LinearAnalysisOptions
from VeraGridEngine.Simulations.ContingencyAnalysis.Methods.linear_contingency_analysis import (
    linear_contingency_analysis, linear_contingency_scan_numba)
from VeraGridEngine.Simulations.ContingencyAnalysis.Methods.nonlinear_contingency_analysis import (
    nonlinear_contingency_analysis)
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_driver import (ContingencyAnalysisOptions,
                                                                                        ContingencyAnalysisDriver)
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_ts_results import (
    ContingencyAnalysisTimeSeriesResults)
from VeraGridEngine.enumerations import SimulationTypes
from VeraGridEngine.Simulations.driver_template import TimeSeriesDriverTemplate
from VeraGridEngine.Simulations.Clustering.clustering_results import ClusteringResults
from VeraGridEngine.Compilers.circuit_to_newton_pa import newton_pa_contingencies, translate_contingency_report, \
    NEWTON_PA_AVAILABLE
from VeraGridEngine.Compilers.circuit_to_gslv import (gslv_contingencies_ts, GSLV_AVAILABLE)
from VeraGridEngine.Utils.NumericalMethods.weldorf_online_stddev import WeldorfOnlineStdDevMat


@nb.njit()
def max_abs_per_col(A: Mat) -> Vec:
    res = np.zeros(A.shape[1], dtype=float)

    for j in range(A.shape[1]):  # for each col (device)
        for i in range(A.shape[0]):  # for each row (contingency)

            val = abs(A[i, j])
            if val > abs(res[j]):
                res[j] = A[i, j]

    return res


@nb.njit()
def max_abs_per_col_cx(A: CxMat) -> CxVec:
    res = np.zeros(A.shape[1], dtype=nb.complex128)

    for j in range(A.shape[1]):  # for each col (device)
        for i in range(A.shape[0]):  # for each row (contingency)

            val = abs(A[i, j])
            if val > abs(res[j]):
                res[j] = A[i, j]

    return res


class ContingencyAnalysisTimeSeriesDriver(TimeSeriesDriverTemplate):
    """
    Contingency Analysis Time Series
    """
    name = 'Contingency analysis time series'
    tpe = SimulationTypes.ContingencyAnalysisTS_run

    def __init__(self,
                 grid: MultiCircuit,
                 options: ContingencyAnalysisOptions,
                 time_indices: IntVec | None = None,
                 clustering_results: Union["ClusteringResults", None] = None,
                 opf_time_series_results=None,
                 engine: EngineType = EngineType.VeraGrid):
        """
        Contingency analysis constructor
        :param grid: MultiCircuit instance
        :param options: ContingencyAnalysisOptions instance
        :param time_indices: array of time indices to simulate
        :param clustering_results: ClusteringResults instance (optional)
        :param engine: Calculation engine to use
        """
        TimeSeriesDriverTemplate.__init__(
            self,
            grid=grid,
            time_indices=grid.get_all_time_indices() if time_indices is None else time_indices,
            clustering_results=clustering_results,
            engine=engine
        )

        # Options to use
        self.options: Union[ContingencyAnalysisOptions, LinearAnalysisOptions] = options

        self.opf_time_series_results = opf_time_series_results

        # N-K results
        self.results: ContingencyAnalysisTimeSeriesResults = ContingencyAnalysisTimeSeriesResults(
            n=self.grid.get_bus_number(),
            nbr=self.grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True),
            time_array=self.grid.time_profile[self.time_indices],
            bus_names=self.grid.get_bus_names(),
            branch_names=self.grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
            bus_types=np.ones(self.grid.get_bus_number(), dtype=int),
            con_names=self.grid.get_contingency_group_names(),
            clustering_results=clustering_results
        )

        self.branch_names: StrVec = np.empty(shape=grid.get_branch_number(add_hvdc=False,
                                                                          add_vsc=False,
                                                                          add_switch=True), dtype=str)

    def run_nonlinear_contingency_analysis(self) -> ContingencyAnalysisTimeSeriesResults:
        """
        Run a contingency analysis in series
        :return: returns the results
        """

        self.report_text("Analyzing...")

        nb = self.grid.get_bus_number()

        time_array = self.grid.time_profile[self.time_indices]

        if self.options.contingency_groups is None:
            con_names = self.grid.get_contingency_group_names()
        else:
            con_names = [con.name for con in self.options.contingency_groups]

        results = ContingencyAnalysisTimeSeriesResults(
            n=nb,
            nbr=self.grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True),
            time_array=time_array,
            branch_names=self.grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
            bus_names=self.grid.get_bus_names(),
            bus_types=np.ones(nb, dtype=int),
            con_names=con_names,
            clustering_results=self.clustering_results
        )

        if self.options is None:
            contingency_groups_used = self.grid.get_contingency_groups()
        else:
            contingency_groups_used = (self.grid.get_contingency_groups()
                                       if self.options.contingency_groups is None
                                       else self.options.contingency_groups)

        linear_multiple_contingencies = LinearMultiContingencies(
            grid=self.grid,
            contingency_groups_used=contingency_groups_used
        )

        area_names, bus_area_indices, F, T, hvdc_F, hvdc_T = self.grid.get_branch_areas_info()

        std_dev_counter = WeldorfOnlineStdDevMat(nrow=results.nt, ncol=results.nbranch)

        for it, t in enumerate(self.time_indices):

            self.report_text('Contingency at ' + str(self.grid.time_profile[t]))
            self.report_progress2(it, len(self.time_indices))

            if self.clustering_results is not None:
                t_prob = self.clustering_results.sampled_probabilities[it]
            else:
                t_prob = 1.0 / len(self.time_indices)

            # set the numerical circuit
            nc = compile_numerical_circuit_at(self.grid,
                                              opf_results=self.opf_time_series_results,
                                              t_idx=t)

            res_t = nonlinear_contingency_analysis(
                nc=nc,
                options=self.options,
                linear_multiple_contingencies=linear_multiple_contingencies,
                area_names=area_names,
                bus_area_indices=bus_area_indices,
                F=F,
                T=T,
                report_text=self.report_text,
                report_progress2=self.report_progress2,
                is_cancel=self.is_cancel,
                t_idx=t,
                t_prob=t_prob,
                logger=self.logger
            )

            # NOTE: res_t results come with the contingencies as rows and the data as columns
            # Sbus[i_con, i_bus]
            # Sf[i_con, k_br]

            # Sbus (ncon, nbus)
            results.S[it, :] = max_abs_per_col_cx(res_t.Sbus)

            results.max_flows[it, :] = max_abs_per_col_cx(res_t.Sf)

            # Note: Loading is (ncon, nbranch)

            loading_abs = np.abs(res_t.loading)
            overloading = loading_abs.copy()
            overloading[overloading <= 1.0] = 0

            for k in range(results.ncon):
                std_dev_counter.update(it, overloading[k, :])

            results.max_loading[it, :] = max_abs_per_col(loading_abs)
            results.overload_count[it, :] = np.count_nonzero(overloading > 1.0)
            results.sum_overload[it, :] = overloading.sum(axis=0)
            results.std_dev_overload[it, :] = overloading.std(axis=0)

            results.srap_used_power += res_t.srap_used_power
            results.report += res_t.report

            # TODO: think what to do about this
            # results.report.merge(res_t.report)

            if self.__cancel__:
                return results

        # compute the mean
        std_dev_counter.finalize()
        results.mean_overload = std_dev_counter.mean
        results.std_dev_overload = std_dev_counter.std_dev

        return results

    def run_linear_contingency_analysis(self) -> ContingencyAnalysisTimeSeriesResults:
        """
        Run a contingency analysis in series
        :return: returns the results
        """

        self.report_text("Analyzing...")

        nb = self.grid.get_bus_number()

        time_array = self.grid.time_profile[self.time_indices]

        if self.options.contingency_groups is None:
            con_names = self.grid.get_contingency_group_names()
        else:
            con_names = [con.name for con in self.options.contingency_groups]

        results = ContingencyAnalysisTimeSeriesResults(
            n=nb,
            nbr=self.grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True),
            time_array=time_array,
            branch_names=self.grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
            bus_names=self.grid.get_bus_names(),
            bus_types=np.ones(nb, dtype=int),
            con_names=con_names,
            clustering_results=self.clustering_results
        )

        if self.options is None:
            contingency_groups_used = self.grid.get_contingency_groups()
        else:
            contingency_groups_used = (self.grid.get_contingency_groups()
                                       if self.options.contingency_groups is None
                                       else self.options.contingency_groups)

        linear_multiple_contingencies = LinearMultiContingencies(
            grid=self.grid,
            contingency_groups_used=contingency_groups_used
        )

        area_names, bus_area_indices, F, T, hvdc_F, hvdc_T = self.grid.get_branch_areas_info()

        std_dev_counter = WeldorfOnlineStdDevMat(nrow=results.nt, ncol=results.nbranch)

        for it, t in enumerate(self.time_indices):

            self.report_text('Contingency at ' + str(self.grid.time_profile[t]))
            self.report_progress2(it, len(self.time_indices))

            if self.clustering_results is not None:
                t_prob = self.clustering_results.sampled_probabilities[it]
            else:
                t_prob = 1.0 / len(self.time_indices)

            # res_t = cdriver.run_at(t_idx=int(t), t_prob=t_prob)
            nc = compile_numerical_circuit_at(self.grid,
                                              opf_results=self.opf_time_series_results,
                                              t_idx=t)

            res_t = linear_contingency_analysis(
                nc=nc,
                options=self.options,
                linear_multiple_contingencies=linear_multiple_contingencies,
                area_names=area_names,
                bus_area_indices=bus_area_indices,
                F=F,
                T=T,
                report_text=None,
                report_progress2=None,
                is_cancel=self.is_cancel,
                t=int(t),
                t_prob=t_prob,
                logger=self.logger
            )

            results.S[it, :] = max_abs_per_col(res_t.Sbus.real)

            results.max_flows[it, :] = max_abs_per_col(res_t.Sf.real)

            # Note: Loading is (ncon, nbranch)

            loading_abs = np.abs(res_t.loading)
            overloading = loading_abs.copy()
            overloading[overloading <= 1.0] = 0

            for k in range(results.ncon):
                std_dev_counter.update(it, overloading[k, :])

            results.max_loading[it, :] = max_abs_per_col(loading_abs)
            results.overload_count[it, :] = np.count_nonzero(overloading > 1.0)
            results.sum_overload[it, :] = overloading.sum(axis=0)
            results.std_dev_overload[it, :] = overloading.std(axis=0)

            results.srap_used_power += res_t.srap_used_power
            results.report += res_t.report

            # TODO: think what to do about this
            # results.report.merge(res_t.report)

            if self.__cancel__:
                return results

        # compute the mean
        std_dev_counter.finalize()
        results.mean_overload = std_dev_counter.mean
        results.std_dev_overload = std_dev_counter.std_dev

        return results

    def run_contingency_scan(self) -> ContingencyAnalysisTimeSeriesResults:
        """
        Run a contngency analysis in series
        :return: returns the results
        """

        self.report_text("Analyzing...")

        nbus = self.grid.get_bus_number()

        time_array = self.grid.time_profile[self.time_indices]

        if self.options.contingency_groups is None:
            con_names = self.grid.get_contingency_group_names()
        else:
            con_names = [con.name for con in self.options.contingency_groups]

        results = ContingencyAnalysisTimeSeriesResults(
            n=nbus,
            nbr=self.grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True),
            time_array=time_array,
            branch_names=self.grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
            bus_names=self.grid.get_bus_names(),
            bus_types=np.ones(nbus, dtype=int),
            con_names=con_names,
            clustering_results=self.clustering_results
        )

        nc = compile_numerical_circuit_at(self.grid,
                                          t_idx=None)

        lin_mc = LinearMultiContingencies(grid=self.grid,
                                          contingency_groups_used=self.grid.get_contingency_groups())

        n_con_groups = self.grid.get_contingency_groups_number()

        # Get the branch index array and the contringency group it belongs array
        # single_con_idx: array of single contingency branch indices,
        # single_con_cg_idx: array of the matching contingency groups
        single_con_br_idx, single_con_cg_idx = lin_mc.get_single_con_branch_idx()

        mon_idx = np.where(nc.passive_branch_data.monitor_loading == 1)[0]

        linear = LinearAnalysisTs(grid=self.grid)

        Pbus_mat = self.grid.get_Pbus_prof()

        std_dev_counter = WeldorfOnlineStdDevMat(nrow=results.nt, ncol=results.nbranch)

        for it, t in enumerate(self.time_indices):

            self.report_text('Contingency at ' + str(self.grid.time_profile[t]))
            self.report_progress2(it, len(self.time_indices))

            # get the corresponding linear analysis
            lin_t = linear.get_linear_analysis_at(t_idx=t)

            SbrCon, LoadingCon, problems = linear_contingency_scan_numba(
                nbr=nc.nbr,
                n_con_groups=n_con_groups,
                Pbus=Pbus_mat[t, :],
                rates=nc.passive_branch_data.rates,
                con_rates=nc.passive_branch_data.contingency_rates,
                PTDF=lin_t.PTDF,
                LODF=lin_t.LODF,
                mon_idx=mon_idx,
                single_con_br_idx=single_con_br_idx,
                single_con_cg_idx=single_con_cg_idx
            )

            results.S[it, :] = max_abs_per_col(Pbus_mat[t, :])

            results.max_flows[it, :] = max_abs_per_col(SbrCon)

            # Note: Loading is (ncon, nbranch)

            loading_abs = np.abs(LoadingCon)
            overloading = loading_abs.copy()
            overloading[overloading <= 1.0] = 0

            for k in range(results.ncon):
                std_dev_counter.update(it, overloading[k, :])

            results.max_loading[it, :] = max_abs_per_col(loading_abs)
            results.overload_count[it, :] = np.count_nonzero(overloading > 1.0)
            results.sum_overload[it, :] = overloading.sum(axis=0)
            results.std_dev_overload[it, :] = overloading.std(axis=0)

            # results.srap_used_power += res_t.srap_used_power
            # results.report += res_t.report

            # TODO: think what to do about this
            # results.report.merge(res_t.report)

            if self.__cancel__:
                return results

        # compute the mean
        std_dev_counter.finalize()
        results.mean_overload = std_dev_counter.mean
        results.std_dev_overload = std_dev_counter.std_dev

        return results

    def run_newton_pa(self) -> ContingencyAnalysisTimeSeriesResults:
        """
        Run with Newton Power Analytics
        :return:
        """
        res = newton_pa_contingencies(circuit=self.grid,
                                      con_opt=self.options,
                                      time_series=True,
                                      time_indices=self.time_indices)

        time_array = self.grid.time_profile[self.time_indices]

        nb = self.grid.get_bus_number()
        results = ContingencyAnalysisTimeSeriesResults(
            n=nb,
            nbr=self.grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True),
            time_array=time_array,
            branch_names=self.grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
            bus_names=self.grid.get_bus_names(),
            bus_types=np.ones(nb, dtype=int),
            con_names=self.grid.get_contingency_group_names(),
            clustering_results=self.clustering_results
        )

        # results.S[t, :] = res_t.S.real.max(axis=0)
        results.max_flows = np.abs(res.contingency_flows)
        results.max_loading = res.contingency_loading

        translate_contingency_report(newton_report=res.report, veragrid_report=results.report)

        return results

    def run_gslv(self) -> ContingencyAnalysisTimeSeriesResults:
        """
        Run with Newton Power Analytics
        :return:
        """
        res = gslv_contingencies_ts(circuit=self.grid,
                                    con_opt=self.options,
                                    time_series=True,
                                    time_indices=self.time_indices)

        time_array = self.grid.time_profile[self.time_indices]

        nb = self.grid.get_bus_number()
        results = ContingencyAnalysisTimeSeriesResults(
            n=nb,
            nbr=self.grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True),
            time_array=time_array,
            branch_names=self.grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
            bus_names=self.grid.get_bus_names(),
            bus_types=np.ones(nb, dtype=int),
            con_names=self.grid.get_contingency_group_names(),
            clustering_results=self.clustering_results
        )

        # results.S[t, :] = res_t.S.real.max(axis=0)
        results.max_flows = res.max_values.Sf
        results.max_loading = res.max_values.loading

        # translate_contingency_report(newton_report=res.report, veragrid_report=results.report)

        return results

    def run(self) -> None:
        """
        Run contingency analysis time series
        """
        self.tic()

        if self.engine == EngineType.VeraGrid:

            if self.options.contingency_method == ContingencyMethod.PowerFlow:
                self.results = self.run_nonlinear_contingency_analysis()

            elif self.options.contingency_method == ContingencyMethod.Linear:
                self.results = self.run_linear_contingency_analysis()

            elif self.options.contingency_method == ContingencyMethod.PTDF_scan:
                self.results = self.run_contingency_scan()

            else:
                pass

        elif self.engine == EngineType.NewtonPA and NEWTON_PA_AVAILABLE:
            self.report_text('Running contingencies in newton... ')
            self.results = self.run_newton_pa()

        elif self.engine == EngineType.GSLV and GSLV_AVAILABLE:
            self.report_text('Running contingencies in gslv... ')
            self.results = self.run_gslv()

        else:
            # default to VeraGrid mode
            self.results = self.run_linear_contingency_analysis()

        self.toc()
