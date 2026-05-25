# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List, Dict, Set

from PySide6 import QtWidgets, QtCore

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.enumerations import DynamicEventTransitionType, DynamicSimulationMode


class EventRow:
    """Encapsulates a row in the RMS/EMT event table."""

    def __init__(self,
                 table,
                 row,
                 parameters_list,
                 events_groups_list,
                 mode: DynamicSimulationMode,
                 mode_parameter_uids: Set[int] | None = None):
        self.table = table
        self.row = row
        self.mode = mode
        self.mode_parameter_uids: Set[int] = set() if mode_parameter_uids is None else set(mode_parameter_uids)

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

        self.transition_combo: QtWidgets.QComboBox | None = None
        self.end_time_spin: QtWidgets.QDoubleSpinBox | None = None

        if self.mode == DynamicSimulationMode.EMT or self.mode == DynamicSimulationMode.RMS:
            self.transition_combo = QtWidgets.QComboBox()
            self.transition_combo.addItem("Step", DynamicEventTransitionType.Step)
            self.transition_combo.addItem("Ramp", DynamicEventTransitionType.Ramp)
            table.setCellWidget(row, 4, self.transition_combo)

            self.end_time_spin = QtWidgets.QDoubleSpinBox()
            self.end_time_spin.setDecimals(4)
            self.end_time_spin.setRange(0.0, 1e9)
            self.end_time_spin.setSingleStep(0.1)
            self.end_time_spin.setSuffix(" s")
            self.end_time_spin.setEnabled(False)
            table.setCellWidget(row, 5, self.end_time_spin)
            self.transition_combo.currentIndexChanged.connect(self.on_transition_changed)
        else:
            pass

        # --- Event group selector ---
        self.group_combo = QtWidgets.QComboBox()
        for group in events_groups_list:
            self.group_combo.addItem(group.name, group)
        if self.mode == DynamicSimulationMode.EMT or self.mode == DynamicSimulationMode.RMS:
            table.setCellWidget(row, 6, self.group_combo)
        else:
            table.setCellWidget(row, 4, self.group_combo)

        self.force_alignment_check: QtWidgets.QCheckBox | None = None
        if self.mode == DynamicSimulationMode.EMT:
            self.force_alignment_check = QtWidgets.QCheckBox()
            self.force_alignment_check.setChecked(False)
            self.force_alignment_check.setEnabled(False)
            table.setCellWidget(row, 7, self.force_alignment_check)
            self.param_combo.currentIndexChanged.connect(self.on_parameter_changed)
            self.on_transition_changed()
            self.on_parameter_changed()
        else:
            pass

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
        transition_type = DynamicEventTransitionType.Step
        end_time = None

        if self.transition_combo is not None:
            transition_data = self.transition_combo.currentData()
            if isinstance(transition_data, DynamicEventTransitionType):
                transition_type = transition_data
            else:
                raise TypeError("transition_type must be DynamicEventTransitionType")
        else:
            pass

        if self.end_time_spin is not None and self.end_time_spin.isEnabled():
            end_time = self.end_time_spin.value()
        else:
            pass

        if self.force_alignment_check is not None:
            force_step_alignment = self.force_alignment_check.isChecked()
        else:
            force_step_alignment = False

        return param, t, end_time, v, group, force_step_alignment, transition_type

    def add_group(self, group):
        """Add a new group option to the combo."""
        self.group_combo.addItem(group.name, group)

    def set_data(self,
                 parameter: Var,
                 target_time: float,
                 value: float,
                 group,
                 force_step_alignment: bool,
                 transition_type: DynamicEventTransitionType,
                 end_time: float | None) -> None:
        """
        Populate the row widgets from explicit event data.

        :param parameter: Target runtime parameter.
        :param target_time: Event start time.
        :param value: New runtime value.
        :param group: Target events group.
        :param force_step_alignment: Exact-alignment flag.
        :param transition_type: Step or ramp transition type.
        :param end_time: Optional ramp end time.
        :return: None.
        """
        param_index: int = self.param_combo.findData(parameter)
        group_index: int = self.group_combo.findData(group)

        if param_index >= 0:
            self.param_combo.setCurrentIndex(param_index)
        else:
            pass

        self.time_spin.setValue(float(target_time))
        self.value_spin.setValue(float(value))

        if group_index >= 0:
            self.group_combo.setCurrentIndex(group_index)
        else:
            pass

        if self.transition_combo is not None:
            transition_index: int = self.transition_combo.findData(transition_type)
            if transition_index >= 0:
                self.transition_combo.setCurrentIndex(transition_index)
            else:
                pass
        else:
            pass

        if self.end_time_spin is not None:
            if end_time is not None:
                self.end_time_spin.setValue(float(end_time))
            else:
                pass
        else:
            pass

        if self.force_alignment_check is not None:
            self.force_alignment_check.setChecked(bool(force_step_alignment))
        else:
            pass

    def on_transition_changed(self) -> None:
        """
        Update EMT-only controls when the selected transition changes.

        :return: None.
        """
        if self.transition_combo is None or self.end_time_spin is None:
            return
        else:
            pass

        if self.transition_combo.currentData() == DynamicEventTransitionType.Ramp:
            self.end_time_spin.setEnabled(True)
        else:
            self.end_time_spin.setEnabled(False)

    def on_parameter_changed(self) -> None:
        """
        Update EMT-only controls when the selected parameter changes.

        :return: None.
        """
        selected_param = self.param_combo.currentData()

        if self.force_alignment_check is None:
            return
        else:
            pass

        if isinstance(selected_param, Var) and selected_param.uid in self.mode_parameter_uids:
            self.force_alignment_check.setEnabled(True)
            self.force_alignment_check.setChecked(True)
        else:
            self.force_alignment_check.setChecked(False)
            self.force_alignment_check.setEnabled(False)


