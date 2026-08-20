# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialogButtonBox,
                               QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                               QTableWidget, QTableWidgetItem, QVBoxLayout)
from VeraGrid.Session.dynamic_editor_entries import DynamicEditorEntry
from VeraGridEngine.enumerations import DynamicEditorMimeType, DynamicSimulationMode


class DynamicEditorPickerDialog(QtWidgets.QDialog):
    """Modal dialog used by the workspace ``+`` button to open another editor."""

    __slots__ = ()

    def __init__(self,
                 entries: list[DynamicEditorEntry],
                 current_entry: DynamicEditorEntry | None = None,
                 current_mode: DynamicSimulationMode | None = None,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Create a picker for opening another device and simulation mode.

        :param entries: Dynamic editor entries offered by the workspace.
        :param current_entry: Entry represented by the current editor.
        :param current_mode: Simulation mode used by the current editor.
        :param parent: Owning workspace widget.
        :return: None.
        """
        super().__init__(parent)
        self.setObjectName("DynamicEditorPickerDialog")
        self.resize(720, 520)

        self._entries: list[DynamicEditorEntry] = entries
        self._filtered_entries: list[DynamicEditorEntry] = list(entries)
        self._selected_entry: DynamicEditorEntry | None = None
        self._selected_mode: DynamicSimulationMode | None = None
        self._quick_entry: DynamicEditorEntry | None = current_entry
        self._quick_mode: DynamicSimulationMode | None = None

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(12, 12, 12, 12)

        self.quickOpenGroupBox = QGroupBox(self)
        self.quickOpenGroupBox.setTitle(self.tr("Quick Open"))
        self.horizontalLayoutQuick = QHBoxLayout(self.quickOpenGroupBox)

        self.quickOpenLabel = QLabel(self.tr("Open the current block in the other mode."), self.quickOpenGroupBox)
        self.quickOpenLabel.setWordWrap(True)
        self.horizontalLayoutQuick.addWidget(self.quickOpenLabel)

        self.quickOpenButton = QPushButton(self.tr("Open"), self.quickOpenGroupBox)
        self.horizontalLayoutQuick.addWidget(self.quickOpenButton)

        self.verticalLayout.addWidget(self.quickOpenGroupBox)

        self.searchLineEdit = QLineEdit(self)
        self.searchLineEdit.setPlaceholderText(self.tr("Search dynamic editors"))
        self.searchLineEdit.setClearButtonEnabled(True)
        self.verticalLayout.addWidget(self.searchLineEdit)

        self.entriesTableWidget = QTableWidget(self)
        self.entriesTableWidget.setColumnCount(3)
        self.entriesTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entriesTableWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.entriesTableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entriesTableWidget.verticalHeader().setVisible(False)

        header = self.entriesTableWidget.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for col, text in enumerate(list((self.tr("Name"), self.tr("Type"), self.tr("Modes"),))):
            self.entriesTableWidget.setHorizontalHeaderItem(col, QTableWidgetItem(text))

        self.verticalLayout.addWidget(self.entriesTableWidget)

        self.horizontalLayoutMode = QHBoxLayout()

        self.modeLabel = QLabel(self.tr("Mode"), self)
        self.horizontalLayoutMode.addWidget(self.modeLabel)

        self.modeComboBox = QComboBox(self)
        self.horizontalLayoutMode.addWidget(self.modeComboBox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayoutMode.addItem(self.horizontalSpacer)

        self.verticalLayout.addLayout(self.horizontalLayoutMode)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Open)
        self.verticalLayout.addWidget(self.buttonBox)

        self.searchLineEdit.textChanged.connect(self._apply_filter)
        self.entriesTableWidget.itemSelectionChanged.connect(self._on_selection_changed)
        self.entriesTableWidget.itemDoubleClicked.connect(self._accept_selected_entry)
        self.modeComboBox.currentIndexChanged.connect(self._on_mode_changed)
        self.quickOpenButton.clicked.connect(self._accept_quick_open)
        self.buttonBox.accepted.connect(self._accept_selected_entry)
        self.buttonBox.rejected.connect(self.reject)

        self._configure_quick_open(current_entry=current_entry, current_mode=current_mode)
        self._apply_filter("")

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """
        Refresh runtime-owned dialog strings after a Qt language change.

        :param event: Incoming Qt change event.
        :return: None.
        """
        QtWidgets.QDialog.changeEvent(self, event)

        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.refresh_runtime_translations()
        else:
            pass

    def refresh_runtime_translations(self) -> None:
        """
        Refresh the picker strings created directly from Python code.

        :return: None.
        """
        self.quickOpenGroupBox.setTitle(self.tr("Quick Open"))
        self.quickOpenLabel.setText(self.tr("Open the current block in the other mode."))
        self.quickOpenButton.setText(self.tr("Open"))
        self.searchLineEdit.setPlaceholderText(self.tr("Search dynamic editors"))
        self.modeLabel.setText(self.tr("Mode"))
        self.entriesTableWidget.setHorizontalHeaderLabels(list((self.tr("Name"), self.tr("Type"), self.tr("Modes"),)))
        self._configure_quick_open(current_entry=self._quick_entry, current_mode=self._selected_mode)

    def _configure_quick_open(self,
                              current_entry: DynamicEditorEntry | None,
                              current_mode: DynamicSimulationMode | None) -> None:
        """Configure the shortcut that opens the current device in another mode.

        :param current_entry: Entry represented by the current editor.
        :param current_mode: Simulation mode used by the current editor.
        :return: None.
        """
        if current_entry is None or current_mode is None:
            self.quickOpenGroupBox.setVisible(False)
            return
        else:
            pass

        alternate_modes = [mode for mode in current_entry.available_modes if mode != current_mode]
        if len(alternate_modes) == 0:
            self.quickOpenGroupBox.setVisible(False)
            return
        else:
            pass

        self._quick_mode = alternate_modes[0]
        self.quickOpenGroupBox.setVisible(True)
        self.quickOpenLabel.setText(
            self.tr("Open the current block in {mode}.").format(mode=self._quick_mode.name)
        )
        self.quickOpenButton.setText(self.tr("Open {mode}").format(mode=self._quick_mode.name))

    def _apply_filter(self, text: str) -> None:
        """Filter the candidate table using device, type, and mode text.

        :param text: User-entered search text.
        :return: None.
        """
        needle = text.strip().lower()
        if needle:
            self._filtered_entries = [
                entry
                for entry in self._entries
                if needle in entry.display_name.lower()
                   or needle in entry.type_label.lower()
                   or needle in " ".join(mode.name.lower() for mode in entry.available_modes)
            ]
        else:
            self._filtered_entries = list(self._entries)

        self.entriesTableWidget.setRowCount(len(self._filtered_entries))
        for row, entry in enumerate(self._filtered_entries):
            self.entriesTableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(entry.display_name))
            self.entriesTableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(entry.type_label))
            self.entriesTableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(
                " / ".join(mode.name for mode in entry.available_modes)))

        if len(self._filtered_entries) > 0:
            self.entriesTableWidget.selectRow(0)
        else:
            self._selected_entry = None
            self._selected_mode = None
            self.modeComboBox.clear()

    def _on_selection_changed(self) -> None:
        """Synchronize the selected entry and its available mode choices.

        :return: None.
        """
        current_row = self.entriesTableWidget.currentRow()
        if current_row < 0 or current_row >= len(self._filtered_entries):
            self._selected_entry = None
            self._selected_mode = None
            self.modeComboBox.clear()
            return
        else:
            pass

        self._selected_entry = self._filtered_entries[current_row]
        self.modeComboBox.blockSignals(True)
        self.modeComboBox.clear()
        for mode in self._selected_entry.available_modes:
            self.modeComboBox.addItem(mode.name, mode)
        self.modeComboBox.blockSignals(False)

        if self.modeComboBox.count() > 0:
            self._selected_mode = self.modeComboBox.currentData(QtCore.Qt.ItemDataRole.UserRole)
        else:
            self._selected_mode = None

    def _on_mode_changed(self, _index: int) -> None:
        """Store the mode selected by the user.

        :param _index: Combo-box index supplied by Qt.
        :return: None.
        """
        self._selected_mode = self.modeComboBox.currentData(QtCore.Qt.ItemDataRole.UserRole)

    def _accept_quick_open(self) -> None:
        """Accept the current-device shortcut when its target is complete.

        :return: None.
        """
        if self._quick_entry is None or self._quick_mode is None:
            return
        else:
            pass

        self._selected_entry = self._quick_entry
        self._selected_mode = self._quick_mode
        self.accept()

    def _accept_selected_entry(self) -> None:
        """Accept the table selection when both entry and mode are available.

        :return: None.
        """
        if self._selected_entry is None or self._selected_mode is None:
            return
        else:
            pass
        self.accept()

    def get_selection(self) -> tuple[DynamicEditorEntry, DynamicSimulationMode] | None:
        """Return the accepted entry and simulation mode.

        :return: Accepted selection, or ``None`` when incomplete.
        """
        if self._selected_entry is None or self._selected_mode is None:
            return None
        else:
            pass
        return self._selected_entry, self._selected_mode


class DynamicEditorAddButton(QtWidgets.QToolButton):
    """Corner button serving as add-entry action and reattach drop target."""

    __slots__ = ()

    tabWidgetDropRequested = QtCore.Signal(QtCore.QPoint)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Create the add button and enable it as a tab drop target.

        :param parent: Owning tab widget.
        :return: None.
        """
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("+")
        self.setAutoRaise(True)
        self.setToolTip(self.tr("Open another Dynamic Editor"))

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """
        Refresh the button tooltip after a Qt language change.

        :param event: Incoming Qt change event.
        :return: None.
        """
        QtWidgets.QToolButton.changeEvent(self, event)

        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.setToolTip(self.tr("Open another Dynamic Editor"))
        else:
            pass

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accept drag entry only for Dynamic Editor tabs.

        :param event: Incoming drag event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Keep a compatible tab drag accepted while it crosses the button.

        :param event: Incoming drag-move event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Request tab reattachment when a compatible drop is completed.

        :param event: Incoming drop event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value):
            self.tabWidgetDropRequested.emit(self.mapToGlobal(event.position().toPoint()))
            event.acceptProposedAction()
        else:
            event.ignore()


