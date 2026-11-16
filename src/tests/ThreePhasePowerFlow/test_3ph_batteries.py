"""Storage injections and U1 control, checked independently through terminal KCL."""
from pathlib import Path
import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.enumerations import GeneratorControlMode, ShuntConnectionType
from tests.ThreePhasePowerFlow.test_3ph_positive_sequence_voltage_control import make_grid, solve, target_voltages
from tests.ThreePhasePowerFlow.test_3ph_common_mode import floating_grid, formulation


def replace_generator(grid: vge.MultiCircuit) -> vge.Battery:
    """Replace the test regulator while retaining its electrical and storage identity.

    :param grid: Existing two-bus voltage-control test network.
    :return: Added battery.
    """
    gen: vge.Generator = grid.generators[1]
    battery: vge.Battery = vge.Battery(P=gen.P, Q=gen.Q, vset=gen.Vset,
        Qmin=gen.Qmin, Qmax=gen.Qmax, control_mode=gen.control_mode,
        r0=gen.R0, x0=gen.X0, r2=gen.R2, x2=gen.X2, Enom=80, soc=0.65)
    battery.conn = gen.conn
    grid.delete_generator(gen)
    grid.add_battery(grid.buses[1], battery)
    return battery


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
@pytest.mark.parametrize('limited', (False, True))
def test_battery_reuses_generator_u1_control(solver: vge.SolverType, limited: bool) -> None:
    """Battery and generator give identical ABC solutions, including Q saturation.

    :param solver: Existing numerical method.
    :param limited: Saturate the common reactive control.
    """
    grid: vge.MultiCircuit = make_grid()
    if limited:
        grid.generators[1].Qmin = -2
        grid.generators[1].Qmax = 2
    else:
        pass
    reference: vge.PowerFlowResults3Ph = solve(grid, solver=solver)
    battery: vge.Battery = replace_generator(grid)
    result: vge.PowerFlowResults3Ph = solve(grid, solver=solver)
    np.testing.assert_allclose(target_voltages(result), target_voltages(reference), atol=1e-9)
    assert battery.Enom == 80 and battery.soc_0 == 0.65
    assert len(grid.batteries) == 1 and len(grid.generators) == 1


@pytest.mark.parametrize('power', (12+3j, -4-1j, 0j))
@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar,
    ShuntConnectionType.FloatingStar, ShuntConnectionType.Delta))
@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_battery_fixed_power_and_passive_sequences(power: complex, connection: ShuntConnectionType,
                                                  sbase: float) -> None:
    """Check charge, discharge and zero setpoints under genuinely unbalanced loading.

    :param power: Positive-sequence injection in MW+jMVAr, as for PF constq.
    :param connection: Physical zero-sequence path.
    :param sbase: System power base in MVA.
    """
    grid: vge.MultiCircuit = make_grid(sbase=sbase)
    battery: vge.Battery = replace_generator(grid)
    battery.control_mode = GeneratorControlMode.Q
    battery.P, battery.Q = power.real, power.imag
    battery.conn = connection
    result: vge.PowerFlowResults3Ph = solve(grid)
    voltage: np.ndarray = target_voltages(result)
    # Reconstruct storage current from the independent line terminal powers and load.
    injection: np.ndarray = np.array((result.St_A[0], result.St_B[0], result.St_C[0]))
    injection += np.array((8+3j, 5+2j, 2+1j))
    a: complex = np.exp(2j*np.pi/3)
    transform: np.ndarray = np.array(((1, 1, 1), (1, a, a*a), (1, a*a, a))) / 3
    v012: np.ndarray = transform @ voltage
    i012: np.ndarray = transform @ (np.conj(injection / voltage) * 3 / sbase)
    np.testing.assert_allclose(v012[1] * i012[1].conj() * sbase, power, atol=1e-6)
    expected_i0: complex = -v012[0] / complex(battery.R0, battery.X0) if (
        connection == ShuntConnectionType.GroundedStar) else 0j
    np.testing.assert_allclose(i012[[0, 2]], (expected_i0,
        -v012[2]/complex(battery.R2, battery.X2)), atol=2e-8)


@pytest.mark.parametrize('mode', (GeneratorControlMode.Q, GeneratorControlMode.V))
def test_balanced_battery_matches_positive_sequence(mode: GeneratorControlMode) -> None:
    """Preserve the balanced power-flow result for both existing control modes.

    :param mode: Fixed Q or voltage control.
    """
    grid: vge.MultiCircuit = make_grid(unbalanced=False)
    battery: vge.Battery = replace_generator(grid)
    battery.control_mode = mode
    battery.Q = 3
    abc: vge.PowerFlowResults3Ph = solve(grid, control_q=False)
    positive: vge.PowerFlowResults = vge.power_flow(grid, options=vge.PowerFlowOptions(
        tolerance=1e-9, control_q=False, retry_with_other_methods=False))
    assert positive.converged
    np.testing.assert_allclose(abc.voltage_A, positive.voltage, atol=1e-8)


