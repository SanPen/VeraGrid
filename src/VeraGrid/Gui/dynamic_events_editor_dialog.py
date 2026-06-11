# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List, Dict, Set, Sequence

from PySide6 import QtWidgets, QtCore

from VeraGrid.Gui.messages import info_msg

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.emt_event import EmtEvent
from VeraGridEngine.enumerations import DynamicEventTransitionType, DynamicSimulationMode


EVENT_TIME_TOLERANCE: float = 1.0e-9


class EventValidationEntry:
    """
    Normalized dynamic-event entry used by overlap validation.
    """

    __slots__ = (
        "parameter",
        "start_time",
        "end_time",
        "value",
        "group",
        "transition_type",
        "origin",
    )

    def __init__(self,
                 parameter: Var,
                 start_time: float,
                 end_time: float,
                 value: float,
                 group: RmsEventsGroup | EmtEventsGroup,
                 transition_type: DynamicEventTransitionType,
                 origin: str) -> None:
        """
        Build one normalized validation entry.

        :param parameter: Target runtime parameter.
        :param start_time: Event start time.
        :param end_time: Event end time after step/ramp normalization.
        :param value: Target value applied by the event.
        :param group: Event group that contains the event.
        :param transition_type: Transition profile.
        :param origin: Human-readable origin used in validation messages.
        :return: None.
        """
        self.parameter: Var = parameter
        self.start_time: float = float(start_time)
        self.end_time: float = float(end_time)
        self.value: float = float(value)
        self.group: RmsEventsGroup | EmtEventsGroup = group
        self.transition_type: DynamicEventTransitionType = transition_type
        self.origin: str = origin


class EventValidationConflict:
    """
    Pair of normalized events that overlap in time.
    """

    __slots__ = (
        "group",
        "first_event",
        "second_event",
    )

    def __init__(self,
                 group: RmsEventsGroup | EmtEventsGroup,
                 first_event: EventValidationEntry,
                 second_event: EventValidationEntry) -> None:
        """
        Build one validation conflict.

        :param group: Group that contains the conflicting events.
        :param first_event: First conflicting event.
        :param second_event: Second conflicting event.
        :return: None.
        """
        self.group: RmsEventsGroup | EmtEventsGroup = group
        self.first_event: EventValidationEntry = first_event
        self.second_event: EventValidationEntry = second_event


def _normalize_event_interval(start_time: float,
                              end_time: float | None,
                              transition_type: DynamicEventTransitionType) -> tuple[float, float]:
    """
    Normalize one event into an explicit occupied time interval.

    The overlap algorithm works on intervals only, so both step and ramp
    events are reduced to a common representation before any group-level
    comparison happens.

    :param start_time: Event start time.
    :param end_time: Optional event end time.
    :param transition_type: Step or ramp transition type.
    :return: Normalized ``(start_time, end_time)`` interval.
    """
    normalized_start_time: float = float(start_time)
    normalized_end_time: float

    if transition_type == DynamicEventTransitionType.Ramp:
        if end_time is None:
            normalized_end_time = normalized_start_time
        else:
            normalized_end_time = float(end_time)
    else:
        normalized_end_time = normalized_start_time

    return normalized_start_time, normalized_end_time


def _build_validation_entry(parameter: Var,
                            start_time: float,
                            end_time: float | None,
                            value: float,
                            group: RmsEventsGroup | EmtEventsGroup,
                            transition_type: DynamicEventTransitionType,
                            origin: str) -> EventValidationEntry:
    """
    Build one normalized validation entry from raw event data.

    :param parameter: Target runtime parameter.
    :param start_time: Event start time.
    :param end_time: Optional event end time.
    :param value: Target value.
    :param group: Target group.
    :param transition_type: Transition profile.
    :param origin: Human-readable origin used in messages.
    :return: Normalized validation entry.
    """
    normalized_start_time: float
    normalized_end_time: float
    normalized_start_time, normalized_end_time = _normalize_event_interval(start_time=start_time,
                                                                          end_time=end_time,
                                                                          transition_type=transition_type)
    return EventValidationEntry(parameter=parameter,
                                start_time=normalized_start_time,
                                end_time=normalized_end_time,
                                value=value,
                                group=group,
                                transition_type=transition_type,
                                origin=origin)


def _validate_event_interval(entry: EventValidationEntry) -> str | None:
    """
    Validate the local time interval of one normalized event entry.

    The overlap check assumes that every event interval is well-formed first.
    Invalid intervals are therefore reported before any pairwise comparison.

    :param entry: Normalized event entry.
    :return: Error message or ``None`` when the interval is valid.
    """
    error_message: str | None = None

    if entry.transition_type == DynamicEventTransitionType.Ramp:
        if entry.end_time + EVENT_TIME_TOLERANCE < entry.start_time:
            error_message = (
                f"{entry.origin} has an invalid ramp interval for parameter {entry.parameter.name}: "
                f"time={entry.start_time:.4f} s, end_time={entry.end_time:.4f} s."
            )
        else:
            pass
    else:
        error_message = None

    return error_message


