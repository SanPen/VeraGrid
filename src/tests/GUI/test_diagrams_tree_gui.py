# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import json
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Devices.Diagrams.diagram_tree import DiagramFolder, DiagramTree
from VeraGridEngine.Devices.Diagrams.schematic_diagram import SchematicDiagram
from VeraGridEngine.Devices.Diagrams.map_diagram import MapDiagram
from VeraGrid.Gui.Diagrams.diagrams_model import DiagramsTreeModel
from VeraGrid.Gui.Main.SubClasses.Model.data_base import DataBaseTableMain
from VeraGrid.Gui.Main.SubClasses.Model.scenarios import ScenariosMain


def test_diagrams_tree_model_structure_and_navigation(qt_app: object) -> None:
    del qt_app

    tree = DiagramTree()
    f1 = tree.add_folder("Region North")
    f2 = tree.add_folder("Zone A", parent=f1)
    d_root = SchematicDiagram(name="Root Schematic")
    d_f1 = SchematicDiagram(name="North 220kV")
    d_f2 = MapDiagram(name="Zone A Geo")

    tree.add_diagram(d_root)
    tree.add_diagram(d_f1, folder=f1)
    tree.add_diagram(d_f2, folder=f2)

    model = DiagramsTreeModel(tree=tree)

    # Root level has 1 folder and 1 diagram
    assert model.rowCount(QtCore.QModelIndex()) == 2
    assert model.columnCount(QtCore.QModelIndex()) == 1

    # Row 0 is f1, Row 1 is d_root
    idx_f1 = model.index(0, 0, QtCore.QModelIndex())
    assert idx_f1.isValid()
    assert model.data(idx_f1, QtCore.Qt.ItemDataRole.DisplayRole) == "Region North"
    assert model.get_item(idx_f1) is f1

    idx_root_d = model.index(1, 0, QtCore.QModelIndex())
    assert idx_root_d.isValid()
    assert model.data(idx_root_d, QtCore.Qt.ItemDataRole.DisplayRole) == "Root Schematic"
    assert model.get_item(idx_root_d) is d_root

    # Children of f1: 1 subfolder (f2) and 1 diagram (d_f1)
    assert model.rowCount(idx_f1) == 2
    idx_f2 = model.index(0, 0, idx_f1)
    assert idx_f2.isValid()
    assert model.data(idx_f2, QtCore.Qt.ItemDataRole.DisplayRole) == "Zone A"
    assert model.get_item(idx_f2) is f2

    idx_d_f1 = model.index(1, 0, idx_f1)
    assert idx_d_f1.isValid()
    assert model.data(idx_d_f1, QtCore.Qt.ItemDataRole.DisplayRole) == "North 220kV"
    assert model.get_item(idx_d_f1) is d_f1

    # Children of f2: 1 diagram (d_f2)
    assert model.rowCount(idx_f2) == 1
    idx_d_f2 = model.index(0, 0, idx_f2)
    assert idx_d_f2.isValid()
    assert model.data(idx_d_f2, QtCore.Qt.ItemDataRole.DisplayRole) == "Zone A Geo"
    assert model.get_item(idx_d_f2) is d_f2

    # Verify parent indices
    assert model.parent(idx_f1) == QtCore.QModelIndex()
    assert model.parent(idx_root_d) == QtCore.QModelIndex()
    assert model.parent(idx_f2) == idx_f1
    assert model.parent(idx_d_f1) == idx_f1
    assert model.parent(idx_d_f2) == idx_f2

    # index_for_item
    assert model.index_for_item(f1) == idx_f1
    assert model.index_for_item(f2) == idx_f2
    assert model.index_for_item(d_root) == idx_root_d
    assert model.index_for_item(d_f1) == idx_d_f1
    assert model.index_for_item(d_f2) == idx_d_f2


def test_diagrams_tree_model_rename_and_decorations(qt_app: object) -> None:
    del qt_app

    tree = DiagramTree()
    folder = tree.add_folder("Substations")
    diag = SchematicDiagram(name="Main Station")
    tree.add_diagram(diag, folder=folder)

    model = DiagramsTreeModel(tree=tree)
    idx_folder = model.index(0, 0, QtCore.QModelIndex())
    idx_diag = model.index(0, 0, idx_folder)

    # Decoration role check
    folder_icon = model.data(idx_folder, QtCore.Qt.ItemDataRole.DecorationRole)
    assert isinstance(folder_icon, QtGui.QIcon)
    diag_icon = model.data(idx_diag, QtCore.Qt.ItemDataRole.DecorationRole)
    assert isinstance(diag_icon, QtGui.QIcon)

    # Rename folder
    renamed = model.setData(idx_folder, "Grid Substations", QtCore.Qt.ItemDataRole.EditRole)
    assert renamed is True
    assert folder.name == "Grid Substations"
    assert model.data(idx_folder, QtCore.Qt.ItemDataRole.DisplayRole) == "Grid Substations"

    # Rename diagram
    renamed_diag = model.setData(idx_diag, "Station 400kV", QtCore.Qt.ItemDataRole.EditRole)
    assert renamed_diag is True
    assert diag.name == "Station 400kV"
    assert model.data(idx_diag, QtCore.Qt.ItemDataRole.DisplayRole) == "Station 400kV"

    # Empty name rejected
    assert model.setData(idx_folder, "   ", QtCore.Qt.ItemDataRole.EditRole) is False
    assert folder.name == "Grid Substations"


