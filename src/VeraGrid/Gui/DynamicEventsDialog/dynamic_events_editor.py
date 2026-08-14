# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, List, Set

from PySide6 import QtWidgets

from VeraGrid.Gui.DynamicEventsDialog.dynamic_events_editor_dialog import Ui_DynamicEventDialogue
from VeraGrid.Gui.DynamicEventsDialog.dynamic_events_editor_support import (
    EventRow,
    EventValidationEntry,
    SwitchSequenceDialog,
    _build_validation_entry,
    _validate_dynamic_event_entries,
    create_dynamic_events_group_with_dialog,
)
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DynamicEventTransitionType, DynamicSimulationMode


class DynamicEventEditorData:
    """
    Typed payload collected by the dynamic-event editor.
    """

    __slots__ = (
        "parameters",
        "target_times",
        "end_times",
        "values",
        "groups",
        "force_step_alignment",
        "transition_types",
    )

    def __init__(self) -> None:
        """
        Build an empty editor payload.

        :return: None.
        """
        self.parameters: List[Var] = list()
        self.target_times: List[float] = list()
        self.end_times: List[float | None] = list()
        self.values: List[float] = list()
        self.groups: List[RmsEventsGroup | EmtEventsGroup] = list()
        self.force_step_alignment: List[bool] = list()
        self.transition_types: List[DynamicEventTransitionType] = list()

    def to_dict(self) -> Dict[str, List]:
        """
        Preserve the historical payload format expected by callers.

        :return: Dictionary view of the editor payload.
        """
        payload: Dict[str, List] = dict()
        payload["parameters"] = list(self.parameters)
        payload["target_times"] = list(self.target_times)
        payload["end_times"] = list(self.end_times)
        payload["values"] = list(self.values)
        payload["groups"] = list(self.groups)
        payload["force_step_alignment"] = list(self.force_step_alignment)
        payload["transition_types"] = list(self.transition_types)
        return payload


