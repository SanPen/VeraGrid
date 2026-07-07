# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List
import numpy as np
import pandas as pd
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.basic_structures import IntVec, Vec, StrVec, CxVec, ObjVec
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType


class OptimalNetTransferCapacityResults(ResultsTemplate):
    """
    OPF results.
    Arguments:
        **Sbus**: bus power Injections
        **voltage**: bus voltages
        **load_shedding**: load shedding values
        **Sf**: branch power values
        **overloads**: branch overloading values
        **loading**: branch loading values
        **losses**: branch losses
        **converged**: converged?
    """

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='bus_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='branch_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='contingency_group_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='bus_types', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='voltage', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Sbus', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='dSbus', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='bus_shadow_prices', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='load_shedding', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='nodal_balance', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='Sf', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='St', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='overloads', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='loading', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='losses', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='phase_shift', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='rates', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='contingency_rates', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='alpha', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='monitor_logic', tpe=ObjVec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_Pf', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_loading', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_losses', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_Pf', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_loading', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_losses', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='converged', tpe=bool, old_names=list(), expandable=False),
        ResultsProperty(name='inter_area_flows', tpe=float, old_names=list(), expandable=False),
        ResultsProperty(name='structural_inter_area_flows', tpe=float, old_names=list(), expandable=False),
        ResultsProperty(name='contingency_flows_list', tpe=list, old_names=list(), expandable=False),
        ResultsProperty(name='strict_formulation', tpe=bool, old_names=list(), expandable=False),
        ResultsProperty(name='sending_bus_idx', tpe=list, old_names=list(), expandable=False),
        ResultsProperty(name='receiving_bus_idx', tpe=list, old_names=list(), expandable=False),
        ResultsProperty(name='inter_space_branches', tpe=list, old_names=list(), expandable=False),
        ResultsProperty(name='inter_space_hvdc', tpe=list, old_names=list(), expandable=False),
        ResultsProperty(name='inter_space_vsc', tpe=list, old_names=list(), expandable=False),
    )

    __slots__ = (
        "bus_names",
        "branch_names",
        "hvdc_names",
        "vsc_names",
        "contingency_group_names",
        "bus_types",
        "voltage",
        "Sbus",
        "dSbus",
        "bus_shadow_prices",
        "load_shedding",
        "nodal_balance",
        "Sf",
        "St",
        "overloads",
        "loading",
        "losses",
        "phase_shift",
        "rates",
        "contingency_rates",
        "alpha",
        "monitor_logic",
        "hvdc_Pf",
        "hvdc_loading",
        "hvdc_losses",
        "vsc_Pf",
        "vsc_loading",
        "vsc_losses",
        "sending_bus_idx",
        "receiving_bus_idx",
        "inter_space_branches",
        "inter_space_hvdc",
        "inter_space_vsc",
        "contingency_flows_list",
        "strict_formulation",
        "converged",
        "inter_area_flows",
        "structural_inter_area_flows",
    )

    def __init__(self,
                 bus_names: StrVec,
                 branch_names: StrVec,
                 hvdc_names: StrVec,
                 vsc_names: StrVec,
                 contingency_group_names: StrVec, ):
        """

        :param bus_names:
        :param branch_names:
        :param hvdc_names:
        """

        ResultsTemplate.__init__(self,
                                 name='NTC',
                                 available_results={
                                     ResultTypes.BusResults: [
                                         ResultTypes.BusVoltageModule,
                                         ResultTypes.BusVoltageAngle,
                                         ResultTypes.BusActivePower,
                                         ResultTypes.BusActivePowerIncrement,
                                     ],
                                     ResultTypes.BranchResults: [
                                         ResultTypes.BranchActivePowerFrom,
                                         ResultTypes.BranchLoading,
                                         ResultTypes.BranchTapAngle,
                                         ResultTypes.BranchMonitoring,
                                         ResultTypes.AvailableTransferCapacityAlpha,
                                     ],
                                     ResultTypes.HvdcResults: [
                                         ResultTypes.HvdcPowerFrom,
                                     ],
                                     ResultTypes.VscResults: [
                                         ResultTypes.VscPowerFromPositive,
                                         ResultTypes.VscPowerFromNegative,
                                     ],
                                     ResultTypes.FlowReports: [
                                         ResultTypes.ContingencyFlowsReport,
                                         ResultTypes.InterSpaceBranchPower,
                                         ResultTypes.InterSpaceBranchLoading,
                                     ],
                                 },
                                 time_array=None,
                                 clustering_results=None,
                                 study_results_type=StudyResultsType.NetTransferCapacity
                                 )

        n = len(bus_names)
        m = len(branch_names)
        nhvdc = len(hvdc_names)
        nvsc = len(vsc_names)

        self.bus_names = bus_names
        self.branch_names = branch_names
        self.hvdc_names = hvdc_names
        self.vsc_names = vsc_names
        self.contingency_group_names = contingency_group_names
        self.bus_types = np.ones(n, dtype=int)

        self.voltage = np.zeros(n, dtype=complex)
        self.Sbus = np.zeros(n, dtype=complex)
        self.dSbus = np.zeros(n, dtype=complex)
        self.bus_shadow_prices = np.zeros(n, dtype=float)
        self.load_shedding = np.zeros(n, dtype=float)
        self.nodal_balance = np.zeros(n, dtype=float)

        self.Sf = np.zeros(m, dtype=float)
        self.St = np.zeros(m, dtype=float)
        self.overloads = np.zeros(m, dtype=float)
        self.loading = np.zeros(m, dtype=float)
        self.losses = np.zeros(m, dtype=float)
        self.phase_shift = np.zeros(m, dtype=float)
        self.rates = np.zeros(m, dtype=float)
        self.contingency_rates = np.zeros(m, dtype=float)
        self.alpha = np.zeros(m, dtype=float)
        self.monitor_logic = np.zeros(m, dtype=object)

        self.hvdc_Pf = np.zeros(nhvdc, dtype=float)
        self.hvdc_loading = np.zeros(nhvdc, dtype=float)
        self.hvdc_losses = np.zeros(nhvdc, dtype=float)

        self.vsc_Pf = np.zeros(nvsc, dtype=float)
        self.vsc_loading = np.zeros(nvsc, dtype=float)
        self.vsc_losses = np.zeros(nvsc, dtype=float)

        # indices to post process
        self.sending_bus_idx: List[int] = list()
        self.receiving_bus_idx: List[int] = list()
        self.inter_space_branches: List[tuple[int, float]] = list()  # index, sense
        self.inter_space_hvdc: List[tuple[int, float]] = list()  # index, sense
        self.inter_space_vsc: List[tuple[int, float]] = list()  # index, sense

        # t, m, c, contingency, negative_slack, positive_slack (non-strict)
        # t, m, c, contingency (strict)
        self.contingency_flows_list = list()

        # whether the results come from the strict formulation (no flow slacks)
        self.strict_formulation = False

        self.converged = False

        self.inter_area_flows = 0
        self.structural_inter_area_flows = 0


    def get_bus_df(self) -> pd.DataFrame:
        """
        Get a DataFrame with the buses results
        :return: DataFrame
        """
        return pd.DataFrame(data={'Va': np.angle(self.voltage, deg=True),
                                  'P': self.Sbus.real,
                                  'Shadow price': self.bus_shadow_prices},
                            index=self.bus_names)

    def get_branch_df(self) -> pd.DataFrame:
        """
        Get a DataFrame with the branches results
        :return: DataFrame
        """
        return pd.DataFrame(data={'Pf': self.Sf.real,
                                  'Pt': self.St.real,
                                  'Tap angle': self.phase_shift,
                                  'loading': self.loading.real * 100.0},
                            index=self.branch_names)

    def get_hvdc_df(self) -> pd.DataFrame:
        """
        Get a DataFrame with the battery results
        :return: DataFrame
        """
        return pd.DataFrame(data={'P': self.hvdc_Pf,
                                  'Loading': self.hvdc_loading},
                            index=self.hvdc_names)

    def mdl(self, result_type) -> ResultsTable:
        """
        Plot the results
        :param result_type: type of results (string)
        :return: DataFrame of the results (or None if the result was not understood)
        """

        if result_type == ResultTypes.BusVoltageModule:
            return ResultsTable(
                data=np.abs(self.voltage),
                index=self.bus_names,
                columns=['V (p.u.)'],
                title=str(result_type.value),
                ylabel='(p.u.)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BusDevice
            )

        elif result_type == ResultTypes.BusVoltageAngle:
            return ResultsTable(
                data=np.angle(self.voltage),
                index=self.bus_names,
                columns=['V (radians)'],
                title=str(result_type.value),
                ylabel='(radians)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BusDevice
            )

        elif result_type == ResultTypes.BusActivePower:
            return ResultsTable(
                data=np.real(self.Sbus),
                index=self.bus_names,
                columns=[result_type.value],
                title=str(result_type.value),
                ylabel='(MW)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BusDevice
            )

        elif result_type == ResultTypes.BusActivePowerIncrement:
            return ResultsTable(
                data=np.real(self.dSbus),
                index=self.bus_names,
                columns=[result_type.value],
                title=str(result_type.value),
                ylabel='(MW)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BusDevice
            )

        elif result_type == ResultTypes.BranchActivePowerFrom:
            return ResultsTable(
                data=self.Sf.real,
                columns=['Sf'],
                index=self.branch_names,
                title=str(result_type.value),
                ylabel='(MW)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BranchDevice
            )

        elif result_type == ResultTypes.BranchLoading:
            return ResultsTable(
                data=self.loading * 100.0,
                index=self.branch_names,
                columns=['Loading'],
                title=str(result_type.value),
                ylabel='(%)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BranchDevice
            )

        elif result_type == ResultTypes.BranchLosses:
            return ResultsTable(
                data=self.losses.real,
                index=self.branch_names,
                columns=['PLosses'],
                title=str(result_type.value),
                ylabel='(MW)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BranchDevice
            )

        elif result_type == ResultTypes.BranchTapAngle:
            return ResultsTable(
                data=np.rad2deg(self.phase_shift),
                index=self.branch_names,
                columns=['V (deg)'],
                title=str(result_type.value),
                ylabel='(deg)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BranchDevice
            )

        elif result_type == ResultTypes.HvdcPowerFrom:
            return ResultsTable(
                data=self.hvdc_Pf,
                index=self.hvdc_names,
                columns=['Pf'],
                title=str(result_type.value),
                ylabel='(MW)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.HVDCLineDevice
            )

        elif result_type == ResultTypes.VscPowerFromPositive:
            return ResultsTable(
                data=self.vsc_Pf,
                index=self.vsc_names,
                columns=['Pf'],
                title=str(result_type.value),
                ylabel='(MW)',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.VscDevice
            )

        elif result_type == ResultTypes.AvailableTransferCapacityAlpha:
            return ResultsTable(
                data=self.alpha,
                index=self.branch_names,
                title=str(result_type.value),
                columns=['Sensitivity'],
                ylabel='(p.u.)',
                xlabel='',
                units='',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BranchDevice
            )

        elif result_type == ResultTypes.InterSpaceBranchPower:

            data = list()
            index = list()
            for k, sense in self.inter_space_branches:
                index.append(self.branch_names[k])
                data.append(self.Sf[k].real)

            for k, sense in self.inter_space_hvdc:
                index.append(self.hvdc_names[k])
                data.append(self.hvdc_Pf[k])

            for k, sense in self.inter_space_vsc:
                index.append(self.vsc_names[k])
                data.append(self.vsc_Pf[k])

            index.append("Total")
            data.append(self.inter_area_flows)

            return ResultsTable(
                data=np.array(data),
                index=np.array(index),
                columns=['Flow (MW)'],
                title=str(result_type.value),
                ylabel='(MW)',
                xlabel='',
                units='',
                cols_device_type=DeviceType.BranchDevice,
                idx_device_type=DeviceType.BranchDevice
            )

        elif result_type == ResultTypes.InterSpaceBranchLoading:
            data = list()
            index = list()
            for k, sense in self.inter_space_branches:
                index.append(self.branch_names[k])
                data.append(self.loading[k].real)

            for k, sense in self.inter_space_hvdc:
                index.append(self.hvdc_names[k])
                data.append(self.hvdc_loading[k])

            for k, sense in self.inter_space_vsc:
                index.append(self.vsc_names[k])
                data.append(self.vsc_loading[k])

            return ResultsTable(
                data=np.array(data) * 100.0,
                index=np.array(index),
                columns=['Loading (%)'],
                title=str(result_type.value),
                ylabel='(%)',
                xlabel='',
                units='',
                cols_device_type=DeviceType.BranchDevice,
                idx_device_type=DeviceType.BranchDevice
            )

        elif result_type == ResultTypes.BranchMonitoring:
            return ResultsTable(
                data=self.monitor_logic,
                index=self.branch_names,
                title=str(result_type.value),
                columns=['Monitoring logic'],
                ylabel='()',
                xlabel='',
                units='',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.BranchDevice
            )

        elif result_type == ResultTypes.ContingencyFlowsReport:
            data = list()
            index = list()
            columns = ['Contingency group index', 'Contingency group',
                       'Monitored index', 'Monitored branch',
                       'Flow (MW)', 'Loading (%)']
            for entry in self.contingency_flows_list:
                # The strict formulation stores (t, m, c, flow) with no slacks,
                # while the non-strict one stores (t, m, c, flow, neg_slack, pos_slack).
                if self.strict_formulation:
                    t, m, c, contingency = entry
                    flow_c = contingency
                else:
                    t, m, c, contingency, negative_slack, positive_slack = entry
                    flow_c = contingency - negative_slack + positive_slack
                index.append("")
                loading_c = abs(flow_c) / self.contingency_rates[m] * 100
                data.append([
                    # Contingency group info
                    c, self.contingency_group_names[c],
                    # Monitored branch info
                    m, self.branch_names[m], np.round(flow_c, 4), np.round(loading_c, 4)
                ])

            return ResultsTable(
                data=np.array(data),
                index=np.array(index),
                columns=columns,
                title=str(result_type.value),
                ylabel='',
                xlabel='',
                units='',
                cols_device_type=DeviceType.NoDevice,
                idx_device_type=DeviceType.NoDevice
            )

        else:
            raise ValueError(f"Unknown NTC result type {result_type}")
