# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Synchronous PQ terminal powers and passive sequences, checked through network KCL."""
import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.enumerations import GeneratorControlMode, ShuntConnectionType
from tests.ThreePhasePowerFlow.test_3ph_positive_sequence_voltage_control import make_grid, solve, target_voltages
from tests.ThreePhasePowerFlow.test_3ph_common_mode import floating_grid, formulation


@pytest.mark.parametrize('power', (12+3j, -4-1j, 0j))
@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar,
    ShuntConnectionType.FloatingStar, ShuntConnectionType.Delta))
@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_pq_terminal_power_and_passive_sequences(power: complex, connection: ShuntConnectionType,
                                                sbase: float) -> None:
    """Preserve total P/Q under imbalance and obtain I0/I2 from physical impedances.

    :param power: Total terminal injection, MW+jMVAr.
    :param connection: Physical zero-sequence path.
    :param sbase: System power base in MVA.
    """
    grid: vge.MultiCircuit = make_grid(sbase=sbase)
    gen: vge.Generator = grid.generators[1]
    gen.control_mode = GeneratorControlMode.Q
    gen.P, gen.Q, gen.conn = power.real, power.imag, connection
    # Blocked I0 does not require a fictitious nonzero Z0.
    if connection != ShuntConnectionType.GroundedStar:
        gen.R0 = gen.X0 = 0.0
    result: vge.PowerFlowResults3Ph = solve(grid)
    voltage: np.ndarray = target_voltages(result)
    injection: np.ndarray = np.array((result.St_A[0], result.St_B[0], result.St_C[0]))
    injection += np.array((8+3j, 5+2j, 2+1j))
    a: complex = np.exp(2j*np.pi/3)
    transform: np.ndarray = np.array(((1, 1, 1), (1, a, a*a), (1, a*a, a))) / 3
    v012: np.ndarray = transform @ voltage
    i012: np.ndarray = transform @ (np.conj(injection / voltage) * 3 / sbase)
    np.testing.assert_allclose(injection.sum(), power, atol=1e-6)
    expected_i0: complex = -v012[0] / complex(gen.R0, gen.X0) if (
        connection == ShuntConnectionType.GroundedStar) else 0j
    np.testing.assert_allclose(i012[[0, 2]], (expected_i0, -v012[2]/complex(gen.R2, gen.X2)), atol=2e-8)
    assert abs(v012[2]) > 1e-4
    assert abs(abs(v012[1]) - gen.Vset) > 1e-3  # PQ must not regulate U1.
    sequence_power: np.ndarray = v012 * i012.conj() * sbase
    np.testing.assert_allclose(sequence_power[1], power - sequence_power[0] - sequence_power[2], atol=1e-6)


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_balanced_pq_matches_positive_sequence(solver: vge.SolverType) -> None:
    """Recover the existing balanced solution without changing any solver.

    :param solver: Existing numerical method.
    """
    grid: vge.MultiCircuit = make_grid(unbalanced=False)
    grid.generators[1].control_mode = GeneratorControlMode.Q
    grid.generators[1].Q = 3.0
    abc: vge.PowerFlowResults3Ph = solve(grid, solver=solver)
    positive: vge.PowerFlowResults = vge.power_flow(grid, options=vge.PowerFlowOptions(
        tolerance=1e-9, control_q=False, retry_with_other_methods=False))
    assert positive.converged
    np.testing.assert_allclose(abc.voltage_A, positive.voltage, atol=1e-8)


def test_pq_matches_pv_at_reactive_limit() -> None:
    """A PV machine at its Q bound must have the same sequence response as fixed PQ."""
    grid: vge.MultiCircuit = make_grid()
    gen: vge.Generator = grid.generators[1]
    gen.Qmax = 2.0
    limited: vge.PowerFlowResults3Ph = solve(grid)
    gen.control_mode = GeneratorControlMode.Q
    gen.Q = 2.0
    np.testing.assert_allclose(target_voltages(solve(grid)), target_voltages(limited), atol=1e-8)


def test_parallel_pq_and_inactive_generators() -> None:
    """Accumulate colocated sources while ignoring inactive sequence placeholders."""
    grid: vge.MultiCircuit = make_grid()
    gen: vge.Generator = grid.generators[1]
    gen.control_mode = GeneratorControlMode.Q
    gen.Q = 3.0
    reference: vge.PowerFlowResults3Ph = solve(grid)
    gen.P /= 2
    gen.Q /= 2
    gen.R0 *= 2
    gen.X0 *= 2
    gen.R2 *= 2
    gen.X2 *= 2
    grid.add_generator(grid.buses[1], vge.Generator(P=gen.P, Q=gen.Q,
        control_mode=GeneratorControlMode.Q, r0=gen.R0, x0=gen.X0, r2=gen.R2, x2=gen.X2))
    grid.add_generator(grid.buses[1], vge.Generator(P=100, Q=50,
        control_mode=GeneratorControlMode.Q, active=False))
    np.testing.assert_allclose(target_voltages(solve(grid)), target_voltages(reference), atol=1e-8)


@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar,
    ShuntConnectionType.FloatingStar, ShuntConnectionType.Delta))
def test_pq_preserves_physical_common_mode(connection: ShuntConnectionType) -> None:
    """PQ creates an earth reference only when its connection actually permits I0.

    :param connection: Floating or earthed machine.
    """
    grid: vge.MultiCircuit = floating_grid()
    gen: vge.Generator = vge.Generator(P=2, Q=1, control_mode=GeneratorControlMode.Q,
        r0=0.01, x0=0.08, r2=0.02, x2=0.1)
    gen.conn = connection
    grid.add_generator(grid.buses[2], gen)
    problem = formulation(grid)
    assert len(problem.common_mode.phases) == int(connection != ShuntConnectionType.GroundedStar)
    if connection != ShuntConnectionType.GroundedStar:
        shifted: np.ndarray = problem.V.copy()
        shifted[problem.bus_lookup[4*2 + np.array((1, 2, 3))]] += 0.03+0.02j
        np.testing.assert_allclose(problem.generator_currents(shifted, problem.positive_sequence.q),
            problem.generator_currents(problem.V, problem.positive_sequence.q), atol=1e-12)
    assert solve(grid).converged


@pytest.mark.parametrize('sequence', (0, 2))
def test_pq_invalid_sequence_names_machine(sequence: int) -> None:
    """Missing physical impedances produce the existing specific diagnosis.

    :param sequence: Invalid passive sequence.
    :return: None.
    """
    grid: vge.MultiCircuit = make_grid()
    gen: vge.Generator = grid.generators[1]
    gen.name = 'PQ machine'
    gen.control_mode = GeneratorControlMode.Q
    # Non-finite properties are rejected at assignment by devel's device contract.
    with pytest.raises(ValueError, match=rf'Non-finite value rejected for Generator\.R{sequence}'):
        if sequence == 0:
            gen.R0 = float('nan')
        else:
            gen.R2 = float('nan')
    # A finite but invalid impedance still requires the machine-specific physical diagnosis.
    with pytest.raises(ValueError, match=f'Z{sequence}.*PQ machine'):
        if sequence == 0:
            gen.R0, gen.X0 = 1e-20, 0.0
        else:
            gen.R2, gen.X2 = 1e-20, 0.0
        formulation(grid)
