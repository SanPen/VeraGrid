# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Union

import matplotlib.colors as plt_colors
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from VeraGridEngine.Simulations.Clustering.clustering_results import ClusteringResults
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsProperty, ResultsTemplate
from VeraGridEngine.basic_structures import BoolVec, CxMat, DateVec, IntVec, Mat, StrVec, Vec
from VeraGridEngine.enumerations import DeviceType, ResultTypes, StudyResultsType


def _build_time_series_results_table(
    data: np.ndarray,
    time_array: DateVec,
    columns: np.ndarray,
    cols_device_type: DeviceType,
    title: str,
    ylabel: str,
    units: str,
) -> ResultsTable:
    """
    Build one standard time-series results table.

    :param data: Matrix whose first dimension is time.
    :param time_array: Simulation time stamps.
    :param columns: Output column labels.
    :param cols_device_type: Device type associated with the columns.
    :param title: Table title.
    :param ylabel: Plot y-axis label.
    :param units: Engineering units label.
    :return: Time-indexed results table.
    """
    return ResultsTable(
        data=data,
        index=pd.to_datetime(time_array),
        idx_device_type=DeviceType.TimeDevice,
        columns=columns,
        cols_device_type=cols_device_type,
        title=title,
        ylabel=ylabel,
        units=units,
    )


