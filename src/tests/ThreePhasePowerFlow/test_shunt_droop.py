"""Physical SVC response using the existing Q-U1 droop law."""
from pathlib import Path

import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.enumerations import ShuntControlMode, ShuntConnectionType
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.static_generator_droop import StaticGeneratorDroop
from tests.ThreePhasePowerFlow.test_static_generator_droop import make_grid, solve


def make_svc_grid(sbase=100.0, unbalanced=False, connection=ShuntConnectionType.Delta):
    """Replace the test feeder's ideal current source with a physical susceptance."""
    grid = make_grid(sbase, unbalanced)
    grid.static_generators.clear()
    shunt = vge.ControllableShunt(name='Physical SVC', control_mode=ShuntControlMode.QVDroop,
                                 Snom=80.0, droop=3.0, vset=1.01, G=0.0, B=123.0)
    shunt.conn = connection
    grid.add_controllable_shunt(grid.buses[1], shunt)
    return grid


@pytest.mark.parametrize('sbase', (25.0, 100.0))
@pytest.mark.parametrize('connection', (ShuntConnectionType.Delta, ShuntConnectionType.GroundedStar,
                                       ShuntConnectionType.FloatingStar))
def test_unbalanced_svc_power_and_sequence_currents(sbase, connection):
    """Recover the SVC from solved KCL and independently check B, I0, I2 and total Q."""
    grid = make_svc_grid(sbase, True, connection)
    result = vge.power_flow3ph(grid, vge.PowerFlowOptions(tolerance=1e-10, max_iter=100,
                                                       retry_with_other_methods=False))
    assert result.converged
    voltage = np.array((result.voltage_A[1], result.voltage_B[1], result.voltage_C[1]))
    power = np.array((result.Sbus_A[1], result.Sbus_B[1], result.Sbus_C[1])) + (8+3j, 5+2j, 2+1j)
    current = np.conj(power / voltage) * 3 / sbase
    a = np.exp(2j*np.pi/3)
    transform = np.array(((1, 1, 1), (1, a, a*a), (1, a*a, a))) / 3
    v012 = transform @ voltage
    q = 80 / 0.03 * (1.01 - np.clip(abs(v012[1]), 0.9, 1.1))
    np.testing.assert_allclose(power.sum(), 1j*q, atol=1e-6)
    connected = voltage if connection == ShuntConnectionType.GroundedStar else voltage - voltage.mean()
    b = q / sbase / np.mean(abs(connected)**2)
    np.testing.assert_allclose(current, -1j*b*connected, atol=1e-8)
    np.testing.assert_allclose((transform @ current)[2], -1j*b*v012[2], atol=1e-8)
    assert abs((transform @ current)[2]) > 1e-5
    if connection != ShuntConnectionType.GroundedStar:
        np.testing.assert_allclose(current.sum(), 0, atol=1e-8)


@pytest.mark.parametrize('sbase', (25.0, 100.0))
@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_balanced_svc_preserves_existing_droop(sbase, solver):
    """The physical model must reduce to the established VSC-equivalent source in balance."""
    grid = make_grid(sbase)
    grid.static_generators[0].P = 0
    grid.static_generators[0].Q = 0
    reference = solve(grid, solver)
    physical = make_svc_grid(sbase)
    np.testing.assert_allclose(solve(physical, solver).voltage, reference.voltage, atol=1e-8)
    abc = vge.power_flow3ph(physical, vge.PowerFlowOptions(solver_type=solver, tolerance=1e-9,
                                                        max_iter=100, retry_with_other_methods=False))
    assert abc.converged
    np.testing.assert_allclose(abc.voltage_A, reference.voltage, atol=1e-8)


def test_svc_roundtrip_profiles_units_and_parallel_devices(tmp_path: Path):
    """Retain controller data through native files, island slicing, copying and profiles."""
    grid = make_svc_grid()
    reference = solve(grid)
    first = grid.controllable_shunts[0]
    first.Snom = 40000.0
    first.use_kw = True
    first.Vset_prof = np.array((1.02,))
    second = vge.ControllableShunt(Snom=40, droop=3, vset=1.01, G=0,
                                  control_mode=ShuntControlMode.QVDroop)
    second.conn = ShuntConnectionType.Delta
    grid.add_controllable_shunt(grid.buses[1], second)
    grid.add_controllable_shunt(grid.buses[1], vge.ControllableShunt(
        active=False, Snom=0, droop=0, control_mode=ShuntControlMode.QVDroop))
    filename = str(tmp_path/'svc.veragrid')
    vge.FileSave(grid, filename).save()
    restored = vge.FileOpen(filename).open()
    np.testing.assert_allclose(solve(restored).voltage, reference.voltage, atol=1e-8)
    nc = compile_numerical_circuit_at(grid, t_idx=0, fill_three_phase=True)
    control = StaticGeneratorDroop(nc.split_into_islands()[0])
    np.testing.assert_allclose(control.snom, (40, 40))
    np.testing.assert_allclose(control.vset, (1.02, 1.01))
    np.testing.assert_allclose(nc.shunt_data.copy().q_droop, nc.shunt_data.q_droop)
    np.testing.assert_allclose(nc.shunt_data.copy().q_droop_snom, nc.shunt_data.q_droop_snom)


@pytest.mark.parametrize('invalid', ('rating', 'droop', 'remote', 'dc', 'phase', 'clamps'))
def test_invalid_svc_has_specific_diagnostic(invalid):
    """Reject unsupported configurations rather than silently changing their model."""
    grid = make_svc_grid()
    unit = grid.controllable_shunts[0]
    if invalid == 'rating':
        unit.Snom = 0
    elif invalid == 'droop':
        unit.droop = 0
    elif invalid == 'remote':
        unit.control_bus = grid.buses[0]
    elif invalid == 'dc':
        unit.bus.is_dc = True
    elif invalid == 'phase':
        unit.phA = False
    else:
        unit.Vmin = 1.1
    with pytest.raises(ValueError, match='Physical SVC'):
        compile_numerical_circuit_at(grid)
