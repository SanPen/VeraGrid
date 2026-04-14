# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, Any

from PySide6 import QtGui
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.multiverse import MultiVerse, ScenarioNode


class ScenarioTreeModel(QAbstractItemModel):
    __slots__ = (
        "_multiverse",
        "_headers",
    )

    def __init__(self, multiverse: MultiVerse, parent=None) -> None:
        """
        Qt tree model adapter for the MultiVerse hierarchy.

        :param multiverse: Scenario hierarchy container
        :param parent: Optional Qt parent
        """
        super().__init__(parent)
        self._multiverse: MultiVerse = multiverse
        self._headers: List[str] = [
            "Name",
            "Objects",
            "Comment"
        ]
        # Reuse existing application icons so root scenarios and child scenarios are
        # visually distinct in the tree without adding new GUI resources.
        self._root_icon = QtGui.QIcon()
        self._root_icon.addPixmap(QtGui.QPixmap(":/Icons/icons/schematic.png"))
        self._scenario_icon = QtGui.QIcon()
        self._scenario_icon.addPixmap(QtGui.QPixmap(":/Icons/icons/grid_icon.png"))

    @property
    def multiverse(self) -> MultiVerse:
        return self._multiverse

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Number of visible columns in the tree.

        :param parent: Parent model index
        :return: Number of columns
        """
        return len(self._headers)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Number of rows under a given parent.

        :param parent: Parent model index
        :return: Number of child rows
        """
        if parent.isValid():
            parent_node: ScenarioNode = parent.internalPointer()
            return parent_node.child_count()
        else:
            return len(self._multiverse.root_nodes)

    def index(
            self,
            row: int,
            column: int,
            parent: QModelIndex = QModelIndex(),
    ) -> QModelIndex:
        """
        Create a model index for the given row/column under parent.

        :param row: Row number
        :param column: Column number
        :param parent: Parent model index
        :return: QModelIndex
        """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if parent.isValid():
            parent_node: ScenarioNode = parent.internalPointer()
            child_node: ScenarioNode = parent_node.child(row)
        else:
            child_node = self._multiverse.root_nodes[row]

        return self.createIndex(row, column, child_node)

    def parent(self, index: QModelIndex) -> QModelIndex:
        """
        Get the Qt parent index of a given node index.

        :param index: Child index
        :return: Parent QModelIndex, or invalid index if root
        """
        if not index.isValid():
            return QModelIndex()

        node: ScenarioNode = index.internalPointer()
        parent_node: ScenarioNode | None = node.parent

        if parent_node is None:
            return QModelIndex()

        grand_parent: ScenarioNode | None = parent_node.parent

        if grand_parent is None:
            row: int = self._multiverse.root_nodes.index(parent_node)
        else:
            row = parent_node.row()

        return self.createIndex(row, 0, parent_node)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Provide the data to the view.

        :param index: Model index
        :param role: Qt item role
        :return: Data value for the requested role
        """
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            node: ScenarioNode = index.internalPointer()
            if node.parent is None:
                return self._root_icon
            return self._scenario_icon

        if role not in (Qt.ItemDataRole.DisplayRole,
                        Qt.ItemDataRole.EditRole):
            return None

        node: ScenarioNode = index.internalPointer()
        circuit: MultiCircuit = node.circuit
        column: int = index.column()

        if column == 0:
            return circuit.name
        if column == 1:
            return f"{circuit.get_all_elements_number()}"
        if column == 2:
            return circuit.comments

        return None

    def setData(
            self,
            index: QModelIndex,
            value: Any,
            role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        """
        Edit the underlying MultiCircuit data.

        :param index: Model index
        :param value: New value
        :param role: Qt item role
        :return: True if edited, False otherwise
        """
        if not index.isValid():
            return False

        if role != Qt.ItemDataRole.EditRole:
            return False

        node: ScenarioNode = index.internalPointer()
        circuit: MultiCircuit = node.circuit
        column: int = index.column()

        if column == 0:
            circuit.name = str(value)
        elif column == 1:
            return False
        elif column == 2:
            circuit.comments = str(value)
        else:
            return False

        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """
        Item capabilities.

        :param index: Model index
        :return: Qt item flags
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
        )

    def headerData(
            self,
            section: int,
            orientation: Qt.Orientation,
            role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """
        Horizontal header labels.

        :param section: Section number
        :param orientation: Orientation
        :param role: Qt item role
        :return: Header label
        """
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]

        return None

    def get_node(self, index: QModelIndex) -> ScenarioNode | None:
        """
        Convenience accessor.

        :param index: Model index
        :return: ScenarioNode or None if invalid
        """
        if index.isValid():
            return index.internalPointer()
        return None

    def index_for_node(self, node: ScenarioNode | None, column: int = 0) -> QModelIndex:
        """
        Build the QModelIndex that points to a specific scenario node.

        :param node: Scenario node to locate
        :param column: Target column
        :return: QModelIndex for the node, or invalid index if the node is not part of the model
        """
        if node is None:
            return QModelIndex()

        if node.parent is None:
            try:
                row = self._multiverse.root_nodes.index(node)
            except ValueError:
                return QModelIndex()
            return self.createIndex(row, column, node)

        # Recreate the parent index first so Qt receives a fully valid hierarchical index
        # for nodes that are not direct roots.
        parent_index = self.index_for_node(node.parent, 0)
        if not parent_index.isValid():
            return QModelIndex()

        return self.index(node.row(), column, parent_index)

    def refresh(self) -> None:
        """
        Full model reset after external structural changes.
        """
        self.beginResetModel()
        self.endResetModel()

    def refresh_data(self) -> None:
        """
        Refresh all cell data without resetting the model structure.
        Preserves tree expansion state and selection.
        Emit dataChanged for every node in the tree.
        """
        for node in self._multiverse.iter_nodes_depth_first():
            if node.parent is None:
                row: int = self._multiverse.root_nodes.index(node)
            else:
                row = node.row()
            top_left: QModelIndex = self.createIndex(row, 0, node)
            bottom_right: QModelIndex = self.createIndex(row, len(self._headers) - 1, node)
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])

    # -------------------------------------------------------------------------
    # CRUD wrappers synchronized with Qt model notifications
    # -------------------------------------------------------------------------
    def append_root(self, data: MultiCircuit) -> ScenarioNode:
        """
        Append a new root node.

        :param data: MultiCircuit to store
        :return: Created ScenarioNode
        """
        row: int = len(self._multiverse.root_nodes)
        self.beginInsertRows(QModelIndex(), row, row)
        node: ScenarioNode = self._multiverse.create_node(data=data, parent_id=None, position=row)
        self.endInsertRows()
        return node

    def append_child(self, parent_index: QModelIndex, data: MultiCircuit) -> ScenarioNode:
        """
        Append a child under the given parent index.

        :param parent_index: Parent QModelIndex
        :param data: MultiCircuit to store
        :return: Created ScenarioNode
        """
        if not parent_index.isValid():
            raise ValueError("Parent index must be valid")

        parent_node: ScenarioNode = parent_index.internalPointer()
        row: int = parent_node.child_count()

        self.beginInsertRows(parent_index, row, row)
        node: ScenarioNode = self._multiverse.create_node(
            data=data,
            parent_id=parent_node.node_id,
            position=row,
        )
        self.endInsertRows()
        return node

    def remove_node(self, index: QModelIndex) -> bool:
        """
        Remove one node and its subtree.

        :param index: QModelIndex to remove
        :return: True if removed
        """
        if not index.isValid():
            return False

        node: ScenarioNode = index.internalPointer()
        parent_node: ScenarioNode | None = node.parent

        if parent_node is None:
            parent_index: QModelIndex = QModelIndex()
            row: int = self._multiverse.root_nodes.index(node)
        else:
            parent_index = self.parent(index)
            row = node.row()

        self.beginRemoveRows(parent_index, row, row)
        self._multiverse.delete_node(node.node_id)
        self.endRemoveRows()
        return True

    def merge_children_into_parent(self, index: QModelIndex) -> bool:
        """
        Merge all direct children of the selected node into that node.

        A model reset is used because the operation can both remove nodes and
        reparent descendants in one step.

        :param index: Parent QModelIndex
        :return: True if the merge was applied
        """
        if not index.isValid():
            return False

        node: ScenarioNode = index.internalPointer()

        self.beginResetModel()
        self._multiverse.merge_children_into_parent(node.node_id)
        self.endResetModel()
        return True
