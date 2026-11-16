"""Stepped banks must stamp their own NABC block and their actual connected admittance."""
import numpy as np
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.enumerations import ShuntConnectionType, ShuntControlMode


@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar,
    ShuntConnectionType.Delta, ShuntConnectionType.FloatingStar))
@pytest.mark.parametrize('step', (0, 1, 2))
@pytest.mark.parametrize('active', (False, True))
def test_bank_currents_and_adjacent_blocks(connection: ShuntConnectionType, step: int, active: bool) -> None:
    """Verify phase currents and I0 independently, including an entirely disconnected bank."""
    grid = vge.MultiCircuit()
    bus = grid.add_bus(vge.Bus(is_slack=True))
    grid.add_shunt(bus, vge.Shunt(G1=0.3, G2=0.4, G3=0.5, B1=0, B2=0, B3=0))
    before = compile_numerical_circuit_at(grid, fill_three_phase=True).shunt_data.Y3_star.copy()
    bank = vge.ControllableShunt(number_of_steps=2, step=step, g_per_step=600, b_per_step=3000,
        control_mode=ShuntControlMode.Discrete, active=active)
    bank.conn = connection
    bank.use_kw = True
    grid.add_controllable_shunt(bus, bank)
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    np.testing.assert_array_equal(nc.shunt_data.Y3_star[:4], before)
    block = nc.shunt_data.Y3_star[4:8]
    np.testing.assert_array_equal(block[0], 0)
    np.testing.assert_array_equal(block[:, 0], 0)
    voltage = np.array((1.01+0.03j, -0.45-0.82j, -0.51+0.87j))
    effective = voltage if connection == ShuntConnectionType.GroundedStar else voltage - voltage.mean()
    expected = effective * (0.6+3j) * step * active / 3
    np.testing.assert_allclose(block[1:, 1:] @ voltage, expected, atol=1e-14)
    if step == 0 or not active:
        np.testing.assert_array_equal(block, 0)


@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar, ShuntConnectionType.Delta))
def test_locked_bank_retains_explicit_phase_admittances(connection: ShuntConnectionType) -> None:
    """Keep the existing per-phase locked-shunt interface while fixing indexing and units."""
    grid = vge.MultiCircuit()
    bus = grid.add_bus(vge.Bus(is_slack=True))
    bank = vge.ControllableShunt(control_mode=ShuntControlMode.Locked,
        G1=300, G2=600, G3=900, B1=0, B2=0, B3=0)
    bank.conn, bank.use_kw = connection, True
    grid.add_controllable_shunt(bus, bank)
    block = compile_numerical_circuit_at(grid, fill_three_phase=True).shunt_data.Y3_star[1:4, 1:4]
    voltage = np.array((1, -0.4-0.8j, -0.6+0.9j))
    if connection == ShuntConnectionType.GroundedStar:
        expected = np.array((0.3, 0.6, 0.9)) * voltage
    else:
        a, b, c = voltage
        expected = np.array((0.3*(a-b)+0.9*(a-c), 0.6*(b-c)+0.3*(b-a),
                             0.9*(c-a)+0.6*(c-b))) / 3
    np.testing.assert_allclose(block @ voltage, expected, atol=1e-14)
