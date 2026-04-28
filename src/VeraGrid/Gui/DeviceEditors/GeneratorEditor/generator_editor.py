# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
import sys
from PySide6 import QtCore, QtWidgets
from typing import Callable

from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor_gui import Ui_GeneratorQCurveEditorDialog
from VeraGridEngine.Devices.Injections.generator_q_curve import GeneratorQCurve
from VeraGridEngine.basic_structures import Mat, Vec


class GeneratorQCurveEditorTableModel(QtCore.QAbstractTableModel):
    """
    Table model for reactive power capability points.
    """

    def __init__(
        self,
        data: Mat,
        headers: list[str],
        callback: Callable[[], None] | None = None,
        parent: QtCore.QObject | None = None,
    ) -> None:
        """
        Build table model.

        :param data: Initial point matrix.
        :param headers: Column labels.
        :param callback: Optional callback on data changes.
        :param parent: Qt parent object.
        """
        super().__init__(parent)
        self._data: Mat = data
        self._headers: list[str] = headers
        self.callback: Callable[[], None] | None = callback

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return number of rows.

        :param parent: Unused parent index.
        :return: Row count.
        """
        _ = parent
        return len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return number of columns.

        :param parent: Unused parent index.
        :return: Column count.
        """
        _ = parent
        return len(self._headers)

    def data(self, index: QtCore.QModelIndex, role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> str | None:
        """
        Return displayed/edited value.

        :param index: Target table index.
        :param role: Qt data role.
        :return: Formatted cell value or None.
        """
        if role == int(QtCore.Qt.ItemDataRole.DisplayRole) or role == int(QtCore.Qt.ItemDataRole.EditRole):
            return str(self._data[index.row(), index.column()])
        else:
            return None

    def setData(self, index: QtCore.QModelIndex, value: object, role: int = int(QtCore.Qt.ItemDataRole.EditRole)) -> bool:
        """
        Set a numeric cell value.

        :param index: Target table index.
        :param value: New value.
        :param role: Qt data role.
        :return: Success flag.
        """
        if role == int(QtCore.Qt.ItemDataRole.EditRole):
            try:
                numeric_value: float = float(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False

            self._data[index.row(), index.column()] = numeric_value
            self.dataChanged.emit(index, index)

            if self.callback is not None:
                self.callback()
            else:
                pass

            if index.column() == 0:
                self.sort_data()
            else:
                pass
            return True
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Define item flags.

        :param index: Target table index.
        :return: Flags for editable selected items.
        """
        _ = index
        return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsSelectable

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = int(QtCore.Qt.ItemDataRole.DisplayRole),
    ) -> str | None:
        """
        Provide header labels.

        :param section: Header section index.
        :param orientation: Header orientation.
        :param role: Qt data role.
        :return: Header text or None.
        """
        if role == int(QtCore.Qt.ItemDataRole.DisplayRole) and orientation == QtCore.Qt.Orientation.Horizontal:
            return self._headers[section]
        else:
            return super().headerData(section, orientation, role)

    def add_row(self, row_data: Vec) -> None:
        """
        Append one row.

        :param row_data: Three-component row vector.
        """
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self._data = np.vstack([self._data, row_data])
        self.endInsertRows()

    def del_row(self, row_index: int) -> None:
        """
        Remove row at index.

        :param row_index: Row index to remove.
        """
        if self._data.shape[0] > 0:
            self.beginRemoveRows(QtCore.QModelIndex(), row_index, row_index)
            self._data = np.delete(self._data, row_index, axis=0)
            self.endRemoveRows()
        else:
            pass

    def del_last_row(self) -> None:
        """
        Remove the last row if any.
        """
        if self._data.shape[0] > 0:
            last_index: int = int(self._data.shape[0] - 1)
            self.beginRemoveRows(QtCore.QModelIndex(), last_index, last_index)
            self._data = np.delete(self._data, last_index, axis=0)
            self.endRemoveRows()
        else:
            pass

    def sort_data(self) -> None:
        """
        Sort rows by active power column.
        """
        sorted_indices: Vec = np.argsort(self._data[:, 0])
        self._data = self._data[sorted_indices]
        self.layoutChanged.emit()

    def get_data(self) -> Mat:
        """
        Return current matrix.

        :return: Data matrix.
        """
        return self._data


class GeneratorQCurveEditor(QtWidgets.QDialog):
    """
    Reactive power capability curve editor backed by a Qt Designer `.ui`.
    """

    def __init__(self, q_curve: GeneratorQCurve, Qmin: float, Qmax: float, Pmin: float, Pmax: float, Snom: float) -> None:
        """
        Build the curve editor.

        :param q_curve: Generator reactive capability object.
        :param Qmin: Initial minimum reactive power.
        :param Qmax: Initial maximum reactive power.
        :param Pmin: Initial minimum active power.
        :param Pmax: Initial maximum active power.
        :param Snom: Initial apparent power nominal value.
        """
        super().__init__()
        self.ui = Ui_GeneratorQCurveEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Reactive power curve editor")

        self.q_curve: GeneratorQCurve = q_curve
        self.Qmin: float = Qmin
        self.Qmax: float = Qmax
        self.Pmin: float = Pmin
        self.Pmax: float = Pmax
        self.Snom: float = Snom
        self.headers: list[str] = ["P", "Qmin", "Qmax"]

        self.table_model: GeneratorQCurveEditorTableModel = GeneratorQCurveEditorTableModel(
            data=self.q_curve.get_data(),
            headers=self.headers,
            callback=self.plot,
            parent=self,
        )

        self._configure_widgets()
        self._connect_signals()
        self.plot()

    def _configure_widgets(self) -> None:
        """
        Configure table and selection behavior.
        """
        self.ui.tableView.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.ui.tableView.setSelectionMode(QtWidgets.QTableView.SelectionMode.SingleSelection)
        self.ui.tableView.setModel(self.table_model)

    def _connect_signals(self) -> None:
        """
        Bind button actions.
        """
        self.ui.addRowButton.clicked.connect(self.add_row)
        self.ui.delRowButton.clicked.connect(self.remove_selected_row)

    def add_row(self) -> None:
        """
        Add an empty row.
        """
        self.table_model.add_row(np.zeros(3))

    def remove_selected_row(self) -> None:
        """
        Remove selected row or last row when none is selected.
        """
        selected_indexes: list[QtCore.QModelIndex] = self.ui.tableView.selectionModel().selectedRows()
        if len(selected_indexes) > 0:
            selected_row: int = selected_indexes[0].row()
            self.table_model.del_row(selected_row)
        else:
            self.table_model.del_last_row()

    def collect_data(self) -> None:
        """
        Persist current table values into the q-curve object and update limits.
        """
        self.q_curve.set(self.table_model.get_data())
        self.Snom = self.q_curve.get_Snom()
        self.Qmax = self.q_curve.get_Qmax()
        self.Qmin = self.q_curve.get_Qmin()
        self.Pmax = self.q_curve.get_Pmax()
        self.Pmin = self.q_curve.get_Pmin()

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """
        Persist the edited curve before close.

        :param event: Qt close event.
        """
        _ = event
        self.collect_data()

    def plot(self) -> None:
        """
        Render capability envelope and curve points.
        """
        self.ui.plotter.clear()
        self.collect_data()

        radius: float = self.q_curve.get_Snom()
        theta: Vec = np.linspace(0, 2.0 * np.pi, 100)
        x_values: Vec = radius * np.cos(theta)
        y_values: Vec = radius * np.sin(theta)

        self.ui.plotter.plot(
            x_values,
            y_values,
            # color="gray",
            # marker=None,
            # linestyle="dotted",
            # linewidth=1,
            # markersize=4,
        )

        self.q_curve.plot(ax=self.ui.plotter.canvas.ax)
        self.ui.plotter.redraw()
        self.ui.plotter.canvas.fig.tight_layout()


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    q_curve_demo = GeneratorQCurve()
    q_curve_demo.make_default_q_curve(Snom=100.0, Qmin=-60.0, Qmax=60.0, n=8)
    dialog_demo = GeneratorQCurveEditor(
        q_curve=q_curve_demo,
        Qmin=-60.0,
        Qmax=60.0,
        Pmin=0.0,
        Pmax=100.0,
        Snom=100.0,
    )
    dialog_demo.show()
    sys.exit(qt_app.exec())
