# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import json
import re
from typing import Any
from PySide6 import QtCore, QtGui, QtWidgets


class EditCellsCommand(QtGui.QUndoCommand):
    """
    Undo/redo command for one batch cell edit operation.
    """

    def __init__(self,
                 model: QtCore.QAbstractItemModel,
                 changes: list[tuple[QtCore.QPersistentModelIndex, Any, Any]],
                 text: str = "Edit Cells") -> None:
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

        # Group changed rows by column so one command can refresh rectangular spans per column.
        rows_by_column: dict[int, list[int]] = dict()
        for idx, old, new in self._changes:
            if idx.isValid():
                value: Any = old if old_value else new
                self._model.setData(idx, value, QtCore.Qt.ItemDataRole.EditRole)
                column_index: int = idx.column()
                if column_index in rows_by_column:
                    rows_by_column[column_index].append(idx.row())
                else:
                    rows_by_column[column_index] = [idx.row()]
            else:
                pass

        if len(rows_by_column) == 0:
            return

        column_index: int
        for column_index, rows in rows_by_column.items():
            top: int = min(rows)
            bottom: int = max(rows)
            top_left: QtCore.QModelIndex = self._model.index(top, column_index)
            bottom_right: QtCore.QModelIndex = self._model.index(bottom, column_index)
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

    Copy/paste note:
    Internal copies store column type metadata in the clipboard. When that
    metadata is present, pastes into columns with different types are rejected.
    """

    _INTERNAL_CLIPBOARD_MIME_TYPE: str = "application/x-veragrid-spreadsheet-copy"

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._handle_size: int = 8
        self._handle_margin: int = 1
        self._is_dragging_fill: bool = False
        self._fill_source: QtCore.QModelIndex | None = None
        self._fill_target: QtCore.QModelIndex | None = None
        self._undo_stack: QtGui.QUndoStack = QtGui.QUndoStack(self)
        self._bound_model: QtCore.QAbstractItemModel | None = None
        self._auto_scroll_timer: QtCore.QTimer = QtCore.QTimer(self)
        self._auto_scroll_direction: int = 0
        self._last_drag_pos: QtCore.QPoint = QtCore.QPoint()

        self.setMouseTracking(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ContiguousSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)

        self._copy_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Copy, self)
        self._copy_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._copy_shortcut.activated.connect(self.copy_selection_to_clipboard)

        self._undo_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Undo, self)
        self._undo_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._undo_shortcut.activated.connect(self._undo_stack.undo)

        self._redo_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Redo, self)
        self._redo_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._redo_shortcut.activated.connect(self._undo_stack.redo)

        self._paste_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Paste, self)
        self._paste_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._paste_shortcut.activated.connect(self.paste_from_clipboard)

        self._delete_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Delete), self)
        self._delete_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._delete_shortcut.activated.connect(self.clear_selected_cells)

        self._auto_scroll_timer.setInterval(60)
        self._auto_scroll_timer.timeout.connect(self._perform_auto_scroll_step)

    def setModel(self, model: QtCore.QAbstractItemModel | None) -> None:
        """
        Attach one model and reset fill/undo state when the backing data source changes.

        :param model: New item model.
        """
        self._disconnect_bound_model()
        QtWidgets.QTableView.setModel(self, model)
        self._bound_model = model
        self._connect_bound_model()
        self._reset_fill_state()
        self._undo_stack.clear()

    def _disconnect_bound_model(self) -> None:
        """
        Disconnect model lifecycle signals from the previously bound model.
        """
        if self._bound_model is not None:
            try:
                self._bound_model.modelReset.disconnect(self._on_bound_model_structure_changed)
            except (RuntimeError, TypeError):
                pass
            try:
                self._bound_model.rowsInserted.disconnect(self._on_bound_model_structure_changed)
            except (RuntimeError, TypeError):
                pass
            try:
                self._bound_model.rowsRemoved.disconnect(self._on_bound_model_structure_changed)
            except (RuntimeError, TypeError):
                pass
            try:
                self._bound_model.columnsInserted.disconnect(self._on_bound_model_structure_changed)
            except (RuntimeError, TypeError):
                pass
            try:
                self._bound_model.columnsRemoved.disconnect(self._on_bound_model_structure_changed)
            except (RuntimeError, TypeError):
                pass
            try:
                self._bound_model.layoutChanged.disconnect(self._on_bound_model_structure_changed)
            except (RuntimeError, TypeError):
                pass
        else:
            pass

    def _connect_bound_model(self) -> None:
        """
        Connect model lifecycle signals so undo history never survives structure changes.
        """
        if self._bound_model is not None:
            self._bound_model.modelReset.connect(self._on_bound_model_structure_changed)
            self._bound_model.rowsInserted.connect(self._on_bound_model_structure_changed)
            self._bound_model.rowsRemoved.connect(self._on_bound_model_structure_changed)
            self._bound_model.columnsInserted.connect(self._on_bound_model_structure_changed)
            self._bound_model.columnsRemoved.connect(self._on_bound_model_structure_changed)
            self._bound_model.layoutChanged.connect(self._on_bound_model_structure_changed)
        else:
            pass

    def _on_bound_model_structure_changed(self, *args: object) -> None:
        """
        Clear state after a structural model change invalidates stored cell references.

        :param args: Unused Qt signal payload.
        """
        _ = args
        self._reset_fill_state()
        self._undo_stack.clear()
        self.viewport().update()

    def _reset_fill_state(self) -> None:
        """
        Clear the transient drag-fill state.
        """
        self._is_dragging_fill = False
        self._fill_source = None
        self._fill_target = None
        self._auto_scroll_direction = 0
        self._auto_scroll_timer.stop()

    def _current_cell_rect(self) -> QtCore.QRect:
        """
        Return the visible rectangle of the current cell.

        :return: Current-cell rectangle or an empty rectangle.
        """
        idx = self.currentIndex()
        if not idx.isValid():
            return QtCore.QRect()
        return self.visualRect(idx)

    def _fill_handle_rect(self) -> QtCore.QRect:
        """
        Return the drag handle rectangle clipped to the viewport.

        :return: Handle rectangle or an empty rectangle.
        """
        cell_rect: QtCore.QRect = self._current_cell_rect()
        viewport_rect: QtCore.QRect = self.viewport().rect()
        if not cell_rect.isValid() or not viewport_rect.intersects(cell_rect):
            return QtCore.QRect()
        if cell_rect.width() <= (self._handle_size + self._handle_margin):
            return QtCore.QRect()
        if cell_rect.height() <= (self._handle_size + self._handle_margin):
            return QtCore.QRect()

        x_value: int = cell_rect.right() - self._handle_size - self._handle_margin + 1
        y_value: int = cell_rect.bottom() - self._handle_size - self._handle_margin + 1
        handle_rect: QtCore.QRect = QtCore.QRect(x_value, y_value, self._handle_size, self._handle_size)
        return handle_rect.intersected(viewport_rect)

    def _index_at_pos(self, pos: QtCore.QPoint) -> QtCore.QModelIndex:
        """
        Resolve one drag target from viewport coordinates while clamping to visible rows.

        :param pos: Viewport position.
        :return: Target model index or invalid index.
        """
        idx: QtCore.QModelIndex = self.indexAt(pos)
        if idx.isValid():
            return idx

        current: QtCore.QModelIndex = self.currentIndex()
        model: QtCore.QAbstractItemModel | None = self.model()
        if not current.isValid() or model is None:
            return QtCore.QModelIndex()

        viewport_rect: QtCore.QRect = self.viewport().rect()
        clamped_x: int = min(max(pos.x(), viewport_rect.left()), viewport_rect.right())
        clamped_y: int = min(max(pos.y(), viewport_rect.top()), viewport_rect.bottom())

        # Clamp the drag target to visible rows only. Auto-scroll handles extending the range.
        row_index: int = self.rowAt(clamped_y)
        col_index: int = self.columnAt(clamped_x)

        if row_index < 0:
            if clamped_y <= viewport_rect.top():
                row_index = self._visible_edge_row(edge="top", fallback_row=0)
            else:
                row_index = self._visible_edge_row(edge="bottom", fallback_row=current.row())
        else:
            pass

        if col_index < 0:
            col_index = current.column()
        else:
            pass

        row_index = min(max(row_index, 0), model.rowCount() - 1)
        col_index = min(max(col_index, 0), model.columnCount() - 1)
        return model.index(row_index, col_index)

    def _visible_edge_row(self, edge: str, fallback_row: int) -> int:
        """
        Resolve the first or last visible row in the viewport.

        :param edge: Visible edge, ``"top"`` or ``"bottom"``.
        :param fallback_row: Row used when no visible row can be resolved.
        :return: Visible row index or the fallback row.
        """
        viewport_rect: QtCore.QRect = self.viewport().rect()
        if edge == "top":
            y_values: range = range(viewport_rect.top(), viewport_rect.bottom() + 1)
        else:
            y_values = range(viewport_rect.bottom(), viewport_rect.top() - 1, -1)

        y_value: int
        for y_value in y_values:
            row_index: int = self.rowAt(y_value)
            if row_index >= 0:
                return row_index
            else:
                pass

        return fallback_row

    @staticmethod
    def _parse_clipboard_grid(clipboard_text: str) -> list[list[str]]:
        """
        Parse one clipboard payload into a two-dimensional text grid.

        :param clipboard_text: Clipboard text.
        :return: Parsed cell rows.
        """
        parsed_rows: list[list[str]] = list()
        line_text: str

        for line_text in clipboard_text.splitlines():
            if len(line_text.strip()) > 0:
                if "\t" in line_text:
                    parsed_rows.append([part.rstrip("\r") for part in line_text.split("\t")])
                else:
                    parsed_rows.append([part.strip() for part in re.split(r"[;,]+", line_text.strip())])
            else:
                pass

        return parsed_rows

    def _get_anchor_index(self) -> QtCore.QModelIndex:
        """
        Return the anchor cell used by spreadsheet paste.

        :return: Anchor cell or invalid index.
        """
        selection_range: QtCore.QItemSelectionRange | None = self._selection_range()
        model: QtCore.QAbstractItemModel | None = self.model()
        if model is None:
            return QtCore.QModelIndex()

        if selection_range is not None and not selection_range.isEmpty():
            return model.index(selection_range.top(), selection_range.left())
        else:
            return self.currentIndex()

    def _source_value_for_edit(self, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> Any:
        """
        Get the preferred source value for one edit operation.

        :param model: Item model.
        :param index: Source index.
        :return: Edit-role value or display fallback.
        """
        value: Any = model.data(index, QtCore.Qt.ItemDataRole.EditRole)
        if value is None:
            return model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
        else:
            return value

    def _set_index_value(self, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex, value: Any) -> bool:
        """
        Assign one value through the edit role.

        :param model: Item model.
        :param index: Target index.
        :param value: Value to assign.
        :return: ``True`` when the model accepted the value.
        """
        if not index.isValid():
            return False
        if not (model.flags(index) & QtCore.Qt.ItemFlag.ItemIsEditable):
            return False
        return bool(model.setData(index, value, QtCore.Qt.ItemDataRole.EditRole))

    def _editable_indexes_from_selection(self) -> list[QtCore.QModelIndex]:
        """
        Return the editable selected cells, or the current cell when nothing is selected.

        :return: Ordered editable index list.
        """
        model: QtCore.QAbstractItemModel | None = self.model()
        if model is None:
            return list()

        selection_model: QtCore.QItemSelectionModel | None = self.selectionModel()
        if selection_model is not None:
            selected_indexes: list[QtCore.QModelIndex] = list(selection_model.selectedIndexes())
        else:
            selected_indexes = list()

        if len(selected_indexes) == 0:
            current_index: QtCore.QModelIndex = self.currentIndex()
            if current_index.isValid():
                selected_indexes = [current_index]
            else:
                pass
        else:
            pass

        selected_indexes.sort(key=lambda idx: (idx.row(), idx.column()))
        editable_indexes: list[QtCore.QModelIndex] = list()
        index: QtCore.QModelIndex
        for index in selected_indexes:
            if model.flags(index) & QtCore.Qt.ItemFlag.ItemIsEditable:
                editable_indexes.append(index)
            else:
                pass

        return editable_indexes

    def _clear_value_for_index(self, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> Any:
        """
        Determine one safe clear value from the current cell type.

        :param model: Item model.
        :param index: Target index.
        :return: Cleared value.
        """
        value: Any = self._source_value_for_edit(model=model, index=index)
        if isinstance(value, bool):
            return False
        elif isinstance(value, int) and not isinstance(value, bool):
            return 0
        elif isinstance(value, float):
            return 0.0
        elif isinstance(value, complex):
            return complex(0.0, 0.0)
        elif value is None:
            return ""
        else:
            return ""

    def _update_drag_target_from_position(self, pos: QtCore.QPoint) -> None:
        """
        Refresh the drag target and auto-scroll state from one viewport position.

        :param pos: Viewport position.
        """
        if self._is_dragging_fill and self._fill_source is not None:
            self._last_drag_pos = pos
            target: QtCore.QModelIndex = self._index_at_pos(pos)
            if target.isValid() and target.column() == self._fill_source.column():
                self._fill_target = target
            else:
                pass
            self._update_auto_scroll_state(pos=pos)
            self.viewport().update()
        else:
            pass

    def _update_auto_scroll_state(self, pos: QtCore.QPoint) -> None:
        """
        Enable or disable vertical auto-scroll according to the drag position.

        :param pos: Viewport position.
        """
        viewport_rect: QtCore.QRect = self.viewport().rect()
        margin: int = 20

        if pos.y() < (viewport_rect.top() + margin):
            self._auto_scroll_direction = -1
        elif pos.y() > (viewport_rect.bottom() - margin):
            self._auto_scroll_direction = 1
        else:
            self._auto_scroll_direction = 0

        if self._auto_scroll_direction == 0:
            self._auto_scroll_timer.stop()
        else:
            if not self._auto_scroll_timer.isActive():
                self._auto_scroll_timer.start()
            else:
                pass

    def _perform_auto_scroll_step(self) -> None:
        """
        Scroll one step while a fill drag remains active.
        """
        if not self._is_dragging_fill:
            self._auto_scroll_timer.stop()
            return

        vertical_scroll_bar: QtWidgets.QScrollBar = self.verticalScrollBar()
        current_value: int = vertical_scroll_bar.value()
        single_step: int = max(1, vertical_scroll_bar.singleStep())
        new_value: int = current_value + self._auto_scroll_direction * single_step
        bounded_value: int = min(max(new_value, vertical_scroll_bar.minimum()), vertical_scroll_bar.maximum())

        if bounded_value != current_value:
            vertical_scroll_bar.setValue(bounded_value)
            self._update_drag_target_from_position(self._last_drag_pos)
        else:
            self._auto_scroll_timer.stop()

    def _select_fill_range(self, source_index: QtCore.QModelIndex, target_index: QtCore.QModelIndex) -> None:
        """
        Select the affected drag-fill range after one fill operation.

        :param source_index: Source cell used for the fill.
        :param target_index: Final drag target cell.
        """
        model: QtCore.QAbstractItemModel | None = self.model()
        selection_model: QtCore.QItemSelectionModel | None = self.selectionModel()
        if model is None or selection_model is None:
            return
        if not source_index.isValid() or not target_index.isValid():
            return
        if source_index.column() != target_index.column():
            return

        top_row: int = min(source_index.row(), target_index.row())
        bottom_row: int = max(source_index.row(), target_index.row())
        top_left: QtCore.QModelIndex = model.index(top_row, source_index.column())
        bottom_right: QtCore.QModelIndex = model.index(bottom_row, source_index.column())
        selection: QtCore.QItemSelection = QtCore.QItemSelection(top_left, bottom_right)

        selection_model.select(
            selection,
            QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect,
        )
        selection_model.setCurrentIndex(
            bottom_right,
            QtCore.QItemSelectionModel.SelectionFlag.Current,
        )

    def _selection_range(self) -> QtCore.QItemSelectionRange | None:
        """
        Return the single rectangular selection range used for spreadsheet copy.

        :return: One rectangular selection range or ``None``.
        """
        selection_model: QtCore.QItemSelectionModel | None = self.selectionModel()
        if selection_model is not None:
            ranges: list[QtCore.QItemSelectionRange] = list(selection_model.selection())
            if len(ranges) > 0:
                return ranges[0]
            else:
                return None
        else:
            return None

    def _column_signature(self, model: QtCore.QAbstractItemModel, column_index: int) -> str:
        """
        Return one stable column signature used to validate typed copy/paste.

        :param model: Source model.
        :param column_index: Column index.
        :return: Column signature string.
        """
        if hasattr(model, "get_column_type"):
            column_tpe: object = model.get_column_type(column_index)  # type: ignore[attr-defined]
            if isinstance(column_tpe, type):
                return f"type:{column_tpe.__module__}.{column_tpe.__qualname__}"
            else:
                return f"repr:{repr(column_tpe)}"
        else:
            row_count: int = model.rowCount()
            row_index: int
            for row_index in range(row_count):
                index: QtCore.QModelIndex = model.index(row_index, column_index)
                value: Any = self._source_value_for_edit(model=model, index=index)
                if value is not None:
                    value_tpe: type = type(value)
                    return f"type:{value_tpe.__module__}.{value_tpe.__qualname__}"
                else:
                    pass
            return "unknown"

    def _build_internal_clipboard_payload(self,
                                          model: QtCore.QAbstractItemModel,
                                          selection_range: QtCore.QItemSelectionRange) -> bytes:
        """
        Build one internal clipboard payload with source column signatures.

        :param model: Source model.
        :param selection_range: Copied rectangular range.
        :return: JSON payload bytes.
        """
        column_signatures: list[str] = list()
        column_index: int
        for column_index in range(selection_range.left(), selection_range.right() + 1):
            column_signatures.append(self._column_signature(model=model, column_index=column_index))

        payload: dict[str, object] = {
            "column_signatures": column_signatures,
            "n_columns": len(column_signatures),
        }
        return json.dumps(payload).encode("utf-8")

    def _get_internal_clipboard_column_signatures(self) -> list[str] | None:
        """
        Read internal copy metadata from the clipboard when available.

        :return: Source column signatures or ``None``.
        """
        mime_data: QtCore.QMimeData | None = QtWidgets.QApplication.clipboard().mimeData()
        if mime_data is None:
            return None
        if not mime_data.hasFormat(self._INTERNAL_CLIPBOARD_MIME_TYPE):
            return None

        payload_bytes: QtCore.QByteArray = mime_data.data(self._INTERNAL_CLIPBOARD_MIME_TYPE)
        try:
            payload: object = json.loads(bytes(payload_bytes).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

        if isinstance(payload, dict):
            signatures: object = payload.get("column_signatures", None)
            if isinstance(signatures, list):
                parsed_signatures: list[str] = list()
                signature: object
                for signature in signatures:
                    if isinstance(signature, str):
                        parsed_signatures.append(signature)
                    else:
                        return None
                return parsed_signatures
            else:
                return None
        else:
            return None

    def _can_paste_column_signatures(self,
                                     model: QtCore.QAbstractItemModel,
                                     anchor_index: QtCore.QModelIndex,
                                     source_column_signatures: list[str],
                                     parsed_rows: list[list[str]]) -> bool:
        """
        Check whether one typed clipboard rectangle can be pasted at the target anchor.

        :param model: Target model.
        :param anchor_index: Paste anchor cell.
        :param source_column_signatures: Source column signatures from internal clipboard metadata.
        :param parsed_rows: Parsed clipboard cell rows.
        :return: ``True`` when the target columns match the source types.
        """
        max_source_columns: int = 0
        row_values: list[str]
        for row_values in parsed_rows:
            if len(row_values) > max_source_columns:
                max_source_columns = len(row_values)
            else:
                pass

        if max_source_columns > len(source_column_signatures):
            return False
        else:
            pass

        column_offset: int
        for column_offset in range(max_source_columns):
            target_column_index: int = anchor_index.column() + column_offset
            if target_column_index >= model.columnCount():
                return False
            source_signature: str = source_column_signatures[column_offset]
            target_signature: str = self._column_signature(model=model, column_index=target_column_index)
            if source_signature != target_signature:
                return False
            else:
                pass

        return True

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        Paint the table and the spreadsheet fill affordances.

        :param event: Paint event.
        """
        super().paintEvent(event)
        idx: QtCore.QModelIndex = self.currentIndex()
        if not idx.isValid():
            return

        model: QtCore.QAbstractItemModel | None = self.model()
        if model is None:
            return

        if not (model.flags(idx) & QtCore.Qt.ItemFlag.ItemIsEditable):
            return

        handle_rect: QtCore.QRect = self._fill_handle_rect()
        if not handle_rect.isValid():
            return

        # Paint the handle over the current cell only when the handle fits inside the viewport.
        painter: QtGui.QPainter = QtGui.QPainter(self.viewport())
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
        """
        Start a fill drag when the handle receives the press.

        :param event: Mouse event.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos: QtCore.QPoint = event.position().toPoint()
            handle_rect: QtCore.QRect = self._fill_handle_rect()
            if handle_rect.contains(pos):
                idx: QtCore.QModelIndex = self.currentIndex()
                if idx.isValid():
                    self._is_dragging_fill = True
                    self._fill_source = idx
                    self._fill_target = idx
                    self.viewport().update()
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Update the drag target while one fill operation is active.

        :param event: Mouse event.
        """
        if self._is_dragging_fill and self._fill_source is not None:
            self._update_drag_target_from_position(event.position().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Commit one fill drag on release.

        :param event: Mouse event.
        """
        if self._is_dragging_fill and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._apply_fill()
            self._reset_fill_state()
            self.viewport().update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Open a small spreadsheet context menu.

        :param event: Context menu event.
        """
        menu: QtWidgets.QMenu = QtWidgets.QMenu(self)
        copy_action: QtGui.QAction = menu.addAction("Copy")
        paste_action: QtGui.QAction = menu.addAction("Paste")
        clear_action: QtGui.QAction = menu.addAction("Clear")
        menu.addSeparator()
        undo_action: QtGui.QAction = menu.addAction("Undo")
        redo_action: QtGui.QAction = menu.addAction("Redo")

        undo_action.setEnabled(self._undo_stack.canUndo())
        redo_action.setEnabled(self._undo_stack.canRedo())

        selected_action: QtGui.QAction | None = menu.exec(event.globalPos())
        if selected_action == copy_action:
            self.copy_selection_to_clipboard()
        elif selected_action == paste_action:
            self.paste_from_clipboard()
        elif selected_action == clear_action:
            self.clear_selected_cells()
        elif selected_action == undo_action:
            self._undo_stack.undo()
        elif selected_action == redo_action:
            self._undo_stack.redo()
        else:
            pass

    def _apply_fill(self) -> None:
        """
        Copy the current cell value into the dragged vertical range.
        """
        if self._fill_source is None or self._fill_target is None:
            return
        model: QtCore.QAbstractItemModel | None = self.model()
        if model is None:
            return

        src: QtCore.QModelIndex = self._fill_source
        dst: QtCore.QModelIndex = self._fill_target
        if not src.isValid() or not dst.isValid():
            return
        if src.column() != dst.column():
            return
        if src.row() == dst.row():
            return

        # Resolve the source value once so the whole dragged range receives the same typed payload.
        value: Any = model.data(src, QtCore.Qt.ItemDataRole.EditRole)
        if value is None:
            value = model.data(src, QtCore.Qt.ItemDataRole.DisplayRole)

        top: int = min(src.row(), dst.row())
        bottom: int = max(src.row(), dst.row())
        changes: list[tuple[QtCore.QPersistentModelIndex, Any, Any]] = list()

        for row in range(top, bottom + 1):
            if row == src.row():
                continue
            idx: QtCore.QModelIndex = model.index(row, src.column())
            if model.flags(idx) & QtCore.Qt.ItemFlag.ItemIsEditable:
                old_value: Any = model.data(idx, QtCore.Qt.ItemDataRole.EditRole)
                if old_value is None:
                    old_value = model.data(idx, QtCore.Qt.ItemDataRole.DisplayRole)
                changes.append((QtCore.QPersistentModelIndex(idx), old_value, value))
            else:
                pass

        if not changes:
            return

        command: EditCellsCommand = EditCellsCommand(model=model, changes=changes, text="Fill Cells")
        self._undo_stack.push(command)
        self._select_fill_range(source_index=src, target_index=dst)

    def undo_stack(self) -> QtGui.QUndoStack:
        """
        Return the local undo stack used by spreadsheet fill operations.

        :return: Undo stack.
        """
        return self._undo_stack

    def paste_from_clipboard(self) -> tuple[int, int]:
        """
        Paste one clipboard rectangle starting at the current anchor cell.

        :return: Tuple ``(pasted_cells, failed_cells)``.
        """
        model: QtCore.QAbstractItemModel | None = self.model()
        if model is None:
            return 0, 0

        clipboard_text: str = QtWidgets.QApplication.clipboard().text()
        parsed_rows: list[list[str]] = self._parse_clipboard_grid(clipboard_text=clipboard_text)
        if len(parsed_rows) == 0:
            return 0, 0

        anchor_index: QtCore.QModelIndex = self._get_anchor_index()
        if not anchor_index.isValid():
            return 0, 0

        source_column_signatures: list[str] | None = self._get_internal_clipboard_column_signatures()
        if source_column_signatures is not None:
            if not self._can_paste_column_signatures(
                model=model,
                anchor_index=anchor_index,
                source_column_signatures=source_column_signatures,
                parsed_rows=parsed_rows,
            ):
                return 0, len(parsed_rows) * max((len(row_values) for row_values in parsed_rows), default=0)
            else:
                pass
        else:
            pass

        row_count: int = model.rowCount()
        col_count: int = model.columnCount()
        changes: list[tuple[QtCore.QPersistentModelIndex, Any, Any]] = list()
        failed_cells: int = 0
        row_offset: int
        col_offset: int

        for row_offset, row_values in enumerate(parsed_rows):
            for col_offset, value_text in enumerate(row_values):
                target_row: int = anchor_index.row() + row_offset
                target_col: int = anchor_index.column() + col_offset
                if target_row < row_count and target_col < col_count:
                    target_index: QtCore.QModelIndex = model.index(target_row, target_col)
                    if model.flags(target_index) & QtCore.Qt.ItemFlag.ItemIsEditable:
                        old_value: Any = self._source_value_for_edit(model=model, index=target_index)
                        changes.append((QtCore.QPersistentModelIndex(target_index), old_value, value_text))
                    else:
                        failed_cells += 1
                else:
                    failed_cells += 1

        if len(changes) > 0:
            command: EditCellsCommand = EditCellsCommand(model=model, changes=changes, text="Paste Cells")
            self._undo_stack.push(command)
        else:
            pass

        return len(changes), failed_cells

    def clear_selected_cells(self) -> int:
        """
        Clear the selected editable cells, or the current cell when nothing is selected.

        :return: Number of cleared cells.
        """
        model: QtCore.QAbstractItemModel | None = self.model()
        if model is None:
            return 0

        editable_indexes: list[QtCore.QModelIndex] = self._editable_indexes_from_selection()
        if len(editable_indexes) == 0:
            return 0

        cleared_cells: int = 0
        index: QtCore.QModelIndex
        for index in editable_indexes:
            clear_value: Any = self._clear_value_for_index(model=model, index=index)
            if self._set_index_value(model=model, index=index, value=clear_value):
                cleared_cells += 1
            else:
                pass

        return cleared_cells

    def copy_selection_to_clipboard(self) -> bool:
        """
        Copy the current rectangular selection to the clipboard.

        :return: ``True`` when one selection or current cell was copied.
        """
        model: QtCore.QAbstractItemModel | None = self.model()
        if model is None:
            return False

        selection_range: QtCore.QItemSelectionRange | None = self._selection_range()
        if selection_range is None or selection_range.isEmpty():
            idx: QtCore.QModelIndex = self.currentIndex()
            if not idx.isValid():
                return False
            selection_range = QtCore.QItemSelectionRange(idx)
        else:
            pass

        text_rows: list[str] = list()
        row_index: int
        col_index: int

        # Copy one explicit rectangle only, matching spreadsheet expectations and paste semantics.
        for row_index in range(selection_range.top(), selection_range.bottom() + 1):
            row_values: list[str] = list()
            for col_index in range(selection_range.left(), selection_range.right() + 1):
                idx = model.index(row_index, col_index)
                value: Any = model.data(idx, QtCore.Qt.ItemDataRole.DisplayRole)
                row_values.append("" if value is None else str(value))
            text_rows.append("\t".join(row_values))

        text_payload: str = "\n".join(text_rows)
        mime_data: QtCore.QMimeData = QtCore.QMimeData()
        mime_data.setText(text_payload)
        mime_data.setData(
            self._INTERNAL_CLIPBOARD_MIME_TYPE,
            self._build_internal_clipboard_payload(model=model, selection_range=selection_range),
        )
        QtWidgets.QApplication.clipboard().setMimeData(mime_data)
        return True

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
