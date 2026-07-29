# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any, List, Dict, Tuple, TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_tab import DynamicEditorTab
from VeraGrid.Session.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Session.dynamic_editor_entries import build_dynamic_editor_entry
from VeraGrid.Session.dynamic_editor_entries import get_block_for_entry
from VeraGrid.Session.dynamic_editor_entries import get_templates_for_entry
from VeraGridEngine.enumerations import DynamicSimulationMode, DynEditorGraphicsModes

if TYPE_CHECKING:
    from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_window import DynamicEditorWorkspaceWindow


def _get_page_entry(page: DynamicBlockEditorGUI | None) -> DynamicEditorEntry | None:
    """
    Return the cached dynamic-editor entry stored on one page widget.

    :param page: Candidate workspace page.
    :return: Cached entry or ``None`` when unavailable.
    """
    if page is None:
        return None
    return page.get_dynamic_editor_entry()


def get_page_mode(page: DynamicBlockEditorGUI | None) -> DynamicSimulationMode | None:
    """
    Return the cached dynamic-editor mode stored on one page widget.

    :param page: Candidate workspace page.
    :return: Cached mode or ``None`` when unavailable.
    """
    if page is None:
        return None
    return page.get_dynamic_editor_mode()


class DynamicEditorWorkspaceSession(QtCore.QObject):
    """
    Shared state for one family of detachable workspace windows.
    """

    def __init__(self) -> None:
        """
        Initialize the shared session state for one workspace family.

        :param current_theme:
        :return: None.
        """
        super().__init__()
        self._open_workspaces: List[DynamicEditorWorkspaceWindow] = list()
        self._session_pages: Dict[str, DynamicEditorTab] = dict()
        self._last_mode_by_key_base: Dict[str, DynamicSimulationMode] = dict()
        self._last_active_workspace: DynamicEditorWorkspaceWindow | None = None
        self._pending_drag_page: DynamicEditorTab | DynamicBlockEditorGUI | None = None
        self._pending_drag_workspace: DynamicEditorWorkspaceWindow | None = None
        self._retained_workspaces: List[DynamicEditorWorkspaceWindow] = list()
        self._retained_pages: List[DynamicEditorTab | DynamicBlockEditorGUI] = list()
        self.current_theme: DynEditorGraphicsModes = DynEditorGraphicsModes.DARK

    def register_workspace(self, workspace: "DynamicEditorWorkspaceWindow") -> None:
        """
        Register one live workspace window in this shared session.

        :param workspace: Workspace to register.
        :return: None.
        """
        if workspace not in self._open_workspaces:
            self._open_workspaces.append(workspace)
        if workspace not in self._retained_workspaces:
            self._retained_workspaces.append(workspace)
        self._last_active_workspace = workspace

    def unregister_workspace(self, workspace: "DynamicEditorWorkspaceWindow") -> None:
        """
        Remove one workspace window from this shared session.

        :param workspace: Workspace to unregister.
        :return: None.
        """
        if workspace in self._open_workspaces:
            self._open_workspaces.remove(workspace)
        if self._last_active_workspace is workspace:
            self._last_active_workspace = self._open_workspaces[-1] if self._open_workspaces else None

    def get_open_workspaces(self) -> list["DynamicEditorWorkspaceWindow"]:
        """
        Return the currently open workspaces belonging to this session.

        :return: Open workspaces for this session.
        """
        return list(self._open_workspaces)

    def get_last_active_workspace(self) -> "DynamicEditorWorkspaceWindow | None":
        """
        Return the workspace that should receive newly opened editor tabs.

        :return: Preferred workspace or ``None`` when no window is open.
        """
        if self._last_active_workspace is not None:
            return self._last_active_workspace
        if len(self._open_workspaces) > 0:
            return self._open_workspaces[-1]
        return None

    def reset_for_tests(self) -> None:
        """
        Close every workspace and clear all retained session state.

        :return: None.
        """
        for workspace in list(self._open_workspaces):
            workspace.close()
            workspace.deleteLater()

        app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
        if app is not None:
            app.processEvents()

        self._open_workspaces.clear()
        self._session_pages.clear()
        self._last_mode_by_key_base.clear()
        self._last_active_workspace = None
        self._pending_drag_page = None
        self._pending_drag_workspace = None
        self._retained_workspaces.clear()
        self._retained_pages.clear()

    def workspace_for_page(self, page: DynamicBlockEditorGUI | DynamicEditorTab) -> "DynamicEditorWorkspaceWindow | None":
        """
        Locate the workspace that currently owns one editor page.

        :param page: Page to resolve.
        :return: Owning workspace or ``None``.
        """
        workspace: DynamicEditorWorkspaceWindow
        for workspace in self._open_workspaces:
            if workspace.index_of_page(page) >= 0:
                return workspace
            else:
                pass

        return None

    def note_page_activated(self, page: DynamicBlockEditorGUI | DynamicEditorTab) -> None:
        """
        Record the active page so reopen operations reuse the right mode and window.

        :param page: Newly activated page.
        :return: None.
        """
        entry = _get_page_entry(page)
        mode = get_page_mode(page)
        workspace = self.workspace_for_page(page)
        if entry is not None and mode is not None:
            self._last_mode_by_key_base[entry.key_base] = mode
        if workspace is not None:
            self._last_active_workspace = workspace

    @staticmethod
    def build_page_tab_title(page: DynamicBlockEditorGUI | DynamicEditorTab) -> str:
        """
        Build the tab title shown for one page, including dirty-state marker.

        :param page: Page whose title will be shown.
        :return: User-facing tab title.
        """
        title = str(page.get_dynamic_editor_display_title())
        if page.has_unapplied_changes:
            return f"* {title}"
        return title

    def refresh_open_page_title(self, page: DynamicBlockEditorGUI) -> None:
        """
        Refresh the tab title for one open page if its workspace is still alive.

        :param page: Page whose title should be refreshed.
        :return: None.
        """
        workspace = self.workspace_for_page(page)
        if workspace is not None:
            workspace.set_page_tab_title(page, self.build_page_tab_title(page))

    def connect_page_signals(self, page: "DynamicBlockEditorGUI") -> None:
        """
        Connect long-lived page signals needed by the workspace session.

        :param page: Editor page whose signals will be connected.
        :return: None.
        """
        page.dirtyStateChanged.connect(self._on_page_dirty_state_changed)

    def _on_page_dirty_state_changed(self, _dirty: bool) -> None:
        """
        Refresh the sender page title after its dirty state changes.

        :param _dirty: New dirty-state flag emitted by the page.
        :return: None.
        """
        page: DynamicBlockEditorGUI = self.sender()
        if isinstance(page, QtWidgets.QWidget):
            self.refresh_open_page_title(page)

    def resolve_mode(self,
                     entry: DynamicEditorEntry,
                     preferred_mode: DynamicSimulationMode | None = None) -> DynamicSimulationMode:
        """
        Choose the dynamic mode to open for one entry.

        :param entry: Entry being opened.
        :param preferred_mode: Explicit requested mode, if any.
        :return: Mode that should be opened.
        """
        if preferred_mode is not None:
            return preferred_mode
        last_mode = self._last_mode_by_key_base.get(entry.key_base, None)
        if last_mode is not None and last_mode in entry.available_modes:
            return last_mode
        if DynamicSimulationMode.RMS in entry.available_modes:
            return DynamicSimulationMode.RMS
        return entry.available_modes[0]

    def create_page(self, entry: DynamicEditorEntry, mode: DynamicSimulationMode) -> "DynamicEditorTab":
        """
        Instantiate one embedded editor tab for the requested entry and mode.

        :param entry: Entry being edited.
        :param mode: Dynamic mode to open.
        :return: Newly created editor tab.
        """
        from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_tab import DynamicEditorTab

        page = DynamicEditorTab(
            var_factory=entry.circuit.var_factory,
            block=get_block_for_entry(entry, mode),
            api_object=entry.api_object,
            mode=mode,
            templates_list=get_templates_for_entry(entry, mode),
            circuit=entry.circuit,
            current_theme = self.current_theme
        )
        page.set_dynamic_editor_entry(entry)
        self.connect_page_signals(page)
        self._retained_pages.append(page)
        return page

    def open_entry(self,
                   entry: DynamicEditorEntry,
                   preferred_mode: DynamicSimulationMode | None = None,
                   target_workspace: "DynamicEditorWorkspaceWindow | None" = None) -> "DynamicEditorTab":
        """
        Open one entry in the session, reusing an existing page when possible.

        :param entry: Entry to open.
        :param preferred_mode: Explicit requested mode, if any.
        :param target_workspace: Preferred destination workspace.
        :return: Open editor tab for the requested entry.
        """
        mode = self.resolve_mode(entry, preferred_mode)
        session_key = entry.session_key(mode)
        existing_page = self._session_pages.get(session_key, None)
        if existing_page is not None:
            workspace = self.workspace_for_page(existing_page)
            if workspace is None:
                self.unregister_page(existing_page)
            else:
                workspace.editor_tabs.setCurrentWidget(existing_page)
                workspace.showNormal()
                workspace.raise_()
                workspace.activateWindow()
                self.note_page_activated(existing_page)
                return existing_page

        workspace = target_workspace if target_workspace is not None else self.get_last_active_workspace()
        if workspace is None:
            raise RuntimeError("DynamicEditorWorkspaceSession requires an existing workspace")
        page = self.create_page(entry, mode)
        self._session_pages[session_key] = page
        self._last_mode_by_key_base[entry.key_base] = mode
        workspace.add_editor_page(page, self.build_page_tab_title(page), activate=True)
        self._last_active_workspace = workspace
        return page

    def open_dynamic_editor_for(
            self,
            api_object: Any,
            circuit: Any,
            preferred_mode: DynamicSimulationMode | None = None,
            target_workspace: "DynamicEditorWorkspaceWindow | None" = None
    ) -> "DynamicEditorTab | None":
        """
        Build and open the dynamic-editor entry for one API object.

        :param api_object: Device or template to edit.
        :param circuit: Circuit that owns the device.
        :param preferred_mode: Explicit requested mode, if any.
        :param target_workspace: Preferred destination workspace.
        :return: Open editor tab or ``None`` when no dynamic editor exists.
        """
        entry = build_dynamic_editor_entry(api_object, circuit)
        if entry is None:
            return None
        return self.open_entry(entry, preferred_mode=preferred_mode, target_workspace=target_workspace)

    def unregister_page(self, page: DynamicBlockEditorGUI | DynamicEditorTab) -> None:
        """
        Forget one page in the session registries.

        :param page: Page being removed.
        :return: None.
        """
        entry = _get_page_entry(page)
        mode = get_page_mode(page)
        if entry is not None and mode is not None:
            self._session_pages.pop(entry.session_key(mode), None)

        if self._pending_drag_page is page:
            self._pending_drag_page = None
            self._pending_drag_workspace = None

    def handle_tab_drag_started(self, workspace: "DynamicEditorWorkspaceWindow", index: int) -> None:
        """
        Remember which page started a detach or reattach drag gesture.

        :param workspace: Source workspace.
        :param index: Dragged tab index.
        :return: None.
        """
        page = workspace.page_at(index)
        if page is not None:
            self._pending_drag_page = page
            self._pending_drag_workspace = workspace

    def get_pending_tab_drag(self) -> Tuple[DynamicBlockEditorGUI | None, "DynamicEditorWorkspaceWindow | None"]:
        """
        Return the page and workspace remembered for the current drag gesture.

        :return: Pending dragged page and its source workspace.
        """
        return self._pending_drag_page, self._pending_drag_workspace

    def clear_pending_tab_drag(self) -> None:
        """
        Clear the remembered drag source information.

        :return: None.
        """
        self._pending_drag_page = None
        self._pending_drag_workspace = None

    def set_dark_mode(self):
        """
        Set the dark mode
        :return:
        """
        self.current_theme = DynEditorGraphicsModes.DARK
        for ws in self._open_workspaces:
            ws.set_dark_mode()

    def set_light_mode(self):
        """
                Set the dark mode
                :return:
                """
        self.current_theme = DynEditorGraphicsModes.LIGHT
        for ws in self._open_workspaces:
            ws.set_light_mode()