# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import DynamicEditorAddButton
from VeraGrid.Gui.DynamicModelEditor.dyn_editor_multiwindow_engine import DetachableEditorTabWidget
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace import Ui_DynamicEditorWorkspaceWindow


class DynamicEditorWorkspaceWindow(QtWidgets.QMainWindow):
    """
    Tabbed workspace hosting one or more dynamic editor pages.
    """

    def __init__(self, manager: Any, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_DynamicEditorWorkspaceWindow()
        self.ui.setupUi(self)
        self.manager = manager
        self._add_button = DynamicEditorAddButton(self)

        self.editor_tabs = DetachableEditorTabWidget(self)
        self.ui.verticalLayout.replaceWidget(self.ui.editorTabs, self.editor_tabs)
        self.ui.editorTabs.deleteLater()
        self.ui.editorTabs = self.editor_tabs
        self.ui.editorTabs.setCornerWidget(self._add_button, QtCore.Qt.Corner.TopRightCorner)

        self._add_button.clicked.connect(self._open_picker)
        self._add_button.tabWidgetDropRequested.connect(lambda _pos: self.manager.handle_tab_reattach(self, _pos, -1))
        self.ui.editorTabs.tabCloseRequested.connect(self.close_tab_at)
        self.ui.editorTabs.currentChanged.connect(self._on_current_tab_changed)
        self.ui.editorTabs.tabDragStarted.connect(self._on_tab_drag_started)
        self.ui.editorTabs.detachRequested.connect(self._on_tab_detach_requested)
        self.ui.editorTabs.reattachRequested.connect(self._on_tab_reattach_requested)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self._refresh_window_title()

    def _open_picker(self) -> None:
        self.manager.open_picker(self)

    def _on_tab_drag_started(self, index: int) -> None:
        self.manager.handle_tab_drag_started(self, index)

    def _on_tab_detach_requested(self, global_pos: QtCore.QPoint) -> None:
        self.manager.handle_tab_detach(self, global_pos)

    def _on_tab_reattach_requested(self, global_pos: QtCore.QPoint, target_index: int) -> None:
        self.manager.handle_tab_reattach(self, global_pos, target_index)

    def _on_current_tab_changed(self, index: int) -> None:
        page = self.page_at(index)
        if page is not None:
            self.manager.note_page_activated(page)
        else:
            pass
        self._refresh_window_title()

    def add_editor_page(self,
                        page: QtWidgets.QWidget,
                        tab_title: str,
                        activate: bool = True,
                        insert_index: int = -1) -> None:
        if insert_index < 0 or insert_index > self.ui.editorTabs.count():
            index = self.ui.editorTabs.addTab(page, tab_title)
        else:
            index = self.ui.editorTabs.insertTab(insert_index, page, tab_title)

        if activate:
            self.ui.editorTabs.setCurrentIndex(index)

        self._refresh_window_title()

    def index_of_page(self, page: QtWidgets.QWidget) -> int:
        return self.ui.editorTabs.indexOf(page)

    def page_at(self, index: int) -> QtWidgets.QWidget | None:
        if index < 0 or index >= self.ui.editorTabs.count():
            return None
        return self.ui.editorTabs.widget(index)

    def current_page(self) -> QtWidgets.QWidget | None:
        return self.page_at(self.ui.editorTabs.currentIndex())

    def remove_page(self, page: QtWidgets.QWidget) -> None:
        index = self.index_of_page(page)
        if index >= 0:
            self.ui.editorTabs.removeTab(index)
        self._refresh_window_title()

    def set_page_tab_title(self, page: QtWidgets.QWidget, title: str) -> None:
        index = self.index_of_page(page)
        if index >= 0:
            self.ui.editorTabs.setTabText(index, title)
        self._refresh_window_title()

    def close_tab_at(self, index: int) -> None:
        page = self.page_at(index)
        if page is None:
            return

        can_close = True
        # Todo:remove hasattr
        if hasattr(page, "can_close_editor"):
            can_close = bool(page.can_close_editor(self))
        if not can_close:
            return

        self.manager.unregister_page(page)
        self.remove_page(page)
        page.deleteLater()

        if self.ui.editorTabs.count() == 0:
            self.close()
        else:
            pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        for index in range(self.ui.editorTabs.count() - 1, -1, -1):
            page = self.page_at(index)
            if page is None:
                continue
            # Todo:remove hasattr
            if hasattr(page, "can_close_editor") and not bool(page.can_close_editor(self)):
                event.ignore()
                return

        pages = [self.page_at(index) for index in range(self.ui.editorTabs.count())]
        for page in pages:
            if page is None:
                continue
            self.manager.unregister_page(page)

        self.manager.unregister_workspace(self)
        event.accept()

    def _refresh_window_title(self) -> None:
        current_page = self.current_page()
        if current_page is None:
            self.setWindowTitle("Dynamic Editor Workspace")
            return

        current_title = self.ui.editorTabs.tabText(self.ui.editorTabs.currentIndex())
        self.setWindowTitle(f"Dynamic Editor - {current_title}")
