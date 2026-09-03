import json
import math
from pathlib import Path

import VeraGridEngine.api as vge
from VeraGridEngine import PowerFlowOptions, ShortCircuitOptions
from VeraGridEngine.enumerations import FaultType, MethodShortCircuit, PhasesShortCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import SolverType
import numpy as np
import pytest


TEST_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SP_SHORT_CIRCUIT_GRID = TEST_DATA_DIR / "grids" / "shortcircuit_sp.dgs"
SP_LOPA3_REFERENCE = TEST_DATA_DIR / "grids" / "json" / "sp_lopa3_short_circuit_veragrid_reference.json"


def _sp_short_circuit_pf_options() -> PowerFlowOptions:
    return PowerFlowOptions(solver_type=SolverType.NR,
                            retry_with_other_methods=True,
                            control_q=False,
                            control_taps_modules=False,
                            control_taps_phase=False,
                            control_remote_voltage=False,
                            apply_temperature_correction=False,
                            initialize_angles=False,
                            ignore_single_node_islands=True,
                            use_stored_guess=False,
                            use_autodiff_jacobian=True,
                            tolerance=1e-8,
                            max_iter=50)


def _complex_angle_deg(value: complex) -> float:
    return float(np.degrees(np.angle(value)))


def _fault_current_ka(voltage_pu: float, vnom_kv: float, rf_ohm: float) -> float:
    return float(voltage_pu) * float(vnom_kv) / (math.sqrt(3.0) * float(rf_ohm))


def _injected_current(injected_s_mva: complex,
                      voltage_pu_complex: complex,
                      vnom_kv: float,
                      sbase_mva: float) -> tuple[float, float]:
    v_kv = abs(voltage_pu_complex) * float(vnom_kv)
    current_ka = abs(injected_s_mva) / (math.sqrt(3.0) * v_kv)
    current_pu = np.conj((injected_s_mva / float(sbase_mva)) / voltage_pu_complex)
    return float(current_ka), _complex_angle_deg(current_pu)


def _is_wind_vsc(name: str) -> bool:
    return name.startswith("WTG_") or name.startswith("EMW_")


def _find_bus_index(grid: vge.MultiCircuit, name: str, vnom_kv: float) -> int:
    matches = [
        idx for idx, bus in enumerate(grid.buses)
        if str(bus.name) == name and np.isclose(float(bus.Vnom), float(vnom_kv), atol=1e-9)
    ]
    assert len(matches) == 1
    return matches[0]


def _assert_numeric_block_close(actual: dict[str, float], expected: dict[str, float], context: str) -> None:
    assert set(actual) == set(expected), context
    for key, expected_value in expected.items():
        actual_value = actual[key]
        rtol = 5e-5
        if key.endswith("_angle_deg"):
            atol = 5e-3
        elif key.endswith("_ka"):
            atol = 1e-4
        elif key.endswith("_mw") or key.endswith("_mvar"):
            atol = 5e-3
        elif key.endswith("_pu"):
            atol = 2e-5
        else:
            atol = 1e-6

        assert np.isclose(actual_value, expected_value, rtol=rtol, atol=atol), (
            f"{context}.{key}: {actual_value} != {expected_value}"
        )


def _fault_bus_block(sc_results, bus_index: int, event_index: int, vnom_kv: float, rf_ohm: float) -> dict[str, float]:
    voltage = sc_results.voltage1[bus_index, event_index]
    voltage_pu = float(abs(voltage))
    voltage_angle_deg = _complex_angle_deg(voltage)
    return {
        "voltage_pu": voltage_pu,
        "voltage_angle_deg": voltage_angle_deg,
        "current_ka": _fault_current_ka(voltage_pu=voltage_pu, vnom_kv=vnom_kv, rf_ohm=rf_ohm),
        "current_angle_deg": voltage_angle_deg,
    }


