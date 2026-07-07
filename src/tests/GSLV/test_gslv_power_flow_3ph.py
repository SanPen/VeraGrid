from __future__ import annotations

import numpy as np

import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.circuit_to_gslv import GSLV_AVAILABLE
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_ts_results_3ph import PowerFlowTimeSeriesResults3Ph


def _build_3ph_options() -> vg.PowerFlowOptions:
    """
    Build one deterministic three-phase power-flow options object.

    :return: Power-flow options.
    """
    return vg.PowerFlowOptions(
        solver_type=vg.SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=False,
        tolerance=1e-8,
        max_iter=80,
        control_q=False,
        control_taps_modules=True,
        control_taps_phase=True,
        control_remote_voltage=True,
        orthogonalize_controls=True,
        apply_temperature_correction=True,
        branch_impedance_tolerance_mode=vg.BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=False,
        generate_report=False,
    )


def _build_unbalanced_3ph_grid() -> vg.MultiCircuit:
    """
    Build one small unbalanced three-phase grid used for engine comparison.

    :return: Three-phase test grid.
    """
    grid: vg.MultiCircuit = vg.MultiCircuit(name="gslv-3ph-integration")

    # The time profile is created first so every injected device allocates its
    # profiles with the target time dimension from the beginning.
    grid.set_unix_time(np.array([0, 3600, 7200], dtype=np.int64))

    slack_bus: vg.Bus = vg.Bus(name="Slack", Vnom=10.0, is_slack=True)
    load_bus: vg.Bus = vg.Bus(name="Load", Vnom=10.0)
    grid.add_bus(slack_bus)
    grid.add_bus(load_bus)

    slack_gen: vg.Generator = vg.Generator(
        name="SlackGen",
        P=0.0,
        Q=0.0,
        vset=1.0,
        control_mode=vg.GeneratorControlMode.V,
        r0=0.01,
        x0=0.05,
        r2=0.01,
        x2=0.05,
    )
    grid.add_generator(bus=slack_bus, api_obj=slack_gen)

    line: vg.Line = vg.Line(
        name="Line12",
        bus_from=slack_bus,
        bus_to=load_bus,
        r=0.01,
        x=0.05,
        b=0.0,
        rate=100.0,
        r0=0.01,
        x0=0.05,
        b0=0.0,
        r2=0.01,
        x2=0.05,
        b2=0.0,
    )
    grid.add_line(line)

    load: vg.Load = vg.Load(
        name="UnbalancedLoad",
        P=0.0,
        Q=0.0,
        P1=1.20,
        P2=0.85,
        P3=1.05,
        Q1=0.35,
        Q2=0.20,
        Q3=0.28,
    )

    # The connection type is part of the actual 3-phase solver contract, so the
    # comparison must exercise that conversion path as well.
    load.conn = vg.ShuntConnectionType.GroundedStar
    load.Pa_prof = np.array([1.20, 1.00, 1.35], dtype=float)
    load.Pb_prof = np.array([0.85, 0.90, 0.75], dtype=float)
    load.Pc_prof = np.array([1.05, 1.15, 0.95], dtype=float)
    load.Qa_prof = np.array([0.35, 0.30, 0.38], dtype=float)
    load.Qb_prof = np.array([0.20, 0.22, 0.18], dtype=float)
    load.Qc_prof = np.array([0.28, 0.31, 0.24], dtype=float)
    grid.add_load(bus=load_bus, api_obj=load)

    return grid


def _assert_snapshot_close(native: PowerFlowResults3Ph, gslv: PowerFlowResults3Ph, atol: float) -> None:
    """
    Compare the key three-phase snapshot result channels.

    :param native: VeraGrid snapshot results.
    :param gslv: GSLV snapshot results translated into VeraGrid containers.
    :param atol: Absolute tolerance.
    :return: None.
    """
    # The snapshot comparison focuses on the channels consumed later by the GUI
    # and by downstream post-processing of 3-phase studies.
    assert np.allclose(native.voltage_A, gslv.voltage_A, atol=atol)
    assert np.allclose(native.voltage_B, gslv.voltage_B, atol=atol)
    assert np.allclose(native.voltage_C, gslv.voltage_C, atol=atol)
    assert np.allclose(native.Sf_A, gslv.Sf_A, atol=atol)
    assert np.allclose(native.Sf_B, gslv.Sf_B, atol=atol)
    assert np.allclose(native.Sf_C, gslv.Sf_C, atol=atol)
    assert np.allclose(native.loading_A, gslv.loading_A, atol=atol)
    assert np.allclose(native.loading_B, gslv.loading_B, atol=atol)
    assert np.allclose(native.loading_C, gslv.loading_C, atol=atol)


