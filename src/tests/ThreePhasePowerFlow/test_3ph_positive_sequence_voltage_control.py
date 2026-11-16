# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.DataStructures.generator_data import GeneratorData
from VeraGridEngine.IO.veragrid.pack_unpack import parse_object_type_from_json
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.pf_basic_formulation_3ph import (
    PfBasicFormulation3Ph, compute_ybus, expand3ph, expandVoltage3ph)
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.positive_sequence_control import PositiveSequenceControl
from VeraGridEngine.enumerations import GeneratorControlMode, ShuntConnectionType


def make_grid(unbalanced: bool = True, sbase: float = 100.0) -> vge.MultiCircuit:
    """Create a public two-bus example with a load and a colocated PV generator.

    :param unbalanced: Whether to distribute the load unequally across phases.
    :param sbase: Network power base in MVA.
    :return: Grid for voltage-control regression tests.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit(Sbase=sbase)
    source: vge.Bus = grid.add_bus(vge.Bus(name='Slack', Vnom=20.0, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(name='PV', Vnom=20.0))
    grid.add_generator(bus=source, api_obj=vge.Generator(r0=0.01, x0=0.08, r2=0.02, x2=0.10))
    # U1 control needs physical sequence data, not Generator's legacy SC placeholders.
    grid.add_generator(bus=target, api_obj=vge.Generator(
        P=12.0, vset=1.01, r0=0.01, x0=0.08, r2=0.02, x2=0.10))
    grid.add_line(vge.Line(bus_from=source, bus_to=target, r=0.02, x=0.08, r0=0.04, x0=0.16))
    if unbalanced:
        grid.add_load(bus=target, api_obj=vge.Load(P=15.0, Q=6.0, P1=8.0, P2=5.0, P3=2.0,
                                                 Q1=3.0, Q2=2.0, Q3=1.0))
    else:
        grid.add_load(bus=target, api_obj=vge.Load(P=15.0, Q=6.0))
    return grid


def solve(grid: vge.MultiCircuit, control_q: bool = True,
          solver: vge.SolverType = vge.SolverType.NR) -> vge.PowerFlowResults3Ph:
    """Solve the example with strict tolerances and no solver fallback.

    :param grid: Network to solve.
    :param control_q: Enable reactive capability limits.
    :param solver: Numerical method to exercise.
    :return: Converged three-phase results.
    """
    results: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid=grid, options=vge.PowerFlowOptions(
        solver_type=solver, tolerance=1e-9, max_iter=100, control_q=control_q,
        retry_with_other_methods=False))
    assert results.converged
    return results


def target_voltages(results: vge.PowerFlowResults3Ph) -> np.ndarray:
    """Collect target-bus ABC phasors.

    :param results: Three-phase solution.
    :return: ABC voltage vector.
    """
    return np.array((results.voltage_A[1], results.voltage_B[1], results.voltage_C[1]))


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_u1_controls_voltage_with_sequence_response(sbase: float, solver: vge.SolverType) -> None:
    """Regulate U1 under imbalance while satisfying phase KCL and total active power.

    :param sbase: Non-unit power base detects incorrect Q/current scaling.
    :param solver: Newton or Levenberg-Marquardt.
    """
    grid: vge.MultiCircuit = make_grid(sbase=sbase)
    results: vge.PowerFlowResults3Ph = solve(grid, solver=solver)
    voltage: np.ndarray = target_voltages(results)
    a: complex = np.exp(2j * np.pi / 3)
    v1: complex = (voltage[0] + a * voltage[1] + a * a * voltage[2]) / 3
    assert abs(abs(v1) - 1.01) < 1e-8
    assert np.ptp(np.abs(voltage)) > 1e-3

    # Reconstruct the injection from network results plus the known phase load.
    power: np.ndarray = np.array((results.Sbus_A[1], results.Sbus_B[1], results.Sbus_C[1]))
    power += np.array((8 + 3j, 5 + 2j, 2 + 1j))
    current: np.ndarray = np.conj(power / voltage) * 3.0 / sbase
    assert abs(np.sum(power).real - 12.0) < 1e-6
    transform: np.ndarray = np.array(((1, 1, 1), (1, a, a*a), (1, a*a, a))) / 3
    v012: np.ndarray = transform @ voltage
    i012: np.ndarray = transform @ current
    np.testing.assert_allclose(i012[[0, 2]], (-v012[0] / (0.01 + 0.08j),
                                          -v012[2] / (0.02 + 0.10j)), atol=1e-8)


def test_balanced_u1_matches_positive_sequence() -> None:
    """Recover the existing balanced solution, including complex angles and powers."""
    grid: vge.MultiCircuit = make_grid(unbalanced=False)
    sequence: vge.PowerFlowResults3Ph = solve(grid)
    balanced: vge.PowerFlowResults = vge.power_flow(grid=grid, options=vge.PowerFlowOptions(
        tolerance=1e-9, control_q=False, retry_with_other_methods=False))
    assert balanced.converged
    np.testing.assert_allclose(sequence.voltage_A, balanced.voltage, atol=1e-7)
    np.testing.assert_allclose(sequence.voltage_B, balanced.voltage * np.exp(-2j * np.pi / 3), atol=1e-7)
    np.testing.assert_allclose(sequence.voltage_C, balanced.voltage * np.exp(2j * np.pi / 3), atol=1e-7)


def test_generator_automatically_regulates_u1() -> None:
    """A voltage-controlled generator regulates U1 without a phase/sequence selector."""
    grid: vge.MultiCircuit = make_grid()
    voltage: np.ndarray = target_voltages(solve(grid))
    a: complex = np.exp(2j * np.pi / 3)
    assert abs(abs(voltage @ np.array((1, a, a*a)) / 3) - 1.01) < 1e-9
    assert np.ptp(np.abs(voltage)) > 1e-3
    assert 'voltage_control_mode' not in grid.generators[1].registered_properties


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM))
@pytest.mark.parametrize('vset,limit', ((1.01, 2.0), (0.97, -2.0)))
def test_u1_reactive_limits(vset: float, limit: float, solver: vge.SolverType) -> None:
    """Release U1 regulation at either total Q limit, unless limits are disabled.

    :param vset: Voltage request driving the generator beyond one Q bound.
    :param limit: Expected saturated total MVAr.
    :param solver: Numerical method used for switching to fixed Q.
    """
    grid: vge.MultiCircuit = make_grid()
    grid.generators[1].Vset = vset
    grid.generators[1].Qmin = -2.0
    grid.generators[1].Qmax = 2.0
    limited: vge.PowerFlowResults3Ph = solve(grid, solver=solver)
    total: complex = limited.Sbus_A[1] + limited.Sbus_B[1] + limited.Sbus_C[1] + 15 + 6j
    assert abs(total.imag - limit) < 1e-6
    assert abs(total.real - 12.0) < 1e-6
    unlimited: vge.PowerFlowResults3Ph = solve(grid, control_q=False, solver=solver)
    a: complex = np.exp(2j * np.pi / 3)
    assert abs(abs(target_voltages(unlimited) @ np.array((1, a, a * a)) / 3) - vset) < 1e-8


def test_colocated_u1_regulators_and_offline_units() -> None:
    """Splitting one regulator into parallel units preserves its solution and Q limit."""
    grid: vge.MultiCircuit = make_grid()
    grid.generators[1].Qmax = 2.0
    reference: vge.PowerFlowResults3Ph = solve(grid)
    grid.generators[1].P = 6.0
    grid.generators[1].Qmax = 1.0
    grid.generators[1].R0, grid.generators[1].X0 = 0.02, 0.16
    grid.generators[1].R2, grid.generators[1].X2 = 0.04, 0.20
    grid.add_generator(bus=grid.buses[1], api_obj=vge.Generator(
        P=6.0, Qmax=1.0, vset=1.01, r0=0.02, x0=0.16, r2=0.04, x2=0.20))
    grid.add_generator(bus=grid.buses[1], api_obj=vge.Generator(P=1000.0, active=False))
    parallel: vge.PowerFlowResults3Ph = solve(grid)
    np.testing.assert_allclose(target_voltages(reference), target_voltages(parallel), atol=1e-8)


def test_voltage_control_compilation_copy_slice_and_file_roundtrip(tmp_path: Path) -> None:
    """Preserve PV operation through island extraction and native file serialisation.

    :param tmp_path: Isolated output directory.
    """
    grid: vge.MultiCircuit = make_grid()
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)
    np.testing.assert_array_equal(numerical.generator_data.control_mode_int, (1, 1))
    np.testing.assert_array_equal(numerical.generator_data.copy().control_mode_int, (1, 1))
    sliced: GeneratorData = numerical.generator_data.slice(np.array((1,)), np.array((1,)), np.array((-1, 0)))
    np.testing.assert_array_equal(sliced.control_mode_int, (1,))
    path: str = str(tmp_path / 'u1.veragrid')
    vge.save_file(grid=grid, filename=path)
    restored: vge.MultiCircuit = vge.open_file(path)
    assert restored.generators[1].control_mode == GeneratorControlMode.V
    np.testing.assert_allclose(target_voltages(solve(restored)), target_voltages(solve(grid)), atol=1e-8)


def test_u1_with_colocated_fixed_power_generators() -> None:
    """Sum colocated PQ units without discarding their currents or regulating their Q."""
    grid: vge.MultiCircuit = make_grid()
    grid.generators[1].Qmax = 2.0
    grid.add_generator(bus=grid.buses[1], api_obj=vge.Generator(P=3.0, Q=1.0,
        control_mode=GeneratorControlMode.Q, r0=0.01, x0=0.08, r2=0.02, x2=0.10))
    grid.add_generator(bus=grid.buses[1], api_obj=vge.Generator(P=4.0, Q=2.0,
        control_mode=GeneratorControlMode.Q, r0=0.01, x0=0.08, r2=0.02, x2=0.10))
    results: vge.PowerFlowResults3Ph = solve(grid)
    total: complex = results.Sbus_A[1] + results.Sbus_B[1] + results.Sbus_C[1] + 15 + 6j
    np.testing.assert_allclose(total, 19 + 5j, atol=1e-6)


@pytest.mark.parametrize('old_selector', ('Per phase', 'Positive sequence'))
def test_legacy_voltage_selector_does_not_override_u1(old_selector: str) -> None:
    """Load either former selector value while applying the same physical U1 model.

    :param old_selector: Retired voltage-control setting stored in an older native file.
    """
    grid: vge.MultiCircuit = make_grid()
    reference: vge.PowerFlowResults3Ph = solve(grid)
    # Exercise the real native deserializer with the former field still present.
    entry: dict = dict(idtag='legacy-pv', name='Legacy PV', P=12.0, Vset=1.01,
                       R0=0.01, X0=0.08, R2=0.02, X2=0.10, voltage_control_mode=old_selector)
    devices, _ = parse_object_type_from_json(
        template_elm=vge.Generator(), data_list=list((entry,)), elements_dict_by_type=dict(),
        time_profile=None, block_parser=None, logger=vge.Logger())
    assert isinstance(devices[0], vge.Generator)
    grid.generators[1] = devices[0]
    grid.generators[1].bus = grid.buses[1]
    assert grid.generators[1].control_mode == GeneratorControlMode.V
    assert 'voltage_control_mode' not in grid.generators[1].registered_properties
    np.testing.assert_allclose(target_voltages(solve(grid)), target_voltages(reference), atol=1e-9)


@pytest.mark.parametrize('conflict', ('setpoint', 'remote', 'missing_phase'))
def test_u1_rejects_incompatible_controls(conflict: str) -> None:
    """Reject ambiguous voltage equations instead of silently changing their meaning.

    :param conflict: Unsupported combination to exercise.
    """
    grid: vge.MultiCircuit = make_grid()
    if conflict == 'setpoint':
        grid.add_generator(bus=grid.buses[1], api_obj=vge.Generator(vset=1.02))
    elif conflict == 'remote':
        grid.generators[1].control_bus = grid.buses[0]
    else:
        grid.lines[0].ys.phC = False
        grid.lines[0].ysh.phC = False
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)
    bus_lookup: np.ndarray = compute_ybus(numerical)[5]
    message = 'requires all three terminal phases' if conflict == 'missing_phase' else 'Positive-sequence'
    with pytest.raises(ValueError, match=message):
        PositiveSequenceControl(numerical, bus_lookup)


def test_u1_uses_profile_setpoints_and_limits() -> None:
    """Compile U1 groups from profile values, ignoring an offline unit at that step."""
    grid: vge.MultiCircuit = make_grid()
    grid.generators[1].P_prof = np.array((7.0,))
    grid.generators[1].Vset_prof = np.array((1.025,))
    grid.generators[1].Qmin_prof = np.array((-3.0,))
    grid.generators[1].Qmax_prof = np.array((4.0,))
    offline: vge.Generator = vge.Generator(P=1000.0)
    offline.active_prof = np.array((False,))
    grid.add_generator(bus=grid.buses[1], api_obj=offline)
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, t_idx=0, fill_three_phase=True)
    controls: PositiveSequenceControl = PositiveSequenceControl(numerical, compute_ybus(numerical)[5])
    np.testing.assert_allclose(controls.p, (0.07,))
    np.testing.assert_allclose(controls.vset, (1.025,))
    np.testing.assert_allclose(controls.qmin, (-0.03,))
    np.testing.assert_allclose(controls.qmax, (0.04,))
    np.testing.assert_array_equal(controls.regular_idx, np.array((), dtype=int))
    np.testing.assert_array_equal(controls.slack_bus_idx, (0,))


def test_u1_residual_paths_and_jacobian_agree() -> None:
    """Keep Newton updates, line search and diagnostic Jacobians on the same equations."""
    grid: vge.MultiCircuit = make_grid()
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)
    qmax: np.ndarray
    qmin: np.ndarray
    qmax, qmin = numerical.get_reactive_power_limits()
    problem: PfBasicFormulation3Ph = PfBasicFormulation3Ph(
        V0=expandVoltage3ph(numerical.bus_data.Vbus),
        S0=expand3ph(numerical.get_power_injections_pu()), Qmin=qmin, Qmax=qmax,
        nc=numerical, options=vge.PowerFlowOptions(tolerance=1e-9), logger=vge.Logger())
    trial: np.ndarray = problem.var2x()
    trial[-1] = 0.04
    reference: np.ndarray = problem.compute_f(trial)
    error: float = problem.check_error(trial)[0]
    np.testing.assert_allclose(error, np.max(np.abs(reference)))
    problem.update(trial, update_controls=False)
    np.testing.assert_allclose(problem.fx(), reference)
    np.testing.assert_allclose(problem.var2x(), trial)
    assert problem.size() == len(trial) == len(reference)
    assert len(problem.get_x_names()) == len(problem.get_fx_names()) == len(trial)
    assert problem.Jacobian(autodiff=False).shape == (len(trial), len(trial))


@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar,
                                      ShuntConnectionType.FloatingStar, ShuntConnectionType.Delta))
@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_u1_sequence_impedances_preserve_terminal_power(
        connection: ShuntConnectionType, sbase: float) -> None:
    """Check terminal sequence laws independently from the controller's ABC matrix.

    :param connection: Physical connection determining the earth-return path.
    :param sbase: System base for current and impedance scaling.
    """
    grid: vge.MultiCircuit = make_grid(sbase=sbase)
    gen: vge.Generator = grid.generators[1]
    gen.R0, gen.X0 = 0.01, 0.08
    gen.R2, gen.X2 = 0.02, 0.10
    gen.conn = connection
    results: vge.PowerFlowResults3Ph = solve(grid)
    voltage: np.ndarray = target_voltages(results)
    power: np.ndarray = np.array((results.Sbus_A[1], results.Sbus_B[1], results.Sbus_C[1]))
    power += np.array((8 + 3j, 5 + 2j, 2 + 1j))
    currents: np.ndarray = np.conj(power / voltage) * 3.0 / sbase
    a: complex = np.exp(2j * np.pi / 3)
    transform: np.ndarray = np.array(((1, 1, 1), (1, a, a*a), (1, a*a, a))) / 3
    v012: np.ndarray = transform @ voltage
    i012: np.ndarray = transform @ currents
    expected_i0: complex = (-v012[0] / complex(gen.R0, gen.X0)
                            if connection == ShuntConnectionType.GroundedStar else 0j)
    expected_i2: complex = -v012[2] / complex(gen.R2, gen.X2)
    np.testing.assert_allclose(i012[[0, 2]], (expected_i0, expected_i2), atol=1e-8)
    assert abs(abs(v012[1]) - 1.01) < 1e-8
    assert abs(np.sum(power).real - gen.P) < 1e-6


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM))
@pytest.mark.parametrize('vset,limit', ((1.01, 2.0), (0.97, -2.0)))
def test_sequence_impedances_respect_net_reactive_limits(
        solver: vge.SolverType, vset: float, limit: float) -> None:
    """Q limits apply to total terminal power, including passive sequence absorption.

    :param solver: Numerical solver to exercise.
    :param vset: Voltage target provoking a capability limit.
    :param limit: Expected total terminal Q in MVAr.
    """
    grid: vge.MultiCircuit = make_grid()
    gen: vge.Generator = grid.generators[1]
    gen.R0, gen.X0, gen.R2, gen.X2 = 0.01, 0.08, 0.02, 0.10
    gen.Vset, gen.Qmin, gen.Qmax = vset, -2.0, 2.0
    results: vge.PowerFlowResults3Ph = solve(grid, solver=solver)
    terminal_power: complex = results.Sbus_A[1] + results.Sbus_B[1] + results.Sbus_C[1] + 15 + 6j
    np.testing.assert_allclose(terminal_power, complex(gen.P, limit), atol=1e-6)


def test_sequence_impedances_are_invisible_to_balanced_power_flow() -> None:
    """Passive zero/negative sequences must not add a positive-sequence shunt."""
    grid: vge.MultiCircuit = make_grid(unbalanced=False)
    reference: vge.PowerFlowResults3Ph = solve(grid)
    options: vge.PowerFlowOptions = vge.PowerFlowOptions(tolerance=1e-9, control_q=False)
    balanced_before: vge.PowerFlowResults = vge.power_flow(grid=grid, options=options)
    gen: vge.Generator = grid.generators[1]
    gen.R0, gen.X0, gen.R2, gen.X2 = 0.01, 0.08, 0.02, 0.10
    gen.conn = ShuntConnectionType.FloatingStar
    np.testing.assert_allclose(target_voltages(solve(grid)), target_voltages(reference), atol=1e-8)
    balanced_after: vge.PowerFlowResults = vge.power_flow(grid=grid, options=options)
    assert balanced_before.converged and balanced_after.converged
    np.testing.assert_allclose(balanced_before.voltage, balanced_after.voltage, atol=1e-10)


@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar, ShuntConnectionType.FloatingStar))
def test_sequence_impedances_survive_save_copy_and_parallel_groups(
        tmp_path: Path, connection: ShuntConnectionType) -> None:
    """Persist the connection and correctly sum parallel admittances on extraction.

    :param tmp_path: Isolated native-file output directory.
    :param connection: Connection retained through native serialization and compilation.
    """
    grid: vge.MultiCircuit = make_grid()
    gen: vge.Generator = grid.generators[1]
    gen.R0, gen.X0, gen.R2, gen.X2 = 0.01, 0.08, 0.02, 0.10
    gen.conn = connection
    reference: vge.PowerFlowResults3Ph = solve(grid)
    gen.P = 6.0
    gen.R0, gen.X0, gen.R2, gen.X2 = 0.02, 0.16, 0.04, 0.20
    other: vge.Generator = vge.Generator(
        P=6.0, vset=1.01, r0=0.02, x0=0.16, r2=0.04, x2=0.20)
    other.conn = connection
    grid.add_generator(bus=grid.buses[1], api_obj=other)
    np.testing.assert_allclose(target_voltages(solve(grid)), target_voltages(reference), atol=1e-8)
    path: str = str(tmp_path / 'sequence_impedances.veragrid')
    vge.save_file(grid, path)
    restored: vge.MultiCircuit = vge.open_file(path)
    np.testing.assert_allclose(target_voltages(solve(restored)), target_voltages(reference), atol=1e-8)
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=restored, fill_three_phase=True)
    data: GeneratorData = numerical.generator_data.copy().slice(
        np.array((1, 2)), np.array((1,)), np.array((-1, 0)))
    np.testing.assert_array_equal(data.conn, (connection.idx(), connection.idx()))
    np.testing.assert_allclose(data.r2 + 1j * data.x2, 0.04 + 0.2j)


@pytest.mark.parametrize('sequence', (0, 2))
@pytest.mark.parametrize('impedance', (0j, 1e-20 + 1e-20j,
                                     complex(float('nan'), 0.1), complex(0, float('inf'))))
def test_invalid_sequence_impedance_is_rejected(sequence: int, impedance: complex) -> None:
    """Do not convert a missing/invalid impedance into an enormous generator shunt.

    :param sequence: Homopolar or negative sequence to invalidate.
    :param impedance: Invalid impedance to reject before solving.
    :return: None.
    """
    grid: vge.MultiCircuit = make_grid()
    if sequence == 0 and impedance == 0j:
        # Exact zero is an ideal physical constraint, not a small impedance stamp.
        grid.generators[1].R0, grid.generators[1].X0 = 0.0, 0.0
        numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)
        control: PositiveSequenceControl = PositiveSequenceControl(numerical, compute_ybus(numerical)[5])
        np.testing.assert_allclose(control.yabc[0] @ np.ones(3), 0, atol=1e-12)
    else:
        # Devel rejects non-finite property values before physical compilation.
        # Finite but invalid impedances must still reach the sequence model.
        message: str = 'finite and nonzero'
        if not np.isfinite(impedance):
            component: str = 'R' if not np.isfinite(impedance.real) else 'X'
            message = rf'Non-finite value rejected for Generator\.{component}{sequence}'
        else:
            pass
        with pytest.raises(ValueError, match=message):
            if sequence == 0:
                grid.generators[1].R0, grid.generators[1].X0 = impedance.real, impedance.imag
            else:
                grid.generators[1].R2, grid.generators[1].X2 = impedance.real, impedance.imag
            numerical = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)
            PositiveSequenceControl(numerical, compute_ybus(numerical)[5])


@pytest.mark.parametrize('connection', (ShuntConnectionType.FloatingStar, ShuntConnectionType.Delta))
def test_blocked_zero_sequence_does_not_require_impedance(connection: ShuntConnectionType) -> None:
    """A blocked homopolar path must not depend on irrelevant stored Z0 values.

    :param connection: Three-wire connection with no earth return.
    """
    grid: vge.MultiCircuit = make_grid()
    gen: vge.Generator = grid.generators[1]
    gen.conn = connection
    reference: vge.PowerFlowResults3Ph = solve(grid)
    gen.R0, gen.X0 = 0.0, 0.0
    np.testing.assert_allclose(target_voltages(solve(grid)), target_voltages(reference), atol=1e-9)


def test_explicit_neutral_is_not_silently_treated_as_ground() -> None:
    """Require a supported connection rather than silently changing the return circuit."""
    grid: vge.MultiCircuit = make_grid()
    grid.generators[1].conn = ShuntConnectionType.NeutralStar
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)
    with pytest.raises(ValueError, match='explicit neutral'):
        PositiveSequenceControl(numerical, compute_ybus(numerical)[5])
