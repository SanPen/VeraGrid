from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import VeraGridEngine.api as vg
from VeraGrid.Session.session import SimulationSession
from VeraGridEngine.Simulations.driver_handler import create_driver
from VeraGridEngine.Simulations.NTC.ntc_results import OptimalNetTransferCapacityResults
from VeraGridEngine.Simulations.SigmaAnalysis.sigma_analysis_driver import SigmaAnalysisResults
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_driver import SmallSignalStabilityRmsResults
from VeraGridEngine.Simulations.StateEstimation.state_estimation_results import StateEstimationResults
from VeraGridEngine.enumerations import SimulationTypes
from VeraGridEngine.IO.veragrid.zip_interface import load_session_driver_objects


GRID_FOLDER = Path(__file__).resolve().parents[1] / "data" / "grids"


class FakeSignal:
    """
    Minimal signal object used to capture thread connections in session tests.
    """

    __slots__ = ("callbacks",)

    def __init__(self) -> None:
        """
        Build the fake signal.

        :return: None.
        """
        self.callbacks: list[object] = list()

    def connect(self, callback: object) -> None:
        """
        Record one connected callback.

        :param callback: Connected callback.
        :return: None.
        """
        self.callbacks.append(callback)


class FakeThread:
    """
    Minimal thread used to exercise session replacement logic.
    """

    __slots__ = ("driver", "progress_signal", "progress_text", "done_signal", "started", "terminated")

    def __init__(self, driver: object) -> None:
        """
        Build the fake thread.

        :param driver: Driver stored by the session.
        :return: None.
        """
        self.driver: object = driver
        self.progress_signal: FakeSignal = FakeSignal()
        self.progress_text: FakeSignal = FakeSignal()
        self.done_signal: FakeSignal = FakeSignal()
        self.started: bool = False
        self.terminated: bool = False

    def isRunning(self) -> bool:
        """
        Report whether the fake thread is already running.

        :return: Running state.
        """
        return self.started

    def terminate(self) -> None:
        """
        Mark the fake thread as terminated.

        :return: None.
        """
        self.terminated = True

    def start(self) -> None:
        """
        Mark the fake thread as started.

        :return: None.
        """
        self.started = True


class FakeDriver:
    """
    Minimal driver used to trigger session replacement code paths.
    """

    __slots__ = ("tpe",)

    def __init__(self, driver_tpe: SimulationTypes) -> None:
        """
        Build the fake driver.

        :param driver_tpe: Simulation type exposed to the session.
        :return: None.
        """
        self.tpe: SimulationTypes = driver_tpe


@pytest.mark.parametrize(
    "driver_tpe",
    [
        SimulationTypes.PowerFlow3ph_run,
        SimulationTypes.PowerFlowTimeSeries3ph_run,
        SimulationTypes.StateEstimation_run,
        SimulationTypes.SigmaAnalysis_run,
        SimulationTypes.InputsAnalysis_run,
        SimulationTypes.Reliability_run,
        SimulationTypes.Cascade_run,
        SimulationTypes.NodeGrouping_run,
        SimulationTypes.InvestmentsEvaluation_run,
        SimulationTypes.CatalogueOptimization_run,
        SimulationTypes.OPF_NTC_run,
        SimulationTypes.OptimalNetTransferCapacityTimeSeries_run,
    ],
)
def test_create_driver_supports_additional_disk_retrieval_types(driver_tpe: SimulationTypes) -> None:
    """
    The disk retrieval registry must expose concrete driver shells for the
    additional simulation types supported by the GUI.

    :param driver_tpe: Simulation type under test.
    :return: None.
    """
    grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    driver = create_driver(grid=grid, driver_tpe=driver_tpe, time_indices=grid.get_all_time_indices())

    assert driver is not None