class DetachableEditorTabBar(QtWidgets.QTabBar):
    """Tab bar supporting detach and reattach drags between workspaces."""

    __slots__ = ()

    detachDragIgnored = QtCore.Signal(QtCore.QPoint)
    tabDropRequested = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Create a non-reordering tab bar with detach support.

        :param parent: Owning tab widget.
        :return: None.
        """
        super().__init__(parent)
        self._drag_start_pos: Optional[QtCore.QPoint] = None
        self._drag_index: int = -1
        self.setAcceptDrops(True)
        self.setExpanding(False)
        self.setMovable(False)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Record the possible origin of a left-button tab drag.

        :param event: Incoming mouse press.
        :return: None.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_index = self.tabAt(event.pos())
        else:
            self._drag_start_pos = None
            self._drag_index = -1

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Start a tab drag after Qt's configured movement threshold.

        :param event: Incoming mouse move.
        :return: None.
        """
        if (
                self._drag_start_pos is None
                or self._drag_index < 0
                or not (event.buttons() & QtCore.Qt.MouseButton.LeftButton)
        ):
            super().mouseMoveEvent(event)
            return
        else:
            pass

        if (event.pos() - self._drag_start_pos).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return
        else:
            pass

        tab_widget = self.parent()
        if isinstance(tab_widget, DetachableEditorTabWidget):
            drag = QtGui.QDrag(self)
            mime = QtCore.QMimeData()
            mime.setData(DynamicEditorMimeType.TAB.value, b"dynamic-editor-tab")
            drag.setMimeData(mime)
            drag.setHotSpot(event.pos() - self.tabRect(self._drag_index).topLeft())
            tab_widget.prepare_tab_drag(self._drag_index)
            result = drag.exec(QtCore.Qt.DropAction.MoveAction)
            tab_widget.finish_tab_drag(result, QtGui.QCursor.pos())
            self._drag_start_pos = None
            self._drag_index = -1
            return
        else:
            super().mouseMoveEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accept drag entry only for Dynamic Editor tabs.

        :param event: Incoming drag event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Keep a compatible tab drag accepted over the tab bar.

        :param event: Incoming drag-move event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Request reattachment at the tab index under the drop.

        :param event: Incoming drop event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value):
            target_index = self.tabAt(event.position().toPoint())
            self.tabDropRequested.emit(self.mapToGlobal(event.position().toPoint()), target_index)
            event.acceptProposedAction()
        else:
            event.ignore()


