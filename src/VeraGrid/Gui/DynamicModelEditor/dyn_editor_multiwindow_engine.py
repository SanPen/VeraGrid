# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any, Iterable
from itertools import chain
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialogButtonBox,
                             QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                             QTableWidget, QTableWidgetItem, QVBoxLayout)
from typing import Optional
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode, FmuTemplateDomain



DYNAMIC_EDITOR_TAB_MIME: str = "application/x-veragrid-dynamic-editor-tab"



def get_available_dynamic_modes(api_object: Any) -> tuple[DynamicSimulationMode, ...]:
    """
    Return the modes that can be opened for one API object.
    """
    modes: list[DynamicSimulationMode] = list()

    device_type = api_object.device_type

    if device_type == DeviceType.RmsModelTemplateDevice:
        return (DynamicSimulationMode.RMS,)
    if device_type == DeviceType.EmtModelTemplateDevice:
        return (DynamicSimulationMode.EMT,)

    try:
        if api_object.rms_model is not None:
            modes.append(DynamicSimulationMode.RMS)
        if api_object.emt_model is not None:
            modes.append(DynamicSimulationMode.EMT)
    except:
        pass

    return tuple(modes)


def build_dynamic_editor_title(api_object: Any, mode: DynamicSimulationMode) -> str:
    """
    Build the tab/window title for one dynamic editor session.
    """

    return f"{api_object.name} [{mode.name}]"


def build_dynamic_editor_entry(api_object: Any, circuit: Any) -> DynamicEditorEntry | None:
    """
    Build one dynamic editor picker entry or return None when the object has no dynamic editor.
    """

    available_modes = get_available_dynamic_modes(api_object)
    if len(available_modes) == 0:
        return None

    if isinstance(api_object, EditableDevice):
        key_base = f"{api_object.device_type.value}:{api_object.idtag}"
        type_label = str(api_object.device_type.value)
        display_name = api_object.name
    else:
        key_base = f"dynamic-object:{id(api_object)}"
        type_label = type(api_object).__name__
        display_name = api_object.name

    return DynamicEditorEntry(
        api_object=api_object,
        circuit=circuit,
        available_modes=available_modes,
        display_name=display_name,
        type_label=type_label,
        key_base=key_base,
    )


def iter_dynamic_editor_entries(circuit: Any) -> Iterable[DynamicEditorEntry]:
    """
    Yield every circuit object that can be opened in the unified Dynamic Editor.
    """

    seen_keys: set[str] = set()
    api_object: Any
    for api_object in chain(circuit.get_injection_devices(), circuit.get_branches()):
        entry = build_dynamic_editor_entry(api_object, circuit)
        if entry is None or entry.key_base in seen_keys:
            continue
        seen_keys.add(entry.key_base)
        yield entry


def get_templates_for_entry(entry: DynamicEditorEntry, mode: DynamicSimulationMode) -> list[Any]:
    """
    Return the template list that should be exposed in the editor library for one entry.
    """

    api_object = entry.api_object
    device_type = api_object.device_type

    if device_type == DeviceType.RmsModelTemplateDevice:
        return list(entry.circuit.get_dynamic_templates_by_domain(FmuTemplateDomain.RMS))
    if device_type == DeviceType.EmtModelTemplateDevice:
        return list(entry.circuit.get_dynamic_templates_by_domain(FmuTemplateDomain.EMT))

    if mode == DynamicSimulationMode.RMS:
        return list(entry.circuit.get_rms_models_by_device_type(api_object.device_type))
    else:
        return list(entry.circuit.get_emt_models_by_device_type(api_object.device_type))


def get_block_for_entry(entry: DynamicEditorEntry, mode: DynamicSimulationMode):
    """
    Return the block edited by one entry and mode.
    """

    api_object = entry.api_object
    device_type = api_object.device_type

    if device_type in {DeviceType.RmsModelTemplateDevice, DeviceType.EmtModelTemplateDevice}:
        return api_object.block
    if mode == DynamicSimulationMode.RMS:
        return api_object.rms_model
    else:
        return api_object.emt_model

class DynamicEditorEntry:
    """
    One selectable/openable Dynamic Editor entry.
    """

    def __init__(self,
                 api_object: Any,
                 circuit: Any,
                 available_modes: tuple[DynamicSimulationMode, ...],
                 display_name: str,
                 type_label: str,
                 key_base: str) -> None:
        self.api_object = api_object
        self.circuit = circuit
        self.available_modes = available_modes
        self.display_name = display_name
        self.type_label = type_label
        self.key_base = key_base

    def session_key(self, mode: DynamicSimulationMode) -> str:
        return f"{self.key_base}:{mode.name}"


