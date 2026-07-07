from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from PySide6 import QtCore, QtWidgets

import VeraGridEngine.api as vge
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import (
    SchematicWidget,
    generate_schematic_diagram,
)
from VeraGrid.Gui.Main.SubClasses.io import IoMain
from VeraGrid.Gui.Main.SubClasses.Model.data_base import DataBaseTableMain
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy
from VeraGridEngine.enumerations import DeviceType


def _build_grid_with_two_schematic_diagrams() -> tuple[vge.MultiCircuit, vge.Line]:
    """
    Build a small grid with two stored schematic diagrams referencing the same devices.
    """
    grid = vge.MultiCircuit(name="diagram-widget-regression-grid")
    bus_from = grid.add_bus(vge.Bus(name="B1", Vnom=10.0, is_slack=True))
    bus_to = grid.add_bus(vge.Bus(name="B2", Vnom=10.0))
    line = grid.add_line(
        vge.Line(name="L12", bus_from=bus_from, bus_to=bus_to, r=0.1, x=0.2, rate=100.0)
    )

    for name in ("Stored Diagram A", "Stored Diagram B"):
        diagram = generate_schematic_diagram(
            buses=grid.get_buses(),
            lines=grid.get_lines(),
            dc_lines=grid.get_dc_lines(),
            transformers2w=grid.get_transformers2w(),
            transformers3w=grid.get_transformers3w(),
            transformers_nw=grid.get_transformers_nw(),
            windings=grid.get_windings(),
            hvdc_lines=grid.get_hvdc(),
            vsc_devices=grid.get_vsc(),
            upfc_devices=grid.get_upfc(),
            series_reactances=grid.get_series_reactances(),
            switches=grid.get_switches(),
            fluid_nodes=grid.get_fluid_nodes(),
            fluid_paths=grid.get_fluid_paths(),
            name=name,
        )
        grid.add_diagram(diagram)

    return grid, line


def _save_and_reload_grid(grid: vge.MultiCircuit, tmp_path: Path) -> vge.MultiCircuit:
    """
    Persist a grid to `.veragrid` and reopen it through the engine API.
    """
    file_name = tmp_path / "diagram_widget_storage.veragrid"
    vge.save_file(grid=grid, filename=str(file_name))
    return vge.open_file(str(file_name))


def _build_main_gui() -> DataBaseTableMain:
    """
    Build one real GUI instance and reset it to an empty project.
    """
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    _unused_app = app
    gui = DataBaseTableMain()
    gui.hide()
    gui.circuit = vge.MultiCircuit()
    gui.remove_all_diagrams()
    gui.setup_objects_tree()
    QtWidgets.QApplication.processEvents()
    return gui


def _select_view_row(view: QtWidgets.QAbstractItemView, row: int) -> None:
    """
    Select one row in a Qt item view.
    """
    model = view.model()
    assert model is not None

    index = model.index(row, 0)
    assert index.isValid()

    selection_model = view.selectionModel()
    assert selection_model is not None

    selection_model.clearSelection()
    selection_model.select(
        index,
        QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
        | QtCore.QItemSelectionModel.SelectionFlag.Rows,
    )
    view.setCurrentIndex(index)
    QtWidgets.QApplication.processEvents()


def _accept_next_yes_message_box() -> None:
    """
    Click the next modal `Yes/No` message box on its `Yes` button.
    """

    def _click_yes() -> None:
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(widget, QtWidgets.QMessageBox):
                button = widget.button(QtWidgets.QMessageBox.StandardButton.Yes)
                if button is not None:
                    button.click()
                    return
        QtCore.QTimer.singleShot(10, _click_yes)

    QtCore.QTimer.singleShot(0, _click_yes)


def _scenario_create_stored_diagrams(tmp_path: Path) -> None:
    """
    Run the stored-diagram materialization regression scenario.
    """
    grid, _line = _build_grid_with_two_schematic_diagrams()
    loaded_grid = _save_and_reload_grid(grid=grid, tmp_path=tmp_path)
    gui = _build_main_gui()

    gui.circuit = loaded_grid
    gui.create_circuit_stored_diagrams()

    assert len(gui.diagram_widgets_list) == len(loaded_grid.diagrams) == 2
    assert all(isinstance(widget, SchematicWidget) for widget in gui.diagram_widgets_list)
    assert all(widget.diagram is diagram for widget, diagram in zip(gui.diagram_widgets_list, loaded_grid.diagrams))