def _get_existing_dynamic_events(circuit: MultiCircuit,
                                 mode: DynamicSimulationMode) -> Sequence[RmsEvent] | Sequence[EmtEvent]:
    """
    Return the persisted events for the selected simulation family.

    The dialog must compare pending rows against already stored circuit events
    so the validation covers the complete state that the solver would see.

    :param circuit: Circuit that stores canonical events.
    :param mode: Selected simulation family.
    :return: Sequence of existing RMS or EMT events.
    """
    existing_events: Sequence[RmsEvent] | Sequence[EmtEvent]

    if mode == DynamicSimulationMode.RMS:
        existing_events = circuit.rms_events
    else:
        existing_events = circuit.emt_events

    return existing_events


def _build_validation_entries_from_existing_events(circuit: MultiCircuit,
                                                   mode: DynamicSimulationMode) -> List[EventValidationEntry]:
    """
    Normalize the circuit events already stored for the selected mode.

    :param circuit: Circuit that stores canonical events.
    :param mode: Selected simulation family.
    :return: Normalized existing-event entries.
    """
    existing_entries: List[EventValidationEntry] = list()
    existing_events: Sequence[RmsEvent] | Sequence[EmtEvent] = _get_existing_dynamic_events(circuit=circuit,
                                                                                            mode=mode)
    event_item: RmsEvent | EmtEvent

    for event_item in existing_events:
        origin: str = "Existing event"
        existing_entries.append(_build_validation_entry(parameter=event_item.parameter,
                                                        start_time=float(event_item.time),
                                                        end_time=event_item.end_time,
                                                        value=float(event_item.value),
                                                        group=event_item.group,
                                                        transition_type=event_item.transition_type,
                                                        origin=origin))

    return existing_entries


def _intervals_overlap(first_entry: EventValidationEntry,
                       second_entry: EventValidationEntry) -> bool:
    """
    Check whether two normalized event intervals intersect.

    :param first_entry: First normalized event.
    :param second_entry: Second normalized event.
    :return: True when the occupied intervals overlap.
    """
    overlap_start: float = first_entry.start_time
    overlap_end: float = first_entry.end_time

    if second_entry.start_time > overlap_start:
        overlap_start = second_entry.start_time
    else:
        pass

    if second_entry.end_time < overlap_end:
        overlap_end = second_entry.end_time
    else:
        pass

    return overlap_start <= overlap_end + EVENT_TIME_TOLERANCE


def _format_validation_entry(entry: EventValidationEntry) -> str:
    """
    Format one normalized event for the validation message box.

    :param entry: Normalized event entry.
    :return: Human-readable event description.
    """
    transition_name: str
    message: str

    if entry.transition_type == DynamicEventTransitionType.Ramp:
        transition_name = "Ramp"
        message = (
            f"{entry.origin}: {transition_name}, parameter={entry.parameter.name}, "
            f"time={entry.start_time:.4f} s, end_time={entry.end_time:.4f} s, value={entry.value:.6f}"
        )
    else:
        transition_name = "Step"
        message = (
            f"{entry.origin}: {transition_name}, parameter={entry.parameter.name}, "
            f"time={entry.start_time:.4f} s, value={entry.value:.6f}"
        )

    return message


def _build_overlap_conflict_message(conflicts: Sequence[EventValidationConflict]) -> str:
    """
    Build the warning text shown when overlapping events are found.

    :param conflicts: Overlap conflicts detected across all validated groups.
    :return: Full warning message.
    """
    message_lines: List[str] = list()
    conflict: EventValidationConflict

    message_lines.append("Some events are overlapped and cannot be applied.")
    message_lines.append("")

    for conflict in conflicts:
        message_lines.append(f"Group: {conflict.group.name}")
        message_lines.append(_format_validation_entry(entry=conflict.first_event))
        message_lines.append(_format_validation_entry(entry=conflict.second_event))
        message_lines.append("")

    return "\n".join(message_lines).rstrip()


def _sort_validation_entries(entries: Sequence[EventValidationEntry]) -> List[EventValidationEntry]:
    """
    Return validation entries ordered by start, end and value.

    :param entries: Entries to sort.
    :return: Sorted list.
    """
    return sorted(entries, key=lambda item: (item.start_time, item.end_time, item.value))


