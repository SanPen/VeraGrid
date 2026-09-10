from __future__ import annotations

import sys

from PySide6 import QtCore, QtGui, QtWidgets

import VeraGridEngine.api as vge
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_support import collect_block_runtime_event_parameters
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_models import DynamicEventDraft
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_models import DynamicEventGroupDraft
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_models import DynamicEventsDraftSession
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page import DynamicEventsPage
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page import DynamicEventsFilterHeader
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page import DynamicEventsFilterPopup
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page import DynamicEventsFilterProxyModel
from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page import DynamicEventsTreeModel
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import build_dynamic_editor_entry
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_workspace_session import DynamicEditorWorkspaceSession
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_workspace_window import DynamicEditorWorkspaceWindow
from VeraGrid.Gui.toast_widget import ToastManager
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import DynamicEventTransitionType, DynamicSimulationMode


class DynamicEventEditor:
    """Test harness exposing event components through the unified workspace."""

    __slots__ = (
        "circuit",
        "preferred_mode",
        "workspace_session",
        "workspace",
    )

    def __init__(self,
                 circuit: vge.MultiCircuit,
                 preferred_mode: DynamicSimulationMode,
                 initial_device: vge.Load | None = None,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Create the unified workspace state used by the event component tests.

        :param circuit: Circuit containing models and event assets.
        :param preferred_mode: RMS or EMT family requested by the test.
        :param initial_device: Optional device opened immediately.
        :param parent: Optional owning widget.
        :return: None.
        """
        self.circuit: vge.MultiCircuit = circuit
        self.preferred_mode: DynamicSimulationMode = preferred_mode
        self.workspace_session: DynamicEditorWorkspaceSession = DynamicEditorWorkspaceSession()
        self.workspace: DynamicEditorWorkspaceWindow = DynamicEditorWorkspaceWindow(
            session=self.workspace_session,
            parent=parent,
        )
        self.workspace._set_workspace_circuit(circuit=circuit)
        if initial_device is not None:
            self.workspace.open_dynamic_events_for(
                api_object=initial_device,
                circuit=circuit,
                mode=preferred_mode,
                target_workspace=self.workspace,
            )
            self.workspace.set_tree_visible(visible=False)
        else:
            self.workspace.set_tree_visible(visible=True)

    @property
    def pages(self) -> list[DynamicEventsPage]:
        """Return open event pages in registry order.

        :return: Event pages opened by the unified workspace.
        """
        return list(self.workspace_session._event_pages)

    @property
    def session(self) -> DynamicEventsDraftSession:
        """Return the shared event transaction, creating it when necessary.

        :return: Shared event draft session.
        """
        return self.workspace_session._get_events_session(circuit=self.circuit)

    @property
    def ui(self) -> object:
        """Return the unified workspace UI used by compatibility assertions.

        :return: Generated workspace UI object.
        """
        return self.workspace.ui

    @property
    def toast_manager(self) -> ToastManager:
        """Return the active event page toast manager.

        :return: Toast manager owned by the active events page.
        """
        page: DynamicEventsPage | None = self._current_page()
        if page is None:
            raise RuntimeError("An event page is required for toast assertions")
        else:
            return page.toast_manager

    def _current_page(self) -> DynamicEventsPage | None:
        """Return the active events page.

        :return: Active events page, or ``None``.
        """
        page: object = self.workspace.current_page()
        if isinstance(page, DynamicEventsPage):
            return page
        else:
            return None

    def open_entry(
            self,
            entry: DynamicEditorEntry,
            mode: DynamicSimulationMode,
    ) -> DynamicEventsPage | None:
        """Open one events page through the production workspace session.

        :param entry: Device entry to open.
        :param mode: RMS or EMT events family.
        :return: Open events page, or ``None``.
        """
        return self.workspace_session.open_events_entry(
            entry=entry,
            mode=mode,
            target_workspace=self.workspace,
        )

    def accept_changes(self) -> None:
        """Save the shared transaction through the active page.

        :return: None.
        """
        page: DynamicEventsPage | None = self._current_page()
        if page is not None:
            page.save_changes()
        else:
            pass

    def reject(self) -> None:
        """Discard the shared transaction and close the workspace.

        :return: None.
        """
        if self.workspace_session._events_session is not None:
            self.workspace_session._events_session.reload_from_circuit()
        else:
            pass
        self.workspace.close()

    def close(self) -> None:
        """Close the harness without allowing fixture cleanup to prompt.

        :return: None.
        """
        self.reject()

    def result(self) -> QtWidgets.QDialog.DialogCode:
        """Preserve the former dialog result assertion for saved checkpoints.

        :return: Rejected, because saving an events page does not close the workspace.
        """
        return QtWidgets.QDialog.DialogCode.Rejected


def get_qt_application() -> QtWidgets.QApplication:
    """Return the shared Qt application used by dynamic-events GUI tests.

    :return: Existing or newly created Qt application.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return application


def build_dynamic_target(
        mode: DynamicSimulationMode,
        empty_model: bool = False,
) -> tuple[vge.MultiCircuit, vge.Load, Var, RmsEventsGroup | EmtEventsGroup]:
    """Build one dynamic-capable load and a mode-specific event group.

    :param mode: RMS or EMT model assigned to the load.
    :param empty_model: Whether the assigned block has no event parameters.
    :return: Circuit, load, symbolic parameter and event group.
    """
    circuit: vge.MultiCircuit = vge.MultiCircuit(name="Dynamic events test")
    bus: vge.Bus = vge.Bus(name="Bus", Vnom=10.0)
    circuit.add_bus(bus)
    load: vge.Load = vge.Load(name="Load")
    circuit.add_load(bus=bus, api_obj=load)
    parameter: Var = VarFactory().add_var("event_parameter")
    if empty_model:
        model: Block = Block()
    else:
        event_values: dict[Var, Const] = dict()
        event_values[parameter] = Const(0.0)
        model = Block(event_dict=event_values)

    if mode == DynamicSimulationMode.RMS:
        group: RmsEventsGroup | EmtEventsGroup = RmsEventsGroup(name="RMS group")
        circuit.add_rms_events_group(group)
        load.rms_model = model
    else:
        group = EmtEventsGroup(name="EMT group")
        circuit.add_emt_events_group(group)
        load.emt_model = model
    return circuit, load, parameter, group


def get_dynamic_entry(device: vge.Load, circuit: vge.MultiCircuit) -> DynamicEditorEntry:
    """Resolve the dynamic-editor entry for one test load.

    :param device: Dynamic-capable load.
    :param circuit: Circuit containing the load.
    :return: Resolved dynamic entry.
    """
    entry: DynamicEditorEntry | None = build_dynamic_editor_entry(device, circuit)
    assert entry is not None
    return entry


def test_selected_device_opens_requested_page_with_tree_collapsed() -> None:
    """A unique selected device must open directly in the requested mode.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, _group = build_dynamic_target(DynamicSimulationMode.RMS)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )

    assert len(dialog.pages) == 1
    assert dialog.pages[0].entry.api_object is load
    assert dialog.pages[0].mode == DynamicSimulationMode.RMS
    assert dialog.ui.treeFrame.isHidden()
    dialog.close()


def test_no_selected_device_opens_general_tree() -> None:
    """No selected device must leave the general device tree visible.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, _load, _parameter, _group = build_dynamic_target(DynamicSimulationMode.EMT)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.EMT,
    )

    assert len(dialog.pages) == 0
    assert not dialog.ui.treeFrame.isHidden()
    dialog.close()


