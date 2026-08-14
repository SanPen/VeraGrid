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


class EventRowData:
    """
    Typed payload extracted from one editable event row.
    """

    __slots__ = (
        "parameter",
        "target_time",
        "end_time",
        "value",
        "group",
        "force_step_alignment",
        "transition_type",
    )

    def __init__(self,
                 parameter: Var,
                 target_time: float,
                 end_time: float | None,
                 value: float,
                 group: RmsEventsGroup | EmtEventsGroup,
                 force_step_alignment: bool,
                 transition_type: DynamicEventTransitionType) -> None:
        """
        Build one typed row payload.

        :param parameter: Target runtime parameter.
        :param target_time: Event start time.
        :param end_time: Optional ramp end time.
        :param value: Target runtime value.
        :param group: Selected events group.
        :param force_step_alignment: Exact-alignment flag for EMT mode parameters.
        :param transition_type: Step or ramp transition profile.
        :return: None.
        """
        self.parameter: Var = parameter
        self.target_time: float = float(target_time)
        self.end_time: float | None = end_time
        self.value: float = float(value)
        self.group: RmsEventsGroup | EmtEventsGroup = group
        self.force_step_alignment: bool = bool(force_step_alignment)
        self.transition_type: DynamicEventTransitionType = transition_type


class SwitchSequenceData:
    """
    Typed payload produced by the switch-sequence dialog.
    """

    __slots__ = (
        "parameter",
        "group",
        "times",
        "values",
    )

    def __init__(self,
                 parameter: Var,
                 group: EmtEventsGroup,
                 times: List[float],
                 values: List[float]) -> None:
        """
        Build one switch-sequence payload.

        :param parameter: Mode parameter toggled by the sequence.
        :param group: Target EMT events group.
        :param times: Ordered switching times.
        :param values: Ordered switching values.
        :return: None.
        """
        self.parameter: Var = parameter
        self.group: EmtEventsGroup = group
        self.times: List[float] = times
        self.values: List[float] = values

    def to_dict(self) -> Dict[str, object]:
        """
        Preserve the historical dialog API expected by callers and tests.

        :return: Dictionary view of the payload.
        """
        payload: Dict[str, object] = dict()
        payload["parameter"] = self.parameter
        payload["group"] = self.group
        payload["times"] = list(self.times)
        payload["values"] = list(self.values)
        return payload


def _switch_sequence_pair_sort_key(pair: tuple[float, float]) -> float:
    """
    Return the stable ordering key for one switch-sequence pair.

    :param pair: ``(time, value)`` sequence item.
    :return: Time component used for sorting.
    """
    return float(pair[0])


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
        transition_name = QtCore.QCoreApplication.translate("DynamicEventEditor", "Ramp")
        message = (
            QtCore.QCoreApplication.translate(
                "DynamicEventEditor",
                "{origin}: {transition}, parameter={parameter}, time={time:.4f} s, "
                "end_time={end_time:.4f} s, value={value:.6f}",
            ).format(
                origin=entry.origin,
                transition=transition_name,
                parameter=entry.parameter.name,
                time=entry.start_time,
                end_time=entry.end_time,
                value=entry.value,
            )
        )
    else:
        transition_name = QtCore.QCoreApplication.translate("DynamicEventEditor", "Step")
        message = (
            QtCore.QCoreApplication.translate(
                "DynamicEventEditor",
                "{origin}: {transition}, parameter={parameter}, time={time:.4f} s, value={value:.6f}",
            ).format(
                origin=entry.origin,
                transition=transition_name,
                parameter=entry.parameter.name,
                time=entry.start_time,
                value=entry.value,
            )
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

    message_lines.append(
        QtCore.QCoreApplication.translate("DynamicEventEditor", "Some events are overlapped and cannot be applied.")
    )
    message_lines.append("")

    for conflict in conflicts:
        message_lines.append(
            QtCore.QCoreApplication.translate("DynamicEventEditor", "Group: {group_name}").format(
                group_name=conflict.group.name,
            )
        )
        message_lines.append(_format_validation_entry(entry=conflict.first_event))
        message_lines.append(_format_validation_entry(entry=conflict.second_event))
        message_lines.append("")

    return "\n".join(message_lines).rstrip()


def _validation_entry_sort_key(entry: EventValidationEntry) -> tuple[float, float, float]:
    """
    Return the stable ordering key used by overlap validation.

    :param entry: Validation entry to sort.
    :return: ``(start_time, end_time, value)`` sort key.
    """
    return entry.start_time, entry.end_time, entry.value


def _sort_validation_entries(entries: Sequence[EventValidationEntry]) -> List[EventValidationEntry]:
    """
    Return validation entries ordered by start, end and value.

    :param entries: Entries to sort.
    :return: Sorted list.
    """
    return sorted(entries, key=_validation_entry_sort_key)


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
        dialog_title = QtCore.QCoreApplication.translate("DynamicEventEditor", "No RMS Events Group")
    else:
        dialog_title = QtCore.QCoreApplication.translate("DynamicEventEditor", "No EMT Events Group")

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
                QtCore.QCoreApplication.translate("DynamicEventEditor", "{prefix}: {group_name}").format(
                    prefix=created_group_message_body_prefix,
                    group_name=group_name,
                )
            )
        else:
            pass
        return created_group
    else:
        return None