def _find_overlapping_event_conflicts(entries: Sequence[EventValidationEntry]) -> List[EventValidationConflict]:
    """
    Detect pairwise overlaps between normalized dynamic events.

    The algorithm groups events by events-group and parameter first because only
    those events compete for the same runtime value. It then performs an ordered
    pairwise scan inside each bucket and records every interval intersection.

    :param entries: Normalized event entries from both persisted and pending data.
    :return: List of overlap conflicts.
    """
    conflicts: List[EventValidationConflict] = list()
    grouped_entries: Dict[tuple[int, int], List[EventValidationEntry]] = dict()
    entry: EventValidationEntry

    for entry in entries:
        grouping_key: tuple[int, int] = (id(entry.group), entry.parameter.uid)
        bucket: List[EventValidationEntry] | None = grouped_entries.get(grouping_key, None)

        if bucket is None:
            bucket = list()
            grouped_entries[grouping_key] = bucket
        else:
            pass

        bucket.append(entry)

    bucket_entries: List[EventValidationEntry]

    for bucket_entries in grouped_entries.values():
        sorted_entries: List[EventValidationEntry] = _sort_validation_entries(entries=bucket_entries)
        first_index: int = 0

        while first_index < len(sorted_entries):
            second_index: int = first_index + 1

            while second_index < len(sorted_entries):
                first_entry: EventValidationEntry = sorted_entries[first_index]
                second_entry: EventValidationEntry = sorted_entries[second_index]

                if _intervals_overlap(first_entry=first_entry, second_entry=second_entry):
                    conflicts.append(EventValidationConflict(group=first_entry.group,
                                                             first_event=first_entry,
                                                             second_event=second_entry))
                else:
                    if second_entry.start_time > first_entry.end_time + EVENT_TIME_TOLERANCE:
                        break
                    else:
                        pass

                second_index += 1

            first_index += 1

    return conflicts


def _validate_dynamic_event_entries(circuit: MultiCircuit,
                                    mode: DynamicSimulationMode,
                                    new_entries: Sequence[EventValidationEntry]) -> str | None:
    """
    Validate pending dialog events against existing and new overlap conflicts.

    :param circuit: Circuit that stores canonical events.
    :param mode: Selected simulation family.
    :param new_entries: Pending dialog events already normalized.
    :return: Validation error message or ``None`` when validation succeeds.
    """
    validation_entries: List[EventValidationEntry] = list()
    interval_error: str | None = None
    entry: EventValidationEntry

    validation_entries.extend(_build_validation_entries_from_existing_events(circuit=circuit, mode=mode))
    validation_entries.extend(new_entries)

    for entry in validation_entries:
        interval_error = _validate_event_interval(entry=entry)

        if interval_error is not None:
            return interval_error
        else:
            pass

    conflicts: List[EventValidationConflict] = _find_overlapping_event_conflicts(entries=validation_entries)

    if len(conflicts) > 0:
        return _build_overlap_conflict_message(conflicts=conflicts)
    else:
        return None


def create_dynamic_events_group_with_dialog(circuit: MultiCircuit,
                                            mode: DynamicSimulationMode,
                                            parent: QtWidgets.QWidget | None,
                                            missing_group_message: str,
                                            created_group_message_title: str,
                                            created_group_message_body_prefix: str) -> RmsEventsGroup | EmtEventsGroup | None:
    """
    Create one RMS/EMT events group through the shared modal workflow.

    :param circuit: Circuit that owns the canonical event-group collections.
    :param mode: Dynamic simulation family that determines the group type.
    :param parent: Optional parent widget for the modal dialogs.
    :param missing_group_message: Informational text shown before opening the name dialog.
    :param created_group_message_title: Title shown after the group is created.
    :param created_group_message_body_prefix: Prefix used in the created-group confirmation body.
    :return: Created group asset, or ``None`` when the user cancels.
    """
    dialog_title: str

    # The first modal explains why the broader workflow cannot proceed without
    # at least one event-group asset. Reusing this flow keeps event creation
    # semantics identical across the GUI.
    if mode == DynamicSimulationMode.RMS:
        dialog_title = "No RMS Events Group"
    else:
        dialog_title = "No EMT Events Group"

    if parent is not None:
        QtWidgets.QMessageBox.information(parent, dialog_title, missing_group_message)
    else:
        info_msg(missing_group_message)
        pass

    # The canonical name-entry dialog ensures that every workflow creates the
    # same persisted asset shape and requires the same explicit user choice.
    dialog: DynamicEventsGroupsDialog = DynamicEventsGroupsDialog(parent=parent, mode=mode)
    dialog_result: int = dialog.exec()
    if dialog_result == QtWidgets.QDialog.DialogCode.Accepted:
        group_name: str = dialog.get_name()
        if mode == DynamicSimulationMode.RMS:
            created_group: RmsEventsGroup | EmtEventsGroup = RmsEventsGroup(idtag=None, name=group_name)
            circuit.add_rms_events_group(created_group)
        else:
            created_group = EmtEventsGroup(idtag=None, name=group_name)
            circuit.add_emt_events_group(created_group)

        if parent is not None:
            QtWidgets.QMessageBox.information(
                parent,
                created_group_message_title,
                f"{created_group_message_body_prefix}: {group_name}"
            )
        else:
            pass
        return created_group
    else:
        return None


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
        validation_entries: List[EventValidationEntry] = list()

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

            validation_origin: str = f"New row {i + 1}"
            validation_entries.append(_build_validation_entry(parameter=param,
                                                              start_time=float(t),
                                                              end_time=end_time,
                                                              value=float(v),
                                                              group=group,
                                                              transition_type=transition_type,
                                                              origin=validation_origin))

        validation_error_message: str | None = _validate_dynamic_event_entries(circuit=self.circuit,
                                                                               mode=self.mode,
                                                                               new_entries=validation_entries)

        if validation_error_message is not None:
            QtWidgets.QMessageBox.warning(self,
                                          "Overlapping Events",
                                          validation_error_message)
            return
        else:
            pass

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