def _changed_wind_generator_blocks(grid: vge.MultiCircuit,
                                   pf_results,
                                   sc_results,
                                   event_index: int,
                                   changed_power_tol: float) -> dict[str, dict[str, float]]:
    bus_names = [str(bus.name) for bus in grid.buses]
    vsc_bus_to_indices = [bus_names.index(str(vsc.bus_to.name)) for vsc in grid.vsc_devices]
    blocks = {}

    for idx, vsc in enumerate(grid.vsc_devices):
        name = str(vsc.name)
        if not _is_wind_vsc(name):
            continue

        base = -pf_results.St_vsc[idx]
        injected = -sc_results.vsc_St[idx, event_index]
        delta = injected - base
        delta_p_mw = float(np.real(delta))
        delta_q_mvar = float(np.imag(delta))
        if abs(delta_p_mw) <= changed_power_tol and abs(delta_q_mvar) <= changed_power_tol:
            continue

        terminal_voltage = sc_results.voltage1[vsc_bus_to_indices[idx], event_index]
        current_ka, current_angle_deg = _injected_current(injected_s_mva=injected,
                                                          voltage_pu_complex=terminal_voltage,
                                                          vnom_kv=float(vsc.bus_to.Vnom),
                                                          sbase_mva=float(grid.Sbase))
        blocks[name] = {
            "base_p_mw": float(np.real(base)),
            "base_q_mvar": float(np.imag(base)),
            "p_mw": float(np.real(injected)),
            "q_mvar": float(np.imag(injected)),
            "delta_p_mw": delta_p_mw,
            "delta_q_mvar": delta_q_mvar,
            "terminal_voltage_pu": float(abs(terminal_voltage)),
            "terminal_voltage_angle_deg": _complex_angle_deg(terminal_voltage),
            "current_ka": current_ka,
            "current_angle_deg": current_angle_deg,
        }

    return blocks


@pytest.mark.skip
def test_sp_top50_lopa3_short_circuit_json_sweep():
    with SP_LOPA3_REFERENCE.open(encoding="utf-8") as fh:
        reference = json.load(fh)

    bus_name = reference["metadata"]["bus"]
    vnom_kv = reference["metadata"]["vnom_kv"]
    target_axis = reference["metadata"]["target_voltage_axis_pu"]
    changed_power_tol = reference["metadata"]["changed_power_tol_mw_mvar"]
    reference_data = reference["data"][bus_name]

    assert reference["metadata"]["software"] == "veragrid"
    assert target_axis == [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    assert set(reference_data) == {f"{target:.1f}" for target in target_axis}

    grid = vge.open_file(str(SP_SHORT_CIRCUIT_GRID),
                         options=vge.FileOpenOptions(dgs_use_vsc_for_injections=True))
    bus_index = _find_bus_index(grid=grid, name=bus_name, vnom_kv=vnom_kv)
    fault_bus = grid.buses[bus_index]
    zbase_ohm = float(fault_bus.Vnom) * float(fault_bus.Vnom) / float(grid.Sbase)

    pf_options = _sp_short_circuit_pf_options()
    pf_results = vge.power_flow(grid=grid, options=pf_options)

    assert np.all(pf_results.converged)
    assert np.max(pf_results.error) < 1e-7

    events = []
    for target in target_axis:
        target_label = f"{target:.1f}"
        point = reference_data[target_label]
        events.append(
            vge.ShortCircuitEvent(
                device=fault_bus,
                name=f"{bus_name} target {target_label} pu",
                active=True,
                constz=True,
                fault_type=FaultType.LLLG,
                method=MethodShortCircuit.sequences_vsc,
                phases=PhasesShortCircuit.abc,
                r_fault=point["rf_ohm"] / zbase_ohm,
                x_fault=point["x_f_ohm"] / zbase_ohm,
            )
        )
    grid.short_circuit_event = events

    sc_driver = vge.ShortCircuitDriver(grid=grid,
                                       options=ShortCircuitOptions(),
                                       pf_options=pf_options,
                                       pf_results=pf_results,
                                       pf_results3ph=None)
    sc_driver.run()
    sc_results = sc_driver.results

    assert sc_results.voltage1.shape[1] == len(target_axis)

    for event_index, target in enumerate(target_axis):
        target_label = f"{target:.1f}"
        expected_point = reference_data[target_label]
        event = events[event_index]

        _assert_numeric_block_close(
            actual={
                "target_voltage_pu": target,
                "rf_ohm": event.r_fault * zbase_ohm,
                "x_f_ohm": event.x_fault * zbase_ohm,
            },
            expected={
                "target_voltage_pu": expected_point["target_voltage_pu"],
                "rf_ohm": expected_point["rf_ohm"],
                "x_f_ohm": expected_point["x_f_ohm"],
            },
            context=f"{bus_name} target {target_label} fault_setup",
        )

        _assert_numeric_block_close(
            actual=_fault_bus_block(sc_results=sc_results,
                                    bus_index=bus_index,
                                    event_index=event_index,
                                    vnom_kv=vnom_kv,
                                    rf_ohm=expected_point["rf_ohm"]),
            expected=expected_point["veragrid"]["fault_bus"],
            context=f"{bus_name} target {target_label} fault_bus",
        )

        actual_changed = _changed_wind_generator_blocks(grid=grid,
                                                        pf_results=pf_results,
                                                        sc_results=sc_results,
                                                        event_index=event_index,
                                                        changed_power_tol=changed_power_tol)
        expected_changed = expected_point["veragrid"]["changed_wind_generators"]

        assert set(actual_changed) == set(expected_changed), f"{bus_name} target {target_label} changed generators"
        for generator, expected_block in expected_changed.items():
            _assert_numeric_block_close(
                actual=actual_changed[generator],
                expected=expected_block,
                context=f"{bus_name} target {target_label} changed {generator}",
            )


def test_sp_west():

    grid = vge.open_file('data/grids/test_reduced_sp_v10.dgs',
                         options=vge.FileOpenOptions(dgs_use_vsc_for_injections=True))

    pf_options = PowerFlowOptions(control_taps_modules=False,
                                  use_autodiff_jacobian=True)
    res_pf = vge.power_flow(grid=grid, options=pf_options)

    DUNH0G = 1.0177
    WHLL0G = 1.0174
    TWEN0G = 1.0182
    SNQR0G = 1.0108
    SAKN0G = 1.0013
    AFTO0G = 1.0159
    WNDR0G = 1.0024
    NOKY0B = 1.0087
    NOKY0A = 1.0087
    SOKY0G = 1.0091
    ENHI0G = 1.0086
    DESA0G = 1.0089
    BLKS0G = 1.0189

    assert np.allclose(np.abs(res_pf.voltage[11]), DUNH0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[47]), WHLL0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[45]), TWEN0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[40]), SNQR0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[37]), SAKN0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[0]), AFTO0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[49]), WNDR0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[33]), NOKY0B, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[32]), NOKY0A, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[42]), SOKY0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[17]), ENHI0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[8]), DESA0G, atol=1e-4)
    assert np.allclose(np.abs(res_pf.voltage[6]), BLKS0G, atol=1e-4)