def collect_block_runtime_event_parameters(block: Block) -> tuple[List[Var], Set[int]]:
    """
    Collect all runtime event and mode parameters from a block hierarchy.

    :param block: Root symbolic block.
    :return: Ordered parameter list plus the mode-parameter UID set.
    """
    parameters: List[Var] = list()
    mode_parameter_uids: Set[int] = set()
    seen_uids: Set[int] = set()
    block_obj: Block
    parameter: Var

    for block_obj in block.get_all_blocks():
        for parameter in block_obj.event_dict.keys():
            if parameter.uid not in seen_uids:
                seen_uids.add(parameter.uid)
                parameters.append(parameter)
            else:
                pass

        for parameter in block_obj.mode_dict.keys():
            mode_parameter_uids.add(parameter.uid)

            if parameter.uid not in seen_uids:
                seen_uids.add(parameter.uid)
                parameters.append(parameter)
            else:
                pass

    return parameters, mode_parameter_uids


class SwitchSequenceRow:
    """
    Encapsulates one row in the switch sequence helper dialog.
    """

    def __init__(self, table: QtWidgets.QTableWidget, row: int) -> None:
        self.table = table
        self.row = row

        checkbox = QtWidgets.QTableWidgetItem()
        checkbox.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
        checkbox.setCheckState(QtCore.Qt.CheckState.Unchecked)
        table.setItem(row, 0, checkbox)

        self.time_spin = QtWidgets.QDoubleSpinBox()
        self.time_spin.setDecimals(4)
        self.time_spin.setRange(0.0, 1e9)
        self.time_spin.setSingleStep(0.1)
        self.time_spin.setSuffix(" s")
        table.setCellWidget(row, 1, self.time_spin)

        self.state_combo = QtWidgets.QComboBox()
        self.state_combo.addItem("Open", 0.0)
        self.state_combo.addItem("Close", 1.0)
        table.setCellWidget(row, 2, self.state_combo)

    def is_checked(self) -> bool:
        item = self.table.item(self.row, 0)
        return bool(item and item.checkState() == QtCore.Qt.CheckState.Checked)

    def get_data(self) -> tuple[float, float]:
        return float(self.time_spin.value()), float(self.state_combo.currentData())

    def set_data(self, target_time: float, state_value: float) -> None:
        self.time_spin.setValue(float(target_time))
        state_index: int = self.state_combo.findData(float(state_value))
        if state_index >= 0:
            self.state_combo.setCurrentIndex(state_index)
        else:
            pass


