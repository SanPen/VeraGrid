# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any, Optional

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import DynamicEditorPickerDialog
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import build_dynamic_editor_entry
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import build_dynamic_editor_title
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import get_block_for_entry
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import get_templates_for_entry
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import iter_dynamic_editor_entries
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_window import DynamicEditorWorkspaceWindow
from VeraGridEngine.enumerations import DynamicSimulationMode


class DynamicEditorWorkspaceManager(QtCore.QObject):
    """
    Central launcher/registry for the unified Dynamic Editor workspaces.
    """

    _instance: "DynamicEditorWorkspaceManager | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._workspaces: list[DynamicEditorWorkspaceWindow] = list()
        self._page_to_workspace: dict[QtWidgets.QWidget, DynamicEditorWorkspaceWindow] = dict()
        self._page_to_entry: dict[QtWidgets.QWidget, DynamicEditorEntry] = dict()
        self._page_to_mode: dict[QtWidgets.QWidget, DynamicSimulationMode] = dict()
        self._session_pages: dict[str, QtWidgets.QWidget] = dict()
        self._last_mode_by_key_base: dict[str, DynamicSimulationMode] = dict()
        self._last_active_workspace: DynamicEditorWorkspaceWindow | None = None
        self._pending_drag_page: QtWidgets.QWidget | None = None
        self._pending_drag_workspace: DynamicEditorWorkspaceWindow | None = None

    @classmethod
    def instance(cls) -> "DynamicEditorWorkspaceManager":
        if cls._instance is None:
            cls._instance = DynamicEditorWorkspaceManager()
        return cls._instance

    def reset_for_tests(self) -> None:
        for workspace in list(self._workspaces):
            workspace.close()
            workspace.deleteLater()

        app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
        if app is not None:
            app.processEvents()
        else:
            pass

        self._workspaces.clear()
        self._page_to_workspace.clear()
        self._page_to_entry.clear()
        self._page_to_mode.clear()
        self._session_pages.clear()
        self._last_mode_by_key_base.clear()
        self._last_active_workspace = None
        self._pending_drag_page = None
        self._pending_drag_workspace = None

    def register_workspace(self, workspace: DynamicEditorWorkspaceWindow) -> None:
        if workspace not in self._workspaces:
            self._workspaces.append(workspace)
        self._last_active_workspace = workspace

    def unregister_workspace(self, workspace: DynamicEditorWorkspaceWindow) -> None:
        if workspace in self._workspaces:
            self._workspaces.remove(workspace)
        if self._last_active_workspace is workspace:
            self._last_active_workspace = self._workspaces[-1] if self._workspaces else None

    def note_page_activated(self, page: QtWidgets.QWidget) -> None:
        entry = self._page_to_entry.get(page, None)
        mode = self._page_to_mode.get(page, None)
        workspace = self._page_to_workspace.get(page, None)
        if entry is not None and mode is not None:
            self._last_mode_by_key_base[entry.key_base] = mode
        if workspace is not None:
            self._last_active_workspace = workspace

    def build_page_tab_title(self, page: QtWidgets.QWidget) -> str:
        entry = self._page_to_entry[page]
        mode = self._page_to_mode[page]
        title = build_dynamic_editor_title(entry.api_object, mode)
        # Todo:remove getattr
        if getattr(page, "has_unapplied_changes", False):
            return f"* {title}"
        return title

    def _connect_page_signals(self, page: QtWidgets.QWidget) -> None:
        # Todo:remove hasattr
        if hasattr(page, "dirtyStateChanged"):
            page.dirtyStateChanged.connect(lambda _dirty, page=page: self.refresh_page_title(page))

    def refresh_page_title(self, page: QtWidgets.QWidget) -> None:
        workspace = self._page_to_workspace.get(page, None)
        if workspace is None:
            return
        workspace.set_page_tab_title(page, self.build_page_tab_title(page))

    def _create_workspace(self, global_pos: QtCore.QPoint | None = None) -> DynamicEditorWorkspaceWindow:
        workspace = DynamicEditorWorkspaceWindow(manager=self)
        self.register_workspace(workspace)
        if global_pos is not None:
            workspace.move(global_pos)
        workspace.show()
        workspace.raise_()
        workspace.activateWindow()
        return workspace

    def _resolve_workspace(self, preferred_workspace: DynamicEditorWorkspaceWindow | None = None) -> DynamicEditorWorkspaceWindow:
        if preferred_workspace is not None:
            self._last_active_workspace = preferred_workspace
            return preferred_workspace
        if self._last_active_workspace is not None:
            return self._last_active_workspace
        if len(self._workspaces) > 0:
            self._last_active_workspace = self._workspaces[-1]
            return self._last_active_workspace
        return self._create_workspace()

    def _resolve_mode(self, entry: DynamicEditorEntry, preferred_mode: DynamicSimulationMode | None = None) -> DynamicSimulationMode:
        if preferred_mode is not None:
            return preferred_mode
        last_mode = self._last_mode_by_key_base.get(entry.key_base, None)
        if last_mode is not None and last_mode in entry.available_modes:
            return last_mode
        if DynamicSimulationMode.RMS in entry.available_modes:
            return DynamicSimulationMode.RMS
        return entry.available_modes[0]

    def _create_page(self, entry: DynamicEditorEntry, mode: DynamicSimulationMode) -> DynamicBlockEditorGUI:
        page = DynamicBlockEditorGUI(
            var_factory=entry.circuit.var_factory,
            block=get_block_for_entry(entry, mode),
            api_object=entry.api_object,
            mode=mode,
            templates_list=get_templates_for_entry(entry, mode),
            circuit=entry.circuit,
            main_editor=True,
            modal=False,
            workspace_embedded=True,
        )
        self._connect_page_signals(page)
        return page

    def open_entry(self,
                   entry: DynamicEditorEntry,
                   preferred_mode: DynamicSimulationMode | None = None,
                   target_workspace: DynamicEditorWorkspaceWindow | None = None) -> DynamicBlockEditorGUI:
        mode = self._resolve_mode(entry, preferred_mode)
        session_key = entry.session_key(mode)
        existing_page = self._session_pages.get(session_key, None)
        if existing_page is not None:
            workspace = self._page_to_workspace[existing_page]
            workspace.ui.editorTabs.setCurrentWidget(existing_page)
            workspace.showNormal()
            workspace.raise_()
            workspace.activateWindow()
            self.note_page_activated(existing_page)
            return existing_page  # type: ignore[return-value]

        workspace = self._resolve_workspace(target_workspace)
        page = self._create_page(entry, mode)
        self._page_to_workspace[page] = workspace
        self._page_to_entry[page] = entry
        self._page_to_mode[page] = mode
        self._session_pages[session_key] = page
        self._last_mode_by_key_base[entry.key_base] = mode
        workspace.add_editor_page(page, self.build_page_tab_title(page), activate=True)
        self._last_active_workspace = workspace
        return page

    def open_dynamic_editor_for(self,
                                api_object: Any,
                                circuit: Any,
                                preferred_mode: DynamicSimulationMode | None = None,
                                target_workspace: DynamicEditorWorkspaceWindow | None = None) -> DynamicBlockEditorGUI | None:
        entry = build_dynamic_editor_entry(api_object, circuit)
        if entry is None:
            return None
        return self.open_entry(entry, preferred_mode=preferred_mode, target_workspace=target_workspace)

    def unregister_page(self, page: QtWidgets.QWidget) -> None:
        entry = self._page_to_entry.pop(page, None)
        mode = self._page_to_mode.pop(page, None)
        self._page_to_workspace.pop(page, None)
        if entry is not None and mode is not None:
            self._session_pages.pop(entry.session_key(mode), None)

        if self._pending_drag_page is page:
            self._pending_drag_page = None
            self._pending_drag_workspace = None

    def open_picker(self, workspace: DynamicEditorWorkspaceWindow) -> None:
        current_page = workspace.current_page()
        current_entry = self._page_to_entry.get(current_page, None) if current_page is not None else None
        current_mode = self._page_to_mode.get(current_page, None) if current_page is not None else None

        if current_entry is None:
            return

        entries = sorted(iter_dynamic_editor_entries(current_entry.circuit), key=lambda entry: entry.display_name.lower())
        dialog = DynamicEditorPickerDialog(entries=entries, current_entry=current_entry, current_mode=current_mode, parent=workspace)
        if dialog.exec():
            selection = dialog.get_selection()
            if selection is not None:
                entry, mode = selection
                self.open_entry(entry, preferred_mode=mode, target_workspace=workspace)

    def handle_tab_drag_started(self, workspace: DynamicEditorWorkspaceWindow, index: int) -> None:
        page = workspace.page_at(index)
        self._pending_drag_page = page
        self._pending_drag_workspace = workspace

    def handle_tab_detach(self, workspace: DynamicEditorWorkspaceWindow, global_pos: QtCore.QPoint) -> None:
        page = self._pending_drag_page
        source_workspace = self._pending_drag_workspace
        if page is None or source_workspace is None:
            return

        source_workspace.remove_page(page)
        new_workspace = self._create_workspace(global_pos)
        self._page_to_workspace[page] = new_workspace
        new_workspace.add_editor_page(page, self.build_page_tab_title(page), activate=True)
        if source_workspace.ui.editorTabs.count() == 0:
            source_workspace.close()
        self._last_active_workspace = new_workspace
        self._pending_drag_page = None
        self._pending_drag_workspace = None

    def handle_tab_reattach(self,
                            target_workspace: DynamicEditorWorkspaceWindow,
                            _global_pos: QtCore.QPoint,
                            target_index: int) -> None:
        page = self._pending_drag_page
        source_workspace = self._pending_drag_workspace
        if page is None or source_workspace is None:
            return

        if source_workspace is target_workspace:
            self._pending_drag_page = None
            self._pending_drag_workspace = None
            return

        source_workspace.remove_page(page)
        self._page_to_workspace[page] = target_workspace
        target_workspace.add_editor_page(page, self.build_page_tab_title(page), activate=True, insert_index=target_index)
        if source_workspace.ui.editorTabs.count() == 0:
            source_workspace.close()
        target_workspace.showNormal()
        target_workspace.raise_()
        target_workspace.activateWindow()
        self._last_active_workspace = target_workspace
        self._pending_drag_page = None
        self._pending_drag_workspace = None


def open_dynamic_editor(api_object: Any,
                        circuit: Any,
                        preferred_mode: DynamicSimulationMode | None = None,
                        target_workspace: DynamicEditorWorkspaceWindow | None = None) -> DynamicBlockEditorGUI | None:
    """
    Unified public launcher used by context menus and dialogs.
    """

    return DynamicEditorWorkspaceManager.instance().open_dynamic_editor_for(
        api_object=api_object,
        circuit=circuit,
        preferred_mode=preferred_mode,
        target_workspace=target_workspace,
    )
