# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Iterator

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Events.dynamic_events_page import DynamicEventsPage
from VeraGrid.Gui.DynamicModelEditor.Workspace.detachable_editor_tabs_widget import DetachableEditorTabWidget
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.Workspace.Tabs.dynamic_editor_tab import DynamicEditorTab
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_workspace import Ui_DynamicEditorWorkspaceWindow
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_device_tree import DynamicDeviceTreeWidget
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import build_dynamic_editor_entry
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_workspace_session import DynamicEditorWorkspaceSession
from VeraGridEngine.enumerations import DynamicEditorContentType, DynamicSimulationMode
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.types import ALL_DEV_TYPES


class DynamicEditorWorkspaceWindow(QtWidgets.QMainWindow):
    """
    Tabbed workspace hosting one or more dynamic editor pages.
    """

    __slots__ = (
        "__session",
        "_accepts_new_pages",
        "_current_circuit",
        "device_tree_widget",
        "ui",
        "editor_tabs",
    )

    def __init__(
            self,
            session: DynamicEditorWorkspaceSession,
            parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """
        Initialize one dynamic-editor workspace window.

        :param session: Shared workspace session.
        :param parent: Optional Qt parent widget.
        :return: None.
        """
        super().__init__(parent)
        self.__session: DynamicEditorWorkspaceSession = session
        self._accepts_new_pages: bool = True
        self._current_circuit: MultiCircuit | None = None
        self.ui: Ui_DynamicEditorWorkspaceWindow = Ui_DynamicEditorWorkspaceWindow()
        self.ui.setupUi(self)

        # Replace the workspace-owned search/tree pair with the shared dynamic
        # device widget used by every dynamic editing workflow.
        self.ui.verticalLayout_2.removeWidget(self.ui.frame_2)
        self.ui.frame_2.setParent(None)
        self.ui.verticalLayout_2.removeWidget(self.ui.treeView)
        self.ui.treeView.setParent(None)
        self.device_tree_widget: DynamicDeviceTreeWidget = DynamicDeviceTreeWidget(
            parent=self.ui.treeFrame,
        )
        self.ui.verticalLayout_2.addWidget(self.device_tree_widget)
        self.ui.searchInTreeLineEdit = self.device_tree_widget.search_line_edit
        self.ui.treeView = self.device_tree_widget.tree_view

        self.ui.splitter.setStretchFactor(0, 1)
        self.ui.splitter.setStretchFactor(1, 10)

        self.editor_tabs: DetachableEditorTabWidget = DetachableEditorTabWidget(self)
        self.ui.editorFrameLayout.addWidget(self.editor_tabs)
        self.ui.editorTabs = self.editor_tabs

        self.editor_tabs.tabCloseRequested.connect(self.close_tab_at)
        self.editor_tabs.currentChanged.connect(self._on_current_tab_changed)
        self.editor_tabs.tabDragStarted.connect(self._on_tab_drag_started)
        self.editor_tabs.detachRequested.connect(self._on_tab_detach_requested)
        self.editor_tabs.reattachRequested.connect(self._on_tab_reattach_requested)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.session.register_workspace(self)
        self._refresh_window_title()

        self.ui.actionview_tree.triggered.connect(self.show_hide_tree)
        self.ui.actionRMS_Editor.triggered.connect(self.open_rms_editor_entry)
        self.ui.actionRMS_Events.triggered.connect(self.open_rms_events_entry)
        self.ui.actionEMT_Editor.triggered.connect(self.open_emt_editor_entry)
        self.ui.actionEMT_Events.triggered.connect(self.open_emt_events_entry)

        self.device_tree_widget.entryPageRequested.connect(self._open_device_tree_entry)

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """
        Refresh runtime-owned workspace strings after a Qt language change.

        :param event: Incoming Qt change event.
        :return: None.
        """
        QtWidgets.QMainWindow.changeEvent(self, event)

        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.ui.retranslateUi(self)
            self.refresh_runtime_translations()
        else:
            pass

    def refresh_runtime_translations(self) -> None:
        """
        Refresh the workspace strings that are created from Python code.

        :return: None.
        """
        self._refresh_window_title()

    def get_open_workspaces(self) -> list["DynamicEditorWorkspaceWindow"]:
        """
        Return the open workspaces that share this window session.

        :return: Open workspaces for this session.
        """
        return self.session.get_open_workspaces()

    def is_available_for_pages(self) -> bool:
        """
        Return whether this workspace can still receive editor pages.

        The Python wrapper can outlive the underlying Qt window while deferred
        deletion is being processed. Session routing uses this Python-owned flag
        so it never calls into a workspace whose native children are closing.

        :return: ``True`` while new pages may be added.
        """
        return self._accepts_new_pages

    @property
    def session(self) -> DynamicEditorWorkspaceSession:
        """
        Return the shared session that coordinates this workspace family.

        :return: Shared workspace session.
        """
        return self.__session

    def workspace_for_page(
            self,
            page: DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage,
    ) -> "DynamicEditorWorkspaceWindow | None":
        """
        Return the workspace in this session that owns one page.

        :param page: Page to resolve.
        :return: Owning workspace or ``None``.
        """
        return self.session.workspace_for_page(page)

    def note_page_activated(
            self,
            page: DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage,
    ) -> None:
        """
        Forward page-activation bookkeeping to the shared session.

        :param page: Newly activated page.
        :return: None.
        """
        self.session.note_page_activated(page)

    def open_entry(
            self,
            entry: DynamicEditorEntry,
            preferred_mode: DynamicSimulationMode | None = None,
            target_workspace: "DynamicEditorWorkspaceWindow | None" = None,
    ) -> DynamicEditorTab:
        """
        Open one editor entry in this workspace session.

        :param entry: Entry to open.
        :param preferred_mode: Explicit requested mode, if any.
        :param target_workspace: Preferred destination workspace.
        :return: Open editor page for the requested entry.
        """
        target = target_workspace if target_workspace is not None else self
        if not target.is_available_for_pages():
            raise RuntimeError("Cannot open a dynamic editor in a closing workspace")
        else:
            pass
        target._set_workspace_circuit(entry.circuit)
        return self.session.open_entry(
            entry,
            preferred_mode=preferred_mode,
            target_workspace=target,
        )

    def open_dynamic_editor_for(
            self,
            api_object: ALL_DEV_TYPES,
            circuit: MultiCircuit,
            preferred_mode: DynamicSimulationMode | None = None,
            target_workspace: "DynamicEditorWorkspaceWindow | None" = None,
    ) -> DynamicEditorTab | None:
        """
        Open the dynamic editor for one API object in this workspace session.

        :param api_object: Device or template to edit.
        :param circuit: Circuit that owns the device.
        :param preferred_mode: Explicit requested mode, if any.
        :param target_workspace: Preferred destination workspace.
        :return: Open editor page or ``None`` when no dynamic editor exists.
        """
        entry = build_dynamic_editor_entry(api_object, circuit)
        if entry is None:
            return None
        else:
            pass
        return self.open_entry(
            entry,
            preferred_mode=preferred_mode,
            target_workspace=target_workspace,
        )

    def open_dynamic_events_for(
            self,
            api_object: ALL_DEV_TYPES,
            circuit: MultiCircuit,
            mode: DynamicSimulationMode,
            target_workspace: "DynamicEditorWorkspaceWindow | None" = None,
    ) -> DynamicEventsPage | None:
        """Open one device's RMS or EMT events in this workspace family.

        :param api_object: Device whose events will be edited.
        :param circuit: Circuit that owns the device and event assets.
        :param mode: RMS or EMT event family requested by the caller.
        :param target_workspace: Preferred destination workspace.
        :return: Open events page, or ``None`` when unsupported.
        """
        target: DynamicEditorWorkspaceWindow = target_workspace if target_workspace is not None else self
        if not target.is_available_for_pages():
            raise RuntimeError("Cannot open dynamic events in a closing workspace")
        else:
            pass
        target._set_workspace_circuit(circuit=circuit)
        return self.session.open_dynamic_events_for(
            api_object=api_object,
            circuit=circuit,
            mode=mode,
            target_workspace=target,
        )

    def show_hide_tree(self) -> None:
        """
        Toggle visibility of the device tree panel.

        :return: None.
        """
        self.ui.treeFrame.setVisible(not self.ui.treeFrame.isVisible())

    def set_tree_visible(self, visible: bool) -> None:
        """
        Set visibility of the device tree panel explicitly.

        :param visible: Desired visibility state.
        :return: None.
        """
        self.ui.treeFrame.setVisible(visible)

    def get_current_block_editor(self) -> DynamicBlockEditorGUI | None:
        """
        Return the currently selected block editor tab, if any.

        :return: Active block editor or ``None``.
        """
        page = self.current_page()
        if isinstance(page, DynamicEditorTab):
            return page.editor
        else:
            pass
        if isinstance(page, DynamicBlockEditorGUI):
            return page
        else:
            pass
        return None



    def _set_workspace_circuit(self, circuit: MultiCircuit) -> None:
        """
        Bind this workspace tree to one circuit and rebuild its contents.

        :param circuit: Circuit to display in the tree.
        :return: None.
        """
        if self._current_circuit is circuit:
            return
        else:
            pass
        self._current_circuit = circuit
        self.device_tree_widget.set_circuit(circuit)

    def _rebuild_tree(self) -> None:
        """
        Rebuild the left-side device tree from the current circuit.

        :return: None.
        """
        self.device_tree_widget.rebuild()

    def _apply_tree_filter(self, text: str) -> None:
        """
        Apply the current search text to the device tree.

        :param text: Search text entered by the user.
        :return: None.
        """
        self.device_tree_widget.apply_filter(text)

    def _entry_from_tree_index(self, index: QtCore.QModelIndex) -> DynamicEditorEntry | None:
        """
        Resolve one visible tree index back to its dynamic-editor entry.

        :param index: Visible proxy-model index.
        :return: Backing entry or ``None``.
        """
        return self.device_tree_widget.entry_from_index(index)

    def _get_tree_entry_modes(self, index: QtCore.QModelIndex) -> tuple[DynamicSimulationMode, ...]:
        """
        Return the modes supported by the tree entry at one index.

        :param index: Visible proxy-model index.
        :return: Supported dynamic modes for that entry.
        """
        entry = self._entry_from_tree_index(index)
        if entry is None:
            return tuple()
        else:
            pass
        return entry.available_modes

    def _open_tree_entry(self, index: QtCore.QModelIndex, mode: DynamicSimulationMode) -> DynamicBlockEditorGUI | None:
        """
        Open one tree entry in the requested dynamic mode.

        :param index: Visible proxy-model index.
        :param mode: Requested dynamic mode.
        :return: Open editor page or ``None`` when opening is invalid.
        """
        entry = self._entry_from_tree_index(index)
        if entry is None or mode not in entry.available_modes:
            return None
        else:
            pass
        return self.open_entry(entry, preferred_mode=mode, target_workspace=self)

    def _selected_dynamic_entry(self) -> DynamicEditorEntry | None:
        """
        Return the selected tree entry, falling back to the active tab entry.

        :return: Selected dynamic editor entry or ``None``.
        """
        # Toolbar actions belong to the workspace, so the device tree selection
        # is the first source even when no editor tab has been opened yet.
        tree_index: QtCore.QModelIndex = self.ui.treeView.currentIndex()
        entry: DynamicEditorEntry | None = self._entry_from_tree_index(tree_index)
        if entry is None:
            page: DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage | None = self.current_page()
            if page is not None:
                entry = page.get_dynamic_editor_entry()
            else:
                pass
        else:
            pass
        return entry

    @QtCore.Slot(object, object, object)
    def _open_device_tree_entry(
            self,
            entry: object,
            mode: object,
            content_type: object,
    ) -> None:
        """Open model or event content requested by the device tree.

        :param entry: Dynamic device entry emitted by the tree.
        :param mode: RMS or EMT mode emitted by the tree.
        :param content_type: Model or events content selected by the user.
        :return: None.
        """
        valid_request: bool = (
            isinstance(entry, DynamicEditorEntry)
            and isinstance(mode, DynamicSimulationMode)
            and isinstance(content_type, DynamicEditorContentType)
        )
        if valid_request and content_type == DynamicEditorContentType.MODEL:
            self.open_entry(entry, preferred_mode=mode, target_workspace=self)
        elif valid_request and content_type == DynamicEditorContentType.EVENTS:
            self.session.open_events_entry(entry=entry, mode=mode, target_workspace=self)
        else:
            pass

    def open_emt_editor_entry(self, _checked: bool = False) -> None:
        """Open the EMT model editor for the selected device.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        entry: DynamicEditorEntry | None = self._selected_dynamic_entry()
        if entry is not None and DynamicSimulationMode.EMT in entry.available_modes:
            self.open_entry(entry, preferred_mode=DynamicSimulationMode.EMT, target_workspace=self)
        else:
            pass

    def open_rms_editor_entry(self, _checked: bool = False) -> None:
        """Open the RMS model editor for the selected device.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        entry: DynamicEditorEntry | None = self._selected_dynamic_entry()
        if entry is not None and DynamicSimulationMode.RMS in entry.available_modes:
            self.open_entry(entry, preferred_mode=DynamicSimulationMode.RMS, target_workspace=self)
        else:
            pass

    def open_emt_events_entry(self, _checked: bool = False) -> None:
        """Open the EMT events editor for the selected device.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        entry: DynamicEditorEntry | None = self._selected_dynamic_entry()
        if entry is not None:
            self.session.open_events_entry(entry, mode=DynamicSimulationMode.EMT, target_workspace=self)
        else:
            pass

    def open_rms_events_entry(self, _checked: bool = False) -> None:
        """Open the RMS events editor for the selected device.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        entry: DynamicEditorEntry | None = self._selected_dynamic_entry()
        if entry is not None:
            self.session.open_events_entry(entry, mode=DynamicSimulationMode.RMS, target_workspace=self)
        else:
            pass

    def _on_tree_double_clicked(self, index: QtCore.QModelIndex) -> None:
        """
        Open the double-clicked tree entry in RMS mode.

        :param index: Double-clicked tree index.
        :return: None.
        """
        self._open_tree_entry(index, DynamicSimulationMode.RMS)

    def _on_tab_drag_started(self, index: int) -> None:
        """
        Forward tab-drag bookkeeping to the shared session.

        :param index: Dragged tab index.
        :return: None.
        """
        self.session.handle_tab_drag_started(self, index)

    def _on_tab_detach_requested(self, global_pos: QtCore.QPoint) -> None:
        """
        Detach the dragged tab into a new workspace window.

        :param global_pos: Screen position for the new window.
        :return: None.
        """
        page, source_workspace = self.session.get_pending_tab_drag()
        if page is None or source_workspace is None:
            return
        else:
            pass

        source_workspace.remove_page(page)
        new_workspace = DynamicEditorWorkspaceWindow(session=self.session)
        if source_workspace._current_circuit is not None:
            new_workspace._set_workspace_circuit(source_workspace._current_circuit)
        else:
            pass
        new_workspace.move(global_pos)
        new_workspace.show()
        new_workspace.raise_()
        new_workspace.activateWindow()
        new_workspace.add_editor_page(page, self.session.build_page_tab_title(page), activate=True)
        if source_workspace.editor_tabs.count() == 0:
            source_workspace.close()
        else:
            pass
        self.session.clear_pending_tab_drag()

    def _on_tab_reattach_requested(self, _global_pos: QtCore.QPoint | int, target_index: int) -> None:
        """
        Reattach the dragged tab into this workspace window.

        :param _global_pos: Drop position emitted by the tab widget.
        :param target_index: Destination tab index.
        :return: None.
        """
        page, source_workspace = self.session.get_pending_tab_drag()
        if page is None or source_workspace is None:
            return
        else:
            pass

        if source_workspace is self:
            self.session.clear_pending_tab_drag()
            return
        else:
            pass

        if source_workspace._current_circuit is not None:
            self._set_workspace_circuit(source_workspace._current_circuit)
        else:
            pass
        source_workspace.remove_page(page)
        self.add_editor_page(page, self.session.build_page_tab_title(page), activate=True, insert_index=target_index)
        if source_workspace.editor_tabs.count() == 0:
            source_workspace.close()
        else:
            pass
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.session.clear_pending_tab_drag()

    def _on_current_tab_changed(self, index: int) -> None:
        """
        Refresh window state after the current tab changes.

        :param index: Newly selected tab index.
        :return: None.
        """
        page = self.page_at(index)
        if page is not None:
            self.note_page_activated(page)
        else:
            pass
        self._refresh_window_title()

    def add_editor_page(
            self,
            page: DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage,
            tab_title: str,
            activate: bool = True,
            insert_index: int = -1,
    ) -> None:
        """
        Insert one editor page into the tab widget.

        :param page: Page widget to insert.
        :param tab_title: Visible tab title.
        :param activate: Whether to activate the inserted page.
        :param insert_index: Target insertion index, or ``-1`` to append.
        :return: None.
        """
        if not self.is_available_for_pages():
            raise RuntimeError("Cannot add a dynamic editor page to a closing workspace")
        else:
            pass

        if insert_index < 0 or insert_index > self.editor_tabs.count():
            index = self.editor_tabs.addTab(page, tab_title)
        else:
            index = self.editor_tabs.insertTab(insert_index, page, tab_title)

        if activate:
            self.editor_tabs.setCurrentIndex(index)
        else:
            pass

        self._refresh_window_title()

    def index_of_page(
            self,
            page: DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage,
    ) -> int:
        """
        Return the tab index for one page, or ``-1`` when absent.

        :param page: Page to locate.
        :return: Tab index or ``-1``.
        """
        return self.editor_tabs.indexOf(page)

    def page_at(
            self,
            index: int,
    ) -> DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage | None:
        """
        Return the page at one tab index.

        :param index: Tab index to inspect.
        :return: Page at that index or ``None``.
        """
        if index < 0 or index >= self.editor_tabs.count():
            return None
        else:
            pass
        page = self.editor_tabs.widget(index)
        if isinstance(page, (DynamicBlockEditorGUI, DynamicEditorTab, DynamicEventsPage)):
            return page
        else:
            return None

    def pages_iter(self) -> Iterator[DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage]:
        """Yield every valid editor page in tab order.

        :return: Iterator over the hosted dynamic editor pages.
        """
        for index in range(self.editor_tabs.count()):
            page = self.editor_tabs.widget(index)
            if isinstance(page, (DynamicBlockEditorGUI, DynamicEditorTab, DynamicEventsPage)):
                yield page
            else:
                pass

    def current_page(self) -> DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage | None:
        """
        Return the currently selected tab page.

        :return: Current page or ``None``.
        """
        return self.page_at(self.editor_tabs.currentIndex())

    def remove_page(
            self,
            page: DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage,
    ) -> None:
        """
        Remove one page from the tab widget.

        :param page: Page to remove.
        :return: None.
        """
        index = self.index_of_page(page)
        if index >= 0:
            self.editor_tabs.removeTab(index)
        else:
            pass
        self._refresh_window_title()

    def set_page_tab_title(
            self,
            page: DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage,
            title: str,
    ) -> None:
        """
        Update the visible tab title for one page.

        :param page: Page whose title should be updated.
        :param title: New visible title.
        :return: None.
        """
        index = self.index_of_page(page)
        if index >= 0:
            self.editor_tabs.setTabText(index, title)
        else:
            pass
        self._refresh_window_title()

    def close_tab_at(self, index: int) -> None:
        """
        Close the page at one tab index after running close guards.

        :param index: Tab index to close.
        :return: None.
        """
        page = self.page_at(index)
        if page is None:
            return
        else:
            pass

        pages_to_close: list[DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage] = list((page,))
        if not self.session.can_close_pages(pages=pages_to_close, parent=self):
            return
        else:
            pass

        # Both supported page families expose the same explicit teardown
        # contract, so the workspace can release them without reflection.
        page.prepare_to_delete()
        self.session.unregister_page(page)
        self.remove_page(page)
        page.setParent(None)
        page.deleteLater()

        if self.editor_tabs.count() == 0:
            self.close()
        else:
            pass

    def _dispose_all_pages(self) -> None:
        """Dispose every editor page after its close guards have succeeded.

        The workspace owns the complete editor hierarchy. Tearing pages down
        here ensures floating block-properties docks are destroyed before the
        circuit that backs them is replaced.

        :return: None.
        """
        # Iterate over a stable snapshot because removing each tab changes the
        # live tab order and unregisters the page from the shared session.
        pages_to_dispose: list[DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage] = list(self.pages_iter())
        page_to_dispose: DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage
        for page_to_dispose in pages_to_dispose:
            page_to_dispose.prepare_to_delete()
            self.session.unregister_page(page_to_dispose)
            self.remove_page(page_to_dispose)
            page_to_dispose.setParent(None)
            page_to_dispose.deleteLater()

    def close_for_project_replacement(self) -> None:
        """Close this workspace after session-wide guards were accepted.

        Project replacement validates every page in every detachable workspace
        before closing the first window. This method performs only the teardown
        phase so a later workspace cannot leave a partially closed editor
        family by rejecting the replacement.

        :return: None.
        """
        # Stop routing new pages to the old circuit before releasing any editor
        # object that still retains its device and symbolic working tree.
        self._accepts_new_pages = False
        self._dispose_all_pages()

        # With no pages left, the regular close event can unregister and delete
        # the top-level workspace without displaying the page guards again.
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Close the workspace window after checking every open page.

        :param event: Qt close event.
        :return: None.
        """
        pages_to_close: list[DynamicBlockEditorGUI | DynamicEditorTab | DynamicEventsPage] = list(self.pages_iter())
        if not self.session.can_close_pages(pages=pages_to_close, parent=self):
            event.ignore()
            return
        else:
            pass

        self._accepts_new_pages = False
        self._dispose_all_pages()

        self.session.unregister_workspace(self)
        event.accept()

    def _refresh_window_title(self) -> None:
        """
        Refresh the top-level window title from the active tab.

        :return: None.
        """
        current_page = self.current_page()
        if current_page is None:
            self.setWindowTitle(self.tr("Dynamic Editor Workspace"))
            return
        else:
            pass

        current_title = self.editor_tabs.tabText(self.editor_tabs.currentIndex())
        self.setWindowTitle(self.tr("Dynamic Editor - {title}").format(title=current_title))

    def set_dark_mode(self) -> None:
        """
        Apply dark mode to every hosted editor page.

        :return: None.
        """
        for page in self.pages_iter():
            page.set_dark_mode()

    def set_light_mode(self) -> None:
        """
        Apply light mode to every hosted editor page.

        :return: None.
        """
        for page in self.pages_iter():
            page.set_light_mode()