class PowerFlowTimeSeriesResults3Ph(ResultsTemplate):
    """
    Three-phase power-flow time-series results container.
    """

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name="bus_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="branch_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="hvdc_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="vsc_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="gen_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="batt_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="sh_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="load_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="bus_types", tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name="time_array", tpe=DateVec, old_names=list(), expandable=False),
        ResultsProperty(name="F", tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name="T", tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name="hvdc_F", tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name="hvdc_T", tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name="bus_area_indices", tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name="area_names", tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name="Sbus_N", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="Sbus_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="Sbus_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="Sbus_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="voltage_N", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="voltage_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="voltage_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="voltage_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="Sf_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="Sf_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="Sf_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="St_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="St_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="St_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="If_N", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="If_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="If_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="If_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="It_N", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="It_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="It_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="It_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="tap_module", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="tap_angle", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="Vbranch_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="Vbranch_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="Vbranch_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="loading_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="loading_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="loading_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="losses_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="losses_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="losses_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="losses_hvdc", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="Pf_hvdc_A", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="Pf_hvdc_B", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="Pf_hvdc_C", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="Pt_hvdc_A", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="Pt_hvdc_B", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="Pt_hvdc_C", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="loading_hvdc", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="losses_vsc", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="Pfp_vsc", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="St_vsc_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="St_vsc_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="St_vsc_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="If_vsc", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="It_vsc_A", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="It_vsc_B", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="It_vsc_C", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="loading_vsc", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="gen_q_A", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="gen_q_B", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="gen_q_C", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="battery_q_A", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="battery_q_B", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="battery_q_C", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="shunt_q_A", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="shunt_q_B", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="shunt_q_C", tpe=Mat, old_names=list(), expandable=True),
        ResultsProperty(name="shunt_Vn", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="load_Vn", tpe=CxMat, old_names=list(), expandable=True),
        ResultsProperty(name="error_values", tpe=Vec, old_names=list(), expandable=True),
        ResultsProperty(name="converged_values", tpe=BoolVec, old_names=list(), expandable=True),
    )

    __slots__ = (
        "bus_names",
        "branch_names",
        "hvdc_names",
        "vsc_names",
        "gen_names",
        "batt_names",
        "sh_names",
        "load_names",
        "bus_types",
        "Sbus_N",
        "Sbus_A",
        "Sbus_B",
        "Sbus_C",
        "voltage_N",
        "voltage_A",
        "voltage_B",
        "voltage_C",
        "Sf_A",
        "Sf_B",
        "Sf_C",
        "St_A",
        "St_B",
        "St_C",
        "If_N",
        "If_A",
        "If_B",
        "If_C",
        "It_N",
        "It_A",
        "It_B",
        "It_C",
        "tap_module",
        "tap_angle",
        "Vbranch_A",
        "Vbranch_B",
        "Vbranch_C",
        "loading_A",
        "loading_B",
        "loading_C",
        "losses_A",
        "losses_B",
        "losses_C",
        "losses_hvdc",
        "Pf_hvdc_A",
        "Pf_hvdc_B",
        "Pf_hvdc_C",
        "Pt_hvdc_A",
        "Pt_hvdc_B",
        "Pt_hvdc_C",
        "loading_hvdc",
        "losses_vsc",
        "Pfp_vsc",
        "St_vsc_A",
        "St_vsc_B",
        "St_vsc_C",
        "If_vsc",
        "It_vsc_A",
        "It_vsc_B",
        "It_vsc_C",
        "loading_vsc",
        "gen_q_A",
        "gen_q_B",
        "gen_q_C",
        "battery_q_A",
        "battery_q_B",
        "battery_q_C",
        "shunt_q_A",
        "shunt_q_B",
        "shunt_q_C",
        "shunt_Vn",
        "load_Vn",
        "error_values",
        "converged_values",
    )

    def __init__(
        self,
        n: int,
        m: int,
        n_hvdc: int,
        n_vsc: int,
        n_gen: int,
        n_batt: int,
        n_sh: int,
        n_load: int,
        bus_names: StrVec,
        branch_names: StrVec,
        hvdc_names: StrVec,
        vsc_names: StrVec,
        gen_names: StrVec,
        batt_names: StrVec,
        sh_names: StrVec,
        load_names: StrVec,
        bus_types: IntVec,
        time_array: DateVec,
        clustering_results: Union[ClusteringResults, None] = None,
    ) -> None:
        """
        Build one three-phase power-flow time-series results object.

        :param n: Expanded three-phase bus count.
        :param m: Expanded three-phase branch count.
        :param n_hvdc: Number of HVDC devices.
        :param n_vsc: Number of VSC devices.
        :param n_gen: Number of generator-like devices.
        :param n_batt: Number of batteries.
        :param n_sh: Number of shunt-like devices.
        :param n_load: Number of load-like devices.
        :param bus_names: Physical bus names.
        :param branch_names: Physical branch names.
        :param hvdc_names: HVDC names.
        :param vsc_names: VSC names.
        :param gen_names: Generator names.
        :param batt_names: Battery names.
        :param sh_names: Shunt names.
        :param load_names: Load names.
        :param bus_types: Bus types vector.
        :param time_array: Simulated time index.
        :param clustering_results: Optional clustering metadata.
        :return: None.
        """
        ResultsTemplate.__init__(
            self,
            name="Power flow time series 3ph",
            available_results={
                ResultTypes.BusResults: [
                    ResultTypes.BusVoltageModuleA,
                    ResultTypes.BusVoltageModuleB,
                    ResultTypes.BusVoltageModuleC,
                    ResultTypes.BusVoltageAngleA,
                    ResultTypes.BusVoltageAngleB,
                    ResultTypes.BusVoltageAngleC,
                    ResultTypes.BusActivePowerA,
                    ResultTypes.BusActivePowerB,
                    ResultTypes.BusActivePowerC,
                    ResultTypes.BusReactivePowerA,
                    ResultTypes.BusReactivePowerB,
                    ResultTypes.BusReactivePowerC,
                ],
                ResultTypes.BranchResults: [
                    ResultTypes.BranchActivePowerFromA,
                    ResultTypes.BranchActivePowerFromB,
                    ResultTypes.BranchActivePowerFromC,
                    ResultTypes.BranchReactivePowerFromA,
                    ResultTypes.BranchReactivePowerFromB,
                    ResultTypes.BranchReactivePowerFromC,
                    ResultTypes.BranchActivePowerToA,
                    ResultTypes.BranchActivePowerToB,
                    ResultTypes.BranchActivePowerToC,
                    ResultTypes.BranchReactivePowerToA,
                    ResultTypes.BranchReactivePowerToB,
                    ResultTypes.BranchReactivePowerToC,
                    ResultTypes.BranchActiveCurrentFromA,
                    ResultTypes.BranchActiveCurrentFromB,
                    ResultTypes.BranchActiveCurrentFromC,
                    ResultTypes.BranchReactiveCurrentFromA,
                    ResultTypes.BranchReactiveCurrentFromB,
                    ResultTypes.BranchReactiveCurrentFromC,
                    ResultTypes.BranchActiveCurrentToA,
                    ResultTypes.BranchActiveCurrentToB,
                    ResultTypes.BranchActiveCurrentToC,
                    ResultTypes.BranchReactiveCurrentToA,
                    ResultTypes.BranchReactiveCurrentToB,
                    ResultTypes.BranchReactiveCurrentToC,
                    ResultTypes.BranchTapModule,
                    ResultTypes.BranchTapAngle,
                    ResultTypes.BranchLoadingA,
                    ResultTypes.BranchLoadingB,
                    ResultTypes.BranchLoadingC,
                    ResultTypes.BranchActiveLossesA,
                    ResultTypes.BranchActiveLossesB,
                    ResultTypes.BranchActiveLossesC,
                    ResultTypes.BranchReactiveLossesA,
                    ResultTypes.BranchReactiveLossesB,
                    ResultTypes.BranchReactiveLossesC,
                    ResultTypes.BranchActiveLossesPercentageA,
                    ResultTypes.BranchActiveLossesPercentageB,
                    ResultTypes.BranchActiveLossesPercentageC,
                    ResultTypes.BranchVoltageA,
                    ResultTypes.BranchVoltageB,
                    ResultTypes.BranchVoltageC,
                    ResultTypes.BranchAnglesA,
                    ResultTypes.BranchAnglesB,
                    ResultTypes.BranchAnglesC,
                ],
                ResultTypes.HvdcResults: [
                    ResultTypes.HvdcPowerFromA,
                    ResultTypes.HvdcPowerFromB,
                    ResultTypes.HvdcPowerFromC,
                    ResultTypes.HvdcPowerToA,
                    ResultTypes.HvdcPowerToB,
                    ResultTypes.HvdcPowerToC,
                    ResultTypes.HvdcLosses,
                ],
                ResultTypes.VscResults: [
                    ResultTypes.VscPowerFromPositive,
                    ResultTypes.VscPowerToA,
                    ResultTypes.VscPowerToB,
                    ResultTypes.VscPowerToC,
                    ResultTypes.VscLosses,
                ],
                ResultTypes.GeneratorResults: [
                    ResultTypes.GeneratorReactivePowerA,
                    ResultTypes.GeneratorReactivePowerB,
                    ResultTypes.GeneratorReactivePowerC,
                ],
                ResultTypes.BatteryResults: [
                    ResultTypes.BatteryReactivePowerA,
                    ResultTypes.BatteryReactivePowerB,
                    ResultTypes.BatteryReactivePowerC,
                ],
                ResultTypes.ShuntResults: [
                    ResultTypes.ShuntReactivePowerA,
                    ResultTypes.ShuntReactivePowerB,
                    ResultTypes.ShuntReactivePowerC,
                    ResultTypes.ShuntNeutralVoltage,
                ],
                ResultTypes.LoadResults: [
                    ResultTypes.LoadNeutralVoltage,
                ],
                ResultTypes.SpecialPlots: [
                    ResultTypes.BusVoltagePolarPlot,
                ],
                ResultTypes.InfoResults: [
                    ResultTypes.SimulationError,
                ],
            },
            time_array=None,
            clustering_results=clustering_results,
            study_results_type=StudyResultsType.PowerFlowTimeSeries,
            is_3ph=True,
        )

        n_bus: int = int(n / 3)
        n_branch: int = int(m / 3)
        n_time: int = len(time_array)

        self.bus_names: StrVec = bus_names
        self.branch_names: StrVec = branch_names
        self.hvdc_names: StrVec = hvdc_names
        self.vsc_names: StrVec = vsc_names
        self.gen_names: StrVec = gen_names
        self.batt_names: StrVec = batt_names
        self.sh_names: StrVec = sh_names
        self.load_names: StrVec = load_names
        self.bus_types: IntVec = np.array(bus_types, dtype=int)
        self.time_array = time_array

        self.F: IntVec = None
        self.T: IntVec = None
        self.hvdc_F: IntVec = None
        self.hvdc_T: IntVec = None
        self.bus_area_indices: IntVec = None
        self.area_names: StrVec = None

        self.Sbus_N: CxMat = np.zeros((n_time, n_bus), dtype=complex)
        self.Sbus_A: CxMat = np.zeros((n_time, n_bus), dtype=complex)
        self.Sbus_B: CxMat = np.zeros((n_time, n_bus), dtype=complex)
        self.Sbus_C: CxMat = np.zeros((n_time, n_bus), dtype=complex)

        self.voltage_N: CxMat = np.zeros((n_time, n_bus), dtype=complex)
        self.voltage_A: CxMat = np.zeros((n_time, n_bus), dtype=complex)
        self.voltage_B: CxMat = np.zeros((n_time, n_bus), dtype=complex)
        self.voltage_C: CxMat = np.zeros((n_time, n_bus), dtype=complex)

        self.Sf_A: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.Sf_B: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.Sf_C: CxMat = np.zeros((n_time, n_branch), dtype=complex)

        self.St_A: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.St_B: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.St_C: CxMat = np.zeros((n_time, n_branch), dtype=complex)

        self.If_N: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.If_A: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.If_B: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.If_C: CxMat = np.zeros((n_time, n_branch), dtype=complex)

        self.It_N: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.It_A: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.It_B: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.It_C: CxMat = np.zeros((n_time, n_branch), dtype=complex)

        self.tap_module: Mat = np.zeros((n_time, n_branch), dtype=float)
        self.tap_angle: Mat = np.zeros((n_time, n_branch), dtype=float)

        self.Vbranch_A: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.Vbranch_B: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.Vbranch_C: CxMat = np.zeros((n_time, n_branch), dtype=complex)

        self.loading_A: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.loading_B: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.loading_C: CxMat = np.zeros((n_time, n_branch), dtype=complex)

        self.losses_A: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.losses_B: CxMat = np.zeros((n_time, n_branch), dtype=complex)
        self.losses_C: CxMat = np.zeros((n_time, n_branch), dtype=complex)

        self.losses_hvdc: Mat = np.zeros((n_time, n_hvdc), dtype=float)
        self.Pf_hvdc_A: Mat = np.zeros((n_time, n_hvdc), dtype=float)
        self.Pf_hvdc_B: Mat = np.zeros((n_time, n_hvdc), dtype=float)
        self.Pf_hvdc_C: Mat = np.zeros((n_time, n_hvdc), dtype=float)
        self.Pt_hvdc_A: Mat = np.zeros((n_time, n_hvdc), dtype=float)
        self.Pt_hvdc_B: Mat = np.zeros((n_time, n_hvdc), dtype=float)
        self.Pt_hvdc_C: Mat = np.zeros((n_time, n_hvdc), dtype=float)
        self.loading_hvdc: Mat = np.zeros((n_time, n_hvdc), dtype=float)

        self.losses_vsc: Mat = np.zeros((n_time, n_vsc), dtype=float)
        self.Pfp_vsc: Mat = np.zeros((n_time, n_vsc), dtype=float)
        self.St_vsc_A: CxMat = np.zeros((n_time, n_vsc), dtype=complex)
        self.St_vsc_B: CxMat = np.zeros((n_time, n_vsc), dtype=complex)
        self.St_vsc_C: CxMat = np.zeros((n_time, n_vsc), dtype=complex)
        self.If_vsc: Mat = np.zeros((n_time, n_vsc), dtype=float)
        self.It_vsc_A: CxMat = np.zeros((n_time, n_vsc), dtype=complex)
        self.It_vsc_B: CxMat = np.zeros((n_time, n_vsc), dtype=complex)
        self.It_vsc_C: CxMat = np.zeros((n_time, n_vsc), dtype=complex)
        self.loading_vsc: Mat = np.zeros((n_time, n_vsc), dtype=float)

        self.gen_q_A: Mat = np.zeros((n_time, n_gen), dtype=float)
        self.gen_q_B: Mat = np.zeros((n_time, n_gen), dtype=float)
        self.gen_q_C: Mat = np.zeros((n_time, n_gen), dtype=float)

        self.battery_q_A: Mat = np.zeros((n_time, n_batt), dtype=float)
        self.battery_q_B: Mat = np.zeros((n_time, n_batt), dtype=float)
        self.battery_q_C: Mat = np.zeros((n_time, n_batt), dtype=float)

        self.shunt_q_A: Mat = np.zeros((n_time, n_sh), dtype=float)
        self.shunt_q_B: Mat = np.zeros((n_time, n_sh), dtype=float)
        self.shunt_q_C: Mat = np.zeros((n_time, n_sh), dtype=float)
        self.shunt_Vn: CxMat = np.zeros((n_time, n_sh), dtype=complex)
        self.load_Vn: CxMat = np.zeros((n_time, n_load), dtype=complex)

        self.error_values: Vec = np.zeros(n_time, dtype=float)
        self.converged_values: BoolVec = np.zeros(n_time, dtype=bool)

    def set_at(self, t: int, results: PowerFlowResults3Ph) -> None:
        """
        Store one snapshot three-phase power-flow solution at one time index.

        :param t: Time row index.
        :param results: Snapshot three-phase results object.
        :return: None.
        """
        self.Sbus_N[t, :] = results.Sbus_N
        self.Sbus_A[t, :] = results.Sbus_A
        self.Sbus_B[t, :] = results.Sbus_B
        self.Sbus_C[t, :] = results.Sbus_C
        self.voltage_N[t, :] = results.voltage_N
        self.voltage_A[t, :] = results.voltage_A
        self.voltage_B[t, :] = results.voltage_B
        self.voltage_C[t, :] = results.voltage_C
        self.Sf_A[t, :] = results.Sf_A
        self.Sf_B[t, :] = results.Sf_B
        self.Sf_C[t, :] = results.Sf_C
        self.St_A[t, :] = results.St_A
        self.St_B[t, :] = results.St_B
        self.St_C[t, :] = results.St_C
        self.If_N[t, :] = results.If_N
        self.If_A[t, :] = results.If_A
        self.If_B[t, :] = results.If_B
        self.If_C[t, :] = results.If_C
        self.It_N[t, :] = results.It_N
        self.It_A[t, :] = results.It_A
        self.It_B[t, :] = results.It_B
        self.It_C[t, :] = results.It_C
        self.tap_module[t, :] = results.tap_module
        self.tap_angle[t, :] = results.tap_angle
        self.Vbranch_A[t, :] = results.Vbranch_A
        self.Vbranch_B[t, :] = results.Vbranch_B
        self.Vbranch_C[t, :] = results.Vbranch_C
        self.loading_A[t, :] = results.loading_A
        self.loading_B[t, :] = results.loading_B
        self.loading_C[t, :] = results.loading_C
        self.losses_A[t, :] = results.losses_A
        self.losses_B[t, :] = results.losses_B
        self.losses_C[t, :] = results.losses_C
        self.losses_hvdc[t, :] = results.losses_hvdc
        self.Pf_hvdc_A[t, :] = results.Pf_hvdc_A
        self.Pf_hvdc_B[t, :] = results.Pf_hvdc_B
        self.Pf_hvdc_C[t, :] = results.Pf_hvdc_C
        self.Pt_hvdc_A[t, :] = results.Pt_hvdc_A
        self.Pt_hvdc_B[t, :] = results.Pt_hvdc_B
        self.Pt_hvdc_C[t, :] = results.Pt_hvdc_C
        self.loading_hvdc[t, :] = results.loading_hvdc
        self.losses_vsc[t, :] = results.losses_vsc
        self.Pfp_vsc[t, :] = results.Pfp_vsc
        self.St_vsc_A[t, :] = results.St_vsc_A
        self.St_vsc_B[t, :] = results.St_vsc_B
        self.St_vsc_C[t, :] = results.St_vsc_C
        self.If_vsc[t, :] = results.If_vsc
        self.It_vsc_A[t, :] = results.It_vsc_A
        self.It_vsc_B[t, :] = results.It_vsc_B
        self.It_vsc_C[t, :] = results.It_vsc_C
        self.loading_vsc[t, :] = results.loading_vsc
        self.gen_q_A[t, :] = results.gen_q_A
        self.gen_q_B[t, :] = results.gen_q_B
        self.gen_q_C[t, :] = results.gen_q_C
        self.battery_q_A[t, :] = results.battery_q_A
        self.battery_q_B[t, :] = results.battery_q_B
        self.battery_q_C[t, :] = results.battery_q_C
        self.shunt_q_A[t, :] = results.shunt_q_A
        self.shunt_q_B[t, :] = results.shunt_q_B
        self.shunt_q_C[t, :] = results.shunt_q_C
        self.shunt_Vn[t, :] = results.shunt_Vn
        self.load_Vn[t, :] = results.load_Vn
        self.error_values[t] = results.error
        self.converged_values[t] = results.converged

    def mdl(self, result_type: ResultTypes) -> ResultsTable:
        """
        Build the requested time-series table.

        :param result_type: Requested result type.
        :return: Results table.
        """
        if result_type == ResultTypes.BusVoltageModuleA:
            return _build_time_series_results_table(np.abs(self.voltage_A), self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BusVoltageModuleB:
            return _build_time_series_results_table(np.abs(self.voltage_B), self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BusVoltageModuleC:
            return _build_time_series_results_table(np.abs(self.voltage_C), self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BusVoltageAngleA:
            return _build_time_series_results_table(np.angle(self.voltage_A, deg=True), self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(deg)", "(deg)")
        elif result_type == ResultTypes.BusVoltageAngleB:
            return _build_time_series_results_table(np.angle(self.voltage_B, deg=True), self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(deg)", "(deg)")
        elif result_type == ResultTypes.BusVoltageAngleC:
            return _build_time_series_results_table(np.angle(self.voltage_C, deg=True), self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(deg)", "(deg)")
        elif result_type == ResultTypes.BusActivePowerA:
            return _build_time_series_results_table(self.Sbus_A.real, self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BusActivePowerB:
            return _build_time_series_results_table(self.Sbus_B.real, self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BusActivePowerC:
            return _build_time_series_results_table(self.Sbus_C.real, self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BusReactivePowerA:
            return _build_time_series_results_table(self.Sbus_A.imag, self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BusReactivePowerB:
            return _build_time_series_results_table(self.Sbus_B.imag, self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BusReactivePowerC:
            return _build_time_series_results_table(self.Sbus_C.imag, self.time_array, self.bus_names, DeviceType.BusDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BusVoltagePolarPlot:
            vm_a: np.ndarray = np.abs(self.voltage_A)
            vm_b: np.ndarray = np.abs(self.voltage_B)
            vm_c: np.ndarray = np.abs(self.voltage_C)
            va_a: np.ndarray = np.angle(self.voltage_A, deg=True)
            va_b: np.ndarray = np.angle(self.voltage_B, deg=True)
            va_c: np.ndarray = np.angle(self.voltage_C, deg=True)
            va_rad: np.ndarray = np.concatenate((np.angle(self.voltage_A, deg=False).reshape(-1), np.angle(self.voltage_B, deg=False).reshape(-1), np.angle(self.voltage_C, deg=False).reshape(-1)))
            vm_flat: np.ndarray = np.concatenate((vm_a.reshape(-1), vm_b.reshape(-1), vm_c.reshape(-1)))
            columns: list[str] = list()
            bus_name: str
            for bus_name in self.bus_names:
                columns.append(f"{bus_name} |Va|")
                columns.append(f"{bus_name} |Vb|")
                columns.append(f"{bus_name} |Vc|")
                columns.append(f"{bus_name} angle A (deg)")
                columns.append(f"{bus_name} angle B (deg)")
                columns.append(f"{bus_name} angle C (deg)")
            if self.plotting_allowed():
                plt.ion()
                color_norm = plt_colors.LogNorm()
                fig = plt.figure(figsize=(8, 6))
                ax3 = plt.subplot(1, 1, 1, projection="polar")
                ax3.scatter(va_rad, vm_flat, c=vm_flat, norm=color_norm)
                fig.suptitle(result_type.value)
                plt.tight_layout()
                plt.show()
            data: np.ndarray = np.concatenate((vm_a, vm_b, vm_c, va_a, va_b, va_c), axis=1)
            return _build_time_series_results_table(data, self.time_array, np.array(columns), DeviceType.NoDevice, result_type.value, "(p.u., deg)", "(p.u., deg)")
        elif result_type == ResultTypes.BranchActivePowerFromA:
            return _build_time_series_results_table(self.Sf_A.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchActivePowerFromB:
            return _build_time_series_results_table(self.Sf_B.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchActivePowerFromC:
            return _build_time_series_results_table(self.Sf_C.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchReactivePowerFromA:
            return _build_time_series_results_table(self.Sf_A.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchReactivePowerFromB:
            return _build_time_series_results_table(self.Sf_B.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchReactivePowerFromC:
            return _build_time_series_results_table(self.Sf_C.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchActivePowerToA:
            return _build_time_series_results_table(self.St_A.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchActivePowerToB:
            return _build_time_series_results_table(self.St_B.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchActivePowerToC:
            return _build_time_series_results_table(self.St_C.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchReactivePowerToA:
            return _build_time_series_results_table(self.St_A.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchReactivePowerToB:
            return _build_time_series_results_table(self.St_B.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchReactivePowerToC:
            return _build_time_series_results_table(self.St_C.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchActiveCurrentFromA:
            return _build_time_series_results_table(self.If_A.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchActiveCurrentFromB:
            return _build_time_series_results_table(self.If_B.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchActiveCurrentFromC:
            return _build_time_series_results_table(self.If_C.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchReactiveCurrentFromA:
            return _build_time_series_results_table(self.If_A.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchReactiveCurrentFromB:
            return _build_time_series_results_table(self.If_B.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchReactiveCurrentFromC:
            return _build_time_series_results_table(self.If_C.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchActiveCurrentToA:
            return _build_time_series_results_table(self.It_A.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchActiveCurrentToB:
            return _build_time_series_results_table(self.It_B.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchActiveCurrentToC:
            return _build_time_series_results_table(self.It_C.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchReactiveCurrentToA:
            return _build_time_series_results_table(self.It_A.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchReactiveCurrentToB:
            return _build_time_series_results_table(self.It_B.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchReactiveCurrentToC:
            return _build_time_series_results_table(self.It_C.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchTapModule:
            return _build_time_series_results_table(self.tap_module, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchTapAngle:
            return _build_time_series_results_table(np.rad2deg(self.tap_angle), self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(deg)", "(deg)")
        elif result_type == ResultTypes.BranchLoadingA:
            return _build_time_series_results_table(np.abs(self.loading_A) * 100.0, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(%)", "(%)")
        elif result_type == ResultTypes.BranchLoadingB:
            return _build_time_series_results_table(np.abs(self.loading_B) * 100.0, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(%)", "(%)")
        elif result_type == ResultTypes.BranchLoadingC:
            return _build_time_series_results_table(np.abs(self.loading_C) * 100.0, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(%)", "(%)")
        elif result_type == ResultTypes.BranchActiveLossesA:
            return _build_time_series_results_table(self.losses_A.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchActiveLossesB:
            return _build_time_series_results_table(self.losses_B.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchActiveLossesC:
            return _build_time_series_results_table(self.losses_C.real, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.BranchReactiveLossesA:
            return _build_time_series_results_table(self.losses_A.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchReactiveLossesB:
            return _build_time_series_results_table(self.losses_B.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchReactiveLossesC:
            return _build_time_series_results_table(self.losses_C.imag, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BranchActiveLossesPercentageA:
            return _build_time_series_results_table(np.abs(self.losses_A.real) / (np.abs(self.Sf_A.real) + 1e-20) * 100.0, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(%)", "(%)")
        elif result_type == ResultTypes.BranchActiveLossesPercentageB:
            return _build_time_series_results_table(np.abs(self.losses_B.real) / (np.abs(self.Sf_B.real) + 1e-20) * 100.0, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(%)", "(%)")
        elif result_type == ResultTypes.BranchActiveLossesPercentageC:
            return _build_time_series_results_table(np.abs(self.losses_C.real) / (np.abs(self.Sf_C.real) + 1e-20) * 100.0, self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(%)", "(%)")
        elif result_type == ResultTypes.BranchVoltageA:
            return _build_time_series_results_table(np.abs(self.Vbranch_A), self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchVoltageB:
            return _build_time_series_results_table(np.abs(self.Vbranch_B), self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchVoltageC:
            return _build_time_series_results_table(np.abs(self.Vbranch_C), self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.BranchAnglesA:
            return _build_time_series_results_table(np.angle(self.Vbranch_A, deg=True), self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(deg)", "(deg)")
        elif result_type == ResultTypes.BranchAnglesB:
            return _build_time_series_results_table(np.angle(self.Vbranch_B, deg=True), self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(deg)", "(deg)")
        elif result_type == ResultTypes.BranchAnglesC:
            return _build_time_series_results_table(np.angle(self.Vbranch_C, deg=True), self.time_array, self.branch_names, DeviceType.BranchDevice, result_type.value, "(deg)", "(deg)")
        elif result_type == ResultTypes.HvdcPowerFromA:
            return _build_time_series_results_table(self.Pf_hvdc_A, self.time_array, self.hvdc_names, DeviceType.HVDCLineDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.HvdcPowerFromB:
            return _build_time_series_results_table(self.Pf_hvdc_B, self.time_array, self.hvdc_names, DeviceType.HVDCLineDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.HvdcPowerFromC:
            return _build_time_series_results_table(self.Pf_hvdc_C, self.time_array, self.hvdc_names, DeviceType.HVDCLineDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.HvdcPowerToA:
            return _build_time_series_results_table(self.Pt_hvdc_A, self.time_array, self.hvdc_names, DeviceType.HVDCLineDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.HvdcPowerToB:
            return _build_time_series_results_table(self.Pt_hvdc_B, self.time_array, self.hvdc_names, DeviceType.HVDCLineDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.HvdcPowerToC:
            return _build_time_series_results_table(self.Pt_hvdc_C, self.time_array, self.hvdc_names, DeviceType.HVDCLineDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.HvdcLosses:
            return _build_time_series_results_table(self.losses_hvdc, self.time_array, self.hvdc_names, DeviceType.HVDCLineDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.VscPowerFromPositive:
            return _build_time_series_results_table(self.Pfp_vsc, self.time_array, self.vsc_names, DeviceType.VscDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.VscPowerToA:
            return _build_time_series_results_table(self.St_vsc_A.real, self.time_array, self.vsc_names, DeviceType.VscDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.VscPowerToB:
            return _build_time_series_results_table(self.St_vsc_B.real, self.time_array, self.vsc_names, DeviceType.VscDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.VscPowerToC:
            return _build_time_series_results_table(self.St_vsc_C.real, self.time_array, self.vsc_names, DeviceType.VscDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.VscLosses:
            return _build_time_series_results_table(self.losses_vsc, self.time_array, self.vsc_names, DeviceType.VscDevice, result_type.value, "(MW)", "(MW)")
        elif result_type == ResultTypes.GeneratorReactivePowerA:
            return _build_time_series_results_table(self.gen_q_A, self.time_array, self.gen_names, DeviceType.GeneratorDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.GeneratorReactivePowerB:
            return _build_time_series_results_table(self.gen_q_B, self.time_array, self.gen_names, DeviceType.GeneratorDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.GeneratorReactivePowerC:
            return _build_time_series_results_table(self.gen_q_C, self.time_array, self.gen_names, DeviceType.GeneratorDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BatteryReactivePowerA:
            return _build_time_series_results_table(self.battery_q_A, self.time_array, self.batt_names, DeviceType.BatteryDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BatteryReactivePowerB:
            return _build_time_series_results_table(self.battery_q_B, self.time_array, self.batt_names, DeviceType.BatteryDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.BatteryReactivePowerC:
            return _build_time_series_results_table(self.battery_q_C, self.time_array, self.batt_names, DeviceType.BatteryDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.ShuntReactivePowerA:
            return _build_time_series_results_table(self.shunt_q_A, self.time_array, self.sh_names, DeviceType.ShuntDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.ShuntReactivePowerB:
            return _build_time_series_results_table(self.shunt_q_B, self.time_array, self.sh_names, DeviceType.ShuntDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.ShuntReactivePowerC:
            return _build_time_series_results_table(self.shunt_q_C, self.time_array, self.sh_names, DeviceType.ShuntDevice, result_type.value, "(MVAr)", "(MVAr)")
        elif result_type == ResultTypes.ShuntNeutralVoltage:
            return _build_time_series_results_table(np.abs(self.shunt_Vn), self.time_array, self.sh_names, DeviceType.ShuntDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.LoadNeutralVoltage:
            return _build_time_series_results_table(np.abs(self.load_Vn), self.time_array, self.load_names, DeviceType.LoadDevice, result_type.value, "(p.u.)", "(p.u.)")
        elif result_type == ResultTypes.SimulationError:
            return _build_time_series_results_table(self.error_values.reshape(-1, 1), self.time_array, np.array(["Error"]), DeviceType.NoDevice, result_type.value, "(p.u.)", "(p.u.)")
        else:
            raise Exception("Result type not understood:" + str(result_type))
