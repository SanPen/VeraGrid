# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Synchronous slack U1 references with physical zero/negative-sequence response."""
import numpy as np
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.enumerations import ExternalGridMode, GeneratorType, ShuntConnectionType


def sequence_transform() -> np.ndarray:
    """Return the conventional ABC-to-012 transform, independently of the solver."""
    a = np.exp(2j*np.pi/3)
    return np.array(((1, 1, 1), (1, a, a*a), (1, a*a, a))) / 3


def make_grid(sbase: float = 100.0, balanced: bool = False,
              connection: ShuntConnectionType = ShuntConnectionType.GroundedStar) -> vge.MultiCircuit:
    """Create a linear load circuit with explicitly supplied synchronous sequence data.

    :param sbase: Network MVA base; impedances scale to preserve the physical circuit.
    :param balanced: Equal phase conductances or unequal conductances exciting U0/U2.
    :param connection: Physical zero-sequence connection of the slack generator.
    """
    grid = vge.MultiCircuit(Sbase=sbase)
    source = grid.add_bus(vge.Bus(name='Source', Vnom=20, is_slack=True))
    target = grid.add_bus(vge.Bus(name='Load', Vnom=20))
    scale = sbase / 100
    generator = vge.Generator(name='Synchronous slack', vset=1.03, tpe=GeneratorType.Synchronous,
        r0=0.01*scale, x0=0.08*scale, r2=0.02*scale, x2=0.10*scale)
    generator.conn = connection
    grid.add_generator(source, generator)
    # The existing sequence-derived line model uses Z2=Z1; the machine keeps its own Z2.
    grid.add_line(vge.Line(bus_from=source, bus_to=target, r=0.02*scale, x=0.08*scale,
        r0=0.04*scale, x0=0.16*scale, r2=0.02*scale, x2=0.08*scale, b=0, b0=0, b2=0))
    conductance = (10/3, 10/3, 10/3) if balanced else (6, 3, 1)
    grid.add_load(target, vge.Load(G=10, G1=conductance[0], G2=conductance[1], G3=conductance[2]))
    return grid


def options(solver: vge.SolverType = vge.SolverType.NR) -> vge.PowerFlowOptions:
    """Solve without numerical fallback or generator reactive-limit switching."""
    return vge.PowerFlowOptions(solver_type=solver, tolerance=1e-10, max_iter=60,
        control_q=False, retry_with_other_methods=False)


def voltages(result) -> np.ndarray:
    """Collect physical bus ABC phasors in result order."""
    return np.column_stack((result.voltage_A, result.voltage_B, result.voltage_C))


