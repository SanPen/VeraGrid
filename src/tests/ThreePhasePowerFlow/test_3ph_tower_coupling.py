"""Physical tower currents, phase arrangements and passive-neutral reconstruction."""
from pathlib import Path
import numpy as np
import pytest
from scipy.sparse import csc_matrix
import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmTow
from VeraGridEngine.IO.dgs.dgs_to_veragrid import _apply_elmtow_tower_coupling
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.pf_basic_formulation_3ph import (
    compute_ybus, passive_neutral_reduction)


def tower_grid(reverse: bool = False) -> vge.MultiCircuit:
    """Construct two galvanically separate circuits sharing an asymmetric tower.

    :param reverse: Reverse the public orientation of the second circuit.
    :return: Network with a reusable geometric template.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit()
    wire: vge.Wire = vge.Wire(name='Phase wire', r=0.12, diameter=22)
    grid.add_wire(wire)
    tower: vge.OverheadLineType = vge.OverheadLineType(Vnom=132)
    for phase, xy in enumerate(((-4, 18), (-5, 15), (-4, 12), (4, 19), (5, 16), (4, 13)), start=1):
        tower.add_wire_relationship(wire, xpos=xy[0], ypos=xy[1], phase=phase)
    tower.add_wire_relationship(wire, xpos=0, ypos=24, phase=0)
    tower.compute()
    grid.add_overhead_line(tower)
    for k in range(2):
        source: vge.Bus = grid.add_bus(vge.Bus(name=f'Source{k}', Vnom=132, is_slack=True))
        target: vge.Bus = grid.add_bus(vge.Bus(name=f'Target{k}', Vnom=132))
        grid.add_generator(source, vge.Generator())
        line: vge.Line = vge.Line(bus_from=target if reverse and k == 1 else source,
                                 bus_to=source if reverse and k == 1 else target, length=35)
        line.set_circuit_idx(k + 1, tower)
        line.apply_template(tower, Sbase=grid.Sbase, freq=grid.fBase, logger=vge.Logger())
        line.coupling_group = 'Physical section'
        line.coupling_reversed = reverse and k == 1
        grid.add_line(line)
        grid.add_load(target, vge.Load(P=30, Q=9, P1=10 + 2*k, P2=11, P3=9 - 2*k,
                                      Q1=3, Q2=4, Q3=2))
    return grid


@pytest.mark.parametrize('reverse', (False, True))
@pytest.mark.parametrize('second_length,shared_length', ((35.0, 35.0), (20.0, 20.0), (50.0, 35.0)))
def test_complete_tower_currents_and_islands(reverse: bool, second_length: float, shared_length: float) -> None:
    """Check physical Ohm's law, shunt current and power conservation across both circuits.

    :param reverse: Reverse circuit two without changing the physical system.
    :param second_length: Full length of the second circuit, in km.
    :param shared_length: Length over which the two circuits are coupled, in km.
    """
    grid: vge.MultiCircuit = tower_grid(reverse)
    grid.lines[1].length = second_length
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    assert len(nc.split_into_islands()) == 1
    assert len(compile_numerical_circuit_at(grid).split_into_islands()) == 2
    assert not np.any(nc.passive_branch_data.phN)
    tower: vge.OverheadLineType = grid.lines[0].template
    result = vge.power_flow3ph(grid, options=vge.PowerFlowOptions(tolerance=1e-10, control_q=False,
                                                               retry_with_other_methods=False))
    assert result.converged
    voltage: np.ndarray = np.column_stack((result.voltage_A, result.voltage_B, result.voltage_C))
    physical: np.ndarray = voltage * 132 / np.sqrt(3)
    vf: np.ndarray = physical[[0, 2]].ravel()
    vt: np.ndarray = physical[[1, 3]].ravel()
    # Assemble physical blocks independently, preserving both self and shared lengths.
    impedance: np.ndarray = np.block([[tower.z_abc[:3, :3] * 35, tower.z_abc[:3, 3:] * shared_length],
                                     [tower.z_abc[3:, :3] * shared_length, tower.z_abc[3:, 3:] * second_length]])
    shunt: np.ndarray = np.block([[tower.y_abc[:3, :3] * 35, tower.y_abc[:3, 3:] * shared_length],
                                 [tower.y_abc[3:, :3] * shared_length, tower.y_abc[3:, 3:] * second_length]])
    series: np.ndarray = np.linalg.solve(impedance, vf - vt)
    send: np.ndarray = series + shunt @ vf / 2
    receive: np.ndarray = -series + shunt @ vt / 2
    loads: np.ndarray = np.array((10+3j, 11+4j, 9+2j, 12+3j, 11+4j, 7+2j))
    np.testing.assert_allclose(receive, -np.conj(loads / vt), atol=1e-9)
    ybus, yf, yt, _, mask, _, branch_lookup = compute_ybus(nc)
    full: np.ndarray = np.zeros(16, dtype=complex)
    full.reshape(-1, 4)[:, 1:] = voltage
    from_current: np.ndarray = send.copy()
    to_current: np.ndarray = receive.copy()
    if reverse:
        from_current[3:] = receive[3:]
        to_current[3:] = send[3:]
    else:
        pass
    ibase: float = grid.Sbase / (132 * np.sqrt(3))
    np.testing.assert_allclose(yf @ full[mask] * ibase, from_current, atol=1e-9)
    np.testing.assert_allclose(yt @ full[mask] * ibase, to_current, atol=1e-9)
    assert np.all(branch_lookup.reshape(-1, 4)[:, 0] == -1)
    np.testing.assert_allclose(ybus.toarray(), ybus.toarray().T, atol=1e-10)
    assert np.sum((vf - vt) * np.conj(series)).real > 0
    copied = nc.passive_branch_data.copy()
    copied.Ycoupling3.data[:] = 0
    assert nc.passive_branch_data.Ycoupling3.nnz > 0
    indices: np.ndarray = np.array((1, 0))
    sliced = nc.passive_branch_data.slice(indices, np.arange(4), np.arange(4), vge.Logger())
    terminal: np.ndarray = np.r_[np.arange(4, 8), np.arange(4), np.arange(12, 16), np.arange(8, 12)]
    np.testing.assert_allclose(sliced.Ycoupling3.toarray(),
                              nc.passive_branch_data.Ycoupling3.toarray()[np.ix_(terminal, terminal)])


@pytest.mark.parametrize('code,order', ((0, (0, 1, 2)), (1, (0, 2, 1)), (2, (1, 0, 2)),
                                       (3, (2, 0, 1)), (4, (1, 2, 0)), (5, (2, 1, 0))))
def test_dgs_phasing_preserves_catalogue(code: int, order: tuple[int, int, int]) -> None:
    """Verify physical-to-electrical phase permutations and independent catalogue variants.

    :param code: PowerFactory physical phase arrangement code.
    :param order: Physical conductor indices in electrical ABC order.
    """
    grid: vge.MultiCircuit = tower_grid()
    original: vge.OverheadLineType = grid.lines[0].template
    initial: np.ndarray = original.z_abc.copy()
    header: dict[str, int] = dict((name, k) for k, name in enumerate((
        'FID', 'loc_name', 'pGeo:SIZEROW', 'pGeo:0', 'plines:SIZEROW', 'plines:0', 'plines:1',
        'dphasing:SIZEROW', 'dphasing:0', 'dphasing:1', 'dpolar:SIZEROW', 'dpolar:0', 'dpolar:1')))
    tow: ElmTow = ElmTow.parse_line(f'section;section;1;type;2;line0;line1;2;{code};0;2;0;1', header)
    assert tow.dphasing == [code, 0] and tow.dpolar == [0, 1]
    dgs: DgsCircuit = DgsCircuit()
    dgs.elmtows.append(tow)
    _apply_elmtow_tower_coupling(dgs, dict((('line0', [grid.lines[0]]), ('line1', [grid.lines[1]]))),
                               dict((('type', original),)), grid.Sbase, grid.fBase, vge.Logger(), grid)
    variant: vge.OverheadLineType = grid.lines[0].template
    permutation: np.ndarray = np.r_[order, (3, 4, 5)]
    electrical: np.ndarray = np.argsort(variant.z_phases_abc)
    np.testing.assert_allclose(variant.z_abc[np.ix_(electrical, electrical)],
                              initial[np.ix_(permutation, permutation)], atol=1e-12)
    np.testing.assert_array_equal(original.z_abc, initial)
    assert [w.phase for w in original.wires_in_tower.data] == [1, 2, 3, 4, 5, 6, 0]
    assert grid.lines[0].coupling_group == grid.lines[1].coupling_group == 'section'
    assert grid.lines[1].coupling_reversed


def test_tower_roundtrip_and_absent_circuit(tmp_path: Path) -> None:
    """Preserve associations on disk and treat an inactive circuit as open, not shorted.

    :param tmp_path: Isolated test output directory.
    """
    grid: vge.MultiCircuit = tower_grid(True)
    path: str = str(tmp_path / 'coupled.veragrid')
    vge.save_file(grid, path)
    restored: vge.MultiCircuit = vge.open_file(path)
    before: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    after: NumericalCircuit = compile_numerical_circuit_at(restored, fill_three_phase=True)
    np.testing.assert_allclose(compute_ybus(before)[0].toarray(), compute_ybus(after)[0].toarray())
    assert restored.lines[1].coupling_reversed
    grid.lines[1].active = False
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    assert nc.passive_branch_data.Ycoupling3.nnz == 0
    tower: vge.OverheadLineType = grid.lines[0].template
    expected: np.ndarray = np.linalg.inv(tower.z_abc[:3, :3] * 35) * 132**2 / grid.Sbase
    np.testing.assert_allclose(nc.passive_branch_data.Yft3[1:4, 1:], -expected)


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_passive_neutral_schur_reconstruction(solver: vge.SolverType) -> None:
    """Check full-network KCL, nonzero neutral voltage and protected nonlinear neutrals.

    :param solver: Existing numerical algorithm, without fallback.
    """
    grid: vge.MultiCircuit = tower_grid()
    # Use an ordinary four-wire line, with its actual neutral retained in the physical model.
    grid.lines = grid.lines[:1]
    grid.buses = grid.buses[:2]
    grid.loads = grid.loads[:1]
    grid.generators = grid.generators[:1]
    grid.lines[0].coupling_group = ''
    grid.lines[0].ys.values = np.linalg.inv(np.array((
        (0.08+0.15j, 0.01j, 0.02j, 0.015j), (0.01j, 0.04+0.12j, 0.015j, 0.02j),
        (0.02j, 0.015j, 0.05+0.13j, 0.01j), (0.015j, 0.02j, 0.01j, 0.04+0.11j))))
    grid.lines[0].ysh.values[:] = 0
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    nc.load_data.S3_star[:] = 0
    nc.load_data.I3_star[:] = 0
    ybus, _, _, _, mask, _, _ = compute_ybus(nc)
    keep, lift = passive_neutral_reduction(nc, ybus, mask)
    assert lift is not None and len(keep) == ybus.shape[0] - 1
    voltage: np.ndarray = np.array((1, np.exp(-2j*np.pi/3), np.exp(2j*np.pi/3),
                                   0.95-0.02j, -0.51-0.85j, -0.46+0.83j))
    full: np.ndarray = lift @ voltage
    eliminated: np.ndarray = np.setdiff1d(np.arange(ybus.shape[0]), keep)
    assert abs(full[eliminated[0]]) > 1e-5
    np.testing.assert_allclose((ybus @ full)[eliminated], 0, atol=1e-12)
    reduced: csc_matrix = ybus[keep, :] @ lift
    np.testing.assert_allclose((ybus @ full)[keep], reduced @ voltage, atol=1e-12)
    nc.load_data.S3_star[1:4] = (1+1j, 2+1j, 3+1j)
    nc.load_data.S3_star[0] = -6-3j
    assert passive_neutral_reduction(nc, ybus, mask)[1] is None
    # A singular passive neutral is retained, rather than silently grounded or regularised.
    nc.load_data.S3_star[:] = 0
    singular: np.ndarray = ybus.toarray()
    singular[eliminated, :] = 0
    singular[:, eliminated] = 0
    assert passive_neutral_reduction(nc, csc_matrix(singular), mask)[1] is None
    # Exercise reconstruction through the public solver/result path as well.
    result = vge.power_flow3ph(grid, options=vge.PowerFlowOptions(solver_type=solver, max_iter=100,
        tolerance=1e-10, control_q=False, retry_with_other_methods=False))
    assert result.converged and abs(result.voltage_N[1]) > 1e-5
    solved: np.ndarray = np.column_stack((result.voltage_N, result.voltage_A,
                                         result.voltage_B, result.voltage_C)).ravel()[mask]
    injection: np.ndarray = ybus @ solved
    np.testing.assert_allclose(injection[eliminated], 0, atol=1e-10)
    np.testing.assert_allclose(injection[keep][-3:],
                              -np.conj(np.array((10+3j, 11+4j, 9+2j)) / solved[keep][-3:]) * 3/100,
                              atol=1e-10)
    np.testing.assert_allclose(result.If_N, 0, atol=1e-10)