class DynamicEventEditor(QtWidgets.QDialog):
    """
    Main dialog used to create RMS and EMT dynamic events.
    """

    __slots__ = (
        "ui",
        "mode",
        "circuit",
        "parameters_list",
        "target_device_name",
        "mode_parameter_uids",
        "rows",
        "_data",
    )

    def __init__(
        self,
        circuit: MultiCircuit,
        parameters_list: List[Var],
        target_device_name: str,
        mode: DynamicSimulationMode,
        mode_parameter_uids: Set[int] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """
        Build the dynamic-events editor dialog.

        :param circuit: Circuit that stores the event groups and existing events.
        :param parameters_list: Runtime parameters available for editing.
        :param target_device_name: Visible device name shown in the dialog.
        :param mode: Selected simulation family.
        :param mode_parameter_uids: EMT mode-parameter identifiers.
        :param parent: Optional parent widget.
        :return: None.
        """
        super().__init__(parent)
        self.ui: Ui_DynamicEventDialogue = Ui_DynamicEventDialogue()
        self.ui.setupUi(self)

        self.mode: DynamicSimulationMode = mode
        self.circuit: MultiCircuit = circuit
        self.parameters_list: List[Var] = parameters_list
        self.target_device_name: str = target_device_name
        self.mode_parameter_uids: Set[int] = set() if mode_parameter_uids is None else set(mode_parameter_uids)
        self.rows: List[EventRow] = list()
        self._data: DynamicEventEditorData = DynamicEventEditorData()

        self._configure_window()
        self._configure_table()
        self._connect_signals()

    def _configure_window(self) -> None:
        """
        Apply the mode-specific dialog title and static widget texts.

        :return: None.
        """
        # Stage 1: adapt the shell of the dialog to the selected simulation
        # family so the user sees immediately whether RMS or EMT is being edited.
        if self.mode == DynamicSimulationMode.RMS:
            self.setWindowTitle(self.tr("RMS Event Editor"))
        else:
            self.setWindowTitle(self.tr("EMT Event Editor"))

        self.setMinimumWidth(600)
        self.ui.targetDeviceLabel.setText(
            f"<b>{self.tr('Target device:')}</b> {self.target_device_name}"
        )

        # Stage 2: show the EMT-only sequence wizard only when discrete mode
        # switching is meaningful for the active simulation family.
        if self.mode == DynamicSimulationMode.EMT:
            self.ui.switchSequenceButton.setVisible(True)
        else:
            self.ui.switchSequenceButton.setVisible(False)

        ok_button: QtWidgets.QPushButton | None = self.ui.dialogButtonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        cancel_button: QtWidgets.QPushButton | None = self.ui.dialogButtonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        # Stage 3: keep button captions explicit because the dialog commits
        # persisted event assets, not just temporary form state.
        if ok_button is not None:
            ok_button.setText(self.tr("✅ Add Events"))
        else:
            pass

        if cancel_button is not None:
            cancel_button.setText(self.tr("Cancel"))
        else:
            pass

    def _configure_table(self) -> None:
        """
        Create the mode-specific column layout used by the dynamic rows.

        :return: None.
        """
        headers: List[str]

        # Stage 1: size the table to the exact schema used by the active mode so
        # row widgets and headers stay structurally aligned.
        if self.mode == DynamicSimulationMode.RMS or self.mode == DynamicSimulationMode.EMT:
            self.ui.eventsTableWidget.setColumnCount(8)
            headers = [
                "",
                self.tr("Parameter"),
                self.tr("Time"),
                self.tr("New Value"),
                self.tr("Transition"),
                self.tr("End Time"),
                self.tr("Group"),
                self.tr("Align Step"),
            ]
        else:
            self.ui.eventsTableWidget.setColumnCount(5)
            headers = [
                "",
                self.tr("Parameter"),
                self.tr("Time"),
                self.tr("New Value"),
                self.tr("Group"),
            ]

        self.ui.eventsTableWidget.setHorizontalHeaderLabels(headers)
        self.ui.eventsTableWidget.horizontalHeader().setSectionResizeMode(
            0,
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents,
        )
        self.ui.eventsTableWidget.horizontalHeader().setStretchLastSection(True)

    def _connect_signals(self) -> None:
        """
        Connect the static dialog buttons to the controller actions.

        :return: None.
        """
        # Stage 1: connect every static control to one explicit controller
        # action so the dialog state transitions stay easy to trace.
        self.ui.addRowButton.clicked.connect(self.add_row)
        self.ui.removeRowButton.clicked.connect(self.remove_checked_rows)
        self.ui.newGroupButton.clicked.connect(self.create_event_group)
        self.ui.dialogButtonBox.accepted.connect(self.accept_dialog)
        self.ui.dialogButtonBox.rejected.connect(self.reject)

        if self.mode == DynamicSimulationMode.EMT:
            self.ui.switchSequenceButton.clicked.connect(self.open_switch_sequence_dialog)
        else:
            pass

    def add_row(self) -> EventRow | None:
        """
        Append one editable event row to the table.

        :return: Created row object or ``None`` when the mode is unsupported.
        """
        # Stage 1: reserve the physical row first so the helper object can wire
        # its editors directly into the correct table positions.
        row_index: int = self.ui.eventsTableWidget.rowCount()
        self.ui.eventsTableWidget.insertRow(row_index)

        if self.mode == DynamicSimulationMode.RMS:
            row: EventRow = EventRow(
                self.ui.eventsTableWidget,
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
                self.ui.eventsTableWidget,
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

    def remove_checked_rows(self) -> None:
        """
        Remove every table row whose checkbox is selected.

        :return: None.
        """
        # Stage 1: gather the marked rows first because removing rows mutates
        # table indices and would otherwise invalidate the traversal.
        rows_to_remove: List[EventRow] = [row for row in self.rows if row.is_checked()]

        if len(rows_to_remove) == 0:
            QtWidgets.QMessageBox.information(
                self,
                self.tr("No Rows Selected"),
                self.tr("Please check at least one row to remove."),
            )
        else:
            row: EventRow
            for row in reversed(rows_to_remove):
                self.ui.eventsTableWidget.removeRow(row.row)
                self.rows.remove(row)

            reindexed_row: EventRow
            for index, reindexed_row in enumerate(self.rows):
                reindexed_row.row = index

    def create_event_group(self) -> None:
        """
        Open the shared RMS/EMT events-group creation workflow.

        :return: None.
        """
        # Stage 1: compute the mode-specific messages before opening the shared
        # workflow so both RMS and EMT reuse the same persisted-asset path.
        missing_group_message: str
        created_group_message_title: str
        created_group_message_body_prefix: str = self.tr("New group name")

        if self.mode == DynamicSimulationMode.RMS:
            missing_group_message = self.tr("No RMS Events Group found, please create one before adding an event.")
            created_group_message_title = self.tr("RMS group Created")
        else:
            missing_group_message = self.tr("No EMT Events Group found, please create one before adding an event.")
            created_group_message_title = self.tr("EMT group Created")

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
        Expand one switch open/close sequence into EMT rows.

        :return: None.
        """
        # Stage 1: expose only EMT discrete mode parameters that represent
        # switch state, because the wizard expands open/close transitions only.
        mode_parameters: List[Var] = list()
        parameter: Var

        for parameter in self.parameters_list:
            if parameter.uid in self.mode_parameter_uids and parameter.name.startswith("switch_closed_mode_"):
                mode_parameters.append(parameter)
            else:
                pass

        if len(mode_parameters) == 0:
            QtWidgets.QMessageBox.information(
                self,
                self.tr("Switch Sequence"),
                self.tr("No switch EMT mode parameter is available in this device."),
            )
        else:
            dialog: SwitchSequenceDialog = SwitchSequenceDialog(
                mode_parameters=mode_parameters,
                events_groups=self.circuit.emt_events_groups,
                parent=self,
            )

            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                sequence_data: Dict[str, object] = dialog.get_data()
                index: int
                for index in range(len(sequence_data["times"])):
                    row: EventRow | None = self.add_row()
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
            else:
                pass

    def accept_dialog(self) -> None:
        """
        Validate the editable rows and collect their event payload.

        :return: None.
        """
        # Stage 1: reject empty submissions early because downstream validation
        # assumes at least one pending event row exists.
        if len(self.rows) == 0:
            QtWidgets.QMessageBox.warning(
                self,
                self.tr("No Events"),
                self.tr("Please add at least one event before confirming."),
            )
        else:
            # Stage 2: collect typed row payloads and build normalized
            # validation entries before mutating the editor result state.
            parameters: List[Var] = list()
            target_times: List[float] = list()
            end_times: List[float | None] = list()
            values: List[float] = list()
            groups: List[RmsEventsGroup | EmtEventsGroup] = list()
            force_step_alignment_flags: List[bool] = list()
            transition_types: List[DynamicEventTransitionType] = list()
            validation_entries: List[EventValidationEntry] = list()
            row_index: int
            row: EventRow

            for row_index, row in enumerate(self.rows):
                try:
                    row_data = row.get_data()
                except Exception as exc:
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.tr("Invalid Input"),
                        self.tr("Row {row_number}: {message}").format(row_number=row_index + 1, message=exc),
                    )
                    return

                parameters.append(row_data.parameter)
                target_times.append(row_data.target_time)
                end_times.append(row_data.end_time)
                values.append(row_data.value)
                groups.append(row_data.group)
                force_step_alignment_flags.append(row_data.force_step_alignment)
                transition_types.append(row_data.transition_type)

                validation_origin: str = self.tr("New row {row_number}").format(row_number=row_index + 1)
                validation_entries.append(
                    _build_validation_entry(
                        parameter=row_data.parameter,
                        start_time=float(row_data.target_time),
                        end_time=row_data.end_time,
                        value=float(row_data.value),
                        group=row_data.group,
                        transition_type=row_data.transition_type,
                        origin=validation_origin,
                    )
                )

            validation_error_message: str | None = _validate_dynamic_event_entries(
                circuit=self.circuit,
                mode=self.mode,
                new_entries=validation_entries,
            )

            if validation_error_message is not None:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Overlapping Events"),
                    validation_error_message,
                )
            else:
                # Stage 3: commit the result only after global validation passes
                # so every consumer observes one coherent payload snapshot.
                self._data.parameters = parameters
                self._data.target_times = target_times
                self._data.end_times = end_times
                self._data.values = values
                self._data.groups = groups
                self._data.force_step_alignment = force_step_alignment_flags
                self._data.transition_types = transition_types
                self.accept()

    def get_data(self) -> Dict[str, List]:
        """
        Return the validated payload collected by the dialog.

        :return: Dictionary with the event fields grouped by column.
        """
        return self._data.to_dict()