class DetachableEditorTabWidget(QtWidgets.QTabWidget):
    """Tab widget wrapper used by the Dynamic Editor workspace."""

    __slots__ = ()

    tabDragStarted = QtCore.Signal(int)
    detachRequested = QtCore.Signal(QtCore.QPoint)
    reattachRequested = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Create a tab widget whose pages can move between workspaces.

        :param parent: Owning workspace widget.
        :return: None.
        """
        super().__init__(parent)
        self._tab_bar = DetachableEditorTabBar(self)
        self._pending_drag_index: int = -1
        self.setTabBar(self._tab_bar)
        self.setAcceptDrops(True)
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setMovable(False)
        self._tab_bar.detachDragIgnored.connect(self._on_detach_drag_ignored)
        self._tab_bar.tabDropRequested.connect(self.reattachRequested.emit)

    def prepare_tab_drag(self, index: int) -> None:
        """Record and announce the page that begins a detach drag.

        :param index: Source tab index.
        :return: None.
        """
        self._pending_drag_index = index
        self.tabDragStarted.emit(index)

    def finish_tab_drag(self, result: QtCore.Qt.DropAction, global_pos: QtCore.QPoint) -> None:
        """Complete a tab drag by requesting detachment when no drop consumed it.

        :param result: Qt drag result.
        :param global_pos: Cursor position at drag completion.
        :return: None.
        """
        if self._pending_drag_index < 0:
            return
        else:
            pass

        if result != QtCore.Qt.DropAction.MoveAction:
            self.detachRequested.emit(global_pos)
        else:
            pass

        self._pending_drag_index = -1

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accept compatible drags entering the tab-bar strip.

        :param event: Incoming drag event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value) and event.position().y() <= self.tabBar().height() + 8:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Keep compatible drags accepted while they remain over the tab strip.

        :param event: Incoming drag-move event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value) and event.position().y() <= self.tabBar().height() + 8:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Request reattachment at the tab index under a compatible drop.

        :param event: Incoming drop event.
        :return: None.
        """
        if event.mimeData().hasFormat(DynamicEditorMimeType.TAB.value) and event.position().y() <= self.tabBar().height() + 8:
            target_index = self.tabBar().tabAt(self.tabBar().mapFrom(self, event.position().toPoint()))
            self.reattachRequested.emit(self.mapToGlobal(event.position().toPoint()), target_index)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_detach_drag_ignored(self, global_pos: QtCore.QPoint) -> None:
        """Translate an unconsumed tab-bar drag into a detach request.

        :param global_pos: Cursor position where the drag was ignored.
        :return: None.
        """
        self.detachRequested.emit(global_pos)
