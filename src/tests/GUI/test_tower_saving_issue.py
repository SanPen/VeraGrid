from __future__ import annotations

import gc
import shutil
import time
from pathlib import Path

from PySide6 import QtCore
from PySide6 import QtWidgets

import VeraGridEngine as vge
from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI
from VeraGrid.Gui.DeviceEditors.TowerBuilder.LineBuilderDialogue import TowerBuilderGUI
from VeraGrid.Gui.dialog_lifecycle import delete_dialog_safely
from VeraGrid.templates import get_cables_catalogue
from VeraGrid.templates import get_sequence_lines_catalogue
from VeraGrid.templates import get_transformer_catalogue
from VeraGrid.templates import get_wires_catalogue
from VeraGrid.Session.file_handler import FileOpenThread
from VeraGrid.Session.file_handler import FileSaveThread
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import SimulationTypes

TESTS_ROOT: Path = Path(__file__).resolve().parents[1]
TOWER_EDIT_CRASH_FIXTURE: Path = (
    TESTS_ROOT / "data" / "grids" / "demo_15_bus_clean_crash_after_tower_editong.veragrid"
)


class MessageBoxAutoResponder(QtCore.QObject):
    """
    Click one expected QMessageBox button without blocking the GUI test.
    """
    __slots__ = ("_app", "_button", "_remaining_attempts")

    def __init__(self,
                 app: QtWidgets.QApplication,
                 button: QtWidgets.QMessageBox.StandardButton,
                 parent: QtCore.QObject | None = None) -> None:
        """
        Build one delayed QMessageBox responder.

        :param app: Shared Qt application.
        :param button: QMessageBox standard button to click.
        :param parent: Optional Qt parent keeping the responder alive.
        :return: None.
        """
        QtCore.QObject.__init__(self, parent)
        self._app: QtWidgets.QApplication = app
        self._button: QtWidgets.QMessageBox.StandardButton = button
        self._remaining_attempts: int = 100

    def arm(self) -> None:
        """
        Start polling for the expected modal QMessageBox.

        :return: None.
        """
        QtCore.QTimer.singleShot(10, self.click_button)

    def click_button(self) -> None:
        """
        Click the configured button if the QMessageBox is visible.

        :return: None.
        """
        clicked: bool = False
        active_modal_widget: QtWidgets.QWidget | None = self._app.activeModalWidget()
        widget: QtWidgets.QWidget

        if isinstance(active_modal_widget, QtWidgets.QMessageBox):
            message_button: QtWidgets.QAbstractButton | None = active_modal_widget.button(self._button)
            if message_button is not None:
                message_button.click()
                clicked = True
            else:
                pass
        else:
            for widget in self._app.topLevelWidgets():
                if isinstance(widget, QtWidgets.QMessageBox):
                    message_button = widget.button(self._button)
                    if message_button is not None:
                        message_button.click()
                        clicked = True
                    else:
                        pass
                else:
                    pass

        if clicked:
            self.deleteLater()
        elif self._remaining_attempts > 0:
            self._remaining_attempts -= 1
            self.arm()
        else:
            self.deleteLater()


class TowerEditorAutoResponder(QtCore.QObject):
    """
    Click Calculate and Accept on one tower editor without blocking the GUI test.
    """
    __slots__ = ("_app", "_clicked", "_remaining_attempts")

    def __init__(self, app: QtWidgets.QApplication, parent: QtCore.QObject | None = None) -> None:
        """
        Build one delayed TowerBuilderGUI responder.

        :param app: Shared Qt application.
        :param parent: Optional Qt parent keeping the responder alive.
        :return: None.
        """
        QtCore.QObject.__init__(self, parent)
        self._app: QtWidgets.QApplication = app
        self._clicked: bool = False
        self._remaining_attempts: int = 100

    def was_clicked(self) -> bool:
        """
        Return whether the responder found and accepted the tower editor.

        :return: True when the tower editor was accepted.
        """
        return self._clicked

    def arm(self) -> None:
        """
        Start polling for the expected tower editor.

        :return: None.
        """
        QtCore.QTimer.singleShot(10, self.click_calculate_and_accept)

    def click_calculate_and_accept(self) -> None:
        """
        Click Calculate and Accept if the tower editor is visible.

        :return: None.
        """
        widget: QtWidgets.QWidget

        for widget in self._app.topLevelWidgets():
            if isinstance(widget, TowerBuilderGUI):
                widget.ui.compute_pushButton.click()
                widget.accept()
                self._clicked = True
            else:
                pass

        if self._clicked:
            pass
        elif self._remaining_attempts > 0:
            self._remaining_attempts -= 1
            self.arm()
        else:
            pass


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