def test_power_flow_3ph_results_register_from_disk_data(tmp_path: Path) -> None:
    """
    Three-phase power-flow results must support disk registration.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    driver = create_driver(grid=grid, driver_tpe=SimulationTypes.PowerFlow3ph_run, time_indices=None)
    assert driver is not None

    file_name = tmp_path / "pf3_disk_driver.veragrid"
    vg.save_file(grid=grid, filename=str(file_name), drivers_to_save=[driver.get_save_data()])

    stored_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=driver.name,
        study_name=driver.tpe.value,
    )

    session = SimulationSession()
    logger = session.register_driver_from_disk_data(
        grid=grid,
        study_name=driver.tpe.value,
        data_dict=stored_data,
    )

    assert not logger.has_logs()
    assert session.exists(SimulationTypes.PowerFlow3ph_run)


def test_power_flow_3ph_time_series_results_register_from_disk_data(tmp_path: Path) -> None:
    """
    Three-phase power-flow time-series results must support disk registration.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    driver = create_driver(
        grid=grid,
        driver_tpe=SimulationTypes.PowerFlowTimeSeries3ph_run,
        time_indices=grid.get_all_time_indices(),
    )
    assert driver is not None

    file_name = tmp_path / "pf3_ts_disk_driver.veragrid"
    vg.save_file(grid=grid, filename=str(file_name), drivers_to_save=[driver.get_save_data()])

    stored_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=driver.name,
        study_name=driver.tpe.value,
    )

    session = SimulationSession()
    logger = session.register_driver_from_disk_data(
        grid=grid,
        study_name=driver.tpe.value,
        data_dict=stored_data,
    )

    assert not logger.has_logs(), logger.to_df().to_string()
    assert session.exists(SimulationTypes.PowerFlowTimeSeries3ph_run)


def test_state_estimation_results_register_from_disk_data(tmp_path: Path) -> None:
    """
    State-estimation result shells must support disk registration.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    driver = create_driver(grid=grid, driver_tpe=SimulationTypes.StateEstimation_run, time_indices=None)
    assert driver is not None

    driver.results = StateEstimationResults(
        n=grid.get_bus_number(),
        m=grid.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True),
        n_hvdc=grid.get_hvdc_number(),
        n_vsc=grid.get_vsc_number(),
        n_gen=grid.get_generation_like_number(),
        n_batt=grid.get_batteries_number(),
        n_sh=grid.get_shunt_like_device_number(),
        bus_names=grid.get_bus_names(),
        branch_names=grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
        hvdc_names=grid.get_hvdc_names(),
        vsc_names=grid.get_vsc_names(),
        gen_names=grid.get_generation_like_names(),
        batt_names=grid.get_battery_names(),
        sh_names=grid.get_shunt_like_devices_names(),
        bus_types=np.ones(grid.get_bus_number(), dtype=int),
    )

    file_name = tmp_path / "state_estimation_disk_driver.veragrid"
    vg.save_file(grid=grid, filename=str(file_name), drivers_to_save=[driver.get_save_data()])

    stored_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=driver.name,
        study_name=driver.tpe.value,
    )

    session = SimulationSession()
    logger = session.register_driver_from_disk_data(
        grid=grid,
        study_name=driver.tpe.value,
        data_dict=stored_data,
    )

    assert not logger.has_logs()
    assert session.exists(SimulationTypes.StateEstimation_run)


def test_sigma_results_register_from_disk_data(tmp_path: Path) -> None:
    """
    Sigma-analysis result shells must support disk registration.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    driver = create_driver(grid=grid, driver_tpe=SimulationTypes.SigmaAnalysis_run, time_indices=None)
    assert driver is not None

    driver.results = SigmaAnalysisResults(n=grid.get_bus_number())

    file_name = tmp_path / "sigma_disk_driver.veragrid"
    vg.save_file(grid=grid, filename=str(file_name), drivers_to_save=[driver.get_save_data()])

    stored_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=driver.name,
        study_name=driver.tpe.value,
    )

    session = SimulationSession()
    logger = session.register_driver_from_disk_data(
        grid=grid,
        study_name=driver.tpe.value,
        data_dict=stored_data,
    )

    assert not logger.has_logs()
    assert session.exists(SimulationTypes.SigmaAnalysis_run)


