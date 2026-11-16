"""Phase faults must not depend on the source bus position or absent phases."""
from pathlib import Path
import warnings

import numpy as np
import pytest
from scipy.sparse.linalg import MatrixRankWarning

import VeraGridEngine.api as vg


@pytest.mark.parametrize('fault_type,phases', [
    (vg.FaultType.LG, vg.PhasesShortCircuit.a),
    (vg.FaultType.LLLG, vg.PhasesShortCircuit.abc),
])
def test_phase_fault_source_bus_order(fault_type: vg.FaultType,
                                     phases: vg.PhasesShortCircuit) -> None:
    """Compare IEEE13 bus voltages and branch currents with the source first or later."""
    path = Path(__file__).resolve().parents[1] / 'data/grids/DGS/ieee13_bus_test_feeder.dgs'
    grid = vg.open_file(str(path))
    source = grid.generators[0]
    assert grid.buses.index(source.bus) > 0
    # Use finite sequence impedances to isolate indexing from source conditioning.
    source.R0 = source.R1 = source.R2 = 0.01
    source.X0 = source.X1 = source.X2 = 0.2
    target = next(bus for bus in grid.buses if bus.name == '634')
    grid.add_short_circuit_event(vg.ShortCircuitEvent(
        device=target, method=vg.MethodShortCircuit.phases,
        fault_type=fault_type, phases=phases, r_fault=0.01,
    ))
    options = vg.PowerFlowOptions(tolerance=1e-10, max_iter=100)
    original_order = grid.buses.copy()
    results = []

    for source_first in (True, False):
        grid.buses = ([source.bus] + [bus for bus in original_order if bus is not source.bus]
                      if source_first else original_order)
        pf = vg.power_flow3ph(grid, options)
        assert pf.converged
        assert pf.voltage_A[grid.buses.index(next(bus for bus in grid.buses if bus.name == '611'))] == 0
        driver = vg.ShortCircuitDriver(grid, vg.ShortCircuitOptions(), options, None, pf)
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            warnings.simplefilter('error', MatrixRankWarning)
            driver.run()
        assert not driver.logger.has_errors(), str(driver.logger)
        order = [grid.buses.index(bus) for bus in original_order]
        voltage: np.ndarray = np.column_stack((driver.results.voltageA[order, 0],
                                               driver.results.voltageB[order, 0],
                                               driver.results.voltageC[order, 0]))
        current: np.ndarray = np.column_stack((driver.results.IfA[:, 0],
                                               driver.results.IfB[:, 0],
                                               driver.results.IfC[:, 0]))
        assert np.isfinite(voltage).all() and np.isfinite(current).all()
        assert np.max(np.abs(voltage)) > 0.1
        assert np.max(np.abs(current)) > 0.1
        results.append((voltage, current))

    for first, later in zip(results[0], results[1]):
        np.testing.assert_allclose(first, later, rtol=1e-7, atol=1e-8)
