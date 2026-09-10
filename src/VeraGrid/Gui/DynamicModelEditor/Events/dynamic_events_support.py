# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List, Dict, Set

from PySide6 import QtWidgets, QtCore

from VeraGrid.Gui.messages import info_msg
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import get_block_for_entry

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.enumerations import DynamicSimulationMode


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


def collect_dynamic_events_page_parameters(
        entry: DynamicEditorEntry,
        mode: DynamicSimulationMode,
) -> tuple[List[Var], Set[int], bool]:
    """Collect the current saved-model parameters used by one events page.

    The persistent model is read every time the events page is activated. This
    ensures that an events page never keeps the detached ``Var`` objects owned
    by a model editor working copy.

    :param entry: Device entry represented by the events page.
    :param mode: RMS or EMT model whose parameters are requested.
    :return: Parameters, mode-parameter UIDs and saved-model empty state.
    """
    block: object = get_block_for_entry(entry=entry, mode=mode)
    if isinstance(block, Block):
        parameters: List[Var]
        mode_parameter_uids: Set[int]
        parameters, mode_parameter_uids = collect_block_runtime_event_parameters(block=block)
        return list(parameters), set(mode_parameter_uids), block.empty()
    else:
        return list(), set(), True


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

    def get_typed_data(self) -> SwitchSequenceData | None:
        """Return the validated switch sequence without dictionary conversion.

        :return: Typed sequence payload, or ``None`` before acceptance.
        """
        return self._data


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
