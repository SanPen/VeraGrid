from __future__ import annotations

import multiprocessing
import queue
import time
import traceback
from pathlib import Path
from typing import Any

import pytest
from PySide6 import QtCore
from PySide6 import QtWidgets

from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI
from VeraGrid.Gui.dialog_lifecycle import delete_dialog_safely
from VeraGrid.Session.file_handler import FileOpenThread
from VeraGrid.Session.session import GcThread
from VeraGridEngine.enumerations import SimulationTypes


CND_CONTINGENCY_CRASH_FILE: Path = Path(
    "/home/santi/Git/eRoots/VeraGridDemos/Trainings/CND/Training_CND_19AUG2026_real.veragrid"
)


def wait_for_file_open(gui: VeraGridMainGUI, app: QtWidgets.QApplication, timeout_s: float) -> None:
    """
    Process Qt events until the GUI file-open worker has finished.

    :param gui: Main GUI instance running the file-open worker.
    :param app: Shared Qt application.
    :param timeout_s: Maximum wait time in seconds.
    :return: None.
    """
    deadline_s: float = time.monotonic() + timeout_s
    open_finished: bool = False

    while time.monotonic() < deadline_s and not open_finished:
        app.processEvents()
        open_thread: FileOpenThread | None = gui.open_file_thread_object

        if open_thread is None:
            open_finished = True
        elif open_thread.isRunning():
            time.sleep(0.01)
        elif SimulationTypes.FileOpen in gui.stuff_running_now:
            time.sleep(0.01)
        else:
            open_thread.wait(5000)
            open_finished = True

    assert open_finished


def wait_for_simulation(gui: VeraGridMainGUI,
                        app: QtWidgets.QApplication,
                        simulation_type: SimulationTypes,
                        timeout_s: float) -> None:
    """
    Process Qt events until one GUI simulation worker has finished.

    :param gui: Main GUI instance running the contingency worker.
    :param app: Shared Qt application.
    :param simulation_type: Simulation type to wait for.
    :param timeout_s: Maximum wait time in seconds.
    :return: None.
    """
    deadline_s: float = time.monotonic() + timeout_s
    simulation_finished: bool = False

    while time.monotonic() < deadline_s and not simulation_finished:
        app.processEvents()
        simulation_thread: GcThread | None = gui.session.threads.get(simulation_type, None)

        if simulation_thread is None:
            simulation_finished = True
        elif simulation_thread.isRunning():
            time.sleep(0.01)
        elif simulation_type in gui.stuff_running_now:
            time.sleep(0.01)
        else:
            simulation_thread.wait(5000)
            simulation_finished = True

    assert simulation_finished


def run_cnd_contingency_gui_flow(message_queue: Any) -> None:
    """
    Launch the GUI, run OPF, enable OPF copy, and run contingencies.

    :param message_queue: Parent-visible queue receiving failure details.
    :return: None.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(list(("cnd-contingency-regression",)))
    else:
        pass

    gui: VeraGridMainGUI = VeraGridMainGUI()
    gui.show()
    app.processEvents()

    try:
        gui.open_file_now(filenames=str(CND_CONTINGENCY_CRASH_FILE))
        wait_for_file_open(gui=gui, app=app, timeout_s=60.0)

        assert gui.circuit.get_bus_number() > 0
        assert len(gui.circuit.contingency_groups) > 0

        gui.ui.actionOPF.trigger()
        wait_for_simulation(gui=gui, app=app, simulation_type=SimulationTypes.OPF_run, timeout_s=180.0)

        opf_driver, opf_results = gui.session.optimal_power_flow
        assert opf_driver is not None
        assert opf_results is not None

        gui.ui.actionOpf_to_Power_flow.setChecked(True)
        gui.ui.actionContingency_analysis.trigger()
        if gui.ui.actionactivate_time_series.isChecked():
            simulation_type: SimulationTypes = SimulationTypes.ContingencyAnalysisTS_run
        else:
            simulation_type = SimulationTypes.ContingencyAnalysis_run

        wait_for_simulation(gui=gui, app=app, simulation_type=simulation_type, timeout_s=180.0)

        if simulation_type == SimulationTypes.ContingencyAnalysisTS_run:
            contingency_driver, contingency_results = gui.session.contingency_ts
        else:
            contingency_driver, contingency_results = gui.session.contingency
        assert contingency_driver is not None
        assert contingency_results is not None
    except Exception:
        message_queue.put(traceback.format_exc())
        raise
    finally:
        gui.hide()
        gui.stop_all_threads()
        delete_dialog_safely(dialog=gui)
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        app.processEvents()


def test_cnd_training_file_contingency_analysis_does_not_clean_crash() -> None:
    """
    Check the reported CND OPF-to-contingency GUI crash in a subprocess.

    :return: None.
    """
    if CND_CONTINGENCY_CRASH_FILE.exists():
        pass
    else:
        pytest.skip(f"CND contingency crash fixture is not available: {CND_CONTINGENCY_CRASH_FILE}")

    process_context: multiprocessing.context.BaseContext = multiprocessing.get_context("spawn")
    message_queue: Any = process_context.Queue()
    process: multiprocessing.Process = process_context.Process(
        target=run_cnd_contingency_gui_flow,
        args=(message_queue,),
    )

    process.start()
    process.join(360.0)

    if process.is_alive():
        process.terminate()
        process.join(10.0)
        raise AssertionError("CND contingency GUI subprocess timed out")
    else:
        pass

    message: str = ""
    try:
        queued_message: object = message_queue.get_nowait()
        if isinstance(queued_message, str):
            message = queued_message
        else:
            message = repr(queued_message)
    except queue.Empty:
        pass

    assert process.exitcode == 0, message