def wait_for_file_open(gui: VeraGridMainGUI, app: QtWidgets.QApplication, timeout_s: float) -> None:
    """
    Process Qt events until the GUI file-open worker has finished.

    :param gui: Main GUI instance running the open worker.
    :param app: Shared Qt application.
    :param timeout_s: Maximum wait time in seconds.
    :return: Nothing.
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


def close_gui_accepting_exit(gui: VeraGridMainGUI, app: QtWidgets.QApplication) -> None:
    """
    Close the main GUI and accept its exit confirmation automatically.

    :param gui: Main GUI instance to close.
    :param app: Shared Qt application.
    :return: Nothing.
    """
    responder: MessageBoxAutoResponder = MessageBoxAutoResponder(
        app=app,
        button=QtWidgets.QMessageBox.StandardButton.Yes,
        parent=app)
    responder.arm()
    closed: bool = gui.close()
    app.processEvents()
    if closed:
        pass
    else:
        gui.hide()
        gui.stop_all_threads()


def select_index(view: QtWidgets.QAbstractItemView, index: QtCore.QModelIndex) -> None:
    """
    Select one row in a Qt item view.

    :param view: Qt view to select in.
    :param index: Model index to select.
    :return: Nothing.
    """
    assert index.isValid()
    selection_model: QtCore.QItemSelectionModel | None = view.selectionModel()
    assert selection_model is not None

    selection_model.clearSelection()
    selection_model.select(
        index,
        QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
        | QtCore.QItemSelectionModel.SelectionFlag.Rows,
    )
    view.setCurrentIndex(index)
    QtWidgets.QApplication.processEvents()


def find_device_tree_index(gui: VeraGridMainGUI, device_type: DeviceType) -> QtCore.QModelIndex:
    """
    Find the database-tree row for one device type.

    :param gui: Main GUI instance with the database tree.
    :param device_type: Device type to find.
    :return: Matching tree index, or an invalid index when missing.
    """
    tree_model: QtCore.QAbstractItemModel | None = gui.ui.dataStructuresTreeView.model()
    if tree_model is not None:
        for parent_row in range(tree_model.rowCount()):
            parent_index: QtCore.QModelIndex = tree_model.index(parent_row, 0)
            for child_row in range(tree_model.rowCount(parent_index)):
                child_index: QtCore.QModelIndex = tree_model.index(child_row, 0, parent_index)
                if child_index.data(QtCore.Qt.ItemDataRole.UserRole) == device_type:
                    return child_index
                else:
                    pass
    else:
        pass

    return QtCore.QModelIndex()


def edit_tower_from_database_row(gui: VeraGridMainGUI, app: QtWidgets.QApplication, row: int) -> None:
    """
    Open the tower editor from the GUI database table and accept its calculation.

    :param gui: Main GUI instance.
    :param app: Shared Qt application.
    :param row: Tower row to edit in the overhead-line type table.
    :return: Nothing.
    """
    tree_index: QtCore.QModelIndex = find_device_tree_index(
        gui=gui,
        device_type=DeviceType.OverheadLineTypeDevice,
    )
    select_index(view=gui.ui.dataStructuresTreeView, index=tree_index)
    gui.view_objects_data()

    table_model: QtCore.QAbstractItemModel | None = gui.ui.dataStructureTableView.model()
    assert table_model is not None
    assert table_model.rowCount() > row

    table_index: QtCore.QModelIndex = table_model.index(row, 0)
    select_index(view=gui.ui.dataStructureTableView, index=table_index)

    responder: TowerEditorAutoResponder = TowerEditorAutoResponder(app=app, parent=app)
    responder.arm()
    gui.launch_object_editor()
    app.processEvents()

    accepted_editor: bool = responder.was_clicked()
    responder.deleteLater()
    assert accepted_editor


def calculate_and_accept_tower_editor(tower: vge.OverheadLineType,
                                      wire: vge.Wire) -> None:
    """
    Open a tower editor, calculate it, accept it, and release pending Qt deletes.

    :param tower: Tower template to edit.
    :param wire: Wire catalogue entry needed by the editor.
    :return: Nothing.
    """
    wires_catalogue: list[vge.Wire] = list()
    wires_catalogue.append(wire)
    dialog: TowerBuilderGUI = TowerBuilderGUI(tower=tower, wires_catalogue=wires_catalogue)
    try:
        dialog.ui.compute_pushButton.click()
        dialog.accept()
    finally:
        delete_dialog_safely(dialog=dialog)


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
        close_gui_accepting_exit(gui=gui, app=app)
        gui.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
        app.processEvents()


def test_tower_editor_cleanup_survives_forced_gc(qt_app: QtWidgets.QApplication) -> None:
    """
    Check that two calculated tower editors can close before cyclic GC runs.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    app: QtWidgets.QApplication = qt_app
    wire: vge.Wire = vge.Wire(name="Alex Blanco",
                              diameter=23.0,
                              diameter_internal=9.0,
                              is_tube=True,
                              r=0.19,
                              max_current=1)

    tower_first: vge.OverheadLineType = vge.OverheadLineType(name="Tower 1", Vnom=10.0)
    tower_first.add_wire_relationship(wire=wire, xpos=-2, ypos=20, phase=1)
    tower_first.add_wire_relationship(wire=wire, xpos=0, ypos=20, phase=2)
    tower_first.add_wire_relationship(wire=wire, xpos=2, ypos=20, phase=3)

    tower_second: vge.OverheadLineType = vge.OverheadLineType(name="Tower 2", Vnom=10.0)
    tower_second.add_wire_relationship(wire=wire, xpos=-3, ypos=22, phase=1)
    tower_second.add_wire_relationship(wire=wire, xpos=0, ypos=22, phase=2)
    tower_second.add_wire_relationship(wire=wire, xpos=3, ypos=22, phase=3)

    calculate_and_accept_tower_editor(tower=tower_second, wire=wire)
    calculate_and_accept_tower_editor(tower=tower_first, wire=wire)

    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    app.processEvents()
    active_modal_widget: QtWidgets.QWidget | None = app.activeModalWidget()
    assert active_modal_widget is None


