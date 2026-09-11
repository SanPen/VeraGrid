# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page_ui import Ui_DynamicEventsPage
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_support import SwitchSequenceData, SwitchSequenceDialog
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.object_model import ObjectsModel
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy
from VeraGrid.Gui.table_view_header_wrap import HeaderViewWithWordWrap
from VeraGrid.Gui.toast_widget import ToastManager
from VeraGridEngine.Devices.Events.emt_event import EmtEvent
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, DynamicEventTransitionType, DynamicSimulationMode, PrpCat


class DynamicEventGroupsTreeModel(QtGui.QStandardItemModel):
    """Display and directly edit the event groups of one simulation mode."""

    groupSelectionInvalidated = QtCore.Signal()

    __slots__ = ("circuit", "device", "mode")

    GROUP_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole)

    def __init__(self,
                 circuit: MultiCircuit,
                 device: EditableDevice,
                 mode: DynamicSimulationMode,
                 parent: QtCore.QObject | None = None) -> None:
        """Create the real-object event-group tree model.

        :param circuit: Circuit that owns the groups and events.
        :param device: Device used to calculate the displayed event counts.
        :param mode: RMS or EMT simulation family.
        :param parent: Optional Qt owner.
        :return: None.
        """
        QtGui.QStandardItemModel.__init__(self, parent)
        self.circuit: MultiCircuit = circuit
        self.device: EditableDevice = device
        self.mode: DynamicSimulationMode = mode
        self.setHorizontalHeaderLabels([self.tr("Event groups")])
        self.rebuild()

    def get_groups(self) -> List[RmsEventsGroup | EmtEventsGroup]:
        """Return the circuit groups belonging to this model simulation mode.

        :return: Ordered real event-group objects.
        """
        if self.mode == DynamicSimulationMode.RMS:
            return list(self.circuit.rms_events_groups)
        else:
            return list(self.circuit.emt_events_groups)

    def get_group_events(self,
                         group: RmsEventsGroup | EmtEventsGroup) -> List[RmsEvent | EmtEvent]:
        """Return this page device events belonging to one real group.

        :param group: Real group whose events are requested.
        :return: Matching real event objects.
        """
        if self.mode == DynamicSimulationMode.RMS:
            source_events: List[RmsEvent | EmtEvent] = list(self.circuit.rms_events)
        else:
            source_events = list(self.circuit.emt_events)

        group_events: List[RmsEvent | EmtEvent] = list()
        event: RmsEvent | EmtEvent
        for event in source_events:
            if event.group is group and event.device is self.device:
                group_events.append(event)
            else:
                pass
        return group_events

    def rebuild(self) -> None:
        """Rebuild tree rows from the current real circuit groups.

        :return: None.
        """
        self.removeRows(0, self.rowCount())
        group: RmsEventsGroup | EmtEventsGroup
        for group in self.get_groups():
            event_count: int = len(self.get_group_events(group=group))
            item: QtGui.QStandardItem = QtGui.QStandardItem(f"{group.name} ({event_count})")
            item.setData(group, self.GROUP_ROLE)
            item.setEditable(False)
            item.setCheckable(True)
            if group.active:
                item.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.appendRow(item)

    def group_from_index(self,
                         index: QtCore.QModelIndex) -> RmsEventsGroup | EmtEventsGroup | None:
        """Return the real group stored by a tree index.

        :param index: Candidate tree-model index.
        :return: Stored group or ``None``.
        """
        if index.isValid():
            group: object = index.data(self.GROUP_ROLE)
            if isinstance(group, (RmsEventsGroup, EmtEventsGroup)):
                return group
            else:
                return None
        else:
            return None

    def index_for_group(self,
                        group: RmsEventsGroup | EmtEventsGroup) -> QtCore.QModelIndex:
        """Locate a real group by object identity.

        :param group: Group that should be selected.
        :return: Matching tree index or an invalid index.
        """
        row_index: int
        for row_index in range(self.rowCount()):
            candidate_index: QtCore.QModelIndex = self.index(row_index, 0)
            if self.group_from_index(candidate_index) is group:
                return candidate_index
            else:
                pass
        return QtCore.QModelIndex()

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = QtCore.Qt.ItemDataRole.EditRole) -> bool:
        """Apply checkbox changes directly to the real group object.

        :param index: Edited tree index.
        :param value: New item value.
        :param role: Qt data role being changed.
        :return: Whether the value was accepted.
        """
        group: RmsEventsGroup | EmtEventsGroup | None = self.group_from_index(index=index)
        if group is not None and role == QtCore.Qt.ItemDataRole.CheckStateRole:
            checked: bool = value == QtCore.Qt.CheckState.Checked or value == int(QtCore.Qt.CheckState.Checked.value)
            group.active = checked
            accepted: bool = QtGui.QStandardItemModel.setData(self, index, value, role)
            return accepted
        else:
            return QtGui.QStandardItemModel.setData(self, index, value, role)


