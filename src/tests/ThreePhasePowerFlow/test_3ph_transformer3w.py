# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
import numpy as np
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.basic_structures import Logger, Mat
from VeraGridEngine.Devices.Branches.winding import Winding
from VeraGridEngine.enumerations import WindingType
from VeraGridEngine.IO.dgs.dgs_to_veragrid import _tr3_zero_sequence_impedance
from VeraGridEngine.IO.dgs.veragrid_to_dgs import _build_typtr3_and_elmtr3


def make_grid() -> tuple[vge.MultiCircuit, vge.Transformer3W]:
    """Create a three-terminal star equivalent with separate zero-sequence data.

    :return: Grid and its three-winding transformer.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit()
    hv: vge.Bus = grid.add_bus(vge.Bus(name='HV', Vnom=110.0, is_slack=True))
    mv: vge.Bus = grid.add_bus(vge.Bus(name='MV', Vnom=33.0))
    lv: vge.Bus = grid.add_bus(vge.Bus(name='LV', Vnom=11.0))
    grid.add_generator(hv, vge.Generator())
    tr: vge.Transformer3W = vge.Transformer3W(bus1=hv, bus2=mv, bus3=lv,
        V1=110.0, V2=33.0, V3=11.0, r12=0.015, x12=0.15,
        r23=0.022, x23=0.22, r31=0.017, x31=0.17,
        rate12=100.0, rate23=60.0, rate31=30.0)
    tr.compute_delta_to_star()
    tr.fill_zero_sequence(0.03 + 0.3j, 0.05 + 0.5j, 0.04 + 0.4j)
    grid.add_transformer3w(tr)
    return grid, tr


@pytest.mark.parametrize('clock', (0, 1, 11))
def test_balanced_3w_matches_positive_sequence(clock: int) -> None:
    """Match the complete positive-sequence phasors in balanced ABC operation.

    :param clock: MV terminal lag relative to HV and the internal bus.
    :return: None.
    """
    grid, tr = make_grid()
    tr.winding2.vector_group_number = clock
    grid.add_load(tr.bus2, vge.Load(P=12, Q=3, P1=4, P2=4, P3=4, Q1=1, Q2=1, Q3=1))
    grid.add_load(tr.bus3, vge.Load(P=6, Q=1.5, P1=2, P2=2, P3=2, Q1=0.5, Q2=0.5, Q3=0.5))
    options: vge.PowerFlowOptions = vge.PowerFlowOptions(tolerance=1e-10, control_q=False,
        control_taps_modules=False, control_taps_phase=False, retry_with_other_methods=False)
    positive = vge.power_flow(grid, options)
    abc = vge.power_flow3ph(grid, options)
    assert positive.converged and abc.converged
    expected: np.ndarray = positive.voltage.copy()
    np.testing.assert_allclose(abc.voltage_A, expected, atol=1e-9, rtol=0)
    np.testing.assert_allclose(abc.voltage_B, expected * np.exp(-2j * np.pi / 3), atol=1e-9, rtol=0)
    np.testing.assert_allclose(abc.voltage_C, expected * np.exp(2j * np.pi / 3), atol=1e-9, rtol=0)


@pytest.mark.parametrize('delta_tertiary', (False, True))
def test_single_phase_load_matches_sequence_network(delta_tertiary: bool) -> None:
    """Check unbalanced voltages against an independent sequence-network solution.

    :param delta_tertiary: Close the unloaded tertiary's internal zero-sequence path.
    :return: None.
    """
    grid, tr = make_grid()
    if delta_tertiary:
        tr.winding3.conn_f = WindingType.Delta
    else:
        pass
    grid.add_load(tr.bus2, vge.Load(G1=10.0, G2=0.0, G3=0.0))
    # The HV source has zero U0/U2. An unloaded delta terminates the tertiary
    # zero-sequence leg while an unloaded grounded star carries no current.
    z0_h: complex = complex(tr.winding1.R0, tr.winding1.X0)
    z0_m: complex = complex(tr.winding2.R0, tr.winding2.X0)
    z0_l: complex = complex(tr.winding3.R0, tr.winding3.X0)
    z0: complex = z0_m + (z0_h * z0_l / (z0_h + z0_l) if delta_tertiary else z0_h)
    z1: complex = complex(tr.r12, tr.x12)
    a: complex = np.exp(2j * np.pi / 3)
    transform: Mat = np.array(((1, 1, 1), (1, a*a, a), (1, a, a*a)))
    impedance: Mat = transform @ np.diag((z0, z1, z1)) @ np.linalg.inv(transform)
    expected: np.ndarray = np.linalg.solve(np.eye(3) + impedance @ np.diag((0.3, 0, 0)),
                                           np.array((1, a*a, a)))
    result = vge.power_flow3ph(grid, vge.PowerFlowOptions(tolerance=1e-11, control_q=False))
    assert result.converged
    actual: np.ndarray = np.array((result.voltage_A[1], result.voltage_B[1], result.voltage_C[1]))
    np.testing.assert_allclose(actual, expected, atol=1e-9, rtol=0)


@pytest.mark.parametrize('connection', (WindingType.GroundedStar, WindingType.FloatingStar, WindingType.Delta))
@pytest.mark.parametrize('clock', (0, 1, 5, 11))
@pytest.mark.parametrize('reverse', (False, True))
def test_winding_clock_and_taps(connection: WindingType, clock: int, reverse: bool) -> None:
    """Check relative terminal clocks, taps and both sequence orientations.

    :param connection: External terminal connection.
    :param clock: Terminal lag relative to the core, in units of 30 degrees.
    :param reverse: Put the common internal bus at the from terminal.
    :return: None.
    """
    external: vge.Bus = vge.Bus(Vnom=33)
    internal: vge.Bus = vge.Bus(Vnom=1, is_internal=True)
    winding: Winding = Winding(bus_from=internal if reverse else external,
        bus_to=external if reverse else internal, HV=33, LV=1, r=0.02, x=0.2,
        r0=0.04, x0=0.4, r2=0.03, x2=0.3, tap_module=1.07, tap_phase=0.08)
    winding.conn_f = WindingType.GroundedStar if reverse else connection
    winding.conn_t = connection if reverse else WindingType.GroundedStar
    winding.vector_group_number = clock
    yff, yft, ytf, ytt = winding.transformer_admittance(1.1, 0.97, Logger())
    a: complex = np.exp(2j * np.pi / 3)
    for vector, sign in ((np.array((0, 1, a*a, a)), 1), (np.array((0, 1, a, a*a)), -1)):
        shift: float = (1 if reverse else -1) * np.deg2rad(30 * clock)
        target: np.ndarray = vector * 0.97 / (1.07 * 1.1) * np.exp(-1j * (0.08 + sign * shift))
        np.testing.assert_allclose(yff @ vector + yft @ target, 0, atol=1e-13)
        np.testing.assert_allclose(ytf @ vector + ytt @ target, 0, atol=1e-13)
        impedance: complex = complex(0.02, 0.2) if sign == 1 else complex(0.03, 0.3)
        np.testing.assert_allclose(yff @ vector, vector / (impedance * (1.07 * 1.1)**2), atol=1e-13)


@pytest.mark.parametrize('connection', (WindingType.FloatingStar, WindingType.Delta))
def test_zero_sequence_terminal_paths(connection: WindingType) -> None:
    """Distinguish an isolated star from the circulating path of a delta.

    :param connection: Floating star or delta at the external terminal.
    :return: None.
    """
    _, tr = make_grid()
    winding: Winding = tr.winding3
    winding.conn_f = connection
    yff, yft, ytf, ytt = winding.transformer_admittance(1, 1, Logger())
    zero: np.ndarray = np.array((0, 1, 1, 1), dtype=complex)
    np.testing.assert_allclose(yff @ zero, 0, atol=1e-13)
    np.testing.assert_allclose(yft @ zero, 0, atol=1e-13)
    np.testing.assert_allclose(ytf @ zero, 0, atol=1e-13)
    if connection == WindingType.Delta:
        np.testing.assert_allclose(ytt @ zero, zero / complex(winding.R0, winding.X0), atol=1e-13)
    else:
        np.testing.assert_allclose(ytt @ zero, 0, atol=1e-13)


def test_explicit_neutral_and_invalid_zero_sequence() -> None:
    """Retain the neutral return current and diagnose missing winding data.

    :return: None.
    """
    _, tr = make_grid()
    winding: Winding = tr.winding2
    winding.conn_f = WindingType.NeutralStar
    winding.phases = np.array((0, 1, 2, 3))
    yff, yft, ytf, ytt = winding.transformer_admittance(1, 1, Logger())
    np.testing.assert_allclose(np.sum(yff, axis=0), 0, atol=1e-13)
    np.testing.assert_allclose(np.sum(yft, axis=0), 0, atol=1e-13)
    assert abs(yff[0, 0]) > 0
    winding.R0 = winding.X0 = 0
    with pytest.raises(ValueError, match='winding Z0.*uk0hm'):
        winding.transformer_admittance(1, 1, Logger())


def test_native_roundtrip_and_legacy_connections(tmp_path: Path) -> None:
    """Preserve winding data and interpret the former reversed DGS layout.

    :param tmp_path: Isolated temporary directory.
    :return: None.
    """
    grid, tr = make_grid()
    tr.winding3.conn_f = WindingType.Delta
    tr.winding3.vector_group_number = 11
    original: tuple = tr.winding3.transformer_admittance(1, 1, Logger())
    # Historical native files retained the external delta on the internal end.
    tr.winding3.conn_f, tr.winding3.conn_t = WindingType.GroundedStar, WindingType.Delta
    path: Path = tmp_path / 'three_winding.veragrid'
    vge.save_file(grid, str(path))
    restored: vge.MultiCircuit = vge.open_file(str(path))
    winding: Winding = restored.transformers3w[0].winding3
    assert winding.R0 == tr.winding3.R0 and winding.X0 == tr.winding3.X0
    assert winding.vector_group_number == 11
    for expected, actual in zip(original, winding.transformer_admittance(1, 1, Logger())):
        np.testing.assert_allclose(actual, expected, atol=1e-13)


def test_pf_zero_sequence_bases_and_dgs_export() -> None:
    """Verify PF pairwise percentages and independent unequal MVA bases.

    :return: None.
    """
    grid, tr = make_grid()
    grid.Sbase = 50
    # Native PF TORN SGT1 data, retaining its negative equivalent MV resistance.
    tr.fill_zero_sequence(
        _tr3_zero_sequence_impedance(16.21, 0.4052, 240, grid.Sbase),
        _tr3_zero_sequence_impedance(5.79, 0.1013, 60, grid.Sbase),
        _tr3_zero_sequence_impedance(9.25, 0.3039, 60, grid.Sbase))
    np.testing.assert_allclose(tr.winding2.R0, -0.0004220833333333333, atol=1e-14)
    tr.winding1.rate, tr.winding2.rate, tr.winding3.rate = 240, 240, 60
    tr.rate1, tr.rate2, tr.rate3 = 240, 240, 60
    tr.winding3.conn_f = WindingType.Delta
    tpe, _, _ = _build_typtr3_and_elmtr3(tr, 'type', 'element', 'folder', None, grid.Sbase)
    np.testing.assert_allclose((tpe.uk0hm, tpe.uk0ml, tpe.uk0hl), (16.21, 5.79, 9.25), atol=1e-12)
    np.testing.assert_allclose((tpe.ur0hm, tpe.ur0ml, tpe.ur0hl), (0.4052, 0.1013, 0.3039), atol=1e-12)
    assert (tpe.tr3cn_h, tpe.tr3cn_m, tpe.tr3cn_l) == ('YN', 'YN', 'D')


def test_dgs_roundtrip_preserves_winding_sequences(tmp_path: Path) -> None:
    """Exercise the full DGS writer and importer, including terminal orientation.

    :param tmp_path: Isolated temporary directory.
    :return: None.
    """
    source: Path = Path(__file__).resolve().parents[1] / 'data/grids/three_winding_transformer_powers.dgs'
    grid: vge.MultiCircuit = vge.open_file(str(source))
    tr: vge.Transformer3W = grid.transformers3w[0]
    tr.fill_zero_sequence(0.03 + 0.3j, 0.05 + 0.5j, 0.04 + 0.4j)
    tr.winding2.conn_f = WindingType.FloatingStar
    tr.winding3.conn_f = WindingType.Delta
    tr.winding2.vector_group_number = 1
    tr.winding3.vector_group_number = 11
    path: Path = tmp_path / 'three_winding.dgs'
    vge.save_file(grid, str(path))
    restored: vge.MultiCircuit = vge.open_file(str(path))
    other: vge.Transformer3W = restored.transformers3w[0]
    for before, after in zip((tr.winding1, tr.winding2, tr.winding3),
                             (other.winding1, other.winding2, other.winding3)):
        assert before.conn_f == after.conn_f
        assert after.conn_t == WindingType.GroundedStar
        assert before.vector_group_number == after.vector_group_number
        np.testing.assert_allclose((after.R, after.X, after.R0, after.X0),
                                   (before.R, before.X, before.R0, before.X0), atol=1e-6)
