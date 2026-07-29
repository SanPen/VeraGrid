from __future__ import annotations

import csv
import io
from typing import Sequence

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DeviceEditors.LineLocationsEditor.line_locations_editor_gui import (
    Ui_LineLocationsEditorWidget,
)
from VeraGrid.Gui.gui_functions import FloatDelegate, IntDelegate, TextDelegate
from VeraGridEngine.Devices.Branches.line_locations import LineLocation, LineLocations


class LineLocationsTableModel(QtCore.QAbstractTableModel):
    """
    Table model exposing one :class:`LineLocations` object as editable rows.
    """

    __slots__ = ("_headers", "_rows")

    def __init__(self,
                 line_locations: LineLocations,
                 parent: QtCore.QObject | None = None) -> None:
        """
        Build the table model from one line-locations snapshot.

        :param line_locations: Source value copied into the model.
        :param parent: Optional Qt parent.
        """
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._headers: tuple[str, ...] = ("sequence", "latitude", "longitude", "altitude", "idtag")
        self._rows: list[list[object]] = list()
        self.load_from_line_locations(line_locations=line_locations)

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return the row count.

        :param parent: Unused parent index.
        :return: Number of rows.
        """
        _ = parent
        return len(self._rows)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return the column count.

        :param parent: Unused parent index.
        :return: Number of columns.
        """
        _ = parent
        return len(self._headers)

    def data(self,
             index: QtCore.QModelIndex,
             role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> object | None:
        """
        Return one table cell value.

        :param index: Cell index.
        :param role: Qt data role.
        :return: Cell value or ``None``.
        """
        if index.isValid():
            if role == int(QtCore.Qt.ItemDataRole.DisplayRole):
                return str(self._rows[index.row()][index.column()])
            elif role == int(QtCore.Qt.ItemDataRole.EditRole):
                return self._rows[index.row()][index.column()]
            else:
                return None
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = int(QtCore.Qt.ItemDataRole.EditRole)) -> bool:
        """
        Store one edited cell value.

        :param index: Target cell.
        :param value: New value.
        :param role: Qt data role.
        :return: ``True`` when the value is accepted.
        """
        if index.isValid():
            if role == int(QtCore.Qt.ItemDataRole.EditRole):
                try:
                    if index.column() == 0:
                        parsed_value: object = int(value)
                    else:
                        if index.column() in (1, 2, 3):
                            parsed_value = float(value)
                        else:
                            parsed_value = str(value)
                except (TypeError, ValueError):
                    return False

                self._rows[index.row()][index.column()] = parsed_value
                self.dataChanged.emit(index, index, [int(QtCore.Qt.ItemDataRole.DisplayRole)])
                return True
            else:
                return False
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Return the item flags for one cell.

        :param index: Cell index.
        :return: Qt item flags.
        """
        if index.isValid():
            return (QtCore.Qt.ItemFlag.ItemIsEnabled
                    | QtCore.Qt.ItemFlag.ItemIsSelectable
                    | QtCore.Qt.ItemFlag.ItemIsEditable)
        else:
            return QtCore.Qt.ItemFlag.NoItemFlags

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> str | None:
        """
        Return row and column header labels.

        :param section: Header section index.
        :param orientation: Header orientation.
        :param role: Qt data role.
        :return: Header text or ``None``.
        """
        if role == int(QtCore.Qt.ItemDataRole.DisplayRole):
            if orientation == QtCore.Qt.Orientation.Horizontal:
                if section < len(self._headers):
                    return self._headers[section]
                else:
                    return ""
            else:
                return str(section)
        else:
            return None

    def load_from_line_locations(self, line_locations: LineLocations) -> None:
        """
        Replace the current rows with one copied ``LineLocations`` object.

        :param line_locations: Source value.
        """
        self.beginResetModel()
        self._rows = list()

        location: LineLocation
        for location in line_locations.get_locations():
            self._rows.append([
                int(location.seq),
                float(location.lat),
                float(location.long),
                float(location.alt),
                str(location.idtag),
            ])

        self.endResetModel()

    def load_rows(self, rows: list[list[object]]) -> None:
        """
        Replace the current rows with one raw row collection.

        :param rows: Raw row values in table-column order.
        """
        self.beginResetModel()
        self._rows = [list(row) for row in rows]
        self.endResetModel()
        self.renumber_sequences()

    def add_empty_row(self) -> None:
        """
        Append one default row at the end of the table.
        """
        row_index: int = len(self._rows)
        self.beginInsertRows(QtCore.QModelIndex(), row_index, row_index)
        self._rows.append([row_index, 0.0, 0.0, 0.0, ""])
        self.endInsertRows()

    def remove_rows(self, row_indices: Sequence[int]) -> None:
        """
        Remove the requested rows and renumber the remaining sequence column.

        :param row_indices: Row indices to remove.
        """
        sorted_rows: list[int] = sorted(set(row_indices), reverse=True)
        row_index: int
        for row_index in sorted_rows:
            if 0 <= row_index < len(self._rows):
                self.beginRemoveRows(QtCore.QModelIndex(), row_index, row_index)
                del self._rows[row_index]
                self.endRemoveRows()
            else:
                pass

        self.renumber_sequences()

    def renumber_sequences(self) -> None:
        """
        Rewrite the sequence column so rows remain ordered after insertions and deletions.
        """
        row_index: int
        for row_index in range(len(self._rows)):
            self._rows[row_index][0] = row_index

        if len(self._rows) > 0:
            top_left: QtCore.QModelIndex = self.index(0, 0)
            bottom_right: QtCore.QModelIndex = self.index(len(self._rows) - 1, 0)
            self.dataChanged.emit(top_left, bottom_right, [int(QtCore.Qt.ItemDataRole.DisplayRole)])
        else:
            pass

    def to_line_locations(self) -> LineLocations:
        """
        Build one ``LineLocations`` object from the current table rows.

        :return: New ``LineLocations`` instance.
        """
        line_locations: LineLocations = LineLocations()

        row: list[object]
        for row in self._rows:
            line_locations.add(
                sequence=int(row[0]),
                latitude=float(row[1]),
                longitude=float(row[2]),
                altitude=float(row[3]),
                idtag=str(row[4]),
            )

        return line_locations


class LineLocationsEditorWidget(QtWidgets.QWidget):
    """
    Reusable editor widget for one :class:`LineLocations` object.
    """

    __slots__ = ("ui", "_table_model")

    def __init__(self,
                 line_locations: LineLocations,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the editor widget.

        :param line_locations: Initial value copied into the widget.
        :param parent: Optional Qt parent.
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_LineLocationsEditorWidget()
        self.ui.setupUi(self)

        self._table_model: LineLocationsTableModel = LineLocationsTableModel(
            line_locations=line_locations,
            parent=self.ui.tableView,
        )

        self.ui.tableView.setModel(self._table_model)
        self.ui.tableView.setAlternatingRowColors(True)
        self.ui.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ui.tableView.setItemDelegateForColumn(0, IntDelegate(self.ui.tableView))
        self.ui.tableView.setItemDelegateForColumn(1, FloatDelegate(self.ui.tableView, decimals=8))
        self.ui.tableView.setItemDelegateForColumn(2, FloatDelegate(self.ui.tableView, decimals=8))
        self.ui.tableView.setItemDelegateForColumn(3, FloatDelegate(self.ui.tableView, decimals=6))
        self.ui.tableView.setItemDelegateForColumn(4, TextDelegate(self.ui.tableView))

        self.ui.addButton.clicked.connect(self._on_add_clicked)
        self.ui.removeButton.clicked.connect(self._on_remove_clicked)
        self.ui.importButton.clicked.connect(self.import_csv)
        self.ui.exportButton.clicked.connect(self.export_csv)
        self.ui.copyButton.clicked.connect(self.copy_selection_to_clipboard)
        self.ui.pasteButton.clicked.connect(self.paste_from_clipboard)

        copy_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Copy, self)
        paste_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Paste, self)
        copy_shortcut.activated.connect(self.copy_selection_to_clipboard)
        paste_shortcut.activated.connect(self.paste_from_clipboard)

    def get_value(self) -> LineLocations:
        """
        Return the edited value.

        :return: Edited ``LineLocations``.
        """
        return self._table_model.to_line_locations()

    def set_value(self, line_locations: LineLocations) -> None:
        """
        Replace the current edited state with one source value.

        :param line_locations: New source value.
        """
        self._table_model.load_from_line_locations(line_locations=line_locations)

    def _on_add_clicked(self) -> None:
        """
        Append one new default location row.
        """
        self._table_model.add_empty_row()

    def _on_remove_clicked(self) -> None:
        """
        Remove the currently selected rows.
        """
        selection_model: QtCore.QItemSelectionModel | None = self.ui.tableView.selectionModel()
        selected_rows: list[int] = list()

        if selection_model is not None:
            model_index: QtCore.QModelIndex
            for model_index in selection_model.selectedRows():
                selected_rows.append(model_index.row())
        else:
            pass

        self._table_model.remove_rows(row_indices=selected_rows)

    def import_csv(self) -> None:
        """
        Import line-location rows from one CSV file.
        """
        file_name: str
        selected_filter: str
        file_name, selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import coordinates",
            "",
            "CSV files (*.csv);;Text files (*.txt);;All files (*)",
        )
        _ = selected_filter

        if len(file_name) > 0:
            try:
                with open(file_name, "r", encoding="utf-8") as file_pointer:
                    file_text: str = file_pointer.read()
                parsed_rows: list[list[object]] = parse_line_locations_text(text=file_text)
                self._table_model.load_rows(rows=parsed_rows)
            except (OSError, ValueError) as exception:
                QtWidgets.QMessageBox.warning(self, "Locations", str(exception))
        else:
            pass

    def export_csv(self) -> None:
        """
        Export the current line-location rows to one CSV file.
        """
        file_name: str
        selected_filter: str
        file_name, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export coordinates",
            "line_locations.csv",
            "CSV files (*.csv);;All files (*)",
        )
        _ = selected_filter

        if len(file_name) > 0:
            try:
                csv_text: str = build_line_locations_csv_text(line_locations=self.get_value())
                with open(file_name, "w", encoding="utf-8", newline="") as file_pointer:
                    file_pointer.write(csv_text)
            except OSError as exception:
                QtWidgets.QMessageBox.warning(self, "Locations", str(exception))
        else:
            pass

    def copy_selection_to_clipboard(self) -> None:
        """
        Copy the current selected rows to the clipboard as CSV-like tabular text.
        """
        selection_model: QtCore.QItemSelectionModel | None = self.ui.tableView.selectionModel()
        selected_rows: list[int] = list()

        if selection_model is not None:
            model_index: QtCore.QModelIndex
            for model_index in selection_model.selectedRows():
                selected_rows.append(model_index.row())
        else:
            pass

        if len(selected_rows) == 0:
            selected_rows = list(range(self._table_model.rowCount()))
        else:
            pass

        clipboard_rows: list[list[object]] = list()
        row_index: int
        for row_index in sorted(selected_rows):
            row_values: list[object] = list()
            column_index: int
            for column_index in range(self._table_model.columnCount()):
                model_index = self._table_model.index(row_index, column_index)
                row_values.append(self._table_model.data(model_index, int(QtCore.Qt.ItemDataRole.EditRole)))
            clipboard_rows.append(row_values)

        csv_text_io: io.StringIO = io.StringIO()
        csv_writer = csv.writer(csv_text_io, delimiter="\t", lineterminator="\n")
        csv_writer.writerow(["sequence", "latitude", "longitude", "altitude", "idtag"])
        csv_writer.writerows(clipboard_rows)
        QtWidgets.QApplication.clipboard().setText(csv_text_io.getvalue())

    def paste_from_clipboard(self) -> None:
        """
        Replace the current rows with the clipboard tabular data.
        """
        clipboard_text: str = QtWidgets.QApplication.clipboard().text()

        if len(clipboard_text.strip()) > 0:
            try:
                parsed_rows: list[list[object]] = parse_line_locations_text(text=clipboard_text)
                self._table_model.load_rows(rows=parsed_rows)
            except ValueError as exception:
                QtWidgets.QMessageBox.warning(self, "Locations", str(exception))
        else:
            pass


def build_line_locations_csv_text(line_locations: LineLocations) -> str:
    """
    Build CSV text from one ``LineLocations`` object.

    :param line_locations: Source value.
    :return: CSV text with one header row.
    """
    text_io: io.StringIO = io.StringIO()
    csv_writer = csv.writer(text_io, delimiter=",", lineterminator="\n")
    csv_writer.writerow(["sequence", "latitude", "longitude", "altitude", "idtag"])

    location: LineLocation
    for location in line_locations.get_locations():
        csv_writer.writerow([
            int(location.seq),
            float(location.lat),
            float(location.long),
            float(location.alt),
            str(location.idtag),
        ])

    return text_io.getvalue()


def parse_line_locations_text(text: str) -> list[list[object]]:
    """
    Parse CSV or tabular coordinate text into line-location rows.

    Supported layouts are:
    ``latitude,longitude``,
    ``latitude,longitude,altitude``,
    ``sequence,latitude,longitude,altitude``,
    ``latitude,longitude,altitude,idtag``,
    ``sequence,latitude,longitude,altitude,idtag``.
    A header row using those field names is also supported.

    :param text: Input text.
    :return: Parsed rows in internal table-column order.
    :raises ValueError: If the text cannot be interpreted.
    """
    stripped_lines: list[str] = [line for line in text.splitlines() if len(line.strip()) > 0]
    if len(stripped_lines) == 0:
        raise ValueError("No coordinate rows were found")
    else:
        pass

    dialect = csv.excel_tab if "\t" in text and "," not in text else csv.excel
    csv_reader = csv.reader(io.StringIO("\n".join(stripped_lines)), dialect=dialect)
    raw_rows: list[list[str]] = [list(row) for row in csv_reader if len(row) > 0]

    if len(raw_rows) == 0:
        raise ValueError("No coordinate rows were found")
    else:
        pass

    normalized_header: list[str] = [cell.strip().lower() for cell in raw_rows[0]]
    canonical_headers: set[str] = {"sequence", "latitude", "longitude", "altitude", "idtag"}
    data_rows: list[list[str]]

    if len(normalized_header) > 0 and all(cell in canonical_headers for cell in normalized_header):
        data_rows = raw_rows[1:]
    else:
        data_rows = raw_rows

    parsed_rows: list[list[object]] = list()
    raw_row: list[str]
    for raw_row in data_rows:
        stripped_row: list[str] = [cell.strip() for cell in raw_row]
        if len(stripped_row) >= 2:
            parsed_rows.append(_parse_line_locations_row(row=stripped_row, default_sequence=len(parsed_rows)))
        else:
            raise ValueError("Each coordinate row must have at least latitude and longitude")

    if len(parsed_rows) == 0:
        raise ValueError("No coordinate rows were found")
    else:
        pass

    row_index: int
    for row_index in range(len(parsed_rows)):
        parsed_rows[row_index][0] = row_index

    return parsed_rows


def _parse_line_locations_row(row: list[str], default_sequence: int) -> list[object]:
    """
    Parse one raw coordinate row.

    :param row: Raw string cells.
    :param default_sequence: Fallback sequence index.
    :return: Parsed row values in internal table-column order.
    :raises ValueError: If the row shape is unsupported.
    """
    if len(row) == 2:
        return [default_sequence, float(row[0]), float(row[1]), 0.0, ""]
    elif len(row) == 3:
        return [default_sequence, float(row[0]), float(row[1]), float(row[2]), ""]
    elif len(row) == 4:
        try:
            sequence_value: int = int(float(row[0]))
            return [sequence_value, float(row[1]), float(row[2]), float(row[3]), ""]
        except ValueError:
            return [default_sequence, float(row[0]), float(row[1]), float(row[2]), str(row[3])]
    elif len(row) >= 5:
        return [int(float(row[0])), float(row[1]), float(row[2]), float(row[3]), str(row[4])]
    else:
        raise ValueError("Each coordinate row must have between 2 and 5 columns")
