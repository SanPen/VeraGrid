# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.enumerations import FaultType
from VeraGridEngine.basic_structures import IntVec, Vec, StrVec, CxVec
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_basic_formulation_3ph import (expand_indices_3ph)


class ShortCircuitResults(ResultsTemplate):

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='bus_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='branch_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='sc_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='bus_types', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='F', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='T', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_F', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_T', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='bus_area_indices', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='area_names', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='Sbus1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='voltage1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Sf1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='St1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='If1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='It1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Vbranch1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='loading1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='losses1', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Sbus0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='voltage0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Sf0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='St0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='If0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='It0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Vbranch0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='loading0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='losses0', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Sbus2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='voltage2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Sf2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='St2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='If2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='It2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='Vbranch2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='loading2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='losses2', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SbusN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='voltageN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SfN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='StN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='IfN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='ItN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='VbranchN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='loadingN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='lossesN', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SbusA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='voltageA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SfA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='StA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='IfA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='ItA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='VbranchA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='loadingA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='lossesA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SbusB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='voltageB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SfB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='StB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='IfB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='ItB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='VbranchB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='loadingB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='lossesB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SbusC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='voltageC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SfC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='StC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='IfC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='ItC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='VbranchC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='loadingC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='lossesC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_losses', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_Pf', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_Pt', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='hvdc_loading', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_If', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_It', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_Pfp', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_Pfn', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_St', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_losses', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='vsc_loading', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='SCpower', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SCpowerA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SCpowerB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='SCpowerC', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='ICurrent', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='ICurrentA', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='ICurrentB', tpe=CxVec, old_names=list(), expandable=False),
        ResultsProperty(name='ICurrentC', tpe=CxVec, old_names=list(), expandable=False),
    )

    __slots__ = (
        "bus_types",
        "bus_names",
        "branch_names",
        "hvdc_names",
        "sc_names",
        "Sbus1",
        "voltage1",
        "Sf1",
        "St1",
        "If1",
        "It1",
        "Vbranch1",
        "loading1",
        "losses1",
        "Sbus0",
        "voltage0",
        "Sf0",
        "St0",
        "If0",
        "It0",
        "Vbranch0",
        "loading0",
        "losses0",
        "Sbus2",
        "voltage2",
        "Sf2",
        "St2",
        "If2",
        "It2",
        "Vbranch2",
        "loading2",
        "losses2",
        "SbusN",
        "voltageN",
        "SfN",
        "StN",
        "IfN",
        "ItN",
        "VbranchN",
        "loadingN",
        "lossesN",
        "SbusA",
        "voltageA",
        "SfA",
        "StA",
        "IfA",
        "ItA",
        "VbranchA",
        "loadingA",
        "lossesA",
        "SbusB",
        "voltageB",
        "SfB",
        "StB",
        "IfB",
        "ItB",
        "VbranchB",
        "loadingB",
        "lossesB",
        "SbusC",
        "voltageC",
        "SfC",
        "StC",
        "IfC",
        "ItC",
        "VbranchC",
        "loadingC",
        "lossesC",
        "hvdc_losses",
        "hvdc_Pf",
        "hvdc_Pt",
        "hvdc_loading",
        "vsc_If",
        "vsc_It",
        "vsc_Pfp",
        "vsc_Pfn",
        "vsc_St",
        "vsc_losses",
        "vsc_loading",
        "SCpower",
        "SCpowerA",
        "SCpowerB",
        "SCpowerC",
        "ICurrent",
        "ICurrentA",
        "ICurrentB",
        "ICurrentC",
    )

    def __init__(self,
                 nsc: int,
                 n: int,
                 m: int,
                 n_hvdc: int,
                 n_vsc: int,
                 sc_names: StrVec,
                 bus_names: StrVec,
                 branch_names: StrVec,
                 hvdc_names: StrVec,
                 vsc_names: StrVec,
                 bus_types: IntVec,
                 area_names: StrVec | None = None):
        """
        A **ShortCircuitResults** object is create as an attribute of the
        :ref:`ShortCircuitResults<pf_mp>` (as ShortCircuitResults.results) when the power flow is run. It
        provides access to the simulation results through its class attributes.
        :param n: number of nodes
        :param m: number of branches (without HVDC)
        :param n_hvdc: number of HVDC lines
        :param bus_names: array of bus names
        :param branch_names: array of branch names
        :param hvdc_names: array of HVDC names
        :param bus_types: array of bus types
        """

        ResultsTemplate.__init__(self,
                                 name='Short circuit',
                                 available_results={
                                     ResultTypes.BusResults: [ResultTypes.BusVoltageModule0,
                                                              ResultTypes.BusVoltageModule1,
                                                              ResultTypes.BusVoltageModule2,

                                                              ResultTypes.BusVoltageModuleA,
                                                              ResultTypes.BusVoltageModuleB,
                                                              ResultTypes.BusVoltageModuleC,

                                                              ResultTypes.BusVoltageAngle0,
                                                              ResultTypes.BusVoltageAngle1,
                                                              ResultTypes.BusVoltageAngle2,

                                                              ResultTypes.BusVoltageAngleA,
                                                              ResultTypes.BusVoltageAngleB,
                                                              ResultTypes.BusVoltageAngleC,

                                                              ResultTypes.BusShortCircuitActivePower,
                                                              ResultTypes.BusShortCircuitActivePowerA,
                                                              ResultTypes.BusShortCircuitActivePowerB,
                                                              ResultTypes.BusShortCircuitActivePowerC,

                                                              ResultTypes.BusShortCircuitReactivePower,
                                                              ResultTypes.BusShortCircuitReactivePowerA,
                                                              ResultTypes.BusShortCircuitReactivePowerB,
                                                              ResultTypes.BusShortCircuitReactivePowerC,

                                                              ResultTypes.BusShortCircuitActiveCurrent,
                                                              ResultTypes.BusShortCircuitActiveCurrentA,
                                                              ResultTypes.BusShortCircuitActiveCurrentB,
                                                              ResultTypes.BusShortCircuitActiveCurrentC,

                                                              ResultTypes.BusShortCircuitReactiveCurrent,
                                                              ResultTypes.BusShortCircuitReactiveCurrentA,
                                                              ResultTypes.BusShortCircuitReactiveCurrentB,
                                                              ResultTypes.BusShortCircuitReactiveCurrentC
                                                              ],

                                     ResultTypes.BranchResults: [ResultTypes.BranchActivePowerFrom0,
                                                                 ResultTypes.BranchActivePowerFrom1,
                                                                 ResultTypes.BranchActivePowerFrom2,

                                                                 ResultTypes.BranchActivePowerFromA,
                                                                 ResultTypes.BranchActivePowerFromB,
                                                                 ResultTypes.BranchActivePowerFromC,

                                                                 ResultTypes.BranchReactivePowerFrom0,
                                                                 ResultTypes.BranchReactivePowerFrom1,
                                                                 ResultTypes.BranchReactivePowerFrom2,

                                                                 ResultTypes.BranchReactivePowerFromA,
                                                                 ResultTypes.BranchReactivePowerFromB,
                                                                 ResultTypes.BranchReactivePowerFromC,

                                                                 ResultTypes.BranchActiveCurrentFrom0,
                                                                 ResultTypes.BranchActiveCurrentFrom1,
                                                                 ResultTypes.BranchActiveCurrentFrom2,

                                                                 ResultTypes.BranchActiveCurrentFromA,
                                                                 ResultTypes.BranchActiveCurrentFromB,
                                                                 ResultTypes.BranchActiveCurrentFromC,

                                                                 ResultTypes.BranchReactiveCurrentFrom0,
                                                                 ResultTypes.BranchReactiveCurrentFrom1,
                                                                 ResultTypes.BranchReactiveCurrentFrom2,

                                                                 ResultTypes.BranchReactiveCurrentFromA,
                                                                 ResultTypes.BranchReactiveCurrentFromB,
                                                                 ResultTypes.BranchReactiveCurrentFromC,

                                                                 ResultTypes.BranchLoading0,
                                                                 ResultTypes.BranchLoading1,
                                                                 ResultTypes.BranchLoading2,

                                                                 ResultTypes.BranchLoadingA,
                                                                 ResultTypes.BranchLoadingB,
                                                                 ResultTypes.BranchLoadingC,

                                                                 ResultTypes.BranchActiveLosses0,
                                                                 ResultTypes.BranchActiveLosses1,
                                                                 ResultTypes.BranchActiveLosses2,

                                                                 ResultTypes.BranchActiveLossesA,
                                                                 ResultTypes.BranchActiveLossesB,
                                                                 ResultTypes.BranchActiveLossesC,

                                                                 ResultTypes.BranchReactiveLosses0,
                                                                 ResultTypes.BranchReactiveLosses1,
                                                                 ResultTypes.BranchReactiveLosses2,

                                                                 ResultTypes.BranchReactiveLossesA,
                                                                 ResultTypes.BranchReactiveLossesB,
                                                                 ResultTypes.BranchReactiveLossesC],

                                     # ResultTypes.InfoResults: [ResultTypes.ShortCircuitInfo],
                                 },
                                 time_array=None,
                                 clustering_results=None,
                                 study_results_type=StudyResultsType.ShortCircuit
                                 )

        self.bus_types = bus_types
        self.bus_names = bus_names
        self.branch_names = branch_names
        self.hvdc_names = hvdc_names
        self.sc_names = sc_names

        # vars for the inter-area computation
        self.F = np.zeros(m, dtype=int)
        self.T = np.zeros(m, dtype=int)
        self.hvdc_F = np.zeros(n_hvdc, dtype=int)
        self.hvdc_T = np.zeros(n_hvdc, dtype=int)
        self.bus_area_indices = np.zeros(n, dtype=int)
        self.area_names = area_names

        self.Sbus1 = np.zeros((n, nsc), dtype=np.complex64)
        self.voltage1 = np.zeros((n, nsc), dtype=np.complex64)
        self.Sf1 = np.zeros((m, nsc), dtype=np.complex64)
        self.St1 = np.zeros((m, nsc), dtype=np.complex64)
        self.If1 = np.zeros((m, nsc), dtype=np.complex64)
        self.It1 = np.zeros((m, nsc), dtype=np.complex64)
        self.Vbranch1 = np.zeros((m, nsc), dtype=np.complex64)
        self.loading1 = np.zeros((m, nsc), dtype=np.complex64)
        self.losses1 = np.zeros((m, nsc), dtype=np.complex64)

        self.Sbus0 = np.zeros((n, nsc), dtype=np.complex64)
        self.voltage0 = np.zeros((n, nsc), dtype=np.complex64)
        self.Sf0 = np.zeros((m, nsc), dtype=np.complex64)
        self.St0 = np.zeros((m, nsc), dtype=np.complex64)
        self.If0 = np.zeros((m, nsc), dtype=np.complex64)
        self.It0 = np.zeros((m, nsc), dtype=np.complex64)
        self.Vbranch0 = np.zeros((m, nsc), dtype=np.complex64)
        self.loading0 = np.zeros((m, nsc), dtype=np.complex64)
        self.losses0 = np.zeros((m, nsc), dtype=np.complex64)

        self.Sbus2 = np.zeros((n, nsc), dtype=np.complex64)
        self.voltage2 = np.zeros((n, nsc), dtype=np.complex64)
        self.Sf2 = np.zeros((m, nsc), dtype=np.complex64)
        self.St2 = np.zeros((m, nsc), dtype=np.complex64)
        self.If2 = np.zeros((m, nsc), dtype=np.complex64)
        self.It2 = np.zeros((m, nsc), dtype=np.complex64)
        self.Vbranch2 = np.zeros((m, nsc), dtype=np.complex64)
        self.loading2 = np.zeros((m, nsc), dtype=np.complex64)
        self.losses2 = np.zeros((m, nsc), dtype=np.complex64)

        self.SbusN = np.zeros((n, nsc), dtype=np.complex64)
        self.voltageN = np.zeros((n, nsc), dtype=np.complex64)
        self.SfN = np.zeros((m, nsc), dtype=np.complex64)
        self.StN = np.zeros((m, nsc), dtype=np.complex64)
        self.IfN = np.zeros((m, nsc), dtype=np.complex64)
        self.ItN = np.zeros((m, nsc), dtype=np.complex64)
        self.VbranchN = np.zeros((m, nsc), dtype=np.complex64)
        self.loadingN = np.zeros((m, nsc), dtype=np.complex64)
        self.lossesN = np.zeros((m, nsc), dtype=np.complex64)

        self.SbusA = np.zeros((n, nsc), dtype=np.complex64)
        self.voltageA = np.zeros((n, nsc), dtype=np.complex64)
        self.SfA = np.zeros((m, nsc), dtype=np.complex64)
        self.StA = np.zeros((m, nsc), dtype=np.complex64)
        self.IfA = np.zeros((m, nsc), dtype=np.complex64)
        self.ItA = np.zeros((m, nsc), dtype=np.complex64)
        self.VbranchA = np.zeros((m, nsc), dtype=np.complex64)
        self.loadingA = np.zeros((m, nsc), dtype=np.complex64)
        self.lossesA = np.zeros((m, nsc), dtype=np.complex64)

        self.SbusB = np.zeros((n, nsc), dtype=np.complex64)
        self.voltageB = np.zeros((n, nsc), dtype=np.complex64)
        self.SfB = np.zeros((m, nsc), dtype=np.complex64)
        self.StB = np.zeros((m, nsc), dtype=np.complex64)
        self.IfB = np.zeros((m, nsc), dtype=np.complex64)
        self.ItB = np.zeros((m, nsc), dtype=np.complex64)
        self.VbranchB = np.zeros((m, nsc), dtype=np.complex64)
        self.loadingB = np.zeros((m, nsc), dtype=np.complex64)
        self.lossesB = np.zeros((m, nsc), dtype=np.complex64)

        self.SbusC = np.zeros((n, nsc), dtype=np.complex64)
        self.voltageC = np.zeros((n, nsc), dtype=np.complex64)
        self.SfC = np.zeros((m, nsc), dtype=np.complex64)
        self.StC = np.zeros((m, nsc), dtype=np.complex64)
        self.IfC = np.zeros((m, nsc), dtype=np.complex64)
        self.ItC = np.zeros((m, nsc), dtype=np.complex64)
        self.VbranchC = np.zeros((m, nsc), dtype=np.complex64)
        self.loadingC = np.zeros((m, nsc), dtype=np.complex64)
        self.lossesC = np.zeros((m, nsc), dtype=np.complex64)

        self.hvdc_losses = np.zeros((n_hvdc, nsc))
        self.hvdc_Pf = np.zeros((n_hvdc, nsc))
        self.hvdc_Pt = np.zeros((n_hvdc, nsc))
        self.hvdc_loading = np.zeros((n_hvdc, nsc))

        self.vsc_If = np.zeros((n_vsc, nsc))
        self.vsc_It = np.zeros((n_vsc, nsc), dtype=np.complex64)
        self.vsc_Pfp = np.zeros((n_vsc, nsc))
        self.vsc_Pfn = np.zeros((n_vsc, nsc))
        self.vsc_St = np.zeros((n_vsc, nsc), dtype=np.complex64)
        self.vsc_losses = np.zeros((n_vsc, nsc), dtype=float)
        self.vsc_loading = np.zeros((n_vsc, nsc), dtype=float)

        self.SCpower = np.zeros((n, nsc), dtype=np.complex64)
        self.SCpowerA = np.zeros((n, nsc), dtype=np.complex64)
        self.SCpowerB = np.zeros((n, nsc), dtype=np.complex64)
        self.SCpowerC = np.zeros((n, nsc), dtype=np.complex64)

        self.ICurrent = np.zeros((n, nsc), dtype=np.complex64)
        self.ICurrentA = np.zeros((n, nsc), dtype=np.complex64)
        self.ICurrentB = np.zeros((n, nsc), dtype=np.complex64)
        self.ICurrentC = np.zeros((n, nsc), dtype=np.complex64)

        # Register results


    @property
    def elapsed(self):
        """
        Check if converged in all modes
        :return: True / False
        """
        val = 0.0
        return val

    def apply_from_island(self, sc_idx: int, results: "ShortCircuitResults", b_idx: IntVec, br_idx: IntVec,
                          hvdc_idx: IntVec, vsc_idx: IntVec):
        """
        Apply results from another island circuit to the circuit results represented
        here.

        Arguments:

            **results**: PowerFlowResults

            **b_idx**: bus original indices

            **elm_idx**: branch original indices
        """
        self.SCpower[b_idx, sc_idx] = results.SCpower[:, 0]
        self.ICurrent[b_idx, sc_idx] = results.ICurrent[:, 0]

        self.Sbus1[b_idx, sc_idx] = results.Sbus1[:, 0]
        self.voltage1[b_idx, sc_idx] = results.voltage1[:, 0]
        self.Sf1[br_idx, sc_idx] = results.Sf1[:, 0]
        self.St1[br_idx, sc_idx] = results.St1[:, 0]
        self.If1[br_idx, sc_idx] = results.If1[:, 0]
        self.It1[br_idx, sc_idx] = results.It1[:, 0]
        self.Vbranch1[br_idx, sc_idx] = results.Vbranch1[:, 0]
        self.loading1[br_idx, sc_idx] = results.loading1[:, 0]
        self.losses1[br_idx, sc_idx] = results.losses1[:, 0]

        self.Sbus0[b_idx, sc_idx] = results.Sbus0[:, 0]
        self.voltage0[b_idx, sc_idx] = results.voltage0[:, 0]
        self.Sf0[br_idx, sc_idx] = results.Sf0[:, 0]
        self.St0[br_idx, sc_idx] = results.St0[:, 0]
        self.If0[br_idx, sc_idx] = results.If0[:, 0]
        self.It0[br_idx, sc_idx] = results.It0[:, 0]
        self.Vbranch0[br_idx, sc_idx] = results.Vbranch0[:, 0]
        self.loading0[br_idx, sc_idx] = results.loading0[:, 0]
        self.losses0[br_idx, sc_idx] = results.losses0[:, 0]

        self.Sbus2[b_idx, sc_idx] = results.Sbus2[:, 0]
        self.voltage2[b_idx, sc_idx] = results.voltage2[:, 0]
        self.Sf2[br_idx, sc_idx] = results.Sf2[:, 0]
        self.St2[br_idx, sc_idx] = results.St2[:, 0]
        self.If2[br_idx, sc_idx] = results.If2[:, 0]
        self.It2[br_idx, sc_idx] = results.It2[:, 0]
        self.Vbranch2[br_idx, sc_idx] = results.Vbranch2[:, 0]
        self.loading2[br_idx, sc_idx] = results.loading2[:, 0]
        self.losses2[br_idx, sc_idx] = results.losses2[:, 0]

        self.SbusN[b_idx, sc_idx] = results.SbusN[:, 0]
        self.voltageN[b_idx, sc_idx] = results.voltageN[:, 0]
        self.SfN[br_idx, sc_idx] = results.SfN[:, 0]
        self.StN[br_idx, sc_idx] = results.StN[:, 0]
        self.IfN[br_idx, sc_idx] = results.IfN[:, 0]
        self.ItN[br_idx, sc_idx] = results.ItN[:, 0]
        self.VbranchN[br_idx, sc_idx] = results.VbranchN[:, 0]
        self.loadingN[br_idx, sc_idx] = results.loadingN[:, 0]
        self.lossesN[br_idx, sc_idx] = results.lossesN[:, 0]

        self.SbusA[b_idx, sc_idx] = results.SbusA[:, 0]
        self.voltageA[b_idx, sc_idx] = results.voltageA[:, 0]
        self.SfA[br_idx, sc_idx] = results.SfA[:, 0]
        self.StA[br_idx, sc_idx] = results.StA[:, 0]
        self.IfA[br_idx, sc_idx] = results.IfA[:, 0]
        self.ItA[br_idx, sc_idx] = results.ItA[:, 0]
        self.VbranchA[br_idx, sc_idx] = results.VbranchA[:, 0]
        self.loadingA[br_idx, sc_idx] = results.loadingA[:, 0]
        self.lossesA[br_idx, sc_idx] = results.lossesA[:, 0]

        self.SbusB[b_idx, sc_idx] = results.SbusB[:, 0]
        self.voltageB[b_idx, sc_idx] = results.voltageB[:, 0]
        self.SfB[br_idx, sc_idx] = results.SfB[:, 0]
        self.StB[br_idx, sc_idx] = results.StB[:, 0]
        self.IfB[br_idx, sc_idx] = results.IfB[:, 0]
        self.ItB[br_idx, sc_idx] = results.ItB[:, 0]
        self.VbranchB[br_idx, sc_idx] = results.VbranchB[:, 0]
        self.loadingB[br_idx, sc_idx] = results.loadingB[:, 0]
        self.lossesB[br_idx, sc_idx] = results.lossesB[:, 0]

        self.SbusC[b_idx, sc_idx] = results.SbusC[:, 0]
        self.voltageC[b_idx, sc_idx] = results.voltageC[:, 0]
        self.SfC[br_idx, sc_idx] = results.SfC[:, 0]
        self.StC[br_idx, sc_idx] = results.StC[:, 0]
        self.IfC[br_idx, sc_idx] = results.IfC[:, 0]
        self.ItC[br_idx, sc_idx] = results.ItC[:, 0]
        self.VbranchC[br_idx, sc_idx] = results.VbranchC[:, 0]
        self.loadingC[br_idx, sc_idx] = results.loadingC[:, 0]
        self.lossesC[br_idx, sc_idx] = results.lossesC[:, 0]

        self.hvdc_losses[hvdc_idx, sc_idx] = results.hvdc_losses[:, 0]
        self.hvdc_Pf[hvdc_idx, sc_idx] = results.hvdc_Pf[:, 0]
        self.hvdc_Pt[hvdc_idx, sc_idx] = results.hvdc_Pt[:, 0]
        self.hvdc_loading[hvdc_idx, sc_idx] = results.hvdc_loading[:, 0]

        self.vsc_If[vsc_idx, sc_idx] = results.vsc_If[:, 0]
        self.vsc_It[vsc_idx, sc_idx] = results.vsc_It[:, 0]
        self.vsc_Pfp[vsc_idx, sc_idx] = results.vsc_Pfp[:, 0]
        self.vsc_Pfn[vsc_idx, sc_idx] = results.vsc_Pfn[:, 0]
        self.vsc_St[vsc_idx, sc_idx] = results.vsc_St[:, 0]
        self.vsc_losses[vsc_idx, sc_idx] = results.vsc_losses[:, 0]
        self.vsc_loading[vsc_idx, sc_idx] = results.vsc_loading[:, 0]

    def mdl(self, result_type: ResultTypes) -> ResultsTable:
        """

        :param result_type:
        :return:
        """

        # columns = np.array([result_type.value])
        title = result_type.value

        if result_type == ResultTypes.BusShortCircuitActivePower:
            labels = self.bus_names
            y = np.real(self.SCpower)
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitActivePowerA:
            labels = self.bus_names
            y = np.real(self.SCpowerA)
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitActivePowerB:
            labels = self.bus_names
            y = np.real(self.SCpowerB)
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitActivePowerC:
            labels = self.bus_names
            y = np.real(self.SCpowerC)
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitReactivePower:
            labels = self.bus_names
            y = np.imag(self.SCpower)
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitReactivePowerA:
            labels = self.bus_names
            y = np.imag(self.SCpowerA)
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitReactivePowerB:
            labels = self.bus_names
            y = np.imag(self.SCpowerB)
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitReactivePowerC:
            labels = self.bus_names
            y = np.imag(self.SCpowerC)
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitActiveCurrent:
            labels = self.bus_names
            y = np.real(self.ICurrent)
            y_label = '(kA)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitActiveCurrentA:
            labels = self.bus_names
            y = np.real(self.ICurrentA)
            y_label = '(kA)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitActiveCurrentB:
            labels = self.bus_names
            y = np.real(self.ICurrentB)
            y_label = '(kA)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitActiveCurrentC:
            labels = self.bus_names
            y = np.real(self.ICurrentC)
            y_label = '(kA)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitReactiveCurrent:
            labels = self.bus_names
            y = np.imag(self.ICurrent)
            y_label = '(kAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitReactiveCurrentA:
            labels = self.bus_names
            y = np.imag(self.ICurrentA)
            y_label = '(kAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitReactiveCurrentB:
            labels = self.bus_names
            y = np.imag(self.ICurrentB)
            y_label = '(kAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusShortCircuitReactiveCurrentC:
            labels = self.bus_names
            y = np.imag(self.ICurrentC)
            y_label = '(kAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageModule0:
            labels = self.bus_names
            y = np.abs(self.voltage0)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageAngle0:
            labels = self.bus_names
            y = np.angle(self.voltage0)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActivePowerFrom0:
            labels = self.branch_names
            y = self.Sf0.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactivePowerFrom0:
            labels = self.branch_names
            y = self.Sf0.imag
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveCurrentFrom0:
            labels = self.branch_names
            y = self.If0.real
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveCurrentFrom0:
            labels = self.branch_names
            y = self.If0.imag
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchLoading0:
            labels = self.branch_names
            y = self.loading0.real * 100.0
            y_label = '(%)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveLosses0:
            labels = self.branch_names
            y = self.losses0.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveLosses0:
            labels = self.branch_names
            y = self.losses0.imag
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageModule1:
            labels = self.bus_names
            y = np.abs(self.voltage1)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageAngle1:
            labels = self.bus_names
            y = np.angle(self.voltage1)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActivePowerFrom1:
            labels = self.branch_names
            y = self.Sf1.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactivePowerFrom1:
            labels = self.branch_names
            y = self.Sf1.imag
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveCurrentFrom1:
            labels = self.branch_names
            y = self.If1.real
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveCurrentFrom1:
            labels = self.branch_names
            y = self.If1.imag
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchLoading1:
            labels = self.branch_names
            y = self.loading1.real * 100.0
            y_label = '(%)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveLosses1:
            labels = self.branch_names
            y = self.losses1.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveLosses1:
            labels = self.branch_names
            y = self.losses1.imag
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageModule2:
            labels = self.bus_names
            y = np.abs(self.voltage2)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageAngle2:
            labels = self.bus_names
            y = np.angle(self.voltage2)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActivePowerFrom2:
            labels = self.branch_names
            y = self.Sf2.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactivePowerFrom2:
            labels = self.branch_names
            y = self.Sf2.imag
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveCurrentFrom2:
            labels = self.branch_names
            y = self.If2.real
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveCurrentFrom2:
            labels = self.branch_names
            y = self.If2.imag
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchLoading2:
            labels = self.branch_names
            y = self.loading2.real * 100.0
            y_label = '(%)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveLosses2:
            labels = self.branch_names
            y = self.losses2.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveLosses2:
            labels = self.branch_names
            y = self.losses2.imag
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageModuleA:
            labels = self.bus_names
            y = np.abs(self.voltageA)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageAngleA:
            labels = self.bus_names
            y = np.angle(self.voltageA)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActivePowerFromA:
            labels = self.branch_names
            y = self.SfA.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactivePowerFromA:
            labels = self.branch_names
            y = self.SfA.imag
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveCurrentFromA:
            labels = self.branch_names
            y = self.IfA.real
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveCurrentFromA:
            labels = self.branch_names
            y = self.IfA.imag
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchLoadingA:
            labels = self.branch_names
            y = self.loadingA.real * 100.0
            y_label = '(%)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveLossesA:
            labels = self.branch_names
            y = self.lossesA.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveLossesA:
            labels = self.branch_names
            y = self.lossesA.imag
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageModuleB:
            labels = self.bus_names
            y = np.abs(self.voltageB)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageAngleB:
            labels = self.bus_names
            y = np.angle(self.voltageB)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActivePowerFromB:
            labels = self.branch_names
            y = self.SfB.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactivePowerFromB:
            labels = self.branch_names
            y = self.SfB.imag
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveCurrentFromB:
            labels = self.branch_names
            y = self.IfB.real
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveCurrentFromB:
            labels = self.branch_names
            y = self.IfB.imag
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchLoadingB:
            labels = self.branch_names
            y = self.loadingB.real * 100.0
            y_label = '(%)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveLossesB:
            labels = self.branch_names
            y = self.lossesB.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveLossesB:
            labels = self.branch_names
            y = self.lossesB.imag
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageModuleC:
            labels = self.bus_names
            y = np.abs(self.voltageC)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BusVoltageAngleC:
            labels = self.bus_names
            y = np.angle(self.voltageC)
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BusDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActivePowerFromC:
            labels = self.branch_names
            y = self.SfC.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactivePowerFromC:
            labels = self.branch_names
            y = self.SfC.imag
            y_label = '(MVAr)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveCurrentFromC:
            labels = self.branch_names
            y = self.IfC.real
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveCurrentFromC:
            labels = self.branch_names
            y = self.IfC.imag
            y_label = '(p.u.)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchLoadingC:
            labels = self.branch_names
            y = self.loadingC.real * 100.0
            y_label = '(%)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchActiveLossesC:
            labels = self.branch_names
            y = self.lossesC.real
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        elif result_type == ResultTypes.BranchReactiveLossesC:
            labels = self.branch_names
            y = self.lossesC.imag
            y_label = '(MW)'

            return ResultsTable(data=y,
                                index=labels,
                                idx_device_type=DeviceType.BranchDevice,
                                columns=self.sc_names,
                                cols_device_type=DeviceType.NoDevice,
                                title=title,
                                ylabel=y_label,
                                units=y_label)

        # elif result_type == ResultTypes.ShortCircuitInfo:
        #     labels = np.array(['Type', 'Bus name'])
        #     y = np.array([self.sc_type.value, self.bus_names[self.sc_bus_index]])
        #     y_label = ''
        #
        #     return ResultsTable(data=y,
        #                         index=labels,
        #                         idx_device_type=DeviceType.BusDevice,
        #                         columns=self.sc_names,
        #                         cols_device_type=DeviceType.NoDevice,
        #                         title=title,
        #                         ylabel=y_label,
        #                         units=y_label)

        else:
            raise Exception('Unsupported result type: ' + str(result_type))

    def get_voltage_df(self, sc_idx=0) -> pd.DataFrame:
        """

        :param sc_idx:
        :return:
        """

        return pd.DataFrame(data={'Um 0 [p.u.]': np.abs(self.voltage0[:, sc_idx]),
                                  'Ua 0 [º]': np.angle(self.voltage0[:, sc_idx], deg=True),
                                  'Um 1 [p.u.]': np.abs(self.voltage1[:, sc_idx]),
                                  'Ua 1 [º]': np.angle(self.voltage1[:, sc_idx], deg=True),
                                  'Um 2 [p.u.]': np.abs(self.voltage2[:, sc_idx]),
                                  'Ua 2 [º]': np.angle(self.voltage2[:, sc_idx], deg=True)},
                            index=self.bus_names)

    def get_current_df(self, sc_idx=0) -> pd.DataFrame:
        """

        :param sc_idx:
        :return:
        """

        return pd.DataFrame(data={'Im 0 [p.u.]': np.abs(self.If0[:, sc_idx]),
                                  'Ia 0 [º]': np.angle(self.If0[:, sc_idx], deg=True),
                                  'Im 1 [p.u.]': np.abs(self.If1[:, sc_idx]),
                                  'Ia 1 [º]': np.angle(self.If1[:, sc_idx], deg=True),
                                  'Im 2 [p.u.]': np.abs(self.If2[:, sc_idx]),
                                  'Ia 2 [º]': np.angle(self.If2[:, sc_idx], deg=True)},
                            index=self.branch_names)

    def get_voltage_3ph_df(self, sc_idx: int = 0) -> pd.DataFrame:
        """

        :param sc_idx:
        :return:
        """
        return pd.DataFrame(data={'Um A [p.u.]': np.abs(self.voltageA[:, sc_idx]).round(5),
                                  'Ua A [º]': np.angle(self.voltageA[:, sc_idx], deg=True).round(1),
                                  'Um B [p.u.]': np.abs(self.voltageB[:, sc_idx]).round(5),
                                  'Ua B [º]': np.angle(self.voltageB[:, sc_idx], deg=True).round(1),
                                  'Um C [p.u.]': np.abs(self.voltageC[:, sc_idx]).round(5),
                                  'Ua C [º]': np.angle(self.voltageC[:, sc_idx], deg=True).round(1)},
                            index=self.bus_names)

    def export_all(self):
        """
        Exports all the results to DataFrames.

        Returns:

            Bus results, Branch reuslts
        """

        # buses results
        vm = np.abs(self.voltage1)
        va = np.angle(self.voltage1)
        vr = self.voltage1.real
        vi = self.voltage1.imag
        bus_data = np.c_[vr, vi, vm, va]
        bus_cols = ['Real voltage (p.u.)',
                    'Imag Voltage (p.u.)',
                    'Voltage module (p.u.)',
                    'Voltage angle (rad)']
        df_bus = pd.DataFrame(data=bus_data, columns=bus_cols)

        # branch results
        sr = self.Sf1.real
        si = self.Sf1.imag
        sm = np.abs(self.Sf1)
        ld = np.abs(self.loading1)
        la = self.losses1.real
        lr = self.losses1.imag
        ls = np.abs(self.losses1)

        branch_data = np.c_[sr, si, sm, ld, la, lr, ls]
        branch_cols = ['Real power (MW)',
                       'Imag power (MVAr)',
                       'Power module (MVA)',
                       'Loading(%)',
                       'Losses (MW)',
                       'Losses (MVAr)',
                       'Losses (MVA)']
        df_branch = pd.DataFrame(data=branch_data, columns=branch_cols)

        return df_bus, df_branch
