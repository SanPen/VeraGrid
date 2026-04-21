# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List, Dict

from PySide6 import QtWidgets, QtCore

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.enumerations import DynamicSimulationMode


class EventRow:
    """Encapsulates a row in the RMS/EMT event table."""

    def __init__(self, table, row, parameters_list, events_groups_list):
        self.table = table
        self.row = row

        # --- Checkbox ---
        checkbox = QtWidgets.QTableWidgetItem()
        checkbox.setFlags(
            QtCore.Qt.ItemFlag.ItemIsUserCheckable |
            QtCore.Qt.ItemFlag.ItemIsEnabled
        )
        checkbox.setCheckState(QtCore.Qt.CheckState.Unchecked)
        table.setItem(row, 0, checkbox)

        # --- Parameter selector ---
        self.param_combo = QtWidgets.QComboBox()
        for var in parameters_list:
            self.param_combo.addItem(var.name, var)
        table.setCellWidget(row, 1, self.param_combo)

        # --- Time spinbox ---
        self.time_spin = QtWidgets.QDoubleSpinBox()
        self.time_spin.setDecimals(4)
        self.time_spin.setRange(0.0, 1e9)
        self.time_spin.setSingleStep(0.1)
        self.time_spin.setSuffix(" s")
        table.setCellWidget(row, 2, self.time_spin)

        # --- Value spinbox ---
        self.value_spin = QtWidgets.QDoubleSpinBox()
        self.value_spin.setDecimals(6)
        self.value_spin.setRange(-1e9, 1e9)
        self.value_spin.setSingleStep(0.01)
        table.setCellWidget(row, 3, self.value_spin)

        # --- Event group selector ---
        self.group_combo = QtWidgets.QComboBox()
        for group in events_groups_list:
            self.group_combo.addItem(group.name, group)
        table.setCellWidget(row, 4, self.group_combo)

    def is_checked(self):
        item = self.table.item(self.row, 0)
        return item and item.checkState() == QtCore.Qt.CheckState.Checked

    def get_data(self):
        """Return validated row data."""
        param = self.param_combo.currentData()
        group = self.group_combo.currentData()

        if param is None or group is None:
            raise ValueError("Missing fields")

        t = self.time_spin.value()
        v = self.value_spin.value()

        return param, t, v, group

    def add_group(self, group):
        """Add a new group option to the combo."""
        self.group_combo.addItem(group.name, group)

