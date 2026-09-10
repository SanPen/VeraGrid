"""Integration checks for the small dynamics-based persistent-fault example."""
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "examples"))
from dynamic_fault_equilibrium import (
    hardcoded_reference, physical_results, run_case, solve_equilibrium,
)


@pytest.fixture(scope="module")
def current_limited_case():
    return run_case(fault_r=0.15)


@pytest.mark.parametrize("fault_r", [0.3, 0.15])
def test_rms_equilibrium_matches_time_domain_and_legacy(fault_r, current_limited_case):
    """Cover unsaturated voltage support and current limiting."""
    result = current_limited_case if fault_r == 0.15 else run_case(fault_r=fault_r)
    prefault, legacy = hardcoded_reference(fault_r)
    assert legacy is not None
    voltage, power, current, fault_current, kcl = physical_results(result)
    assert len(result["grid"].buses) == 2
    assert result["problem"].get_states_number() == 3
    np.testing.assert_allclose(result["pf"].voltage, prefault.voltage[:2], atol=1e-9, rtol=0)
    np.testing.assert_allclose(voltage, legacy.voltage1[:2, 0], atol=1e-6, rtol=0)
    np.testing.assert_allclose(power * 100.0, -legacy.vsc_St[0, 0], atol=5e-6, rtol=0)
    assert result["endpoint_error"] < 1e-6
    assert result["final_residual"] < 1e-6
    assert kcl < 1e-8
    assert abs(fault_current) > 0.0
    if fault_r == 0.15:
        assert abs(current) / 0.5 == pytest.approx(1.3, abs=1e-8)
    else:
        assert 0.0 < abs(current) / 0.5 < 1.3


def test_procedural_blocking_matches_time_domain_and_passive_network():
    """Check blocking against the exact passive-network solution at zero injection."""
    result = run_case(fault_r=0.15, blocking_voltage=0.5)
    voltage, _, current, _, kcl = physical_results(result)
    emf = result["emf"][0] * np.exp(1j * result["emf"][1])
    passive_current = emf / (complex(0.02, 0.4) + 0.15)
    np.testing.assert_allclose(voltage[1], passive_current * 0.15, atol=1e-9, rtol=0)
    assert abs(current) < 1e-10
    assert result["endpoint_error"] < 1e-6
    assert kcl < 1e-8


def test_deep_fault_does_not_accept_spurious_zero_voltage_root():
    """The limited polar Newton prototype must reject its collapsed solution branch."""
    with pytest.raises(RuntimeError, match="Equilibrium Newton"):
        run_case(fault_r=0.02)


def test_converter_states_are_unknowns_not_frozen(current_limited_case):
    """All states change, and a different Newton seed reaches the same solution."""
    result = current_limited_case
    indices = result["state_indices"]
    assert np.all(np.abs(result["equilibrium"][indices] - result["initial"][indices]) > 0.01)
    different_seed = result["initial"].copy()
    different_seed[indices] = [0.7, 0.1, 0.2]
    solution, _ = solve_equilibrium(result["problem"], different_seed)
    np.testing.assert_allclose(solution, result["equilibrium"], atol=1e-8, rtol=0)


def test_model_gain_changes_fault_result_without_solver_changes(current_limited_case):
    """Changing a model parameter affects both the equilibrium and RMS endpoint."""
    changed = run_case(fault_r=0.15, kqv=1.0)
    baseline = current_limited_case
    v_base = baseline["equilibrium"][baseline["vm_indices"][1]]
    v_changed = changed["equilibrium"][changed["vm_indices"][1]]
    assert abs(v_base - v_changed) > 0.01
    assert changed["endpoint_error"] < 1e-6


def test_time_constant_changes_transient_but_not_equilibrium(current_limited_case):
    """The same model equations support physical time evolution and t→∞."""
    slower = run_case(current_tau=0.05, end_time=2.0)
    baseline = current_limited_case
    np.testing.assert_allclose(slower["equilibrium"], baseline["equilibrium"], atol=1e-8, rtol=0)
    baseline_sample = np.argmin(abs(baseline["times"] - 0.13))
    slower_sample = np.argmin(abs(slower["times"] - 0.13))
    iq_base = baseline["trajectory"][baseline_sample, baseline["state_indices"][2]]
    iq_slow = slower["trajectory"][slower_sample, slower["state_indices"][2]]
    assert abs(iq_base - iq_slow) > 0.05
