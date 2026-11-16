# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from scipy.sparse import csc_matrix

from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.DataStructures.generator_data import GeneratorData
from VeraGridEngine.basic_structures import CxVec, IntVec, Vec
from VeraGridEngine.enumerations import GeneratorControlMode, BusMode, ShuntControlMode
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import voltage_q_droop, generator_qv_droop
from VeraGridEngine.Utils.Sparse.csc2 import CSC, scipy_to_mat


class StaticGeneratorDroop:
    """Evaluate existing Q-V laws for static/synchronous generators and shunts."""

    __slots__ = ('idx', 'shunt_idx', 'generator_idx', 'generator_data', 'bus_idx', 'reference',
                 'snom', 'droop', 'vset', 'vmin', 'vmax', 'sbase', 'nbus')

    def __init__(self, nc: NumericalCircuit) -> None:
        """Select active droop devices without changing their fixed P/Q reference.

        :param nc: Compiled circuit with static generators in load data.
        """
        self.idx: IntVec = np.flatnonzero(nc.load_data.active & (nc.load_data.q_droop > 0.0))
        self.bus_idx: IntVec = nc.load_data.bus_idx[self.idx]
        self.reference: CxVec = -nc.load_data.S[self.idx] / nc.Sbase
        self.snom: Vec = nc.load_data.q_droop_snom[self.idx]
        self.droop: Vec = nc.load_data.q_droop[self.idx]
        self.vset: Vec = nc.load_data.q_droop_vset[self.idx]
        self.vmin: Vec = nc.load_data.q_droop_vmin[self.idx]
        self.vmax: Vec = nc.load_data.q_droop_vmax[self.idx]
        self.shunt_idx: IntVec = np.flatnonzero(
            nc.shunt_data.active
            & (nc.shunt_data.control_mode_int == ShuntControlMode.QVDroop.idx())
            & (nc.shunt_data.q_droop_snom > 0.0)
        )
        self.bus_idx = np.r_[self.bus_idx, nc.shunt_data.bus_idx[self.shunt_idx]]
        self.reference = np.r_[self.reference, np.zeros(len(self.shunt_idx), dtype=complex)]
        self.snom = np.r_[self.snom, nc.shunt_data.q_droop_snom[self.shunt_idx]]
        self.droop = np.r_[self.droop, nc.shunt_data.q_droop[self.shunt_idx]]
        self.vset = np.r_[self.vset, nc.shunt_data.vset[self.shunt_idx]]
        self.vmin = np.r_[self.vmin, nc.shunt_data.vmin[self.shunt_idx]]
        self.vmax = np.r_[self.vmax, nc.shunt_data.vmax[self.shunt_idx]]
        self.generator_data: GeneratorData = nc.generator_data
        self.generator_idx: IntVec = np.flatnonzero(nc.generator_data.active
            & (nc.generator_data.control_mode_int == GeneratorControlMode.QVDroop.idx())
            & (nc.bus_data.bus_types[nc.generator_data.bus_idx] != BusMode.Slack_tpe.value))
        self.bus_idx = np.r_[self.bus_idx, nc.generator_data.bus_idx[self.generator_idx]]
        self.reference = np.r_[self.reference, (nc.generator_data.p[self.generator_idx]
            + 1j * nc.generator_data.q[self.generator_idx]) / nc.Sbase]
        self.sbase: float = nc.Sbase
        self.nbus: int = nc.nbus

    def power(self, voltage: CxVec) -> CxVec:
        """Evaluate the existing VSC curve with the AC injection sign.

        :param voltage: Terminal positive-sequence voltage of each selected device, pu.
        :return: Total three-phase complex injection per device, system pu.
        """
        power: CxVec = self.reference.copy()
        k: int
        offset: int = len(self.idx) + len(self.shunt_idx)
        for k in range(offset):
            # The VSC function uses absorbed Q; a static generator uses injected Q.
            # Keep its voltage clamps and its existing (unclipped) reactive-power law.
            power[k] = complex(self.reference[k].real, -voltage_q_droop(
                ut=voltage[k], u_setpoint_min=self.vmin[k], u_setpoint_max=self.vmax[k],
                u_setpoint=self.vset[k], Q_setpoint=-self.reference[k].imag,
                S_r=self.snom[k], droop=self.droop[k], Q_min=-np.inf, Q_max=np.inf, S_base=self.sbase))
        for k, member in enumerate(self.generator_idx):
            data = self.generator_data
            q: float = generator_qv_droop(abs(voltage[offset + k]), data.v[member], data.k_droop[member],
                data.dead_band[member], data.qmin[member], data.qmax[member])
            power[offset + k] = complex(power[offset + k].real, q / self.sbase)
        return power

    def delta_q_bus(self, voltage: CxVec, include_generators: bool = True) -> Vec:
        """Correct the fixed Q reference already present in balanced bus injections.

        :param voltage: Bus voltages in pu.
        :param include_generators: Exclude generators when preparing the fixed non-generator result split.
        :return: Additional injected Q per bus, system pu.
        """
        result: Vec = np.zeros(self.nbus)
        count: int = len(self.bus_idx) if include_generators else len(self.idx) + len(self.shunt_idx)
        np.add.at(result, self.bus_idx[:count],
                  (self.power(voltage[self.bus_idx]).imag - self.reference.imag)[:count])
        return result

    def dq_dvm_per_device(self, voltage: CxVec) -> Vec:
        """Return the injected Q sensitivity to each selected device's voltage magnitude.

        :param voltage: Voltage of each selected device in power() order, p.u.
        :return: Reactive power sensitivity of each device in system p.u.
        """
        vm: Vec = np.abs(voltage)
        offset: int = len(self.idx) + len(self.shunt_idx)
        inside: np.ndarray = (self.vmin < vm[:offset]) & (vm[:offset] < self.vmax)
        values: Vec = np.zeros(len(self.bus_idx))
        values[:offset] = np.where(inside, -self.snom * 100.0 / (self.droop + 1e-20) / self.sbase, 0.0)
        data: GeneratorData = self.generator_data
        for position, member in enumerate(self.generator_idx, start=offset):
            deviation: float = data.v[member] - vm[position]
            if abs(deviation) > data.dead_band[member]:
                gain: float = data.k_droop[member] * data.qmax[member]
                reactive: float = (deviation - np.copysign(data.dead_band[member], deviation)) * gain
                if data.qmin[member] < reactive < data.qmax[member]:
                    values[position] = -gain / self.sbase
        return values

    def dq_dvm(self, voltage: CxVec) -> CSC:
        """Return the injected droop Q derivative by bus voltage magnitude.

        :param voltage: Bus voltages in pu.
        :return: nbus x nbus diagonal matrix in system pu.
        """
        values: Vec = self.dq_dvm_per_device(voltage[self.bus_idx])
        return scipy_to_mat(csc_matrix((values, (self.bus_idx, self.bus_idx)), shape=(self.nbus, self.nbus)))