def test_empty_model_page_removes_stale_events_and_disables_add() -> None:
    """An empty model page must discard events whose parameters disappeared.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, parameter, group = build_dynamic_target(
        DynamicSimulationMode.RMS,
        empty_model=True,
    )
    assert isinstance(group, RmsEventsGroup)
    existing_event: vge.RmsEvent = vge.RmsEvent(
        device=load,
        parameter=parameter,
        time=1.0,
        value=2.0,
        group=group,
    )
    circuit.add_rms_event(existing_event)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]
    assert not page.empty_model_message.isHidden()
    assert page.tree_model.rowCount() == 0
    assert page.add_event_action.isEnabled()
    assert page.session.has_unapplied_changes
    dialog.close()


def test_empty_model_message_is_page_specific_and_uses_block_empty_state() -> None:
    """The centered empty-state message must not leak into a non-empty mode tab.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, _group = build_dynamic_target(
        DynamicSimulationMode.RMS,
        empty_model=True,
    )
    emt_group: EmtEventsGroup = EmtEventsGroup(name="EMT group")
    circuit.add_emt_events_group(emt_group)
    load.emt_model = Block(name="Non-empty EMT model without event parameters")
    entry: DynamicEditorEntry = get_dynamic_entry(load, circuit)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    rms_page: DynamicEventsPage = dialog.pages[0]
    opened_emt_page: DynamicEventsPage | None = dialog.open_entry(entry, DynamicSimulationMode.EMT)
    assert opened_emt_page is not None

    assert not rms_page.empty_model_message.isHidden()
    assert opened_emt_page.empty_model_message.isHidden()
    assert opened_emt_page.add_event_action.isEnabled()
    dialog.close()


