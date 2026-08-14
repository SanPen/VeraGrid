from __future__ import annotations

import time
from pathlib import Path

from PySide6 import QtCore
from PySide6 import QtWidgets

import VeraGridEngine as vge
from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI
from VeraGrid.templates import get_cables_catalogue
from VeraGrid.templates import get_sequence_lines_catalogue
from VeraGrid.templates import get_transformer_catalogue
from VeraGrid.templates import get_wires_catalogue
from VeraGrid.Session.file_handler import FileSaveThread
from VeraGridEngine.enumerations import SimulationTypes


def wait_for_file_save(gui: VeraGridMainGUI, app: QtWidgets.QApplication, timeout_s: float) -> None:
    """
    Process Qt events until the GUI file-save worker has finished.

    :param gui: Main GUI instance running the save worker.
    :param app: Shared Qt application.
    :param timeout_s: Maximum wait time in seconds.
    :return: Nothing.
    """
    deadline_s: float = time.monotonic() + timeout_s
    save_finished: bool = False

    while time.monotonic() < deadline_s and not save_finished:
        app.processEvents()
        save_thread: FileSaveThread | None = gui.save_file_thread_object

        if save_thread is None:
            save_finished = True
        elif save_thread.isRunning():
            time.sleep(0.01)
        elif SimulationTypes.FileSave in gui.stuff_running_now:
            time.sleep(0.01)
        else:
            save_thread.wait(5000)
            save_finished = True

    assert save_finished


def stop_gui_qthreads(gui: VeraGridMainGUI) -> None:
    """
    Stop Qt worker threads owned by the main GUI without invoking close prompts.

    :param gui: Main GUI instance to clean up.
    :return: Nothing.
    """
    gui.shutdown_tile_sources()

    thread: QtCore.QThread | None
    for thread in gui.get_all_threads():
        if thread is not None:
            if thread.isRunning():
                thread.quit()
                thread.wait(5000)
            else:
                thread.wait(5000)
        else:
            pass

    if gui.server_driver.isRunning():
        gui.server_driver.quit()
        gui.server_driver.wait(5000)
    else:
        pass


def test_tower_saving_issue(qt_app: QtWidgets.QApplication, tmp_path: Path) -> None:
    """
    Check that saving and solving a GUI-built circuit with an overhead tower does not crash.

    :param qt_app: Shared Qt application fixture.
    :param tmp_path: Temporary output directory.
    :return: Nothing.
    """
    app: QtWidgets.QApplication = qt_app
    gui: VeraGridMainGUI = VeraGridMainGUI()

    try:
        transformer_tpe: object
        for transformer_tpe in get_transformer_catalogue():
            gui.circuit.add_transformer_type(transformer_tpe)

        cable_tpe: object
        for cable_tpe in get_cables_catalogue():
            gui.circuit.add_underground_line(cable_tpe)

        wire_tpe: object
        for wire_tpe in get_wires_catalogue():
            gui.circuit.add_wire(wire_tpe)

        sequence_line_tpe: object
        for sequence_line_tpe in get_sequence_lines_catalogue():
            gui.circuit.add_sequence_line(sequence_line_tpe)

        logger: vge.Logger = vge.Logger()
        bus_slack: vge.Bus = vge.Bus(name="Slack", xpos=0, ypos=0)
        bus_slack.is_slack = True
        gui.circuit.add_bus(obj=bus_slack)

        bus_load: vge.Bus = vge.Bus(name="Load", xpos=0, ypos=200)
        gui.circuit.add_bus(obj=bus_load)

        gen_slack: vge.Generator = vge.Generator()
        gui.circuit.add_generator(bus=bus_slack, api_obj=gen_slack)

        tower: vge.OverheadLineType = vge.OverheadLineType(name="Tower", Vnom=10.0)
        wire: vge.Wire = vge.Wire(name="Alex Blanco",
                                  diameter=23.0,
                                  diameter_internal=9.0,
                                  is_tube=True,
                                  r=0.19,
                                  max_current=1)

        tower.add_wire_relationship(wire=wire, xpos=-2, ypos=20, phase=1)
        tower.add_wire_relationship(wire=wire, xpos=0, ypos=20, phase=2)
        tower.add_wire_relationship(wire=wire, xpos=2, ypos=20, phase=3)

        line: vge.Line = vge.Line(bus_from=bus_slack, bus_to=bus_load)
        line.apply_template(tower, gui.circuit.Sbase, gui.circuit.fBase, logger)
        gui.circuit.add_line(obj=line)

        load: vge.Load = vge.Load(P=4.0, Q=2.0)
        gui.circuit.add_load(bus=bus_load, api_obj=load)

        output_file: Path = tmp_path / "tower.veragrid"
        gui.save_file_now(filename=str(output_file))
        wait_for_file_save(gui=gui, app=app, timeout_s=30.0)
        assert output_file.exists()

        power_flow_results: object = vge.power_flow(grid=gui.circuit, options=vge.PowerFlowOptions())
        voltage_frame: object = power_flow_results.get_voltage_df()
        assert voltage_frame is not None
    finally:
        stop_gui_qthreads(gui=gui)
        gui.hide()
        gui.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
        app.processEvents()
