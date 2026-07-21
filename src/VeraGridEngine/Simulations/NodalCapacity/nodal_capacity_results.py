# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
import numpy as np
from typing import Union
from VeraGridEngine.basic_structures import IntVec, Vec
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsProperty
from VeraGridEngine.Simulations.OPF.opf_results import OptimalPowerFlowResults
from VeraGridEngine.enumerations import ResultTypes, DeviceType


class NodalCapacityResults(OptimalPowerFlowResults):
    """
    Snapshot nodal capacity results
    """

    LOCAL_RESULTS_DECLARATIONS = OptimalPowerFlowResults.LOCAL_RESULTS_DECLARATIONS + (
        ResultsProperty(name='capacity_nodes_idx', tpe=IntVec, old_names=list(), expandable=False),
        ResultsProperty(name='nodal_capacity', tpe=Vec, old_names=list(), expandable=False),
    )

    __slots__ = (
        "capacity_nodes_idx",
        "nodal_capacity",
    )

    def __init__(self,
                 capacity_nodes_idx: Union[None, IntVec] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.capacity_nodes_idx = capacity_nodes_idx if capacity_nodes_idx is not None else np.zeros(0, dtype=int)
        self.nodal_capacity = np.zeros(len(self.capacity_nodes_idx), dtype=float)
        self.available_results[ResultTypes.BusResults].append(ResultTypes.BusNodalCapacity)

    def mdl(self, result_type) -> ResultsTable:
        if result_type == ResultTypes.BusNodalCapacity:
            return ResultsTable(data=self.nodal_capacity,
                                index=self.bus_names[self.capacity_nodes_idx],
                                idx_device_type=DeviceType.BusDevice,
                                columns=[result_type.value],
                                cols_device_type=DeviceType.NoDevice,
                                title=str(result_type.value),
                                ylabel='(MW)',
                                xlabel='',
                                units='(MW)')
        return super().mdl(result_type=result_type)