def test_sp_north():

    v_powerfactory = np.array([
        1.024555, 1.015524, 1.015895, 1.034784, 1.031238, 1.024810, 1.074590, 1.074605,
        1.081009, 1.000000, 1.000000, 1.016668, 1.016677, 1.075665, 1.072288, 1.076095,
        1.076068, 1.073081, 1.073386, 1.013502, 1.013502, 1.019082, 1.035745, 1.045892,
        1.037262, 1.011622, 1.011622, 1.027771, 1.039984, 1.066080, 1.076443, 1.076417,
        1.069907, 1.062895, 1.062901, 1.062887, 1.062893, 1.039789, 1.035278, 1.026786,
        1.063884, 1.041257, 1.072647, 1.071983, 1.064949, 1.064959, 1.068474, 1.068977,
        1.067204, 1.067174, 1.017362, 1.017362, 1.034540, 1.034540, 1.066432, 1.068037,
        1.048957, 1.069123, 1.058824, 1.058825, 1.064842, 1.064842, 1.076505, 1.042604,
        1.055452, 1.055880, 1.027097, 1.041610, 1.031120, 1.039729, 1.069974, 1.069989,
        1.056466, 1.072150, 1.024699, 1.066100, 1.071983, 1.056445, 1.072119, 1.024692,
        1.066099, 1.071952, 1.014495, 1.041119, 1.073394, 1.073351, 1.077001, 1.076958,
        1.072863, 1.077061, 1.076995, 1.069653, 1.069653, 1.066460, 1.076297, 1.065425,
        1.078088, 1.068658, 1.066911, 1.067005, 1.031147, 1.037378, 1.000000, 1.000000,
        1.064828, 1.057504, 1.057500, 1.066129, 1.000000, 1.025350, 1.045269, 1.076485,
        1.076460, 1.071684, 1.072658, 1.072657, 1.029825, 1.023753, 1.029852, 1.023776,
        1.076153, 1.066183, 1.064769, 1.064770, 1.066460, 1.066421, 1.072099, 1.068079,
        1.072089, 1.068081, 1.066239, 1.066249, 1.072030, 1.061188, 1.071999, 1.061157,
        1.076307, 1.076306
    ], dtype=float)

    assert v_powerfactory.size == 138

    # ------------------------------------------------------------------------------------------------------------------
    #   AC/DC Power Flow under healthy conditions
    # ------------------------------------------------------------------------------------------------------------------
    grid = vge.open_file('data/grids/11_05_sp.dgs',
                         options=vge.FileOpenOptions(dgs_use_vsc_for_injections=True))

    pf_options = PowerFlowOptions(solver_type=SolverType.NR,
                                  retry_with_other_methods=False,
                                  limit_i_vsc=False,
                                  control_taps_modules=False,  # keeps taps fixed → limited support behaves like basic
                                  control_taps_phase=False,
                                  use_stored_guess=True,
                                  use_autodiff_jacobian=True,
                                  verbose=0)
    res_pf = vge.power_flow(grid=grid, options=pf_options)

    v_veragrid = np.abs(res_pf.voltage[0:138])

    assert v_veragrid.size == 138

    assert np.allclose(v_veragrid, v_powerfactory, atol=1e-3)