def test_rms_small_signal_results_register_from_disk_data(tmp_path: Path) -> None:
    """
    RMS small-signal result shells must support disk registration.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    pf_driver = create_driver(grid=grid, driver_tpe=SimulationTypes.PowerFlow_run, time_indices=None)
    assert pf_driver is not None

    driver = create_driver(
        grid=grid,
        driver_tpe=SimulationTypes.RmsSmallSignal_run,
        time_indices=None,
        pf_results=pf_driver.results,
    )
    assert driver is not None

    driver.results = SmallSignalStabilityRmsResults(
        eigenvalues=np.array([-1.0, -2.0], dtype=float),
        participation_factors=np.array([[0.8, 0.2], [0.2, 0.8]], dtype=float),
        damping_ratios=np.array([1.0, 1.0], dtype=float),
        conjugate_frequencies=np.array([0.0, 0.0], dtype=float),
        state_matrix=np.array([[-1.0, 0.0], [0.0, -2.0]], dtype=float),
        stat_vars=list(),
        algebraic_vars=list()
    )
    driver.results.stat_vars_array = np.array(["x1", "x2"], dtype=str)

    file_name = tmp_path / "rms_small_signal_disk_driver.veragrid"
    vg.save_file(
        grid=grid,
        filename=str(file_name),
        drivers_to_save=[pf_driver.get_save_data(), driver.get_save_data()],
    )

    pf_stored_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=pf_driver.name,
        study_name=pf_driver.tpe.value,
    )
    small_signal_stored_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=driver.name,
        study_name=driver.tpe.value,
    )

    session = SimulationSession()
    pf_logger = session.register_driver_from_disk_data(
        grid=grid,
        study_name=pf_driver.tpe.value,
        data_dict=pf_stored_data,
    )
    assert not pf_logger.has_logs()

    logger = session.register_driver_from_disk_data(
        grid=grid,
        study_name=driver.tpe.value,
        data_dict=small_signal_stored_data,
    )

    assert not logger.has_logs()
    assert session.exists(SimulationTypes.RmsSmallSignal_run)

    _, results = session.small_signal_stability_simulation
    assert results is not None
    assert np.array_equal(results.stat_vars_array, driver.results.stat_vars_array)
    assert np.array_equal(results.eigenvalues, driver.results.eigenvalues)
    assert np.array_equal(results.participation_factors, driver.results.participation_factors)
    assert np.array_equal(results.damping_ratios, driver.results.damping_ratios)
    assert np.array_equal(results.conjugate_frequencies, driver.results.conjugate_frequencies)
    assert np.array_equal(results.state_matrix, driver.results.state_matrix)


def test_rms_small_signal_results_warn_when_power_flow_is_not_loaded(tmp_path: Path) -> None:
    """
    RMS small-signal disk registration depends on power-flow results in the loaded session.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    pf_driver = create_driver(grid=grid, driver_tpe=SimulationTypes.PowerFlow_run, time_indices=None)
    assert pf_driver is not None

    driver = create_driver(
        grid=grid,
        driver_tpe=SimulationTypes.RmsSmallSignal_run,
        time_indices=None,
        pf_results=pf_driver.results,
    )
    assert driver is not None

    file_name = tmp_path / "rms_small_signal_without_pf.veragrid"
    vg.save_file(grid=grid, filename=str(file_name), drivers_to_save=[driver.get_save_data()])

    stored_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=driver.name,
        study_name=driver.tpe.value,
    )

    session = SimulationSession()
    logger = session.register_driver_from_disk_data(
        grid=grid,
        study_name=driver.tpe.value,
        data_dict=stored_data,
    )

    assert logger.has_logs()
    assert "Power Flow results must be loaded" in logger.entries[0].msg
    assert not session.exists(SimulationTypes.RmsSmallSignal_run)


def test_ntc_results_register_from_disk_data(tmp_path: Path) -> None:
    """
    Snapshot NTC result shells must support disk registration.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    driver = create_driver(grid=grid, driver_tpe=SimulationTypes.OPF_NTC_run, time_indices=None)
    assert driver is not None

    driver.results = OptimalNetTransferCapacityResults(
        bus_names=grid.get_bus_names(),
        branch_names=grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True),
        hvdc_names=grid.get_hvdc_names(),
        vsc_names=grid.get_vsc_names(),
        contingency_group_names=grid.get_contingency_group_names(),
    )

    file_name = tmp_path / "ntc_disk_driver.veragrid"
    vg.save_file(grid=grid, filename=str(file_name), drivers_to_save=[driver.get_save_data()])

    stored_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=driver.name,
        study_name=driver.tpe.value,
    )

    session = SimulationSession()
    logger = session.register_driver_from_disk_data(
        grid=grid,
        study_name=driver.tpe.value,
        data_dict=stored_data,
    )

    assert session.exists(SimulationTypes.OPF_NTC_run)


def test_session_run_replaces_existing_driver_without_registered_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Re-running one study must tolerate sessions that kept a driver but lost its live thread entry.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    session = SimulationSession()
    previous_driver = FakeDriver(driver_tpe=SimulationTypes.PowerFlow_run)
    next_driver = FakeDriver(driver_tpe=SimulationTypes.PowerFlow_run)
    session.drivers[SimulationTypes.PowerFlow_run] = previous_driver

    monkeypatch.setattr("VeraGrid.Session.session.GcThread", FakeThread)

    session.run(
        driver=next_driver,
        post_func=lambda: None,
        prog_func=lambda _value: None,
        text_func=lambda _text: None,
    )

    assert session.drivers[SimulationTypes.PowerFlow_run] is next_driver
    assert SimulationTypes.PowerFlow_run in session.threads
    assert isinstance(session.threads[SimulationTypes.PowerFlow_run], FakeThread)
    assert session.threads[SimulationTypes.PowerFlow_run].started is True