def test_original_honduras_tower_edit_save_and_solve(qt_app: QtWidgets.QApplication, tmp_path: Path) -> None:
    """
    Reproduce the original tower edit/save crash flow using the checked-in grid.

    :param qt_app: Shared Qt application fixture.
    :param tmp_path: Temporary output directory.
    :return: Nothing.
    """
    app: QtWidgets.QApplication = qt_app
    working_file: Path = tmp_path / TOWER_EDIT_CRASH_FIXTURE.name
    shutil.copyfile(src=TOWER_EDIT_CRASH_FIXTURE, dst=working_file)

    gui: VeraGridMainGUI = VeraGridMainGUI()

    try:
        gui.open_file_now(filenames=str(working_file))
        wait_for_file_open(gui=gui, app=app, timeout_s=30.0)

        tower_count: int = len(gui.circuit.overhead_line_types)
        assert tower_count >= 2

        edit_tower_from_database_row(gui=gui, app=app, row=1)
        gc.collect(0)
        gc.collect(1)
        gc.collect(2)
        app.processEvents()

        edit_tower_from_database_row(gui=gui, app=app, row=0)
        gc.collect(0)
        gc.collect(1)
        gc.collect(2)
        app.processEvents()

        gui.save_file_now(filename=str(working_file))
        wait_for_file_save(gui=gui, app=app, timeout_s=30.0)
        assert working_file.exists()

        gc.collect(0)
        gc.collect(1)
        gc.collect(2)
        app.processEvents()
    finally:
        close_gui_accepting_exit(gui=gui, app=app)
        gui.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
        app.processEvents()

    reopened_circuit: vge.MultiCircuit = FileOpen(str(working_file)).open()
    power_flow_results: object = vge.power_flow(grid=reopened_circuit, options=vge.PowerFlowOptions())
    voltage_frame: object = power_flow_results.get_voltage_df()
    assert voltage_frame is not None
