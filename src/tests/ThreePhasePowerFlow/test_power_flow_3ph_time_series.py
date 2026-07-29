from __future__ import annotations

import numpy as np

import VeraGridEngine.api as vg
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_ts_driver_3ph import PowerFlowTimeSeriesDriver3Ph
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_ts_results_3ph import PowerFlowTimeSeriesResults3Ph


class _SyntheticConvergenceReport:
    """
    Minimal convergence-report double for synthetic three-phase results.
    """

    __slots__ = ()

    def converged(self) -> bool:
        """
        Return the synthetic convergence flag.

        :return: True.
        """
        return True

    def error(self) -> float:
        """
        Return the synthetic error value.

        :return: Error.
        """
        return 1.25e-4

    def elapsed(self) -> float:
        """
        Return the synthetic elapsed time.

        :return: Elapsed time.
        """
        return 0.01

    def iterations(self) -> int:
        """
        Return the synthetic iteration count.

        :return: Iterations.
        """
        return 3


def _build_snapshot_results() -> PowerFlowResults3Ph:
    """
    Build one synthetic snapshot results object for time-series storage tests.

    :return: Snapshot three-phase results.
    """
    results: PowerFlowResults3Ph = PowerFlowResults3Ph(
        n=6,
        m=3,
        n_hvdc=1,
        n_vsc=1,
        n_gen=1,
        n_batt=1,
        n_sh=1,
        n_load=1,
        bus_names=np.array(["Bus 1", "Bus 2"], dtype=str),
        branch_names=np.array(["Line 1"], dtype=str),
        hvdc_names=np.array(["HVDC 1"], dtype=str),
        vsc_names=np.array(["VSC 1"], dtype=str),
        gen_names=np.array(["Gen 1"], dtype=str),
        batt_names=np.array(["Batt 1"], dtype=str),
        sh_names=np.array(["Shunt 1"], dtype=str),
        load_names=np.array(["Load 1"], dtype=str),
        bus_types=np.array([1, 1], dtype=int),
    )

    results.Sbus_A[:] = np.array([10.0 + 1.0j, 20.0 + 2.0j], dtype=complex)
    results.Sbus_B[:] = np.array([11.0 + 1.5j, 21.0 + 2.5j], dtype=complex)
    results.Sbus_C[:] = np.array([12.0 + 2.0j, 22.0 + 3.0j], dtype=complex)
    results.voltage_A[:] = np.array([1.01 + 0.01j, 0.99 - 0.02j], dtype=complex)
    results.voltage_B[:] = np.array([1.02 + 0.02j, 0.98 - 0.03j], dtype=complex)
    results.voltage_C[:] = np.array([1.03 + 0.03j, 0.97 - 0.04j], dtype=complex)
    results.Sf_A[:] = np.array([5.0 + 0.5j], dtype=complex)
    results.Sf_B[:] = np.array([6.0 + 0.6j], dtype=complex)
    results.Sf_C[:] = np.array([7.0 + 0.7j], dtype=complex)
    results.St_A[:] = np.array([4.5 + 0.4j], dtype=complex)
    results.St_B[:] = np.array([5.5 + 0.5j], dtype=complex)
    results.St_C[:] = np.array([6.5 + 0.6j], dtype=complex)
    results.If_A[:] = np.array([0.5 + 0.05j], dtype=complex)
    results.If_B[:] = np.array([0.6 + 0.06j], dtype=complex)
    results.If_C[:] = np.array([0.7 + 0.07j], dtype=complex)
    results.It_A[:] = np.array([0.4 + 0.04j], dtype=complex)
    results.It_B[:] = np.array([0.5 + 0.05j], dtype=complex)
    results.It_C[:] = np.array([0.6 + 0.06j], dtype=complex)
    results.loading_A[:] = np.array([0.80 + 0.0j], dtype=complex)
    results.loading_B[:] = np.array([0.85 + 0.0j], dtype=complex)
    results.loading_C[:] = np.array([0.90 + 0.0j], dtype=complex)
    results.losses_A[:] = np.array([0.10 + 0.01j], dtype=complex)
    results.losses_B[:] = np.array([0.20 + 0.02j], dtype=complex)
    results.losses_C[:] = np.array([0.30 + 0.03j], dtype=complex)
    results.Pf_hvdc_A[:] = np.array([1.0], dtype=float)
    results.Pf_hvdc_B[:] = np.array([1.1], dtype=float)
    results.Pf_hvdc_C[:] = np.array([1.2], dtype=float)
    results.Pt_hvdc_A[:] = np.array([0.9], dtype=float)
    results.Pt_hvdc_B[:] = np.array([1.0], dtype=float)
    results.Pt_hvdc_C[:] = np.array([1.1], dtype=float)
    results.losses_hvdc[:] = np.array([0.2], dtype=float)
    results.loading_hvdc[:] = np.array([0.7], dtype=float)
    results.Pfp_vsc[:] = np.array([2.0], dtype=float)
    results.St_vsc_A[:] = np.array([1.5 + 0.15j], dtype=complex)
    results.St_vsc_B[:] = np.array([1.6 + 0.16j], dtype=complex)
    results.St_vsc_C[:] = np.array([1.7 + 0.17j], dtype=complex)
    results.If_vsc[:] = np.array([0.3], dtype=float)
    results.It_vsc_A[:] = np.array([0.25 + 0.025j], dtype=complex)
    results.It_vsc_B[:] = np.array([0.26 + 0.026j], dtype=complex)
    results.It_vsc_C[:] = np.array([0.27 + 0.027j], dtype=complex)
    results.losses_vsc[:] = np.array([0.05], dtype=float)
    results.loading_vsc[:] = np.array([0.6], dtype=float)
    results.gen_q_A[:] = np.array([3.0], dtype=float)
    results.gen_q_B[:] = np.array([3.1], dtype=float)
    results.gen_q_C[:] = np.array([3.2], dtype=float)
    results.battery_q_A[:] = np.array([4.0], dtype=float)
    results.battery_q_B[:] = np.array([4.1], dtype=float)
    results.battery_q_C[:] = np.array([4.2], dtype=float)
    results.shunt_q_A[:] = np.array([5.0], dtype=float)
    results.shunt_q_B[:] = np.array([5.1], dtype=float)
    results.shunt_q_C[:] = np.array([5.2], dtype=float)
    results.shunt_Vn[:] = np.array([0.01 + 0.001j], dtype=complex)
    results.load_Vn[:] = np.array([0.02 + 0.002j], dtype=complex)
    results.convergence_reports.append(_SyntheticConvergenceReport())

    return results