class DynamicEventsPage(QtWidgets.QWidget):
    """Edit real RMS or EMT event assets for one dynamic device."""

    dirtyStateChanged = QtCore.Signal(bool)

    __slots__ = (
        "entry", "circuit", "device", "mode", "parameters", "mode_parameter_uids",
        "model_is_empty", "ui", "toast_manager", "group_model", "selected_group",
        "objects_model", "filter_model", "tree_view", "groups_tree_view",
        "empty_model_message", "switch_sequence_action", "add_event_action",
        "remove_action", "new_group_action", "clear_device_events_action",
    )

    def __init__(self,
                 entry: DynamicEditorEntry,
                 device: EditableDevice,
                 mode: DynamicSimulationMode,
                 parameters: List[Var],
                 mode_parameter_uids: set[int],
                 model_is_empty: bool,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Build a direct, real-object dynamic-events editor page.

        :param entry: Dynamic editor entry represented by this page.
        :param device: Device targeted by the displayed events.
        :param mode: RMS or EMT simulation family.
        :param parameters: Symbolic parameters available to event objects.
        :param mode_parameter_uids: UIDs of discrete mode parameters.
        :param model_is_empty: Whether the device dynamic model is empty.
        :param parent: Optional owning widget.
        :return: None.
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.entry: DynamicEditorEntry = entry
        self.circuit: MultiCircuit = entry.circuit
        self.device: EditableDevice = device
        self.mode: DynamicSimulationMode = mode
        self.parameters: List[Var] = list(parameters)
        self.mode_parameter_uids: set[int] = set(mode_parameter_uids)
        self.model_is_empty: bool = bool(model_is_empty)
        self.selected_group: RmsEventsGroup | EmtEventsGroup | None = None
        self.objects_model: ObjectsModel | None = None
        self.filter_model: ObjectModelFilterProxy | None = None
        self.toast_manager: ToastManager = ToastManager(parent=self, position_top=False)

        self.ui: Ui_DynamicEventsPage = Ui_DynamicEventsPage()
        self.ui.setupUi(self)
        # Keep the group tree at its minimum useful width so event properties receive the available space.
        self.ui.eventsSplitter.setSizes([220, 680])
        self.tree_view: QtWidgets.QTableView = self.ui.eventsTableView
        self.groups_tree_view: QtWidgets.QTreeView = self.ui.eventGroupsTreeView
        self.empty_model_message: QtWidgets.QLabel = self.ui.emptyModelMessage
        self.switch_sequence_action: QtGui.QAction = self.ui.actionSwitchSequence
        self.add_event_action: QtGui.QAction = self.ui.actionAddEvent
        self.remove_action: QtGui.QAction = self.ui.actionRemove
        self.new_group_action: QtGui.QAction = self.ui.actionNewGroup
        self.clear_device_events_action: QtGui.QAction = self.ui.actionClearDeviceEvents

        # The generic database table presentation is reused for the real event objects.
        self.tree_view.setHorizontalHeader(HeaderViewWithWordWrap(self.tree_view))
        self.empty_model_message.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.empty_model_message.setVisible(self.model_is_empty)
        self.empty_model_message.raise_()
        self.switch_sequence_action.setVisible(self.mode == DynamicSimulationMode.EMT)

        self.group_model: DynamicEventGroupsTreeModel = DynamicEventGroupsTreeModel(
            circuit=self.circuit,
            device=self.device,
            mode=self.mode,
            parent=self,
        )
        self.groups_tree_view.setModel(self.group_model)
        self.groups_tree_view.setRootIsDecorated(False)

        self.groups_tree_view.selectionModel().currentChanged.connect(self._on_group_selected)
        self.add_event_action.triggered.connect(self.add_event)
        self.remove_action.triggered.connect(self.remove_selection)
        self.new_group_action.triggered.connect(self.add_event_group)
        self.clear_device_events_action.triggered.connect(self.clear_device_events)
        self.switch_sequence_action.triggered.connect(self.open_switch_sequence)
        self._select_initial_group()
        self.update_actions()

    @property
    def has_unapplied_changes(self) -> bool:
        """Report no transactional state because every edit is immediate.

        :return: Always ``False``.
        """
        return False

    def get_dynamic_editor_entry(self) -> DynamicEditorEntry:
        """Return the dynamic editor entry represented by this page.

        :return: Page entry.
        """
        return self.entry

    def get_dynamic_editor_mode(self) -> DynamicSimulationMode:
        """Return the page simulation mode.

        :return: RMS or EMT mode.
        """
        return self.mode

    def get_dynamic_editor_display_title(self) -> str:
        """Return the workspace title for this event page.

        :return: Device and simulation-mode title.
        """
        return f"{self.entry.display_name} [{self.mode.name} events]"

    def can_close_editor(self, parent: QtWidgets.QWidget | None = None) -> bool:
        """Allow immediate-edit pages to close without a save prompt.

        :param parent: Unused compatibility parent.
        :return: Always ``True``.
        """
        del parent
        return True

    def prepare_to_delete(self) -> None:
        """Release model references before Qt destroys the page.

        :return: None.
        """
        self.tree_view.setModel(None)
        self.groups_tree_view.setModel(None)

    def set_dark_mode(self) -> None:
        """Refresh both event views after a dark-theme change.

        :return: None.
        """
        self.groups_tree_view.viewport().update()
        self.tree_view.viewport().update()

    def set_light_mode(self) -> None:
        """Refresh both event views after a light-theme change.

        :return: None.
        """
        self.groups_tree_view.viewport().update()
        self.tree_view.viewport().update()

    def refresh_from_saved_model(self) -> int:
        """Refresh real groups and events after the dynamic model changes.

        :return: Zero because this direct editor does not reconcile drafts.
        """
        previous_group: RmsEventsGroup | EmtEventsGroup | None = self.selected_group
        self.group_model.rebuild()
        self._restore_group_selection(preferred_group=previous_group)
        return 0

    def _select_initial_group(self) -> None:
        """Select the first available real group after page construction.

        :return: None.
        """
        self._restore_group_selection(preferred_group=None)

    def _restore_group_selection(self,
                                 preferred_group: RmsEventsGroup | EmtEventsGroup | None) -> None:
        """Restore a surviving group selection or choose the first group.

        :param preferred_group: Group that should remain selected when possible.
        :return: None.
        """
        preferred_index: QtCore.QModelIndex = QtCore.QModelIndex()
        if preferred_group is not None:
            preferred_index = self.group_model.index_for_group(group=preferred_group)
        else:
            pass
        if not preferred_index.isValid() and self.group_model.rowCount() > 0:
            preferred_index = self.group_model.index(0, 0)
        else:
            pass
        if preferred_index.isValid():
            self.groups_tree_view.setCurrentIndex(preferred_index)
            self._on_group_selected(preferred_index, QtCore.QModelIndex())
        else:
            self.selected_group = None
            self._rebuild_events_table()

    @QtCore.Slot(QtCore.QModelIndex, QtCore.QModelIndex)
    def _on_group_selected(self,
                           current: QtCore.QModelIndex,
                           _previous: QtCore.QModelIndex) -> None:
        """Display the real events belonging to the selected group.

        :param current: Newly selected group index.
        :param _previous: Previously selected group index.
        :return: None.
        """
        self.selected_group = self.group_model.group_from_index(index=current)
        self._rebuild_events_table()
        self.update_actions()

    def _event_device_type(self) -> DeviceType:
        """Return the concrete event type represented by this page.

        :return: RMS or EMT event device type.
        """
        if self.mode == DynamicSimulationMode.RMS:
            return DeviceType.RmsEventDevice
        else:
            return DeviceType.EmtEventDevice

    def _rebuild_events_table(self) -> None:
        """Build the same generic object table used by Database.

        :return: None.
        """
        if self.selected_group is not None:
            events: List[RmsEvent | EmtEvent] = self.group_model.get_group_events(group=self.selected_group)
        else:
            events = list()
        template_event: EditableDevice
        dictionary_of_lists: dict[object, list[object]]
        template_event, dictionary_of_lists = self.circuit.get_dictionary_of_lists(
            elm_type=self._event_device_type()
        )
        dictionary_of_lists["parameter"] = list(self.parameters)

        # Reuse the event schema while exposing only the properties relevant to this focused editor.
        property_names: tuple[str, ...] = (
            "parameter",
            "time",
            "end_time",
            "value",
            "force_step_alignment",
            "transition_type",
        )
        event_properties: List[GCProp] = list()
        property_name: str
        for property_name in property_names:
            event_property: GCProp = template_event.get_property_by_name(prop_name=property_name)
            event_properties.append(event_property)

        self.objects_model = ObjectsModel(
            objects=events,
            property_list=event_properties,
            time_index=None,
            parent=self.tree_view,
            editable=True,
            dictionary_of_lists=dictionary_of_lists,
            properties_filter=PrpCat.All,
            error_msg_ptr=self.toast_manager.show_error_toast,
        )
        self.filter_model = ObjectModelFilterProxy(mdl=self.objects_model, parent=self)
        self.tree_view.setModel(self.filter_model)

    def _selected_event(self) -> RmsEvent | EmtEvent | None:
        """Return the real event selected in the generic table.

        :return: Selected real event or ``None``.
        """
        if self.filter_model is not None:
            current_index: QtCore.QModelIndex = self.tree_view.currentIndex()
            if current_index.isValid():
                event: object | None = self.filter_model.get_object_at_proxy_row(current_index.row())
                if isinstance(event, (RmsEvent, EmtEvent)):
                    return event
                else:
                    return None
            else:
                return None
        else:
            return None

    @QtCore.Slot(bool)
    def add_event_group(self, _checked: bool = False) -> None:
        """Ask for a name and immediately add one real event group.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        group_name: str
        accepted: bool
        group_name, accepted = QtWidgets.QInputDialog.getText(
            self,
            self.tr("Add Event Group"),
            self.tr("Group name:"),
        )
        normalized_name: str = group_name.strip()
        if accepted and normalized_name != "":
            existing_names: set[str] = set(group.name.casefold() for group in self.group_model.get_groups())
            if normalized_name.casefold() in existing_names:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid event group"),
                    self.tr("An event group with this name already exists."),
                )
            else:
                if self.mode == DynamicSimulationMode.RMS:
                    created_group: RmsEventsGroup | EmtEventsGroup = RmsEventsGroup(name=normalized_name)
                    self.circuit.add_rms_events_group(obj=created_group)
                else:
                    created_group = EmtEventsGroup(name=normalized_name)
                    self.circuit.add_emt_events_group(obj=created_group)
                self.group_model.rebuild()
                self._restore_group_selection(preferred_group=created_group)
        else:
            pass

    @QtCore.Slot(bool)
    def add_event(self, _checked: bool = False) -> None:
        """Immediately add one real event to the selected real group.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        if self.selected_group is None:
            self.toast_manager.show_warning_toast(self.tr("Select an event group before adding an event."))
        elif len(self.parameters) == 0:
            self.toast_manager.show_warning_toast(self.tr("The dynamic model has no event parameters."))
        else:
            parameter: Var = self.parameters[0]
            if self.mode == DynamicSimulationMode.RMS and isinstance(self.selected_group, RmsEventsGroup):
                created_event: RmsEvent | EmtEvent = RmsEvent(
                    name=f"RMS event {len(self.circuit.rms_events)}",
                    device=self.device,
                    parameter=parameter,
                    group=self.selected_group,
                    force_step_alignment=parameter.uid in self.mode_parameter_uids,
                )
                self.circuit.add_rms_event(obj=created_event)
            elif self.mode == DynamicSimulationMode.EMT and isinstance(self.selected_group, EmtEventsGroup):
                created_event = EmtEvent(
                    name=f"EMT event {len(self.circuit.emt_events)}",
                    device=self.device,
                    parameter=parameter,
                    group=self.selected_group,
                    force_step_alignment=parameter.uid in self.mode_parameter_uids,
                )
                self.circuit.add_emt_event(obj=created_event)
            else:
                return
            self.group_model.rebuild()
            self._restore_group_selection(preferred_group=self.selected_group)
            if self.filter_model is not None and self.filter_model.rowCount() > 0:
                new_index: QtCore.QModelIndex = self.filter_model.index(self.filter_model.rowCount() - 1, 0)
                self.tree_view.setCurrentIndex(new_index)
                self.tree_view.scrollTo(new_index)
            else:
                pass

    @QtCore.Slot(bool)
    def remove_selection(self, _checked: bool = False) -> None:
        """Immediately remove the selected real event or selected real group.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        selected_event: RmsEvent | EmtEvent | None = self._selected_event()
        if selected_event is not None:
            self._remove_event(event=selected_event)
        elif self.selected_group is not None:
            self._remove_group(group=self.selected_group)
        else:
            self.toast_manager.show_warning_toast(self.tr("Select an event or event group to remove."))

    def _remove_event(self, event: RmsEvent | EmtEvent) -> None:
        """Confirm and immediately remove one real event.

        :param event: Real event selected in the table.
        :return: None.
        """
        answer: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.question(
            self,
            self.tr("Remove event"),
            self.tr("Remove the selected event?"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            if isinstance(event, RmsEvent):
                self.circuit.delete_rms_event(obj=event)
            else:
                self.circuit.delete_emt_event(obj=event)
            self.group_model.rebuild()
            self._restore_group_selection(preferred_group=self.selected_group)
        else:
            pass

    def _remove_group(self, group: RmsEventsGroup | EmtEventsGroup) -> None:
        """Confirm and immediately remove one real group and its events.

        :param group: Real group selected in the tree.
        :return: None.
        """
        answer: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.question(
            self,
            self.tr("Remove event group"),
            self.tr("Remove '{name}' and all events in this group?").format(name=group.name),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            if isinstance(group, RmsEventsGroup):
                self.circuit.delete_rms_events_group(obj=group)
            else:
                self.circuit.delete_emt_events_group(obj=group)
            self.selected_group = None
            self.group_model.rebuild()
            self._restore_group_selection(preferred_group=None)
        else:
            pass

    @QtCore.Slot(bool)
    def clear_device_events(self, _checked: bool = False) -> None:
        """Immediately remove every page-device event in the current mode.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        if self.mode == DynamicSimulationMode.RMS:
            matching_events: List[RmsEvent | EmtEvent] = [
                event for event in self.circuit.rms_events if event.device is self.device
            ]
        else:
            matching_events = [event for event in self.circuit.emt_events if event.device is self.device]
        if len(matching_events) > 0:
            answer: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.question(
                self,
                self.tr("Delete all device events"),
                self.tr("Delete all events for this device and simulation mode?"),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                event: RmsEvent | EmtEvent
                for event in matching_events:
                    if isinstance(event, RmsEvent):
                        self.circuit.delete_rms_event(obj=event)
                    else:
                        self.circuit.delete_emt_event(obj=event)
                self.group_model.rebuild()
                self._restore_group_selection(preferred_group=self.selected_group)
            else:
                pass
        else:
            pass

    def update_actions(self) -> None:
        """Refresh action availability for current real-object selections.

        :return: None.
        """
        self.add_event_action.setEnabled(self.selected_group is not None and len(self.parameters) > 0)
        self.remove_action.setEnabled(self.selected_group is not None)
        if self.mode == DynamicSimulationMode.RMS:
            matching_count: int = len([event for event in self.circuit.rms_events if event.device is self.device])
        else:
            matching_count = len([event for event in self.circuit.emt_events if event.device is self.device])
        self.clear_device_events_action.setEnabled(matching_count > 0)
        self.switch_sequence_action.setEnabled(
            self.mode == DynamicSimulationMode.EMT
            and len(self._get_switch_mode_parameters()) > 0
            and len(self.circuit.emt_events_groups) > 0
        )

    def _get_switch_mode_parameters(self) -> List[Var]:
        """Return EMT switch-state parameters available on this page.

        :return: Ordered switch mode parameters.
        """
        mode_parameters: List[Var] = list()
        parameter: Var
        for parameter in self.parameters:
            if parameter.uid in self.mode_parameter_uids and parameter.name.startswith("switch_closed_mode_"):
                mode_parameters.append(parameter)
            else:
                pass
        return mode_parameters

    @QtCore.Slot(bool)
    def open_switch_sequence(self, _checked: bool = False) -> None:
        """Immediately create real EMT switch-sequence events.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        mode_parameters: List[Var] = self._get_switch_mode_parameters()
        groups: List[EmtEventsGroup] = list(self.circuit.emt_events_groups)
        if self.mode == DynamicSimulationMode.EMT and len(mode_parameters) > 0 and len(groups) > 0:
            dialog: SwitchSequenceDialog = SwitchSequenceDialog(
                mode_parameters=mode_parameters,
                events_groups=groups,
                parent=self,
            )
            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                sequence_data: SwitchSequenceData | None = dialog.get_typed_data()
                if sequence_data is not None:
                    sequence_index: int
                    for sequence_index in range(min(len(sequence_data.times), len(sequence_data.values))):
                        created_event: EmtEvent = EmtEvent(
                            name=f"EMT event {len(self.circuit.emt_events)}",
                            device=self.device,
                            parameter=sequence_data.parameter,
                            time=float(sequence_data.times[sequence_index]),
                            value=float(sequence_data.values[sequence_index]),
                            group=sequence_data.group,
                            force_step_alignment=True,
                            transition_type=DynamicEventTransitionType.Step,
                        )
                        self.circuit.add_emt_event(obj=created_event)
                    self.group_model.rebuild()
                    self._restore_group_selection(preferred_group=sequence_data.group)
                else:
                    pass
            else:
                pass
        else:
            pass
