# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Iterator

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.detachable_editor_tabs_widget import DetachableEditorTabWidget
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_tab import DynamicEditorTab
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace import Ui_DynamicEditorWorkspaceWindow
from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGrid.Gui.gui_functions import add_menu_entry
from VeraGrid.Session.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Session.dynamic_editor_entries import build_dynamic_editor_entry
from VeraGrid.Session.dynamic_editor_entries import iter_dynamic_editor_entries
from VeraGrid.Session.dynamic_editor_workspace_session import DynamicEditorWorkspaceSession
from VeraGridEngine.enumerations import DynamicSimulationMode
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.types import ALL_DEV_TYPES


def build_entry_sort_key(entry: DynamicEditorEntry) -> tuple[str, str]:
    """Return the deterministic sorting key used for device-tree entries.

    :param entry: Entry to sort.
    :return: Lowercase type and name tuple.
    """
    return entry.type_label.lower(), entry.display_name.lower()


class DynamicEditorWorkspaceWindow(QtWidgets.QMainWindow):
    """
    Tabbed workspace hosting one or more dynamic editor pages.
    """

    __slots__ = (
        "__session",
        "_accepts_new_pages",
        "_current_circuit",
        "_tree_model",
        "_tree_proxy",
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
        self._tree_model: QtGui.QStandardItemModel = QtGui.QStandardItemModel(self)
        self._tree_proxy: QtCore.QSortFilterProxyModel = QtCore.QSortFilterProxyModel(self)
        self._tree_proxy.setRecursiveFilteringEnabled(True)
        self._tree_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self._tree_proxy.setSourceModel(self._tree_model)
        self.ui: Ui_DynamicEditorWorkspaceWindow = Ui_DynamicEditorWorkspaceWindow()
        self.ui.setupUi(self)

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
        self.ui.block_editor_actionCheckModel.triggered.connect(self.open_inspect_dialog)
        self.ui.actionCenter.triggered.connect(self.center_view_on_items)
        self.ui.actionZoom_in.triggered.connect(self.zoom_in_view)
        self.ui.actionZoom_out.triggered.connect(self.zoom_out_view)
        self.ui.action_delete_all.triggered.connect(self.delete_all_blocks_with_confirmation)
        self.ui.actionValidate.triggered.connect(self.show_model_consistency_validation)
        self.ui.treeView.setModel(self._tree_proxy)
        self.ui.treeView.setHeaderHidden(True)
        self.ui.treeView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.treeView.doubleClicked.connect(self._on_tree_double_clicked)
        self.ui.treeView.customContextMenuRequested.connect(self._show_tree_context_menu)
        self.ui.searchInTreeLineEdit.setClearButtonEnabled(True)
        self.ui.searchInTreeLineEdit.textChanged.connect(self._apply_tree_filter)

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

    def workspace_for_page(self, page: DynamicBlockEditorGUI) -> "DynamicEditorWorkspaceWindow | None":
        """
        Return the workspace in this session that owns one page.

        :param page: Page to resolve.
        :return: Owning workspace or ``None``.
        """
        return self.session.workspace_for_page(page)

    def note_page_activated(self, page: DynamicBlockEditorGUI) -> None:
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
    ) -> DynamicBlockEditorGUI:
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
    ) -> DynamicBlockEditorGUI | None:
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

    def open_inspect_dialog(self) -> None:
        """
        Open the inspect dialog on the active block editor.

        :return: None.
        """
        editor = self.get_current_block_editor()
        if editor is not None:
            editor.open_inspect_dialog()
        else:
            pass

    def center_view_on_items(self) -> None:
        """
        Center the active block editor view on its scene items.

        :return: None.
        """
        editor = self.get_current_block_editor()
        if editor is not None:
            editor.center_view_on_items()
        else:
            pass

    def zoom_in_view(self) -> None:
        """
        Zoom in the active block editor view.

        :return: None.
        """
        editor = self.get_current_block_editor()
        if editor is not None:
            editor.zoom_in_view()
        else:
            pass

    def zoom_out_view(self) -> None:
        """
        Zoom out the active block editor view.

        :return: None.
        """
        editor = self.get_current_block_editor()
        if editor is not None:
            editor.zoom_out_view()
        else:
            pass

    def delete_all_blocks_with_confirmation(self) -> None:
        """
        Delete all blocks from the active editor after confirmation.

        :return: None.
        """
        editor = self.get_current_block_editor()
        if editor is not None:
            editor.delete_all_blocks_with_confirmation()
        else:
            pass

    def show_model_consistency_validation(self) -> None:
        """
        Run the model-consistency validation on the active editor.

        :return: None.
        """
        editor = self.get_current_block_editor()
        if editor is not None:
            editor.show_model_consistency_validation()
        else:
            pass

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
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        """
        Rebuild the left-side device tree from the current circuit.

        :return: None.
        """
        self._tree_model.clear()
        root = self._tree_model.invisibleRootItem()
        if self._current_circuit is None:
            return
        else:
            pass

        groups: dict[str, QtGui.QStandardItem] = dict()
        entries: list[DynamicEditorEntry] = sorted(
            iter_dynamic_editor_entries(self._current_circuit),
            key=build_entry_sort_key,
        )

        entry: DynamicEditorEntry
        for entry in entries:
            group_item = groups.get(entry.type_label, None)
            if group_item is None:
                group_item = QtGui.QStandardItem(entry.type_label)
                group_item.setEditable(False)
                self._set_device_tree_item_icon(group_item, entry.type_label)
                groups[entry.type_label] = group_item
                root.appendRow(group_item)
            else:
                pass

            item = QtGui.QStandardItem(entry.display_name)
            item.setEditable(False)
            item.setData(entry, QtCore.Qt.ItemDataRole.UserRole)
            item.setToolTip(entry.display_name)
            self._set_device_tree_item_icon(item, entry.type_label)
            group_item.appendRow(item)

        self._apply_tree_filter(self.ui.searchInTreeLineEdit.text())

    def _set_device_tree_item_icon(self, item: QtGui.QStandardItem, icon_key: str) -> None:
        """
        Set the tree icon for one device item when an icon association exists.

        :param item: Tree item that may receive an icon.
        :param icon_key: Key used to look up the icon resource path.
        :return: None.
        """
        icon_path = device_type_icons.get(icon_key, None)
        if icon_path is None:
            return
        else:
            pass
        item.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_path)))

    def _apply_tree_filter(self, text: str) -> None:
        """
        Apply the current search text to the device tree.

        :param text: Search text entered by the user.
        :return: None.
        """
        needle = text.strip()
        if needle == "":
            self._tree_proxy.setFilterRegularExpression(QtCore.QRegularExpression())
        else:
            regex = QtCore.QRegularExpression(
                QtCore.QRegularExpression.escape(needle),
                QtCore.QRegularExpression.PatternOption.CaseInsensitiveOption,
            )
            self._tree_proxy.setFilterRegularExpression(regex)
        self._expand_tree_matches()
        self._select_first_tree_match()

    def _expand_tree_matches(self) -> None:
        """
        Expand the device tree so current matches remain visible.

        :return: None.
        """
        self.ui.treeView.expandAll()

    def _select_first_tree_match(self) -> None:
        """
        Select the first visible device entry after filtering.

        :return: None.
        """
        index = self._first_visible_tree_entry_index()
        if index.isValid():
            self.ui.treeView.setCurrentIndex(index)
            self.ui.treeView.scrollTo(index)
        else:
            pass

    def _first_visible_tree_entry_index(
            self,
            parent: QtCore.QModelIndex = QtCore.QModelIndex(),
    ) -> QtCore.QModelIndex:
        """
        Return the first visible device-entry index under one tree node.

        :param parent: Parent index to search below.
        :return: First visible matching device index, if any.
        """
        row_count = self._tree_proxy.rowCount(parent)
        row: int
        for row in range(row_count):
            index = self._tree_proxy.index(row, 0, parent)
            if self._entry_from_tree_index(index) is not None:
                return index
            else:
                pass
            child_index = self._first_visible_tree_entry_index(index)
            if child_index.isValid():
                return child_index
            else:
                pass
        return QtCore.QModelIndex()

    def _entry_from_tree_index(self, index: QtCore.QModelIndex) -> DynamicEditorEntry | None:
        """
        Resolve one visible tree index back to its dynamic-editor entry.

        :param index: Visible proxy-model index.
        :return: Backing entry or ``None``.
        """
        source_index = self._tree_proxy.mapToSource(index)
        if not source_index.isValid():
            return None
        else:
            pass
        data = self._tree_model.data(source_index, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(data, DynamicEditorEntry):
            return data
        else:
            pass
        return None

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

    def _on_tree_double_clicked(self, index: QtCore.QModelIndex) -> None:
        """
        Open the double-clicked tree entry in RMS mode.

        :param index: Double-clicked tree index.
        :return: None.
        """
        self._open_tree_entry(index, DynamicSimulationMode.RMS)

    def _show_tree_context_menu(self, position: QtCore.QPoint) -> None:
        """
        Show the RMS/EMT context menu for the tree entry under the cursor.

        :param position: Tree viewport position where the menu was requested.
        :return: None.
        """
        index = self.ui.treeView.indexAt(position)
        entry = self._entry_from_tree_index(index)
        if entry is None:
            return
        else:
            pass

        menu = QtWidgets.QMenu(self.ui.treeView)
        if DynamicSimulationMode.RMS in entry.available_modes:
            action = add_menu_entry(
                menu=menu,
                text=self.tr("Open RMS editor"),
                function_ptr=self._open_tree_rms_from_menu,
            )
            action.setData(QtCore.QPersistentModelIndex(index))
        else:
            pass
        if DynamicSimulationMode.EMT in entry.available_modes:
            action = add_menu_entry(
                menu=menu,
                text=self.tr("Open EMT editor"),
                function_ptr=self._open_tree_emt_from_menu,
            )
            action.setData(QtCore.QPersistentModelIndex(index))
        else:
            pass

        if menu.isEmpty():
            return
        else:
            pass

        menu.exec(self.ui.treeView.viewport().mapToGlobal(position))

    def _open_tree_rms_from_menu(self, _checked: bool = False) -> None:
        """
        Open the tree entry referenced by the sender action in RMS mode.

        :param _checked: QAction checked flag.
        :return: None.
        """
        index = self._tree_menu_index_from_sender()
        if index is not None:
            self._open_tree_entry(index, DynamicSimulationMode.RMS)
        else:
            pass

    def _open_tree_emt_from_menu(self, _checked: bool = False) -> None:
        """
        Open the tree entry referenced by the sender action in EMT mode.

        :param _checked: QAction checked flag.
        :return: None.
        """
        index = self._tree_menu_index_from_sender()
        if index is not None:
            self._open_tree_entry(index, DynamicSimulationMode.EMT)
        else:
            pass

    def _tree_menu_index_from_sender(self) -> QtCore.QModelIndex | None:
        """
        Return the tree index stored on the sender context-menu action.

        :return: Stored tree index or ``None``.
        """
        action = self.sender()
        if not isinstance(action, QtGui.QAction):
            return None
        else:
            pass
        data = action.data()
        if isinstance(data, QtCore.QPersistentModelIndex) and data.isValid():
            return QtCore.QModelIndex(data)
        else:
            pass
        return None

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
            page: DynamicBlockEditorGUI,
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

    def index_of_page(self, page: DynamicBlockEditorGUI) -> int:
        """
        Return the tab index for one page, or ``-1`` when absent.

        :param page: Page to locate.
        :return: Tab index or ``-1``.
        """
        return self.editor_tabs.indexOf(page)

    def page_at(self, index: int) -> DynamicBlockEditorGUI | DynamicEditorTab | None:
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
        if isinstance(page, (DynamicBlockEditorGUI, DynamicEditorTab)):
            return page
        else:
            return None

    def pages_iter(self) -> Iterator[DynamicBlockEditorGUI | DynamicEditorTab]:
        """Yield every valid editor page in tab order.

        :return: Iterator over the hosted dynamic editor pages.
        """
        for index in range(self.editor_tabs.count()):
            page = self.editor_tabs.widget(index)
            if isinstance(page, (DynamicBlockEditorGUI, DynamicEditorTab)):
                yield page
            else:
                pass

    def current_page(self) -> DynamicBlockEditorGUI | DynamicEditorTab | None:
        """
        Return the currently selected tab page.

        :return: Current page or ``None``.
        """
        return self.page_at(self.editor_tabs.currentIndex())

    def remove_page(self, page: DynamicBlockEditorGUI | DynamicEditorTab) -> None:
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

    def set_page_tab_title(self, page: QtWidgets.QWidget, title: str) -> None:
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

        if not bool(page.can_close_editor(self)):
            return
        else:
            pass

        # The workspace only hosts dynamic block editors, so teardown can call
        # the page lifecycle directly without reflective guards.
        page.prepare_to_delete()
        self.session.unregister_page(page)
        self.remove_page(page)
        page.setParent(None)
        page.deleteLater()

        if self.editor_tabs.count() == 0:
            self.close()
        else:
            pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Close the workspace window after checking every open page.

        :param event: Qt close event.
        :return: None.
        """
        for index in range(self.editor_tabs.count() - 1, -1, -1):
            page: DynamicBlockEditorGUI | DynamicEditorTab | None = self.page_at(index)
            if page is None:
                pass
            else:
                if not bool(page.can_close_editor(self)):
                    event.ignore()
                    return
                else:
                    pass

        self._accepts_new_pages = False
        pages = [self.page_at(index) for index in range(self.editor_tabs.count())]
        for page in pages:
            if page is None:
                pass
            else:
                page.prepare_to_delete()
                self.session.unregister_page(page)
                self.remove_page(page)
                page.setParent(None)
                page.deleteLater()

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
