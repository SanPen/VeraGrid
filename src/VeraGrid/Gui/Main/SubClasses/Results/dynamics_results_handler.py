# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Dict, List, Set, Tuple
import numpy as np
from matplotlib import pyplot as plt
from PySide6 import QtCore, QtGui

from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGrid.Gui.results_model import ResultsModel


def _build_tree_item(text: str) -> QtGui.QStandardItem:
    """
    Build a non-editable tree item.

    :param text: Text to display in the tree node.
    :return: Configured tree item.
    """
    # Every tree node is marked as read-only because the trees are used as selectors and drop targets.
    item: QtGui.QStandardItem = QtGui.QStandardItem(text)
    item.setEditable(False)
    return item


def _get_device_type_label(device_tpe: DeviceType) -> str:
    """
    Get the label that represents a device type.

    :param device_tpe: Device type enum value.
    :return: User-facing label for the device type node.
    """
    # The enum value is already the canonical label used across the GUI.
    return str(device_tpe.value)


def _get_device_label(device: ALL_DEV_TYPES) -> str:
    """
    Get the label that represents a device instance.

    :param device: Device instance stored in the RMS results tree.
    :return: User-facing label for the device node.
    """
    # Engine devices expose the correct GUI name through their string representation.
    return str(device)


def _get_var_label(variable: Var) -> str:
    """
    Get the label that represents a simulation variable.

    :param variable: RMS variable object.
    :return: User-facing label for the variable node.
    """
    # The symbolic variable name is the exact identifier used by the simulation arrays.
    return variable.name


def _set_item_icon(item: QtGui.QStandardItem, icon_key: str) -> None:
    """
    Set the item icon from the shared device-type icon dictionary.

    :param item: Tree item that should receive the icon.
    :param icon_key: Key used to search in ``device_type_icons``.
    :return: Nothing.
    """
    # The icon mapping is shared with the rest of the GUI so tree categories stay visually consistent.
    icon_path: str | None = device_type_icons.get(icon_key, None)
    if icon_path is not None:
        icon: QtGui.QIcon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path))
        item.setIcon(icon)
    else:
        pass