def test_add_event_without_selection_opens_event_group_editor() -> None:
    """Adding an event must reveal its row and open the Event Group combo.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, group = build_dynamic_target(DynamicSimulationMode.RMS)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]
    page.tree_view.setCurrentIndex(QtCore.QModelIndex())
    page.add_event()
    current_index: QtCore.QModelIndex = page.tree_view.currentIndex()
    source_index: QtCore.QModelIndex = page.filter_model.mapToSource(current_index)
    current_backing: object | None = page.tree_model.backing_object(source_index)
    editor: QtWidgets.QWidget | None = page.tree_view.indexWidget(current_index)

    assert isinstance(current_backing, DynamicEventDraft)
    assert current_index.column() == page.tree_model.COLUMN_EVENT_GROUP
    assert current_backing.group is None
    assert isinstance(editor, QtWidgets.QComboBox)
    assert editor.count() == 1
    assert editor.itemText(0) == group.name
    dialog.close()


def test_page_table_filters_events_by_device() -> None:
    """Each page table must contain only events for its own device and mode.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, first_load, parameter, group = build_dynamic_target(DynamicSimulationMode.EMT)
    assert isinstance(group, EmtEventsGroup)
    second_bus: vge.Bus = vge.Bus(name="Second bus", Vnom=10.0)
    circuit.add_bus(second_bus)
    second_load: vge.Load = vge.Load(name="Second load")
    circuit.add_load(bus=second_bus, api_obj=second_load)
    second_load.emt_model = first_load.emt_model
    circuit.add_emt_event(vge.EmtEvent(device=first_load, parameter=parameter, time=1.0, value=1.0, group=group))
    circuit.add_emt_event(vge.EmtEvent(device=second_load, parameter=parameter, time=2.0, value=2.0, group=group))
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.EMT,
        initial_device=first_load,
    )
    page: DynamicEventsPage = dialog.pages[0]
    assert page.tree_model.rowCount() == 1
    event_index: QtCore.QModelIndex = page.tree_model.index(0, 0)
    event_draft: object | None = page.tree_model.backing_object(event_index)
    assert isinstance(event_draft, DynamicEventDraft)
    assert event_draft.device is first_load
    assert page.tree_model.headerData(0, QtCore.Qt.Orientation.Horizontal) == "Event Group"
    dialog.close()


