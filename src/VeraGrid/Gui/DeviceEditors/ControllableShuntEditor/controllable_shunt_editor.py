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


class ControllableShuntStepsEditorWidget(QtWidgets.QWidget):
    """
    Embedded widget to edit controllable-shunt step arrays.
    """

    steps_applied = QtCore.Signal(bool)

    def __init__(self, api_object: ControllableShunt, parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build controllable shunt steps editor.

        :param api_object: Controllable shunt object to mutate on apply.
        :param parent: Optional Qt parent widget.
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_ControllableShuntEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("")

        self.api_object: ControllableShunt = api_object
        self.model: ControllableShuntArray = ControllableShuntArray(
            data=[self.api_object.active_steps, self.api_object.g_steps, self.api_object.b_steps],
            headers=["Active", "G steps (MW)", "B steps (MVAr)"],
            dtypes=[bool, float, float],
        )

        self.ui.tableView.setModel(self.model)
        self.ui.doneButton.setText("Apply")
        self._connect_signals()

    def _connect_signals(self) -> None:
        """
        Connect UI events.
        """
        self.ui.addButton.clicked.connect(self.add_row)
        self.ui.deleteButton.clicked.connect(self.delete_row)
        self.ui.doneButton.clicked.connect(self.apply_changes)

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

    def apply_changes(self) -> bool:
        """
        Apply edited arrays into API object.

        :return: ``True`` when assignment succeeds.
        """
        self.api_object.active_steps = self.get_active_steps()
        self.api_object.g_steps = self.get_g_steps()
        self.api_object.b_steps = self.get_b_steps()

        if len(self.api_object.g_steps) > 0:
            self.api_object.Gmax = float(self.api_object.g_steps.max())
            self.api_object.Gmin = float(self.api_object.g_steps.min())
        else:
            self.api_object.Gmax = 0.0
            self.api_object.Gmin = 0.0

        if len(self.api_object.b_steps) > 0:
            self.api_object.Bmax = float(self.api_object.b_steps.max())
            self.api_object.Bmin = float(self.api_object.b_steps.min())
        else:
            self.api_object.Bmax = 0.0
            self.api_object.Bmin = 0.0

        self.steps_applied.emit(True)
        return True


class ControllableShuntEditor(QtWidgets.QDialog):
    """
    Standalone controllable shunt editor dialog.
    """

    def __init__(self, api_object: ControllableShunt) -> None:
        """
        Build controllable shunt editor.

        :param api_object: Controllable shunt object to mutate on acceptance.
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(self.tr("Controllable shunt editor"))
        self.resize(640, 420)

        self.main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        self.steps_widget: ControllableShuntStepsEditorWidget = ControllableShuntStepsEditorWidget(
            api_object=api_object,
            parent=self,
        )
        self.main_layout.addWidget(self.steps_widget)
        self.steps_widget.steps_applied.connect(self.accept)

    def get_active_steps(self) -> np.ndarray:
        """
        Get active steps array from model.

        :return: Active flags vector.
        """
        return self.steps_widget.get_active_steps()

    def get_g_steps(self) -> np.ndarray:
        """
        Get G steps array from model.

        :return: Conductance steps.
        """
        return self.steps_widget.get_g_steps()

    def get_b_steps(self) -> np.ndarray:
        """
        Get B steps array from model.

        :return: Susceptance steps.
        """
        return self.steps_widget.get_b_steps()


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    shunt_demo = ControllableShunt(name="Demo controllable shunt")
    shunt_demo.active_steps = np.array([True, True, False], dtype=bool)
    shunt_demo.g_steps = np.array([0.0, 10.0, 20.0], dtype=float)
    shunt_demo.b_steps = np.array([0.0, -5.0, -10.0], dtype=float)
    dialog_demo = ControllableShuntEditor(api_object=shunt_demo)
    dialog_demo.show()
    sys.exit(qt_app.exec())
