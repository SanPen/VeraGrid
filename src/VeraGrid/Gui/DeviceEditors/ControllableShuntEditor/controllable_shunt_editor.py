# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys
from typing import List

import numpy as np
from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DeviceEditors.ControllableShuntEditor.controllable_shunt_editor_gui import (
    Ui_ControllableShuntEditorDialog,
)
from VeraGrid.Gui.general_dialogues import ArrayTableModel
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt


class ControllableShuntArray(ArrayTableModel):
    """
    Table model for controllable shunt step arrays.
    """

    def __init__(self, data: List[np.ndarray], headers: List[str], dtypes: List[np.dtype]) -> None:
        """
        Build shunt array model.

        :param data: Column-major arrays used by ArrayTableModel.
        :param headers: Header labels.
        :param dtypes: Column dtypes to enforce on edit.
        """
        ArrayTableModel.__init__(self, data=data, headers=headers)
        self.dtypes: List[np.dtype] = dtypes

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: float,
        role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.EditRole,
    ) -> bool:
        """
        Set edited table value with dtype casting.

        :param index: Cell index.
        :param value: New value.
        :param role: Qt role.
        :return: True when set succeeds.
        """
        if not index.isValid():
            return False
        else:
            pass

        if role == QtCore.Qt.ItemDataRole.EditRole:
            row_index: int = index.row()
            col_index: int = index.column()
            try:
                numeric_value: float = float(value)
            except ValueError:
                return False

            col_dtype: np.dtype = self.dtypes[col_index]
            self._data[col_index][row_index] = col_dtype(numeric_value)
            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole])
            return True
        else:
            return False


class ControllableShuntEditor(QtWidgets.QDialog):
    """
    Controllable shunt editor backed by a Qt Designer `.ui`.
    """

    def __init__(self, api_object: ControllableShunt) -> None:
        """
        Build controllable shunt editor.

        :param api_object: Controllable shunt object to mutate on acceptance.
        """
        super().__init__()
        self.ui = Ui_ControllableShuntEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Controllable shunt editor")

        self.api_object: ControllableShunt = api_object
        self.model: ControllableShuntArray = ControllableShuntArray(
            data=[self.api_object.active_steps, self.api_object.g_steps, self.api_object.b_steps],
            headers=["Active", "G steps (MW)", "B steps (MVAr)"],
            dtypes=[bool, float, float],
        )

        self.ui.tableView.setModel(self.model)
        self._connect_signals()

    def _connect_signals(self) -> None:
        """
        Connect UI events.
        """
        self.ui.addButton.clicked.connect(self.add_row)
        self.ui.deleteButton.clicked.connect(self.delete_row)
        self.ui.doneButton.clicked.connect(self.accept_click)

    def get_active_steps(self) -> np.ndarray:
        """
        Get active steps array from model.

        :return: Active flags vector.
        """
        return self.model.get_data()[0]

    def get_g_steps(self) -> np.ndarray:
        """
        Get G steps array from model.

        :return: Conductance steps.
        """
        return self.model.get_data()[1]

    def get_b_steps(self) -> np.ndarray:
        """
        Get B steps array from model.

        :return: Susceptance steps.
        """
        return self.model.get_data()[2]

    def add_row(self) -> None:
        """
        Add one row at the bottom.
        """
        row_count: int = self.model.rowCount()
        self.model.insertRows(row_count, 1)

    def delete_row(self) -> None:
        """
        Delete selected rows.
        """
        selected_indexes: list[QtCore.QModelIndex] = self.ui.tableView.selectionModel().selectedIndexes()
        selected_rows: list[int] = list({index.row() for index in selected_indexes})
        selected_rows.sort(reverse=True)

        for row_index in selected_rows:
            self.model.removeRows(position=row_index, rows=1)

    def accept_click(self) -> None:
        """
        Apply edited arrays into API object and close dialog.
        """
        self.api_object.active_steps = self.get_active_steps()
        self.api_object.g_steps = self.get_g_steps()
        self.api_object.Gmax = self.api_object.g_steps.max()
        self.api_object.Gmin = self.api_object.g_steps.min()
        self.api_object.b_steps = self.get_b_steps()
        self.api_object.Bmax = self.api_object.b_steps.max()
        self.api_object.Bmin = self.api_object.b_steps.min()
        self.accept()


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    shunt_demo = ControllableShunt(name="Demo controllable shunt")
    shunt_demo.active_steps = np.array([True, True, False], dtype=bool)
    shunt_demo.g_steps = np.array([0.0, 10.0, 20.0], dtype=float)
    shunt_demo.b_steps = np.array([0.0, -5.0, -10.0], dtype=float)
    dialog_demo = ControllableShuntEditor(api_object=shunt_demo)
    dialog_demo.show()
    sys.exit(qt_app.exec())