def linear_reference(grid: vge.MultiCircuit, reference: complex | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Solve independent complex nodal equations with the generator's sequence boundary laws.

    :param grid: Two-bus constant-impedance fixture.
    :param reference: Complex U1 reference, defaulting to the generator voltage setpoint at zero angle.
    :return: Source/load ABC voltages and independent line series admittance.
    """
    generator, line, load = grid.generators[0], grid.lines[0], grid.loads[0]
    transform = sequence_transform()
    series = np.linalg.inv(transform) @ np.diag(1 / np.array((
        complex(line.R0, line.X0), complex(line.R, line.X), complex(line.R2, line.X2)))) @ transform
    load_y = np.diag(np.array((load.G1, load.G2, load.G3)) * 3 / grid.Sbase)
    matrix = np.zeros((6, 6), dtype=complex)
    rhs = np.zeros(6, dtype=complex)
    matrix[3:, :3], matrix[3:, 3:] = -series, series + load_y
    matrix[:3, :3], matrix[:3, 3:] = transform @ series, -transform @ series
    matrix[1, :3], matrix[1, 3:] = transform[1], 0
    rhs[1] = generator.Vset if reference is None else reference
    if generator.conn == ShuntConnectionType.GroundedStar:
        z0 = complex(generator.R0, generator.X0)
        if z0 == 0j:
            matrix[0, :3], matrix[0, 3:] = transform[0], 0
        else:
            matrix[0, :3] += transform[0] / z0
    matrix[2, :3] += transform[2] / complex(generator.R2, generator.X2)
    return np.linalg.solve(matrix, rhs).reshape(2, 3), series


@pytest.mark.parametrize('sbase', (25.0, 100.0))
@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar,
                                       ShuntConnectionType.FloatingStar, ShuntConnectionType.Delta))
@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM))
def test_synchronous_slack_matches_independent_sequence_boundary(sbase, connection, solver) -> None:
    """Fix only U1 while satisfying both passive sequence laws and all load-bus KCL."""
    grid = make_grid(sbase=sbase, connection=connection)
    generator = grid.generators[0]
    expected, series = linear_reference(grid)
    result = vge.power_flow3ph(grid, options(solver))
    assert result.converged
    actual = voltages(result)
    np.testing.assert_allclose(actual, expected, atol=2e-8, rtol=0)
    current = series @ (actual[0] - actual[1])
    load_y = np.array((6, 3, 1)) * 3 / sbase
    np.testing.assert_allclose(current, load_y * actual[1], atol=2e-9, rtol=0)
    transform = sequence_transform()
    u012, i012 = transform @ actual[0], transform @ current
    np.testing.assert_allclose(u012[1], generator.Vset, atol=1e-9, rtol=0)
    assert abs(u012[0]) > 1e-4 and abs(u012[2]) > 1e-4
    assert np.ptp(abs(actual[0])) > 1e-3
    expected_i0 = (-u012[0] / complex(generator.R0, generator.X0)
                   if connection == ShuntConnectionType.GroundedStar else 0j)
    np.testing.assert_allclose(i012[[0, 2]],
        (expected_i0, -u012[2] / complex(generator.R2, generator.X2)), atol=2e-9, rtol=0)
    power = actual[0] * current.conj() * sbase / 3
    np.testing.assert_allclose(np.array((result.Sf_A[0], result.Sf_B[0], result.Sf_C[0])),
                               power, atol=1e-7, rtol=0)
    # Slack active/reactive powers are recovered from KCL, not forced to the zero schedule.
    assert power.real.sum() > 5


def test_synchronous_slack_supplies_unbalanced_constant_power_load() -> None:
    """Recover the slack injection from nonlinear load and network KCL, including losses."""
    grid = make_grid()
    generator = grid.generators[0]
    _, series = linear_reference(grid)
    grid.loads.clear()
    grid.add_load(grid.buses[1], vge.Load(P=15, Q=6, P1=8, P2=5, P3=2, Q1=3, Q2=2, Q3=1))
    result = vge.power_flow3ph(grid, options())
    assert result.converged
    actual = voltages(result)
    current = series @ (actual[0] - actual[1])
    np.testing.assert_allclose(current,
        np.conj(np.array((8+3j, 5+2j, 2+1j)) / actual[1]) * 3 / grid.Sbase, atol=2e-9, rtol=0)
    transform = sequence_transform()
    u012, i012 = transform @ actual[0], transform @ current
    np.testing.assert_allclose(u012[1], generator.Vset, atol=1e-9, rtol=0)
    np.testing.assert_allclose(i012[[0, 2]],
        (-u012[0] / complex(generator.R0, generator.X0),
         -u012[2] / complex(generator.R2, generator.X2)), atol=2e-9, rtol=0)
    source_power = np.sum(actual[0] * current.conj()) * grid.Sbase / 3
    assert source_power.real > 15 and source_power.imag > 6


def test_synchronous_slack_preserves_complex_u1_reference() -> None:
    """The angle reference belongs to U1, not to one unbalanced terminal phase."""
    grid = make_grid()
    angle = 0.17
    grid.buses[0].Va0 = angle
    reference = grid.generators[0].Vset * np.exp(1j*angle)
    expected, _ = linear_reference(grid, reference=reference)
    pf_options = options()
    pf_options.use_stored_guess = True
    result = vge.power_flow3ph(grid, pf_options)
    assert result.converged
    np.testing.assert_allclose(voltages(result), expected, atol=2e-8, rtol=0)
    np.testing.assert_allclose(sequence_transform()[1] @ voltages(result)[0], reference,
                               atol=1e-9, rtol=0)


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_ideal_z0_slack_keeps_u0_constraint_and_u1_reference(solver) -> None:
    """An ideal zero-sequence source carries I0 while its finite Z2 still responds to U2."""
    grid = make_grid()
    generator = grid.generators[0]
    generator.R0 = generator.X0 = 0
    expected, series = linear_reference(grid)
    result = vge.power_flow3ph(grid, options(solver))
    assert result.converged
    actual = voltages(result)
    np.testing.assert_allclose(actual, expected, atol=2e-8, rtol=0)
    transform = sequence_transform()
    u012 = transform @ actual[0]
    i012 = transform @ (series @ (actual[0] - actual[1]))
    np.testing.assert_allclose(u012[:2], (0j, generator.Vset), atol=1e-9, rtol=0)
    assert abs(i012[0]) > 1e-3 and abs(u012[2]) > 1e-4
    np.testing.assert_allclose(i012[2], -u012[2] / complex(generator.R2, generator.X2), atol=2e-9)
    assert generator.R0 == generator.X0 == 0


@pytest.mark.parametrize('connection', (ShuntConnectionType.Delta, ShuntConnectionType.FloatingStar))
def test_blocked_slack_zero_sequence_is_not_an_ideal_ground(connection) -> None:
    """A zero stored Z0 must remain disconnected when the machine connection blocks I0."""
    grid = make_grid(connection=connection)
    grid.generators[0].R0 = grid.generators[0].X0 = 0
    expected, series = linear_reference(grid)
    result = vge.power_flow3ph(grid, options())
    assert result.converged
    actual = voltages(result)
    np.testing.assert_allclose(actual, expected, atol=2e-8, rtol=0)
    assert abs(np.mean(actual[0])) > 1e-3
    np.testing.assert_allclose(np.mean(series @ (actual[0] - actual[1])), 0, atol=2e-9)


@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_balanced_synchronous_slack_matches_positive_sequence(sbase) -> None:
    """Retain the existing balanced result, including complex voltages and line powers."""
    grid = make_grid(sbase=sbase, balanced=True)
    abc = vge.power_flow3ph(grid, options())
    positive = vge.power_flow(grid, options())
    assert abc.converged and positive.converged
    rotation = np.exp(-2j*np.pi*np.arange(3)/3)
    np.testing.assert_allclose(voltages(abc), positive.voltage[:, None]*rotation, atol=1e-9, rtol=0)
    np.testing.assert_allclose(abc.Sf_A + abc.Sf_B + abc.Sf_C, positive.Sf, atol=1e-7, rtol=0)


@pytest.mark.parametrize('kind', ('bare_bus', 'external_grid', 'legacy_generator'))
def test_existing_fixed_abc_slack_remains_fixed(kind) -> None:
    """Do not reinterpret a fixed external boundary or a legacy generator's missing sequence data."""
    grid = make_grid()
    grid.generators.clear()
    reference = 1.0
    if kind == 'external_grid':
        reference = 1.03
        grid.add_external_grid(grid.buses[0], vge.ExternalGrid(mode=ExternalGridMode.VD, Vm=reference))
    elif kind == 'legacy_generator':
        reference = 1.03
        grid.add_generator(grid.buses[0], vge.Generator(vset=reference))
    result = vge.power_flow3ph(grid, options())
    assert result.converged
    np.testing.assert_allclose(voltages(result)[0],
                               reference*np.exp(-2j*np.pi*np.arange(3)/3), atol=1e-12, rtol=0)


@pytest.mark.parametrize('boundary', ('external_grid', 'legacy_generator'))
def test_colocated_ideal_boundary_keeps_fixed_abc_boundary(boundary) -> None:
    """An existing ideal source still fixes ABC when a physical machine shares its bus."""
    grid = make_grid()
    _, series = linear_reference(grid)
    source = grid.generators[0].Vset * np.exp(-2j*np.pi*np.arange(3)/3)
    load_y = np.diag(np.array((6, 3, 1)) * 3 / grid.Sbase)
    expected = np.vstack((source, np.linalg.solve(series + load_y, series @ source)))
    if boundary == 'external_grid':
        grid.add_external_grid(grid.buses[0], vge.ExternalGrid(mode=ExternalGridMode.VD, Vm=1.03))
    else:
        grid.add_generator(grid.buses[0], vge.Generator(vset=1.03))
    result = vge.power_flow3ph(grid, options())
    assert result.converged
    np.testing.assert_allclose(voltages(result), expected, atol=2e-9, rtol=0)


@pytest.mark.parametrize('r2', (0.0, float('nan')))
def test_invalid_physical_slack_z2_is_rejected(r2: float) -> None:
    """Reject invalid sequence data at assignment or physical compilation.

    :param r2: Invalid negative-sequence resistance.
    :return: None.
    """
    grid: vge.MultiCircuit = make_grid()
    # The devel value contract rejects NaN before the physical model is compiled.
    with pytest.raises(ValueError, match=r'Z2 must be finite and nonzero|Non-finite value rejected for Generator\.R2'):
        grid.generators[0].R2, grid.generators[0].X2 = r2, 0
        vge.power_flow3ph(grid, options())


@pytest.mark.parametrize('ideal_zero', (False, True))
def test_colocated_synchronous_slack_units_share_reference(ideal_zero) -> None:
    """Parallel identical machines preserve their aggregate admittance and slack solution."""
    grid = make_grid()
    first = grid.generators[0]
    if ideal_zero:
        first.R0 = first.X0 = 0
    baseline = vge.power_flow3ph(grid, options())
    assert baseline.converged
    first.R0 *= 2
    first.X0 *= 2
    first.R2 *= 2
    first.X2 *= 2
    grid.add_generator(grid.buses[0], vge.Generator(vset=first.Vset,
        r0=first.R0, x0=first.X0, r2=first.R2, x2=first.X2))
    grid.add_generator(grid.buses[0], vge.Generator(active=False, vset=1.4, r0=0, x0=0, r2=0, x2=0))
    parallel = vge.power_flow3ph(grid, options())
    assert parallel.converged
    np.testing.assert_allclose(voltages(parallel), voltages(baseline), atol=2e-8, rtol=0)


def test_synchronous_slack_island_references_are_local() -> None:
    """Keep each island's physical source and voltage reference after bus reordering."""
    grid = make_grid()
    other = make_grid(connection=ShuntConnectionType.FloatingStar)
    other.generators[0].Vset = 0.98
    expected = {}
    for circuit in (grid, other):
        reference, _ = linear_reference(circuit)
        expected.update((bus.idtag, row) for bus, row in zip(circuit.buses, reference))
    for bus in other.buses:
        grid.add_bus(bus)
    for line in other.lines:
        grid.add_line(line)
    for generator in other.generators:
        grid.add_generator(generator.bus, generator)
    for load in other.loads:
        grid.add_load(load.bus, load)
    grid.buses.reverse()
    result = vge.power_flow3ph(grid, options())
    assert result.converged
    for bus, actual in zip(grid.buses, voltages(result)):
        np.testing.assert_allclose(actual, expected[bus.idtag], atol=2e-8, rtol=0)
