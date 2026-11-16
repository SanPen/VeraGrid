# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Analytical source derivatives retain the merged ABC physical models."""
import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.basic_structures import CxVec, IntVec
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.positive_sequence_control import PositiveSequenceControl


def make_source_grid(sbase: float) -> vge.MultiCircuit:
    """Create a feeder with an ideal boundary and no nonlinear target devices.

    :param sbase: System power base in MVA.
    :return: Two-bus circuit for independent source evaluation.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit(Sbase=sbase)
    source: vge.Bus = grid.add_bus(vge.Bus(name='Source', Vnom=20.0, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(name='Target', Vnom=20.0))
    grid.add_generator(source, vge.Generator())
    grid.add_line(vge.Line(bus_from=source, bus_to=target, r=.02, x=.08, r0=.04, x0=.16))
    return grid


def compile_source_control(grid: vge.MultiCircuit) -> tuple[PositiveSequenceControl, CxVec, IntVec]:
    """Compile sources and supply a fixed, independently unbalanced voltage.

    :param grid: Public circuit containing the sources under test.
    :return: Source evaluator, retained ABC voltages, and full NABC lookup.
    """
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    lookup: IntVec = np.full(4 * nc.nbus, -1, dtype=int)
    phases: np.ndarray = 4 * np.arange(nc.nbus)[:, None] + np.arange(1, 4)
    lookup[phases] = np.arange(3 * nc.nbus).reshape(nc.nbus, 3)
    rotation: CxVec = np.exp(-2j * np.pi * np.arange(3) / 3.0)
    voltage: CxVec = np.tile(rotation, nc.nbus)
    voltage[3:6] = .985 * np.exp(.03j) * rotation + (.018 - .012j) * rotation.conj() + (.013 + .007j)
    return PositiveSequenceControl(nc, lookup), voltage, lookup


def source_currents(control: PositiveSequenceControl, voltage: CxVec) -> CxVec:
    """Evaluate the public current path in system pu.

    :param control: Source evaluator under test.
    :param voltage: Retained ABC voltage vector.
    :return: Physical source current injections in system pu.
    """
    current: CxVec = np.zeros(len(voltage), dtype=complex)
    control.add_currents(current, voltage, control.q)
    return current * 3.0 / control.sbase


def assert_current_derivatives(control: PositiveSequenceControl, voltage: CxVec, lookup: IntVec) -> None:
    """Compare every local analytical block to central physical-current differences.

    :param control: Source evaluator under test.
    :param voltage: Operating point away from nonsmooth control boundaries.
    :param lookup: Full NABC to retained conductor lookup.
    :return: None.
    """
    angle: np.ndarray
    magnitude: np.ndarray
    reactive: np.ndarray
    angle, magnitude, reactive = control.current_derivative_blocks(voltage, control.q, lookup)
    step: float = 1e-6
    bus: int
    phase: int
    for bus in range(len(lookup) // 4):
        local: IntVec = lookup[4 * bus + np.arange(1, 4)]
        for phase in range(3):
            conductor: int = local[phase]
            plus: CxVec = voltage.copy()
            minus: CxVec = voltage.copy()
            plus[conductor] *= np.exp(1j * step)
            minus[conductor] *= np.exp(-1j * step)
            numerical: CxVec = (source_currents(control, plus) - source_currents(control, minus)) / (2.0 * step)
            expected: CxVec = np.zeros(len(voltage), dtype=complex)
            expected[local] = angle[bus, 1:4, phase + 1]
            np.testing.assert_allclose(expected, numerical, atol=3e-8, rtol=2e-7)
            plus = voltage.copy()
            minus = voltage.copy()
            direction: complex = voltage[conductor] / abs(voltage[conductor])
            plus[conductor] += step * direction
            minus[conductor] -= step * direction
            numerical = (source_currents(control, plus) - source_currents(control, minus)) / (2.0 * step)
            expected[local] = magnitude[bus, 1:4, phase + 1]
            np.testing.assert_allclose(expected, numerical, atol=3e-8, rtol=2e-7)
    # The Q coordinates remain separate from voltage sensitivities.
    index: int
    for index in range(len(control.q)):
        original: float = control.q[index]
        control.q[index] = original + step
        plus = source_currents(control, voltage)
        control.q[index] = original - step
        minus = source_currents(control, voltage)
        control.q[index] = original
        expected = np.zeros(len(voltage), dtype=complex)
        expected[control.phases[index]] = reactive[index, 1:4]
        np.testing.assert_allclose(expected, (plus - minus) / (2.0 * step), atol=3e-8, rtol=2e-7)


@pytest.mark.parametrize('sbase', (25.0, 100.0))
@pytest.mark.parametrize('connection', (vge.ShuntConnectionType.GroundedStar,
                                      vge.ShuntConnectionType.FloatingStar, vge.ShuntConnectionType.Delta))
def test_synchronous_pq_derivative_and_terminal_sequences(sbase: float,
                                                         connection: vge.ShuntConnectionType) -> None:
    """Preserve total terminal P/Q and passive I0/I2 at an unbalanced point.

    :param sbase: System power base in MVA.
    :param connection: Physical machine connection.
    :return: None.
    """
    grid: vge.MultiCircuit = make_source_grid(sbase)
    machine: vge.Generator = vge.Generator(P=12.0, Q=4.0, control_mode=vge.GeneratorControlMode.Q,
                                         r0=.01, x0=.08, r2=.02, x2=.10)
    machine.conn = connection
    grid.add_generator(grid.buses[1], machine)
    control: PositiveSequenceControl
    voltage: CxVec
    lookup: IntVec
    control, voltage, lookup = compile_source_control(grid)
    current: CxVec = source_currents(control, voltage)[3:6]
    np.testing.assert_allclose(np.mean(voltage[3:6] * current.conj()), (12.0 + 4.0j) / sbase, atol=1e-12)
    rotation: CxVec = control.rotation
    v0: complex = np.mean(voltage[3:6])
    v2: complex = voltage[3:6] @ rotation / 3.0
    expected_zero: complex = -v0 / complex(.01, .08) if connection == vge.ShuntConnectionType.GroundedStar else 0j
    np.testing.assert_allclose(np.mean(current), expected_zero, atol=1e-12)
    np.testing.assert_allclose(current @ rotation / 3.0, -v2 / complex(.02, .10), atol=1e-12)
    assert_current_derivatives(control, voltage, lookup)


@pytest.mark.parametrize('ideal_zero', (False, True))
def test_synchronous_slack_passive_derivatives(ideal_zero: bool) -> None:
    """Differentiate the physical response before the core eliminates free I1.

    :param ideal_zero: Whether the grounded machine imposes ideal U0.
    :return: None.
    """
    grid: vge.MultiCircuit = make_source_grid(100.0)
    machine: vge.Generator = grid.generators[0]
    machine.R0 = 0.0 if ideal_zero else .01
    machine.X0 = 0.0 if ideal_zero else .08
    machine.R2, machine.X2 = .02, .10
    control: PositiveSequenceControl
    voltage: CxVec
    lookup: IntVec
    control, voltage, lookup = compile_source_control(grid)
    voltage[:3] = voltage[3:6]
    assert len(control.slack_bus_idx) == 1
    current: CxVec = source_currents(control, voltage)[:3]
    np.testing.assert_allclose(current @ control.rotation.conj() / 3.0, 0.0, atol=1e-12)
    assert_current_derivatives(control, voltage, lookup)


@pytest.mark.parametrize('connection', (vge.ShuntConnectionType.GroundedStar,
                                      vge.ShuntConnectionType.FloatingStar, vge.ShuntConnectionType.Delta))
@pytest.mark.parametrize('magnitude', (.85, .985, 1.15))
@pytest.mark.parametrize('legacy', (True, False))
def test_physical_shunt_droop_derivatives(connection: vge.ShuntConnectionType, magnitude: float, legacy: bool) -> None:
    """Include the voltage normalization and all conducting sequences of a SVC.

    :param connection: Physical shunt connection.
    :param magnitude: U1 magnitude selecting the linear region or either limit.
    :param legacy: Use the stored percentage droop and voltage clamps.
    :return: None.
    """
    grid: vge.MultiCircuit = make_source_grid(25.0)
    shunt: vge.ControllableShunt = vge.ControllableShunt(control_mode=vge.ShuntControlMode.QVDroop,
                                                       Snom=8.0, droop=3.0, vset=1.01,
                                                       qdroop=0.0 if legacy else 8.0 * 100.0 / 3.0,
                                                       Bmin=-18.0, Bmax=18.0)
    shunt.conn = connection
    grid.add_controllable_shunt(grid.buses[1], shunt)
    control: PositiveSequenceControl
    voltage: CxVec
    lookup: IntVec
    control, voltage, lookup = compile_source_control(grid)
    voltage[3:6] += (magnitude - .985) * np.exp(.03j) * control.rotation
    current: CxVec = source_currents(control, voltage)[3:6]
    v1: complex = voltage[3:6] @ control.rotation.conj() / 3.0
    if legacy:
        q: float = control.static_droop.power(np.array((v1,)))[0].imag
    else:
        conducting: CxVec = voltage[3:6]
        if connection != vge.ShuntConnectionType.GroundedStar:
            conducting = conducting - np.mean(conducting)
        squared: float = float(np.mean(np.abs(conducting) ** 2))
        q = float(np.clip(shunt.Qdroop * (shunt.Vset - abs(v1)),
                          shunt.Bmin * squared, shunt.Bmax * squared) / grid.Sbase)
    np.testing.assert_allclose(np.mean(voltage[3:6] * current.conj()), 1j * q, atol=1e-12)
    assert abs(current @ control.rotation / 3.0) > 1e-5
    assert_current_derivatives(control, voltage, lookup)


@pytest.mark.parametrize('vset', (.8, .97, .985, 1.0, 1.2))
def test_synchronous_droop_derivatives(vset: float) -> None:
    """Use the synchronous gain, dead band and Q clamps with total terminal P/Q.

    :param vset: Reference selecting each smooth interval of the existing law.
    :return: None.
    """
    grid: vge.MultiCircuit = make_source_grid(100.0)
    machine: vge.Generator = vge.Generator(P=12.0, control_mode=vge.GeneratorControlMode.QVDroop,
                                         vset=vset, r0=.01, x0=.08, r2=.02, x2=.10)
    machine.k_droop, machine.dead_band, machine.Qmin, machine.Qmax = 10.0, .005, -40.0, 50.0
    grid.add_generator(grid.buses[1], machine)
    control: PositiveSequenceControl
    voltage: CxVec
    lookup: IntVec
    control, voltage, lookup = compile_source_control(grid)
    current: CxVec = source_currents(control, voltage)[3:6]
    v1: complex = voltage[3:6] @ control.rotation.conj() / 3.0
    power: complex = control.static_droop.power(np.array((v1,)))[0]
    np.testing.assert_allclose(np.mean(voltage[3:6] * current.conj()), power, atol=1e-12)
    assert_current_derivatives(control, voltage, lookup)


def test_colocated_pv_and_new_droop_derivatives() -> None:
    """Accumulate physical sources without changing the existing PV Q column.

    :return: None.
    """
    grid: vge.MultiCircuit = make_source_grid(100.0)
    grid.add_generator(grid.buses[1], vge.Generator(P=3.0, r0=.01, x0=.08, r2=.02, x2=.10))
    droop: vge.Generator = vge.Generator(P=2.0, control_mode=vge.GeneratorControlMode.QVDroop,
                                       vset=1.01, r0=.02, x0=.09, r2=.03, x2=.11)
    droop.k_droop, droop.dead_band = 10.0, .002
    grid.add_generator(grid.buses[1], droop)
    grid.add_static_generator(grid.buses[1], vge.StaticGenerator(P=1.0, Q=.5, Snom=3.0,
        control_mode=vge.StaticGeneratorControlMode.QVDroop, vset=1.01, droop=3.0))
    grid.add_controllable_shunt(grid.buses[1], vge.ControllableShunt(Snom=2.0, droop=3.0, vset=1.01,
        control_mode=vge.ShuntControlMode.QVDroop))
    control: PositiveSequenceControl
    voltage: CxVec
    lookup: IntVec
    control, voltage, lookup = compile_source_control(grid)
    assert len(control.q) == 1
    assert_current_derivatives(control, voltage, lookup)
