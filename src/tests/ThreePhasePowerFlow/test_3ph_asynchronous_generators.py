# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import pytest
from scipy.optimize import brentq

import VeraGridEngine.api as vge
from VeraGridEngine.enumerations import GeneratorType, GeneratorControlMode, ShuntConnectionType
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import (
    asynchronous_gen_currents, asynchronous_gen_q)
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import multi_island_pf_nc


def reference_power(slip: float, v012: np.ndarray, y0: complex) -> float:
    """Independent sequence-power balance for the single-cage test machine.

    :param slip: Candidate generating slip.
    :param v012: Terminal sequence voltages in pu.
    :param y0: Machine-base zero-sequence admittance.
    :return: Active injection minus the 6.3 MW setpoint.
    """
    rotor: np.ndarray = 0.00765 / np.array((slip, 2.0-slip)) + 0.05188j
    impedances: np.ndarray = 0.00546 + 0.12287j + 1.0 / (1.0 / (3.41315j) + 1.0 / rotor)
    powers: np.ndarray = -abs(v012[1:])**2 / impedances.conj()
    return float(powers[0].real * 15.6 - 6.3)


@pytest.mark.parametrize('y0', (0j, 1.0 / (0.01 + 0.1j)))
def test_asynchronous_sequence_currents_and_positive_power(y0: complex) -> None:
    """Check I2 at 2-s, I0 and P1 against an independent sequence solution.

    :param y0: Blocked or grounded zero-sequence path.
    """
    a: complex = np.exp(2j * np.pi / 3)
    transform: np.ndarray = np.array(((1, 1, 1), (1, a*a, a), (1, a, a*a)))
    v012: np.ndarray = np.array((0.03 + 0.02j, 0.98 + 0.04j, 0.04 - 0.02j))
    voltage: np.ndarray = transform @ v012
    currents: np.ndarray = asynchronous_gen_currents(voltage, 0.00546, 0.12287, 3.41315,
                                                      0.00765, 0.05188, 6.3, 15.6, y0)
    slip: float = brentq(reference_power, -0.05, -1e-6, args=(v012, y0), xtol=1e-14)
    rotor: np.ndarray = 0.00765 / np.array((slip, 2-slip)) + 0.05188j
    z12: np.ndarray = 0.00546 + 0.12287j + 1 / (1 / (3.41315j) + 1 / rotor)
    expected: np.ndarray = -v012 * np.array((y0, 1/z12[0], 1/z12[1]))
    np.testing.assert_allclose(np.linalg.solve(transform, currents * 3 / 15.6), expected, atol=1e-8)
    assert abs((v012[1] * expected[1].conjugate()).real * 15.6 - 6.3) < 1e-6
    assert np.sum(voltage * currents.conj()).real < 6.3  # Passive sequences absorb power.


