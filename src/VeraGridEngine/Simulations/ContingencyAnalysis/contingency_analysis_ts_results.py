# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from typing import Union
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.ContingencyAnalysis.contingencies_report import ContingencyResultsReport
from VeraGridEngine.basic_structures import DateVec, IntVec, StrVec, Mat
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType
from VeraGridEngine.Simulations.Clustering.clustering_results import ClusteringResults


class ContingencyAnalysisTimeSeriesResults(ResultsTemplate):
    """
    Contingency analysis time series results
    """

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='branch_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='bus_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='bus_types', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='con_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='S', tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name='max_flows', tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name='max_loading', tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name='sum_overload', tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name='mean_overload', tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name='std_dev_overload', tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name='srap_used_power', tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name='report', tpe=ContingencyResultsReport, old_names=list(), expandable=False),
    )

    __slots__ = (
        "nt",
        "original_time_array",
        "branch_names",
        "bus_names",
        "con_names",
        "bus_types",
        "S",
        "max_flows",
        "max_loading",
        "overload_count",
        "sum_overload",
        "mean_overload",
        "std_dev_overload",
        "srap_used_power",
        "report",
    )

    def __init__(self,
                 n: int,
                 nbr: int,
                 time_array: DateVec,
                 original_time_array: DateVec,
                 bus_names: StrVec,
                 branch_names: StrVec,
                 bus_types: IntVec,
                 con_names: StrVec,
                 clustering_results: Union[ClusteringResults, None]):
        """
        ContingencyAnalysisTimeSeriesResults
        :param n: number of nodes
        :param nbr: number of branches
        :param time_array: array of time values
        :param bus_names: array of bus names
        :param branch_names: array of branch names
        :param bus_types: array of bus types
        :param con_names: array of contingency names
        :param clustering_results: Clustering results if applicable
        """

        ResultsTemplate.__init__(
            self,
            name='N-1 time series',
            available_results={
                ResultTypes.StatisticResults: [
                    ResultTypes.MaxContingencyFlows,
                    ResultTypes.MaxContingencyLoading,
                    ResultTypes.ContingencyOverloadSum,
                    ResultTypes.MeanContingencyOverLoading,
                    ResultTypes.StdDevContingencyOverLoading,
                    ResultTypes.SrapUsedPower,
                ],
                ResultTypes.ReportsResults: [
                    ResultTypes.ContingencyAnalysisReport,
                    ResultTypes.ContingencyStatisticalAnalysisReport
                ]
            },
            time_array=time_array,
            clustering_results=clustering_results,
            study_results_type=StudyResultsType.ContingencyAnalysisTimeSeries
        )

        self.nt = len(time_array)

        # this is the complete time array because the report indices
        # may be referring to a point outside the simulation range
        self.original_time_array = original_time_array

        self.branch_names: StrVec = branch_names
        self.bus_names: StrVec = bus_names
        self.con_names: StrVec = con_names
        self.bus_types: IntVec = bus_types

        """
        Tabla de sobrecargas máximas (tiempo, rama)
        Tabla de desviación típica (tiempo, rama)
        Tabla de frecuencia de sobrecarga (tiempo, rama)
        Tabla de índices de la máxima sobrecarga (tiempo, rama)
        Tabla de suma de sobrecarga (tiempo, rama)
        """

        self.S: Mat = np.zeros((self.nt, n))

        self.max_flows: Mat = np.zeros((self.nt, nbr))

        self.max_loading: Mat = np.zeros((self.nt, nbr))

        self.overload_count: Mat = np.zeros((self.nt, nbr))

        self.sum_overload: Mat = np.zeros((self.nt, nbr))

        self.mean_overload: Mat = np.zeros((self.nt, nbr))

        self.std_dev_overload: Mat = np.zeros((self.nt, nbr))

        self.srap_used_power = np.zeros((nbr, n), dtype=float)

        self.report: ContingencyResultsReport = ContingencyResultsReport()


    @property
    def nbus(self) -> int:
        """
        Number of buses
        """
        return len(self.bus_names)

    @property
    def nbranch(self) -> int:
        """
        Number of branches
        """
        return len(self.branch_names)

    @property
    def ncon(self) -> int:
        """
        Number of contingencies
        """
        return len(self.con_names)

    def apply_new_time_series_rates(self, nc: NumericalCircuit):
        """
        Apply new rates
        :param nc:
        :return:
        """
        rates = nc.Rates.T
        self.max_loading = self.max_flows / (rates + 1e-9)

    # def get_dict(self):
    #     """
    #     Returns a dictionary with the results sorted in a dictionary
    #     :return: dictionary of 2D numpy arrays (probably of complex numbers)
    #     """
    #     data = {
    #         # 'overload_count': self.overload_count.tolist(),
    #         # 'relative_frequency': self.relative_frequency.tolist(),
    #         # 'max_overload': self.max_overload.tolist(),
    #         'worst_flows': self.max_flows.tolist(),
    #         'worst_loading': self.max_loading.tolist(),
    #     }
    #     return data

    def mdl(self, result_type: ResultTypes):
        """
        Plot the results
        :param result_type:
        :return:
        """

        if result_type == ResultTypes.MaxContingencyFlows:

            return ResultsTable(
                data=self.max_flows,
                index=pd.to_datetime(self.time_array),
                columns=self.branch_names,
                title=result_type.value,
                units='(MW)',
                cols_device_type=DeviceType.BranchDevice,
                idx_device_type=DeviceType.TimeDevice
            )

        elif result_type == ResultTypes.MaxContingencyLoading:

            return ResultsTable(
                data=self.max_loading * 100.0,
                index=pd.to_datetime(self.time_array),
                columns=self.branch_names,
                title=result_type.value,
                units='(%)',
                cols_device_type=DeviceType.BranchDevice,
                idx_device_type=DeviceType.TimeDevice
            )

        elif result_type == ResultTypes.ContingencyOverloadSum:

            return ResultsTable(
                data=self.sum_overload,
                index=pd.to_datetime(self.time_array),
                idx_device_type=DeviceType.TimeDevice,
                columns=self.branch_names,
                cols_device_type=DeviceType.BranchDevice,
                title=result_type.value,
                units='(MW)'
            )

        elif result_type == ResultTypes.MeanContingencyOverLoading:

            return ResultsTable(
                data=self.mean_overload * 100.0,
                index=pd.to_datetime(self.time_array),
                idx_device_type=DeviceType.TimeDevice,
                columns=self.branch_names,
                cols_device_type=DeviceType.BranchDevice,
                title=result_type.value,
                units='(%)'
            )

        elif result_type == ResultTypes.StdDevContingencyOverLoading:

            return ResultsTable(
                data=self.std_dev_overload * 100.0,
                index=pd.to_datetime(self.time_array),
                idx_device_type=DeviceType.TimeDevice,
                columns=self.branch_names,
                cols_device_type=DeviceType.BranchDevice,
                title=result_type.value,
                units='(%)'
            )

        elif result_type == ResultTypes.SrapUsedPower:

            return ResultsTable(
                data=self.srap_used_power * 100.0,
                index=self.branch_names,
                idx_device_type=DeviceType.BranchDevice,
                columns=self.bus_names,
                cols_device_type=DeviceType.BusDevice,
                title=result_type.value,
                units='(MW)'
            )

        elif result_type == ResultTypes.ContingencyAnalysisReport:

            return ResultsTable(
                data=self.report.get_data(time_array=self.original_time_array, time_format='%Y/%m/%d  %H:%M.%S'),
                index=self.report.get_index(),
                idx_device_type=DeviceType.NoDevice,
                columns=self.report.get_headers(),
                cols_device_type=DeviceType.NoDevice,
                title=result_type.value,
            )

        elif result_type == ResultTypes.ContingencyStatisticalAnalysisReport:

            try:
                df = self.report.get_summary_table(time_array=self.original_time_array,
                                                   time_format='%Y/%m/%d  %H:%M.%S')

                return ResultsTable(
                    data=df.values,
                    index=df.index.tolist(),
                    idx_device_type=DeviceType.NoDevice,
                    columns=df.columns.tolist(),
                    cols_device_type=DeviceType.NoDevice,
                    title=result_type.value,
                )
            except KeyError as e:
                print(f"error getting summary table: {e}")
                return None


        else:
            raise Exception('Result type not understood:' + str(result_type))