class EventRow:
    """
    Encapsulate one editable row in the RMS/EMT event table.
    """

    __slots__ = (
        "__weakref__",
        "table",
        "row",
        "mode",
        "mode_parameter_uids",
        "param_combo",
        "time_spin",
        "value_spin",
        "transition_combo",
        "end_time_spin",
        "group_combo",
        "force_alignment_check",
    )

    def __init__(self,
                 table: QtWidgets.QTableWidget,
                 row: int,
                 parameters_list: List[Var],
                 events_groups_list: List[RmsEventsGroup] | List[EmtEventsGroup],
                 mode: DynamicSimulationMode,
                 mode_parameter_uids: Set[int] | None = None) -> None:
        """
        Build one dynamic-event editor row.

        :param table: Parent table that owns the row widgets.
        :param row: Physical row index inside the table.
        :param parameters_list: Candidate runtime parameters.
        :param events_groups_list: Candidate RMS/EMT event groups.
        :param mode: Selected simulation family.
        :param mode_parameter_uids: EMT mode-parameter identifiers.
        :return: None.
        """
        self.table: QtWidgets.QTableWidget = table
        self.row: int = row
        self.mode: DynamicSimulationMode = mode
        self.mode_parameter_uids: Set[int] = set() if mode_parameter_uids is None else set(mode_parameter_uids)

        # Stage 1: create the checkbox that marks rows for removal without
        # relying on selection state, because the table intentionally disables
        # row selection for safer editing.
        checkbox: QtWidgets.QTableWidgetItem = QtWidgets.QTableWidgetItem()
        checkbox.setFlags(
            QtCore.Qt.ItemFlag.ItemIsUserCheckable |
            QtCore.Qt.ItemFlag.ItemIsEnabled
        )
        checkbox.setCheckState(QtCore.Qt.CheckState.Unchecked)
        table.setItem(row, 0, checkbox)

        # Stage 2: populate the runtime-parameter selector from the symbolic
        # model so the user can only pick parameters the solver actually owns.
        self.param_combo = QtWidgets.QComboBox()
        parameter: Var
        for parameter in parameters_list:
            self.param_combo.addItem(parameter.name, parameter)
        table.setCellWidget(row, 1, self.param_combo)

        # Stage 3: create the numerical editors that define the event payload.
        self.time_spin = QtWidgets.QDoubleSpinBox()
        self.time_spin.setDecimals(4)
        self.time_spin.setRange(0.0, 1e9)
        self.time_spin.setSingleStep(0.1)
        self.time_spin.setSuffix(" s")
        table.setCellWidget(row, 2, self.time_spin)

        self.value_spin = QtWidgets.QDoubleSpinBox()
        self.value_spin.setDecimals(6)
        self.value_spin.setRange(-1e9, 1e9)
        self.value_spin.setSingleStep(0.01)
        table.setCellWidget(row, 3, self.value_spin)

        # Stage 4: create transition-specific widgets only for dynamic modes
        # that support both steps and ramps, so the row shape matches the table.
        self.transition_combo: QtWidgets.QComboBox | None = None
        self.end_time_spin: QtWidgets.QDoubleSpinBox | None = None

        if self.mode == DynamicSimulationMode.EMT or self.mode == DynamicSimulationMode.RMS:
            self.transition_combo = QtWidgets.QComboBox()
            self.transition_combo.addItem(
                QtCore.QCoreApplication.translate("DynamicEventEditor", "Step"),
                DynamicEventTransitionType.Step,
            )
            self.transition_combo.addItem(
                QtCore.QCoreApplication.translate("DynamicEventEditor", "Ramp"),
                DynamicEventTransitionType.Ramp,
            )
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

        # Stage 5: attach the event-group selector because event ownership is
        # resolved against those persisted group assets during simulation.
        self.group_combo = QtWidgets.QComboBox()
        for group in events_groups_list:
            self.group_combo.addItem(group.name, group)
        if self.mode == DynamicSimulationMode.EMT or self.mode == DynamicSimulationMode.RMS:
            table.setCellWidget(row, 6, self.group_combo)
        else:
            table.setCellWidget(row, 4, self.group_combo)

        # Stage 6: EMT mode parameters optionally expose exact-step alignment,
        # because discrete mode changes must sometimes happen on the solver step.
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

    def is_checked(self) -> bool:
        """
        Return whether the removal checkbox is selected.

        :return: True when the row is marked for removal.
        """
        item: QtWidgets.QTableWidgetItem | None = self.table.item(self.row, 0)
        return item and item.checkState() == QtCore.Qt.CheckState.Checked

    def get_data(self) -> EventRowData:
        """
        Build a typed payload from the current widget values.

        :return: Validated row payload.
        """
        param: object = self.param_combo.currentData()
        group: object = self.group_combo.currentData()

        if param is None or group is None:
            raise ValueError(QtCore.QCoreApplication.translate("DynamicEventEditor", "Missing fields"))
        else:
            pass

        if not isinstance(param, Var):
            raise TypeError(QtCore.QCoreApplication.translate("DynamicEventEditor", "parameter must be Var"))
        else:
            pass

        if not isinstance(group, (RmsEventsGroup, EmtEventsGroup)):
            raise TypeError(QtCore.QCoreApplication.translate("DynamicEventEditor", "group has invalid type"))
        else:
            pass

        target_time: float = self.time_spin.value()
        value: float = self.value_spin.value()
        transition_type: DynamicEventTransitionType = DynamicEventTransitionType.Step
        end_time: float | None = None

        if self.transition_combo is not None:
            transition_data: object = self.transition_combo.currentData()
            if isinstance(transition_data, DynamicEventTransitionType):
                transition_type = transition_data
            else:
                raise TypeError(
                    QtCore.QCoreApplication.translate(
                        "DynamicEventEditor",
                        "transition_type must be DynamicEventTransitionType",
                    )
                )
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

        # Stage 7: return one typed object so the editor can validate and store
        # rows without depending on positional tuples or ad-hoc dictionaries.
        return EventRowData(parameter=param,
                            target_time=target_time,
                            end_time=end_time,
                            value=value,
                            group=group,
                            force_step_alignment=force_step_alignment,
                            transition_type=transition_type)

    def add_group(self, group: RmsEventsGroup | EmtEventsGroup) -> None:
        """
        Add one newly created event group to the combo box.

        :param group: New RMS/EMT events group.
        :return: None.
        """
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

    __slots__ = (
        "__weakref__",
        "table",
        "row",
        "time_spin",
        "state_combo",
    )

    def __init__(self, table: QtWidgets.QTableWidget, row: int) -> None:
        """
        Build one switch-sequence row.

        :param table: Parent table that owns the row widgets.
        :param row: Physical row index inside the table.
        :return: None.
        """
        self.table: QtWidgets.QTableWidget = table
        self.row: int = row

        checkbox: QtWidgets.QTableWidgetItem = QtWidgets.QTableWidgetItem()
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
        self.state_combo.addItem(QtCore.QCoreApplication.translate("SwitchSequenceDialog", "Open"), 0.0)
        self.state_combo.addItem(QtCore.QCoreApplication.translate("SwitchSequenceDialog", "Close"), 1.0)
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

    __slots__ = (
        "mode_parameters",
        "events_groups",
        "rows",
        "_data",
        "parameter_combo",
        "group_combo",
        "sequence_table",
        "add_row_btn",
        "remove_row_btn",
    )

    def __init__(self,
                 mode_parameters: List[Var],
                 events_groups: List[EmtEventsGroup],
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the switch-sequence helper dialog.

        :param mode_parameters: Discrete mode parameters eligible for switching.
        :param events_groups: Available EMT events groups.
        :param parent: Optional parent widget.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle(self.tr("Switch Sequence Wizard"))
        self.setMinimumWidth(520)
        self.mode_parameters: List[Var] = mode_parameters
        self.events_groups: List[EmtEventsGroup] = events_groups
        self.rows: List[SwitchSequenceRow] = list()
        self._data: SwitchSequenceData | None = None

        # Stage 1: build the static form that chooses the discrete parameter
        # and the persisted events group receiving the expanded sequence.
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        layout.addLayout(form_layout)

        self.parameter_combo = QtWidgets.QComboBox()
        parameter: Var
        for parameter in mode_parameters:
            self.parameter_combo.addItem(parameter.name, parameter)
        form_layout.addRow(self.tr("Mode Parameter"), self.parameter_combo)

        self.group_combo = QtWidgets.QComboBox()
        group: EmtEventsGroup
        for group in events_groups:
            self.group_combo.addItem(group.name, group)
        form_layout.addRow(self.tr("Group"), self.group_combo)

        self.sequence_table = QtWidgets.QTableWidget(0, 3)
        self.sequence_table.setHorizontalHeaderLabels(["", self.tr("Time"), self.tr("State")])
        self.sequence_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.sequence_table.horizontalHeader().setStretchLastSection(True)
        self.sequence_table.verticalHeader().setVisible(False)
        self.sequence_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.sequence_table)

        # Stage 2: expose row-level editing controls that let the user build
        # the ordered switching sequence explicitly.
        buttons_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.add_row_btn = QtWidgets.QPushButton(self.tr("Add Sequence Step"))
        self.remove_row_btn = QtWidgets.QPushButton(self.tr("Remove Selected Rows"))
        buttons_layout.addWidget(self.add_row_btn)
        buttons_layout.addWidget(self.remove_row_btn)
        layout.addLayout(buttons_layout)

        # Stage 3: keep confirmation at the bottom so the sequence is validated
        # only after all rows have been normalized and sorted.
        dialog_buttons: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(
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
        """
        Append one editable step to the switch sequence.

        :return: None.
        """
        row_index: int = self.sequence_table.rowCount()
        self.sequence_table.insertRow(row_index)
        row: SwitchSequenceRow = SwitchSequenceRow(self.sequence_table, row_index)
        self.rows.append(row)

    def remove_checked_rows(self) -> None:
        """
        Remove every sequence row marked for deletion.

        :return: None.
        """
        rows_to_remove: List[SwitchSequenceRow] = [row for row in self.rows if row.is_checked()]

        if len(rows_to_remove) == 0:
            QtWidgets.QMessageBox.information(self,
                                              self.tr("Switch Sequence"),
                                              self.tr("Please check at least one row to remove."))
        else:
            row: SwitchSequenceRow
            for row in reversed(rows_to_remove):
                self.sequence_table.removeRow(row.row)
                self.rows.remove(row)

            index: int
            reindexed_row: SwitchSequenceRow
            for index, reindexed_row in enumerate(self.rows):
                reindexed_row.row = index

    def accept_dialog(self) -> None:
        """
        Validate the discrete sequence and store it as typed payload.

        :return: None.
        """
        parameter: object = self.parameter_combo.currentData()
        group: object = self.group_combo.currentData()
        times: list[float] = list()
        values: list[float] = list()
        row: SwitchSequenceRow

        if parameter is None or group is None:
            QtWidgets.QMessageBox.warning(self,
                                          self.tr("Switch Sequence"),
                                          self.tr("Select a mode parameter and an events group."))
            return
        else:
            pass

        if not isinstance(parameter, Var) or not isinstance(group, EmtEventsGroup):
            QtWidgets.QMessageBox.warning(self,
                                          self.tr("Switch Sequence"),
                                          self.tr("The selected parameter or group is invalid."))
            return
        else:
            pass

        if len(self.rows) == 0:
            QtWidgets.QMessageBox.warning(self,
                                          self.tr("Switch Sequence"),
                                          self.tr("Add at least one sequence row."))
            return
        else:
            pass

        # Stage 4: read every row before sorting so the dialog preserves the
        # explicit user input and then normalizes it into monotonic time order.
        for row in self.rows:
            target_time, state_value = row.get_data()
            times.append(target_time)
            values.append(state_value)

        sorted_pairs: List[tuple[float, float]] = sorted(zip(times, values), key=_switch_sequence_pair_sort_key)
        sorted_times: List[float] = [float(item[0]) for item in sorted_pairs]
        sorted_values: List[float] = [float(item[1]) for item in sorted_pairs]
        self._data = SwitchSequenceData(parameter=parameter,
                                        group=group,
                                        times=sorted_times,
                                        values=sorted_values)
        self.accept()

    def get_data(self) -> Dict[str, object]:
        """
        Return the historical dictionary view expected by callers and tests.

        :return: Dictionary payload for compatibility.
        """
        if self._data is None:
            return dict()
        else:
            return self._data.to_dict()

class DynamicEventsGroupsDialog(QtWidgets.QDialog):
    """
    Name-entry dialog used to create one RMS or EMT events group.
    """

    __slots__ = (
        "mode",
        "_name",
        "name_label",
        "name_edit",
        "buttons",
    )

    def __init__(self,
                 mode: DynamicSimulationMode,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the events-group creation dialog.

        :param mode: Dynamic simulation family that determines the title.
        :param parent: Optional parent widget.
        :return: None.
        """
        super().__init__(parent)

        self.mode = mode
        if self.mode == DynamicSimulationMode.RMS:
            self.setWindowTitle(self.tr("Create RMS Events Group"))
        elif self.mode == DynamicSimulationMode.EMT:
            self.setWindowTitle(self.tr("Create EMT Events Group"))
        self.setModal(True)
        self.setMinimumWidth(300)

        self._name: str | None = None

        # Stage 1: keep the dialog focused on a single explicit choice, the
        # canonical name of the persisted events group asset.
        self.name_label = QtWidgets.QLabel(self.tr("Name:"))
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText(self.tr("Enter group name"))

        # Buttons
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        # Stage 2: build the minimal form that validates the name before the
        # calling workflow mutates the circuit state.
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.name_label, self.name_edit)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.buttons)

        # Stage 3: connect both button acceptance and return-press to the same
        # validation path so the workflow stays consistent across input styles.
        self.buttons.accepted.connect(self.accept_dialog)
        self.buttons.rejected.connect(self.reject)
        self.name_edit.returnPressed.connect(self.accept_dialog)

    def accept_dialog(self) -> None:
        """
        Validate the input and store the name.

        :return: None.
        """
        name: str = self.name_edit.text().strip()

        if not name:
            QtWidgets.QMessageBox.warning(
                self,
                self.tr("Invalid name"),
                self.tr("The name cannot be empty.")
            )
            return
        else:
            pass

        self._name = name
        self.accept()

    def get_name(self) -> str:
        """
        Return the validated group name.

        :return: Group name text.
        """
        if self._name is None:
            return ""
        else:
            return self._name
