# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np

from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.DataStructures.generator_data import GeneratorData
from VeraGridEngine.basic_structures import CxVec, IntVec, Vec, BoolVec
from VeraGridEngine.enumerations import (BusMode, GeneratorControlMode, ShuntConnectionType, GeneratorType,
                                         ShuntControlMode)
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import fortescue_012_to_abc
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.shunt_droop import ShuntDroop
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.static_generator_droop import StaticGeneratorDroop




def generator_sequence_admittance(data: GeneratorData, members: IntVec) -> np.ndarray:
    """Build the passive sequence response shared by generators and batteries.

    :param data: Compiled generator or battery data, on the system base.
    :param members: Active device indices to combine.
    :return: Finite ABC admittance; an ideal Z0=0 is constrained by CommonModeControl.
    """
    y0: complex = 0j
    y2: complex = 0j
    member: int
    for member in members:
        connection: int = data.conn[member]
        if connection == ShuntConnectionType.GroundedStar.idx():
            z0: complex = complex(data.r0[member], data.x0[member])
            if z0 == 0j:
                # The ABC formulation imposes U0=0 and recovers I0 from KCL.
                pass
            elif not np.isfinite(z0) or abs(z0) < 1e-12:
                raise ValueError('U1 power-flow Z0 must be finite and nonzero (at least 1e-12 pu), '
                                 'or exactly zero for an ideal grounded source: '
                                 + str(data.names[member])
                                 + '. Check R0/X0; for DGS imports, export r0 and x0 from PowerFactory.')
            else:
                y0 += 1.0 / z0
        elif connection in (ShuntConnectionType.FloatingStar.idx(), ShuntConnectionType.Delta.idx()):
            pass
        else:
            raise ValueError('U1 power-flow control does not support an explicit neutral connection: '
                             + str(data.names[member]))
        z2: complex = complex(data.r2[member], data.x2[member])
        if not np.isfinite(z2) or abs(z2) < 1e-12:
            raise ValueError('U1 power-flow Z2 must be finite and nonzero: '
                             + str(data.names[member])
                             + '. Check R2/X2; for DGS imports, export r2 and x2 from PowerFactory.')
        else:
            y2 += 1.0 / z2
    # An ideal Z0=0 has no finite stamp; it is distinct from a blocked I0 path.
    return fortescue_012_to_abc(y0, 0j, y2)


def sequence_source_currents(voltage: np.ndarray, power: CxVec,
                             admittance: np.ndarray, rotation: CxVec,
                             total_power: bool) -> np.ndarray:
    """Evaluate an I1 source with the passive I0/I2 response.

    :param voltage: ABC terminal voltages, one row per source.
    :param power: Source power injections in system pu.
    :param admittance: Passive ABC response, one matrix per source.
    :param rotation: Positive-sequence ABC rotation.
    :param total_power: Compensate passive absorption to preserve total terminal P/Q.
    :return: ABC current injections in system pu.
    """
    v1: CxVec = voltage @ rotation.conj() / 3.0
    passive_current: np.ndarray = -np.einsum('nij,nj->ni', admittance, voltage)
    if total_power:
        power = power - np.sum(voltage * passive_current.conj(), axis=1) / 3.0
    else:
        # Static generators and fixed-Q batteries specify positive-sequence power.
        pass
    i1: CxVec = np.conj(power / v1)
    return i1[:, None] * rotation + passive_current


def sequence_source_current_derivative(
        voltage: CxVec,
        d_voltage: CxVec,
        power: complex,
        d_power: complex,
        admittance: np.ndarray,
        rotation: CxVec,
        total_power: bool) -> CxVec:
    """Differentiate one positive-sequence source and its passive response.

    The source current is ``conj(Peff / U1) * rotation + Ipass``, where
    ``U1 = voltage @ conj(rotation) / 3`` and ``Ipass = -Yabc @ voltage``.
    When ``total_power`` is set, ``Peff`` subtracts the passive complex
    power, so that term must be differentiated as well.

    :param voltage: Three ABC terminal voltages.
    :param d_voltage: Changes in those voltages.
    :param power: Source power in system pu.
    :param d_power: Change in source power in system pu.
    :param admittance: Passive ABC admittance.
    :param rotation: Positive-sequence ABC rotation.
    :param total_power: Include passive-power compensation.
    :return: ABC current change in system pu.
    """
    v1: complex = voltage @ rotation.conj() / 3.0
    d_v1: complex = d_voltage @ rotation.conj() / 3.0
    passive: CxVec = -(admittance @ voltage)
    d_passive: CxVec = -(admittance @ d_voltage)
    if total_power:
        d_power -= np.sum(d_voltage * passive.conj() + voltage * d_passive.conj()) / 3.0
        power -= np.sum(voltage * passive.conj()) / 3.0
    else:
        pass
    d_i1: complex = np.conj(d_power / v1 - power * d_v1 / v1 ** 2)
    return d_i1 * rotation + d_passive


