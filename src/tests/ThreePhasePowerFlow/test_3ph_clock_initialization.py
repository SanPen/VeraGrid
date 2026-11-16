"""Clock-aware starts must reach the high-voltage solution without changing warm starts."""
import numpy as np
import pytest
import VeraGridEngine.api as vge
import VeraGridEngine.Simulations.PowerFlow3ph.power_flow_worker_3ph as worker
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.enumerations import WindingType


def clock_grid(reverse: bool = False) -> tuple[vge.MultiCircuit, vge.Transformer2W]:
    """Build a loaded transformer with both port orientations available."""
    grid = vge.MultiCircuit()
    source = grid.add_bus(vge.Bus(name='HV', Vnom=132, is_slack=True))
    target = grid.add_bus(vge.Bus(name='LV', Vnom=33))
    grid.add_generator(source, vge.Generator())
    grid.add_load(target, vge.Load(P=20, Q=5))
    transformer = vge.Transformer2W(bus_from=target if reverse else source,
        bus_to=source if reverse else target, HV=132, LV=33, r=0.01, x=0.1,
        r0=0.02, x0=0.2, r2=0.01, x2=0.1)
    transformer.conn_f = WindingType.GroundedStar if reverse else WindingType.Delta
    transformer.conn_t = WindingType.Delta if reverse else WindingType.GroundedStar
    grid.add_transformer2w(transformer)
    return grid, transformer


@pytest.mark.parametrize('clock', (1, 5, 6, 11))
@pytest.mark.parametrize('reverse', (False, True))
def test_loaded_clock_reaches_same_high_voltage_solution(clock: int, reverse: bool) -> None:
    """Large clock shifts rotate the known solution, rather than selecting a low-voltage root."""
    grid, transformer = clock_grid(reverse)
    options = vge.PowerFlowOptions(tolerance=1e-10, max_iter=15, retry_with_other_methods=False,
                                   control_taps_modules=False, control_taps_phase=False)
    reference = vge.power_flow3ph(grid, options)
    transformer.vector_group_number = clock
    result = vge.power_flow3ph(grid, options)
    assert reference.converged and result.converged
    for phase in ('A', 'B', 'C'):
        expected = getattr(reference, 'voltage_' + phase).copy()
        expected[1] *= np.exp(-1j * np.deg2rad(30 * clock))
        np.testing.assert_allclose(getattr(result, 'voltage_' + phase), expected, atol=1e-9)


def test_three_winding_start_uses_each_terminal_clock() -> None:
    """The existing star equivalent must retain independent MV/LV clocks."""
    grid = vge.MultiCircuit()
    hv = grid.add_bus(vge.Bus(Vnom=110, is_slack=True))
    mv = grid.add_bus(vge.Bus(Vnom=33))
    lv = grid.add_bus(vge.Bus(Vnom=11))
    grid.add_generator(hv, vge.Generator())
    transformer = vge.Transformer3W(bus1=hv, bus2=mv, bus3=lv, V1=110, V2=33, V3=11,
        r12=0.015, x12=0.15, r23=0.022, x23=0.22, r31=0.017, x31=0.17)
    transformer.compute_delta_to_star()
    transformer.fill_zero_sequence(0.03+0.3j, 0.05+0.5j, 0.04+0.4j)
    grid.add_transformer3w(transformer)
    grid.add_load(mv, vge.Load(P=12, Q=3))
    grid.add_load(lv, vge.Load(P=6, Q=1.5))
    options = vge.PowerFlowOptions(tolerance=1e-10, max_iter=15, retry_with_other_methods=False,
                                   control_taps_modules=False, control_taps_phase=False)
    reference = vge.power_flow3ph(grid, options)
    transformer.winding2.vector_group_number = 5
    transformer.winding3.vector_group_number = 11
    result = vge.power_flow3ph(grid, options)
    assert reference.converged and result.converged
    for phase in ('A', 'B', 'C'):
        expected = getattr(reference, 'voltage_' + phase).copy()
        expected[1] *= np.exp(-1j * np.deg2rad(150))
        expected[2] *= np.exp(-1j * np.deg2rad(330))
        np.testing.assert_allclose(getattr(result, 'voltage_' + phase), expected, atol=1e-9)


def test_initialization_preserves_references_magnitudes_and_inputs() -> None:
    """A meshed island with two reference buses must not overwrite either reference."""
    grid, transformer = clock_grid()
    transformer.vector_group_number = 5
    extra = grid.add_bus(vge.Bus(Vnom=33, is_slack=True))
    grid.add_generator(extra, vge.Generator())
    grid.add_line(vge.Line(bus_from=grid.buses[1], bus_to=extra, r=0.02, x=0.1))
    grid.add_line(vge.Line(bus_from=grid.buses[1], bus_to=extra, r=0.03, x=0.2))
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    voltage = np.array((1.02*np.exp(0.1j), 0.97, 1.01*np.exp(-0.3j)))
    original = voltage.copy()
    compiled = nc.bus_data.Vbus.copy()
    result = worker.initialize_angles_3ph(nc, voltage, np.array((0, 2)))
    np.testing.assert_array_equal(voltage, original)
    np.testing.assert_array_equal(nc.bus_data.Vbus, compiled)
    np.testing.assert_array_equal(result[[0, 2]], original[[0, 2]])
    np.testing.assert_allclose(abs(result), abs(original), atol=1e-14)
    np.testing.assert_allclose(result[1], 0.97*np.exp(1j*(0.1-np.deg2rad(150))), atol=1e-14)


def test_warm_starts_and_positive_sequence_do_not_run_the_sweep(monkeypatch: pytest.MonkeyPatch) -> None:
    """The sweep belongs only to a fresh three-phase solve."""
    grid, _ = clock_grid()
    def unexpected_sweep(*args, **kwargs):
        raise AssertionError('The three-phase angle sweep must not run here')
    monkeypatch.setattr(worker, 'initialize_angles_3ph', unexpected_sweep)
    options = vge.PowerFlowOptions(use_stored_guess=True, tolerance=1e-9)
    assert vge.power_flow3ph(grid, options).converged
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    assert worker.multi_island_pf_nc_3ph(nc, vge.PowerFlowOptions(), V_guess=nc.bus_data.Vbus).converged
    assert vge.power_flow(grid, vge.PowerFlowOptions()).converged


def test_line_matrix_does_not_acquire_a_clock_from_scalar_impedance() -> None:
    """An asymmetric line has no winding clock even when its scalar Z1 differs."""
    grid = vge.MultiCircuit()
    source = grid.add_bus(vge.Bus(Vnom=33, is_slack=True))
    target = grid.add_bus(vge.Bus(Vnom=33))
    grid.add_generator(source, vge.Generator())
    grid.add_line(vge.Line(bus_from=source, bus_to=target, r=0.02, x=0.2))
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    impedance = np.array(((0.4+0.7j, 0.1+0.2j, 0.1+0.1j),
                          (0.1+0.2j, 0.3+0.8j, 0.1+0.3j),
                          (0.1+0.1j, 0.1+0.3j, 0.5+0.6j)))
    series = np.linalg.inv(impedance)
    nc.passive_branch_data.Ytt3[1:4, 1:4] = series
    nc.passive_branch_data.Ytf3[1:4, 1:4] = -series
    voltage = np.array((np.exp(0.1j), 0.97))
    result = worker.initialize_angles_3ph(nc, voltage, np.array((0,)))
    np.testing.assert_allclose(result, (voltage[0], 0.97*voltage[0]), atol=1e-14)