class SwitchSequenceDialog(QtWidgets.QDialog):
    """
    Helper dialog that expands one switch opening and reclosing plan into EMT event rows.
    """

    def __init__(self,
                 mode_parameters: List[Var],
                 events_groups: List[EmtEventsGroup],
                 parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Switch Sequence Wizard")
        self.setMinimumWidth(520)
        self.mode_parameters = mode_parameters
        self.events_groups = events_groups
        self.rows: List[SwitchSequenceRow] = list()
        self.data: Dict[str, object] = dict()

        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()
        layout.addLayout(form_layout)

        self.parameter_combo = QtWidgets.QComboBox()
        for parameter in mode_parameters:
            self.parameter_combo.addItem(parameter.name, parameter)
        form_layout.addRow("Mode Parameter", self.parameter_combo)

        self.group_combo = QtWidgets.QComboBox()
        for group in events_groups:
            self.group_combo.addItem(group.name, group)
        form_layout.addRow("Group", self.group_combo)

        self.sequence_table = QtWidgets.QTableWidget(0, 3)
        self.sequence_table.setHorizontalHeaderLabels(["", "Time", "State"])
        self.sequence_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.sequence_table.horizontalHeader().setStretchLastSection(True)
        self.sequence_table.verticalHeader().setVisible(False)
        self.sequence_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.sequence_table)

        buttons_layout = QtWidgets.QHBoxLayout()
        self.add_row_btn = QtWidgets.QPushButton("Add Sequence Step")
        self.remove_row_btn = QtWidgets.QPushButton("Remove Selected Rows")
        buttons_layout.addWidget(self.add_row_btn)
        buttons_layout.addWidget(self.remove_row_btn)
        layout.addLayout(buttons_layout)

        dialog_buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        layout.addWidget(dialog_buttons)

        self.add_row_btn.clicked.connect(self.add_row)
        self.remove_row_btn.clicked.connect(self.remove_checked_rows)
        dialog_buttons.accepted.connect(self.accept_dialog)
        dialog_buttons.rejected.connect(self.reject)

        self.add_row()

    def add_row(self) -> None:
        row_index = self.sequence_table.rowCount()
        self.sequence_table.insertRow(row_index)
        row = SwitchSequenceRow(self.sequence_table, row_index)
        self.rows.append(row)

    def remove_checked_rows(self) -> None:
        rows_to_remove = [row for row in self.rows if row.is_checked()]

        if len(rows_to_remove) == 0:
            QtWidgets.QMessageBox.information(self, "Switch Sequence", "Please check at least one row to remove.")
        else:
            for row in reversed(rows_to_remove):
                self.sequence_table.removeRow(row.row)
                self.rows.remove(row)

            for index, row in enumerate(self.rows):
                row.row = index

    def accept_dialog(self) -> None:
        parameter = self.parameter_combo.currentData()
        group = self.group_combo.currentData()
        times: list[float] = list()
        values: list[float] = list()
        row: SwitchSequenceRow

        if parameter is None or group is None:
            QtWidgets.QMessageBox.warning(self, "Switch Sequence", "Select a mode parameter and an events group.")
            return
        else:
            pass

        if len(self.rows) == 0:
            QtWidgets.QMessageBox.warning(self, "Switch Sequence", "Add at least one sequence row.")
            return
        else:
            pass

        for row in self.rows:
            target_time, state_value = row.get_data()
            times.append(target_time)
            values.append(state_value)

        sorted_pairs = sorted(zip(times, values), key=lambda item: float(item[0]))
        self.data = dict({
            "parameter": parameter,
            "group": group,
            "times": [float(item[0]) for item in sorted_pairs],
            "values": [float(item[1]) for item in sorted_pairs],
        })
        self.accept()

    def get_data(self) -> Dict[str, object]:
        return self.data