def test_event_filters_combine_multiple_values_and_columns() -> None:
    """Column values must use OR while different filters combine with AND.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, first_parameter, first_group = build_dynamic_target(
        DynamicSimulationMode.RMS
    )
    assert isinstance(first_group, RmsEventsGroup)
    second_parameter: Var = VarFactory().add_var("second_parameter")
    event_values: dict[Var, Const] = dict()
    event_values[first_parameter] = Const(0.0)
    event_values[second_parameter] = Const(0.0)
    load.rms_model = Block(event_dict=event_values)
    second_group: RmsEventsGroup = RmsEventsGroup(name="Second group")
    circuit.add_rms_events_group(second_group)
    circuit.add_rms_event(vge.RmsEvent(
        device=load,
        parameter=first_parameter,
        time=1.0,
        value=1.0,
        group=first_group,
        transition_type=DynamicEventTransitionType.Step,
    ))
    circuit.add_rms_event(vge.RmsEvent(
        device=load,
        parameter=second_parameter,
        time=2.0,
        end_time=3.0,
        value=2.0,
        group=first_group,
        transition_type=DynamicEventTransitionType.Ramp,
    ))
    circuit.add_rms_event(vge.RmsEvent(
        device=load,
        parameter=first_parameter,
        time=4.0,
        value=3.0,
        group=second_group,
        transition_type=DynamicEventTransitionType.Step,
    ))
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]

    assert page.filter_model.rowCount() == 3
    assert isinstance(page.filter_header, DynamicEventsFilterHeader)
    filter_indicator: QtWidgets.QLabel
    for filter_indicator in (
        page.filter_header.event_group_indicator,
        page.filter_header.parameter_indicator,
        page.filter_header.transition_indicator,
    ):
        assert filter_indicator.text() == "\N{BLACK DOWN-POINTING SMALL TRIANGLE}"
        assert not filter_indicator.isHidden()
        assert filter_indicator.parent() is page.filter_header.viewport()
    assert set(page.filter_model.available_values(page.tree_model.COLUMN_EVENT_GROUP)) == {
        "RMS group",
        "Second group",
    }

    page.filter_model.set_selected_values(
        page.tree_model.COLUMN_EVENT_GROUP,
        {"RMS group", "Second group"},
    )
    assert page.filter_model.rowCount() == 3

    page.filter_model.set_selected_values(
        page.tree_model.COLUMN_PARAMETER,
        {first_parameter.name},
    )
    assert page.filter_model.rowCount() == 2

    page.filter_model.set_selected_values(
        page.tree_model.COLUMN_TRANSITION,
        {DynamicEventTransitionType.Step.name},
    )
    assert page.filter_model.rowCount() == 2

    page.filter_model.set_selected_values(
        page.tree_model.COLUMN_EVENT_GROUP,
        {first_group.name},
    )
    assert page.filter_model.rowCount() == 1

    page.filter_model.set_selected_values(page.tree_model.COLUMN_PARAMETER, set())
    assert page.filter_model.rowCount() == 1
    page.filter_model.clear_filters()
    assert page.filter_model.rowCount() == 3
    assert not page.filter_model.is_filter_active(page.tree_model.COLUMN_EVENT_GROUP)
    dialog.close()


def test_filter_popup_keeps_multiple_values_selected_and_all_clears_them() -> None:
    """The header popup must retain highlighted choices until All is selected.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    filter_model: DynamicEventsFilterProxyModel = DynamicEventsFilterProxyModel()
    popup: DynamicEventsFilterPopup = DynamicEventsFilterPopup(
        column=DynamicEventsTreeModel.COLUMN_EVENT_GROUP,
        available_values=list(("Group one", "Group two")),
        selected_values=set(),
    )
    popup.filterSelectionChanged.connect(filter_model.set_selected_values)
    first_group_item: QtWidgets.QListWidgetItem = popup.values_list.item(1)
    second_group_item: QtWidgets.QListWidgetItem = popup.values_list.item(2)

    first_group_item.setSelected(True)
    popup._on_item_clicked(first_group_item)
    second_group_item.setSelected(True)
    popup._on_item_clicked(second_group_item)

    assert filter_model.selected_values(DynamicEventsTreeModel.COLUMN_EVENT_GROUP) == {
        "Group one",
        "Group two",
    }
    assert first_group_item.isSelected()
    assert second_group_item.isSelected()
    assert not popup.all_item.isSelected()

    popup._on_item_clicked(popup.all_item)

    assert filter_model.selected_values(DynamicEventsTreeModel.COLUMN_EVENT_GROUP) == set()
    assert popup.all_item.isSelected()
    assert not first_group_item.isSelected()
    assert not second_group_item.isSelected()
    popup.close()


