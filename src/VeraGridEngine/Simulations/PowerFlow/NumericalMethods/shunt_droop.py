# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from scipy.sparse import csc_matrix

from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Topology.topology import find_islands
from VeraGridEngine.basic_structures import CxVec, IntVec, Vec
from VeraGridEngine.enumerations import ShuntControlMode
from VeraGridEngine.Utils.Sparse.csc2 import CSC, scipy_to_mat


class ShuntDroop:
    """Q-V droop shunts: Q = Qdroop * (Vset - |Vc|), kept within [Bmin, Bmax] * |V|^2 at the shunt bus."""

    __slots__ = ('idx', 'bus_idx', 'control_bus_idx', 'slope', 'vset', 'bmin', 'bmax', 'nbus')

    def __init__(self, nc: NumericalCircuit) -> None:
        """Select the active ShuntControlMode.QVDroop shunts of a compiled circuit.

        :param nc: Compiled circuit
        """
        self.idx: IntVec = np.flatnonzero(
            nc.shunt_data.active.astype(bool)
            & (nc.shunt_data.control_mode_int == ShuntControlMode.QVDroop.idx())
            & (nc.shunt_data.q_droop_snom == 0.0)
        )
        self.bus_idx: IntVec = nc.shunt_data.bus_idx[self.idx]
        control: IntVec = nc.shunt_data.controllable_bus_idx[self.idx]
        if len(self.idx) > 0:
            # A control bus outside the shunt island, as the complete-support power flow splits it, leaves the shunt
            # on its own bus, so a full circuit and its island slices give the same law
            island_of_bus: IntVec = np.full(nc.nbus, -1, dtype=int)
            island_buses: IntVec
            for label, island_buses in enumerate(find_islands(
                    adj=nc.compute_adjacency_matrix(consider_hvdc_as_island_links=True), active=nc.bus_data.active)):
                island_of_bus[island_buses] = label
            own_island: IntVec = island_of_bus[self.bus_idx]
            same_island: np.ndarray = ((control > -1) & (own_island > -1)
                                       & (island_of_bus[np.maximum(control, 0)] == own_island))
            self.control_bus_idx: IntVec = np.where(same_island, control, self.bus_idx)
        else:
            self.control_bus_idx = self.bus_idx.copy()
        self.slope: Vec = nc.shunt_data.q_droop[self.idx] / nc.Sbase
        self.vset: Vec = nc.shunt_data.vset[self.idx]
        self.bmin: Vec = nc.shunt_data.qmin[self.idx] / nc.Sbase
        self.bmax: Vec = nc.shunt_data.qmax[self.idx] / nc.Sbase
        self.nbus: int = nc.nbus

    def q_and_limits(self, squared_voltage: Vec, control_magnitude: Vec) -> tuple[Vec, np.ndarray]:
        """Evaluate the common shunt law and identify active susceptance limits.

        :param squared_voltage: Squared effective voltage across each shunt.
        :param control_magnitude: Voltage magnitude measured by each controller.
        :return: Injected reactive power and whether a susceptance limit is active.
        """
        requested: Vec = self.slope * (self.vset - control_magnitude)
        lower: Vec = self.bmin * squared_voltage
        upper: Vec = self.bmax * squared_voltage
        return np.clip(requested, lower, upper), (requested < lower) | (requested > upper)

    def q(self, voltage: CxVec) -> Vec:
        """Injected reactive power of each shunt.

        :param voltage: Bus voltages in p.u.
        :return: Injected Q per shunt, system p.u.
        """
        vm: Vec = np.abs(voltage[self.bus_idx])
        vc: Vec = np.abs(voltage[self.control_bus_idx])
        values, _ = self.q_and_limits(vm * vm, vc)
        return values

    def delta_q_bus(self, voltage: CxVec) -> Vec:
        """Injected reactive power per bus; these shunts add nothing to the compiled admittances.

        :param voltage: Bus voltages in p.u.
        :return: Injected Q per bus, system p.u.
        """
        result: Vec = np.zeros(self.nbus)
        np.add.at(result, self.bus_idx, self.q(voltage))
        return result

    def dq_dvm(self, voltage: CxVec) -> CSC:
        """Derivative of the injected Q per bus with respect to the bus voltage modules.

        Inside the band Q follows the control voltage; on a limit it follows B * |V|^2 at the shunt bus.

        :param voltage: Bus voltages in p.u.
        :return: nbus x nbus matrix, rows are the injecting buses and columns the voltage modules
        """
        vm: Vec = np.abs(voltage[self.bus_idx])
        vc: Vec = np.abs(voltage[self.control_bus_idx])
        droop: Vec = self.slope * (self.vset - vc)
        high: Vec = self.bmax * vm * vm
        low: Vec = self.bmin * vm * vm
        cols: IntVec = np.where((droop > high) | (droop < low), self.bus_idx, self.control_bus_idx)
        values: Vec = np.where(droop > high, 2.0 * self.bmax * vm,
                               np.where(droop < low, 2.0 * self.bmin * vm, -self.slope))
        return scipy_to_mat(csc_matrix((values, (self.bus_idx, cols)), shape=(self.nbus, self.nbus)))
