# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Devices.admittance_matrix import AdmittanceMatrix


def make_legacy_grid(zero_impedance: complex, zero_susceptance: float) -> vge.MultiCircuit:
    """Build a balanced grid containing stale phase matrices without a template.

    :param zero_impedance: Zero-sequence line impedance in per unit.
    :param zero_susceptance: Zero-sequence line susceptance in per unit.
    :return: Two-bus grid with deliberately inconsistent stored phase matrices.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit()
    source: vge.Bus = grid.add_bus(vge.Bus(name="Source", Vnom=20.0, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(name="Load", Vnom=20.0))
    grid.add_generator(bus=source, api_obj=vge.Generator())
    grid.add_load(bus=target, api_obj=vge.Load(P=10.0, Q=4.0))
    line: vge.Line = vge.Line(bus_from=source, bus_to=target, r=0.02, x=0.06, b=0.03,
                              r0=zero_impedance.real, x0=zero_impedance.imag, b0=zero_susceptance)

    # Parsing older files can populate both matrices independently of sequence data.
    line.disable_auto_updates()
    line.ys = AdmittanceMatrix(size=4)
    line.ysh = AdmittanceMatrix(size=4)
    stored: AdmittanceMatrix
    for stored in (line.ys, line.ysh):
        stored.values[1:, 1:] = np.eye(3, dtype=complex) * (2.0 - 3.0j)
        stored.phA = True
        stored.phB = True
        stored.phC = True
    line.enable_auto_updates()
    grid.add_line(line)
    return grid


@pytest.mark.parametrize(
    "zero_impedance,zero_susceptance,expected_zero_impedance,expected_zero_susceptance",
    ((0.04 + 0.12j, 0.01, 0.04 + 0.12j, 0.01),
     (0.12j, 0.01, 0.12j, 0.01),
     (0.04 + 0j, 0.01, 0.04 + 0j, 0.01),
     (0j, 0.0, 0.02 + 0.06j, 0.03)),
)
def test_legacy_line_compiles_from_sequence_data(zero_impedance: complex,
                                                zero_susceptance: float,
                                                expected_zero_impedance: complex,
                                                expected_zero_susceptance: float) -> None:
    """Compile the physical pi model from sequence data despite populated matrices.

    :param zero_impedance: Stored zero-sequence impedance, including missing data.
    :param zero_susceptance: Stored zero-sequence susceptance.
    :param expected_zero_impedance: Effective zero-sequence impedance after fallback.
    :param expected_zero_susceptance: Effective zero-sequence susceptance after fallback.
    :return: None.
    """
    grid: vge.MultiCircuit = make_legacy_grid(zero_impedance, zero_susceptance)
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)

    # Independent sequence projectors reconstruct the expected pi admittance in p.u.
    zero_projector: np.ndarray = np.ones((3, 3), dtype=complex) / 3.0
    other_projector: np.ndarray = np.eye(3, dtype=complex) - zero_projector
    expected_series: np.ndarray = np.zeros((4, 4), dtype=complex)
    expected_shunt: np.ndarray = np.zeros((4, 4), dtype=complex)
    expected_series[1:, 1:] = other_projector / (0.02 + 0.06j) + zero_projector / expected_zero_impedance
    expected_shunt[1:, 1:] = 1j * (0.03 * other_projector + expected_zero_susceptance * zero_projector)
    np.testing.assert_allclose(numerical.passive_branch_data.Yff3, expected_series + expected_shunt / 2.0)
    np.testing.assert_allclose(numerical.passive_branch_data.Yft3, -expected_series)
    np.testing.assert_allclose(numerical.passive_branch_data.Ytt3, expected_series + expected_shunt / 2.0)
    np.testing.assert_allclose(numerical.passive_branch_data.Ytf3, -expected_series)


def test_line_sequence_edits_refresh_existing_phase_matrices() -> None:
    """Refresh both matrices after sequence parameters change following an initial read.

    :return: None.
    """
    line: vge.Line = vge.Line(r=0.02, x=0.06, b=0.03)
    initial_series: np.ndarray = line.ys.values.copy()
    initial_shunt: np.ndarray = line.ysh.values.copy()

    # With zero-sequence data absent, both sequence subspaces track the new values.
    line.R = 0.04
    line.X = 0.12
    line.B = 0.06
    expected_series: np.ndarray = np.zeros((4, 4), dtype=complex)
    expected_shunt: np.ndarray = np.zeros((4, 4), dtype=complex)
    expected_series[1:, 1:] = np.eye(3, dtype=complex) / (0.04 + 0.12j)
    expected_shunt[1:, 1:] = np.eye(3, dtype=complex) * 0.06j * 1e6
    np.testing.assert_allclose(line.ysh.values, expected_shunt)
    np.testing.assert_allclose(line.ys.values, expected_series)
    assert not np.allclose(line.ys.values, initial_series)
    assert not np.allclose(line.ysh.values, initial_shunt)


def test_sequence_refresh_preserves_disconnected_phases() -> None:
    """Retain explicitly disconnected phases while rebuilding sequence admittance.

    :return: None.
    """
    line: vge.Line = vge.Line(r=0.02, x=0.06, b=0.03)
    line.ys.phC = False
    line.ysh.phC = False
    line.R = 0.04

    # Phase masks remain authoritative even when their coefficients must refresh.
    series: AdmittanceMatrix = line.ys
    shunt: AdmittanceMatrix = line.ysh
    assert series.phA and series.phB and not series.phC and not series.phN
    assert shunt.phA and shunt.phB and not shunt.phC and not shunt.phN
    np.testing.assert_allclose(series.values[1:3, 1:3], np.eye(2) / (0.04 + 0.06j))
    np.testing.assert_allclose(shunt.values[1:3, 1:3], np.eye(2) * 0.03j * 1e6)
    np.testing.assert_array_equal(series.values[3, :], 0.0)
    np.testing.assert_array_equal(series.values[:, 3], 0.0)
    np.testing.assert_array_equal(shunt.values[3, :], 0.0)
    np.testing.assert_array_equal(shunt.values[:, 3], 0.0)


def test_physical_template_preserves_asymmetric_phase_matrices() -> None:
    """Keep template matrices on reads, allowing an explicitly requested rebuild.

    :return: None.
    """
    source: vge.Bus = vge.Bus(Vnom=10.0)
    target: vge.Bus = vge.Bus(Vnom=10.0)
    impedance: np.ndarray = np.diag(np.array((0.02 + 0.06j, 0.03 + 0.08j, 0.04 + 0.1j)))
    admittance: np.ndarray = np.diag(np.array((0.01j, 0.02j, 0.03j)))
    template: vge.OverheadLineType = vge.create_known_abc_overhead_template(
        name="Asymmetric", z_nabc=impedance, ysh_nabc=admittance,
        phases=np.array((1, 2, 3)), Vnom=10.0,
    )
    line: vge.Line = vge.Line(bus_from=source, bus_to=target)
    line.apply_template(template, Sbase=100.0, freq=50.0, logger=vge.Logger())
    original_series: np.ndarray = line.ys.values.copy()
    original_shunt: np.ndarray = line.ysh.values.copy()

    # Sequence parameters cannot replace the template's asymmetric phase model.
    line.R = 0.5
    line.X = 0.8
    line.B = 0.2
    assert line.template is template
    np.testing.assert_allclose(original_series[1:, 1:], np.linalg.inv(impedance))
    np.testing.assert_allclose(original_shunt[1:, 1:], admittance * 1e6)
    np.testing.assert_array_equal(line.ys.values, original_series)
    np.testing.assert_array_equal(line.ysh.values, original_shunt)

    # The editor explicitly rebuilds all phases before applying a new selection.
    line.ys.phC = False
    line.ysh.phC = False
    line.fill_3_phase_from_sequence()
    assert line.ys.phC and line.ysh.phC
    assert abs(line.ys.values[3, 3]) > 0.0
    assert abs(line.ysh.values[3, 3]) > 0.0


def test_legacy_grid_three_phase_matches_positive_sequence() -> None:
    """Solve a legacy grid with stale matrices and nonzero charging consistently.

    :return: None.
    """
    grid: vge.MultiCircuit = make_legacy_grid(0.04 + 0.12j, 0.01)
    options: vge.PowerFlowOptions = vge.PowerFlowOptions(
        solver_type=vge.SolverType.NR, tolerance=1e-9, control_q=False, retry_with_other_methods=False,
    )
    positive: vge.PowerFlowResults = vge.power_flow(grid=grid, options=options)
    three_phase: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid=grid, options=options)

    # Balanced phases must recover the positive-sequence complex voltages.
    rotation: complex = np.exp(2j * np.pi / 3.0)
    assert positive.converged
    assert three_phase.converged
    np.testing.assert_allclose(three_phase.voltage_A, positive.voltage, atol=1e-7)
    np.testing.assert_allclose(three_phase.voltage_B * rotation, positive.voltage, atol=1e-7)
    np.testing.assert_allclose(three_phase.voltage_C / rotation, positive.voltage, atol=1e-7)