def sequence_source_voltage_derivatives(
        voltage: CxVec,
        power: complex,
        admittance: np.ndarray,
        rotation: CxVec,
        total_power: bool) -> tuple[np.ndarray, np.ndarray]:
    """Differentiate one ABC source with respect to its three polar voltages.

    :param voltage: Local ABC terminal voltages.
    :param power: Positive-sequence source power in system pu.
    :param admittance: Passive ABC admittance.
    :param rotation: Positive-sequence ABC rotation.
    :param total_power: Include passive-power compensation.
    :return: Angle and magnitude derivative matrices, with current rows and voltage columns.
    """
    angle: np.ndarray = np.empty((3, 3), dtype=np.complex128)
    magnitude: np.ndarray = np.empty((3, 3), dtype=np.complex128)
    d_voltage: CxVec = np.zeros(3, dtype=np.complex128)

    # Each column perturbs one phase. Reuse the directional derivative so the
    # passive-power compensation is identical for angle and magnitude changes.
    for phase in range(3):
        d_voltage[phase] = 1j * voltage[phase]
        angle[:, phase] = sequence_source_current_derivative(
            voltage=voltage,
            d_voltage=d_voltage,
            power=power,
            d_power=0j,
            admittance=admittance,
            rotation=rotation,
            total_power=total_power)

        d_voltage[phase] = voltage[phase] / abs(voltage[phase])
        magnitude[:, phase] = sequence_source_current_derivative(
            voltage=voltage,
            d_voltage=d_voltage,
            power=power,
            d_power=0j,
            admittance=admittance,
            rotation=rotation,
            total_power=total_power)
        d_voltage[phase] = 0j

    return angle, magnitude


