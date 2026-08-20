# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import re
from typing import Sequence

from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets


def sort_pair_by_x(point: tuple[float, float] | tuple[float, int]) -> float:
    """Return the first coordinate used to sort one lookup-table pair.

    :param point: Lookup-table value/index pair.
    :return: First coordinate as a floating-point sorting key.
    """
    return float(point[0])


def build_sorted_axis_indexes(axis_values: Sequence[float]) -> list[int]:
    """Return the stable sorted index order for one lookup-table axis.

    :param axis_values: Axis values to sort.
    :return: Sorted index list.
    """
    indexed_values: list[tuple[float, int]] = list()
    value_index: int

    for value_index in range(len(axis_values)):
        indexed_values.append((float(axis_values[value_index]), value_index))

    indexed_values.sort(key=sort_pair_by_x)
    return list(item[1] for item in indexed_values)


def _copy_selected_table_range_to_clipboard(table_widget: QtWidgets.QTableWidget) -> None:
    """
    Copy the currently selected table range to the clipboard.

    :param table_widget: Source table widget.
    :return: None.
    """
    selected_indexes: list[QtCore.QModelIndex] = list(table_widget.selectionModel().selectedIndexes())

    if len(selected_indexes) == 0:
        return
    else:
        pass

    min_row: int = min(index.row() for index in selected_indexes)
    max_row: int = max(index.row() for index in selected_indexes)
    min_col: int = min(index.column() for index in selected_indexes)
    max_col: int = max(index.column() for index in selected_indexes)
    lines: list[str] = list()
    row_index: int
    col_index: int

    for row_index in range(min_row, max_row + 1):
        row_cells: list[str] = list()
        for col_index in range(min_col, max_col + 1):
            item: QtWidgets.QTableWidgetItem | None = table_widget.item(row_index, col_index)

            if item is None:
                row_cells.append("")
            else:
                row_cells.append(item.text())

        lines.append("\t".join(row_cells))

    QtWidgets.QApplication.clipboard().setText("\n".join(lines))


def _clear_selected_table_cells(table_widget: QtWidgets.QTableWidget) -> None:
    """
    Clear the currently selected cells in place.

    :param table_widget: Target table widget.
    :return: None.
    """
    selected_indexes: list[QtCore.QModelIndex] = list(table_widget.selectionModel().selectedIndexes())
    index: QtCore.QModelIndex

    for index in selected_indexes:
        item: QtWidgets.QTableWidgetItem | None = table_widget.item(index.row(), index.column())

        if item is not None:
            item.setText("")
        else:
            pass


def _parse_clipboard_grid(clipboard_text: str) -> list[list[str]]:
    """
    Parse one clipboard payload into a rectangular text grid.

    :param clipboard_text: Clipboard text.
    :return: Parsed grid.
    :raises ValueError: If the clipboard has no usable rows.
    """
    parsed_rows: list[list[str]] = list()
    line_text: str

    for line_text in clipboard_text.splitlines():
        if len(line_text.strip()) == 0:
            pass
        else:
            if "\t" in line_text:
                parsed_rows.append([part.strip() for part in line_text.rstrip("\r").split("\t")])
            else:
                parsed_rows.append([part.strip() for part in re.split(r"[;,]+", line_text.strip())])

    if len(parsed_rows) == 0:
        raise ValueError("Clipboard does not contain table rows")
    else:
        return parsed_rows


def _get_selection_anchor(table_widget: QtWidgets.QTableWidget, default_row: int, default_col: int) -> tuple[int, int]:
    """
    Return the top-left anchor used for spreadsheet-style pasting.

    :param table_widget: Target table widget.
    :param default_row: Fallback row.
    :param default_col: Fallback column.
    :return: Anchor `(row, column)`.
    """
    selected_indexes: list[QtCore.QModelIndex] = list(table_widget.selectionModel().selectedIndexes())

    if len(selected_indexes) == 0:
        current_row: int = table_widget.currentRow()
        current_col: int = table_widget.currentColumn()

        if current_row >= 0 and current_col >= 0:
            return current_row, current_col
        else:
            return default_row, default_col
    else:
        return min(index.row() for index in selected_indexes), min(index.column() for index in selected_indexes)