def make_grid(unbalanced: bool, sbase: float, connection: ShuntConnectionType) -> vge.MultiCircuit:
    """Build a public AG example without an SVC capable of masking missing Q.

    :param unbalanced: Whether to use unequal phase loads.
    :param sbase: Network MVA base.
    :param connection: Asynchronous machine winding connection.
    :return: Two-bus example.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit(Sbase=sbase)
    source: vge.Bus = grid.add_bus(vge.Bus(name='Slack', Vnom=0.69, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(name='AG', Vnom=0.69))
    grid.add_generator(source, vge.Generator())
    machine: vge.Generator = vge.Generator(name='AG', tpe=GeneratorType.Asynchronous,
        control_mode=GeneratorControlMode.Q, P=6.3, Q=123.0, Snom=15.6,
        Rs=0.00546, Xs=0.12287, Xm=3.41315, Rr=0.00765, Xr=0.05188,
        r0=0.01*sbase/15.6, x0=0.1*sbase/15.6)
    machine.conn = connection
    grid.add_generator(target, machine)
    grid.add_line(vge.Line(bus_from=source, bus_to=target, r=0.02*sbase/100,
                           x=0.08*sbase/100, r0=0.04*sbase/100, x0=0.16*sbase/100))
    if unbalanced:
        grid.add_load(target, vge.Load(P=3.0, Q=0.9, P1=1.8, P2=0.8, P3=0.4,
                                      Q1=0.6, Q2=0.2, Q3=0.1))
    else:
        grid.add_load(target, vge.Load(P=3.0, Q=0.9))
    return grid


@pytest.mark.parametrize('sbase', (25.0, 100.0))
@pytest.mark.parametrize('connection', (ShuntConnectionType.Delta, ShuntConnectionType.FloatingStar,
                                       ShuntConnectionType.GroundedStar))
def test_unbalanced_machine_network_balance(sbase: float, connection: ShuntConnectionType) -> None:
    """Check terminal P/Q and phase KCL, including machine/system base conversion.

    :param sbase: Network MVA base.
    :param connection: Machine connection.
    """
    grid: vge.MultiCircuit = make_grid(True, sbase, connection)
    results: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, options=vge.PowerFlowOptions(
        tolerance=1e-9, max_iter=50, retry_with_other_methods=False, control_q=False))
    assert results.converged
    voltage: np.ndarray = np.array((results.voltage_A[1], results.voltage_B[1], results.voltage_C[1]))
    power: np.ndarray = np.array((results.Sbus_A[1], results.Sbus_B[1], results.Sbus_C[1]))
    power += np.array((1.8+0.6j, 0.8+0.2j, 0.4+0.1j))
    y0: complex = 1/(0.01+0.1j) if connection == ShuntConnectionType.GroundedStar else 0j
    expected: np.ndarray = asynchronous_gen_currents(voltage, 0.00546, 0.12287, 3.41315,
                                                     0.00765, 0.05188, 6.3, 15.6, y0)
    np.testing.assert_allclose(np.conj(power / voltage), expected, atol=1e-7)
    rotation: np.ndarray = np.exp(-2j*np.pi/3*np.arange(3))
    u1: complex = voltage @ rotation.conj() / 3
    i1: complex = np.conj(power / voltage) @ rotation.conj() / 3
    assert abs((3*u1*i1.conjugate()).real - 6.3) < 1e-6
    assert power.sum().imag < -4.0  # The arbitrary stored Q=123 must not enter the residual.


def test_balanced_ag_recovers_existing_positive_sequence() -> None:
    """Match the existing positive-sequence voltages and machine Q independently.

    :return: None.
    """
    grid: vge.MultiCircuit = make_grid(False, 100.0, ShuntConnectionType.Delta)
    grid.generators[1].Q = 0.0  # The existing positive-sequence import uses Q=0.
    options: vge.PowerFlowOptions = vge.PowerFlowOptions(tolerance=1e-9, max_iter=50,
        retry_with_other_methods=False, control_q=False, use_autodiff_jacobian=True)
    # The existing AG model belongs to the full AC/DC formulation. Select that
    # existing route explicitly, without changing the production solver selector.
    nc: NumericalCircuit = compile_numerical_circuit_at(grid)
    nc.active_branch_data.any_pf_control = True
    positive: vge.PowerFlowResults = multi_island_pf_nc(nc, options, logger=vge.Logger())
    three: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, options=options)
    assert positive.converged and three.converged
    np.testing.assert_allclose(three.voltage_A, positive.voltage, atol=1e-7)
    q: float = asynchronous_gen_q(positive.voltage[1], 0.00546, 0.12287, 3.41315,
                                  0.00765, 0.05188, 6.3, 15.6)
    assert abs(three.Sbus_A[1].imag + three.Sbus_B[1].imag + three.Sbus_C[1].imag + 0.9 - q) < 1e-6


def test_inactive_machine_adds_no_current() -> None:
    """Ignore an inactive AG with invalid parameters rather than solving its slip.

    :return: None.
    """
    grid: vge.MultiCircuit = make_grid(False, 100.0, ShuntConnectionType.Delta)
    grid.generators[1].active = False
    grid.generators[1].Xm = 0.0
    result: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid)
    assert result.converged
    assert abs(result.Sbus_A[1] + result.Sbus_B[1] + result.Sbus_C[1] + 3.0 + 0.9j) < 1e-4


@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar, ShuntConnectionType.NeutralStar))
def test_incomplete_grounding_has_specific_diagnostic(connection: ShuntConnectionType) -> None:
    """Reject missing Z0 or an unsupported explicit neutral, naming the problem.

    :param connection: Incomplete or unsupported grounding configuration.
    """
    grid: vge.MultiCircuit = make_grid(False, 100.0, connection)
    grid.generators[1].R0 = grid.generators[1].X0 = 1e-20
    with pytest.raises(ValueError, match='Asynchronous generator.*(Z0|neutral)'):
        vge.power_flow3ph(grid)
