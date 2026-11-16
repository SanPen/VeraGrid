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
from VeraGridEngine.enumerations import StaticGeneratorControlMode, ConverterControlType, ShuntControlMode
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import voltage_q_droop
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.static_generator_droop import StaticGeneratorDroop
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_full_acdc_with_negative_poles import PfAcDcWithNegativePoles


def make_grid(sbase: float = 100.0, unbalanced: bool = False) -> vge.MultiCircuit:
    """Build an AC feeder with a controlled injection and a known phase load.

    :param sbase: System power base, MVA.
    :param unbalanced: Whether to use unequal phase powers.
    :return: Two-bus circuit.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit(Sbase=sbase)
    source: vge.Bus = grid.add_bus(vge.Bus(name='Slack', Vnom=20.0, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(name='SVC', Vnom=20.0))
    grid.add_generator(source, vge.Generator())
    grid.add_line(vge.Line(bus_from=source, bus_to=target, r=0.02, x=0.08, r0=0.04, x0=0.16))
    grid.add_static_generator(target, vge.StaticGenerator(
        name='SVC droop', P=2.0, Q=1.0, Snom=80.0,
        control_mode=StaticGeneratorControlMode.QVDroop, vset=1.01, droop=3.0))
    if unbalanced:
        grid.add_load(target, vge.Load(P=15.0, Q=6.0, P1=8.0, P2=5.0, P3=2.0, Q1=3.0, Q2=2.0, Q3=1.0))
    else:
        grid.add_load(target, vge.Load(P=15.0, Q=6.0))
    return grid


def solve(grid: vge.MultiCircuit, solver: vge.SolverType = vge.SolverType.NR,
          autodiff: bool = True) -> vge.PowerFlowResults:
    """Solve with no fallback, to expose failures in the selected formulation.

    :param grid: Network to solve.
    :param solver: Numerical method.
    :param autodiff: Use the existing finite-difference option, equally for both droop models.
    :return: Converged positive-sequence results.
    """
    results: vge.PowerFlowResults = vge.power_flow(grid, vge.PowerFlowOptions(
        solver_type=solver, tolerance=1e-9, max_iter=100, control_q=False,
        use_autodiff_jacobian=autodiff, retry_with_other_methods=False))
    assert results.converged
    return results


@pytest.mark.parametrize('sbase', (25.0, 100.0))
@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_droop_matches_vsc_and_balanced_abc(sbase: float, solver: vge.SolverType) -> None:
    """Match an actual lossless VSC, including Q sign, reference, rating and units.

    :param sbase: Power base detecting incorrect scaling.
    :param solver: Nonlinear solver to exercise.
    """
    grid: vge.MultiCircuit = make_grid(sbase=sbase)
    # ElmSvs uses zero reference Q in the established VSC import route.
    grid.static_generators[0].Q = 0.0
    balanced: vge.PowerFlowResults = solve(grid, solver)
    abc: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, vge.PowerFlowOptions(
        solver_type=solver, tolerance=1e-9, max_iter=100, control_q=False, retry_with_other_methods=False))
    assert abc.converged
    np.testing.assert_allclose(abc.voltage_A, balanced.voltage, atol=1e-8)
    np.testing.assert_allclose(abc.voltage_B, balanced.voltage * np.exp(-2j*np.pi/3), atol=1e-8)
    np.testing.assert_allclose(abc.voltage_C, balanced.voltage * np.exp(2j*np.pi/3), atol=1e-8)
    grid.static_generators.clear()
    dc: vge.Bus = grid.add_bus(vge.Bus(name='DC reference', Vnom=20.0, is_dc=True, is_slack=True))
    grid.add_vsc(vge.VSC(bus_from=dc, bus_to=grid.buses[1], rate=80.0,
        alpha1=0.0, alpha2=0.0, alpha3=0.0,
        control1=ConverterControlType.Pac, control1_val=-2.0,
        control2=ConverterControlType.Q_droop, control2_val=0.0,
        control2_droop=3.0, control2_droop_val=1.01))
    vsc: vge.PowerFlowResults = solve(grid, solver)
    np.testing.assert_allclose(vsc.voltage[:2], balanced.voltage, atol=1e-8)
    np.testing.assert_allclose(vsc.St_vsc[0], -(balanced.Sbus[1] + 15 + 6j), atol=1e-6)


@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_unbalanced_droop_uses_u1_and_injects_only_i1(sbase: float) -> None:
    """Recover the independent VSC law and zero I0/I2 from solved phase KCL.

    :param sbase: System base, MVA.
    """
    grid: vge.MultiCircuit = make_grid(sbase=sbase, unbalanced=True)
    results: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, vge.PowerFlowOptions(tolerance=1e-9))
    assert results.converged
    voltage: np.ndarray = np.array((results.voltage_A[1], results.voltage_B[1], results.voltage_C[1]))
    power: np.ndarray = np.array((results.Sbus_A[1], results.Sbus_B[1], results.Sbus_C[1]))
    power += np.array((8+3j, 5+2j, 2+1j))
    current: np.ndarray = np.conj(power / voltage) * 3.0 / sbase
    a: complex = np.exp(2j*np.pi/3)
    transform: np.ndarray = np.array(((1, 1, 1), (1, a, a*a), (1, a*a, a))) / 3.0
    v1: complex = (transform @ voltage)[1]
    expected_q: float = -sbase * voltage_q_droop(
        ut=v1, u_setpoint_min=0.9, u_setpoint_max=1.1, u_setpoint=1.01,
        Q_setpoint=-1.0/sbase, S_r=80.0, droop=3.0, Q_min=-np.inf, Q_max=np.inf, S_base=sbase)
    np.testing.assert_allclose(np.sum(power), 2.0 + 1j*expected_q, atol=1e-6)
    np.testing.assert_allclose((transform @ current)[[0, 2]], 0.0, atol=1e-8)
    assert np.ptp(np.abs(voltage)) > 1e-3


@pytest.mark.parametrize('magnitude', (0.85, 0.98, 1.15))
def test_droop_residual_consistency_at_voltage_clamps(magnitude: float) -> None:
    """Check Newton and line-search consistency, including both voltage clamps.

    :param magnitude: Trial voltage inside or outside the linear droop region.
    """
    nc: NumericalCircuit = compile_numerical_circuit_at(make_grid())
    qmax: np.ndarray
    qmin: np.ndarray
    qmax, qmin = nc.get_reactive_power_limits()
    voltage: np.ndarray = np.array((1+0j, magnitude*np.exp(-0.03j)))
    problem: PfAcDcWithNegativePoles = PfAcDcWithNegativePoles(
        V0=voltage, S0=nc.get_power_injections_pu(), I0=nc.get_current_injections_pu(),
        Y0=-nc.get_admittance_injections_pu(), Qmin=qmin, Qmax=qmax, nc=nc,
        options=vge.PowerFlowOptions(), logger=vge.Logger())
    trial: np.ndarray = problem.var2x()
    expected: np.ndarray = problem.compute_f(trial)
    problem.update(trial, update_controls=False)
    np.testing.assert_allclose(problem.fx(), expected)


def test_droop_colocated_units_inactive_and_native_roundtrip(tmp_path: Path) -> None:
    """Preserve parallel injections, native files and the default PQ mode.

    :param tmp_path: Isolated directory for the native file.
    """
    grid: vge.MultiCircuit = make_grid()
    reference: vge.PowerFlowResults = solve(grid)
    first: vge.StaticGenerator = grid.static_generators[0]
    first.Snom, first.P, first.Q = 40.0, 1.0, 0.5
    grid.add_static_generator(grid.buses[1], vge.StaticGenerator(
        P=1.0, Q=0.5, Snom=40.0, control_mode=StaticGeneratorControlMode.QVDroop, vset=1.01, droop=3.0))
    grid.add_static_generator(grid.buses[1], vge.StaticGenerator(
        active=False, P=1000.0, Snom=0.0, droop=0.0, control_mode=StaticGeneratorControlMode.QVDroop))
    grid.add_static_generator(grid.buses[1], vge.StaticGenerator(P=0.0, Q=0.0))
    assert grid.static_generators[-1].control_mode == StaticGeneratorControlMode.PQ
    filename: str = str(tmp_path / 'droop.veragrid')
    vge.FileSave(grid, filename).save()
    restored: vge.MultiCircuit = vge.FileOpen(filename).open()
    np.testing.assert_allclose(solve(restored).voltage, reference.voltage, atol=1e-8)
    assert restored.static_generators[0].control_mode == StaticGeneratorControlMode.QVDroop
    abc: vge.PowerFlowResults3Ph = vge.power_flow3ph(restored, vge.PowerFlowOptions(tolerance=1e-9))
    assert abc.converged
    np.testing.assert_allclose(abc.voltage_A, reference.voltage, atol=1e-8)


def test_droop_profiles_compilation_and_island_copy() -> None:
    """Retain time-step references and droop data through numerical island copying."""
    grid: vge.MultiCircuit = make_grid()
    generator: vge.StaticGenerator = grid.static_generators[0]
    generator.P_prof = np.array((4.0,))
    generator.Q_prof = np.array((3.0,))
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, t_idx=0, fill_three_phase=True)
    island: NumericalCircuit = nc.split_into_islands()[0]
    control: StaticGeneratorDroop = StaticGeneratorDroop(island)
    np.testing.assert_allclose(control.power(np.array((1.01+0j,))), (0.04+0.03j,))
    np.testing.assert_allclose(nc.load_data.S3_star[-4:], 0.0)
    logger: vge.Logger = vge.Logger()
    nc.load_data.compare(nc.load_data.copy(), 1e-12, logger)
    assert logger.error_count() == 0


def test_droop_does_not_attribute_its_reactive_power_to_a_colocated_generator() -> None:
    """Keep reported generator Q consistent with network KCL at PV and slack buses."""
    grid: vge.MultiCircuit = make_grid()
    grid.add_generator(grid.buses[1], vge.Generator(
        P=4.0, vset=1.02, r0=0.01, x0=0.08, r2=0.02, x2=0.10))
    grid.add_static_generator(grid.buses[0], vge.StaticGenerator(
        Snom=20.0, Q=2.0, vset=1.01, droop=3.0, control_mode=StaticGeneratorControlMode.QVDroop))
    results: vge.PowerFlowResults = solve(grid)
    expected_droop: np.ndarray = np.array((2.0 + 2000.0/3.0*0.01, 1.0 + 8000.0/3.0*(-0.01)))
    np.testing.assert_allclose(results.gen_q + expected_droop - np.array((0.0, 6.0)),
                               results.Sbus.imag, atol=1e-6)
    abc: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, vge.PowerFlowOptions(
        tolerance=1e-9, control_q=False))
    assert abc.converged
    np.testing.assert_allclose(abc.voltage_A, results.voltage, atol=1e-8)


def test_droop_kw_units_preserve_reference_and_rating() -> None:
    """Convert dispatch and rating together when the existing kW option is selected."""
    grid: vge.MultiCircuit = make_grid()
    reference: vge.PowerFlowResults = solve(grid)
    generator: vge.StaticGenerator = grid.static_generators[0]
    generator.P *= 1000.0
    generator.Q *= 1000.0
    generator.Snom *= 1000.0
    generator.use_kw = True
    np.testing.assert_allclose(solve(grid).voltage, reference.voltage, atol=1e-8)
    abc: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, vge.PowerFlowOptions(tolerance=1e-9))
    assert abc.converged
    np.testing.assert_allclose(abc.voltage_A, reference.voltage, atol=1e-8)


@pytest.mark.parametrize('use_vsc', (False, True))
def test_elmsvs_import_preserves_droop_and_other_routes(use_vsc: bool) -> None:
    """Use the committed SVC fixture to exercise both public import routes.

    :param use_vsc: Whether the user explicitly selects converter import.
    """
    source: Path = Path(__file__).resolve().parents[1] / 'data/grids/test_ieee14_svs.dgs'
    grid: vge.MultiCircuit = vge.FileOpen(str(source), options=FileOpenOptions(
        dgs_use_vsc_for_injections=use_vsc)).open()
    if use_vsc:
        units: dict = dict((unit.name, unit) for unit in grid.vsc_devices)
        assert units['SVS_Droop'].control2 == ConverterControlType.Q_droop
        assert units['SVS_Droop'].control2_val_droop == 3.0
        assert units['SVS_Droop'].rate == 30.0
        assert units['SVS_Qcontrol'].control2 == ConverterControlType.Qac
        assert units['SVS_Ucontrol'].control2 == ConverterControlType.Vm_ac
    else:
        units = dict((unit.name, unit) for unit in grid.controllable_shunts)
        shunt = units['SVS_Droop']
        assert shunt.control_mode == ShuntControlMode.QVDroop
        assert shunt.Qdroop == pytest.approx(30.0 * 100.0 / 3.0)
        assert (shunt.Bmin, shunt.Bmax) == pytest.approx((-10.0, 40.0))
        assert shunt.Vset == 1.0
        assert set(unit.name for unit in grid.controllable_shunts) == set((
            'SVS_Droop', 'SVS_NoControl', 'SVS_Qcontrol', 'SVS_Ucontrol'))


@pytest.mark.parametrize('invalid', ('droop', 'rating', 'dc_bus', 'phase'))
def test_invalid_droop_reports_device(invalid: str) -> None:
    """Reject an unusable controller with an actionable device-specific message.

    :param invalid: Invalid input to exercise.
    """
    grid: vge.MultiCircuit = make_grid()
    if invalid == 'droop':
        grid.static_generators[0].droop = 0.0
    elif invalid == 'rating':
        grid.static_generators[0].Snom = 0.0
    elif invalid == 'dc_bus':
        grid.buses[1].is_dc = True
    else:
        grid.static_generators[0].phA = False
    with pytest.raises(ValueError, match='SVC droop'):
        compile_numerical_circuit_at(grid)