def _assert_time_series_close(
        native: PowerFlowTimeSeriesResults3Ph,
        gslv: PowerFlowTimeSeriesResults3Ph,
        atol: float) -> None:
    """
    Compare the key three-phase time-series result channels.

    :param native: VeraGrid time-series results.
    :param gslv: GSLV time-series results translated into VeraGrid containers.
    :param atol: Absolute tolerance.
    :return: None.
    """
    # The time-series comparison verifies that each per-time-step translated
    # snapshot stays numerically aligned with the native VeraGrid solver.
    assert np.allclose(native.voltage_A, gslv.voltage_A, atol=atol)
    assert np.allclose(native.voltage_B, gslv.voltage_B, atol=atol)
    assert np.allclose(native.voltage_C, gslv.voltage_C, atol=atol)
    assert np.allclose(native.Sf_A, gslv.Sf_A, atol=atol)
    assert np.allclose(native.Sf_B, gslv.Sf_B, atol=atol)
    assert np.allclose(native.Sf_C, gslv.Sf_C, atol=atol)
    assert np.allclose(native.loading_A, gslv.loading_A, atol=atol)
    assert np.allclose(native.loading_B, gslv.loading_B, atol=atol)
    assert np.allclose(native.loading_C, gslv.loading_C, atol=atol)
    assert np.allclose(native.error_values, gslv.error_values, atol=atol)
    assert np.array_equal(native.converged_values, gslv.converged_values)


def test_gslv_power_flow_3ph_snapshot_matches_veragrid() -> None:
    """
    Compare the translated GSLV three-phase snapshot against the native engine.

    :return: None.
    """
    if not GSLV_AVAILABLE:
        return
    else:
        pass

    grid: vg.MultiCircuit = _build_unbalanced_3ph_grid()
    options: vg.PowerFlowOptions = _build_3ph_options()

    native: PowerFlowResults3Ph = vg.power_flow3ph(
        grid=grid,
        options=options,
        engine=vg.EngineType.VeraGrid,
    )
    gslv: PowerFlowResults3Ph = vg.power_flow3ph(
        grid=grid,
        options=options,
        engine=vg.EngineType.GSLV,
    )

    # The two engines solve the same physical problem through different
    # implementations, so the integration test enforces close agreement rather
    # than bitwise equality.
    _assert_snapshot_close(native=native, gslv=gslv, atol=2e-3)


def test_gslv_power_flow_3ph_time_series_matches_veragrid() -> None:
    """
    Compare the translated GSLV three-phase time series against the native engine.

    :return: None.
    """
    if not GSLV_AVAILABLE:
        return
    else:
        pass

    grid: vg.MultiCircuit = _build_unbalanced_3ph_grid()
    options: vg.PowerFlowOptions = _build_3ph_options()
    time_indices: np.ndarray = np.array([0, 1, 2], dtype=int)

    native: PowerFlowTimeSeriesResults3Ph = vg.power_flow3ph_ts(
        grid=grid,
        options=options,
        time_indices=time_indices,
        engine=vg.EngineType.VeraGrid,
    )
    gslv: PowerFlowTimeSeriesResults3Ph = vg.power_flow3ph_ts(
        grid=grid,
        options=options,
        time_indices=time_indices,
        engine=vg.EngineType.GSLV,
    )

    # The time-series path reuses the same translated GSLV snapshot engine at
    # each time step, so the comparison keeps the same numerical tolerance.
    _assert_time_series_close(native=native, gslv=gslv, atol=2e-3)
