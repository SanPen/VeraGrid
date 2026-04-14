# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING

import numpy as np
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.types import BRANCH_TYPES
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.basic_structures import Mat

if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class ProceduralGrid:
    """
    Class to chracterize and create grids procedurally
    """
    __slots__ = (
        "states",
        "state_index",
        "transition_probabilities",
    )

    def __init__(self):
        # list of states, ony buses and branches for now
        self.states: List[DeviceType] = [
            DeviceType.BusDevice,
            DeviceType.LineDevice,
            DeviceType.DCLineDevice,
            DeviceType.Transformer2WDevice,
            DeviceType.SeriesReactanceDevice,
            DeviceType.HVDCLineDevice,
            DeviceType.VscDevice,
            DeviceType.SwitchDevice,
            # DeviceType.LoadDevice,
            # DeviceType.GeneratorDevice,
            # DeviceType.ShuntDevice,
        ]

        ns = len(self.states)

        self.state_index: Dict[DeviceType, int] = {s: i for i, s in enumerate(self.states)}

        # Transition probabilities: row-> state I'm at | col -> state I will be
        self.transition_probabilities: Mat = np.zeros((ns, ns))

    def train(self, grid: MultiCircuit):
        """
        Fill the transition probabilities with the grid information
        :param grid:
        :return:
        """

        ns = len(self.states)

        # at the beginning, these will be the simple frequency counts
        self.transition_probabilities = np.zeros((ns, ns))

        # get dictionary of branches connected to each bus
        d: Dict[dev.Bus, List[BRANCH_TYPES]] = grid.get_bus_branch_dict()

        pool = [grid.buses[0]]
        used_buses = set()

        while len(pool) > 0:

            # get the firts out of the cue
            bus = pool.pop(0)

            # get the device index
            row = self.state_index[bus.device_type]

            # add the popeddevice to the used buses
            used_buses.add(bus)

            # get the list of branches of the bus
            br_list = d.get(bus, list())

            # for every connected brnach...
            for branch in br_list:

                if branch.bus_from not in used_buses:
                    pool.append(branch.bus_from)

                if branch.bus_to not in used_buses:
                    pool.append(branch.bus_to)

                # get the device type column in the states matrix
                col = self.state_index[branch.device_type]

                # increase the frequency
                self.transition_probabilities[row, col] += 1
                self.transition_probabilities[col, row] += 1

        # normalize
        for i in len(self.states):
            s = np.sum(self.transition_probabilities[i, :])
            self.transition_probabilities[i, :] /= s


if __name__ == '__main__':

    pass
