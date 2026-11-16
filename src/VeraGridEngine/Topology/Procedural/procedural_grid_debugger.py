# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import List, Tuple

import numpy as np
import VeraGridEngine.Devices as dev


class ProceduralGridDebugger:
    """
    Helper class for plotting and validating intermediate results during
    procedural grid generation.

    This class should only contain debug/inspection utilities and must not
    modify the production objects.
    """
    __slots__ = ("enabled",)

    def __init__(self, enabled: bool = True):
        """
        :param enabled: Enable or disable debug actions
        """
        self.enabled = enabled


    def snapshot_grid_element_names(self, grid: dev.MultiCircuit) -> set[str]:
        """
        Take a snapshot of the current element names in the grid.

        :param grid: MultiCircuit instance
        :return: Set of element names currently present in the grid
        """
        names: set[str] = set()

        for bus in grid.buses:
            names.add(bus.name)

        for branch in grid.get_branches(add_vsc=True, add_hvdc=True, add_switch=True):
            names.add(branch.name)

        for load in grid.get_loads():
            names.add(load.name)

        for generator in grid.get_generators():
            names.add(generator.name)

        return names

    def get_added_element_names(
            self,
            grid: dev.MultiCircuit,
            previous_names: set[str],
    ) -> list[str]:
        """
        Return the names of the elements that were added to the grid
        after a previous snapshot.

        :param grid: MultiCircuit instance
        :param previous_names: Snapshot of names taken before modification
        :return: Sorted list of newly added element names
        """
        current_names = self.snapshot_grid_element_names(grid=grid)
        added_names = current_names - previous_names
        return sorted(added_names)