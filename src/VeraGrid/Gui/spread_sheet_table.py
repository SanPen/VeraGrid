# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Any
from PySide6 import QtCore, QtGui, QtWidgets


class FillCellsCommand(QtGui.QUndoCommand):
    """
    Undo/redo command for one fill operation.
    """

    def __init__(self,
                 model: QtCore.QAbstractItemModel,
                 changes: list[tuple[QtCore.QModelIndex, Any, Any]],
                 text: str = "Fill Cells") -> None:
        super().__init__(text)
        self._model = model
        self._changes = changes

    def undo(self) -> None:
        self._apply(old_value=True)

    def redo(self) -> None:
        self._apply(old_value=False)

    def _apply(self, old_value: bool) -> None:
        if not self._changes:
            return

        rows = []
        col = self._changes[0][0].column()
        for idx, old, new in self._changes:
            value = old if old_value else new
            self._model.setData(idx, value, QtCore.Qt.ItemDataRole.EditRole)
            rows.append(idx.row())

        top = min(rows)
        bottom = max(rows)
        top_left = self._model.index(top, col)
        bottom_right = self._model.index(bottom, col)
        self._model.dataChanged.emit(
            top_left,
            bottom_right,
            [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole],
        )


class SpreadsheetTableView(QtWidgets.QTableView):
    """
    QTableView with an Excel-like fill handle on the current cell.
    Dragging the handle down copies the current cell value to the selected range.

    VeraGrid integration note:
    Replace an existing .ui QTableView (for example `dataStructureTableView`) by
    promoting it in Qt Designer to this class:
      - class: SpreadsheetTableView
      - module: VeraGrid.Gui.spread_sheet_table
    This keeps the same object name and layout position.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._handle_size = 8
        self._handle_margin = 1
        self._is_dragging_fill = False
        self._fill_source: QtCore.QModelIndex | None = None
        self._fill_target: QtCore.QModelIndex | None = None
        self._undo_stack = QtGui.QUndoStack(self)

        self.setMouseTracking(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ContiguousSelection)

        self._copy_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Copy, self)
        self._copy_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._copy_shortcut.activated.connect(self._copy_selection_to_clipboard)

        self._undo_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Undo, self)
        self._undo_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._undo_shortcut.activated.connect(self._undo_stack.undo)

        self._redo_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Redo, self)
        self._redo_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._redo_shortcut.activated.connect(self._undo_stack.redo)

    def _current_cell_rect(self) -> QtCore.QRect:
        idx = self.currentIndex()
        if not idx.isValid():
            return QtCore.QRect()
        return self.visualRect(idx)

    def _fill_handle_rect(self) -> QtCore.QRect:
        cell_rect = self._current_cell_rect()
        if not cell_rect.isValid():
            return QtCore.QRect()
        x = cell_rect.right() - self._handle_size - self._handle_margin + 1
        y = cell_rect.bottom() - self._handle_size - self._handle_margin + 1
        return QtCore.QRect(x, y, self._handle_size, self._handle_size)

    def _index_at_pos(self, pos: QtCore.QPoint) -> QtCore.QModelIndex:
        idx = self.indexAt(pos)
        if idx.isValid():
            return idx
        current = self.currentIndex()
        if not current.isValid():
            return QtCore.QModelIndex()
        rect = self.rect()
        if not rect.contains(pos):
            return current
        row = current.row()
        col = current.column()
        if pos.y() > self._current_cell_rect().bottom():
            row = self.model().rowCount() - 1
        return self.model().index(max(0, row), max(0, col))

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        idx = self.currentIndex()
        if not idx.isValid():
            return

        model = self.model()
        if model is None:
            return

        if not (model.flags(idx) & QtCore.Qt.ItemFlag.ItemIsEditable):
            return

        handle_rect = self._fill_handle_rect()
        if not handle_rect.isValid():
            return

        painter = QtGui.QPainter(self.viewport())
        painter.save()
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor("#2a7fff"))
        painter.drawRect(handle_rect)
        painter.restore()

        if self._is_dragging_fill and self._fill_source and self._fill_target:
            src = self._fill_source
            dst = self._fill_target
            if src.column() == dst.column():
                top = min(src.row(), dst.row())
                bottom = max(src.row(), dst.row())
                r1 = self.visualRect(self.model().index(top, src.column()))
                r2 = self.visualRect(self.model().index(bottom, src.column()))
                selection_rect = r1.united(r2)
                painter.save()
                pen = QtGui.QPen(QtGui.QColor("#2a7fff"))
                pen.setWidth(1)
                pen.setStyle(QtCore.Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                painter.drawRect(selection_rect)
                painter.restore()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            handle_rect = self._fill_handle_rect()
            if handle_rect.contains(pos):
                idx = self.currentIndex()
                if idx.isValid():
                    self._is_dragging_fill = True
                    self._fill_source = idx
                    self._fill_target = idx
                    self.viewport().update()
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._is_dragging_fill and self._fill_source is not None:
            target = self._index_at_pos(event.position().toPoint())
            if target.isValid() and target.column() == self._fill_source.column():
                self._fill_target = target
                self.viewport().update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._is_dragging_fill and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._apply_fill()
            self._is_dragging_fill = False
            self._fill_source = None
            self._fill_target = None
            self.viewport().update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _apply_fill(self) -> None:
        if self._fill_source is None or self._fill_target is None:
            return
        model = self.model()
        if model is None:
            return

        src = self._fill_source
        dst = self._fill_target
        if not src.isValid() or not dst.isValid():
            return
        if src.column() != dst.column():
            return
        if src.row() == dst.row():
            return

        value: Any = model.data(src, QtCore.Qt.ItemDataRole.EditRole)
        if value is None:
            value = model.data(src, QtCore.Qt.ItemDataRole.DisplayRole)

        top = min(src.row(), dst.row())
        bottom = max(src.row(), dst.row())
        changes: list[tuple[QtCore.QModelIndex, Any, Any]] = []

        for row in range(top, bottom + 1):
            if row == src.row():
                continue
            idx = model.index(row, src.column())
            if model.flags(idx) & QtCore.Qt.ItemFlag.ItemIsEditable:
                old_value = model.data(idx, QtCore.Qt.ItemDataRole.EditRole)
                if old_value is None:
                    old_value = model.data(idx, QtCore.Qt.ItemDataRole.DisplayRole)
                changes.append((idx, old_value, value))

        if not changes:
            return

        command = FillCellsCommand(model=model, changes=changes)
        self._undo_stack.push(command)

    def undo_stack(self) -> QtGui.QUndoStack:
        return self._undo_stack

    def _copy_selection_to_clipboard(self) -> None:
        model = self.model()
        if model is None:
            return

        selected = self.selectionModel().selectedIndexes() if self.selectionModel() else []
        if not selected:
            idx = self.currentIndex()
            if not idx.isValid():
                return
            selected = [idx]

        rows = sorted({idx.row() for idx in selected})
        cols = sorted({idx.column() for idx in selected})
        selected_pos = {(idx.row(), idx.column()) for idx in selected}

        text_rows = []
        for r in rows:
            row_values = []
            for c in cols:
                idx = model.index(r, c)
                if (r, c) in selected_pos:
                    value = model.data(idx, QtCore.Qt.ItemDataRole.DisplayRole)
                    row_values.append("" if value is None else str(value))
                else:
                    row_values.append("")
            text_rows.append("\t".join(row_values))

        QtWidgets.QApplication.clipboard().setText("\n".join(text_rows))


def _build_demo_model(rows: int = 20, cols: int = 4) -> QtGui.QStandardItemModel:
    model = QtGui.QStandardItemModel(rows, cols)
    model.setHorizontalHeaderLabels([f"Col {i + 1}" for i in range(cols)])
    for r in range(rows):
        for c in range(cols):
            item = QtGui.QStandardItem(f"{(r + 1) * (c + 1)}")
            item.setEditable(True)
            model.setItem(r, c, item)
    return model


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    view = SpreadsheetTableView()
    view.setWindowTitle("SpreadsheetTableView Demo")
    view.resize(720, 420)
    view.setAlternatingRowColors(True)
    view.setModel(_build_demo_model())
    view.horizontalHeader().setStretchLastSection(True)
    view.show()

    sys.exit(app.exec())