class PositiveSequenceControl:
    """Sequence sources and local U1 regulators, preserving their connections."""

    __slots__ = ('bus_idx', 'phases', 'regular_idx', 'p', 'q', 'vset', 'qmin', 'qmax',
                 'limited', 'qbound', 'rotation', 'sbase', 'yabc', 'static_droop', 'droop_phases',
                 'static_phases', 'static_power', 'generator_share', 'generator_offset',
                 'shunt_slope', 'shunt_offset', 'battery_phases', 'battery_power', 'battery_yabc',
                 'pq_phases', 'pq_power', 'pq_yabc', 'generator_droop_idx',
                 'shunt_droop', 'droop_shunt_phases', 'droop_shunt_pattern',
                 'slack_bus_idx', 'slack_phases', 'slack_yabc', 'slack_vset')

    def __init__(self, nc: NumericalCircuit, bus_lookup: IntVec) -> None:
        """Group active U1 regulators on each non-reference bus.

        :param nc: Compiled island, with powers in MW/MVAr.
        :param bus_lookup: Mapping from full NABC slots to retained voltage unknowns.
        """
        asynchronous: BoolVec = nc.generator_data.active.astype(bool) & (
            nc.generator_data.tpe_int == GeneratorType.Asynchronous.idx())
        if np.any(asynchronous & (nc.generator_data.control_mode_int != GeneratorControlMode.Q.idx())):
            raise ValueError('Asynchronous generators require Q control mode in ABC; '
                             'their reactive power is calculated from the equivalent circuit.')
        else:
            pass
        pv: BoolVec = nc.generator_data.active.astype(bool) & (
            nc.generator_data.control_mode_int == GeneratorControlMode.V.idx())
        # A physical synchronous slack fixes complex U1; its I0/I2 still follow
        # the machine impedances. Legacy ideal sources retain their fixed ABC.
        slack: BoolVec = nc.generator_data.active.astype(bool) & (
            nc.generator_data.tpe_int == GeneratorType.Synchronous.idx()) & (
            ~nc.generator_data.is_static_generator) & (
            nc.bus_data.bus_types[nc.generator_data.bus_idx] == BusMode.Slack_tpe.value)
        # Disconnected terminals with no retained phase keep the existing island handling.
        slack &= np.any(bus_lookup[4 * nc.generator_data.bus_idx[:, None] + np.arange(1, 4)] >= 0, axis=1)
        if nc.load_data.fixed_voltage is not None:
            fixed_buses: IntVec = nc.load_data.bus_idx[nc.load_data.active & nc.load_data.fixed_voltage]
            slack &= ~np.isin(nc.generator_data.bus_idx, fixed_buses)
        else:
            pass
        for member in np.flatnonzero(slack):
            z0: complex = complex(nc.generator_data.r0[member], nc.generator_data.x0[member])
            z2: complex = complex(nc.generator_data.r2[member], nc.generator_data.x2[member])
            if (abs(z0) < 1e-12 and abs(z2) < 1e-12
                    and nc.generator_data.conn[member] == ShuntConnectionType.GroundedStar.idx()):
                # Defaults historically represent an ideal balanced voltage boundary.
                slack[nc.generator_data.bus_idx == nc.generator_data.bus_idx[member]] = False
            else:
                pass
        self.slack_bus_idx: IntVec = np.unique(nc.generator_data.bus_idx[slack])
        self.slack_phases: np.ndarray = bus_lookup[4 * self.slack_bus_idx[:, None] + np.arange(1, 4)]
        if np.any(self.slack_phases < 0):
            raise ValueError('Synchronous slack sequence model requires all three terminal phases.')
        else:
            pass
        self.slack_vset: CxVec = nc.bus_data.Vbus[self.slack_bus_idx].copy()
        self.slack_yabc: np.ndarray = np.zeros((len(self.slack_bus_idx), 3, 3), dtype=complex)
        for index, bus in enumerate(self.slack_bus_idx):
            members: IntVec = np.flatnonzero(slack & (nc.generator_data.bus_idx == bus))
            self.slack_yabc[index] = generator_sequence_admittance(nc.generator_data, members)
        selected: BoolVec = pv & (
            nc.bus_data.bus_types[nc.generator_data.bus_idx] != BusMode.Slack_tpe.value)
        pq: BoolVec = nc.generator_data.active.astype(bool) & ~asynchronous & (
            (nc.generator_data.control_mode_int == GeneratorControlMode.Q.idx())
            | (nc.generator_data.control_mode_int == GeneratorControlMode.QVDroop.idx())) & (
            nc.bus_data.bus_types[nc.generator_data.bus_idx] != BusMode.Slack_tpe.value)
        battery_selected: BoolVec = nc.battery_data.active.astype(bool) & (
            nc.battery_data.control_mode_int == GeneratorControlMode.V.idx()) & (
            nc.bus_data.bus_types[nc.battery_data.bus_idx] != BusMode.Slack_tpe.value)
        shunts: BoolVec = nc.shunt_data.active & (
            nc.shunt_data.control_mode_int == ShuntControlMode.Continuous.idx()) & (
            nc.bus_data.bus_types[nc.shunt_data.bus_idx] != BusMode.Slack_tpe.value)
        self.bus_idx: IntVec = np.union1d(np.union1d(nc.generator_data.bus_idx[selected],
            nc.battery_data.bus_idx[battery_selected]), nc.shunt_data.bus_idx[shunts])
        self.phases: np.ndarray = bus_lookup[4 * self.bus_idx[:, None] + np.array((1, 2, 3))]
        self.regular_idx: IntVec = np.flatnonzero(nc.generator_data.active.astype(bool) & ~selected & ~pq & ~slack)
        count: int = len(self.bus_idx)
        self.p: Vec = np.zeros(count)
        self.q: Vec = np.zeros(count)
        self.vset: Vec = np.ones(count)
        self.qmin: Vec = np.zeros(count)
        self.qmax: Vec = np.zeros(count)
        self.limited: BoolVec = np.zeros(count, dtype=bool)
        self.qbound: Vec = np.zeros(count)
        self.rotation: CxVec = np.exp(-2j * np.pi / 3 * np.arange(3))
        self.sbase: float = nc.Sbase
        # Synchronous PQ machines retain terminal P/Q and the same passive I0/I2 as PV.
        pq_idx: IntVec = np.flatnonzero(pq)
        self.pq_phases: np.ndarray = bus_lookup[
            4 * nc.generator_data.bus_idx[pq_idx, None] + np.array((1, 2, 3))]
        self.pq_power: CxVec = (nc.generator_data.p[pq_idx]
                               + 1j * nc.generator_data.q[pq_idx]) / nc.Sbase
        self.pq_yabc: np.ndarray = np.zeros((len(pq_idx), 3, 3), dtype=complex)
        if np.any(self.pq_phases < 0):
            raise ValueError('Synchronous generator sequence model requires all three terminal phases.')
        else:
            pass
        # Fixed-Q storage uses the same sequence source without adding control unknowns.
        battery_idx: IntVec = np.flatnonzero(nc.battery_data.active.astype(bool) & (
            nc.battery_data.control_mode_int == GeneratorControlMode.Q.idx()))
        self.battery_phases: np.ndarray = bus_lookup[
            4 * nc.battery_data.bus_idx[battery_idx, None] + np.array((1, 2, 3))]
        self.battery_power: CxVec = (nc.battery_data.p[battery_idx]
                                     + 1j * nc.battery_data.q[battery_idx]) / nc.Sbase
        self.battery_yabc: np.ndarray = np.zeros((len(battery_idx), 3, 3), dtype=complex)
        if np.any(self.battery_phases < 0):
            raise ValueError('Battery sequence model requires all three terminal phases.')
        elif np.any(nc.battery_data.active.astype(bool) & ~np.isin(nc.battery_data.control_mode_int,
                (GeneratorControlMode.Q.idx(), GeneratorControlMode.V.idx()))):
            raise ValueError('Battery ABC power flow supports fixed Q or positive-sequence voltage control.')
        else:
            pass
        index: int
        member: int
        for data, indices, admittance in ((nc.generator_data, pq_idx, self.pq_yabc),
                                         (nc.battery_data, battery_idx, self.battery_yabc)):
            for index, member in enumerate(indices):
                admittance[index] = generator_sequence_admittance(data, np.array((member,)))
        self.yabc: np.ndarray = np.zeros((count, 3, 3), dtype=complex)
        self.generator_share: Vec = np.ones(count)
        self.generator_offset: Vec = np.zeros(count)
        self.shunt_slope: np.ndarray = np.zeros((count, 3, 3), dtype=complex)
        self.shunt_offset: np.ndarray = np.zeros((count, 3, 3), dtype=complex)
        # Positive-sequence static injections use a separate fixed-power or
        # Q-V droop law and introduce no additional Newton coordinates.
        self.static_droop: StaticGeneratorDroop = StaticGeneratorDroop(nc)
        self.shunt_droop: ShuntDroop = ShuntDroop(nc)
        if np.any(self.shunt_droop.control_bus_idx != self.shunt_droop.bus_idx):
            raise ValueError('Remote shunt Q-V droop has no three-phase power flow model.')
        self.generator_droop_idx: IntVec = np.searchsorted(pq_idx, self.static_droop.generator_idx)
        static_idx: IntVec = np.flatnonzero(nc.load_data.active & nc.load_data.is_positive_sequence
                                          & (nc.load_data.S != 0j))
        self.static_phases: np.ndarray = bus_lookup[
            4 * nc.load_data.bus_idx[static_idx, None] + np.array((1, 2, 3))]
        self.static_power: CxVec = -nc.load_data.S[static_idx] / nc.Sbase
        if np.any(self.static_phases < 0):
            raise ValueError('Static generator sequence model requires all three terminal phases.')
        else:
            pass
        self.droop_phases: np.ndarray = bus_lookup[
            4 * self.static_droop.bus_idx[:, None] + np.array((1, 2, 3))]
        if np.any(self.droop_phases < 0):
            raise ValueError('Q-V droop requires all three terminal phases.')
        else:
            pass
        droop_shunts: IntVec = np.r_[self.static_droop.shunt_idx, self.shunt_droop.idx]
        self.droop_shunt_phases: np.ndarray = bus_lookup[
            4 * nc.shunt_data.bus_idx[droop_shunts, None] + np.arange(1, 4)]
        if np.any(self.droop_shunt_phases < 0):
            raise ValueError('Shunt Q-V droop requires all three terminal phases.')
        self.droop_shunt_pattern: np.ndarray = np.zeros((len(droop_shunts), 3, 3), dtype=complex)
        for index, member in enumerate(droop_shunts):
            connection: int = nc.shunt_data.conn[member]
            if connection == ShuntConnectionType.GroundedStar.idx():
                self.droop_shunt_pattern[index] = np.eye(3, dtype=complex)
            elif connection in (ShuntConnectionType.Delta.idx(), ShuntConnectionType.FloatingStar.idx()):
                self.droop_shunt_pattern[index] = fortescue_012_to_abc(0j, 1+0j, 1+0j)
            else:
                raise ValueError('Shunt Q-V droop does not support an explicit neutral: '
                                 + str(nc.shunt_data.names[member]))

        # Colocated regulators share one voltage constraint and aggregate Q capability.
        index: int
        bus: int
        for index, bus in enumerate(self.bus_idx):
            members: IntVec = np.flatnonzero(selected & (nc.generator_data.bus_idx == bus))
            battery_members: IntVec = np.flatnonzero(battery_selected & (nc.battery_data.bus_idx == bus))
            shunt_members: IntVec = np.flatnonzero(shunts & (nc.shunt_data.bus_idx == bus))
            if np.any(self.phases[index] < 0):
                raise ValueError('Positive-sequence voltage control requires a local ABC bus.')
            elif len(members):
                self.vset[index] = nc.generator_data.v[members[0]]
            elif len(battery_members):
                self.vset[index] = nc.battery_data.v[battery_members[0]]
            else:
                self.vset[index] = nc.shunt_data.vset[shunt_members[0]]
            data: GeneratorData
            indices: IntVec
            for data, indices in ((nc.generator_data, members), (nc.battery_data, battery_members)):
                remote: IntVec = data.controllable_bus_idx[indices]
                if np.any((remote >= 0) & (remote != bus)):
                    raise ValueError('Positive-sequence voltage control requires a local ABC bus.')
                elif not np.allclose(data.v[indices], self.vset[index], rtol=0.0, atol=1e-8):
                    raise ValueError('Positive-sequence regulators on the same bus need the same voltage setpoint.')
                else:
                    self.p[index] += np.sum(data.p[indices]) / nc.Sbase
                    self.qmin[index] += np.sum(data.qmin[indices]) / nc.Sbase
                    self.qmax[index] += np.sum(data.qmax[indices]) / nc.Sbase
                    self.yabc[index] += generator_sequence_admittance(data, indices)

            # One shared U1 constraint avoids duplicate equations for colocated units.
            # Share the group variable over their available Q / nominal-B ranges.
            if len(shunt_members):
                remote = nc.shunt_data.controllable_bus_idx[shunt_members]
                if np.any((remote >= 0) & (remote != bus)):
                    raise ValueError('Continuous shunt U1 control requires a local ABC bus.')
                elif not np.allclose(nc.shunt_data.vset[shunt_members], self.vset[index], rtol=0.0, atol=1e-8):
                    raise ValueError('Positive-sequence regulators on the same bus need the same voltage setpoint.')
                elif (not np.all(np.isfinite(nc.shunt_data.qmin[shunt_members]))
                      or not np.all(np.isfinite(nc.shunt_data.qmax[shunt_members]))
                      or np.any(nc.shunt_data.qmin[shunt_members] > nc.shunt_data.qmax[shunt_members])):
                    raise ValueError('Continuous shunt U1 control requires finite, ordered limits.')
                else:
                    pass
                generator_min: float = self.qmin[index]
                generator_range: float = self.qmax[index] - generator_min
                self.qmin[index] += np.sum(nc.shunt_data.qmin[shunt_members]) / nc.Sbase
                self.qmax[index] += np.sum(nc.shunt_data.qmax[shunt_members]) / nc.Sbase
                span: float = self.qmax[index] - self.qmin[index]
                if span < 0.0 or not np.isfinite(span):
                    raise ValueError('Continuous shunt U1 control requires finite, ordered limits.')
                elif span == 0.0:
                    self.limited[index] = True
                    self.qbound[index] = self.qmin[index]
                    self.generator_share[index] = 0.0
                else:
                    self.generator_share[index] = generator_range / span
                self.generator_offset[index] = generator_min - self.qmin[index] * self.generator_share[index]
                for member in shunt_members:
                    connection: int = nc.shunt_data.conn[member]
                    if connection == ShuntConnectionType.GroundedStar.idx():
                        pattern: np.ndarray = np.eye(3, dtype=complex)
                    elif connection in (ShuntConnectionType.Delta.idx(), ShuntConnectionType.FloatingStar.idx()):
                        pattern = fortescue_012_to_abc(0j, 1+0j, 1+0j)
                    else:
                        raise ValueError('Continuous shunt U1 control does not support an explicit neutral: '
                                         + str(nc.shunt_data.names[member]))
                    share: float = ((nc.shunt_data.qmax[member] - nc.shunt_data.qmin[member]) / nc.Sbase / span
                                    if span > 0.0 else 0.0)
                    self.shunt_slope[index] += share * pattern
                    self.shunt_offset[index] += (nc.shunt_data.qmin[member] / nc.Sbase
                                                 - self.qmin[index] * share) * pattern
            else:
                pass

    def _evaluate_droop_shunts(self, voltage: CxVec,
                              legacy_power: Vec) -> tuple[np.ndarray, Vec, Vec, BoolVec]:
        """Evaluate the physical shunt current parameters for both stored droop conventions.

        :param voltage: Retained conductor voltages in p.u.
        :param legacy_power: Reactive injections from the legacy percentage droop in system p.u.
        :return: Conducting voltages, their squared magnitudes, susceptances and limit flags.
        """
        phase_voltage: np.ndarray = voltage[self.droop_shunt_phases]
        conducting: np.ndarray = np.einsum('nij,nj->ni', self.droop_shunt_pattern, phase_voltage)
        squared: Vec = np.mean(np.abs(conducting) ** 2, axis=1)
        first_new: int = len(legacy_power)
        control_magnitude: Vec = np.abs(phase_voltage[first_new:] @ self.rotation.conj() / 3.0)
        new_power, limited = self.shunt_droop.q_and_limits(squared[first_new:], control_magnitude)
        susceptance: Vec = np.divide(np.r_[legacy_power, new_power], squared,
                                     out=np.zeros_like(squared), where=squared > 0.0)
        return conducting, squared, susceptance, np.r_[np.zeros(first_new, dtype=bool), limited]

    def add_currents(self, currents: CxVec, voltage: CxVec, q: Vec) -> None:
        """Add voltage-controlled and fixed-power positive-sequence sources.

        :param currents: Existing generator injections, modified in place (MW / pu voltage).
        :param voltage: Retained phase voltages in pu.
        :param q: Group Q / nominal shunt susceptance, in system pu.
        """
        generator_q: Vec = self.generator_offset + self.generator_share * q
        # The unconstrained slack I1 is recovered from KCL by CommonModeControl.
        currents[self.slack_phases] -= np.einsum('nij,nj->ni', self.slack_yabc,
                                               voltage[self.slack_phases]) * self.sbase / 3.0
        droop_v1: CxVec = voltage[self.droop_phases] @ self.rotation.conj() / 3.0
        droop_power: CxVec = self.static_droop.power(droop_v1)
        nstatic: int = len(self.static_droop.idx)
        shunt_end: int = nstatic + len(self.static_droop.shunt_idx)
        # Only Q changes; the existing synchronous source retains terminal P and I0/I2.
        pq_power: CxVec = self.pq_power.copy()
        pq_power[self.generator_droop_idx] = droop_power[shunt_end:]
        currents[self.phases] += sequence_source_currents(voltage[self.phases], self.p + 1j * generator_q,
            self.yabc, self.rotation, total_power=True) * self.sbase / 3.0
        np.add.at(currents, self.pq_phases,
            sequence_source_currents(voltage[self.pq_phases], pq_power,
                self.pq_yabc, self.rotation, total_power=True) * self.sbase / 3.0)
        np.add.at(currents, self.battery_phases,
            sequence_source_currents(voltage[self.battery_phases], self.battery_power,
                self.battery_yabc, self.rotation, total_power=False) * self.sbase / 3.0)
        # A shunt changes one common B, rather than injecting only positive-sequence current.
        # Its connection therefore retains the physical negative/zero-sequence response.
        shunt_admittance: np.ndarray = self.shunt_offset + q[:, None, None] * self.shunt_slope
        currents[self.phases] -= (1j * np.einsum('nij,nj->ni', shunt_admittance, voltage[self.phases])
                                  * self.sbase / 3.0)
        # Reuse the same U1 projection and ABC rotation for controlled static injections.
        # Their Q is an explicit function of U1, so no additional Newton unknown is needed.
        droop_i1: CxVec = np.conj(droop_power[:nstatic] / droop_v1[:nstatic])
        np.add.at(currents, self.droop_phases[:nstatic],
                  droop_i1[:, None] * self.rotation * self.sbase / 3.0)
        # One physical susceptance acts across all conducting sequences.
        shunt_voltage, _, shunt_b, _ = self._evaluate_droop_shunts(voltage, droop_power[nstatic:shunt_end].imag)
        np.add.at(currents, self.droop_shunt_phases, -1j * shunt_b[:, None] * shunt_voltage * self.sbase / 3.0)
        # Fixed-power sequence injections use the same U1 projection. Their passive
        # I0/I2 response is already compiled into Ybus, so do not add it here again.
        static_v1: CxVec = voltage[self.static_phases] @ self.rotation.conj() / 3.0
        static_i1: CxVec = np.conj(self.static_power / static_v1)
        np.add.at(currents, self.static_phases,
                  static_i1[:, None] * self.rotation * self.sbase / 3.0)

    def current_derivative_blocks(self, voltage: CxVec, q: Vec,
                                  bus_lookup: IntVec) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Differentiate all positive-sequence source and shunt injections.

        Angle and magnitude arrays have shape ``(original_buses, 4, 4)`` in
        NABC terminal order: injected-current terminal, then changed-voltage
        terminal. The reactive array has shape ``(controls, 4)``. Controlled
        generators, batteries, static injections, droop, and continuous
        shunts follow the same active branches as the current evaluator.

        :param voltage: Retained conductor voltages.
        :param q: Reactive control coordinates.
        :param bus_lookup: Full NABC to retained conductor lookup.
        :return: Local angle, magnitude, and reactive-control current derivatives in system pu.
        """
        nbus: int = len(bus_lookup) // 4
        d_va: np.ndarray = np.zeros((nbus, 4, 4), dtype=np.complex128)
        d_vm: np.ndarray = np.zeros((nbus, 4, 4), dtype=np.complex128)
        d_q: np.ndarray = np.zeros((len(self.bus_idx), 4), dtype=np.complex128)

        # Source derivatives are local to one original bus; recover that bus
        # for each retained conductor before filling NABC derivative blocks.
        original_bus: IntVec = np.empty(len(voltage), dtype=np.int32)
        for slot in range(len(bus_lookup)):
            conductor: int = bus_lookup[slot]
            if conductor >= 0:
                original_bus[conductor] = slot // 4
            else:
                pass

        # Reuse the evaluator's source ordering and actual droop powers. Synchronous
        # machines retain total terminal power while their passive sequences respond.
        droop_v1: CxVec = voltage[self.droop_phases] @ self.rotation.conj() / 3.0
        droop_power: CxVec = self.static_droop.power(droop_v1)
        nstatic: int = len(self.static_droop.idx)
        shunt_end: int = nstatic + len(self.static_droop.shunt_idx)
        pq_power: CxVec = self.pq_power.copy()
        pq_power[self.generator_droop_idx] = droop_power[shunt_end:]

        # A physical slack contributes only its passive I0/I2 response here.
        # The formulation eliminates its free I1 current and supplies complex U1.
        slack: int
        for slack in range(len(self.slack_bus_idx)):
            phases: IntVec = self.slack_phases[slack]
            local_voltage: CxVec = voltage[phases]
            bus: int = self.slack_bus_idx[slack]
            d_va[bus, 1:4, 1:4] -= self.slack_yabc[slack] @ np.diag(1j * local_voltage)
            d_vm[bus, 1:4, 1:4] -= self.slack_yabc[slack] @ np.diag(local_voltage / np.abs(local_voltage))

        # Controlled sources include the passive ABC response, their shared
        # Q derivative, and the voltage-dependent continuous shunt current.
        zero_voltage: CxVec = np.zeros(3, dtype=np.complex128)
        for control in range(len(self.bus_idx)):
            phases: IntVec = self.phases[control]
            local_voltage: CxVec = voltage[phases]
            source_power: complex = (self.p[control]
                                     + 1j * (self.generator_offset[control]
                                             + self.generator_share[control] * q[control]))
            shunt: np.ndarray = self.shunt_offset[control] + q[control] * self.shunt_slope[control]
            angle_change: np.ndarray
            magnitude_change: np.ndarray
            angle_change, magnitude_change = sequence_source_voltage_derivatives(
                voltage=local_voltage,
                power=source_power,
                admittance=self.yabc[control],
                rotation=self.rotation,
                total_power=True)

            # I_shunt = -j Y(q) V: each voltage column contributes the
            # corresponding column of -j Y(q) diag(dV/dcoordinate).
            angle_change -= 1j * shunt @ np.diag(1j * local_voltage)
            magnitude_change -= 1j * shunt @ np.diag(local_voltage / np.abs(local_voltage))
            d_va[self.bus_idx[control], 1:4, 1:4] += angle_change
            d_vm[self.bus_idx[control], 1:4, 1:4] += magnitude_change

            # The Q column changes both generator power and shunt admittance.
            control_change: CxVec = sequence_source_current_derivative(
                voltage=local_voltage,
                d_voltage=zero_voltage,
                power=source_power,
                d_power=1j * self.generator_share[control],
                admittance=self.yabc[control],
                rotation=self.rotation,
                total_power=True)
            d_q[control, 1:4] = control_change - 1j * (self.shunt_slope[control] @ local_voltage)

        # Fixed-Q sources need no Q column. Synchronous PQ specifies total
        # terminal P/Q; fixed-Q storage retains its positive-sequence convention.
        sequence_phases: np.ndarray
        sequence_power: CxVec
        sequence_admittance: np.ndarray
        total_power: bool
        source: int
        for sequence_phases, sequence_power, sequence_admittance, total_power in (
                (self.pq_phases, pq_power, self.pq_yabc, True),
                (self.battery_phases, self.battery_power, self.battery_yabc, False)):
            for source in range(len(sequence_power)):
                phases: IntVec = sequence_phases[source]
                local_voltage: CxVec = voltage[phases]
                bus: int = original_bus[phases[0]]
                angle_change, magnitude_change = sequence_source_voltage_derivatives(
                    voltage=local_voltage,
                    power=sequence_power[source],
                    admittance=sequence_admittance[source],
                    rotation=self.rotation,
                    total_power=total_power)
                d_va[bus, 1:4, 1:4] += angle_change
                d_vm[bus, 1:4, 1:4] += magnitude_change

        # Static injections have no passive current, so their columns are
        # the positive-sequence voltage sensitivity times the ABC rotation.
        for static in range(len(self.static_power)):
            phases: IntVec = self.static_phases[static]
            local_voltage: CxVec = voltage[phases]
            bus: int = original_bus[phases[0]]
            v1: complex = local_voltage @ self.rotation.conj() / 3.0
            i1: complex = np.conj(self.static_power[static] / v1)
            projection: CxVec = self.rotation.conj() / (3.0 * v1)
            angle_change: CxVec = -i1 * np.conj(1j * local_voltage * projection)
            magnitude_change: CxVec = -i1 * np.conj(
                local_voltage / np.abs(local_voltage) * projection)
            d_va[bus, 1:4, 1:4] += self.rotation[:, None] * angle_change[None, :]
            d_vm[bus, 1:4, 1:4] += self.rotation[:, None] * magnitude_change[None, :]

        # Differentiate each existing Q-U1 law in its active smooth interval.
        # Clamps and the synchronous dead band have zero power sensitivity.
        droop_slopes: Vec = self.static_droop.dq_dvm_per_device(droop_v1)
        sequence_factor: CxVec = self.rotation.conj() / 3.0
        for droop in range(len(droop_power)):
            if nstatic <= droop < shunt_end:
                continue  # Both physical shunt laws are differentiated below.
            phases: IntVec = self.droop_phases[droop]
            local_voltage: CxVec = voltage[phases]
            bus: int = original_bus[phases[0]]
            v1: complex = droop_v1[droop]
            slope: float = droop_slopes[droop]
            angle_u1: CxVec = 1j * local_voltage * sequence_factor
            magnitude_u1: CxVec = local_voltage / np.abs(local_voltage) * sequence_factor
            angle_power: CxVec = 1j * slope * np.real(np.conj(v1) * angle_u1) / abs(v1)
            magnitude_power: CxVec = 1j * slope * np.real(np.conj(v1) * magnitude_u1) / abs(v1)
            if droop < nstatic:
                # Static droop remains a pure I1 injection, including 1/U1.
                angle_current: CxVec = np.conj(
                    angle_power / v1 - droop_power[droop] * angle_u1 / v1 ** 2)
                magnitude_current: CxVec = np.conj(
                    magnitude_power / v1 - droop_power[droop] * magnitude_u1 / v1 ** 2)
                d_va[bus, 1:4, 1:4] += self.rotation[:, None] * angle_current[None, :]
                d_vm[bus, 1:4, 1:4] += self.rotation[:, None] * magnitude_current[None, :]
            else:
                # PQ source derivatives above already include the passive response
                # and 1/U1. Add only the synchronous droop power sensitivity.
                d_va[bus, 1:4, 1:4] += self.rotation[:, None] * np.conj(angle_power / v1)[None, :]
                d_vm[bus, 1:4, 1:4] += self.rotation[:, None] * np.conj(magnitude_power / v1)[None, :]

        # For B=Q/mean(|pattern V|^2), both B and the conducting voltage
        # depend on the phases. At a physical B limit only the latter varies.
        shunt_voltage, squared, susceptance, limited = self._evaluate_droop_shunts(
            voltage, droop_power[nstatic:shunt_end].imag)
        shunt_slopes: Vec = np.r_[droop_slopes[nstatic:shunt_end], -self.shunt_droop.slope]
        for index, phases in enumerate(self.droop_shunt_phases):
            bus: int = original_bus[phases[0]]
            local_voltage: CxVec = voltage[phases]
            pattern: np.ndarray = self.droop_shunt_pattern[index]
            conducting: CxVec = shunt_voltage[index]
            b: float = susceptance[index]
            v1: complex = local_voltage @ sequence_factor
            for change, jacobian in ((1j * local_voltage, d_va),
                                     (local_voltage / np.abs(local_voltage), d_vm)):
                d_conducting: np.ndarray = pattern * change[None, :]
                d_current: np.ndarray = b * d_conducting
                if not limited[index] and squared[index] > 0.0:
                    d_squared: Vec = 2.0 * np.real(conducting.conj() @ d_conducting) / 3.0
                    d_reactive: Vec = (shunt_slopes[index] * np.real(np.conj(v1) * change * sequence_factor) / abs(v1)
                                       if abs(v1) > 0.0 else np.zeros(3))
                    d_b: Vec = (d_reactive - b * d_squared) / squared[index]
                    d_current += conducting[:, None] * d_b[None, :]
                jacobian[bus, 1:4, 1:4] -= 1j * d_current

        return d_va, d_vm, d_q

    def residual(self, voltage: CxVec, q: Vec) -> Vec:
        """Return U1 constraints, or fixed Q constraints after a capability limit.

        :param voltage: Retained phase voltages in pu.
        :param q: Group reactive variable in system pu; shunt contribution is nominal at 1 pu.
        :return: One residual per regulated bus.
        """
        v1: CxVec = voltage[self.phases] @ self.rotation.conj() / 3.0
        return np.where(self.limited, q - self.qbound, np.abs(v1) - self.vset)

    def enforce_limits(self) -> bool:
        """Latch violated Q/B limits, following the existing one-way PV-to-PQ policy.

        :return: Whether any voltage constraint changed to fixed Q.
        """
        violated: BoolVec = ~self.limited & ((self.q < self.qmin) | (self.q > self.qmax))
        self.qbound[violated] = np.clip(self.q, self.qmin, self.qmax)[violated]
        self.limited |= violated
        return bool(np.any(violated))
