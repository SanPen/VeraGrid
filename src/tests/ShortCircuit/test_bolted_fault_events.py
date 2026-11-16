"""Zero-impedance events must reach the short-circuit calculation."""
import warnings

import numpy as np
import pytest

import VeraGridEngine.api as vg


@pytest.fixture
def fault_grid():
    """Independent phases with a known generator-plus-line Thevenin impedance."""
    grid = vg.MultiCircuit(Sbase=100)
    source = grid.add_bus(vg.Bus(name='Source', Vnom=10, is_slack=True))
    target = grid.add_bus(vg.Bus(name='Fault', Vnom=10))
    grid.add_generator(source, vg.Generator(r0=.01, x0=.2, r1=.01, x1=.2, r2=.01, x2=.2))
    grid.add_line(vg.Line(bus_from=source, bus_to=target,
                          r=.01, x=.1, r0=.01, x0=.1, r2=.01, x2=.1))
    options = vg.PowerFlowOptions(control_q=False)
    pf = vg.power_flow(grid, options)
    pf3 = vg.power_flow3ph(grid, options)
    assert pf.converged and pf3.converged
    return grid, options, pf, pf3


def run_fault(fault_grid, event):
    grid, options, pf, pf3 = fault_grid
    grid.short_circuit_event.clear()
    grid.add_short_circuit_event(event)
    driver = vg.ShortCircuitDriver(grid, vg.ShortCircuitOptions(), options, pf, pf3)
    with warnings.catch_warnings():
        warnings.simplefilter('error', RuntimeWarning)
        driver.run()
    return driver


@pytest.mark.parametrize('fault_type,phases', [
    (vg.FaultType.LG, vg.PhasesShortCircuit.a),
    (vg.FaultType.LG, vg.PhasesShortCircuit.b),
    (vg.FaultType.LG, vg.PhasesShortCircuit.c),
    (vg.FaultType.LLG, vg.PhasesShortCircuit.ab),
    (vg.FaultType.LLG, vg.PhasesShortCircuit.bc),
    (vg.FaultType.LLG, vg.PhasesShortCircuit.ca),
    (vg.FaultType.LLLG, vg.PhasesShortCircuit.abc),
])
def test_bolted_ground_fault_phases_matches_thevenin(fault_grid, fault_type, phases):
    grid, _, _, pf3 = fault_grid
    event = vg.ShortCircuitEvent(device=grid.buses[1], method=vg.MethodShortCircuit.phases,
                                fault_type=fault_type, phases=phases, r_fault=0, x_fault=0)
    driver = run_fault(fault_grid, event)
    assert not driver.logger.has_errors(), str(driver.logger)
    assert event.get_fault_impedance() == 0j

    for phase in 'ABC':
        voltage = getattr(driver.results, f'voltage{phase}')[:, 0]
        current = getattr(driver.results, f'If{phase}')[0, 0]
        prefault = getattr(pf3, f'voltage_{phase}')[0]
        if phase.lower() in phases.value:
            expected_current = prefault / (.02 + .3j)
            expected_voltage = [prefault - (.01 + .2j) * expected_current, 0j]
        else:
            expected_current = 0j
            expected_voltage = [prefault, prefault]
        np.testing.assert_allclose(voltage, expected_voltage, atol=1e-6)
        np.testing.assert_allclose(current, expected_current, atol=1e-6)


@pytest.mark.parametrize('fault_type,phases', [
    (vg.FaultType.LG, vg.PhasesShortCircuit.a),
    (vg.FaultType.LL, vg.PhasesShortCircuit.bc),
    (vg.FaultType.LLG, vg.PhasesShortCircuit.bc),
    (vg.FaultType.LLL, vg.PhasesShortCircuit.abc),
    (vg.FaultType.LLLG, vg.PhasesShortCircuit.abc),
])
def test_bolted_sequence_event_matches_small_impedance_limit(fault_grid, fault_type, phases):
    grid, _, _, _ = fault_grid
    event = vg.ShortCircuitEvent(device=grid.buses[1], method=vg.MethodShortCircuit.sequences,
                                fault_type=fault_type, phases=phases, r_fault=0, x_fault=0)
    bolted = run_fault(fault_grid, event)
    assert not bolted.logger.has_errors(), str(bolted.logger)
    assert event.get_fault_impedance() == 0j
    assert np.any(abs(bolted.results.voltage1) > 0)

    event.r_fault = 1e-8
    reference = run_fault(fault_grid, event)
    assert not reference.logger.has_errors(), str(reference.logger)
    for name in ('voltage0', 'voltage1', 'voltage2', 'If0', 'If1', 'If2'):
        np.testing.assert_allclose(getattr(bolted.results, name),
                                   getattr(reference.results, name), atol=1e-6)


@pytest.mark.parametrize('resistance', [np.nan, np.inf])
def test_nonfinite_fault_impedance_still_rejected(resistance: float) -> None:
    """Reject non-finite resistance when constructing the fault event.

    :param resistance: Invalid resistance supplied by the caller.
    :return: None.
    """
    target: vg.Bus = vg.Bus(name='Fault', Vnom=10)
    with pytest.raises(ValueError, match=r'Non-finite value rejected for ShortCircuitEvent\._r_fault'):
        vg.ShortCircuitEvent(device=target, r_fault=resistance)
