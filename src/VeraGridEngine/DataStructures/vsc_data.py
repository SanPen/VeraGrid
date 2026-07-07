# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
from VeraGridEngine.DataStructures.branch_parent_data import BranchParentData
from VeraGridEngine.basic_structures import Vec, IntVec, Logger


class VscData(BranchParentData):
    """
    VscData class provides a structured model for managing data related to
    Voltage Source Converters (VSC) in power grid simulations.
    """

    def __init__(self, nelm: int, nbus: int):
        """
        Branch data arrays
        :param nelm: number of elements
        :param nbus: number of buses
        """
        BranchParentData.__init__(self, nelm=nelm, nbus=nbus)

        self.F_dcn = np.zeros(self.nelm, dtype=int)

        self.alpha1: Vec = np.zeros(self.nelm, dtype=float)  # converter losses parameter (alpha1) (idle loss)
        self.alpha2: Vec = np.zeros(self.nelm, dtype=float)  # converter losses parameter (alpha2) (switching loss)
        self.alpha3: Vec = np.zeros(self.nelm, dtype=float)  # converter losses parameter (alpha3) (resistive loss)

        self.control1_int: IntVec = np.zeros(self.nelm, dtype=int)  # Values from ConverterControlType
        self.control2_int: IntVec = np.zeros(self.nelm, dtype=int)  # Values from ConverterControlType
        self.fault_control_int: IntVec = np.zeros(self.nelm, dtype=int)  # Values from ConverterControlType

        self.control1_val: Vec = np.ones(self.nelm, dtype=float)
        self.control2_val: Vec = np.ones(self.nelm, dtype=float)
        self.control1_val_min: Vec = np.zeros(self.nelm, dtype=float)
        self.control1_val_max: Vec = np.full(self.nelm, 9999.0, dtype=float)
        self.control1_val_droop: Vec = np.full(self.nelm, 0.1, dtype=float)
        self.control1_droop_val: Vec = np.ones(self.nelm, dtype=float)
        self.control1_droop_val_min: Vec = np.full(self.nelm, 0.9, dtype=float)
        self.control1_droop_val_max: Vec = np.full(self.nelm, 1.1, dtype=float)

        self.control2_val_min: Vec = np.zeros(self.nelm, dtype=float)
        self.control2_val_max: Vec = np.full(self.nelm, 9999.0, dtype=float)
        self.control2_val_droop: Vec = np.full(self.nelm, 0.1, dtype=float)
        self.control2_droop_val: Vec = np.ones(self.nelm, dtype=float)
        self.control2_droop_val_min: Vec = np.full(self.nelm, 0.9, dtype=float)
        self.control2_droop_val_max: Vec = np.full(self.nelm, 1.1, dtype=float)

        self.control1_bus_idx: IntVec = np.full(nelm, -1, dtype=int)
        self.control2_bus_idx: IntVec = np.full(nelm, -1, dtype=int)
        self.control1_branch_idx: IntVec = np.full(nelm, -1, dtype=int)
        self.control2_branch_idx: IntVec = np.full(nelm, -1, dtype=int)

        self.min_ac_voltage: Vec = np.full(self.nelm, 0.1, dtype=float)

        self.ysvs: Vec = np.full(self.nelm, 0.0, dtype=float)

    def slice(self, elm_idx: IntVec, bus_idx: IntVec, bus_map: IntVec, logger: Logger | None) -> "VscData":
        """
        Slice branch data by given indices
        :param elm_idx: array of branch indices
        :param bus_idx: array of bus indices
        :param bus_map: map from bus index to branch index
        :param logger: Logger
        :return: new BranchData instance
        """

        data, bus_map = super().slice(elm_idx, bus_idx, bus_map, logger)
        data: VscData = data
        data.__class__ = VscData

        # data.F_dcp = self.F_dcp[elm_idx]
        data.F_dcn = self.F_dcn[elm_idx]
        # data.T_ac = self.T_ac[elm_idx]

        data.alpha1 = self.alpha1[elm_idx]
        data.alpha2 = self.alpha2[elm_idx]
        data.alpha3 = self.alpha3[elm_idx]

        data.control1_int = self.control1_int[elm_idx]
        data.control2_int = self.control2_int[elm_idx]
        data.fault_control_int = self.fault_control_int[elm_idx]

        data.control1_val = self.control1_val[elm_idx]
        data.control2_val = self.control2_val[elm_idx]
        data.control1_val_min = self.control1_val_min[elm_idx]
        data.control1_val_max = self.control1_val_max[elm_idx]
        data.control1_val_droop = self.control1_val_droop[elm_idx]
        data.control1_droop_val = self.control1_droop_val[elm_idx]
        data.control1_droop_val_min = self.control1_droop_val_min[elm_idx]
        data.control1_droop_val_max = self.control1_droop_val_max[elm_idx]

        data.control2_val_min = self.control2_val_min[elm_idx]
        data.control2_val_max = self.control2_val_max[elm_idx]
        data.control2_val_droop = self.control2_val_droop[elm_idx]
        data.control2_droop_val = self.control2_droop_val[elm_idx]
        data.control2_droop_val_min = self.control2_droop_val_min[elm_idx]
        data.control2_droop_val_max = self.control2_droop_val_max[elm_idx]

        data.control1_bus_idx = self.control1_bus_idx[elm_idx]
        data.control2_bus_idx = self.control2_bus_idx[elm_idx]

        # TODO: think about how to re-map this stuff
        data.control1_branch_idx = self.control1_branch_idx[elm_idx]
        data.control2_branch_idx = self.control2_branch_idx[elm_idx]

        data.min_ac_voltage = self.min_ac_voltage[elm_idx]

        data.ysvs = self.ysvs[elm_idx]

        for k in range(data.nelm):
            if data.control1_bus_idx[k] > -1:
                data.control1_bus_idx[k] = bus_map[data.control1_bus_idx[k]]

                if data.control1_bus_idx[k] == -1:
                    if logger is not None:
                        logger.add_error(f"Branch {k}, {self.names[k]} control1 bus is unreachable",
                                         value=data.control1_bus_idx[k])

            if data.control2_bus_idx[k] > -1:
                data.control2_bus_idx[k] = bus_map[data.control2_bus_idx[k]]

                if data.control2_bus_idx[k] == -1:
                    if logger is not None:
                        logger.add_error(f"Branch {k}, {self.names[k]} control2 bus is unreachable",
                                         value=data.control2_bus_idx[k])

        return data

    def copy(self) -> "VscData":
        """
        Get a deep copy of this object
        :return: new BranchData instance
        """
        data: VscData = super().copy()
        data.__class__ = VscData

        data.F_dcn = self.F_dcn.copy()

        data.dc = self.dc.copy()
        data.alpha1 = self.alpha1.copy()
        data.alpha2 = self.alpha2.copy()
        data.alpha3 = self.alpha3.copy()

        data.control1_int = self.control1_int.copy()
        data.control2_int = self.control2_int.copy()
        data.fault_control_int = self.fault_control_int.copy()

        data.control1_val = self.control1_val.copy()
        data.control2_val = self.control2_val.copy()
        data.control1_val_min = self.control1_val_min.copy()
        data.control1_val_max = self.control1_val_max.copy()
        data.control1_val_droop = self.control1_val_droop.copy()
        data.control1_droop_val = self.control1_droop_val.copy()
        data.control1_droop_val_min = self.control1_droop_val_min.copy()
        data.control1_droop_val_max = self.control1_droop_val_max.copy()
        data.control2_val_min = self.control2_val_min.copy()
        data.control2_val_max = self.control2_val_max.copy()
        data.control2_val_droop = self.control2_val_droop.copy()
        data.control2_droop_val = self.control2_droop_val.copy()
        data.control2_droop_val_min = self.control2_droop_val_min.copy()
        data.control2_droop_val_max = self.control2_droop_val_max.copy()

        data.control1_bus_idx = self.control1_bus_idx.copy()
        data.control2_bus_idx = self.control2_bus_idx.copy()
        data.control1_branch_idx = self.control1_branch_idx.copy()
        data.control2_branch_idx = self.control2_branch_idx.copy()

        data.min_ac_voltage = self.min_ac_voltage.copy()

        data.ysvs = self.ysvs.copy()

        return data

    def __len__(self) -> int:
        """
        Get vsc count
        :return:
        """
        return self.nelm