class DynamicEditorPickerDialog(QtWidgets.QDialog):
    """
    Modal dialog used by the workspace `+` button to open another dynamic editor.
    """

    def __init__(self,
                 entries: list[DynamicEditorEntry],
                 current_entry: DynamicEditorEntry | None = None,
                 current_mode: DynamicSimulationMode | None = None,
                 parent: QtWidgets.QWidget | None = None) -> None:
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
        self.quickOpenGroupBox.setTitle("Quick Open")
        self.horizontalLayoutQuick = QHBoxLayout(self.quickOpenGroupBox)

        self.quickOpenLabel = QLabel("Open the current block in the other mode.", self.quickOpenGroupBox)
        self.quickOpenLabel.setWordWrap(True)
        self.horizontalLayoutQuick.addWidget(self.quickOpenLabel)

        self.quickOpenButton = QPushButton("Open", self.quickOpenGroupBox)
        self.horizontalLayoutQuick.addWidget(self.quickOpenButton)

        self.verticalLayout.addWidget(self.quickOpenGroupBox)

        self.searchLineEdit = QLineEdit(self)
        self.searchLineEdit.setPlaceholderText("Search dynamic editors")
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

        for col, text in enumerate(["Name", "Type", "Modes"]):
            self.entriesTableWidget.setHorizontalHeaderItem(col, QTableWidgetItem(text))

        self.verticalLayout.addWidget(self.entriesTableWidget)

        self.horizontalLayoutMode = QHBoxLayout()

        self.modeLabel = QLabel("Mode", self)
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

    def _configure_quick_open(self,
                              current_entry: DynamicEditorEntry | None,
                              current_mode: DynamicSimulationMode | None) -> None:
        if current_entry is None or current_mode is None:
            self.quickOpenGroupBox.setVisible(False)
            return

        alternate_modes = [mode for mode in current_entry.available_modes if mode != current_mode]
        if len(alternate_modes) == 0:
            self.quickOpenGroupBox.setVisible(False)
            return

        self._quick_mode = alternate_modes[0]
        self.quickOpenGroupBox.setVisible(True)
        self.quickOpenLabel.setText(f"Open the current block in {self._quick_mode.name}.")
        self.quickOpenButton.setText(f"Open {self._quick_mode.name}")

    def _apply_filter(self, text: str) -> None:
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
            self.entriesTableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(" / ".join(mode.name for mode in entry.available_modes)))

        if len(self._filtered_entries) > 0:
            self.entriesTableWidget.selectRow(0)
        else:
            self._selected_entry = None
            self._selected_mode = None
            self.modeComboBox.clear()

    def _on_selection_changed(self) -> None:
        current_row = self.entriesTableWidget.currentRow()
        if current_row < 0 or current_row >= len(self._filtered_entries):
            self._selected_entry = None
            self._selected_mode = None
            self.modeComboBox.clear()
            return

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
        self._selected_mode = self.modeComboBox.currentData(QtCore.Qt.ItemDataRole.UserRole)

    def _accept_quick_open(self) -> None:
        if self._quick_entry is None or self._quick_mode is None:
            return

        self._selected_entry = self._quick_entry
        self._selected_mode = self._quick_mode
        self.accept()

    def _accept_selected_entry(self) -> None:
        if self._selected_entry is None or self._selected_mode is None:
            return
        self.accept()

    def get_selection(self) -> tuple[DynamicEditorEntry, DynamicSimulationMode] | None:
        if self._selected_entry is None or self._selected_mode is None:
            return None
        return self._selected_entry, self._selected_mode



class DynamicEditorAddButton(QtWidgets.QToolButton):
    """
    Corner button used as both the add-entry action and a reattach drop target.
    """

    tabWidgetDropRequested = QtCore.Signal(QtCore.QPoint)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("+")
        self.setAutoRaise(True)
        self.setToolTip("Open another Dynamic Editor")

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            self.tabWidgetDropRequested.emit(self.mapToGlobal(event.position().toPoint()))
            event.acceptProposedAction()
        else:
            event.ignore()


class DetachableEditorTabBar(QtWidgets.QTabBar):
    """
    Tab bar that supports drag-out detach and drag-in reattach between workspaces.
    """

    detachDragIgnored = QtCore.Signal(QtCore.QPoint)
    tabDropRequested = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_start_pos: Optional[QtCore.QPoint] = None
        self._drag_index: int = -1
        self.setAcceptDrops(True)
        self.setExpanding(False)
        self.setMovable(False)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_index = self.tabAt(event.pos())
        else:
            self._drag_start_pos = None
            self._drag_index = -1

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if (
            self._drag_start_pos is None
            or self._drag_index < 0
            or not (event.buttons() & QtCore.Qt.MouseButton.LeftButton)
        ):
            super().mouseMoveEvent(event)
            return

        if (event.pos() - self._drag_start_pos).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        tab_widget = self.parent()
        if isinstance(tab_widget, DetachableEditorTabWidget):
            drag = QtGui.QDrag(self)
            mime = QtCore.QMimeData()
            mime.setData(DYNAMIC_EDITOR_TAB_MIME, b"dynamic-editor-tab")
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
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            target_index = self.tabAt(event.position().toPoint())
            self.tabDropRequested.emit(self.mapToGlobal(event.position().toPoint()), target_index)
            event.acceptProposedAction()
        else:
            event.ignore()


class DetachableEditorTabWidget(QtWidgets.QTabWidget):
    """
    QTabWidget wrapper used by the Dynamic Editor workspace.
    """

    tabDragStarted = QtCore.Signal(int)
    detachRequested = QtCore.Signal(QtCore.QPoint)
    reattachRequested = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
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
        self._pending_drag_index = index
        self.tabDragStarted.emit(index)

    def finish_tab_drag(self, result: QtCore.Qt.DropAction, global_pos: QtCore.QPoint) -> None:
        if self._pending_drag_index < 0:
            return

        if result != QtCore.Qt.DropAction.MoveAction:
            self.detachRequested.emit(global_pos)
        else:
            pass

        self._pending_drag_index = -1

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME) and event.position().y() <= self.tabBar().height() + 8:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME) and event.position().y() <= self.tabBar().height() + 8:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME) and event.position().y() <= self.tabBar().height() + 8:
            target_index = self.tabBar().tabAt(self.tabBar().mapFrom(self, event.position().toPoint()))
            self.reattachRequested.emit(self.mapToGlobal(event.position().toPoint()), target_index)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_detach_drag_ignored(self, global_pos: QtCore.QPoint) -> None:
        self.detachRequested.emit(global_pos)