def test_event_group_cell_moves_draft_and_save_persists_it() -> None:
    """Editing Event Group must move the draft transactionally and preserve its identity.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, parameter, source_group = build_dynamic_target(DynamicSimulationMode.RMS)
    assert isinstance(source_group, RmsEventsGroup)
    target_group: RmsEventsGroup = RmsEventsGroup(name="RMS target group", active=False)
    circuit.add_rms_events_group(target_group)
    original_event: vge.RmsEvent = vge.RmsEvent(
        device=load,
        parameter=parameter,
        time=1.0,
        value=2.0,
        group=source_group,
    )
    circuit.add_rms_event(original_event)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]
    group_drafts: list[DynamicEventGroupDraft] = dialog.session.get_groups(DynamicSimulationMode.RMS)
    target_group_draft: DynamicEventGroupDraft = group_drafts[1]
    event_draft: DynamicEventDraft = dialog.session.get_events_for_device(
        load,
        DynamicSimulationMode.RMS,
    )[0]
    event_index: QtCore.QModelIndex = page.tree_model.index_for_backing_object(event_draft)
    group_index: QtCore.QModelIndex = event_index.siblingAtColumn(page.tree_model.COLUMN_EVENT_GROUP)
    accepted: bool = page.tree_model.setData(
        group_index,
        target_group_draft,
        QtCore.Qt.ItemDataRole.EditRole,
    )

    assert accepted
    assert event_draft.group is target_group_draft
    assert page.tree_model.data(group_index) == target_group_draft.name
    assert original_event.group is source_group

    dialog.accept_changes()

    assert circuit.rms_events[0] is original_event
    assert original_event.group is target_group
    dialog.close()


def test_event_group_assignment_rejects_foreign_mode_and_close_discards_change() -> None:
    """Only a same-mode group may be assigned and Close must discard the draft change.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, parameter, source_group = build_dynamic_target(DynamicSimulationMode.EMT)
    assert isinstance(source_group, EmtEventsGroup)
    target_group: EmtEventsGroup = EmtEventsGroup(name="EMT target group")
    circuit.add_emt_events_group(target_group)
    foreign_group: RmsEventsGroup = RmsEventsGroup(name="RMS foreign group")
    circuit.add_rms_events_group(foreign_group)
    original_event: vge.EmtEvent = vge.EmtEvent(
        device=load,
        parameter=parameter,
        time=1.0,
        value=2.0,
        group=source_group,
    )
    circuit.add_emt_event(original_event)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.EMT,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]
    event_draft: DynamicEventDraft = dialog.session.get_events_for_device(
        load,
        DynamicSimulationMode.EMT,
    )[0]
    emt_group_drafts: list[DynamicEventGroupDraft] = dialog.session.get_groups(DynamicSimulationMode.EMT)
    rms_group_draft: DynamicEventGroupDraft = dialog.session.get_groups(DynamicSimulationMode.RMS)[0]
    target_group_draft: DynamicEventGroupDraft = emt_group_drafts[1]
    event_index: QtCore.QModelIndex = page.tree_model.index_for_backing_object(event_draft)
    group_index: QtCore.QModelIndex = event_index.siblingAtColumn(page.tree_model.COLUMN_EVENT_GROUP)
    different_mode_accepted: bool = page.tree_model.setData(
        group_index,
        rms_group_draft,
        QtCore.Qt.ItemDataRole.EditRole,
    )
    valid_move_accepted: bool = page.tree_model.setData(
        group_index,
        target_group_draft,
        QtCore.Qt.ItemDataRole.EditRole,
    )

    assert not different_mode_accepted
    assert valid_move_accepted
    assert event_draft.group is target_group_draft
    assert original_event.group is source_group

    dialog.reject()

    assert original_event.group is source_group


