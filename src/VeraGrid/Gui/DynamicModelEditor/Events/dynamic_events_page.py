# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_support import DynamicEventsGroupsDialog
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_support import collect_dynamic_events_page_parameters
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_support import SwitchSequenceData
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_support import SwitchSequenceDialog
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page_ui import Ui_DynamicEventsPage
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_models import (
    DynamicEventDraft,
    DynamicEventGroupDraft,
    DynamicEventsDraftSession,
)
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.toast_widget import ToastManager
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DynamicEventTransitionType, DynamicSimulationMode


def resolve_qt_checked_state(value: object) -> bool | None:
    """Normalize a Qt checkbox payload to a two-state boolean.

    PySide6 may deliver ``CheckStateRole`` values either as ``Qt.CheckState``
    members or as the corresponding integer stored in the Qt model variant.
    Partial and invalid states are rejected because dynamic-event controls are
    deliberately two-state checkboxes.

    :param value: Check-state payload received by ``setData``.
    :return: Checked boolean, or ``None`` when the payload is unsupported.
    """
    check_state: QtCore.Qt.CheckState
    if isinstance(value, QtCore.Qt.CheckState):
        check_state = value
    elif isinstance(value, int):
        if 0 <= value <= 2:
            check_state = QtCore.Qt.CheckState(value)
        else:
            return None
    else:
        return None

    if check_state == QtCore.Qt.CheckState.Checked:
        return True
    elif check_state == QtCore.Qt.CheckState.Unchecked:
        return False
    else:
        return None