def test_colocated_generator_battery_and_inactive_storage() -> None:
    """Split a regulator between the two device classes without duplicating constraints."""
    grid: vge.MultiCircuit = make_grid()
    reference: vge.PowerFlowResults3Ph = solve(grid)
    gen: vge.Generator = grid.generators[1]
    gen.P = 6
    gen.R0 *= 2
    gen.X0 *= 2
    gen.R2 *= 2
    gen.X2 *= 2
    grid.add_battery(grid.buses[1], vge.Battery(P=6, vset=gen.Vset,
        r0=gen.R0, x0=gen.X0, r2=gen.R2, x2=gen.X2))
    grid.add_battery(grid.buses[1], vge.Battery(P=100, vset=1.1, active=False))
    np.testing.assert_allclose(target_voltages(solve(grid)), target_voltages(reference), atol=1e-8)


def test_battery_persistence_profiles_and_islands(tmp_path: Path) -> None:
    """Keep storage data and sequence behaviour through file and numerical operations.

    :param tmp_path: Isolated output directory.
    """
    grid: vge.MultiCircuit = make_grid()
    battery: vge.Battery = replace_generator(grid)
    battery.control_mode = GeneratorControlMode.Q
    battery.P = -4
    battery.Q = -1
    reference: vge.PowerFlowResults3Ph = solve(grid)
    target: Path = tmp_path / 'battery.veragrid'
    vge.save_file(grid, str(target))
    restored: vge.MultiCircuit = vge.open_file(str(target))
    assert len(restored.batteries) == 1 and restored.batteries[0].Enom == 80
    np.testing.assert_allclose(target_voltages(solve(restored)), target_voltages(reference), atol=1e-9)
    grid.create_profiles(2, 1, 'h')
    battery.P_prof.set(np.array((4.0, -4.0)))
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, t_idx=1, fill_three_phase=True)
    copied: NumericalCircuit = nc.copy()
    island: NumericalCircuit = copied.split_into_islands()[0]
    assert island.battery_data.p[0] == -4 and island.battery_data.enom[0] == 80
    assert island.battery_data.r2[0] == battery.R2


@pytest.mark.parametrize('mode', (GeneratorControlMode.Q, GeneratorControlMode.V))
@pytest.mark.parametrize('connection', (ShuntConnectionType.FloatingStar, ShuntConnectionType.GroundedStar))
def test_battery_preserves_physical_common_mode(mode: GeneratorControlMode,
                                              connection: ShuntConnectionType) -> None:
    """Storage blocks a free voltage reference exactly when it provides an earth path.

    :param mode: Fixed power or local U1 regulation.
    :param connection: Floating or earthed source.
    """
    grid: vge.MultiCircuit = floating_grid()
    battery: vge.Battery = vge.Battery(P=2, Q=1, vset=1.0, control_mode=mode,
        r0=0.01, x0=0.08, r2=0.02, x2=0.1)
    battery.conn = connection
    grid.add_battery(grid.buses[2], battery)
    assert len(formulation(grid).common_mode.phases) == int(connection == ShuntConnectionType.FloatingStar)
    assert solve(grid).converged


def test_colocated_fixed_batteries_accumulate() -> None:
    """Parallel fixed-PQ batteries add their currents without overwriting each other."""
    grid: vge.MultiCircuit = make_grid()
    battery: vge.Battery = replace_generator(grid)
    battery.control_mode = GeneratorControlMode.Q
    battery.Q = 3
    reference: vge.PowerFlowResults3Ph = solve(grid)
    battery.P /= 2
    battery.Q /= 2
    battery.R0 *= 2
    battery.X0 *= 2
    battery.R2 *= 2
    battery.X2 *= 2
    grid.add_battery(grid.buses[1], vge.Battery(P=battery.P, Q=battery.Q,
        control_mode=GeneratorControlMode.Q, r0=battery.R0, x0=battery.X0,
        r2=battery.R2, x2=battery.X2))
    grid.add_battery(grid.buses[1], vge.Battery(P=100, Q=50, control_mode=GeneratorControlMode.Q, active=False))
    np.testing.assert_allclose(target_voltages(solve(grid)), target_voltages(reference), atol=1e-8)