def test_group_active_and_rename_are_transactional() -> None:
    """Group metadata must remain transactional without group table rows.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, group = build_dynamic_target(DynamicSimulationMode.RMS)
    assert isinstance(group, RmsEventsGroup)
    cancelled_dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    cancelled_group: DynamicEventGroupDraft = cancelled_dialog.session.get_groups(
        DynamicSimulationMode.RMS
    )[0]
    cancelled_page: DynamicEventsPage = cancelled_dialog.pages[0]
    cancelled_dialog.session.rename_group(cancelled_group, "Cancelled name")
    cancelled_dialog.session.set_group_active(cancelled_group, False)
    cancelled_dialog.reject()

    assert not cancelled_group.active
    assert cancelled_page.tree_model.rowCount() == 0
    assert group.name == "RMS group"
    assert group.active

    saved_dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    saved_group: DynamicEventGroupDraft = saved_dialog.session.get_groups(DynamicSimulationMode.RMS)[0]
    saved_dialog.session.rename_group(saved_group, "Saved name")
    saved_dialog.session.set_group_active(saved_group, False)
    saved_dialog.accept_changes()

    assert group.name == "Saved name"
    assert not group.active
    assert saved_dialog.result() == QtWidgets.QDialog.DialogCode.Rejected
    assert len(saved_dialog.toast_manager.active_toasts) == 1
    toast_label: QtWidgets.QLabel | None = saved_dialog.toast_manager.active_toasts[0].findChild(
        QtWidgets.QLabel
    )
    assert toast_label is not None
    assert toast_label.text() == "Events saved"
    saved_dialog.close()


def test_group_removal_cascades_events_across_devices_on_save() -> None:
    """Removing a global group must remove all its device events on Save.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, parameter, group = build_dynamic_target(DynamicSimulationMode.EMT)
    assert isinstance(group, EmtEventsGroup)
    circuit.add_emt_event(vge.EmtEvent(device=load, parameter=parameter, time=1.0, value=1.0, group=group))
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.EMT,
        initial_device=load,
    )
    group_draft: DynamicEventGroupDraft = dialog.session.get_groups(DynamicSimulationMode.EMT)[0]
    dialog.session.remove_group(group_draft)
    dialog.accept_changes()

    assert len(circuit.emt_events_groups) == 0
    assert len(circuit.emt_events) == 0
    dialog.close()


def test_align_step_checkbox_accepts_qt_check_state_enum() -> None:
    """Align Step must consume the enum object emitted by PySide6.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, group = build_dynamic_target(DynamicSimulationMode.EMT)
    assert isinstance(group, EmtEventsGroup)
    mode_parameter: Var = VarFactory().add_var("switch_closed_mode_test")
    mode_values: dict[Var, float] = dict()
    mode_values[mode_parameter] = 1.0
    load.emt_model = Block(mode_dict=mode_values)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.EMT,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]
    group_draft: DynamicEventGroupDraft = dialog.session.get_groups(DynamicSimulationMode.EMT)[0]
    event_draft: DynamicEventDraft | None = dialog.session.add_event(
        device=load,
        mode=DynamicSimulationMode.EMT,
        group=group_draft,
        parameters=page.parameters,
        mode_parameter_uids=page.mode_parameter_uids,
    )
    assert event_draft is not None
    event_index: QtCore.QModelIndex = page.tree_model.index_for_backing_object(event_draft)
    align_index: QtCore.QModelIndex = event_index.siblingAtColumn(page.tree_model.COLUMN_ALIGN_STEP)
    edit_accepted: bool = page.tree_model.setData(
        align_index,
        QtCore.Qt.CheckState.Unchecked,
        QtCore.Qt.ItemDataRole.CheckStateRole,
    )

    assert edit_accepted
    assert not event_draft.force_step_alignment
    dialog.close()


def test_tabs_are_unique_per_device_and_mode() -> None:
    """Repeated opens must focus one tab while RMS and EMT remain separate.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, _group = build_dynamic_target(DynamicSimulationMode.RMS)
    emt_group: EmtEventsGroup = EmtEventsGroup(name="EMT group")
    circuit.add_emt_events_group(emt_group)
    load.emt_model = Block()
    entry: DynamicEditorEntry = get_dynamic_entry(load, circuit)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
    )
    first_page: DynamicEventsPage | None = dialog.open_entry(entry, DynamicSimulationMode.RMS)
    repeated_page: DynamicEventsPage | None = dialog.open_entry(entry, DynamicSimulationMode.RMS)
    emt_page: DynamicEventsPage | None = dialog.open_entry(entry, DynamicSimulationMode.EMT)

    assert first_page is repeated_page
    assert emt_page is not None
    assert len(dialog.pages) == 2
    assert first_page.switch_sequence_action.isVisible() is False
    assert emt_page.switch_sequence_action.isVisible()
    dialog.close()


