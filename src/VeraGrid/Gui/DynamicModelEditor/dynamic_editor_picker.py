from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_picker_dialog import Ui_DynamicEditorPickerDialog
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_support import DynamicEditorEntry
from VeraGridEngine.enumerations import DynamicSimulationMode


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
        self.ui = Ui_DynamicEditorPickerDialog()
        self.ui.setupUi(self)

        self._entries: list[DynamicEditorEntry] = entries
        self._filtered_entries: list[DynamicEditorEntry] = list(entries)
        self._selected_entry: DynamicEditorEntry | None = None
        self._selected_mode: DynamicSimulationMode | None = None
        self._quick_entry: DynamicEditorEntry | None = current_entry
        self._quick_mode: DynamicSimulationMode | None = None

        self.ui.entriesTableWidget.horizontalHeader().setStretchLastSection(True)
        self.ui.entriesTableWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ui.entriesTableWidget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.ui.entriesTableWidget.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.ui.entriesTableWidget.verticalHeader().setVisible(False)

        self.ui.searchLineEdit.textChanged.connect(self._apply_filter)
        self.ui.entriesTableWidget.itemSelectionChanged.connect(self._on_selection_changed)
        self.ui.entriesTableWidget.itemDoubleClicked.connect(self._accept_selected_entry)
        self.ui.modeComboBox.currentIndexChanged.connect(self._on_mode_changed)
        self.ui.quickOpenButton.clicked.connect(self._accept_quick_open)
        self.ui.buttonBox.accepted.connect(self._accept_selected_entry)
        self.ui.buttonBox.rejected.connect(self.reject)

        self._configure_quick_open(current_entry=current_entry, current_mode=current_mode)
        self._apply_filter("")

    def _configure_quick_open(self,
                              current_entry: DynamicEditorEntry | None,
                              current_mode: DynamicSimulationMode | None) -> None:
        if current_entry is None or current_mode is None:
            self.ui.quickOpenGroupBox.setVisible(False)
            return

        alternate_modes = [mode for mode in current_entry.available_modes if mode != current_mode]
        if len(alternate_modes) == 0:
            self.ui.quickOpenGroupBox.setVisible(False)
            return

        self._quick_mode = alternate_modes[0]
        self.ui.quickOpenGroupBox.setVisible(True)
        self.ui.quickOpenLabel.setText(f"Open the current block in {self._quick_mode.name}.")
        self.ui.quickOpenButton.setText(f"Open {self._quick_mode.name}")

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

        self.ui.entriesTableWidget.setRowCount(len(self._filtered_entries))
        for row, entry in enumerate(self._filtered_entries):
            self.ui.entriesTableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(entry.display_name))
            self.ui.entriesTableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(entry.type_label))
            self.ui.entriesTableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(" / ".join(mode.name for mode in entry.available_modes)))

        if len(self._filtered_entries) > 0:
            self.ui.entriesTableWidget.selectRow(0)
        else:
            self._selected_entry = None
            self._selected_mode = None
            self.ui.modeComboBox.clear()

    def _on_selection_changed(self) -> None:
        current_row = self.ui.entriesTableWidget.currentRow()
        if current_row < 0 or current_row >= len(self._filtered_entries):
            self._selected_entry = None
            self._selected_mode = None
            self.ui.modeComboBox.clear()
            return

        self._selected_entry = self._filtered_entries[current_row]
        self.ui.modeComboBox.blockSignals(True)
        self.ui.modeComboBox.clear()
        for mode in self._selected_entry.available_modes:
            self.ui.modeComboBox.addItem(mode.name, mode)
        self.ui.modeComboBox.blockSignals(False)

        if self.ui.modeComboBox.count() > 0:
            self._selected_mode = self.ui.modeComboBox.currentData(QtCore.Qt.ItemDataRole.UserRole)
        else:
            self._selected_mode = None

    def _on_mode_changed(self, _index: int) -> None:
        self._selected_mode = self.ui.modeComboBox.currentData(QtCore.Qt.ItemDataRole.UserRole)

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
