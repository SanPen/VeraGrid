# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import DynamicEditorEntry
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import entry_supports_dynamic_events
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import iter_dynamic_editor_entries
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DynamicEditorContentType, DynamicSimulationMode


def build_dynamic_device_entry_sort_key(entry: DynamicEditorEntry) -> tuple[str, str]:
    """Return the deterministic sorting key used by dynamic-device trees.

    :param entry: Dynamic device entry to sort.
    :return: Lowercase device-type and display-name tuple.
    """
    return entry.type_label.lower(), entry.display_name.lower()


class DynamicDeviceTreeWidget(QtWidgets.QWidget):
    """Searchable tree that opens model and event workspace pages."""

    entryPageRequested = QtCore.Signal(object, object, object)

    __slots__ = (
        "_circuit",
        "_preferred_double_click_mode",
        "_model",
        "_proxy",
        "search_line_edit",
        "tree_view",
    )

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Build the shared dynamic-device tree.

        :param parent: Optional owning widget.
        :return: None.
        """
        QtWidgets.QWidget.__init__(self, parent)
        self._circuit: MultiCircuit | None = None
        self._preferred_double_click_mode: DynamicSimulationMode = DynamicSimulationMode.RMS
        self._model: QtGui.QStandardItemModel = QtGui.QStandardItemModel(self)
        self._proxy: QtCore.QSortFilterProxyModel = QtCore.QSortFilterProxyModel(self)
        self._proxy.setRecursiveFilteringEnabled(True)
        self._proxy.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setSourceModel(self._model)

        # Build one self-contained panel so every consumer receives identical
        # search, filtering, selection and context-menu behavior.
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 0)
        self.search_line_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.search_line_edit.setClearButtonEnabled(True)
        self.search_line_edit.setPlaceholderText(self.tr("Type to search the device"))
        layout.addWidget(self.search_line_edit)

        self.tree_view: QtWidgets.QTreeView = QtWidgets.QTreeView(self)
        self.tree_view.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setModel(self._proxy)
        self.tree_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self.tree_view, 1)

        self.search_line_edit.textChanged.connect(self.apply_filter)
        self.tree_view.doubleClicked.connect(self._on_double_clicked)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)

    def set_circuit(self, circuit: MultiCircuit | None) -> None:
        """Bind the tree to a circuit and rebuild its entries.

        :param circuit: Circuit whose dynamic devices must be displayed.
        :return: None.
        """
        if self._circuit is circuit:
            return
        else:
            self._circuit = circuit
        self.rebuild()

    def set_preferred_double_click_mode(self, mode: DynamicSimulationMode) -> None:
        """Set the mode requested when a device is opened by double click.

        :param mode: RMS or EMT mode preferred by the calling workflow.
        :return: None.
        """
        self._preferred_double_click_mode = mode

    def rebuild(self) -> None:
        """Rebuild the grouped device tree from the bound circuit.

        :return: None.
        """
        self._model.clear()
        root_item: QtGui.QStandardItem = self._model.invisibleRootItem()
        if self._circuit is None:
            return
        else:
            pass

        group_labels: list[str] = list()
        group_items: list[QtGui.QStandardItem] = list()
        entries: list[DynamicEditorEntry] = sorted(
            iter_dynamic_editor_entries(self._circuit),
            key=build_dynamic_device_entry_sort_key,
        )

        # Reuse one group item for every equal type label without storing a
        # string-keyed dictionary; group counts are small and stable here.
        entry: DynamicEditorEntry
        for entry in entries:
            group_item: QtGui.QStandardItem | None = None
            group_index: int
            for group_index in range(len(group_labels)):
                if group_labels[group_index] == entry.type_label:
                    group_item = group_items[group_index]
                    break
                else:
                    pass

            if group_item is None:
                group_item = QtGui.QStandardItem(entry.type_label)
                group_item.setEditable(False)
                self._set_item_icon(group_item, entry.type_label)
                group_labels.append(entry.type_label)
                group_items.append(group_item)
                root_item.appendRow(group_item)
            else:
                pass

            device_item: QtGui.QStandardItem = QtGui.QStandardItem(entry.display_name)
            device_item.setEditable(False)
            device_item.setData(entry, QtCore.Qt.ItemDataRole.UserRole)
            device_item.setToolTip(entry.display_name)
            self._set_item_icon(device_item, entry.type_label)
            group_item.appendRow(device_item)

        self.apply_filter(self.search_line_edit.text())

    def _set_item_icon(self, item: QtGui.QStandardItem, icon_key: str) -> None:
        """Set the associated device icon on one tree item when available.

        :param item: Tree item receiving the icon.
        :param icon_key: Device-type key used by the icon association table.
        :return: None.
        """
        icon_path: str | None = device_type_icons.get(icon_key, None)
        if icon_path is None:
            return
        else:
            item.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_path)))

    @QtCore.Slot(str)
    def apply_filter(self, text: str) -> None:
        """Apply a case-insensitive recursive filter to the device tree.

        :param text: Search text entered by the user.
        :return: None.
        """
        needle: str = text.strip()
        if needle == "":
            self._proxy.setFilterRegularExpression(QtCore.QRegularExpression())
        else:
            expression: QtCore.QRegularExpression = QtCore.QRegularExpression(
                QtCore.QRegularExpression.escape(needle),
                QtCore.QRegularExpression.PatternOption.CaseInsensitiveOption,
            )
            self._proxy.setFilterRegularExpression(expression)

        # Expanded categories keep matching leaves visible and the first match
        # provides immediate keyboard navigation after every search update.
        self.tree_view.expandAll()
        first_index: QtCore.QModelIndex = self._first_visible_entry_index()
        if first_index.isValid():
            self.tree_view.setCurrentIndex(first_index)
            self.tree_view.scrollTo(first_index)
        else:
            pass

    def _first_visible_entry_index(
            self,
            parent: QtCore.QModelIndex = QtCore.QModelIndex(),
    ) -> QtCore.QModelIndex:
        """Return the first visible device entry below one proxy-model node.

        :param parent: Parent proxy index to search below.
        :return: First matching device index, or an invalid index.
        """
        row_count: int = self._proxy.rowCount(parent)
        row_index: int
        for row_index in range(row_count):
            index: QtCore.QModelIndex = self._proxy.index(row_index, 0, parent)
            if self.entry_from_index(index) is not None:
                return index
            else:
                child_index: QtCore.QModelIndex = self._first_visible_entry_index(index)
            if child_index.isValid():
                return child_index
            else:
                pass
        return QtCore.QModelIndex()

    def entry_from_index(self, index: QtCore.QModelIndex) -> DynamicEditorEntry | None:
        """Resolve one visible proxy index to its dynamic-device entry.

        :param index: Visible tree index.
        :return: Backing device entry, or ``None`` for category nodes.
        """
        source_index: QtCore.QModelIndex = self._proxy.mapToSource(index)
        if not source_index.isValid():
            return None
        else:
            pass
        data: object = self._model.data(source_index, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(data, DynamicEditorEntry):
            return data
        else:
            return None

    @QtCore.Slot(QtCore.QModelIndex)
    def _on_double_clicked(self, index: QtCore.QModelIndex) -> None:
        """Request the preferred mode for the double-clicked device.

        :param index: Double-clicked proxy-model index.
        :return: None.
        """
        entry: DynamicEditorEntry | None = self.entry_from_index(index)
        if entry is not None and self._preferred_double_click_mode in entry.available_modes:
            self.entryPageRequested.emit(
                entry,
                self._preferred_double_click_mode,
                DynamicEditorContentType.MODEL,
            )
        else:
            pass

    @QtCore.Slot(QtCore.QPoint)
    def _show_context_menu(self, position: QtCore.QPoint) -> None:
        """Show model and event actions supported by the clicked device.

        :param position: Tree viewport position requested by Qt.
        :return: None.
        """
        index: QtCore.QModelIndex = self.tree_view.indexAt(position)
        entry: DynamicEditorEntry | None = self.entry_from_index(index)
        if entry is None:
            return
        else:
            pass

        menu: QtWidgets.QMenu = QtWidgets.QMenu(parent=self.tree_view)
        if DynamicSimulationMode.RMS in entry.available_modes:
            rms_model_action: QtGui.QAction = gf.add_menu_entry(
                menu=menu,
                text=self.tr("RMS editor"),
                icon_path=":/Icons/icons/dyn.png",
                function_ptr=self._open_rms_model_from_action,
            )
            rms_model_action.setData(QtCore.QPersistentModelIndex(index))
        else:
            pass

        if DynamicSimulationMode.EMT in entry.available_modes:
            emt_model_action: QtGui.QAction = gf.add_menu_entry(
                menu=menu,
                text=self.tr("EMT editor"),
                icon_path=":/Icons/icons/dyn_emt.png",
                function_ptr=self._open_emt_model_from_action,
            )
            emt_model_action.setData(QtCore.QPersistentModelIndex(index))
        else:
            pass

        if entry_supports_dynamic_events(entry):
            menu.addSeparator()
            if DynamicSimulationMode.RMS in entry.available_modes:
                rms_events_action: QtGui.QAction = gf.add_menu_entry(
                    menu=menu,
                    text=self.tr("RMS events"),
                    icon_path=":/Icons/icons/dyn_edit.png",
                    function_ptr=self._open_rms_events_from_action,
                )
                rms_events_action.setData(QtCore.QPersistentModelIndex(index))
            else:
                pass

            if DynamicSimulationMode.EMT in entry.available_modes:
                emt_events_action: QtGui.QAction = gf.add_menu_entry(
                    menu=menu,
                    text=self.tr("EMT events"),
                    icon_path=":/Icons/icons/dyn_emt_edit.png",
                    function_ptr=self._open_emt_events_from_action,
                )
                emt_events_action.setData(QtCore.QPersistentModelIndex(index))
            else:
                pass
        else:
            pass

        if menu.isEmpty():
            return
        else:
            menu.exec(self.tree_view.viewport().mapToGlobal(position))

    @QtCore.Slot(bool)
    def _open_rms_model_from_action(self, _checked: bool = False) -> None:
        """Request the RMS model page for the context-menu device.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        self._emit_page_from_sender(DynamicSimulationMode.RMS, DynamicEditorContentType.MODEL)

    @QtCore.Slot(bool)
    def _open_emt_model_from_action(self, _checked: bool = False) -> None:
        """Request the EMT model page for the context-menu device.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        self._emit_page_from_sender(DynamicSimulationMode.EMT, DynamicEditorContentType.MODEL)

    @QtCore.Slot(bool)
    def _open_rms_events_from_action(self, _checked: bool = False) -> None:
        """Request the RMS events page for the context-menu device.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        self._emit_page_from_sender(DynamicSimulationMode.RMS, DynamicEditorContentType.EVENTS)

    @QtCore.Slot(bool)
    def _open_emt_events_from_action(self, _checked: bool = False) -> None:
        """Request the EMT events page for the context-menu device.

        :param _checked: QAction checked state supplied by Qt.
        :return: None.
        """
        self._emit_page_from_sender(DynamicSimulationMode.EMT, DynamicEditorContentType.EVENTS)

    def _emit_page_from_sender(self,
                               mode: DynamicSimulationMode,
                               content_type: DynamicEditorContentType) -> None:
        """Emit one page request using the persistent index on the sender action.

        :param mode: Requested RMS or EMT mode.
        :param content_type: Model or events content requested by the action.
        :return: None.
        """
        action: QtCore.QObject | None = self.sender()
        if not isinstance(action, QtGui.QAction):
            return
        else:
            pass
        data: object = action.data()
        if isinstance(data, QtCore.QPersistentModelIndex) and data.isValid():
            index: QtCore.QModelIndex = QtCore.QModelIndex(data)
            entry: DynamicEditorEntry | None = self.entry_from_index(index)
        else:
            entry = None
        content_is_supported: bool = (
            content_type == DynamicEditorContentType.MODEL
            or (content_type == DynamicEditorContentType.EVENTS and entry is not None
                and entry_supports_dynamic_events(entry))
        )
        if entry is not None and mode in entry.available_modes and content_is_supported:
            self.entryPageRequested.emit(entry, mode, content_type)
        else:
            pass