def test_save_button_and_event_actions_use_ui_toolbar_contract() -> None:
    """The events page must expose its save button and UI-defined toolbar actions.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, _group = build_dynamic_target(DynamicSimulationMode.RMS)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]

    assert page.save_button.text() == ""
    assert page.save_button.toolTip() == "Save events"
    assert not page.save_button.icon().isNull()
    assert isinstance(page.tree_view, QtWidgets.QTableView)
    toolbar_actions: list[QtGui.QAction] = page.ui.eventsToolBar.actions()
    assert page.switch_sequence_action in toolbar_actions
    assert page.add_event_action in toolbar_actions
    assert page.remove_action in toolbar_actions
    assert page.new_group_action in toolbar_actions
    assert isinstance(page.new_group_action, QtGui.QAction)
    assert isinstance(page.add_event_action, QtGui.QAction)
    assert isinstance(page.remove_action, QtGui.QAction)
    assert page.new_group_action.text() != ""
    assert page.add_event_action.toolTip() != ""
    assert page.remove_action.toolTip() != ""
    dialog.close()


def test_add_event_requires_an_existing_event_group() -> None:
    """Add Event must explain that its mode needs at least one event group.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, group = build_dynamic_target(DynamicSimulationMode.RMS)
    assert isinstance(group, RmsEventsGroup)
    circuit.delete_rms_events_group(group)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]

    page.add_event()

    toast_label: QtWidgets.QLabel | None = page.toast_manager.active_toasts[0].findChild(QtWidgets.QLabel)
    assert page.tree_model.rowCount() == 0
    assert toast_label is not None
    assert toast_label.text() == "Create an event group before adding an event."
    dialog.close()


def test_event_controls_add_without_selection_and_explain_missing_remove_selection() -> None:
    """Add must not require selection while Remove must explain its requirement.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, _group = build_dynamic_target(DynamicSimulationMode.RMS)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    page: DynamicEventsPage = dialog.pages[0]
    page.tree_view.clearSelection()
    page.tree_view.setCurrentIndex(QtCore.QModelIndex())

    page.add_event()
    page.tree_view.clearSelection()
    page.tree_view.setCurrentIndex(QtCore.QModelIndex())
    page.remove_selection()
    remove_toast_label: QtWidgets.QLabel | None = page.toast_manager.active_toasts[0].findChild(
        QtWidgets.QLabel
    )

    assert page.tree_model.rowCount() == 1
    assert remove_toast_label is not None
    assert remove_toast_label.text() == "Select the event you want to remove."
    dialog.close()


def test_draft_validation_rejects_overlapping_events() -> None:
    """Prospective validation must reject overlapping target intervals.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    circuit, load, _parameter, _group = build_dynamic_target(DynamicSimulationMode.RMS)
    dialog: DynamicEventEditor = DynamicEventEditor(
        circuit=circuit,
        preferred_mode=DynamicSimulationMode.RMS,
        initial_device=load,
    )
    group_draft: DynamicEventGroupDraft = dialog.session.get_groups(DynamicSimulationMode.RMS)[0]
    first_event: DynamicEventDraft | None = dialog.session.add_event(
        device=load,
        mode=DynamicSimulationMode.RMS,
        group=group_draft,
        parameters=dialog.pages[0].parameters,
        mode_parameter_uids=set(),
    )
    second_event: DynamicEventDraft | None = dialog.session.add_event(
        device=load,
        mode=DynamicSimulationMode.RMS,
        group=group_draft,
        parameters=dialog.pages[0].parameters,
        mode_parameter_uids=set(),
    )
    assert first_event is not None
    assert second_event is not None
    first_event.time = 1.0
    second_event.time = 1.0
    first_event.transition_type = DynamicEventTransitionType.Step
    second_event.transition_type = DynamicEventTransitionType.Step

    validation_error: str | None = dialog.session.validate()
    assert validation_error is not None
    assert "overlap" in validation_error.lower()
    dialog.close()


def test_collect_block_runtime_event_parameters_includes_child_modes() -> None:
    """Parameter discovery must include discrete modes in child blocks.

    :return: None.
    """
    mode_parameter: Var = VarFactory().add_var("switch_closed_mode_child")
    mode_values: dict[Var, float] = dict()
    mode_values[mode_parameter] = 0.0
    child_block: Block = Block(mode_dict=mode_values)
    root_block: Block = Block(children=list((child_block,)))
    parameters: list[Var]
    mode_uids: set[int]
    parameters, mode_uids = collect_block_runtime_event_parameters(root_block)

    assert parameters == list((mode_parameter,))
    assert mode_uids == set((mode_parameter.uid,))