class LookupArrayLinearDialog(QtWidgets.QDialog):
    """
    Modal dialog used to capture a one-dimensional lookup table.
    """

    __slots__ = (
        "_table_widget",
        "_x_points",
        "_y_points",
        "_shortcuts",
        "_x_label",
        "_y_label",
        "_preview_title",
        "_preview_dialog",
    )

    def __init__(self,
                 block_label: str,
                 initial_points: Sequence[tuple[float, float]] | None = None,
                 parent: QtWidgets.QWidget | None = None,
                 x_label: str = "X",
                 y_label: str = "Y",
                 preview_enabled: bool = False,
                 preview_title: str | None = None) -> None:
        """
        Build the modal dialog.

        :param block_label: Visible lookup-table label.
        :param initial_points: Optional initial `(x, y)` rows.
        :param parent: Optional Qt parent.
        :param x_label: Visible label for the first axis.
        :param y_label: Visible label for the second axis.
        :param preview_enabled: Whether to show one plot-preview button.
        :param preview_title: Optional plot-preview window title.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure Lookup Table")
        self.resize(560, 420)

        self._x_points: list[float] = list()
        self._y_points: list[float] = list()
        self._shortcuts: list[QtGui.QShortcut] = list()
        self._x_label: str = str(x_label)
        self._y_label: str = str(y_label)
        self._preview_title: str = preview_title if preview_title is not None else f"{block_label} Preview"
        self._preview_dialog: QtWidgets.QDialog | None = None

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        description_label: QtWidgets.QLabel = QtWidgets.QLabel(
            f"Enter the lookup table points for '{block_label}'.",
            self,
        )
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        self._table_widget = QtWidgets.QTableWidget(self)
        self._table_widget.setColumnCount(2)
        self._table_widget.setHorizontalHeaderLabels(list((self._x_label, self._y_label,)))
        self._table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self._table_widget.horizontalHeader().sectionClicked.connect(self.select_column_by_header)
        self._table_widget.verticalHeader().setVisible(False)
        self._table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)
        self._table_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table_widget.installEventFilter(self)
        main_layout.addWidget(self._table_widget)

        buttons_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        add_row_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Add Row", self)
        remove_row_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Remove Selected", self)
        sort_button: QtWidgets.QPushButton = QtWidgets.QPushButton(f"Sort by {self._x_label}", self)
        paste_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Paste", self)
        preview_button: QtWidgets.QPushButton | None = None
        buttons_layout.addWidget(add_row_button)
        buttons_layout.addWidget(remove_row_button)
        buttons_layout.addWidget(sort_button)
        buttons_layout.addWidget(paste_button)
        if preview_enabled:
            preview_button = QtWidgets.QPushButton("Preview Curve", self)
            buttons_layout.addWidget(preview_button)
        else:
            pass
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        dialog_buttons: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        main_layout.addWidget(dialog_buttons)

        add_row_button.clicked.connect(self.add_empty_row)
        remove_row_button.clicked.connect(self.remove_selected_rows)
        sort_button.clicked.connect(self.sort_rows_by_x)
        paste_button.clicked.connect(self.paste_from_clipboard)
        if preview_button is not None:
            preview_button.clicked.connect(self.show_plot_preview)
        else:
            pass
        dialog_buttons.accepted.connect(self.accept_dialog)
        dialog_buttons.rejected.connect(self.reject)

        self._install_shortcuts()

        self._populate_initial_rows(initial_points)

    def _install_shortcuts(self) -> None:
        """
        Install dialog-level shortcuts that remain active while the table has focus.

        :return: None.
        """
        copy_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Copy, self)
        copy_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(self.copy_selection_to_clipboard)
        self._shortcuts.append(copy_shortcut)

        paste_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Paste, self)
        paste_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        paste_shortcut.activated.connect(self.paste_from_clipboard)
        self._shortcuts.append(paste_shortcut)

        delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete), self)
        delete_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        delete_shortcut.activated.connect(self.delete_selection)
        self._shortcuts.append(delete_shortcut)

    def select_column_by_header(self, section_index: int) -> None:
        """
        Select one complete data column when the user clicks its header.

        :param section_index: Header section index.
        :return: None.
        """
        last_row: int = self._table_widget.rowCount() - 1

        if last_row >= 0:
            self._table_widget.clearSelection()
            selection = QtWidgets.QTableWidgetSelectionRange(0, section_index, last_row, section_index)
            self._table_widget.setRangeSelected(selection, True)
        else:
            pass

    def copy_selection_to_clipboard(self) -> None:
        """
        Copy the current selection to the clipboard.

        :return: None.
        """
        _copy_selected_table_range_to_clipboard(self._table_widget)

    def _populate_initial_rows(self, initial_points: Sequence[tuple[float, float]] | None) -> None:
        """
        Populate the initial grid state.

        :param initial_points: Optional initial rows.
        :return: None.
        """
        points: Sequence[tuple[float, float]]
        point: tuple[float, float]

        if initial_points is None:
            points = ((0.0, 0.0), (1.0, 10.0), (2.0, 20.0))
        else:
            points = initial_points

        for point in points:
            self.add_row_with_values(point[0], point[1])

    def add_empty_row(self) -> None:
        """
        Add one empty row at the end of the table.

        :return: None.
        """
        self.add_row_with_values(0.0, 0.0)

    def add_row_with_values(self, x_value: float, y_value: float) -> None:
        """
        Add one row initialized with explicit values.

        :param x_value: Initial x value.
        :param y_value: Initial y value.
        :return: None.
        """
        row_index: int = self._table_widget.rowCount()
        self._table_widget.insertRow(row_index)
        self._table_widget.setItem(row_index, 0, QtWidgets.QTableWidgetItem(str(float(x_value))))
        self._table_widget.setItem(row_index, 1, QtWidgets.QTableWidgetItem(str(float(y_value))))

    def remove_selected_rows(self) -> None:
        """
        Remove all currently selected rows.

        :return: None.
        """
        selected_indexes: list[QtCore.QModelIndex] = list(self._table_widget.selectionModel().selectedRows())
        row_index: int
        row_indexes: list[int] = list(index.row() for index in selected_indexes)

        for row_index in sorted(row_indexes, reverse=True):
            self._table_widget.removeRow(row_index)

    def sort_rows_by_x(self) -> None:
        """
        Sort the current rows by their x coordinate.

        :return: None.
        """
        x_points: list[float]
        y_points: list[float]

        try:
            x_points, y_points = self._read_points_from_table()
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Lookup Table", str(exc))
            return

        pairs: list[tuple[float, float]] = list(zip(x_points, y_points))
        pairs.sort(key=sort_pair_by_x)
        self._replace_table_points(pairs)

    def paste_from_clipboard(self) -> None:
        """
        Paste the clipboard grid into the current selection like a spreadsheet.

        :return: None.
        """
        clipboard: QtWidgets.QClipboard = QtWidgets.QApplication.clipboard()
        clipboard_text: str = clipboard.text().strip()
        parsed_rows: list[list[str]]
        anchor_row: int
        anchor_col: int
        row_offset: int
        col_offset: int
        target_row: int
        target_col: int
        item: QtWidgets.QTableWidgetItem | None

        if len(clipboard_text) == 0:
            QtWidgets.QMessageBox.information(self, "Lookup Table", "Clipboard is empty.")
            return
        else:
            pass

        try:
            parsed_rows = _parse_clipboard_grid(clipboard_text)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Lookup Table", str(exc))
            return

        if max(len(row) for row in parsed_rows) <= 2:
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "Lookup Table", "Lookup table clipboard data can only have up to two columns.")
            return

        anchor_row, anchor_col = _get_selection_anchor(self._table_widget, 0, 0)

        while self._table_widget.rowCount() < anchor_row + len(parsed_rows):
            self.add_empty_row()

        for row_offset in range(len(parsed_rows)):
            for col_offset in range(len(parsed_rows[row_offset])):
                target_row = anchor_row + row_offset
                target_col = anchor_col + col_offset

                if target_col < self._table_widget.columnCount():
                    item = self._table_widget.item(target_row, target_col)
                    if item is None:
                        item = QtWidgets.QTableWidgetItem("")
                        self._table_widget.setItem(target_row, target_col, item)
                    else:
                        pass

                    item.setText(parsed_rows[row_offset][col_offset])
                else:
                    pass

    def delete_selection(self) -> None:
        """
        Delete the current selection using row-aware behavior.

        :return: None.
        """
        selected_ranges: list[QtWidgets.QTableWidgetSelectionRange] = list(self._table_widget.selectedRanges())
        selection_range: QtWidgets.QTableWidgetSelectionRange
        removes_rows: bool = False

        for selection_range in selected_ranges:
            if selection_range.leftColumn() == 0 and selection_range.rightColumn() == self._table_widget.columnCount() - 1:
                removes_rows = True
            else:
                pass

        if removes_rows:
            self.remove_selected_rows()
        else:
            _clear_selected_table_cells(self._table_widget)

    def accept_dialog(self) -> None:
        """
        Validate and accept the modal.

        :return: None.
        """
        try:
            x_points, y_points = self._read_points_from_table()
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Lookup Table", str(exc))
            return

        sorted_pairs: list[tuple[float, float]] = list(zip(x_points, y_points))
        sorted_pairs.sort(key=sort_pair_by_x)
        self._x_points = list(pair[0] for pair in sorted_pairs)
        self._y_points = list(pair[1] for pair in sorted_pairs)

        if len(self._x_points) < 2:
            QtWidgets.QMessageBox.warning(self, "Lookup Table", "Lookup tables require at least two points.")
            return
        else:
            pass

        for row_index in range(len(self._x_points) - 1):
            if self._x_points[row_index + 1] > self._x_points[row_index]:
                pass
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Lookup Table",
                    "Lookup table x values must be strictly increasing.",
                )
                return

        self.accept()

    def get_points(self) -> tuple[list[float], list[float]]:
        """
        Return the validated x and y vectors.

        :return: Tuple `(x_points, y_points)`.
        """
        return list(self._x_points), list(self._y_points)

    def _clear_preview_dialog_reference(self, destroyed_obj: QtCore.QObject | None = None) -> None:
        """
        Drop the stored preview-dialog reference after the window closes.

        :param destroyed_obj: Destroyed Qt object emitted by the signal.
        :return: None.
        """
        _unused_destroyed_obj: QtCore.QObject | None = destroyed_obj
        self._preview_dialog = None

    def show_plot_preview(self) -> None:
        """
        Render the current lookup-table rows in one external preview window.

        :return: None.
        """
        try:
            x_points, y_points = self._read_points_from_table()
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Lookup Table", str(exc))
            return

        pairs: list[tuple[float, float]] = list(zip(x_points, y_points))
        pairs.sort(key=sort_pair_by_x)

        if len(pairs) < 2:
            QtWidgets.QMessageBox.warning(self, "Lookup Table", "Lookup tables require at least two points.")
            return
        else:
            pass

        if self._preview_dialog is not None:
            self._preview_dialog.close()
        else:
            pass

        # The preview lives in a separate dialog so the user can keep editing the
        # lookup points while visually checking the resulting curve shape.
        preview_dialog: QtWidgets.QDialog = QtWidgets.QDialog(self)
        preview_dialog.setWindowTitle(self._preview_title)
        preview_dialog.resize(720, 440)
        preview_dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        preview_dialog.destroyed.connect(self._clear_preview_dialog_reference)

        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(preview_dialog)
        figure: Figure = Figure(figsize=(7, 4))
        axis: Axes = figure.add_subplot(111)
        canvas: FigureCanvas = FigureCanvas(figure)
        toolbar: NavigationToolbar = NavigationToolbar(canvas, preview_dialog)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        # The preview intentionally plots the sorted point sequence because the
        # effective lookup law always depends on the monotonic x-axis ordering.
        x_values: np.ndarray = np.asarray([pair[0] for pair in pairs], dtype=float)
        y_values: np.ndarray = np.asarray([pair[1] for pair in pairs], dtype=float)
        axis.plot(x_values, y_values, marker="o", color="tab:blue")
        axis.grid(True)
        axis.set_xlabel(self._x_label)
        axis.set_ylabel(self._y_label)
        axis.set_title(self._preview_title)
        figure.tight_layout()
        canvas.draw()

        self._preview_dialog = preview_dialog
        preview_dialog.show()
        preview_dialog.raise_()
        preview_dialog.activateWindow()

    def _read_points_from_table(self) -> tuple[list[float], list[float]]:
        """
        Read the current raw table cells as numeric vectors.

        :return: Tuple `(x_points, y_points)`.
        :raises ValueError: If any row is incomplete or non-numeric.
        """
        x_points: list[float] = list()
        y_points: list[float] = list()
        row_count: int = self._table_widget.rowCount()
        row_index: int

        for row_index in range(row_count):
            x_item: QtWidgets.QTableWidgetItem | None = self._table_widget.item(row_index, 0)
            y_item: QtWidgets.QTableWidgetItem | None = self._table_widget.item(row_index, 1)

            if x_item is None or y_item is None:
                raise ValueError(f"Row {row_index + 1} is incomplete")
            else:
                pass

            x_text: str = x_item.text().strip()
            y_text: str = y_item.text().strip()

            if len(x_text) == 0 or len(y_text) == 0:
                raise ValueError(f"Row {row_index + 1} is incomplete")
            else:
                pass

            try:
                x_points.append(float(x_text))
                y_points.append(float(y_text))
            except ValueError as exc:
                raise ValueError(f"Row {row_index + 1} contains non-numeric data") from exc

        return x_points, y_points

    def _replace_table_points(self, points: Sequence[tuple[float, float]]) -> None:
        """
        Replace the whole table with explicit point rows.

        :param points: New `(x, y)` rows.
        :return: None.
        """
        point: tuple[float, float]
        self._table_widget.setRowCount(0)

        for point in points:
            self.add_row_with_values(point[0], point[1])

    def _parse_points_from_text(self, clipboard_text: str) -> list[tuple[float, float]]:
        """
        Parse tabular clipboard text into lookup-table rows.

        :param clipboard_text: Clipboard text.
        :return: Parsed `(x, y)` rows.
        :raises ValueError: If the text cannot be parsed.
        """
        line_text: str
        parts: list[str]
        parsed_points: list[tuple[float, float]] = list()

        for line_text in clipboard_text.splitlines():
            stripped_line: str = line_text.strip()

            if len(stripped_line) == 0:
                pass
            else:
                parts = list(part.strip() for part in re.split(r"[\t,;]+", stripped_line) if len(part.strip()) > 0)

                if len(parts) < 2:
                    raise ValueError("Clipboard rows must contain at least two numeric columns")
                else:
                    pass

                try:
                    parsed_points.append((float(parts[0]), float(parts[1])))
                except ValueError as exc:
                    raise ValueError("Clipboard contains non-numeric lookup-table data") from exc

        if len(parsed_points) == 0:
            raise ValueError("Clipboard does not contain lookup-table rows")
        else:
            return parsed_points

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Forward unhandled key events to the base dialog.

        :param event: Incoming key event.
        :return: None.
        """
        super().keyPressEvent(event)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """
        Capture table shortcuts directly from the child widget.

        :param watched: Watched QObject.
        :param event: Qt event.
        :return: True when the event is handled here.
        """
        if watched is self._table_widget and event.type() == QtCore.QEvent.Type.KeyPress:
            key_event = event

            if isinstance(key_event, QtGui.QKeyEvent):
                if key_event.matches(QtGui.QKeySequence.StandardKey.Copy):
                    self.copy_selection_to_clipboard()
                    return True
                else:
                    pass

                if key_event.matches(QtGui.QKeySequence.StandardKey.Paste):
                    self.paste_from_clipboard()
                    return True
                else:
                    pass

                if key_event.key() == int(QtCore.Qt.Key.Key_Delete):
                    self.delete_selection()
                    return True
                else:
                    pass
            else:
                pass
        else:
            pass

        return super().eventFilter(watched, event)