class DynamicEventDialogue(QtWidgets.QDialog):

    def __init__(
        self,
        circuit: MultiCircuit,
        parameters_list: List[Var],
        target_device_name: str,
        mode: DynamicSimulationMode,
        mode_parameter_uids: Set[int] | None = None,
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
        self.mode_parameter_uids: Set[int] = set() if mode_parameter_uids is None else set(mode_parameter_uids)

        self.rows: List[EventRow] = []

        self.data = {
            "parameters": [],
            "target_times": [],
            "end_times": [],
            "values": [],
            "groups": [],
            "force_step_alignment": [],
            "transition_types": [],
        }

        # ---- Main Layout ----
        layout = QtWidgets.QVBoxLayout(self)

        # --- Device label ---
        label_device = QtWidgets.QLabel(
            f"<b>Target device:</b> {target_device_name}"
        )
        layout.addWidget(label_device)

        # --- Events Table ---
        if self.mode == DynamicSimulationMode.EMT or self.mode == DynamicSimulationMode.RMS:
            self.table = QtWidgets.QTableWidget(0, 8)
            self.table.setHorizontalHeaderLabels(
                ["", "Parameter", "Time", "New Value", "Transition", "End Time", "Group", "Align Step"]
            )
        else:
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

        self.switch_sequence_btn: QtWidgets.QPushButton | None = None
        if self.mode == DynamicSimulationMode.EMT:
            self.switch_sequence_btn = QtWidgets.QPushButton("Switch Sequence Wizard")
            layout.addWidget(self.switch_sequence_btn)
        else:
            pass

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

        if self.switch_sequence_btn is not None:
            self.switch_sequence_btn.clicked.connect(self.open_switch_sequence_dialog)
        else:
            pass

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
                self.mode,
                self.mode_parameter_uids,
            )
            self.rows.append(row)
            return row

        elif self.mode == DynamicSimulationMode.EMT:

            row = EventRow(
                self.table,
                row_index,
                self.parameters_list,
                self.circuit.emt_events_groups,
                self.mode,
                self.mode_parameter_uids,
            )
            self.rows.append(row)
            return row
        else:
            return None

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
        """
        Open the shared RMS/EMT events-group creation workflow.

        :return: None.
        """
        missing_group_message: str
        created_group_message_title: str
        created_group_message_body_prefix: str = "New group name"

        if self.mode == DynamicSimulationMode.RMS:
            missing_group_message = "No RMS Events Group found, please create one before adding an event."
            created_group_message_title = "RMS group Created"
        else:
            missing_group_message = "No EMT Events Group found, please create one before adding an event."
            created_group_message_title = "EMT group Created"

        new_group: RmsEventsGroup | EmtEventsGroup | None = create_dynamic_events_group_with_dialog(
            circuit=self.circuit,
            mode=self.mode,
            parent=self,
            missing_group_message=missing_group_message,
            created_group_message_title=created_group_message_title,
            created_group_message_body_prefix=created_group_message_body_prefix,
        )

        if new_group is not None:
            row: EventRow
            for row in self.rows:
                row.add_group(new_group)
        else:
            pass

    def open_switch_sequence_dialog(self) -> None:
        """
        Open the helper dialog that expands one switch open/close sequence into EMT event rows.

        :return: None.
        """
        mode_parameters: list[Var] = list()
        parameter: Var

        for parameter in self.parameters_list:
            if parameter.uid in self.mode_parameter_uids and parameter.name.startswith("switch_closed_mode_"):
                mode_parameters.append(parameter)
            else:
                pass

        if len(mode_parameters) == 0:
            QtWidgets.QMessageBox.information(
                self,
                "Switch Sequence",
                "No switch EMT mode parameter is available in this device.",
            )
            return
        else:
            pass

        dialog = SwitchSequenceDialog(mode_parameters=mode_parameters,
                                      events_groups=self.circuit.emt_events_groups,
                                      parent=self)

        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sequence_data = dialog.get_data()
        else:
            return

        index: int
        for index in range(len(sequence_data["times"])):
            row = self.add_row()
            if row is not None:
                row.set_data(
                    parameter=sequence_data["parameter"],
                    target_time=float(sequence_data["times"][index]),
                    value=float(sequence_data["values"][index]),
                    group=sequence_data["group"],
                    force_step_alignment=True,
                    transition_type=DynamicEventTransitionType.Step,
                    end_time=None,
                )
            else:
                pass

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
        end_times = []
        values = []
        groups = []
        force_step_alignment_flags = []
        transition_types = []

        for i, row in enumerate(self.rows):

            try:
                param, t, end_time, v, group, force_step_alignment, transition_type = row.get_data()

            except Exception as exc:

                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid Input",
                    f"Row {i + 1}: {exc}",
                )
                return

            parameters.append(param)
            target_times.append(t)
            end_times.append(end_time)
            values.append(v)
            groups.append(group)
            force_step_alignment_flags.append(force_step_alignment)
            transition_types.append(transition_type)
        self.data["parameters"] = parameters
        self.data["target_times"] = target_times
        self.data["end_times"] = end_times
        self.data["values"] = values
        self.data["groups"] = groups
        self.data["force_step_alignment"] = force_step_alignment_flags
        self.data["transition_types"] = transition_types
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