class DynamicEventDialogue(QtWidgets.QDialog):

    def __init__(
        self,
        circuit: MultiCircuit,
        parameters_list: List[Var],
        target_device_name: str,
        mode: DynamicSimulationMode,
        parent=None,
    ):
        super().__init__(parent)

        self.mode = mode

        if self.mode == DynamicSimulationMode.RMS:
            self.setWindowTitle("RMS Event Editor")
        elif self.mode == DynamicSimulationMode.EMT:
            self.setWindowTitle("EMT Event Editor")
        self.setMinimumWidth(600)

        self.circuit = circuit
        self.parameters_list = parameters_list
        self.target_device_name = target_device_name

        self.rows: List[EventRow] = []

        self.data = {
            "parameters": [],
            "target_times": [],
            "values": [],
            "groups": [],
        }

        # ---- Main Layout ----
        layout = QtWidgets.QVBoxLayout(self)

        # --- Device label ---
        label_device = QtWidgets.QLabel(
            f"<b>Target device:</b> {target_device_name}"
        )
        layout.addWidget(label_device)

        # --- Events Table ---
        self.table = QtWidgets.QTableWidget(0, 5)

        self.table.setHorizontalHeaderLabels(
            ["", "Parameter", "Time", "New Value", "Group"]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection
        )

        layout.addWidget(self.table)

        # --- Groups controls ---
        groups_layout = QtWidgets.QHBoxLayout()

        self.new_group_btn = QtWidgets.QPushButton("➕ New Event Group")

        groups_layout.addStretch()
        groups_layout.addWidget(self.new_group_btn)

        layout.addLayout(groups_layout)


        # --- Table control buttons ---
        table_button_layout = QtWidgets.QHBoxLayout()

        self.add_row_btn = QtWidgets.QPushButton("➕ Add New Event")
        self.remove_row_btn = QtWidgets.QPushButton("❌ Remove Selected Rows")

        table_button_layout.addWidget(self.add_row_btn)
        table_button_layout.addWidget(self.remove_row_btn)

        layout.addLayout(table_button_layout)

        # --- Bottom buttons ---
        button_layout = QtWidgets.QHBoxLayout()

        self.ok_button = QtWidgets.QPushButton("✅ Add Events")
        self.cancel_button = QtWidgets.QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # --- Connections ---
        self.add_row_btn.clicked.connect(self.add_row)
        self.remove_row_btn.clicked.connect(self.remove_checked_rows)
        self.ok_button.clicked.connect(self.accept_dialog)
        self.cancel_button.clicked.connect(self.reject)
        self.new_group_btn.clicked.connect(self.create_event_group)

    def add_row(self):
        """Add a new row to the table."""
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)

        if self.mode == DynamicSimulationMode.RMS:

            row = EventRow(
                self.table,
                row_index,
                self.parameters_list,
                self.circuit.rms_events_groups,
            )
            self.rows.append(row)

        elif self.mode == DynamicSimulationMode.EMT:

            row = EventRow(
                self.table,
                row_index,
                self.parameters_list,
                self.circuit.emt_events_groups,
            )
            self.rows.append(row)

    def remove_checked_rows(self):
        """Remove rows where checkbox is checked."""

        rows_to_remove = [r for r in self.rows if r.is_checked()]

        if not rows_to_remove:
            QtWidgets.QMessageBox.information(
                self,
                "No Rows Selected",
                "Please check at least one row to remove.",
            )
            return

        for row in reversed(rows_to_remove):
            self.table.removeRow(row.row)
            self.rows.remove(row)

        # Reindex rows
        for i, row in enumerate(self.rows):
            row.row = i

    def create_event_group(self):
        """Open dialog to create a new RMS/EMT events group."""

        dialog = DynamicEventsGroupsDialog(parent=self,
                                           mode=self.mode)

        if dialog.exec():
            name = dialog.get_name()

            # create and add new Rms Events Group
            if self.mode == DynamicSimulationMode.RMS:
                new_group = RmsEventsGroup(idtag=None, name=name)
                self.circuit.add_rms_events_group(new_group)
                # update event rows
                for row in self.rows:
                    row.add_group(new_group)

                QtWidgets.QMessageBox.information(
                    self,
                    "RMS group Created",
                    f"New group name: {name}"
                )

            # create and add new Emt Events Group
            elif self.mode == DynamicSimulationMode.EMT:
                new_group = EmtEventsGroup(idtag=None, name=name)
                self.circuit.add_emt_events_group(new_group)

                # update event rows
                for row in self.rows:
                    row.add_group(new_group)

                QtWidgets.QMessageBox.information(
                    self,
                    "EMT group Created",
                    f"New group name: {name}"
                )

    def accept_dialog(self):
        """Validate and collect event data."""

        if not self.rows:
            QtWidgets.QMessageBox.warning(
                self,
                "No Events",
                "Please add at least one event before confirming.",
            )
            return

        parameters = []
        target_times = []
        values = []
        groups = []

        for i, row in enumerate(self.rows):

            try:
                param, t, v, group = row.get_data()

            except Exception as exc:

                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid Input",
                    f"Row {i + 1}: {exc}",
                )
                return

            parameters.append(param)
            target_times.append(t)
            values.append(v)
            groups.append(group)
        self.data["parameters"] = parameters
        self.data["target_times"] = target_times
        self.data["values"] = values
        self.data["groups"] = groups
        self.accept()

    def get_data(self) -> Dict[str, List]:
        """Return collected data."""
        return self.data

class DynamicEventsGroupsDialog(QtWidgets.QDialog):

    def __init__(self,
                 mode: DynamicSimulationMode,
                 parent=None):
        super().__init__(parent)

        self.mode = mode
        if self.mode == DynamicSimulationMode.RMS:
            self.setWindowTitle("Create RMS Events Group")
        elif self.mode == DynamicSimulationMode.EMT:
            self.setWindowTitle("Create EMT Events Group")
        self.setModal(True)
        self.setMinimumWidth(300)

        self._name: str|None = None

        # Widgets
        self.name_label = QtWidgets.QLabel("Name:")
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Enter group name")

        # Buttons
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        # Layout
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.name_label, self.name_edit)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.buttons)

        # Connections
        self.buttons.accepted.connect(self.accept_dialog)
        self.buttons.rejected.connect(self.reject)
        self.name_edit.returnPressed.connect(self.accept_dialog)

    def accept_dialog(self):
        """
        Validate the input and store the name
        """
        name = self.name_edit.text().strip()

        if not name:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid name",
                "The name cannot be empty."
            )
            return

        self._name = name
        self.accept()

    def get_name(self) -> str:
        """
        Returns the entered name
        """
        return self._name