class LookupMatrixLinearDialog(QtWidgets.QDialog):
    """
    Modal dialog used to capture one two-dimensional lookup table.
    """

    __slots__ = ("_table_widget", "_x_points", "_y_points", "_z_matrix", "_shortcuts")

    def __init__(self,
                 block_label: str,
                 initial_x_points: Sequence[float] | None = None,
                 initial_y_points: Sequence[float] | None = None,
                 initial_z_matrix: Sequence[Sequence[float]] | None = None,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the modal dialog.

        :param block_label: Visible lookup-table label.
        :param initial_x_points: Optional initial x-axis values.
        :param initial_y_points: Optional initial y-axis values.
        :param initial_z_matrix: Optional initial z matrix indexed as `[y][x]`.
        :param parent: Optional Qt parent.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure Lookup Matrix")
        self.resize(720, 520)

        self._x_points: list[float] = list()
        self._y_points: list[float] = list()
        self._z_matrix: list[list[float]] = list()
        self._shortcuts: list[QtGui.QShortcut] = list()

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        description_label: QtWidgets.QLabel = QtWidgets.QLabel(
            f"Enter the lookup matrix for '{block_label}'. Use the top row for X values, the first column for Y values, and the inner cells for Z values.",
            self,
        )
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        self._table_widget = QtWidgets.QTableWidget(self)
        self._table_widget.verticalHeader().setVisible(False)
        self._table_widget.horizontalHeader().setVisible(False)
        self._table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self._table_widget.cellPressed.connect(self.on_matrix_cell_pressed)
        self._table_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table_widget.installEventFilter(self)
        main_layout.addWidget(self._table_widget)

        buttons_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        add_x_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Add X", self)
        remove_x_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Remove X", self)
        add_y_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Add Y", self)
        remove_y_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Remove Y", self)
        sort_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Sort Axes", self)
        paste_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Paste", self)
        buttons_layout.addWidget(add_x_button)
        buttons_layout.addWidget(remove_x_button)
        buttons_layout.addWidget(add_y_button)
        buttons_layout.addWidget(remove_y_button)
        buttons_layout.addWidget(sort_button)
        buttons_layout.addWidget(paste_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        dialog_buttons: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        main_layout.addWidget(dialog_buttons)

        add_x_button.clicked.connect(self.add_x_column)
        remove_x_button.clicked.connect(self.remove_x_column)
        add_y_button.clicked.connect(self.add_y_row)
        remove_y_button.clicked.connect(self.remove_y_row)
        sort_button.clicked.connect(self.sort_axes)
        paste_button.clicked.connect(self.paste_from_clipboard)
        dialog_buttons.accepted.connect(self.accept_dialog)
        dialog_buttons.rejected.connect(self.reject)

        self._install_shortcuts()

        self._populate_initial_grid(initial_x_points, initial_y_points, initial_z_matrix)

    def _install_shortcuts(self) -> None:
        """
        Install dialog-level shortcuts that remain active while the table has focus.

        :return: None.
        """
        copy_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Copy, self)
        copy_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(self.copy_selection_to_clipboard)
        self._shortcuts.append(copy_shortcut)

        paste_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Paste, self)
        paste_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        paste_shortcut.activated.connect(self.paste_from_clipboard)
        self._shortcuts.append(paste_shortcut)

        delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete), self)
        delete_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        delete_shortcut.activated.connect(self.delete_selection)
        self._shortcuts.append(delete_shortcut)

    def copy_selection_to_clipboard(self) -> None:
        """
        Copy the current selection to the clipboard.

        :return: None.
        """
        _copy_selected_table_range_to_clipboard(self._table_widget)

    def on_matrix_cell_pressed(self, row_index: int, column_index: int) -> None:
        """
        Convert axis-cell clicks into full row or column selections.

        :param row_index: Pressed row index.
        :param column_index: Pressed column index.
        :return: None.
        """
        if row_index == 0 and column_index > 0:
            self._table_widget.clearSelection()
            selection = QtWidgets.QTableWidgetSelectionRange(0, column_index, self._table_widget.rowCount() - 1, column_index)
            self._table_widget.setRangeSelected(selection, True)
        else:
            if column_index == 0 and row_index > 0:
                self._table_widget.clearSelection()
                selection = QtWidgets.QTableWidgetSelectionRange(row_index, 0, row_index, self._table_widget.columnCount() - 1)
                self._table_widget.setRangeSelected(selection, True)
            else:
                pass

    def _populate_initial_grid(self,
                               initial_x_points: Sequence[float] | None,
                               initial_y_points: Sequence[float] | None,
                               initial_z_matrix: Sequence[Sequence[float]] | None) -> None:
        """
        Populate the initial matrix grid.

        :param initial_x_points: Optional initial x-axis values.
        :param initial_y_points: Optional initial y-axis values.
        :param initial_z_matrix: Optional initial z matrix.
        :return: None.
        """
        x_points: Sequence[float]
        y_points: Sequence[float]
        z_matrix: Sequence[Sequence[float]]

        if initial_x_points is None:
            x_points = (0.0, 1.0)
        else:
            x_points = initial_x_points

        if initial_y_points is None:
            y_points = (0.0, 2.0)
        else:
            y_points = initial_y_points

        if initial_z_matrix is None:
            z_matrix = ((0.0, 10.0), (20.0, 30.0))
        else:
            z_matrix = initial_z_matrix

        self._replace_matrix_data(x_points=list(x_points), y_points=list(y_points), z_matrix=[list(row) for row in z_matrix])

    def add_x_column(self) -> None:
        """
        Append one x-axis column initialized with zeros.

        :return: None.
        """
        x_points: list[float]
        y_points: list[float]
        z_matrix: list[list[float]]

        x_points, y_points, z_matrix = self._read_matrix_from_table()
        x_points.append(0.0)
        row_index: int
        for row_index in range(len(z_matrix)):
            z_matrix[row_index].append(0.0)

        self._replace_matrix_data(x_points=x_points, y_points=y_points, z_matrix=z_matrix)

    def remove_x_column(self) -> None:
        """
        Remove the last x-axis column when possible.

        :return: None.
        """
        x_points: list[float]
        y_points: list[float]
        z_matrix: list[list[float]]
        row_index: int

        x_points, y_points, z_matrix = self._read_matrix_from_table()

        if len(x_points) > 2:
            x_points.pop()
            for row_index in range(len(z_matrix)):
                z_matrix[row_index].pop()
            self._replace_matrix_data(x_points=x_points, y_points=y_points, z_matrix=z_matrix)
        else:
            QtWidgets.QMessageBox.information(self, "Lookup Matrix", "At least two X points are required.")

    def remove_selected_x_columns(self) -> bool:
        """
        Remove the selected X columns when complete axis columns are selected.

        :return: None.
        """
        selected_ranges: list[QtWidgets.QTableWidgetSelectionRange] = list(self._table_widget.selectedRanges())
        selected_x_indexes: set[int] = set()
        selection_range: QtWidgets.QTableWidgetSelectionRange
        x_points: list[float]
        y_points: list[float]
        z_matrix: list[list[float]]
        kept_x_points: list[float] = list()
        kept_z_matrix: list[list[float]] = list()
        x_index: int
        y_index: int

        for selection_range in selected_ranges:
            if selection_range.topRow() == 0 and selection_range.bottomRow() == self._table_widget.rowCount() - 1:
                for x_index in range(selection_range.leftColumn(), selection_range.rightColumn() + 1):
                    if x_index > 0:
                        selected_x_indexes.add(x_index - 1)
                    else:
                        pass
            else:
                pass

        if len(selected_x_indexes) == 0:
            return False
        else:
            pass

        x_points, y_points, z_matrix = self._read_matrix_from_table()

        if len(x_points) - len(selected_x_indexes) >= 2:
            pass
        else:
            return False

        for x_index in range(len(x_points)):
            if x_index not in selected_x_indexes:
                kept_x_points.append(x_points[x_index])
            else:
                pass

        for y_index in range(len(y_points)):
            kept_row: list[float] = list()
            for x_index in range(len(x_points)):
                if x_index not in selected_x_indexes:
                    kept_row.append(z_matrix[y_index][x_index])
                else:
                    pass
            kept_z_matrix.append(kept_row)

        self._replace_matrix_data(x_points=kept_x_points, y_points=y_points, z_matrix=kept_z_matrix)
        return True

    def add_y_row(self) -> None:
        """
        Append one y-axis row initialized with zeros.

        :return: None.
        """
        x_points: list[float]
        y_points: list[float]
        z_matrix: list[list[float]]

        x_points, y_points, z_matrix = self._read_matrix_from_table()
        y_points.append(0.0)
        z_matrix.append(list(0.0 for _ in range(len(x_points))))
        self._replace_matrix_data(x_points=x_points, y_points=y_points, z_matrix=z_matrix)

    def remove_y_row(self) -> None:
        """
        Remove the last y-axis row when possible.

        :return: None.
        """
        x_points: list[float]
        y_points: list[float]
        z_matrix: list[list[float]]

        x_points, y_points, z_matrix = self._read_matrix_from_table()

        if len(y_points) > 2:
            y_points.pop()
            z_matrix.pop()
            self._replace_matrix_data(x_points=x_points, y_points=y_points, z_matrix=z_matrix)
        else:
            QtWidgets.QMessageBox.information(self, "Lookup Matrix", "At least two Y points are required.")

    def remove_selected_y_rows(self) -> bool:
        """
        Remove the selected Y rows when complete axis rows are selected.

        :return: None.
        """
        selected_ranges: list[QtWidgets.QTableWidgetSelectionRange] = list(self._table_widget.selectedRanges())
        selected_y_indexes: set[int] = set()
        selection_range: QtWidgets.QTableWidgetSelectionRange
        x_points: list[float]
        y_points: list[float]
        z_matrix: list[list[float]]
        kept_y_points: list[float] = list()
        kept_z_matrix: list[list[float]] = list()
        row_index: int

        for selection_range in selected_ranges:
            if selection_range.leftColumn() == 0 and selection_range.rightColumn() == self._table_widget.columnCount() - 1:
                for row_index in range(selection_range.topRow(), selection_range.bottomRow() + 1):
                    if row_index > 0:
                        selected_y_indexes.add(row_index - 1)
                    else:
                        pass
            else:
                pass

        if len(selected_y_indexes) == 0:
            return False
        else:
            pass

        x_points, y_points, z_matrix = self._read_matrix_from_table()

        if len(y_points) - len(selected_y_indexes) >= 2:
            pass
        else:
            return False

        for row_index in range(len(y_points)):
            if row_index not in selected_y_indexes:
                kept_y_points.append(y_points[row_index])
                kept_z_matrix.append(z_matrix[row_index])
            else:
                pass

        self._replace_matrix_data(x_points=x_points, y_points=kept_y_points, z_matrix=kept_z_matrix)
        return True

    def delete_selection(self) -> None:
        """
        Delete the current selection using the most specific matrix operation.

        Full selected data rows remove Y rows, full selected columns remove X columns,
        and partial selections clear only the selected cells.

        :return: None.
        """
        selected_ranges: list[QtWidgets.QTableWidgetSelectionRange] = list(self._table_widget.selectedRanges())
        selection_range: QtWidgets.QTableWidgetSelectionRange
        removes_y_rows: bool = False
        removes_x_columns: bool = False

        for selection_range in selected_ranges:
            if selection_range.leftColumn() == 0 and selection_range.rightColumn() == self._table_widget.columnCount() - 1:
                if selection_range.bottomRow() >= 1:
                    removes_y_rows = True
                else:
                    pass
            else:
                pass

            if selection_range.topRow() == 0 and selection_range.bottomRow() == self._table_widget.rowCount() - 1:
                if selection_range.rightColumn() >= 1:
                    removes_x_columns = True
                else:
                    pass
            else:
                pass

        if removes_y_rows:
            self.remove_selected_y_rows()
        else:
            if removes_x_columns:
                self.remove_selected_x_columns()
            else:
                _clear_selected_table_cells(self._table_widget)

    def sort_axes(self) -> None:
        """
        Sort both axes ascending and reorder the matrix accordingly.

        :return: None.
        """
        x_points: list[float]
        y_points: list[float]
        z_matrix: list[list[float]]
        sorted_x_indexes: list[int]
        sorted_y_indexes: list[int]
        reordered_matrix: list[list[float]] = list()
        y_sorted_index: int
        x_sorted_index: int

        try:
            x_points, y_points, z_matrix = self._read_matrix_from_table()
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Lookup Matrix", str(exc))
            return

        sorted_x_indexes = build_sorted_axis_indexes(x_points)
        sorted_y_indexes = build_sorted_axis_indexes(y_points)

        for y_sorted_index in sorted_y_indexes:
            reordered_row: list[float] = list()
            for x_sorted_index in sorted_x_indexes:
                reordered_row.append(z_matrix[y_sorted_index][x_sorted_index])
            reordered_matrix.append(reordered_row)

        self._replace_matrix_data(
            x_points=list(x_points[index] for index in sorted_x_indexes),
            y_points=list(y_points[index] for index in sorted_y_indexes),
            z_matrix=reordered_matrix,
        )

    def paste_from_clipboard(self) -> None:
        """
        Paste the clipboard grid into the current selection like a spreadsheet.

        :return: None.
        """
        clipboard: QtWidgets.QClipboard = QtWidgets.QApplication.clipboard()
        clipboard_text: str = clipboard.text()
        parsed_rows: list[list[str]]
        anchor_row: int
        anchor_col: int
        row_offset: int
        col_offset: int
        target_row: int
        target_col: int
        item: QtWidgets.QTableWidgetItem | None

        if len(clipboard_text.strip()) == 0:
            QtWidgets.QMessageBox.information(self, "Lookup Matrix", "Clipboard is empty.")
            return
        else:
            pass

        try:
            parsed_rows = _parse_clipboard_grid(clipboard_text)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Lookup Matrix", str(exc))
            return

        anchor_row, anchor_col = _get_selection_anchor(self._table_widget, 0, 0)

        if anchor_row == 0 and anchor_col == 0:
            row_count: int = len(parsed_rows)
            col_count: int = max(len(row) for row in parsed_rows)
            self._table_widget.setRowCount(row_count)
            self._table_widget.setColumnCount(col_count)
        else:
            required_rows: int = anchor_row + len(parsed_rows)
            required_cols: int = anchor_col + max(len(row) for row in parsed_rows)

            while self._table_widget.rowCount() < required_rows:
                self.add_y_row()

            while self._table_widget.columnCount() < required_cols:
                self.add_x_column()

        for row_offset in range(len(parsed_rows)):
            for col_offset in range(len(parsed_rows[row_offset])):
                target_row = anchor_row + row_offset
                target_col = anchor_col + col_offset
                item = self._table_widget.item(target_row, target_col)

                if item is None:
                    item = QtWidgets.QTableWidgetItem("")
                    self._table_widget.setItem(target_row, target_col, item)
                else:
                    pass

                item.setText(parsed_rows[row_offset][col_offset])

    def accept_dialog(self) -> None:
        """
        Validate and accept the modal.

        :return: None.
        """
        x_points: list[float]
        y_points: list[float]
        z_matrix: list[list[float]]
        point_index: int

        try:
            x_points, y_points, z_matrix = self._read_matrix_from_table()
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Lookup Matrix", str(exc))
            return

        if len(x_points) >= 2 and len(y_points) >= 2:
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "Lookup Matrix", "Lookup matrix requires at least two X points and two Y points.")
            return

        for point_index in range(len(x_points) - 1):
            if x_points[point_index + 1] > x_points[point_index]:
                pass
            else:
                QtWidgets.QMessageBox.warning(self, "Lookup Matrix", "X axis values must be strictly increasing.")
                return

        for point_index in range(len(y_points) - 1):
            if y_points[point_index + 1] > y_points[point_index]:
                pass
            else:
                QtWidgets.QMessageBox.warning(self, "Lookup Matrix", "Y axis values must be strictly increasing.")
                return

        self._x_points = x_points
        self._y_points = y_points
        self._z_matrix = z_matrix
        self.accept()

    def get_matrix_data(self) -> tuple[list[float], list[float], list[list[float]]]:
        """
        Return the validated matrix data.

        :return: Tuple `(x_points, y_points, z_matrix)`.
        """
        return list(self._x_points), list(self._y_points), list(list(row) for row in self._z_matrix)

    def _replace_matrix_data(self,
                             x_points: list[float],
                             y_points: list[float],
                             z_matrix: list[list[float]]) -> None:
        """
        Replace the whole visible grid with explicit matrix data.

        :param x_points: X-axis values.
        :param y_points: Y-axis values.
        :param z_matrix: Matrix values indexed as `[y][x]`.
        :return: None.
        """
        x_index: int
        y_index: int

        self._table_widget.setRowCount(len(y_points) + 1)
        self._table_widget.setColumnCount(len(x_points) + 1)
        self._table_widget.setItem(0, 0, QtWidgets.QTableWidgetItem(""))

        for x_index in range(len(x_points)):
            self._table_widget.setItem(0, x_index + 1, QtWidgets.QTableWidgetItem(str(float(x_points[x_index]))))

        for y_index in range(len(y_points)):
            self._table_widget.setItem(y_index + 1, 0, QtWidgets.QTableWidgetItem(str(float(y_points[y_index]))))

            for x_index in range(len(x_points)):
                self._table_widget.setItem(
                    y_index + 1,
                    x_index + 1,
                    QtWidgets.QTableWidgetItem(str(float(z_matrix[y_index][x_index]))),
                )

    def _read_matrix_from_table(self) -> tuple[list[float], list[float], list[list[float]]]:
        """
        Read the current matrix grid as numeric axes and matrix values.

        :return: Tuple `(x_points, y_points, z_matrix)`.
        :raises ValueError: If the grid contains incomplete or non-numeric data.
        """
        x_points: list[float] = list()
        y_points: list[float] = list()
        z_matrix: list[list[float]] = list()
        x_index: int
        y_index: int
        x_item: QtWidgets.QTableWidgetItem | None
        y_item: QtWidgets.QTableWidgetItem | None
        z_item: QtWidgets.QTableWidgetItem | None

        for x_index in range(1, self._table_widget.columnCount()):
            x_item = self._table_widget.item(0, x_index)
            if x_item is None or len(x_item.text().strip()) == 0:
                raise ValueError(f"X axis cell {x_index} is incomplete")
            else:
                pass

            try:
                x_points.append(float(x_item.text().strip()))
            except ValueError as exc:
                raise ValueError(f"X axis cell {x_index} contains non-numeric data") from exc

        for y_index in range(1, self._table_widget.rowCount()):
            y_item = self._table_widget.item(y_index, 0)
            if y_item is None or len(y_item.text().strip()) == 0:
                raise ValueError(f"Y axis cell {y_index} is incomplete")
            else:
                pass

            try:
                y_points.append(float(y_item.text().strip()))
            except ValueError as exc:
                raise ValueError(f"Y axis cell {y_index} contains non-numeric data") from exc

            z_row: list[float] = list()
            for x_index in range(1, self._table_widget.columnCount()):
                z_item = self._table_widget.item(y_index, x_index)
                if z_item is None or len(z_item.text().strip()) == 0:
                    raise ValueError(f"Matrix cell ({y_index}, {x_index}) is incomplete")
                else:
                    pass

                try:
                    z_row.append(float(z_item.text().strip()))
                except ValueError as exc:
                    raise ValueError(f"Matrix cell ({y_index}, {x_index}) contains non-numeric data") from exc

            z_matrix.append(z_row)

        return x_points, y_points, z_matrix

    def _parse_matrix_from_text(self, clipboard_text: str) -> tuple[list[float], list[float], list[list[float]]]:
        """
        Parse clipboard text into one matrix lookup surface.

        :param clipboard_text: Clipboard text pasted from a spreadsheet.
        :return: Tuple `(x_points, y_points, z_matrix)`.
        :raises ValueError: If the clipboard cannot be interpreted as a lookup matrix.
        """
        raw_lines: list[str] = list(line.rstrip("\r") for line in clipboard_text.splitlines() if len(line.strip()) > 0)
        row_lengths: set[int] = set()
        row_text: str
        x_points: list[float] = list()
        y_points: list[float] = list()
        z_matrix: list[list[float]] = list()
        parts: list[str]
        row_index: int

        if len(raw_lines) >= 3:
            pass
        else:
            raise ValueError("Clipboard must contain at least one header row and a 2x2 matrix body")

        for row_text in raw_lines:
            parts = row_text.split("\t")
            row_lengths.add(len(parts))

        if len(row_lengths) == 1:
            pass
        else:
            raise ValueError("Clipboard matrix rows must have the same number of columns")

        parts = raw_lines[0].split("\t")
        if len(parts) >= 3:
            pass
        else:
            raise ValueError("Clipboard matrix must contain at least two X columns")

        for row_index in range(1, len(parts)):
            try:
                x_points.append(float(parts[row_index].strip()))
            except ValueError as exc:
                raise ValueError("Clipboard X axis contains non-numeric data") from exc

        for row_text in raw_lines[1:]:
            parts = row_text.split("\t")

            try:
                y_points.append(float(parts[0].strip()))
            except ValueError as exc:
                raise ValueError("Clipboard Y axis contains non-numeric data") from exc

            z_row: list[float] = list()
            for row_index in range(1, len(parts)):
                try:
                    z_row.append(float(parts[row_index].strip()))
                except ValueError as exc:
                    raise ValueError("Clipboard matrix contains non-numeric data") from exc
            z_matrix.append(z_row)

        return x_points, y_points, z_matrix

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Forward unhandled key events to the base dialog.

        :param event: Incoming key event.
        :return: None.
        """
        super().keyPressEvent(event)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """
        Capture table shortcuts directly from the child widget.

        :param watched: Watched QObject.
        :param event: Qt event.
        :return: True when the event is handled here.
        """
        if watched is self._table_widget and event.type() == QtCore.QEvent.Type.KeyPress:
            key_event = event

            if isinstance(key_event, QtGui.QKeyEvent):
                if key_event.matches(QtGui.QKeySequence.StandardKey.Copy):
                    self.copy_selection_to_clipboard()
                    return True
                else:
                    pass

                if key_event.matches(QtGui.QKeySequence.StandardKey.Paste):
                    self.paste_from_clipboard()
                    return True
                else:
                    pass

                if key_event.key() == int(QtCore.Qt.Key.Key_Delete):
                    self.delete_selection()
                    return True
                else:
                    pass
            else:
                pass
        else:
            pass

        return super().eventFilter(watched, event)
