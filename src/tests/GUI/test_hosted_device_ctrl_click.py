# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from unittest.mock import MagicMock, patch
from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.Main.SubClasses.Model import data_base
from VeraGrid.Gui.Main.SubClasses.Model.data_base import DataBaseTableMain
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType


def _find_device_type_index(model: QtCore.QAbstractItemModel,
                            parent: QtCore.QModelIndex,
                            device_type: DeviceType) -> QtCore.QModelIndex:
    """
    Locate one device leaf in the database tree.

    :param model: Tree model to inspect.
    :param parent: Parent index whose children are searched.
    :param device_type: Stable enum payload to find.
    :return: Matching model index or an invalid index when absent.
    """
    row: int
    for row in range(model.rowCount(parent)):
        index: QtCore.QModelIndex = model.index(row, 0, parent)
        payload: object = index.data(QtCore.Qt.ItemDataRole.UserRole)
        if payload == device_type:
            return index
        else:
            child_index: QtCore.QModelIndex = _find_device_type_index(
                model=model,
                parent=index,
                device_type=device_type,
            )
            if child_index.isValid():
                return child_index
            else:
                pass
    return QtCore.QModelIndex()


def test_open_hosted_device_editor_only_upon_ctrl_click(qt_app: object) -> None:
    """
    Verify that open_hosted_device_editor_at_proxy_index is only triggered upon Ctrl+click,
    while normal click and normal right-click preserve selection and the context menu.

    :param qt_app: Qt application fixture.
    :return: None.
    """
    _unused: object = qt_app
    gui: DataBaseTableMain = DataBaseTableMain()
    gui.hide()

    try:
        circuit: MultiCircuit = MultiCircuit()
        bus: Bus = Bus(name="Bus 1")
        generator: Generator = Generator(name="Generator 1")
        circuit.add_bus(bus)
        circuit.add_generator(bus=bus, api_obj=generator)
        gui.circuit = circuit
        gui.setup_objects_tree()

        tree_model: QtCore.QAbstractItemModel | None = gui.ui.dataStructuresTreeView.model()
        assert tree_model is not None
        gen_index: QtCore.QModelIndex = _find_device_type_index(
            model=tree_model,
            parent=QtCore.QModelIndex(),
            device_type=DeviceType.GeneratorDevice,
        )
        assert gen_index.isValid()

        selection_model: QtCore.QItemSelectionModel | None = gui.ui.dataStructuresTreeView.selectionModel()
        assert selection_model is not None
        selection_model.select(
            gen_index,
            QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QtCore.QItemSelectionModel.SelectionFlag.Rows,
        )
        gui.ui.dataStructuresTreeView.setCurrentIndex(gen_index)
        gui.view_objects_data()

        table_model: QtCore.QAbstractItemModel | None = gui.ui.dataStructureTableView.model()
        assert table_model is not None
        assert table_model.rowCount() == 1

        # Locate the bus reference column
        bus_col: int = -1
        col: int
        for col in range(table_model.columnCount()):
            idx: QtCore.QModelIndex = table_model.index(0, col)
            if table_model.data(idx, QtCore.Qt.ItemDataRole.DisplayRole) == "Bus 1":
                bus_col = col
                break
        assert bus_col >= 0
        bus_index: QtCore.QModelIndex = table_model.index(0, bus_col)

        # 1. Normal click without Ctrl: should not open hosted device editor
        with patch.object(gui, "open_hosted_device_editor_at_proxy_index") as mock_open:
            with patch.object(data_base.QtWidgets.QApplication, "keyboardModifiers",
                              return_value=QtCore.Qt.KeyboardModifier.NoModifier):
                gui.on_data_structure_table_clicked(bus_index)
                assert not mock_open.called

        # 2. Ctrl + click: should launch editor for the referenced bus
        with patch.object(gui, "launch_device_editor") as mock_launch:
            with patch.object(data_base.QtWidgets.QApplication, "keyboardModifiers",
                              return_value=QtCore.Qt.KeyboardModifier.ControlModifier):
                gui.on_data_structure_table_clicked(bus_index)
                assert mock_launch.called
                assert mock_launch.call_args[1]["elm"] is bus

        # 3. Context menu (right click) without Ctrl: should not open editor, should show menu
        pos: QtCore.QPoint = gui.ui.dataStructureTableView.visualRect(bus_index).center()
        with patch.object(gui, "open_hosted_device_editor_at_proxy_index") as mock_open:
            with patch.object(data_base.QtWidgets, "QMenu") as mock_qmenu:
                menu_instance: MagicMock = MagicMock()
                mock_qmenu.return_value = menu_instance
                with patch.object(data_base.QtWidgets.QApplication, "keyboardModifiers",
                                  return_value=QtCore.Qt.KeyboardModifier.NoModifier):
                    gui.show_objects_context_menu(pos)
                    assert not mock_open.called
                    assert menu_instance.exec.called

        # 4. Context menu (right click) with Ctrl: should open editor directly and not show menu
        with patch.object(gui, "launch_device_editor") as mock_launch:
            with patch.object(data_base.QtWidgets, "QMenu") as mock_qmenu:
                menu_instance = MagicMock()
                mock_qmenu.return_value = menu_instance
                with patch.object(data_base.QtWidgets.QApplication, "keyboardModifiers",
                                  return_value=QtCore.Qt.KeyboardModifier.ControlModifier):
                    gui.show_objects_context_menu(pos)
                    assert mock_launch.called
                    assert mock_launch.call_args[1]["elm"] is bus
                    assert not menu_instance.exec.called

    finally:
        gui.close()
        gui.deleteLater()
        QtWidgets.QApplication.processEvents()
