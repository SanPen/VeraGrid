"""Fixed-power sequence injections, independently checked through terminal currents."""
from pathlib import Path
import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmGenstat
from VeraGridEngine.IO.dgs.dgs_to_veragrid import _add_elmgenstat_devices
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.positive_sequence_control import PositiveSequenceControl
from VeraGridEngine.enumerations import ShuntConnectionType


def make_grid(sbase: float, connection: ShuntConnectionType) -> vge.MultiCircuit:
    """Create a public network that excites both negative and zero sequence.

    :param sbase: System power base in MVA.
    :param connection: Generator connection.
    :return: Two-bus test network.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit(Sbase=sbase)
    source: vge.Bus = grid.add_bus(vge.Bus(name='Slack', Vnom=20.0, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(name='PQ', Vnom=20.0))
    grid.add_generator(source, vge.Generator())
    grid.add_line(vge.Line(bus_from=source, bus_to=target, r=0.02*sbase/100, x=0.08*sbase/100,
                          r0=0.04*sbase/100, x0=0.16*sbase/100))
    gen: vge.StaticGenerator = vge.StaticGenerator(P=12.0, Q=3.0, Snom=20.0,
        r0=0.01*sbase/100, x0=0.08*sbase/100, r2=0.02*sbase/100, x2=0.10*sbase/100)
    gen.conn = connection
    grid.add_static_generator(target, gen)
    grid.add_load(target, vge.Load(P=15.0, Q=6.0, P1=8.0, P2=5.0, P3=2.0,
                                  Q1=3.0, Q2=2.0, Q3=1.0))
    return grid


@pytest.mark.parametrize('sbase', (25.0, 100.0))
@pytest.mark.parametrize('connection', (ShuntConnectionType.GroundedStar, ShuntConnectionType.FloatingStar,
                                       ShuntConnectionType.Delta))
@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_sequence_injection_terminal_currents(sbase: float, connection: ShuntConnectionType,
                                              solver: vge.SolverType) -> None:
    """Verify the source from line terminal powers, without reading its implementation.

    :param sbase: System power base.
    :param connection: Physical return path.
    :param solver: Existing numerical method, with fallback disabled.
    """
    grid: vge.MultiCircuit = make_grid(sbase, connection)
    result: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, options=vge.PowerFlowOptions(
        solver_type=solver, tolerance=1e-9, max_iter=100, control_q=False, retry_with_other_methods=False))
    assert result.converged
    voltage: np.ndarray = np.array((result.voltage_A[1], result.voltage_B[1], result.voltage_C[1]))
    # KCL: generator power equals the colocated load plus power entering the line.
    power: np.ndarray = np.array((result.St_A[0], result.St_B[0], result.St_C[0]))
    power += np.array((8+3j, 5+2j, 2+1j))
    current: np.ndarray = np.conj(power/voltage)*3/sbase
    a: complex = np.exp(2j*np.pi/3)
    transform: np.ndarray = np.array(((1,1,1), (1,a,a*a), (1,a*a,a)))/3
    v012: np.ndarray = transform@voltage
    i012: np.ndarray = transform@current
    expected_i0: complex = -v012[0]/((0.01+0.08j)*sbase/100) if connection == ShuntConnectionType.GroundedStar else 0j
    np.testing.assert_allclose(i012, (expected_i0, np.conj((12+3j)/sbase/v012[1]),
        -v012[2]/((0.02+0.10j)*sbase/100)), atol=2e-8, rtol=1e-7)
    assert abs(v012[2]) > 1e-4


@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_balanced_static_sequence_matches_positive_flow(sbase: float) -> None:
    """Recover the existing positive-sequence solution in the balanced limit.

    :param sbase: System power base.
    """
    grid: vge.MultiCircuit = make_grid(sbase, ShuntConnectionType.FloatingStar)
    load: vge.Load = grid.loads[0]
    load.Pa = load.Pb = load.Pc = 5.0
    load.Qa = load.Qb = load.Qc = 2.0
    abc: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, options=vge.PowerFlowOptions(tolerance=1e-9))
    positive: vge.PowerFlowResults = vge.power_flow(grid, options=vge.PowerFlowOptions(tolerance=1e-9))
    assert abc.converged and positive.converged
    np.testing.assert_allclose(abc.voltage_A, positive.voltage, atol=1e-8)
    np.testing.assert_allclose(abc.voltage_B, positive.voltage*np.exp(-2j*np.pi/3), atol=1e-8)


@pytest.mark.parametrize('power', (0j, 8+2j, -4-1j))
def test_static_sequence_uses_compiled_power(power: complex) -> None:
    """Read the current compiled S, including zero power and reversed power flow.

    :param power: Updated generator injection in MW+jMVAr.
    """
    grid: vge.MultiCircuit = make_grid(100.0, ShuntConnectionType.FloatingStar)
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    # Numerical consumers may update S after compilation; there must be no stale copy.
    nc.load_data.S[1] = -power
    control: PositiveSequenceControl = PositiveSequenceControl(nc, np.arange(4 * nc.nbus))
    a: complex = np.exp(2j * np.pi / 3)
    voltage: np.ndarray = np.array((0j, 1, a*a, a, 0j, 1.03, 0.97*a*a, 1.01*a))
    currents: np.ndarray = np.zeros(4 * nc.nbus, dtype=complex)
    control.add_currents(currents, voltage, control.q)
    # A pure I1 source delivers its specified complex power at an unbalanced voltage.
    np.testing.assert_allclose(np.sum(voltage[5:8] * currents[5:8].conj()), power, atol=1e-12)
    np.testing.assert_allclose(currents[5:8], currents[5] * np.array((1, a*a, a)), atol=1e-12)
    np.testing.assert_allclose(currents[:5], 0j, atol=1e-12)


def test_static_sequence_profiles_copy_islands_and_persistence(tmp_path: Path) -> None:
    """Retain inputs through the native file and numerical copy/island paths.

    :param tmp_path: Isolated test directory.
    """
    grid: vge.MultiCircuit = make_grid(100.0, ShuntConnectionType.FloatingStar)
    gen: vge.StaticGenerator = grid.static_generators[0]
    gen.use_kw = True
    gen.P = 12000.0
    gen.Q = 3000.0
    gen.P_prof = np.array((18000.0,))
    gen.Q_prof = np.array((6000.0,))
    path: Path = tmp_path/'sequence.veragrid'
    vge.save_file(grid, str(path))
    restored: vge.MultiCircuit = vge.open_file(str(path))
    np.testing.assert_allclose((restored.static_generators[0].R0, restored.static_generators[0].X0,
                               restored.static_generators[0].R2, restored.static_generators[0].X2),
                              (0.01,0.08,0.02,0.10))
    assert restored.static_generators[0].conn == ShuntConnectionType.FloatingStar
    nc: NumericalCircuit = compile_numerical_circuit_at(grid,t_idx=0,fill_three_phase=True)
    assert nc.load_data.S[1] == -18-6j
    assert nc.load_data.is_positive_sequence[1]
    for copied in (nc.copy(),nc.split_into_islands()[0]):
        np.testing.assert_allclose(copied.load_data.S,nc.load_data.S)
        np.testing.assert_array_equal(copied.load_data.is_positive_sequence,nc.load_data.is_positive_sequence)
        np.testing.assert_allclose(copied.load_data.Y3_star,nc.load_data.Y3_star)
    # Explicit per-phase power inputs retain the previous behaviour even with sequence data.
    gen.Pa, gen.Pb, gen.Pc = 1000,2000,3000
    explicit: NumericalCircuit = compile_numerical_circuit_at(grid,fill_three_phase=True)
    assert not explicit.load_data.is_positive_sequence[1]
    assert np.any(explicit.load_data.S3_floatingstar)
    gen.active = False
    offline: NumericalCircuit = compile_numerical_circuit_at(grid,fill_three_phase=True)
    assert not np.any(offline.load_data.is_positive_sequence)
    assert not np.any(offline.load_data.Y3_star)


@pytest.mark.parametrize('sbase,parallel', ((25.0,2),(100.0,1)))
@pytest.mark.parametrize('technology,connection', ((0,ShuntConnectionType.FloatingStar),
                                                 (1,ShuntConnectionType.GroundedStar)))
def test_dgs_pq_imports_sequence_data(sbase: float, parallel: int, technology: int,
                                     connection: ShuntConnectionType) -> None:
    """Exercise both existing PQ import branches with machine/system base conversion.

    :param sbase: Circuit power base.
    :param parallel: Parallel units, each with its own rating.
    :param technology: Native 3PH or 3PH-E.
    :param connection: Expected return path.
    """
    for category in ('Wind','Other'):
        grid: vge.MultiCircuit = vge.MultiCircuit(Sbase=sbase)
        grid.add_bus(vge.Bus(Vnom=20.0))
        dgs: DgsCircuit = DgsCircuit()
        source: ElmGenstat = ElmGenstat()
        source.ID = 'pq'
        source.loc_name = 'Sequence PQ'
        source.cCategory = category
        source.av_mode = 'constq'
        source.pgini = 12.0
        source.qgini = 3.0
        source.sgn = 20.0
        source.ngnum = parallel
        source.phtech = technology
        source.nneutral = 0
        source.r0,source.x0,source.r2,source.x2 = 0.01,0.08,0.02,0.10
        dgs.elmgenstats.append(source)
        _add_elmgenstat_devices(dgs,grid,dict((('pq',list((0,))),)),False,vge.Logger(),dict(),dict())
        assert len(grid.static_generators) == parallel
        for gen in grid.static_generators:
            assert gen.conn == connection
            np.testing.assert_allclose((gen.R0,gen.X0,gen.R2,gen.X2),
                                       np.array((0.01,0.08,0.02,0.10))*sbase/20)
        nc: NumericalCircuit = compile_numerical_circuit_at(grid,fill_three_phase=True)
        np.testing.assert_allclose(nc.load_data.S,np.full(parallel,-12-3j))
        assert np.all(nc.load_data.is_positive_sequence)
        assert not np.any(nc.load_data.S3_star)


@pytest.mark.parametrize('invalid', ('ground','neutral','nonfinite'))
def test_static_sequence_input_diagnostics(invalid: str) -> None:
    """Report unsupported or invalid sequence data before entering the solver.

    :param invalid: Data inconsistency to exercise.
    :return: None.
    """
    grid: vge.MultiCircuit = make_grid(100.0,ShuntConnectionType.GroundedStar)
    gen: vge.StaticGenerator = grid.static_generators[0]
    message: str = (r'Non-finite value rejected for StaticGenerator\.X2'
                    if invalid == 'nonfinite' else '[Ss]tatic generator')
    # Include assignment so devel's finite-value contract is checked directly.
    with pytest.raises(ValueError, match=message):
        if invalid == 'ground':
            gen.R0 = gen.X0 = 0.0
        elif invalid == 'neutral':
            gen.conn = ShuntConnectionType.NeutralStar
        else:
            gen.X2 = np.nan
        compile_numerical_circuit_at(grid,fill_three_phase=True)