class DynamicEventsTreeModel(QtGui.QStandardItemModel):
    """Flat editable event table for one device and simulation mode."""

    rebuilt = QtCore.Signal()

    __slots__ = (
        "session",
        "device",
        "mode",
        "parameters",
        "mode_parameter_uids",
    )

    COLUMN_EVENT_GROUP: int = 0
    COLUMN_PARAMETER: int = 1
    COLUMN_TIME: int = 2
    COLUMN_VALUE: int = 3
    COLUMN_TRANSITION: int = 4
    COLUMN_END_TIME: int = 5
    COLUMN_ALIGN_STEP: int = 6

    def __init__(self,
                 session: DynamicEventsDraftSession,
                 device: EditableDevice,
                 mode: DynamicSimulationMode,
                 parameters: list[Var],
                 mode_parameter_uids: set[int],
                 parent: QtCore.QObject | None = None) -> None:
        """Build a device-scoped event table over the shared transaction.

        :param session: Shared dynamic-events transaction.
        :param device: Device displayed by this page.
        :param mode: RMS or EMT family displayed by this page.
        :param parameters: Runtime parameters available in the current model.
        :param mode_parameter_uids: Parameters representing discrete modes.
        :param parent: Optional Qt owner.
        :return: None.
        """
        QtGui.QStandardItemModel.__init__(self, parent)
        self.session: DynamicEventsDraftSession = session
        self.device: EditableDevice = device
        self.mode: DynamicSimulationMode = mode
        self.parameters: list[Var] = list(parameters)
        self.mode_parameter_uids: set[int] = set(mode_parameter_uids)
        self.setHorizontalHeaderLabels(
            list((
                self.tr("Event Group"),
                self.tr("Parameter"),
                self.tr("Time"),
                self.tr("New Value"),
                self.tr("Transition"),
                self.tr("End Time"),
                self.tr("Align Step"),
            ))
        )
        self.session.changed.connect(self.rebuild)
        self.session.group_changed.connect(self.rebuild)
        self.rebuild()

    @QtCore.Slot()
    @QtCore.Slot(object)
    def rebuild(self, _changed_object: object | None = None) -> None:
        """Rebuild the flat rows for the page device and simulation mode.

        :param _changed_object: Optional changed group supplied by the shared session.
        :return: None.
        """
        row_count: int = self.rowCount()
        if row_count > 0:
            self.removeRows(0, row_count)
        else:
            pass

        event: DynamicEventDraft
        for event in self.session.get_events_for_device(self.device, self.mode):
            self.appendRow(self._build_event_row(event))
        self.rebuilt.emit()

    def replace_parameters(self,
                           parameters: list[Var],
                           mode_parameter_uids: set[int],
                           rebuild: bool) -> None:
        """Replace saved-model parameter references used by this table.

        :param parameters: Current event parameters from the saved model.
        :param mode_parameter_uids: Current discrete-mode parameter UIDs.
        :param rebuild: Whether the visible table must rebuild immediately.
        :return: None.
        """
        self.parameters = list(parameters)
        self.mode_parameter_uids = set(mode_parameter_uids)
        if rebuild:
            self.rebuild()
        else:
            pass

    def _build_event_row(self, event: DynamicEventDraft) -> list[QtGui.QStandardItem]:
        """Build one event table row from the transaction values.

        :param event: Event transaction record represented by the row.
        :return: Complete seven-column item row.
        """
        items: list[QtGui.QStandardItem] = list()
        column_index: int
        for column_index in range(self.columnCount()):
            item: QtGui.QStandardItem = QtGui.QStandardItem()
            item.setData(event, QtCore.Qt.ItemDataRole.UserRole)
            items.append(item)

        if event.group is None:
            group_text: str = self.tr("Select Event Group")
        else:
            group_text = event.group.name
        items[self.COLUMN_EVENT_GROUP].setText(group_text)
        if event.parameter is None:
            parameter_text: str = self.tr("Invalid parameter")
        else:
            parameter_text = event.parameter.name
        items[self.COLUMN_PARAMETER].setText(parameter_text)
        items[self.COLUMN_TIME].setText(f"{event.time:.4f} s")
        items[self.COLUMN_VALUE].setText(f"{event.value:.6f}")
        items[self.COLUMN_TRANSITION].setText(event.transition_type.name)
        if event.transition_type == DynamicEventTransitionType.Ramp and event.end_time is not None:
            items[self.COLUMN_END_TIME].setText(f"{event.end_time:.4f} s")
        else:
            items[self.COLUMN_END_TIME].setText("")

        align_item: QtGui.QStandardItem = items[self.COLUMN_ALIGN_STEP]
        if self._event_uses_mode_parameter(event):
            align_item.setCheckable(True)
            if event.force_step_alignment:
                align_item.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                align_item.setCheckState(QtCore.Qt.CheckState.Unchecked)
        else:
            align_item.setCheckable(False)
        return items

    def backing_object(self, index: QtCore.QModelIndex) -> object | None:
        """Return the event draft represented by a row.

        :param index: Any cell index in the requested row.
        :return: Backing event draft or ``None``.
        """
        if not index.isValid():
            return None
        else:
            return QtGui.QStandardItemModel.data(
                self,
                index.siblingAtColumn(self.COLUMN_EVENT_GROUP),
                QtCore.Qt.ItemDataRole.UserRole,
            )

    def index_for_backing_object(self, backing_object: object) -> QtCore.QModelIndex:
        """Locate the Event Group index representing one draft object.

        :param backing_object: Group or event draft to locate by identity.
        :return: Matching table index, or an invalid index when absent.
        """
        row_count: int = self.rowCount()
        row_index: int
        for row_index in range(row_count):
            candidate_index: QtCore.QModelIndex = self.index(row_index, self.COLUMN_EVENT_GROUP)
            candidate_backing: object | None = self.backing_object(candidate_index)
            if candidate_backing is backing_object:
                return candidate_index
            else:
                pass
        return QtCore.QModelIndex()

    def _parameter_is_available(self, parameter: Var | None) -> bool:
        """Return whether a symbolic parameter still belongs to the current model.

        :param parameter: Parameter referenced by an event.
        :return: Whether the exact symbolic object is available for editing.
        """
        if parameter is None:
            return False
        else:
            pass
        available_parameter: Var
        for available_parameter in self.parameters:
            if available_parameter is parameter:
                return True
            else:
                pass
        return False

    def _event_uses_mode_parameter(self, event: DynamicEventDraft) -> bool:
        """Return whether an event targets a discrete mode parameter.

        :param event: Event draft to inspect.
        :return: Whether step alignment is applicable.
        """
        return event.parameter is not None and event.parameter.uid in self.mode_parameter_uids

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """Expose edits supported by event table rows.

        :param index: Table cell queried by Qt.
        :return: Item flags for selection, editing or check-state changes.
        """
        backing: object | None = self.backing_object(index)
        base_flags: QtCore.Qt.ItemFlag = (
            QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        )
        if isinstance(backing, DynamicEventDraft):
            if index.column() == self.COLUMN_EVENT_GROUP:
                has_groups: bool = len(self.session.get_groups(self.mode)) > 0
                if has_groups:
                    return base_flags | QtCore.Qt.ItemFlag.ItemIsEditable
                else:
                    return base_flags
            elif index.column() == self.COLUMN_PARAMETER and not self._parameter_is_available(backing.parameter):
                return base_flags
            elif index.column() == self.COLUMN_ALIGN_STEP:
                if self._event_uses_mode_parameter(backing):
                    return base_flags | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                else:
                    return base_flags
            elif index.column() == self.COLUMN_END_TIME:
                if backing.transition_type == DynamicEventTransitionType.Ramp:
                    return base_flags | QtCore.Qt.ItemFlag.ItemIsEditable
                else:
                    return base_flags
            else:
                return base_flags | QtCore.Qt.ItemFlag.ItemIsEditable
        else:
            return base_flags

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = QtCore.Qt.ItemDataRole.EditRole) -> bool:
        """Apply one inline edit to the shared transaction record.

        :param index: Edited group or event cell.
        :param value: Typed value supplied by the delegate.
        :param role: Qt edit or check-state role.
        :return: Whether the transaction accepted the edit.
        """
        backing: object | None = self.backing_object(index)
        if isinstance(backing, DynamicEventDraft):
            accepted: bool = self._set_event_data(backing, index.column(), value, role)
            if accepted:
                self._refresh_event_row(index, backing)
                self.session.mark_changed(rebuild=False)
            else:
                pass
            return accepted
        else:
            return False

    def _refresh_event_row(self,
                           index: QtCore.QModelIndex,
                           event: DynamicEventDraft) -> None:
        """Refresh one edited event row without rebuilding the whole table.

        Event values are device-page-local, so an inline edit does not require
        a structural broadcast to other tabs. Keeping the existing model
        indexes alive prevents editors and selection from disappearing while a
        cell is being committed.

        :param index: Any index in the edited event row.
        :param event: Event draft containing the accepted values.
        :return: None.
        """
        group_index: QtCore.QModelIndex = index.siblingAtColumn(self.COLUMN_EVENT_GROUP)
        parameter_index: QtCore.QModelIndex = index.siblingAtColumn(self.COLUMN_PARAMETER)
        time_index: QtCore.QModelIndex = index.siblingAtColumn(self.COLUMN_TIME)
        value_index: QtCore.QModelIndex = index.siblingAtColumn(self.COLUMN_VALUE)
        transition_index: QtCore.QModelIndex = index.siblingAtColumn(self.COLUMN_TRANSITION)
        end_time_index: QtCore.QModelIndex = index.siblingAtColumn(self.COLUMN_END_TIME)
        align_index: QtCore.QModelIndex = index.siblingAtColumn(self.COLUMN_ALIGN_STEP)
        if event.group is None:
            group_text: str = self.tr("Select Event Group")
        else:
            group_text = event.group.name
        QtGui.QStandardItemModel.setData(
            self,
            group_index,
            group_text,
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        if event.parameter is None:
            parameter_text: str = self.tr("Invalid parameter")
        else:
            parameter_text = event.parameter.name
        QtGui.QStandardItemModel.setData(
            self,
            parameter_index,
            parameter_text,
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        QtGui.QStandardItemModel.setData(
            self,
            time_index,
            f"{event.time:.4f} s",
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        QtGui.QStandardItemModel.setData(
            self,
            value_index,
            f"{event.value:.6f}",
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        QtGui.QStandardItemModel.setData(
            self,
            transition_index,
            event.transition_type.name,
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        if event.transition_type == DynamicEventTransitionType.Ramp and event.end_time is not None:
            end_time_text: str = f"{event.end_time:.4f} s"
        else:
            end_time_text = ""
        QtGui.QStandardItemModel.setData(
            self,
            end_time_index,
            end_time_text,
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        if self._event_uses_mode_parameter(event):
            if event.force_step_alignment:
                check_state: QtCore.Qt.CheckState = QtCore.Qt.CheckState.Checked
            else:
                check_state = QtCore.Qt.CheckState.Unchecked
            QtGui.QStandardItemModel.setData(
                self,
                align_index,
                check_state,
                QtCore.Qt.ItemDataRole.CheckStateRole,
            )
        else:
            QtGui.QStandardItemModel.setData(
                self,
                align_index,
                None,
                QtCore.Qt.ItemDataRole.CheckStateRole,
            )

    def _set_event_data(self,
                        event: DynamicEventDraft,
                        column: int,
                        value: object,
                        role: int) -> bool:
        """Apply one typed event-cell value to its transaction record.

        :param event: Event draft being edited.
        :param column: Logical event column.
        :param value: Delegate value.
        :param role: Qt edit or check-state role.
        :return: Whether the value type and column are valid.
        """
        if column == self.COLUMN_EVENT_GROUP and role == QtCore.Qt.ItemDataRole.EditRole:
            if isinstance(value, DynamicEventGroupDraft):
                return self.session.set_event_group(event=event, group=value)
            else:
                return False
        elif column == self.COLUMN_PARAMETER and role == QtCore.Qt.ItemDataRole.EditRole:
            if isinstance(value, Var):
                event.parameter = value
                event.force_step_alignment = value.uid in self.mode_parameter_uids
                return True
            else:
                return False
        elif column == self.COLUMN_TIME and role == QtCore.Qt.ItemDataRole.EditRole:
            if isinstance(value, (float, int)):
                event.time = float(value)
                return True
            else:
                return False
        elif column == self.COLUMN_VALUE and role == QtCore.Qt.ItemDataRole.EditRole:
            if isinstance(value, (float, int)):
                event.value = float(value)
                return True
            else:
                return False
        elif column == self.COLUMN_TRANSITION and role == QtCore.Qt.ItemDataRole.EditRole:
            if isinstance(value, DynamicEventTransitionType):
                event.transition_type = value
                if value == DynamicEventTransitionType.Ramp and event.end_time is None:
                    event.end_time = event.time
                elif value == DynamicEventTransitionType.Step:
                    event.end_time = None
                else:
                    pass
                return True
            else:
                return False
        elif column == self.COLUMN_END_TIME and role == QtCore.Qt.ItemDataRole.EditRole:
            if isinstance(value, (float, int)):
                event.end_time = float(value)
                return True
            else:
                return False
        elif column == self.COLUMN_ALIGN_STEP and role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if self._event_uses_mode_parameter(event):
                force_step_alignment: bool | None = resolve_qt_checked_state(value)
                if force_step_alignment is not None:
                    event.force_step_alignment = force_step_alignment
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False


class DynamicEventsFilterProxyModel(QtCore.QSortFilterProxyModel):
    """Filter event rows by group, parameter and transition selections."""

    filterChanged = QtCore.Signal()

    __slots__ = ("_selected_values",)

    FILTER_COLUMNS: tuple[int, ...] = (
        DynamicEventsTreeModel.COLUMN_EVENT_GROUP,
        DynamicEventsTreeModel.COLUMN_PARAMETER,
        DynamicEventsTreeModel.COLUMN_TRANSITION,
    )
    NO_GROUP_TEXT: str = "No Event Group"
    INVALID_PARAMETER_TEXT: str = "Invalid parameter"

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        """Create an initially unrestricted event filter.

        :param parent: Optional Qt owner.
        :return: None.
        """
        QtCore.QSortFilterProxyModel.__init__(self, parent)
        self._selected_values: dict[int, set[str]] = dict()
        column: int
        for column in self.FILTER_COLUMNS:
            self._selected_values[column] = set()
        self.setDynamicSortFilter(True)

    def selected_values(self, column: int) -> set[str]:
        """Return a copy of the active values for one filter column.

        :param column: Source-model column whose filter is requested.
        :return: Selected display values, or an empty set for All.
        """
        values: set[str] | None = self._selected_values.get(column, None)
        if values is None:
            return set()
        else:
            return set(values)

    def set_selected_values(self, column: int, values: set[str]) -> None:
        """Replace one column filter and refresh the visible rows.

        :param column: Source-model column to filter.
        :param values: Accepted display values; empty means All.
        :return: None.
        """
        if column in self.FILTER_COLUMNS:
            self._selected_values[column] = set(values)
            self.invalidateRowsFilter()
            self.filterChanged.emit()
        else:
            pass

    def clear_filters(self) -> None:
        """Restore All for every filterable column.

        :return: None.
        """
        changed: bool = False
        column: int
        for column in self.FILTER_COLUMNS:
            if len(self._selected_values[column]) > 0:
                self._selected_values[column] = set()
                changed = True
            else:
                pass
        if changed:
            self.invalidateRowsFilter()
            self.filterChanged.emit()
        else:
            pass

    def available_values(self, column: int) -> list[str]:
        """Collect sorted unique values from every source event row.

        Values come from the unfiltered source model so filters in other
        columns never hide choices from the popup.

        :param column: Filterable source-model column.
        :return: Alphabetically sorted unique display values.
        """
        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        values: set[str] = set()
        if isinstance(source_model, DynamicEventsTreeModel) and column in self.FILTER_COLUMNS:
            row: int
            for row in range(source_model.rowCount()):
                event_index: QtCore.QModelIndex = source_model.index(
                    row,
                    DynamicEventsTreeModel.COLUMN_EVENT_GROUP,
                )
                event: object | None = source_model.backing_object(event_index)
                if isinstance(event, DynamicEventDraft):
                    values.add(self._event_filter_value(event, column))
                else:
                    pass
        else:
            pass
        return sorted(values, key=str.casefold)

    def reconcile_selected_values(self) -> None:
        """Remove selected values that no longer exist in the source model.

        :return: None.
        """
        changed: bool = False
        column: int
        for column in self.FILTER_COLUMNS:
            selected: set[str] = self._selected_values[column]
            if len(selected) > 0:
                available: set[str] = set(self.available_values(column))
                reconciled: set[str] = selected.intersection(available)
                if reconciled != selected:
                    self._selected_values[column] = reconciled
                    changed = True
                else:
                    pass
            else:
                pass
        if changed:
            self.invalidateRowsFilter()
            self.filterChanged.emit()
        else:
            pass

    def is_filter_active(self, column: int) -> bool:
        """Return whether a column currently restricts visible rows.

        :param column: Source-model column to inspect.
        :return: ``True`` when at least one explicit value is selected.
        """
        return len(self.selected_values(column)) > 0

    def filterAcceptsRow(self,
                         source_row: int,
                         source_parent: QtCore.QModelIndex) -> bool:
        """Apply OR within each column and AND across filter columns.

        :param source_row: Candidate source-model row.
        :param source_parent: Candidate source parent index.
        :return: Whether the event satisfies every active column filter.
        """
        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if not isinstance(source_model, DynamicEventsTreeModel):
            return True
        else:
            event_index: QtCore.QModelIndex = source_model.index(
                source_row,
                DynamicEventsTreeModel.COLUMN_EVENT_GROUP,
                source_parent,
            )
            event: object | None = source_model.backing_object(event_index)
        if not isinstance(event, DynamicEventDraft):
            return False
        else:
            pass
        column: int
        for column in self.FILTER_COLUMNS:
            selected: set[str] = self._selected_values[column]
            if len(selected) > 0 and self._event_filter_value(event, column) not in selected:
                return False
            else:
                pass
        return True

    def _event_filter_value(self, event: DynamicEventDraft, column: int) -> str:
        """Return the stable displayed filter value for one event column.

        :param event: Event draft represented by a source row.
        :param column: Filterable source-model column.
        :return: Group, parameter or transition label.
        """
        if column == DynamicEventsTreeModel.COLUMN_EVENT_GROUP:
            if event.group is None:
                return self.tr(self.NO_GROUP_TEXT)
            else:
                return event.group.name
        elif column == DynamicEventsTreeModel.COLUMN_PARAMETER:
            if event.parameter is None:
                return self.tr(self.INVALID_PARAMETER_TEXT)
            else:
                return event.parameter.name
        elif column == DynamicEventsTreeModel.COLUMN_TRANSITION:
            return event.transition_type.name
        else:
            return ""


class DynamicEventsFilterPopup(QtWidgets.QMenu):
    """Display persistent multi-selection choices for one header column."""

    filterSelectionChanged = QtCore.Signal(int, object)

    __slots__ = ("column", "all_item", "values_list")

    def __init__(self,
                 column: int,
                 available_values: list[str],
                 selected_values: set[str],
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Build a popup whose selected rows remain visibly highlighted.

        :param column: Filterable model column represented by the popup.
        :param available_values: Values present in the complete source model.
        :param selected_values: Values currently accepted by the filter.
        :param parent: Optional owning widget.
        :return: None.
        """
        QtWidgets.QMenu.__init__(self, parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.column: int = column
        self.values_list: QtWidgets.QListWidget = QtWidgets.QListWidget(self)
        self.values_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.MultiSelection
        )
        self.all_item: QtWidgets.QListWidgetItem = QtWidgets.QListWidgetItem(
            self.tr("All"),
            self.values_list,
        )
        value: str
        for value in available_values:
            item: QtWidgets.QListWidgetItem = QtWidgets.QListWidgetItem(value, self.values_list)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, value)
            item.setSelected(value in selected_values)
        if len(selected_values) == 0:
            self.all_item.setSelected(True)
        else:
            self.all_item.setSelected(False)
        row_height: int = self.values_list.sizeHintForRow(0)
        visible_rows: int = min(self.values_list.count(), 10)
        self.values_list.setMinimumWidth(190)
        self.values_list.setFixedHeight(max(row_height, 22) * visible_rows + 6)
        widget_action: QtWidgets.QWidgetAction = QtWidgets.QWidgetAction(self)
        widget_action.setDefaultWidget(self.values_list)
        self.addAction(widget_action)
        self.values_list.itemClicked.connect(self._on_item_clicked)

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _on_item_clicked(self, clicked_item: QtWidgets.QListWidgetItem) -> None:
        """Enforce All semantics and publish the current explicit values.

        :param clicked_item: List entry whose selection was toggled by Qt.
        :return: None.
        """
        if clicked_item is self.all_item:
            self.values_list.clearSelection()
            self.all_item.setSelected(True)
        else:
            self.all_item.setSelected(False)
            selected_specific_items: list[QtWidgets.QListWidgetItem] = list()
            selected_item: QtWidgets.QListWidgetItem
            for selected_item in self.values_list.selectedItems():
                if selected_item is not self.all_item:
                    selected_specific_items.append(selected_item)
                else:
                    pass
            if len(selected_specific_items) == 0:
                self.all_item.setSelected(True)
            else:
                pass
        selected_values: set[str] = set()
        item: QtWidgets.QListWidgetItem
        for item in self.values_list.selectedItems():
            value: object | None = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if item is not self.all_item and isinstance(value, str):
                selected_values.add(value)
            else:
                pass
        self.filterSelectionChanged.emit(self.column, selected_values)


class DynamicEventsFilterHeader(QtWidgets.QHeaderView):
    """Show filter indicators and open multi-selection popups on header clicks."""

    __slots__ = (
        "filter_model",
        "event_group_indicator",
        "parameter_indicator",
        "transition_indicator",
    )

    def __init__(self,
                 filter_model: DynamicEventsFilterProxyModel,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Create a horizontal header attached to an event filter proxy.

        :param filter_model: Proxy receiving popup selections.
        :param parent: Optional owning widget.
        :return: None.
        """
        QtWidgets.QHeaderView.__init__(self, QtCore.Qt.Orientation.Horizontal, parent)
        self.filter_model: DynamicEventsFilterProxyModel = filter_model
        self.setSectionsClickable(True)
        self.event_group_indicator: QtWidgets.QLabel = self._create_filter_indicator()
        self.parameter_indicator: QtWidgets.QLabel = self._create_filter_indicator()
        self.transition_indicator: QtWidgets.QLabel = self._create_filter_indicator()
        self.sectionResized.connect(self._position_filter_indicators)
        self.sectionMoved.connect(self._position_filter_indicators)
        self.geometriesChanged.connect(self._position_filter_indicators)
        self._position_filter_indicators()

    def _create_filter_indicator(self) -> QtWidgets.QLabel:
        """Create one mouse-transparent downward filter marker.

        :return: Label owned by the header viewport.
        """
        indicator: QtWidgets.QLabel = QtWidgets.QLabel("\N{BLACK DOWN-POINTING SMALL TRIANGLE}", self.viewport())
        indicator.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        indicator.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        indicator.setFixedWidth(16)
        indicator.setStyleSheet("background: transparent; font-size: 11px;")
        indicator.show()
        indicator.raise_()
        return indicator

    def _indicator_for_column(self, column: int) -> QtWidgets.QLabel | None:
        """Return the visible marker assigned to a filterable column.

        :param column: Logical event-table column.
        :return: Matching marker, or ``None`` for a non-filterable column.
        """
        if column == DynamicEventsTreeModel.COLUMN_EVENT_GROUP:
            return self.event_group_indicator
        elif column == DynamicEventsTreeModel.COLUMN_PARAMETER:
            return self.parameter_indicator
        elif column == DynamicEventsTreeModel.COLUMN_TRANSITION:
            return self.transition_indicator
        else:
            return None

    @QtCore.Slot()
    @QtCore.Slot(int, int, int)
    def _position_filter_indicators(self,
                                    _logical_index: int = -1,
                                    _old_size: int = 0,
                                    _new_size: int = 0) -> None:
        """Anchor every marker to the right edge of its current section.

        :param _logical_index: Optional resized or moved logical section.
        :param _old_size: Optional previous section size.
        :param _new_size: Optional new section size or visual index.
        :return: None.
        """
        column: int
        for column in DynamicEventsFilterProxyModel.FILTER_COLUMNS:
            indicator: QtWidgets.QLabel | None = self._indicator_for_column(column)
            if indicator is not None:
                section_left: int = self.sectionViewportPosition(column)
                section_width: int = self.sectionSize(column)
                indicator.move(
                    section_left + section_width - indicator.width() - 3,
                    0,
                )
                indicator.setFixedHeight(self.height())
                if self.filter_model.is_filter_active(column):
                    indicator_color: QtGui.QColor = self.palette().color(
                        QtGui.QPalette.ColorRole.Highlight
                    )
                else:
                    indicator_color = self.palette().color(
                        QtGui.QPalette.ColorRole.ButtonText
                    )
                indicator_palette: QtGui.QPalette = indicator.palette()
                indicator_palette.setColor(
                    QtGui.QPalette.ColorRole.WindowText,
                    indicator_color,
                )
                indicator.setPalette(indicator_palette)
                indicator.raise_()
            else:
                pass

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Keep markers aligned when the complete header changes size.

        :param event: Header resize event.
        :return: None.
        """
        QtWidgets.QHeaderView.resizeEvent(self, event)
        self._position_filter_indicators()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        """Keep markers aligned while the table scrolls horizontally.

        :param dx: Horizontal scroll delta.
        :param dy: Vertical scroll delta.
        :return: None.
        """
        QtWidgets.QHeaderView.scrollContentsBy(self, dx, dy)
        self._position_filter_indicators()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Open the clicked filter column popup.

        :param event: Header mouse press event.
        :return: None.
        """
        logical_index: int = self.logicalIndexAt(event.position().toPoint())
        if (
            event.button() == QtCore.Qt.MouseButton.LeftButton
            and logical_index in DynamicEventsFilterProxyModel.FILTER_COLUMNS
        ):
            popup: DynamicEventsFilterPopup = DynamicEventsFilterPopup(
                column=logical_index,
                available_values=self.filter_model.available_values(logical_index),
                selected_values=self.filter_model.selected_values(logical_index),
                parent=self,
            )
            popup.filterSelectionChanged.connect(self._apply_filter_selection)
            section_left: int = self.sectionViewportPosition(logical_index)
            popup_position: QtCore.QPoint = self.viewport().mapToGlobal(
                QtCore.QPoint(section_left, self.height())
            )
            popup.popup(popup_position)
        else:
            QtWidgets.QHeaderView.mousePressEvent(self, event)

    @QtCore.Slot(int, object)
    def _apply_filter_selection(self, column: int, values_object: object) -> None:
        """Apply a typed popup selection and repaint its header section.

        :param column: Filterable model column.
        :param values_object: Set of selected string values emitted by the popup.
        :return: None.
        """
        if isinstance(values_object, set):
            values: set[str] = set()
            value: object
            for value in values_object:
                if isinstance(value, str):
                    values.add(value)
                else:
                    pass
            self.filter_model.set_selected_values(column, values)
            self._position_filter_indicators()
            self.viewport().update()
        else:
            pass


class DynamicEventsItemDelegate(QtWidgets.QStyledItemDelegate):
    """Provide typed editors for dynamic-event table cells."""

    __slots__ = ()

    def _source_context(self,
                        index: QtCore.QModelIndex) -> tuple[DynamicEventsTreeModel | None,
                                                            QtCore.QModelIndex]:
        """Resolve a view index to the editable source event model.

        :param index: Direct-source or filter-proxy model index.
        :return: Source model and mapped source index, or an invalid context.
        """
        model: QtCore.QAbstractItemModel | None = index.model()
        if isinstance(model, DynamicEventsTreeModel):
            return model, index
        elif isinstance(model, DynamicEventsFilterProxyModel):
            source_model: QtCore.QAbstractItemModel | None = model.sourceModel()
            if isinstance(source_model, DynamicEventsTreeModel):
                return source_model, model.mapToSource(index)
            else:
                return None, QtCore.QModelIndex()
        else:
            return None, QtCore.QModelIndex()

    def createEditor(self,
                     parent: QtWidgets.QWidget,
                     option: QtWidgets.QStyleOptionViewItem,
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget | None:
        """Create the editor appropriate for one event table cell.

        :param parent: Delegate editor parent.
        :param option: Native style options.
        :param index: Edited table cell.
        :return: Typed editor widget, or ``None`` for check-state cells.
        """
        del option
        model: DynamicEventsTreeModel | None
        source_index: QtCore.QModelIndex
        model, source_index = self._source_context(index)
        if model is None:
            return None
        else:
            backing: object | None = model.backing_object(source_index)
        if not isinstance(backing, DynamicEventDraft):
            return None
        elif index.column() == model.COLUMN_EVENT_GROUP:
            group_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
            group: DynamicEventGroupDraft
            for group in model.session.get_groups(model.mode):
                group_combo.addItem(group.name, group)
            group_combo.activated.connect(self._commit_combo_editor)
            return group_combo
        elif index.column() == model.COLUMN_PARAMETER:
            combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
            parameter: Var
            for parameter in model.parameters:
                combo.addItem(parameter.name, parameter)
            combo.activated.connect(self._commit_combo_editor)
            return combo
        elif index.column() in (model.COLUMN_TIME, model.COLUMN_END_TIME):
            time_spin: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(parent)
            time_spin.setDecimals(4)
            time_spin.setRange(0.0, 1.0e9)
            time_spin.setSingleStep(0.1)
            time_spin.setSuffix(" s")
            return time_spin
        elif index.column() == model.COLUMN_VALUE:
            value_spin: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(parent)
            value_spin.setDecimals(6)
            value_spin.setRange(-1.0e9, 1.0e9)
            value_spin.setSingleStep(0.01)
            return value_spin
        elif index.column() == model.COLUMN_TRANSITION:
            transition_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
            transition_combo.addItem(self.tr("Step"), DynamicEventTransitionType.Step)
            transition_combo.addItem(self.tr("Ramp"), DynamicEventTransitionType.Ramp)
            transition_combo.activated.connect(self._commit_combo_editor)
            return transition_combo
        else:
            return None

    @QtCore.Slot(int)
    def _commit_combo_editor(self, _index: int) -> None:
        """Commit a combo selection immediately, including persistent editors.

        :param _index: Newly activated combo index supplied by Qt.
        :return: None.
        """
        editor: QtCore.QObject | None = self.sender()
        if isinstance(editor, QtWidgets.QComboBox):
            self.commitData.emit(editor)
        else:
            pass

    def setEditorData(self,
                      editor: QtWidgets.QWidget,
                      index: QtCore.QModelIndex) -> None:
        """Populate a typed editor from the selected transaction value.

        :param editor: Editor created for the cell.
        :param index: Edited table cell.
        :return: None.
        """
        model: DynamicEventsTreeModel | None
        source_index: QtCore.QModelIndex
        model, source_index = self._source_context(index)
        if model is None:
            return
        else:
            backing: object | None = model.backing_object(source_index)
        if isinstance(backing, DynamicEventDraft):
            self._set_event_editor_data(editor, index.column(), backing)
        else:
            pass

    def _set_event_editor_data(self,
                               editor: QtWidgets.QWidget,
                               column: int,
                               event: DynamicEventDraft) -> None:
        """Populate one event editor from its typed draft value.

        :param editor: Event-cell editor.
        :param column: Logical event column.
        :param event: Event draft being edited.
        :return: None.
        """
        if column == DynamicEventsTreeModel.COLUMN_EVENT_GROUP and isinstance(editor, QtWidgets.QComboBox):
            group_index: int = editor.findData(event.group)
            editor.setCurrentIndex(group_index)
        elif column == DynamicEventsTreeModel.COLUMN_PARAMETER and isinstance(editor, QtWidgets.QComboBox):
            parameter_index: int = editor.findData(event.parameter)
            editor.setCurrentIndex(parameter_index)
        elif column == DynamicEventsTreeModel.COLUMN_TIME and isinstance(editor, QtWidgets.QDoubleSpinBox):
            editor.setValue(event.time)
        elif column == DynamicEventsTreeModel.COLUMN_VALUE and isinstance(editor, QtWidgets.QDoubleSpinBox):
            editor.setValue(event.value)
        elif column == DynamicEventsTreeModel.COLUMN_TRANSITION and isinstance(editor, QtWidgets.QComboBox):
            transition_index: int = editor.findData(event.transition_type)
            editor.setCurrentIndex(transition_index)
        elif column == DynamicEventsTreeModel.COLUMN_END_TIME and isinstance(editor, QtWidgets.QDoubleSpinBox):
            if event.end_time is not None:
                editor.setValue(event.end_time)
            else:
                editor.setValue(event.time)
        else:
            pass

    def setModelData(self,
                     editor: QtWidgets.QWidget,
                     model: QtCore.QAbstractItemModel,
                     index: QtCore.QModelIndex) -> None:
        """Commit one typed editor value to the transaction model.

        :param editor: Editor containing the user value.
        :param model: Dynamic events table model.
        :param index: Edited table cell.
        :return: None.
        """
        source_model: DynamicEventsTreeModel | None
        source_index: QtCore.QModelIndex
        source_model, source_index = self._source_context(index)
        if source_model is None:
            return
        else:
            backing: object | None = source_model.backing_object(source_index)
        if isinstance(backing, DynamicEventDraft):
            if isinstance(editor, QtWidgets.QComboBox):
                source_model.setData(
                    source_index,
                    editor.currentData(),
                    QtCore.Qt.ItemDataRole.EditRole,
                )
            elif isinstance(editor, QtWidgets.QDoubleSpinBox):
                source_model.setData(
                    source_index,
                    editor.value(),
                    QtCore.Qt.ItemDataRole.EditRole,
                )
            else:
                pass
        else:
            pass


class DynamicEventsPage(QtWidgets.QWidget):
    """One tab page displaying every event for a device and simulation mode."""

    dirtyStateChanged = QtCore.Signal(bool)

    __slots__ = (
        "session",
        "entry",
        "device",
        "mode",
        "parameters",
        "mode_parameter_uids",
        "model_is_empty",
        "ui",
        "empty_model_message",
        "tree_model",
        "filter_model",
        "filter_header",
        "tree_view",
        "switch_sequence_action",
        "add_event_action",
        "remove_action",
        "new_group_action",
        "save_button",
        "toast_manager",
        "_prepared_to_delete",
    )

    def __init__(self,
                 session: DynamicEventsDraftSession,
                 entry: DynamicEditorEntry,
                 device: EditableDevice,
                 mode: DynamicSimulationMode,
                 parameters: list[Var],
                 mode_parameter_uids: set[int],
                 model_is_empty: bool,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Build one device/mode event editor page.

        :param session: Shared dynamic-events transaction.
        :param entry: Device represented by the page.
        :param device: Concrete network device targeted by the page events.
        :param mode: RMS or EMT family represented by the page.
        :param parameters: Runtime parameters available in the current model.
        :param mode_parameter_uids: Parameters representing discrete modes.
        :param model_is_empty: Whether the underlying symbolic block is structurally empty.
        :param parent: Optional owning widget.
        :return: None.
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.session: DynamicEventsDraftSession = session
        self.entry: DynamicEditorEntry = entry
        self.device: EditableDevice = device
        self.mode: DynamicSimulationMode = mode
        self.parameters: list[Var] = list(parameters)
        self.mode_parameter_uids: set[int] = set(mode_parameter_uids)
        self.model_is_empty: bool = bool(model_is_empty)
        self._prepared_to_delete: bool = False
        self.toast_manager: ToastManager = ToastManager(parent=self, position_top=False)
        self.ui: Ui_DynamicEventsPage = Ui_DynamicEventsPage()
        self.ui.setupUi(self)

        # Keep explicit typed aliases for the page behavior while the generated
        # UI object remains the declarative owner of widget construction.
        self.empty_model_message: QtWidgets.QLabel = self.ui.emptyModelMessage
        self.tree_view: QtWidgets.QTableView = self.ui.eventsTableView
        self.switch_sequence_action: QtGui.QAction = self.ui.actionSwitchSequence
        self.add_event_action: QtGui.QAction = self.ui.actionAddEvent
        self.remove_action: QtGui.QAction = self.ui.actionRemove
        self.new_group_action: QtGui.QAction = self.ui.actionNewGroup
        self.save_button: QtWidgets.QPushButton = self.ui.saveButton

        # The empty-state label overlays the table without intercepting input,
        # so existing rows remain interactive while the message is visible.
        self.empty_model_message.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        self.empty_model_message.setVisible(self.model_is_empty)
        self.empty_model_message.raise_()
        self.switch_sequence_action.setVisible(self.mode == DynamicSimulationMode.EMT)

        self.tree_model: DynamicEventsTreeModel = DynamicEventsTreeModel(
            session=session,
            device=self.device,
            mode=mode,
            parameters=self.parameters,
            mode_parameter_uids=self.mode_parameter_uids,
            parent=self,
        )
        self.filter_model: DynamicEventsFilterProxyModel = DynamicEventsFilterProxyModel(self)
        self.filter_model.setSourceModel(self.tree_model)
        self.tree_view.setModel(self.filter_model)
        self.tree_view.setItemDelegate(DynamicEventsItemDelegate(self.tree_view))
        self.tree_view.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked
            | QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.tree_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.filter_header: DynamicEventsFilterHeader = DynamicEventsFilterHeader(
            filter_model=self.filter_model,
            parent=self.tree_view,
        )
        self.tree_view.setHorizontalHeader(self.filter_header)
        header: QtWidgets.QHeaderView = self.filter_header
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.resizeSection(DynamicEventsTreeModel.COLUMN_EVENT_GROUP, 180)
        header.resizeSection(DynamicEventsTreeModel.COLUMN_PARAMETER, 190)
        header.resizeSection(DynamicEventsTreeModel.COLUMN_TIME, 105)
        header.resizeSection(DynamicEventsTreeModel.COLUMN_VALUE, 110)
        header.resizeSection(DynamicEventsTreeModel.COLUMN_TRANSITION, 105)
        header.resizeSection(DynamicEventsTreeModel.COLUMN_END_TIME, 105)

        self.add_event_action.triggered.connect(self.add_event)
        self.remove_action.triggered.connect(self.remove_selection)
        self.new_group_action.triggered.connect(self.create_event_group)
        self.save_button.clicked.connect(self.save_changes)
        self.switch_sequence_action.triggered.connect(self.open_switch_sequence)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_model.rebuilt.connect(self._on_event_model_rebuilt)
        self.filter_model.filterChanged.connect(self._on_filter_changed)
        selection_model: QtCore.QItemSelectionModel | None = self.tree_view.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self.update_actions)
        else:
            pass
        self.session.dirty_state_changed.connect(self._on_dirty_state_changed)
        self._open_event_group_editors()
        self.update_actions()

    def get_dynamic_editor_entry(self) -> DynamicEditorEntry:
        """Return the device entry represented by this workspace page.

        :return: Dynamic device entry associated with the events page.
        """
        return self.entry

    def get_dynamic_editor_mode(self) -> DynamicSimulationMode:
        """Return the simulation mode represented by this workspace page.

        :return: RMS or EMT mode.
        """
        return self.mode

    def get_dynamic_editor_display_title(self) -> str:
        """Build the disambiguated title displayed on the workspace tab.

        :return: Device, mode and events content title.
        """
        return f"{self.entry.display_name} [{self.mode.name} events]"

    @property
    def has_unapplied_changes(self) -> bool:
        """Return the dirty state of the shared event transaction.

        :return: ``True`` when any event page has unsaved changes.
        """
        return self.session.has_unapplied_changes

    def can_close_editor(self, parent: QtWidgets.QWidget | None = None) -> bool:
        """Allow the workspace session to coordinate shared-event close guards.

        :param parent: Unused compatibility parent supplied by the workspace.
        :return: Always ``True`` because the shared session performs the guard.
        """
        del parent
        return True

    def prepare_to_delete(self) -> None:
        """Disconnect the page from its shared transaction before deletion.

        :return: None.
        """
        if self._prepared_to_delete:
            return
        else:
            self._prepared_to_delete = True
        try:
            self.session.dirty_state_changed.disconnect(self._on_dirty_state_changed)
        except (RuntimeError, TypeError):
            pass
        try:
            self.session.changed.disconnect(self.tree_model.rebuild)
        except (RuntimeError, TypeError):
            pass
        try:
            self.session.group_changed.disconnect(self.tree_model.rebuild)
        except (RuntimeError, TypeError):
            pass
        try:
            self.tree_model.rebuilt.disconnect(self._on_event_model_rebuilt)
        except (RuntimeError, TypeError):
            pass
        try:
            self.filter_model.filterChanged.disconnect(self._on_filter_changed)
        except (RuntimeError, TypeError):
            pass

    def set_dark_mode(self) -> None:
        """Refresh the events page after the application selects its dark palette.

        :return: None.
        """
        self.tree_view.viewport().update()

    def set_light_mode(self) -> None:
        """Refresh the events page after the application selects its light palette.

        :return: None.
        """
        self.tree_view.viewport().update()

    @QtCore.Slot(bool)
    def _on_dirty_state_changed(self, dirty: bool) -> None:
        """Forward shared transaction changes to workspace tab-title handling.

        :param dirty: New shared transaction dirty state.
        :return: None.
        """
        self.dirtyStateChanged.emit(dirty)

    def refresh_from_saved_model(self) -> int:
        """Regenerate this page from the latest saved RMS or EMT model.

        Existing event drafts are rebound by variable UID. Events whose target
        parameter no longer exists are removed from the shared transaction.

        :return: Number of obsolete events removed by reconciliation.
        """
        parameters: list[Var]
        mode_parameter_uids: set[int]
        model_is_empty: bool
        parameters, mode_parameter_uids, model_is_empty = collect_dynamic_events_page_parameters(
            entry=self.entry,
            mode=self.mode,
        )
        self.parameters = list(parameters)
        self.mode_parameter_uids = set(mode_parameter_uids)
        self.model_is_empty = model_is_empty
        self.empty_model_message.setVisible(self.model_is_empty)
        self.tree_model.replace_parameters(
            parameters=self.parameters,
            mode_parameter_uids=self.mode_parameter_uids,
            rebuild=False,
        )
        removed_count: int = self.session.reconcile_device_parameters(
            device=self.device,
            mode=self.mode,
            parameters=self.parameters,
        )
        # Reconciliation is device-local, so rebuild this projection after
        # updating both its parameter catalogue and its matching event drafts.
        self.tree_model.rebuild()
        self.update_actions()
        return removed_count

    @QtCore.Slot(bool)
    def create_event_group(self, _checked: bool = False) -> None:
        """Ask for and create one draft event group for this page mode.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        group_dialog: DynamicEventsGroupsDialog = DynamicEventsGroupsDialog(
            mode=self.mode,
            parent=self,
        )
        if group_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            created_group: DynamicEventGroupDraft | None = self.session.add_group(
                mode=self.mode,
                name=group_dialog.get_name(),
            )
            if created_group is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.tr("Invalid event group"),
                    self.tr("The event group name must be non-empty and unique in this simulation mode."),
                )
            else:
                pass
        else:
            pass

    @QtCore.Slot()
    def save_changes(self) -> None:
        """Validate and persist the complete shared event transaction.

        :return: None.
        """
        validation_error: str | None = self.session.validate()
        if validation_error is not None:
            QtWidgets.QMessageBox.warning(self, self.tr("Invalid dynamic events"), validation_error)
        else:
            self.session.commit()
            self.toast_manager.show_info_toast(self.tr("Events saved"))

    def has_runtime_parameters(self) -> bool:
        """Return whether the current dynamic model can receive a new event.

        :return: Whether at least one event or mode parameter is available.
        """
        return len(self.parameters) > 0

    def _selected_backing_object(self) -> object | None:
        """Return the transaction object represented by the selected row.

        :return: Selected event or ``None``.
        """
        proxy_index: QtCore.QModelIndex = self.tree_view.currentIndex()
        if proxy_index.isValid():
            source_index: QtCore.QModelIndex = self.filter_model.mapToSource(proxy_index)
            return self.tree_model.backing_object(source_index)
        else:
            return None

    @QtCore.Slot()
    def _on_event_model_rebuilt(self) -> None:
        """Reconcile active filters and restore visible group editors.

        :return: None.
        """
        self.filter_model.reconcile_selected_values()
        self.filter_header.viewport().update()
        self._open_event_group_editors()

    @QtCore.Slot()
    def _on_filter_changed(self) -> None:
        """Refresh the header state and editors after filtering rows.

        :return: None.
        """
        self.filter_header.viewport().update()
        self._open_event_group_editors()

    @QtCore.Slot()
    def _open_event_group_editors(self) -> None:
        """Keep one Event Group combo visible in every event row.

        :return: None.
        """
        row_index: int
        for row_index in range(self.filter_model.rowCount()):
            group_index: QtCore.QModelIndex = self.filter_model.index(
                row_index,
                DynamicEventsTreeModel.COLUMN_EVENT_GROUP,
            )
            self.tree_view.openPersistentEditor(group_index)

    @QtCore.Slot()
    def update_actions(self) -> None:
        """Refresh action availability and contextual guidance.

        Add and remove remain clickable without a selection so their handlers
        can explain what the user must select through a non-blocking toast.

        :return: None.
        """
        self.add_event_action.setEnabled(True)
        self.remove_action.setEnabled(True)

        mode_parameters: list[Var] = self._get_switch_mode_parameters()
        mode_groups: list[DynamicEventGroupDraft] = self.session.get_groups(self.mode)
        can_open_switch_sequence: bool = (
            self.mode == DynamicSimulationMode.EMT
            and len(mode_parameters) > 0
            and len(mode_groups) > 0
        )
        self.switch_sequence_action.setEnabled(can_open_switch_sequence)
        if self.has_runtime_parameters():
            self.add_event_action.setToolTip(self.tr("Add an event and select its event group"))
        else:
            self.add_event_action.setToolTip(
                self.tr("No events can be added because the dynamic model has no event parameters.")
            )

    @QtCore.Slot(bool)
    def add_event(self, _checked: bool = False) -> None:
        """Add one event and open its event-group selector.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        groups: list[DynamicEventGroupDraft] = self.session.get_groups(self.mode)
        if len(groups) == 0:
            self.toast_manager.show_warning_toast(
                self.tr("Create an event group before adding an event.")
            )
        else:
            # A new unassigned event may not satisfy the current selections.
            # Restore All so its mandatory Event Group editor is always visible.
            self.filter_model.clear_filters()
            created_event: DynamicEventDraft | None = self.session.add_event(
                device=self.device,
                mode=self.mode,
                group=None,
                parameters=self.parameters,
                mode_parameter_uids=self.mode_parameter_uids,
            )
            if created_event is None:
                QtWidgets.QMessageBox.information(
                    self,
                    self.tr("Empty dynamic model"),
                    self.tr("Events cannot be added because this dynamic model has no event parameters."),
                )
            else:
                # The shared session rebuilds the table synchronously. Reveal
                # the new row and immediately request its group selection.
                self._reveal_event(created_event, start_editing=True)

    def _reveal_event(self,
                      event: DynamicEventDraft,
                      start_editing: bool) -> None:
        """Select and optionally edit one event after a model rebuild.

        :param event: Event draft that must become visible.
        :param start_editing: Whether to open its Event Group editor immediately.
        :return: None.
        """
        source_index: QtCore.QModelIndex = self.tree_model.index_for_backing_object(event)
        proxy_index: QtCore.QModelIndex = self.filter_model.mapFromSource(source_index)
        if proxy_index.isValid():
            self.tree_view.setCurrentIndex(proxy_index)
            self.tree_view.scrollTo(proxy_index)
            if start_editing:
                self.tree_view.edit(proxy_index)
            else:
                pass
        else:
            pass

    @QtCore.Slot(bool)
    def remove_selection(self, _checked: bool = False) -> None:
        """Remove the selected event after confirmation.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        selected: object | None = self._selected_backing_object()
        if isinstance(selected, DynamicEventDraft):
            self._confirm_remove_event(selected)
        else:
            self.toast_manager.show_warning_toast(
                self.tr("Select the event you want to remove.")
            )

    def _confirm_remove_event(self, event: DynamicEventDraft) -> None:
        """Confirm and remove one selected event.

        :param event: Event transaction record selected for removal.
        :return: None.
        """
        if event.parameter is None:
            parameter_name: str = self.tr("Invalid parameter")
        else:
            parameter_name = event.parameter.name
        result: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.question(
            self,
            self.tr("Remove event"),
            self.tr("Are you sure you want to remove the event for '{parameter}' at {time:.4f} s?").format(
                parameter=parameter_name,
                time=event.time,
            ),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            self.session.remove_event(event)
        else:
            pass

    @QtCore.Slot(QtCore.QPoint)
    def show_context_menu(self, position: QtCore.QPoint) -> None:
        """Show the removal action for the clicked event row.

        :param position: Table viewport position requested by Qt.
        :return: None.
        """
        index: QtCore.QModelIndex = self.tree_view.indexAt(position)
        if not index.isValid():
            return
        else:
            self.tree_view.setCurrentIndex(index)
        source_index: QtCore.QModelIndex = self.filter_model.mapToSource(index)
        selected: object | None = self.tree_model.backing_object(source_index)
        menu: QtWidgets.QMenu = QtWidgets.QMenu(self.tree_view)
        if isinstance(selected, DynamicEventDraft):
            remove_action: QtGui.QAction | None = menu.addAction(self.tr("Remove"))
        else:
            remove_action = None
        chosen_action: QtGui.QAction | None = menu.exec(self.tree_view.viewport().mapToGlobal(position))
        if remove_action is not None and chosen_action is remove_action:
            self.remove_selection()
        else:
            pass

    def _get_switch_mode_parameters(self) -> list[Var]:
        """Return EMT switch-state mode parameters available in this page.

        :return: Ordered switch mode parameter list.
        """
        mode_parameters: list[Var] = list()
        parameter: Var
        for parameter in self.parameters:
            if parameter.uid in self.mode_parameter_uids and parameter.name.startswith("switch_closed_mode_"):
                mode_parameters.append(parameter)
            else:
                pass
        return mode_parameters

    @QtCore.Slot(bool)
    def open_switch_sequence(self, _checked: bool = False) -> None:
        """Create EMT switch events in the group selected by the wizard.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        mode_parameters: list[Var] = self._get_switch_mode_parameters()
        groups: list[DynamicEventGroupDraft] = self.session.get_groups(self.mode)
        if len(groups) == 0 or len(mode_parameters) == 0:
            return
        else:
            proxy_groups: list[EmtEventsGroup] = list()
            group: DynamicEventGroupDraft
            for group in groups:
                proxy_group: EmtEventsGroup = EmtEventsGroup(name=group.name, active=group.active)
                proxy_groups.append(proxy_group)
        dialog: SwitchSequenceDialog = SwitchSequenceDialog(
            mode_parameters=mode_parameters,
            events_groups=proxy_groups,
            parent=self,
        )
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sequence_data: SwitchSequenceData | None = dialog.get_typed_data()
            if sequence_data is not None:
                selected_group: DynamicEventGroupDraft | None = None
                proxy_index: int
                for proxy_index in range(len(proxy_groups)):
                    if proxy_groups[proxy_index] is sequence_data.group:
                        selected_group = groups[proxy_index]
                    else:
                        pass
                last_created_event: DynamicEventDraft | None = None
                sequence_index: int
                if selected_group is not None:
                    for sequence_index in range(min(len(sequence_data.times), len(sequence_data.values))):
                        event: DynamicEventDraft | None = self.session.add_event(
                            device=self.device,
                            mode=self.mode,
                            group=selected_group,
                            parameters=self.parameters,
                            mode_parameter_uids=self.mode_parameter_uids,
                        )
                        if event is not None:
                            event.parameter = sequence_data.parameter
                            event.time = float(sequence_data.times[sequence_index])
                            event.value = float(sequence_data.values[sequence_index])
                            event.transition_type = DynamicEventTransitionType.Step
                            event.end_time = None
                            event.force_step_alignment = True
                            last_created_event = event
                        else:
                            pass
                else:
                    pass
                self.session.changed.emit()
                if last_created_event is not None:
                    self._reveal_event(last_created_event, start_editing=False)
                else:
                    pass
            else:
                pass
        else:
            pass