class DynamicsPlotGroup:
    """
    Group of variables to be plotted together.
    """

    __slots__ = ("_name", "_vars")

    def __init__(self, name: str):
        """
        Build the plot group.

        :param name: Name shown in the plots tree.
        """
        # The name is the external identifier used by the UI and CRUD operations.
        self._name: str = name

        # The variable list is kept ordered because users expect insertion order to be preserved in the plot tree.
        self._vars: List[Var] = list()

    def get_name(self) -> str:
        """
        Get the plot-group name.

        :return: Plot-group name.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """
        Set the plot-group name.

        :param name: New group name.
        :return: Nothing.
        """
        self._name = name

    def get_vars(self) -> List[Var]:
        """
        Get the variables stored in the group.

        :return: Variables in insertion order.
        """
        return list(self._vars)

    def contains_var(self, variable: Var) -> bool:
        """
        Check whether a variable already belongs to the group.

        :param variable: Variable to inspect.
        :return: ``True`` when the variable is already present.
        """
        contained: bool = False
        existing_var: Var
        for existing_var in self._vars:
            if existing_var.uid == variable.uid:
                contained = True
            else:
                pass
        return contained

    def add_var(self, variable: Var) -> bool:
        """
        Add a variable to the group.

        :param variable: Variable to add.
        :return: ``True`` when the variable was inserted.
        """
        # Duplicate insertions are rejected so drag-and-drop remains idempotent.
        if self.contains_var(variable=variable):
            return False
        else:
            self._vars.append(variable)
            return True

    def remove_var(self, variable: Var) -> bool:
        """
        Remove a variable from the group.

        :param variable: Variable to remove.
        :return: ``True`` when the variable was present and removed.
        """
        variable_idx: int = -1
        idx: int
        existing_var: Var
        for idx, existing_var in enumerate(self._vars):
            if existing_var.uid == variable.uid:
                variable_idx = idx
            else:
                pass

        if variable_idx >= 0:
            del self._vars[variable_idx]
            return True
        else:
            return False


class DynamicsPlotGroups:
    """
    Collection of plot groups with explicit CRUD operations.
    """

    __slots__ = ("_groups",)

    def __init__(self) -> None:
        """
        Build an empty plot-group collection.

        :return: Nothing.
        """
        self._groups: List[DynamicsPlotGroup] = list()

    def get_groups(self) -> List[DynamicsPlotGroup]:
        """
        Get the stored plot groups.

        :return: Copy of the plot-group list.
        """
        return list(self._groups)

    def get_group(self, name: str) -> DynamicsPlotGroup | None:
        """
        Get one plot group by name.

        :param name: Plot-group name.
        :return: Matching plot group or ``None``.
        """
        group: DynamicsPlotGroup
        for group in self._groups:
            if group.get_name() == name:
                return group
            else:
                pass
        return None

    def create_group(self, name: str) -> bool:
        """
        Create a new plot group.

        :param name: Requested group name.
        :return: ``True`` when the group was created.
        """
        clean_name: str = name.strip()
        if clean_name == "":
            return False
        else:
            existing_group: DynamicsPlotGroup | None = self.get_group(name=clean_name)
            if existing_group is None:
                self._groups.append(DynamicsPlotGroup(name=clean_name))
                return True
            else:
                return False

    def delete_group(self, name: str) -> bool:
        """
        Delete a plot group.

        :param name: Group name.
        :return: ``True`` when the group existed and was deleted.
        """
        group_idx: int = -1
        idx: int
        group: DynamicsPlotGroup
        for idx, group in enumerate(self._groups):
            if group.get_name() == name:
                group_idx = idx
            else:
                pass

        if group_idx >= 0:
            del self._groups[group_idx]
            return True
        else:
            return False

    def rename_group(self, old_name: str, new_name: str) -> bool:
        """
        Rename an existing group.

        :param old_name: Current group name.
        :param new_name: Requested group name.
        :return: ``True`` when the rename was applied.
        """
        clean_name: str = new_name.strip()
        if clean_name == "":
            return False
        else:
            target_group: DynamicsPlotGroup | None = self.get_group(name=old_name)
            clashing_group: DynamicsPlotGroup | None = self.get_group(name=clean_name)
            if target_group is not None:
                if clashing_group is None or clean_name == old_name:
                    target_group.set_name(name=clean_name)
                    return True
                else:
                    return False
            else:
                return False


class DynamicsDeviceTreeModel(QtGui.QStandardItemModel):
    """
    Source tree model that exports dragged variables.
    """

    __slots__ = ("_var_role", "_mime_type")

    def __init__(self, var_role: int, mime_type: str):
        """
        Build the source dynamics tree model.

        :param var_role: Qt role that stores the ``Var`` object in leaf nodes.
        :param mime_type: Mime type used during drag-and-drop.
        """
        QtGui.QStandardItemModel.__init__(self)
        self._var_role: int = var_role
        self._mime_type: str = mime_type

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Get the Qt flags for an item.

        :param index: Model index.
        :return: Flags controlling selection and dragging.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self._var_role)
                if isinstance(item_data, Var):
                    return (QtCore.Qt.ItemFlag.ItemIsEnabled
                            | QtCore.Qt.ItemFlag.ItemIsSelectable
                            | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
                else:
                    return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
            else:
                return QtCore.Qt.ItemFlag.ItemIsEnabled
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled

    def mimeTypes(self) -> List[str]:
        """
        Get the supported mime types.

        :return: Mime types exported by the model.
        """
        return [self._mime_type]

    def supportedDragActions(self) -> QtCore.Qt.DropAction:
        """
        Get the supported drag actions.

        :return: Copy action.
        """
        return QtCore.Qt.DropAction.CopyAction

    def mimeData(self, indexes: List[QtCore.QModelIndex]) -> QtCore.QMimeData:
        """
        Build mime data from the selected variable item.

        :param indexes: Selected indexes.
        :return: Mime payload containing the dragged variable uid.
        """
        mime_data: QtCore.QMimeData = QtCore.QMimeData()

        index: QtCore.QModelIndex
        for index in indexes:
            if index.isValid():
                item: QtGui.QStandardItem | None = self.itemFromIndex(index)
                if item is not None:
                    item_data: object = item.data(self._var_role)
                    if isinstance(item_data, Var):
                        mime_data.setData(self._mime_type, QtCore.QByteArray(str(item_data.uid).encode("utf-8")))
                        return mime_data
                    else:
                        pass
                else:
                    pass
            else:
                pass

        return mime_data


class DynamicsPlotsTreeModel(QtGui.QStandardItemModel):
    """
    Target tree model that accepts dropped variables into plot groups.
    """

    __slots__ = ("_handler",)

    def __init__(self, handler: "DynamicsResultsHandler"):
        """
        Build the plots tree model.

        :param handler: Dynamics-results handler that owns the plot-group state.
        """
        QtGui.QStandardItemModel.__init__(self)
        self._handler: DynamicsResultsHandler = handler

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Get the Qt flags for a plots-tree item.

        :param index: Model index.
        :return: Flags controlling selection and drop acceptance.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.itemFromIndex(index)
            if item is not None:
                group_name_data: object = item.data(self._handler.get_group_name_role())
                if isinstance(group_name_data, str):
                    return (QtCore.Qt.ItemFlag.ItemIsEnabled
                            | QtCore.Qt.ItemFlag.ItemIsSelectable
                            | QtCore.Qt.ItemFlag.ItemIsDropEnabled)
                else:
                    return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
            else:
                return QtCore.Qt.ItemFlag.ItemIsEnabled
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled

    def mimeTypes(self) -> List[str]:
        """
        Get the supported mime types.

        :return: Mime type accepted by the target model.
        """
        return [self._handler.get_drag_mime_type()]

    def supportedDropActions(self) -> QtCore.Qt.DropAction:
        """
        Get the supported drop actions.

        :return: Copy action.
        """
        return QtCore.Qt.DropAction.CopyAction

    def dropMimeData(self,
                     data: QtCore.QMimeData,
                     action: QtCore.Qt.DropAction,
                     row: int,
                     column: int,
                     parent: QtCore.QModelIndex) -> bool:
        """
        Handle dropping one variable into a plot group.

        :param data: Drag payload.
        :param action: Requested drop action.
        :param row: Drop row.
        :param column: Drop column.
        :param parent: Drop parent index.
        :return: ``True`` when the drop was accepted.
        """
        del row
        del column

        if action == QtCore.Qt.DropAction.IgnoreAction:
            return True
        else:
            if data.hasFormat(self._handler.get_drag_mime_type()):
                payload: bytes = bytes(data.data(self._handler.get_drag_mime_type()))
                payload_text: str = payload.decode("utf-8").strip()
                if payload_text.isdigit():
                    var_uid: int = int(payload_text)
                    group_name: str | None = self._handler.get_group_name_from_drop_index(index=parent)
                    if group_name is not None:
                        return self._handler.add_var_to_group(group_name=group_name, var_uid=var_uid)
                    else:
                        return False
                else:
                    return False
            else:
                return False


def build_dynamics_tree_model(tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]],
                              var_role: int,
                              mime_type: str) -> DynamicsDeviceTreeModel:
    """
    Build the source tree-view model for RMS/EMT dynamics results.

    :param tree_data: Hierarchical RMS results tree grouped by device type and device.
    :param var_role: Qt item-data role used to store the ``Var`` instance in leaf nodes.
    :param mime_type: Mime type exported when dragging a variable.
    :return: Source tree model ready to be assigned to a QTreeView.
    """
    # The source model owns the full device hierarchy and the drag payload for variable leaves.
    model: DynamicsDeviceTreeModel = DynamicsDeviceTreeModel(var_role=var_role, mime_type=mime_type)
    model.setHorizontalHeaderLabels(["Dynamics results"])

    # The invisible root is Qt's insertion point for first-level tree nodes.
    root_item: QtGui.QStandardItem = model.invisibleRootItem()

    device_tpe: DeviceType
    devices_data: Dict[ALL_DEV_TYPES, List[Var]]
    for device_tpe, devices_data in tree_data.items():
        # The first level groups all devices by their type so the tree remains navigable.
        device_type_item: QtGui.QStandardItem = _build_tree_item(text=_get_device_type_label(device_tpe=device_tpe))
        _set_item_icon(item=device_type_item, icon_key=_get_device_type_label(device_tpe=device_tpe))
        root_item.appendRow(device_type_item)

        device: ALL_DEV_TYPES
        variables: List[Var]
        for device, variables in devices_data.items():
            # The second level groups the variables that belong to one physical device.
            device_item: QtGui.QStandardItem = _build_tree_item(text=_get_device_label(device=device))
            device_type_item.appendRow(device_item)

            variable: Var
            for variable in variables:
                # Variable nodes are leaves and store the actual Var object for clicks and drag exports.
                variable_item: QtGui.QStandardItem = _build_tree_item(text=_get_var_label(variable=variable))
                variable_item.setData(variable, var_role)
                device_item.appendRow(variable_item)

    return model


class DynamicsResultsHandler:
    """
    Prepare GUI structures from RMS/EMT dynamics results.
    """

    __slots__ = ("results", "tree_data", "tree_model", "proxy_model", "plots_model", "group_idx",
                 "var_role", "group_name_role", "drag_mime_type", "plot_groups")

    def __init__(self, results: RmsResults|EmtResults):
        """
        Build the handler from RMS/EMT results data.

        :param results: RMS/EMT results container coming from the simulation engine.
        """
        # The original results object is preserved because later GUI actions need arrays and metadata.
        self.results: RmsResults|EmtResults = results

        # These roles are instance-owned so the handler carries all Qt metadata instead of relying on globals.
        self.var_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 300
        self.group_name_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 301
        self.drag_mime_type: str = "application/x-veragrid-dynamics-var"

        # Group-name to RMS/EMT-group-index mapping is precomputed because plotting needs constant-time access.
        self.group_idx: Dict[str, int] = self._build_group_idx(results=self.results)

        # The hierarchical dictionary is the canonical source used to build the device tree.
        self.tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]] = self.results.get_devices_dict_tree()

        # The device tree model is the source tree for the left-hand dynamics browser.
        self.tree_model: DynamicsDeviceTreeModel|None = build_dynamics_tree_model(tree_data=self.tree_data,
                                                                                  var_role=self.var_role,
                                                                                  mime_type=self.drag_mime_type)

        # The proxy model owns the reversible filtering state used by the device tree view.
        self.proxy_model: QtCore.QSortFilterProxyModel = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.tree_model)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)
        if hasattr(self.proxy_model, "setAutoAcceptChildRows"):
            self.proxy_model.setAutoAcceptChildRows(True)
        else:
            pass

        # Plot groups are stored separately from Qt so CRUD operations are explicit and testable.
        self.plot_groups: DynamicsPlotGroups = DynamicsPlotGroups()

        # The plots model is rebuilt from the domain objects after every CRUD operation.
        self.plots_model: DynamicsPlotsTreeModel = DynamicsPlotsTreeModel(handler=self)
        self.rebuild_plots_model()

    def get_group_name_role(self) -> int:
        """
        Get the Qt role used to store plot-group names in the plots tree.

        :return: Item-data role for plot-group names.
        """
        return self.group_name_role

    def get_drag_mime_type(self) -> str:
        """
        Get the mime type used for dynamics-variable drag-and-drop.

        :return: Mime type string.
        """
        return self.drag_mime_type

    def get_view_model(self) -> QtCore.QSortFilterProxyModel:
        """
        Get the proxy model used by the dynamics device tree view.

        :return: Filter proxy model wrapping the source dynamics tree.
        """
        return self.proxy_model

    def get_plots_model(self) -> DynamicsPlotsTreeModel:
        """
        Get the model used by the dynamics plots tree view.

        :return: Plot-groups tree model.
        """
        return self.plots_model

    def set_search_text(self, search_text: str) -> None:
        """
        Update the proxy-model filter with the given search text.

        :param search_text: Text used to filter the device tree nodes.
        :return: Nothing.
        """
        # Escaping the text keeps the search literal and avoids accidental regular-expression semantics.
        escaped_text: str = QtCore.QRegularExpression.escape(search_text.strip())
        regex: QtCore.QRegularExpression = QtCore.QRegularExpression(escaped_text)
        regex.setPatternOptions(QtCore.QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy_model.setFilterRegularExpression(regex)

    def map_to_source(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """
        Map a view index from the proxy model back to the source device-tree model.

        :param index: Index received from the tree-view signal.
        :return: Source-model index understood by the handler internals.
        """
        return self.proxy_model.mapToSource(index)

    def get_var_from_index(self, index: QtCore.QModelIndex) -> Var | None:
        """
        Get the RMS variable associated with a clicked device-tree index.

        :param index: Source-model index coming from the dynamics device tree.
        :return: Variable stored in the clicked leaf node, or ``None`` for non-variable nodes.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.tree_model.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self.var_role)
                if isinstance(item_data, Var):
                    return item_data
                else:
                    return None
            else:
                return None
        else:
            return None

    def get_plot_group_name_from_index(self, index: QtCore.QModelIndex) -> str | None:
        """
        Get the plot-group name represented by a plots-tree index.
        :param index: Index from the plots tree.
        :return: Group name, or ``None`` when the index does not belong to any group.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.plots_model.itemFromIndex(index)
            if item is not None:
                group_name_data: object = item.data(self.group_name_role)
                if isinstance(group_name_data, str):
                    return group_name_data
                else:
                    parent_item: QtGui.QStandardItem | None = item.parent()
                    if parent_item is not None:
                        parent_group_name_data: object = parent_item.data(self.group_name_role)
                        if isinstance(parent_group_name_data, str):
                            return parent_group_name_data
                        else:
                            return None
                    else:
                        return None
            else:
                return None
        else:
            return None

    def get_group_name_from_drop_index(self, index: QtCore.QModelIndex) -> str | None:
        """
        Resolve the plot-group name targeted by a drop operation.

        :param index: Drop target index.
        :return: Group name, or ``None`` when the drop target is invalid.
        """
        return self.get_plot_group_name_from_index(index=index)

    def get_plot_var_from_index(self, index: QtCore.QModelIndex) -> Var | None:
        """
        Get the variable represented by a plots-tree index.

        :param index: Index from the plots tree.
        :return: Variable when the index points to a variable child, otherwise ``None``.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.plots_model.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self.var_role)
                if isinstance(item_data, Var):
                    return item_data
                else:
                    return None
            else:
                return None
        else:
            return None

    def rebuild_plots_model(self) -> None:
        """
        Rebuild the plots-tree model from the plot-group domain objects.

        :return: Nothing.
        """
        # The Qt model is treated as a projection of the handler state so every CRUD operation remains explicit.
        self.plots_model.clear()
        self.plots_model.setHorizontalHeaderLabels(["Dynamic plots"])

        root_item: QtGui.QStandardItem = self.plots_model.invisibleRootItem()
        group: DynamicsPlotGroup
        for group in self.plot_groups.get_groups():
            group_item: QtGui.QStandardItem = _build_tree_item(text=group.get_name())
            group_item.setData(group.get_name(), self.group_name_role)
            _set_item_icon(item=group_item, icon_key="Dynamic")
            root_item.appendRow(group_item)

            variable: Var
            for variable in group.get_vars():
                variable_item: QtGui.QStandardItem = _build_tree_item(text=_get_var_label(variable=variable))
                variable_item.setData(variable, self.var_role)
                group_item.appendRow(variable_item)

    def _build_next_group_name(self) -> str:
        """
        Build the next default plot-group name.

        :return: New plot-group name that does not clash with existing ones.
        """
        group_number: int = 1
        while self.plot_groups.get_group(name="Plot " + str(group_number)) is not None:
            group_number += 1
        return "Plot " + str(group_number)

    def get_next_group_name(self) -> str:
        """
        Get the next available default plot-group name.

        :return: Suggested group name.
        """
        return self._build_next_group_name()

    def create_plot_group(self, name: str) -> bool:
        """
        Create a plot group and refresh the plots tree.

        :param name: Requested plot-group name.
        :return: ``True`` when the group was created.
        """
        created: bool = self.plot_groups.create_group(name=name)
        if created:
            self.rebuild_plots_model()
            return True
        else:
            return False

    def delete_plot_group(self, group_name: str) -> bool:
        """
        Delete one plot group and refresh the plots tree.

        :param group_name: Plot-group name.
        :return: ``True`` when the group existed and was deleted.
        """
        deleted: bool = self.plot_groups.delete_group(name=group_name)
        if deleted:
            self.rebuild_plots_model()
            return True
        else:
            return False

    def add_var_to_group(self, group_name: str, var_uid: int) -> bool:
        """
        Add one variable to a plot group and refresh the plots tree.

        :param group_name: Target plot-group name.
        :param var_uid: Variable uid obtained from the drag payload.
        :return: ``True`` when the variable was inserted.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        variable: Var | None = self.results.get_var(uid=var_uid)
        if group is not None:
            if variable is not None:
                inserted: bool = group.add_var(variable=variable)
                if inserted:
                    self.rebuild_plots_model()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def remove_var_from_group(self, group_name: str, var_uid: int) -> bool:
        """
        Remove one variable from a plot group and refresh the plots tree.

        :param group_name: Plot-group name.
        :param var_uid: Variable uid.
        :return: ``True`` when the variable was removed.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        variable: Var | None = self.results.get_var(uid=var_uid)
        if group is not None:
            if variable is not None:
                removed: bool = group.remove_var(variable=variable)
                if removed:
                    self.rebuild_plots_model()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def delete_plot_entry_from_index(self, index: QtCore.QModelIndex) -> bool:
        """
        Delete the selected group or variable from the plots tree.

        :param index: Selected plots-tree index.
        :return: ``True`` when something was deleted.
        """
        selected_var: Var | None = self.get_plot_var_from_index(index=index)
        if selected_var is not None:
            group_name: str | None = self.get_plot_group_name_from_index(index=index)
            if group_name is not None:
                return self.remove_var_from_group(group_name=group_name, var_uid=selected_var.uid)
            else:
                return False
        else:
            group_name = self.get_plot_group_name_from_index(index=index)
            if group_name is not None:
                return self.delete_plot_group(group_name=group_name)
            else:
                return False

    def plot_var(self, var: Var, group_name: str) -> None:
        """
        Plot one variable for one RMS events group.

        :param var: Variable to plot.
        :param group_name: RMS events group name.
        :return: Nothing.
        """
        gr_idx: int = self.group_idx[group_name]
        self.results.plot_var(var=var, group_idx=gr_idx)

    def plot_group(self, plot_group_name: str, dyn_group_name: str) -> bool:
        """
        Plot all variables stored in one plot group.

        :param plot_group_name: Plot-group name selected by the user.
        :param dyn_group_name: RMS/EMT events group name selected in the combobox.
        :return: ``True`` when the plot group existed and was plotted.
        """
        plot_group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=plot_group_name)
        if plot_group is not None:
            variables: List[Var] = plot_group.get_vars()
            if len(variables) > 0:
                group_idx: int = self.group_idx[dyn_group_name]
                figure = plt.figure(figsize=(12, 8))
                axis = figure.add_subplot(111)

                variable: Var
                for variable in variables:
                    values_idx: int = self.results.uid2idx[variable.uid]
                    y_values = self.results.values[:, values_idx, group_idx]
                    axis.plot(self.results.time_array, y_values, label=variable.name)

                axis.legend()
                axis.set_title(plot_group_name + " - " + dyn_group_name)
                plt.show()
                return True
            else:
                return False
        else:
            return False



    def plot_entry_from_index(self, index: QtCore.QModelIndex, dyn_group_name: str) -> bool:
        """
        Plot the selected plots-tree entry.

        :param index: Selected plots-tree index.
        :param dyn_group_name: Selected RMS/EMT events group name.
        :return: ``True`` when something was plotted.
        """
        selected_var: Var | None = self.get_plot_var_from_index(index=index)
        if selected_var is not None:
            self.plot_var(var=selected_var, group_name=dyn_group_name)
            return True
        else:
            plot_group_name: str | None = self.get_plot_group_name_from_index(index=index)
            if plot_group_name is not None:
                return self.plot_group(plot_group_name=plot_group_name, dyn_group_name=dyn_group_name)
            else:
                return False


    def get_data_from_plot_index(self, index: QtCore.QModelIndex, dyn_group_name: str) -> ResultsModel | None:
        """

        :param index:
        :param dyn_group_name:
        :return:
        """
        plot_group_name: str | None = self.get_plot_group_name_from_index(index=index)

        if plot_group_name is not None:

            plot_group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=plot_group_name)
            variables: List[Var] = plot_group.get_vars()
            if len(variables) > 0:
                group_idx: int = self.group_idx[dyn_group_name]
                data = self.results.get_vars_data(var_list=variables, group_idx=group_idx)

                var_names = np.array([v.name for v in variables])

                table = ResultsTable(
                    data=data,
                    index=self.results.time_array,
                    columns=var_names,
                    title=plot_group_name,
                    ylabel="",
                    cols_device_type=DeviceType.NoDevice,
                    idx_device_type=DeviceType.NoDevice
                )

                mdl = ResultsModel(table=table)

                return mdl
            else:
                return None
        else:
            return None

    def _build_group_idx(self, results: RmsResults | EmtResults) -> Dict[str, int]:
        """
        Build the event-group-name to index mapping for the given results object.
        """
        if type(results) == RmsResults:
            return {str(gr): i for i, gr in enumerate(results.rms_events_group_names)}
        elif type(results) == EmtResults:
            return {str(gr): i for i, gr in enumerate(results.emt_events_group_names)}
        else:
            raise Exception("Unsupported dynamics results type")

    # def _snapshot_plot_groups(self) -> List[tuple[str, List[int]]]:
    #     """
    #     Snapshot current plot groups using variable uid references.
    #
    #     :return: List of tuples (group_name, [var_uid_1, var_uid_2, ...]).
    #     """
    #     snapshot: List[tuple[str, List[int]]] = list()
    #
    #     group: DynamicsPlotGroup
    #     for group in self.plot_groups.get_groups():
    #         var_uids: List[int] = [var.uid for var in group.get_vars()]
    #         snapshot.append((group.get_name(), var_uids))
    #
    #     return snapshot

    def _snapshot_plot_groups(self) -> List[tuple[str, List[tuple[str, str, str]]]]:
        """
        Snapshot current plot groups using stable device-variable references.

        The ``Var.uid`` value can change when a new RMS/EMT simulation is executed.
        Therefore, dynamic plot definitions must be stored using a stable semantic
        reference. The stored signature uses ``(device.idtag, device.name,
        variable.name)`` so repeated runs of the same study can reconnect to the
        same device while still refusing to restore a variable if the device name
        changes.

        :return: List of tuples ``(group_name, [(device_idtag, device_name, variable_name), ...])``.
        """
        # Build a lookup from the current result tree before taking the snapshot.
        # This connects each plotted Var uid to the device that owns that variable.
        variable_signature_by_uid: Dict[int, tuple[str, str, str]] = self._build_uid_to_variable_signature_index()

        # The snapshot stores plot group names and stable variable signatures.
        # It deliberately avoids using Var.uid because uid is not stable across simulations.
        snapshot: List[tuple[str, List[tuple[str, str, str]]]] = list()

        group: DynamicsPlotGroup
        for group in self.plot_groups.get_groups():
            # The variable list is kept ordered so that the restored plot preserves
            # the same visual ordering selected by the user.
            var_signatures: List[tuple[str, str, str]] = list()

            variable: Var
            for variable in group.get_vars():
                var_signature: tuple[str, str, str] | None = variable_signature_by_uid.get(variable.uid, None)

                if var_signature is not None:
                    # Store only variables that can be linked to a device in the current tree.
                    var_signatures.append(var_signature)
                else:
                    # A variable without a device-tree owner cannot be restored safely.
                    # It is skipped instead of storing an unstable uid.
                    pass

            snapshot.append((group.get_name(), var_signatures))

        return snapshot

    # def _restore_plot_groups_from_snapshot(self, snapshot: List[tuple[str, List[int]]]) -> None:
    #     """
    #     Restore plot groups from a uid snapshot using the current results object.
    #
    #     :param snapshot: Plot-group snapshot created with _snapshot_plot_groups().
    #     :return: Nothing.
    #     """
    #     restored_plot_groups = DynamicsPlotGroups()
    #
    #     group_name: str
    #     var_uids: List[int]
    #     for group_name, var_uids in snapshot:
    #         created: bool = restored_plot_groups.create_group(name=group_name)
    #         if created:
    #             group: DynamicsPlotGroup | None = restored_plot_groups.get_group(name=group_name)
    #             if group is not None:
    #                 var_uid: int
    #                 for var_uid in var_uids:
    #                     variable: Var | None = self.results.get_var(uid=var_uid)
    #                     if variable is not None:
    #                         group.add_var(variable=variable)
    #
    #     self.plot_groups = restored_plot_groups

    def _restore_plot_groups_from_snapshot(self,
                                           snapshot: List[tuple[str, List[tuple[str, str, str]]]]) -> None:
        """
        Restore plot groups from stable device-variable references.

        A stored variable is restored only if the new results object contains the same
        device idtag, the same device name, and the same variable name. If either the
        device name or the variable name changes, that variable is omitted from the
        restored dynamic plot. This allows repeated simulations to preserve compatible
        plots while discarding only the obsolete plotted variables.

        :param snapshot: Plot-group snapshot created with ``_snapshot_plot_groups()``.
        :return: Nothing.
        """
        # Build a lookup from the new result tree after self.results has been replaced.
        # This maps stable references back to the current Var objects with current uids.
        variable_by_signature: Dict[tuple[str, str, str], Var] = self._build_variable_signature_to_var_index()

        # A duplicate visible signature means the same ``device.name`` and ``var.name``
        # appears more than once in the new results tree. Those entries are skipped on
        # restore because the GUI's minimum semantic identity is ambiguous, and binding
        # a plot to any one of the duplicates would risk reconnecting it to the wrong device.
        ambiguous_visible_signatures: Set[tuple[str, str]] = self._build_ambiguous_visible_variable_signatures()

        # Build a new plot-group collection so restoration is explicit and does not
        # mutate the old collection while it is being translated to the new results.
        restored_plot_groups: DynamicsPlotGroups = DynamicsPlotGroups()

        group_name: str
        var_signatures: List[tuple[str, str, str]]
        for group_name, var_signatures in snapshot:
            # Preserve the group even if all its variables disappear. This keeps the
            # user's plot structure visible and makes missing variables evident.
            created: bool = restored_plot_groups.create_group(name=group_name)

            if created:
                group: DynamicsPlotGroup | None = restored_plot_groups.get_group(name=group_name)

                if group is not None:
                    var_signature: tuple[str, str, str]
                    for var_signature in var_signatures:
                        visible_signature: tuple[str, str] = (var_signature[1], var_signature[2])

                        variable: Var | None
                        if visible_signature in ambiguous_visible_signatures:
                            # Ambiguous visible signatures are not restored even if the
                            # stored device idtag still matches one candidate. Skipping is
                            # safer than silently rebinding the plot under duplicate names.
                            variable = None
                        else:
                            # A missing full signature means the device idtag changed,
                            # the device name changed, the variable name changed, or the
                            # variable no longer exists in the new results object.
                            variable = variable_by_signature.get(var_signature, None)

                        if variable is not None:
                            # Add the current Var object from the new results object.
                            # This updates the uid used later by plotting and tables.
                            group.add_var(variable=variable)
                        else:
                            # The requested behaviour is to remove incompatible variables
                            # from the dynamic plot instead of rejecting the whole plot.
                            pass
                else:
                    # This state should not occur after a successful create_group(),
                    # but it is handled explicitly to keep all code paths evident.
                    pass
            else:
                # Duplicate or empty group names cannot be restored safely.
                # The original create_group() validation decides this case.
                pass

        self.plot_groups = restored_plot_groups

    def _build_uid_to_variable_signature_index(self) -> Dict[int, tuple[str, str, str]]:
        """
        Build a lookup table from current variable uid to stable device-variable signature.

        The result tree already stores the relationship between devices and variables.
        This method converts that tree into a lookup that can translate the existing
        plot variables from ``Var.uid`` to ``(device.idtag, device.name, variable.name)``.

        :return: Dictionary mapping ``Var.uid`` to ``(device_idtag, device_name, variable_name)``.
        """
        # The dictionary is used only as a lookup table. This is acceptable here
        # because the algorithm needs direct access from uid to the stable signature.
        signature_by_uid: Dict[int, tuple[str, str, str]] = dict()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, List[Var]]
        for device_tpe, devices_data in self.tree_data.items():
            # The device type is not part of the requested matching rule.
            # It is still iterated because the result tree is grouped by device type.
            del device_tpe

            device: ALL_DEV_TYPES
            variables: List[Var]
            for device, variables in devices_data.items():
                # The results tree already exposes device idtag and device name.
                # Storing both keeps the match stable across repeated simulations and
                # also prevents restoring a plot if the device is later renamed.
                device_idtag: str = str(device.idtag)
                device_name: str = str(device.name)

                variable: Var
                for variable in variables:
                    # The stable plot identity requires the same device idtag, the
                    # same device name, and the same variable name in the new results.
                    signature_by_uid[variable.uid] = (device_idtag, device_name, variable.name)

        return signature_by_uid

    def _build_variable_signature_to_var_index(self) -> Dict[tuple[str, str, str], Var]:
        """
        Build a lookup table from stable device-variable signature to current variable.

        This method is used after a new results object has been installed in the handler.
        It maps ``(device.idtag, device.name, variable.name)`` to the new ``Var`` object
        so restored plots use the current simulation's variable uid.

        :return: Dictionary mapping ``(device_idtag, device_name, variable_name)`` to ``Var``.
        """
        # The dictionary is used only as a lookup table. It avoids nested searches
        # during plot restoration and keeps the restoration logic explicit.
        variable_by_signature: Dict[tuple[str, str, str], Var] = dict()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, List[Var]]
        for device_tpe, devices_data in self.tree_data.items():
            # The matching rule requested by the user does not include DeviceType.
            # Therefore, the device type is intentionally ignored.
            del device_tpe

            device: ALL_DEV_TYPES
            variables: List[Var]
            for device, variables in devices_data.items():
                # Direct access to idtag and name is used because dynamic-result
                # devices inherit those fields from the engine's editable-device base.
                device_idtag: str = str(device.idtag)
                device_name: str = str(device.name)

                variable: Var
                for variable in variables:
                    # The full signature lookup stays deterministic because the same
                    # device idtag and variable name should resolve to one current Var.
                    variable_by_signature[(device_idtag, device_name, variable.name)] = variable

        return variable_by_signature

    def _build_ambiguous_visible_variable_signatures(self) -> Set[tuple[str, str]]:
        """
        Detect duplicate visible ``(device.name, variable.name)`` signatures.

        The GUI groups variables by device label and variable label, so duplicate
        visible signatures are ambiguous for cross-run restoration. They are skipped
        instead of being rebound to one arbitrary candidate.

        :return: Set of ambiguous ``(device_name, variable_name)`` signatures.
        """
        unique_signatures: Set[tuple[str, str]] = set()
        ambiguous_signatures: Set[tuple[str, str]] = set()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, List[Var]]
        for device_tpe, devices_data in self.tree_data.items():
            # DeviceType is not part of the requested visible identity, so it is
            # ignored while scanning for duplicate device-name and variable-name pairs.
            del device_tpe

            device: ALL_DEV_TYPES
            variables: List[Var]
            for device, variables in devices_data.items():
                device_name: str = str(device.name)

                variable: Var
                for variable in variables:
                    visible_signature: tuple[str, str] = (device_name, variable.name)

                    if visible_signature in unique_signatures:
                        ambiguous_signatures.add(visible_signature)
                    else:
                        unique_signatures.add(visible_signature)

        return ambiguous_signatures

    def update_results(self, results: RmsResults | EmtResults) -> None:
        """
        Replace the underlying results object while preserving dynamic-plot definitions.

        This method assumes that vars, diff_vars and params are compatible with the
        current handler. Compatibility must be checked before calling it.

        :param results: New RMS/EMT results for the same study type.
        :return: Nothing.
        """
        plot_groups_snapshot: List[tuple[str, List[tuple[str, str, str]]]] = self._snapshot_plot_groups()

        # The snapshot must be taken before swapping ``self.results`` so the plotted
        # Vars are still resolved against the old device tree that created them.

        self.results = results
        self.group_idx = self._build_group_idx(results=self.results)

        # The new tree must be rebuilt before restoration so stored signatures are
        # matched against the fresh RMS/EMT results object rather than stale tree data.
        self.tree_data = self.results.get_devices_dict_tree()
        self.tree_model = build_dynamics_tree_model(
            tree_data=self.tree_data,
            var_role=self.var_role,
            mime_type=self.drag_mime_type
        )
        self.proxy_model.setSourceModel(self.tree_model)

        self._restore_plot_groups_from_snapshot(snapshot=plot_groups_snapshot)
        self.rebuild_plots_model()

    def _var_signature(self, var: Var) -> str:
        """
        Build a stable comparison signature for one variable.

        :param var: Variable object.
        :return: Tuple used to compare variables across result objects.
        """
        return str(var.name)

    def _vars_signature(self, variables: List[Var]) -> List[str]:
        """
        Build comparison signatures for a list of variables.

        :param variables: Variable list.
        :return: List of signatures preserving order.
        """
        return [self._var_signature(var=v) for v in variables]