def test_power_flow_3ph_time_series_results_set_at_preserves_snapshot_payload() -> None:
    """
    The three-phase time-series container must store one snapshot without reshaping mistakes.

    :return: None.
    """
    time_array: np.ndarray = np.array(["2024-01-01T00:00:00", "2024-01-01T01:00:00"], dtype="datetime64[s]")
    results: PowerFlowTimeSeriesResults3Ph = PowerFlowTimeSeriesResults3Ph(
        n=6,
        m=3,
        n_hvdc=1,
        n_vsc=1,
        n_gen=1,
        n_batt=1,
        n_sh=1,
        n_load=1,
        bus_names=np.array(["Bus 1", "Bus 2"], dtype=str),
        branch_names=np.array(["Line 1"], dtype=str),
        hvdc_names=np.array(["HVDC 1"], dtype=str),
        vsc_names=np.array(["VSC 1"], dtype=str),
        gen_names=np.array(["Gen 1"], dtype=str),
        batt_names=np.array(["Batt 1"], dtype=str),
        sh_names=np.array(["Shunt 1"], dtype=str),
        load_names=np.array(["Load 1"], dtype=str),
        bus_types=np.array([1, 1], dtype=int),
        time_array=time_array,
    )
    snapshot_results: PowerFlowResults3Ph = _build_snapshot_results()

    results.set_at(1, snapshot_results)

    assert np.array_equal(results.Sbus_A[1, :], snapshot_results.Sbus_A)
    assert np.array_equal(results.voltage_C[1, :], snapshot_results.voltage_C)
    assert np.array_equal(results.Sf_B[1, :], snapshot_results.Sf_B)
    assert np.array_equal(results.losses_hvdc[1, :], snapshot_results.losses_hvdc)
    assert np.array_equal(results.St_vsc_A[1, :], snapshot_results.St_vsc_A)
    assert np.array_equal(results.shunt_Vn[1, :], snapshot_results.shunt_Vn)
    assert np.array_equal(results.load_Vn[1, :], snapshot_results.load_Vn)
    assert results.error_values[1] == snapshot_results.error
    assert results.converged_values[1] == snapshot_results.converged


def test_power_flow_3ph_time_series_driver_initializes_results_shell() -> None:
    """
    The three-phase time-series driver must create one results shell with matching dimensions.

    :return: None.
    """
    grid: vg.MultiCircuit = vg.MultiCircuit(name="pf3-ts-shell")
    grid.set_unix_time(np.array([0, 3600], dtype=np.int64))
    bus_1 = vg.Bus(name="Bus 1", Vnom=20.0, is_slack=True)
    bus_2 = vg.Bus(name="Bus 2", Vnom=20.0)
    grid.add_bus(bus_1)
    grid.add_bus(bus_2)
    grid.add_line(vg.Line(name="Line 1", bus_from=bus_1, bus_to=bus_2, r=0.01, x=0.05, b=0.0, rate=100.0))

    driver: PowerFlowTimeSeriesDriver3Ph = PowerFlowTimeSeriesDriver3Ph(grid=grid)

    assert driver.results is not None
    assert len(driver.results.time_array) == 2
    assert driver.results.voltage_A.shape[0] == 2