def test_diagrams_tree_model_drag_and_drop(qt_app: object) -> None:
    del qt_app

    tree = DiagramTree()
    folder_a = tree.add_folder("Folder A")
    folder_b = tree.add_folder("Folder B")
    diag = SchematicDiagram(name="Diagram 1")
    tree.add_diagram(diag, folder=folder_a)

    model = DiagramsTreeModel(tree=tree)
    idx_fa = model.index(0, 0, QtCore.QModelIndex())
    idx_fb = model.index(1, 0, QtCore.QModelIndex())
    idx_diag = model.index(0, 0, idx_fa)

    # Mime data serialization
    mime = model.mimeData([idx_diag])
    assert mime.hasFormat(DiagramsTreeModel.MIME_TYPE)
    payload = json.loads(bytes(mime.data(DiagramsTreeModel.MIME_TYPE)).decode("utf-8"))
    assert payload["type"] == "diagram"
    assert payload["idtag"] == diag.idtag

    # Drop into Folder B
    success = model.dropMimeData(mime, QtCore.Qt.DropAction.MoveAction, -1, -1, idx_fb)
    assert success is True
    assert diag in folder_b.diagrams
    assert diag not in folder_a.diagrams
    assert diag.group is folder_b

    # Drag Folder A into Folder B
    mime_fa = model.mimeData([idx_fa])
    success_fa = model.dropMimeData(mime_fa, QtCore.Qt.DropAction.MoveAction, -1, -1, idx_fb)
    assert success_fa is True
    assert folder_a in folder_b.folders
    assert folder_a.parent is folder_b


def test_main_gui_diagram_tree_operations(qt_app: object) -> None:
    del qt_app

    gui = DataBaseTableMain()
    gui.hide()
    gui.circuit = vge.MultiCircuit()
    gui.remove_all_diagrams()

    # Add folders programmatically
    f_north = gui.add_diagram_folder(folder_name="North")
    assert f_north is not None
    assert f_north in gui.circuit.diagrams.folders

    f_sub = gui.add_diagram_folder(parent_folder=f_north, folder_name="Substation 1")
    assert f_sub is not None
    assert f_sub in f_north.folders
    assert f_sub.parent is f_north

    # Add a schematic diagram
    diag = SchematicDiagram(name="Overview")
    gui.circuit.add_diagram(diag, folder=f_sub)
    gui.create_circuit_stored_diagrams()

    assert len(gui.circuit.diagrams) == 1
    assert len(gui.diagram_widgets_list) == 1
    assert gui.diagram_widgets_list[0].diagram is diag
    assert diag.group is f_sub

    # Selected widget is the schematic
    selected_widget = gui.get_selected_diagram_widget()
    assert selected_widget is gui.diagram_widgets_list[0]

    # Delete folder f_north should delete f_sub and diag
    model = gui.ui.diagramsTreeView.model()
    idx_north = model.index_for_item(f_north)
    assert idx_north.isValid()

    # Select f_north
    gui.ui.diagramsTreeView.selectionModel().select(
        idx_north,
        QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtCore.QItemSelectionModel.SelectionFlag.Rows
    )

    # Test removing folder f_north programmatically (bypassing confirmation prompt)
    folders_to_delete = {f_north}
    diagrams_to_delete = set(f_north.get_all_diagrams())
    assert diag in diagrams_to_delete

    gui.circuit.diagrams.remove_folder(f_north)
    gui.set_diagrams_list_view()

    assert len(gui.circuit.diagrams.folders) == 0
    gui.remove_all_diagrams()