def _scenario_remove_non_active_diagram(tmp_path: Path) -> None:
    """
    Run the non-active diagram removal regression scenario.
    """
    grid, _line = _build_grid_with_two_schematic_diagrams()
    loaded_grid = _save_and_reload_grid(grid=grid, tmp_path=tmp_path)
    gui = _build_main_gui()

    gui.circuit = loaded_grid
    gui.create_circuit_stored_diagrams()

    shown_widget = gui.get_selected_diagram_widget()
    assert shown_widget is gui.diagram_widgets_list[0]
    assert shown_widget is not gui.diagram_widgets_list[1]

    _select_view_row(gui.ui.diagramsListView, 1)
    _accept_next_yes_message_box()
    gui.remove_diagram()
    QtWidgets.QApplication.processEvents()

    assert len(gui.diagram_widgets_list) == 1
    assert len(gui.circuit.diagrams) == 1
    assert gui.diagram_widgets_list[0].diagram is gui.circuit.diagrams[0]
    assert gui.get_selected_diagram_widget() is gui.diagram_widgets_list[0]


def _scenario_delete_db_object(tmp_path: Path) -> None:
    """
    Run the DB-object deletion regression scenario.
    """
    grid, line = _build_grid_with_two_schematic_diagrams()
    loaded_grid = _save_and_reload_grid(grid=grid, tmp_path=tmp_path)
    gui = _build_main_gui()

    gui.circuit = loaded_grid
    gui.create_circuit_stored_diagrams()

    objects_model = gui.create_objects_model(elements=gui.circuit.lines, elm_type=DeviceType.LineDevice)
    proxy_model = ObjectModelFilterProxy(mdl=objects_model)
    gui.ui.dataStructureTableView.setModel(proxy_model)
    _select_view_row(gui.ui.dataStructureTableView, 0)

    line_to_delete = gui.circuit.lines[0]
    assert line_to_delete.idtag == line.idtag
    assert all(widget.diagram.query_point(line_to_delete) is not None for widget in gui.diagram_widgets_list)

    _accept_next_yes_message_box()
    gui.delete_selected_db_table_objects()
    QtWidgets.QApplication.processEvents()

    assert len(gui.circuit.lines) == 0
    assert all(widget.diagram.query_point(line_to_delete) is None for widget in gui.diagram_widgets_list)


def _scenario_activate_scenario_without_diagrams() -> None:
    """
    Run the scenario-activation regression where no schematic should be auto-created.
    """
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    _unused_app = app

    gui = IoMain()
    gui.hide()
    gui.new_project_now(create_default_diagrams=False)

    base_grid = vge.MultiCircuit(name="base-scenario")
    bus_from = base_grid.add_bus(vge.Bus(name="B1", Vnom=10.0, is_slack=True))
    bus_to = base_grid.add_bus(vge.Bus(name="B2", Vnom=10.0))
    base_grid.add_line(vge.Line(name="L12", bus_from=bus_from, bus_to=bus_to, r=0.1, x=0.2, rate=100.0))

    gui.circuit = base_grid
    gui.reload_diagrams_for_active_scenario()

    assert len(gui.circuit.diagrams) == 0
    assert len(gui.diagram_widgets_list) == 0
    assert gui.ui.diagramsListView.model() is None

    root = gui.multiverse.root_nodes[0]
    child = gui.multiverse.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    gui.scenario_tree_model.refresh_data()

    child_index = gui.scenario_tree_model.index_for_node(child)
    assert child_index.isValid()

    gui.ui.multiverseTreeView.setCurrentIndex(child_index)
    gui.ui.multiverseTreeView.selectionModel().select(
        child_index,
        QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
        | QtCore.QItemSelectionModel.SelectionFlag.Rows,
    )
    QtWidgets.QApplication.processEvents()

    gui.set_as_current_scenario()
    QtWidgets.QApplication.processEvents()

    assert gui.multiverse.current_node is child
    assert gui.circuit.name == "child"
    assert gui.circuit.get_bus_number() == 2
    assert gui.circuit.get_branch_number(add_hvdc=False, add_vsc=False, add_switch=True) == 1
    assert len(gui.circuit.diagrams) == 0
    assert len(gui.diagram_widgets_list) == 0
    assert gui.ui.diagramsListView.model() is None


def main() -> None:
    """
    Dispatch one regression scenario in an isolated child process.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    if len(sys.argv) != 3:
        raise ValueError("Usage: diagram_widget_storage_runner.py <scenario> <tmp_path>")

    scenario = sys.argv[1]
    tmp_path = Path(sys.argv[2])

    if scenario == "create_stored_diagrams":
        _scenario_create_stored_diagrams(tmp_path=tmp_path)
    elif scenario == "remove_non_active_diagram":
        _scenario_remove_non_active_diagram(tmp_path=tmp_path)
    elif scenario == "delete_db_object":
        _scenario_delete_db_object(tmp_path=tmp_path)
    elif scenario == "activate_scenario_without_diagrams":
        _scenario_activate_scenario_without_diagrams()
    else:
        raise ValueError(f"Unknown scenario: {scenario}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        os._exit(1)
    else:
        os._exit(0)