def test_gui_folder_creation_and_drag_drop_moves(qt_app: object) -> None:
    del qt_app

    gui = DataBaseTableMain()
    gui.hide()
    gui.circuit = vge.MultiCircuit()
    gui.remove_all_diagrams()

    # 1. Test add_diagram_folder with parent_folder=False (Qt action triggered simulation)
    f1 = gui.add_diagram_folder(parent_folder=False, folder_name="Folder1")
    assert f1 is not None
    assert f1 in gui.circuit.diagrams.folders

    # 2. Test add_diagram_folder as subfolder
    f2 = gui.add_diagram_folder(parent_folder=f1, folder_name="SubFolder1")
    assert f2 in f1.folders
    assert f2.parent is f1

    # 3. Add diagrams
    d1 = SchematicDiagram(name="Diagram1")
    d2 = SchematicDiagram(name="Diagram2")
    d3 = SchematicDiagram(name="Diagram3")
    gui.circuit.add_diagram(d1)            # at root
    gui.circuit.add_diagram(d2, folder=f1) # in f1
    gui.circuit.add_diagram(d3, folder=f2) # in f2
    gui.create_circuit_stored_diagrams()

    view = gui.ui.diagramsTreeView
    model = view.model()
    assert view.dragEnabled() is True
    assert view.acceptDrops() is True

    # 4. Drag d1 (at root) into f2
    mime_d1 = model.mimeData([model.index_for_item(d1)])
    idx_f2 = model.index_for_item(f2)
    res = model.dropMimeData(mime_d1, QtCore.Qt.DropAction.MoveAction, -1, -1, idx_f2)
    assert res is True
    assert d1 in f2.diagrams
    assert d1.group is f2

    # 5. Drag d3 (in f2) to root
    mime_d3 = model.mimeData([model.index_for_item(d3)])
    res2 = model.dropMimeData(mime_d3, QtCore.Qt.DropAction.MoveAction, -1, -1, QtCore.QModelIndex())
    assert res2 is True
    assert d3 in gui.circuit.diagrams.diagrams
    assert d3.group is None

    # 6. Drag d2 (in f1) onto d1 (which is in f2)
    mime_d2 = model.mimeData([model.index_for_item(d2)])
    idx_d1 = model.index_for_item(d1)
    res3 = model.dropMimeData(mime_d2, QtCore.Qt.DropAction.MoveAction, -1, -1, idx_d1)
    assert res3 is True
    assert d2 in f2.diagrams
    assert d2.group is f2

    gui.remove_all_diagrams()


def test_gui_multiverse_diagram_tree_scenario_switching(qt_app: object) -> None:
    del qt_app

    gui = ScenariosMain()
    gui.hide()

    try:
        # 1. Base circuit with diagram and folder
        grid = vge.MultiCircuit(name="base_grid")
        b1 = grid.add_bus(vge.Bus(name="B1", Vnom=10.0))
        b2 = grid.add_bus(vge.Bus(name="B2", Vnom=10.0))
        grid.add_line(vge.Line(name="L12", bus_from=b1, bus_to=b2))

        d1 = SchematicDiagram(name="Diagram1")
        f1 = grid.diagrams.add_folder("Folder1")
        grid.add_diagram(d1, folder=f1)

        # Assign circuit to GUI (sets up multiverse with root)
        gui.circuit = grid
        gui.create_circuit_stored_diagrams()

        root_node = gui.multiverse.root_nodes[0]
        root_index = gui.scenario_tree_model.index_for_node(root_node)

        # Check GUI tree view has Folder1
        view = gui.ui.diagramsTreeView
        model = view.model()
        assert model is not None
        assert model.rowCount(QtCore.QModelIndex()) >= 1

        # 2. Add child scenario via scenario tree model
        child_delta = vge.MultiCircuit(name="Child Scenario")
        child_node = gui.scenario_tree_model.append_child(root_index, child_delta)
        child_index = gui.scenario_tree_model.index_for_node(child_node)

        # 3. Switch to child scenario
        gui.ui.multiverseTreeView.setCurrentIndex(child_index)
        gui.set_as_current_scenario()

        assert gui.multiverse.current_node is child_node
        # Child's diagramsTreeView model must reflect child's diagrams
        child_view_model = gui.ui.diagramsTreeView.model()
        assert child_view_model is not None
        assert len(gui.circuit.diagrams.folders) == 1
        assert gui.circuit.diagrams.folders[0].name == "Folder1"

        # Mutate diagrams in child scenario: add Folder2 at root and move diagram
        f2 = gui.add_diagram_folder(parent_folder=None, folder_name="Folder2")
        child_d1 = gui.circuit.diagrams.folders[0].diagrams[0]
        gui.circuit.diagrams.move_diagram(child_d1, target_folder=f2)
        gui.set_diagrams_list_view()

        assert len(gui.circuit.diagrams.folders) == 2

        # 4. Switch back to root scenario
        gui.ui.multiverseTreeView.setCurrentIndex(root_index)
        gui.set_as_current_scenario()

        assert gui.multiverse.current_node is root_node
        # Root scenario must still have only 1 folder (Folder1) containing Diagram1
        assert len(gui.circuit.diagrams.folders) == 1
        assert gui.circuit.diagrams.folders[0].name == "Folder1"
        assert len(gui.circuit.diagrams.folders[0].diagrams) == 1
        assert gui.circuit.diagrams.folders[0].diagrams[0].name == "Diagram1"

        # 5. Switch back to child scenario
        gui.ui.multiverseTreeView.setCurrentIndex(child_index)
        gui.set_as_current_scenario()

        assert gui.multiverse.current_node is child_node
        assert len(gui.circuit.diagrams.folders) == 2
        f2_child = gui.circuit.diagrams.find_folder(f2.idtag)
        assert f2_child is not None
        assert len(f2_child.diagrams) == 1
        assert f2_child.diagrams[0].name == "Diagram1"

    finally:
        gui.remove_all_diagrams()


