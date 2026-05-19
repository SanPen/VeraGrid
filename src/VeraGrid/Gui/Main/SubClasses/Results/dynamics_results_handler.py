# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import json
from typing import Dict, List, Sequence, Set
import numpy as np
from matplotlib import pyplot as plt
from PySide6 import QtCore, QtGui

from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Events.dynamic_plot import DynamicPlot
from VeraGridEngine.Devices.Events.dynamic_plot_entry import DynamicPlotEntry
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Devices.Parents.dynamic_bus_parent import DynamicBusDevice
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, StudyResultsType, PlotSimulationType
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


def _append_unique_variables(target: List[Var], seen_uids: Set[int], variables: Sequence[Var]) -> None:
    """
    Append variables while preserving the first occurrence of each uid.

    :param target: Ordered target list.
    :param seen_uids: Set of already appended variable uids.
    :param variables: Variables to append.
    :return: None.
    """
    variable: Var
    for variable in variables:
        if variable.uid in seen_uids:
            pass
        else:
            target.append(variable)
            seen_uids.add(variable.uid)


def collect_dynamic_model_plot_variables(model: Block,
                                         simulation_type: PlotSimulationType | str) -> List[Var]:
    """
    Collect plottable variables from one dynamic-model block hierarchy.

    :param model: Assigned dynamic model block.
    :param simulation_type: Simulation family identifier.
    :return: Ordered plottable variables without duplicated uids.

    Dynamic Editor-created models can keep their symbolic variables inside
    child blocks instead of on the root wrapper block. This helper traverses
    the full block hierarchy so pre-simulation discovery matches the runtime
    compilation behaviour for both template and editor-created models.
    """
    resolved_simulation_type: PlotSimulationType
    if isinstance(simulation_type, PlotSimulationType):
        resolved_simulation_type = simulation_type
    else:
        resolved_simulation_type = _parse_plot_simulation_type(simulation_type=str(simulation_type))

    ordered_variables: List[Var] = list()
    seen_uids: Set[int] = set()
    block_item: Block
    for block_item in model.get_all_blocks():
        _append_unique_variables(target=ordered_variables, seen_uids=seen_uids, variables=block_item.state_vars)
        _append_unique_variables(target=ordered_variables, seen_uids=seen_uids, variables=block_item.algebraic_vars)
        if resolved_simulation_type == PlotSimulationType.EMT:
            _append_unique_variables(target=ordered_variables, seen_uids=seen_uids, variables=block_item.diff_vars)
        else:
            pass

    return ordered_variables


def _collect_dynamic_model_diff_var_uids(model: Block) -> Set[int]:
    """
    Collect all differential-variable uids declared by one block hierarchy.

    :param model: Assigned dynamic model block.
    :return: Set of differential-variable uids.
    """
    diff_var_uids: Set[int] = set()
    block_item: Block
    for block_item in model.get_all_blocks():
        variable: Var
        for variable in block_item.diff_vars:
            diff_var_uids.add(variable.uid)

    return diff_var_uids


def _parse_plot_simulation_type(simulation_type: str) -> PlotSimulationType:
    """
    Parse one simulation-family label into the handler enum.

    :param simulation_type: Simulation-family label.
    :return: Parsed plot simulation type.
    :raises ValueError: If the label is not a supported plot simulation family.
    """
    if simulation_type == "RMS":
        return PlotSimulationType.RMS
    else:
        if simulation_type == "EMT":
            return PlotSimulationType.EMT
        else:
            raise ValueError("Unsupported plot simulation type")


def _get_plot_simulation_type_from_results(results: RmsResults | EmtResults) -> PlotSimulationType:
    """
    Map one runtime results family to the persistent plot simulation label.

    :param results: RMS or EMT results object.
    :return: Plot simulation type.
    """
    if type(results) == RmsResults:
        return PlotSimulationType.RMS
    else:
        if type(results) == EmtResults:
            return PlotSimulationType.EMT
        else:
            raise ValueError("Unsupported dynamics results type")

def build_pre_simulation_dynamic_tree_data(circuit: MultiCircuit,
                                           simulation_type: PlotSimulationType | str) -> Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]]:
    """
    Build the pre-simulation dynamic variable tree from configured model blocks.

    :param circuit: Project circuit with configured dynamic models.
    :param simulation_type: Simulation family identifier.
    :return: Device tree grouped by device type and device.

    The first implementation uses only declarative variables already present in
    the configured model blocks. Compiler-generated runtime variables are left
    for the post-results handler.
    """
    resolved_simulation_type: PlotSimulationType
    if isinstance(simulation_type, PlotSimulationType):
        resolved_simulation_type = simulation_type
    else:
        resolved_simulation_type = _parse_plot_simulation_type(simulation_type=str(simulation_type))

    tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]] = dict()

    device: ALL_DEV_TYPES
    for device in circuit.get_all_elements_iter():
        include_device: bool = isinstance(device, DynamicDevice)
        if isinstance(device, DynamicBusDevice):
            include_device = True
        else:
            pass

        if include_device:
            variables: List[Var] = list()

            model_block: Block = _get_pre_simulation_block(device=device, simulation_type=resolved_simulation_type)
            variables.extend(collect_dynamic_model_plot_variables(model=model_block,
                                                                  simulation_type=resolved_simulation_type))

            if len(variables) > 0:
                devices_by_type: Dict[ALL_DEV_TYPES, List[Var]] = tree_data.get(device.device_type, dict())
                devices_by_type[device] = list(variables)
                tree_data[device.device_type] = devices_by_type
            else:
                pass
        else:
            pass

    return tree_data


def _get_pre_simulation_block(device: DynamicDevice | DynamicBusDevice,
                              simulation_type: PlotSimulationType) -> Block:
    """
    Get the declarative block that should feed the pre-simulation variable tree.

    :param device: Dynamic device being inspected.
    :param simulation_type: Simulation family requested by the editor.
    :return: Block whose declarative variables should be exposed.

    The pre-simulation editor should reflect the currently configured model
    choice. Template blocks are preferred because they are the authoritative
    configuration immediately after the user swaps a model in the editor.
    """
    if isinstance(device, DynamicBusDevice):
        if simulation_type == PlotSimulationType.RMS:
            return device.rms_model
        else:
            if simulation_type == PlotSimulationType.EMT:
                return device.emt_model
            else:
                raise ValueError("Unsupported pre-simulation plot family")
    else:
        pass

    if simulation_type == PlotSimulationType.RMS:
        if device.rms_template is not None:
            return device.rms_template.block
        else:
            if device.rms_fmu_template is not None:
                return device.rms_fmu_template.block
            else:
                return device.rms_model
    else:
        if simulation_type == PlotSimulationType.EMT:
            if device.emt_template is not None:
                return device.emt_template.block
            else:
                if device.emt_fmu_template is not None:
                    return device.emt_fmu_template.block
                else:
                    return device.emt_model
        else:
            raise ValueError("Unsupported pre-simulation plot family")


class DynamicResultSeriesKey:
    """
    Stable identity for one plottable dynamic-result series.

    The key identifies the exact series selected by the user, not just the
    visible variable name. Its fields intentionally capture the dimensions that
    can otherwise collide in the GUI:

    * simulation family (RMS versus EMT),
    * event-group source within that family,
    * device type and device ``idtag``,
    * result array namespace (``values`` versus ``diff_values``),
    * variable position on the device, and
    * component index in the underlying results array.

    Plot groups store and restore these keys so the handler can reuse plots
    across repeated runs of the same study without relying on transient
    ``Var.uid`` values.
    """

    __slots__ = (
        "_simulation_type",
        "_source_id",
        "_device_type",
        "_device_idtag",
        "_result_path",
        "_variable_index",
        "_component_index",
    )

    def __init__(self,
                 simulation_type: StudyResultsType,
                 source_id: str,
                 device_type: DeviceType,
                 device_idtag: str,
                 result_path: str,
                 variable_index: int,
                 component_index: int) -> None:
        self._simulation_type: StudyResultsType = simulation_type
        self._source_id: str = source_id
        self._device_type: DeviceType = device_type
        self._device_idtag: str = device_idtag
        self._result_path: str = result_path
        self._variable_index: int = variable_index
        self._component_index: int = component_index

    def __hash__(self) -> int:
        return hash((self._simulation_type,
                     self._source_id,
                     self._device_type,
                     self._device_idtag,
                     self._result_path,
                     self._variable_index,
                     self._component_index))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DynamicResultSeriesKey):
            return ((self._simulation_type,
                     self._source_id,
                     self._device_type,
                     self._device_idtag,
                     self._result_path,
                     self._variable_index,
                     self._component_index)
                    == (other._simulation_type,
                        other._source_id,
                        other._device_type,
                        other._device_idtag,
                        other._result_path,
                        other._variable_index,
                        other._component_index))
        else:
            return False

    def to_payload(self) -> str:
        return json.dumps([
            self._simulation_type.value,
            self._source_id,
            self._device_type.value,
            self._device_idtag,
            self._result_path,
            self._variable_index,
            self._component_index,
        ], separators=(",", ":"))

    @classmethod
    def from_payload(cls, payload: str) -> "DynamicResultSeriesKey | None":
        try:
            values = json.loads(payload)
        except json.JSONDecodeError:
            return None

        if isinstance(values, list) and len(values) == 7:
            try:
                return cls(
                    simulation_type=StudyResultsType(values[0]),
                    source_id=str(values[1]),
                    device_type=DeviceType(values[2]),
                    device_idtag=str(values[3]),
                    result_path=str(values[4]),
                    variable_index=int(values[5]),
                    component_index=int(values[6]),
                )
            except (TypeError, ValueError):
                return None
        else:
            return None


class DynamicResultSeries:
    """
    Source-specific dynamic-result series bound to current results arrays.

    A single ``Var`` can produce multiple ``DynamicResultSeries`` objects when a
    results object contains multiple event groups. Each series wraps the current
    ``Var`` together with its :class:`DynamicResultSeriesKey` and the event-group
    index needed to read the correct data slice.
    """

    __slots__ = (
        "_key",
        "_var",
        "_group_idx",
        "_source_label",
        "_device_label",
        "_variable_label",
    )

    def __init__(self,
                 key: DynamicResultSeriesKey,
                 var: Var,
                 group_idx: int,
                 source_label: str,
                 device_label: str,
                 variable_label: str) -> None:
        self._key: DynamicResultSeriesKey = key
        self._var: Var = var
        self._group_idx: int = group_idx
        self._source_label: str = source_label
        self._device_label: str = device_label
        self._variable_label: str = variable_label

    def get_key(self) -> DynamicResultSeriesKey:
        return self._key

    def get_var(self) -> Var:
        return self._var

    def get_var_uid(self) -> int:
        return self._var.uid

    def get_group_idx(self) -> int:
        return self._group_idx

    def get_source_label(self) -> str:
        return self._source_label

    def get_variable_label(self) -> str:
        return self._variable_label

    def get_device_label(self) -> str:
        """
        Get the visible device label associated with this series.

        :return: Device label.
        """
        return self._device_label

    def get_tree_leaf_label(self, has_multiple_sources: bool) -> str:
        if has_multiple_sources:
            return self._source_label
        else:
            return self._variable_label

    def get_plot_label(self, has_multiple_sources: bool) -> str:
        if has_multiple_sources:
            return self._device_label + " - " + self._variable_label + " - " + self._source_label
        else:
            return self._variable_label


class DynamicPlotCandidate:
    """
    Pre-simulation dynamic curve candidate built from configured model blocks.

    The candidate stores the semantic identity needed to create one persistent
    :class:`DynamicPlotEntry` before any runtime result arrays exist.
    """

    __slots__ = (
        "_simulation_type",
        "_event_group_idtag",
        "_event_group_name",
        "_device_type",
        "_device_idtag",
        "_device_label",
        "_variable_name",
        "_result_path_kind",
        "_curve_label",
        "_var",
    )

    def __init__(self,
                 simulation_type: PlotSimulationType,
                 event_group_idtag: str,
                 event_group_name: str,
                 device_type: DeviceType,
                 device_idtag: str,
                 device_label: str,
                 variable_name: str,
                 result_path_kind: str,
                 curve_label: str,
                 var: Var) -> None:
        self._simulation_type: PlotSimulationType = simulation_type
        self._event_group_idtag: str = event_group_idtag
        self._event_group_name: str = event_group_name
        self._device_type: DeviceType = device_type
        self._device_idtag: str = device_idtag
        self._device_label: str = device_label
        self._variable_name: str = variable_name
        self._result_path_kind: str = result_path_kind
        self._curve_label: str = curve_label
        self._var: Var = var

    def get_var(self) -> Var:
        """
        Get the symbolic variable shown in the source tree.

        :return: Symbolic variable.
        """
        return self._var

    def get_tree_leaf_label(self, has_multiple_sources: bool) -> str:
        """
        Get the label shown for this source-tree leaf.

        :param has_multiple_sources: Whether multiple event-group sources exist.
        :return: Leaf label.
        """
        if has_multiple_sources:
            return self._event_group_name
        else:
            return self._variable_name

    def get_plot_label(self, has_multiple_sources: bool) -> str:
        """
        Get the label shown in the plot tree.

        :param has_multiple_sources: Whether multiple event-group sources exist.
        :return: Plot label.
        """
        if has_multiple_sources:
            return self._curve_label
        else:
            return self._variable_name

    def to_payload(self) -> str:
        """
        Serialize this pre-simulation candidate for drag-and-drop.

        :return: Serialized payload.
        """
        payload: Dict[str, str] = dict()
        payload["simulation_type"] = self._simulation_type.value
        payload["event_group_idtag"] = self._event_group_idtag
        payload["event_group_name"] = self._event_group_name
        payload["curve_device_type"] = self._device_type.value
        payload["device_idtag"] = self._device_idtag
        payload["device_name_hint"] = self._device_label
        payload["variable_name"] = self._variable_name
        payload["result_path_kind"] = self._result_path_kind
        payload["curve_label"] = self._curve_label
        return json.dumps(payload, separators=(",", ":"))



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
    Group of plot-variable references selected by the user.

    The group stores runtime resolved series when available and falls back to
    persistent unresolved plot entries when no matching results series exists.
    Legacy ``Var`` entries are still tolerated so older tests and callers keep
    working.
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
        self._vars: List[DynamicResultSeries | DynamicPlotEntry | Var] = list()

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

    def get_series(self) -> List[DynamicResultSeries | DynamicPlotEntry | Var]:
        """
        Get the stored plot-variable references.

        :return: Entries in insertion order.
        """
        return list(self._vars)

    def get_vars(self) -> List[Var]:
        """
        Get the current underlying variables stored in the group.

        :return: Variable list kept for compatibility with older tests and callers.
        """
        variables: List[Var] = list()

        entry: DynamicResultSeries | DynamicPlotEntry | Var
        for entry in self._vars:
            if isinstance(entry, DynamicResultSeries):
                variables.append(entry.get_var())
            elif isinstance(entry, DynamicPlotEntry):
                if isinstance(entry.variable, Var):
                    variables.append(entry.variable)
                else:
                    pass
            elif isinstance(entry, Var):
                variables.append(entry)
            else:
                pass

        return variables

    def contains_var(self, variable: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
        """
        Check whether a series already belongs to the group.

        :param variable: Series to inspect.
        :return: ``True`` when the variable is already present.
        """
        contained: bool = False
        existing_var: DynamicResultSeries | DynamicPlotEntry | Var
        for existing_var in self._vars:
            if isinstance(existing_var, DynamicResultSeries) and isinstance(variable, DynamicResultSeries):
                if existing_var.get_key() == variable.get_key():
                    contained = True
                else:
                    pass
            elif isinstance(existing_var, DynamicPlotEntry) and isinstance(variable, DynamicPlotEntry):
                if existing_var.idtag == variable.idtag:
                    contained = True
                else:
                    pass
            elif isinstance(existing_var, Var) and isinstance(variable, Var):
                if existing_var.uid == variable.uid:
                    contained = True
                else:
                    pass
            else:
                pass
        return contained

    def add_var(self, variable: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
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

    def remove_var(self, variable: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
        """
        Remove a variable from the group.

        :param variable: Variable to remove.
        :return: ``True`` when the variable was present and removed.
        """
        variable_idx: int = -1
        idx: int
        existing_var: DynamicResultSeries | DynamicPlotEntry | Var
        for idx, existing_var in enumerate(self._vars):
            if isinstance(existing_var, DynamicResultSeries) and isinstance(variable, DynamicResultSeries):
                if existing_var.get_key() == variable.get_key():
                    variable_idx = idx
                else:
                    pass
            elif isinstance(existing_var, DynamicPlotEntry) and isinstance(variable, DynamicPlotEntry):
                if existing_var.idtag == variable.idtag:
                    variable_idx = idx
                else:
                    pass
            elif isinstance(existing_var, Var) and isinstance(variable, Var):
                if existing_var.uid == variable.uid:
                    variable_idx = idx
                else:
                    pass
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
                if isinstance(item_data, DynamicResultSeries) or isinstance(item_data, DynamicPlotCandidate):
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
        :return: Mime payload containing the dragged series key.
        """
        mime_data: QtCore.QMimeData = QtCore.QMimeData()

        index: QtCore.QModelIndex
        for index in indexes:
            if index.isValid():
                item: QtGui.QStandardItem | None = self.itemFromIndex(index)
                if item is not None:
                    item_data: object = item.data(self._var_role)
                    if isinstance(item_data, DynamicResultSeries):
                        mime_data.setData(self._mime_type,
                                          QtCore.QByteArray(item_data.get_key().to_payload().encode("utf-8")))
                        return mime_data
                    else:
                        if isinstance(item_data, DynamicPlotCandidate):
                            mime_data.setData(self._mime_type,
                                              QtCore.QByteArray(item_data.to_payload().encode("utf-8")))
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
                series_key: DynamicResultSeriesKey | None = DynamicResultSeriesKey.from_payload(payload_text)
                group_name: str | None = self._handler.get_group_name_from_drop_index(index=parent)
                if group_name is not None:
                    if series_key is not None:
                        return self._handler.add_series_to_group(group_name=group_name, series_key=series_key)
                    else:
                        candidate: DynamicPlotCandidate | None = self._handler.get_candidate_from_payload(payload=payload_text)
                        if candidate is not None:
                            return self._handler.add_candidate_to_group(group_name=group_name, candidate=candidate)
                        else:
                            return False
                else:
                    return False
            else:
                return False


def build_dynamics_tree_model(tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]],
                              var_role: int,
                              mime_type: str,
                              series_by_var_uid: Dict[int, List[DynamicResultSeries | DynamicPlotCandidate]],
                              has_multiple_sources: bool) -> DynamicsDeviceTreeModel:
    """
    Build the source tree-view model for RMS/EMT dynamics results.

    :param tree_data: Hierarchical RMS results tree grouped by device type and device.
    :param var_role: Qt item-data role used to store the ``Var`` instance in leaf nodes.
    :param mime_type: Mime type exported when dragging a variable.
    :param series_by_var_uid: Source-specific dynamic selectors grouped by current variable uid.
    :param has_multiple_sources: ``True`` when multiple event-group sources must be shown.
    :return: Source tree model ready to be assigned to a QTreeView.

    The tree uses the existing device hierarchy from the results object. When a
    variable exists in multiple event groups, the variable node gets one child
    per source-specific series so the drag payload can preserve the exact source
    selected by the user.
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
                variable_item: QtGui.QStandardItem = _build_tree_item(text=_get_var_label(variable=variable))
                device_item.appendRow(variable_item)

                series_list: List[DynamicResultSeries | DynamicPlotCandidate] = series_by_var_uid.get(variable.uid, list())
                if has_multiple_sources:
                    series: DynamicResultSeries | DynamicPlotCandidate
                    for series in series_list:
                        source_item: QtGui.QStandardItem = _build_tree_item(
                            text=series.get_tree_leaf_label(has_multiple_sources=True)
                        )
                        source_item.setData(series, var_role)
                        variable_item.appendRow(source_item)
                elif len(series_list) > 0:
                    variable_item.setData(series_list[0], var_role)
                else:
                    pass

    return model


class DynamicsResultsHandler:
    """
    Prepare GUI structures for dynamic-result selection, plotting, and reuse.

    The handler owns two related views of the same results object:

    * the available-variable tree built from the current results, and
    * the user-defined plot groups that store plot-variable references.

    Plot groups are preserved across repeated runs of the same study by
    snapshotting their series identities before replacing the results object,
    then restoring only the entries that still resolve against the new results.
    """

    __slots__ = ("results", "circuit", "plot_simulation_type", "pre_simulation_mode", "tree_data", "tree_model",
                  "proxy_model", "plots_model", "group_idx", "var_role", "group_name_role", "drag_mime_type",
                  "plot_groups", "series_by_key", "series_by_var_uid", "source_labels")

    def __init__(self,
                 results: RmsResults | EmtResults | None,
                 circuit: MultiCircuit | None = None,
                 simulation_type: PlotSimulationType | str = PlotSimulationType.RMS):
        """
        Build the handler from RMS/EMT results data.

        :param results: RMS/EMT results container coming from the simulation engine, or ``None``.
        :param circuit: Optional circuit that owns the persistent plot definitions.
        :param simulation_type: Pre-simulation family identifier used when ``results`` is ``None``.
        :return: None.
        """
        # Runtime results are optional because the same editor is reused in the
        # pre-simulation workflow where only declarative model metadata exists.
        self.results: RmsResults | EmtResults | None = results
        self.circuit: MultiCircuit | None = circuit
        self.pre_simulation_mode: bool = results is None
        if results is not None:
            self.plot_simulation_type: PlotSimulationType = _get_plot_simulation_type_from_results(results=results)
        else:
            if isinstance(simulation_type, PlotSimulationType):
                self.plot_simulation_type = simulation_type
            else:
                self.plot_simulation_type = _parse_plot_simulation_type(simulation_type=str(simulation_type))

        # These roles are instance-owned so the handler carries all Qt metadata instead of relying on globals.
        self.var_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 300
        self.group_name_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 301
        self.drag_mime_type: str = "application/x-veragrid-dynamics-var"

        self.group_idx: Dict[str, int] = dict()
        self.tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]] = dict()
        self.tree_model: DynamicsDeviceTreeModel | None = None
        self.series_by_key: Dict[DynamicResultSeriesKey, List[DynamicResultSeries]] = dict()
        self.series_by_var_uid: Dict[int, List[DynamicResultSeries | DynamicPlotCandidate]] = dict()
        self.source_labels: List[str] = list()

        # The proxy model owns the reversible filtering state used by the device tree view.
        self.proxy_model: QtCore.QSortFilterProxyModel = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.tree_model)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setAutoAcceptChildRows(True)

        # Plot groups are stored separately from Qt so CRUD operations are explicit and testable.
        self.plot_groups: DynamicsPlotGroups = DynamicsPlotGroups()

        # The plots model is rebuilt from the domain objects after every CRUD operation.
        self.plots_model: DynamicsPlotsTreeModel = DynamicsPlotsTreeModel(handler=self)

        if self.results is not None:
            self._refresh_results_state(results=self.results)
        else:
            self._refresh_pre_simulation_state()

        self._reload_plot_groups_from_persistent_assets()
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

    def _asset_plot_matches_handler_family(self, plot_asset: DynamicPlot) -> bool:
        """
        Check whether one persistent plot asset belongs to this handler family.

        :param plot_asset: Persistent plot asset.
        :return: ``True`` when the asset should be projected by this handler.
        """
        if plot_asset.simulation_type == self.plot_simulation_type:
            return True
        else:
            return False

    def _find_matching_asset_plot(self, group_name: str) -> DynamicPlot | None:
        """
        Find the persistent plot asset that corresponds to one runtime group name.

        :param group_name: Runtime group name.
        :return: Matching persistent plot asset, or ``None``.
        """
        if self.circuit is not None:
            plot_asset: DynamicPlot
            for plot_asset in self.circuit.dynamic_plots:
                if self._asset_plot_matches_handler_family(plot_asset=plot_asset):
                    if plot_asset.name == group_name:
                        return plot_asset
                    else:
                        pass
                else:
                    pass
            return None
        else:
            return None

    def _get_or_create_asset_plot(self, group_name: str) -> DynamicPlot | None:
        """
        Get or create the persistent plot asset for one runtime group.

        :param group_name: Runtime group name.
        :return: Persistent plot asset, or ``None`` when there is no owning circuit.
        """
        plot_asset: DynamicPlot | None = self._find_matching_asset_plot(group_name=group_name)
        if plot_asset is not None:
            return plot_asset
        else:
            if self.circuit is not None:
                created_plot: DynamicPlot = DynamicPlot(name=group_name, simulation_type=self.plot_simulation_type.value)
                self.circuit.add_dynamic_plot(obj=created_plot)
                return created_plot
            else:
                return None

    def _get_matching_rms_group_asset(self, event_group_idtag: str) -> RmsEventsGroup | None:
        """
        Find the RMS event-group asset that matches one stable idtag.

        :param event_group_idtag: Stable RMS event-group identifier.
        :return: Matching RMS event-group asset, or ``None``.
        """
        if self.circuit is not None:
            group_asset: RmsEventsGroup
            for group_asset in self.circuit.rms_events_groups:
                if str(group_asset.idtag) == event_group_idtag:
                    return group_asset
                else:
                    pass
            return None
        else:
            return None

    def _build_series_binding_signature(self, series: DynamicResultSeries) -> tuple[str, str, str, str, str, str]:
        """
        Build the semantic binding signature for one runtime series.

        :param series: Runtime dynamic-result series.
        :return: Binding signature used to match persistent plot entries.
        """
        key: DynamicResultSeriesKey = series.get_key()
        group_idx: int = series.get_group_idx()
        group_idtags: Sequence[str] = self._get_group_idtags(results=self.results)
        group_names: Sequence[str] = self._get_group_names(results=self.results)
        event_group_identity: str = group_idtags[group_idx]

        if event_group_identity == "":
            event_group_identity = group_names[group_idx]
        else:
            pass

        return (
            self.plot_simulation_type.value,
            event_group_identity,
            str(key._device_type.value),
            str(key._device_idtag),
            str(series.get_variable_label()),
            str(key._result_path.split(":", 1)[0]),
        )

    def _build_asset_entry_binding_signature(self, entry: DynamicPlotEntry) -> tuple[str, str, str, str, str, str]:
        """
        Build the semantic binding signature stored in one persistent plot entry.

        :param entry: Persistent plot-entry asset.
        :return: Binding signature used to match runtime series.
        """
        event_group_identity: str = entry.event_group_idtag
        if event_group_identity == "":
            event_group_identity = entry.event_group_name
        else:
            pass

        return (
            str(entry.simulation_type.value),
            event_group_identity,
            str(entry.curve_device_type.value),
            str(entry.device_idtag),
            str(entry.variable_name),
            str(entry.result_path_kind),
        )

    def _build_binding_signature_to_series_index(self) -> Dict[tuple[str, str, str, str, str, str], List[DynamicResultSeries]]:
        """
        Build the semantic binding lookup from persistent signatures to runtime series.

        :return: Dictionary mapping semantic signatures to candidate series.
        """
        series_by_signature: Dict[tuple[str, str, str, str, str, str], List[DynamicResultSeries]] = dict()

        series_list: List[DynamicResultSeries]
        for series_list in self.series_by_var_uid.values():
            series: DynamicResultSeries
            for series in series_list:
                signature: tuple[str, str, str, str, str, str] = self._build_series_binding_signature(series=series)
                candidates: List[DynamicResultSeries] = series_by_signature.get(signature, list())
                candidates.append(series)
                series_by_signature[signature] = candidates

        return series_by_signature

    def _get_pre_simulation_group_assets(self) -> Sequence[RmsEventsGroup | EmtEventsGroup]:
        """
        Get the event-group assets for the current pre-simulation family.

        :return: Sequence of event-group assets.
        """
        if self.circuit is not None:
            if self.plot_simulation_type == PlotSimulationType.RMS:
                return list(self.circuit.rms_events_groups)
            else:
                if self.plot_simulation_type == PlotSimulationType.EMT:
                    return list(self.circuit.emt_events_groups)
                else:
                    return list()
        else:
            return list()

    def _get_pre_simulation_result_path_kind(self,
                                             device: DynamicDevice | DynamicBusDevice,
                                             variable: Var) -> str:
        """
        Determine the expected result namespace for one declarative model variable.

        :param device: Dynamic device that owns the model.
        :param variable: Declarative model variable.
        :return: Expected result namespace.
        """
        if self.plot_simulation_type == PlotSimulationType.EMT:
            emt_block: Block = _get_pre_simulation_block(device=device, simulation_type=self.plot_simulation_type)
            diff_var_uids: Set[int] = _collect_dynamic_model_diff_var_uids(model=emt_block)
            if variable.uid in diff_var_uids:
                return "diff_values"
            else:
                return "values"
        else:
            return "values"

    def _build_pre_simulation_candidate_index(self) -> Dict[int, List[DynamicPlotCandidate]]:
        """
        Build the draggable candidate index for the pre-simulation source tree.

        :return: Dictionary mapping variable uid to candidate leaves.
        """
        candidates_by_var_uid: Dict[int, List[DynamicPlotCandidate]] = dict()
        group_assets: Sequence[RmsEventsGroup | EmtEventsGroup] = self._get_pre_simulation_group_assets()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, List[Var]]
        for device_tpe, devices_data in self.tree_data.items():
            device: ALL_DEV_TYPES
            variables: List[Var]
            for device, variables in devices_data.items():
                if isinstance(device, (DynamicDevice, DynamicBusDevice)):
                    device_label: str = _get_device_label(device=device)
                    variable: Var
                    for variable in variables:
                        result_path_kind: str = self._get_pre_simulation_result_path_kind(device=device, variable=variable)
                        group_asset: RmsEventsGroup | EmtEventsGroup
                        for group_asset in group_assets:
                            candidate: DynamicPlotCandidate = DynamicPlotCandidate(
                                simulation_type=self.plot_simulation_type,
                                event_group_idtag=str(group_asset.idtag),
                                event_group_name=str(group_asset.name),
                                device_type=device_tpe,
                                device_idtag=str(device.idtag),
                                device_label=device_label,
                                variable_name=variable.name,
                                result_path_kind=result_path_kind,
                                curve_label=device_label + " - " + variable.name + " - " + str(group_asset.name),
                                var=variable,
                            )
                            entries: List[DynamicPlotCandidate] = candidates_by_var_uid.get(variable.uid, list())
                            entries.append(candidate)
                            candidates_by_var_uid[variable.uid] = entries
                else:
                    pass

        return candidates_by_var_uid

    def _refresh_pre_simulation_state(self) -> None:
        """
        Rebuild the source lookup maps from configured model metadata only.

        :return: None.
        """
        self.source_labels = [str(group_asset.name) for group_asset in self._get_pre_simulation_group_assets()]
        self.group_idx = dict()
        group_index: int
        group_label: str
        for group_index, group_label in enumerate(self.source_labels):
            self.group_idx[group_label] = group_index

        if self.circuit is not None:
            self.tree_data = build_pre_simulation_dynamic_tree_data(
                circuit=self.circuit,
                simulation_type=self.plot_simulation_type,
            )
        else:
            self.tree_data = dict()

        self.series_by_key = dict()
        self.series_by_var_uid = dict()
        pre_simulation_candidates: Dict[int, List[DynamicPlotCandidate]] = self._build_pre_simulation_candidate_index()
        var_uid: int
        candidate_list: List[DynamicPlotCandidate]
        for var_uid, candidate_list in pre_simulation_candidates.items():
            self.series_by_var_uid[var_uid] = list(candidate_list)

        self.tree_model = build_dynamics_tree_model(
            tree_data=self.tree_data,
            var_role=self.var_role,
            mime_type=self.drag_mime_type,
            series_by_var_uid=self.series_by_var_uid,
            has_multiple_sources=self.has_multiple_sources(),
        )
        self.proxy_model.setSourceModel(self.tree_model)

    def _build_runtime_payload_to_series_index(self) -> Dict[str, List[DynamicResultSeries]]:
        """
        Build the exact runtime-series payload lookup.

        :return: Dictionary mapping serialized runtime keys to candidate series.
        """
        series_by_payload: Dict[str, List[DynamicResultSeries]] = dict()

        series_list: List[DynamicResultSeries]
        for series_list in self.series_by_var_uid.values():
            series: DynamicResultSeries
            for series in series_list:
                payload: str = series.get_key().to_payload()
                candidates: List[DynamicResultSeries] = series_by_payload.get(payload, list())
                candidates.append(series)
                series_by_payload[payload] = candidates

        return series_by_payload

    def _bind_asset_entry_to_series(self,
                                    entry: DynamicPlotEntry,
                                    payload_index: Dict[str, List[DynamicResultSeries]],
                                    signature_index: Dict[tuple[str, str, str, str, str, str], List[DynamicResultSeries]]) -> DynamicResultSeries | None:
        """
        Bind one persistent plot entry to the unique matching runtime series.

        :param entry: Persistent plot-entry asset.
        :param payload_index: Exact runtime payload lookup.
        :param signature_index: Semantic binding lookup.
        :return: Bound runtime series, or ``None`` when missing or ambiguous.
        """
        payload: str = entry.runtime_series_key_payload
        if payload != "":
            payload_candidates: List[DynamicResultSeries] = payload_index.get(payload, list())
            if len(payload_candidates) == 1:
                return payload_candidates[0]
            else:
                pass
        else:
            pass

        signature: tuple[str, str, str, str, str, str] = self._build_asset_entry_binding_signature(entry=entry)
        signature_candidates: List[DynamicResultSeries] = signature_index.get(signature, list())
        if len(signature_candidates) == 1:
            return signature_candidates[0]
        else:
            return None

    def _reload_plot_groups_from_persistent_assets(self) -> None:
        """
        Rebuild the runtime plot-group projection from persistent circuit assets.

        :return: None.

        Persistent plot entries remain the source of truth. Runtime groups only
        receive the entries that can be resolved against the current results.
        """
        if self.circuit is not None:
            restored_plot_groups: DynamicsPlotGroups = DynamicsPlotGroups()
            payload_index: Dict[str, List[DynamicResultSeries]] = dict()
            signature_index: Dict[tuple[str, str, str, str, str, str], List[DynamicResultSeries]] = dict()

            if self.results is not None:
                payload_index = self._build_runtime_payload_to_series_index()
                signature_index = self._build_binding_signature_to_series_index()
            else:
                pass

            plot_asset: DynamicPlot
            for plot_asset in self.circuit.dynamic_plots:
                if self._asset_plot_matches_handler_family(plot_asset=plot_asset):
                    created: bool = restored_plot_groups.create_group(name=plot_asset.name)
                    if created:
                        group: DynamicsPlotGroup | None = restored_plot_groups.get_group(name=plot_asset.name)
                        if group is not None:
                            entry: DynamicPlotEntry
                            for entry in self.circuit.dynamic_plot_entries:
                                if entry.plot == plot_asset:
                                    if self.results is not None:
                                        bound_series: DynamicResultSeries | None = self._bind_asset_entry_to_series(
                                            entry=entry,
                                            payload_index=payload_index,
                                            signature_index=signature_index,
                                        )
                                        if bound_series is not None and entry.enabled:
                                            group.add_var(variable=bound_series)
                                        else:
                                            # Keep unresolved entries visible in the runtime
                                            # projection so the user can inspect or delete them
                                            # without losing the persistent definition.
                                            group.add_var(variable=entry)
                                    else:
                                        group.add_var(variable=entry)
                                else:
                                    pass
                        else:
                            pass
                    else:
                        pass
                else:
                    pass

            self.plot_groups = restored_plot_groups
        else:
            pass

    def _append_asset_entry_for_series(self, group_name: str, series: DynamicResultSeries) -> None:
        """
        Persist one runtime series selection into the owning circuit assets.

        :param group_name: Runtime plot-group name.
        :param series: Runtime series selected by the user.
        :return: None.
        """
        if self.circuit is not None:
            plot_asset: DynamicPlot | None = self._get_or_create_asset_plot(group_name=group_name)
            if plot_asset is not None:
                payload: str = series.get_key().to_payload()
                target_signature: tuple[str, str, str, str, str, str] = self._build_series_binding_signature(series=series)

                existing_entry: DynamicPlotEntry
                for existing_entry in self.circuit.dynamic_plot_entries:
                    if existing_entry.plot == plot_asset:
                        if existing_entry.runtime_series_key_payload == payload:
                            return None
                        else:
                            existing_signature: tuple[str, str, str, str, str, str] = (
                                self._build_asset_entry_binding_signature(entry=existing_entry)
                            )
                            if existing_signature == target_signature:
                                return None
                            else:
                                pass
                    else:
                        pass

                key: DynamicResultSeriesKey = series.get_key()
                group_idx: int = series.get_group_idx()
                group_idtags: Sequence[str] = self._get_group_idtags(results=self.results)
                group_names: Sequence[str] = self._get_group_names(results=self.results)
                legacy_group: RmsEventsGroup | None = None

                if self.plot_simulation_type == PlotSimulationType.RMS:
                    legacy_group = self._get_matching_rms_group_asset(event_group_idtag=group_idtags[group_idx])
                else:
                    pass

                asset_entry: DynamicPlotEntry = DynamicPlotEntry(
                    variable=series.get_var(),
                    plot=plot_asset,
                    group=legacy_group,
                    device=None,
                    simulation_type=self.plot_simulation_type.value,
                    event_group_idtag=group_idtags[group_idx],
                    event_group_name=group_names[group_idx],
                    curve_device_type=key._device_type,
                    device_idtag=key._device_idtag,
                    device_name_hint=series.get_device_label(),
                    variable_name=series.get_variable_label(),
                    result_path_kind=str(key._result_path.split(":", 1)[0]),
                    curve_label=series.get_plot_label(has_multiple_sources=self.has_multiple_sources()),
                    enabled=True,
                    runtime_series_key_payload=payload,
                    name=series.get_variable_label(),
                )
                self.circuit.add_dynamic_plot_entry(obj=asset_entry)
        else:
            pass

    def _append_asset_entry_for_candidate(self, group_name: str, candidate: DynamicPlotCandidate) -> DynamicPlotEntry | None:
        """
        Persist one pre-simulation curve candidate into the owning circuit assets.

        :param group_name: Runtime plot-group name.
        :param candidate: Pre-simulation candidate selected by the user.
        :return: Created persistent plot entry, or ``None``.
        """
        if self.circuit is not None:
            plot_asset: DynamicPlot | None = self._get_or_create_asset_plot(group_name=group_name)
            if plot_asset is not None:
                existing_entry: DynamicPlotEntry
                for existing_entry in self.circuit.dynamic_plot_entries:
                    if existing_entry.plot == plot_asset:
                        existing_signature: tuple[str, str, str, str, str, str] = (
                            self._build_asset_entry_binding_signature(entry=existing_entry)
                        )
                        candidate_signature: tuple[str, str, str, str, str, str] = (
                            str(candidate._simulation_type),
                            str(candidate._event_group_idtag),
                            str(candidate._device_type.value),
                            str(candidate._device_idtag),
                            str(candidate._variable_name),
                            str(candidate._result_path_kind),
                        )
                        if existing_signature == candidate_signature:
                            return existing_entry
                        else:
                            pass
                    else:
                        pass

                legacy_group: RmsEventsGroup | None = None
                if self.plot_simulation_type == PlotSimulationType.RMS:
                    legacy_group = self._get_matching_rms_group_asset(event_group_idtag=candidate._event_group_idtag)
                else:
                    pass

                asset_entry: DynamicPlotEntry = DynamicPlotEntry(
                    variable=candidate.get_var(),
                    plot=plot_asset,
                    group=legacy_group,
                    device=None,
                    simulation_type=candidate._simulation_type.value,
                    event_group_idtag=candidate._event_group_idtag,
                    event_group_name=candidate._event_group_name,
                    curve_device_type=candidate._device_type,
                    device_idtag=candidate._device_idtag,
                    device_name_hint=candidate._device_label,
                    variable_name=candidate._variable_name,
                    result_path_kind=candidate._result_path_kind,
                    curve_label=candidate._curve_label,
                    enabled=True,
                    runtime_series_key_payload="",
                    name=candidate._variable_name,
                )
                self.circuit.add_dynamic_plot_entry(obj=asset_entry)
                return asset_entry
            else:
                return None
        else:
            return None

    def _delete_asset_entry_for_series(self, group_name: str, series: DynamicResultSeries) -> None:
        """
        Delete the persistent plot entry that corresponds to one runtime series.

        :param group_name: Runtime plot-group name.
        :param series: Runtime series selected for deletion.
        :return: None.
        """
        if self.circuit is not None:
            plot_asset: DynamicPlot | None = self._find_matching_asset_plot(group_name=group_name)
            if plot_asset is not None:
                target_payload: str = series.get_key().to_payload()
                target_signature: tuple[str, str, str, str, str, str] = self._build_series_binding_signature(series=series)
                entry_to_delete: DynamicPlotEntry | None = None

                entry: DynamicPlotEntry
                for entry in self.circuit.dynamic_plot_entries:
                    if entry.plot == plot_asset:
                        if entry.runtime_series_key_payload == target_payload:
                            entry_to_delete = entry
                        else:
                            entry_signature: tuple[str, str, str, str, str, str] = (
                                self._build_asset_entry_binding_signature(entry=entry)
                            )
                            if entry_signature == target_signature:
                                entry_to_delete = entry
                            else:
                                pass
                    else:
                        pass

                if entry_to_delete is not None:
                    self.circuit.delete_dynamic_plot_entry(obj=entry_to_delete)
                else:
                    pass
            else:
                pass
        else:
            pass

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

    def get_series_from_index(self, index: QtCore.QModelIndex) -> DynamicResultSeries | None:
        """
        Get the source-specific dynamic series associated with a clicked device-tree index.

        :param index: Source-model index coming from the dynamics device tree.
        :return: Series stored in the clicked leaf node, or ``None`` for non-leaf nodes.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.tree_model.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self.var_role)
                if isinstance(item_data, DynamicResultSeries):
                    return item_data
                else:
                    return None
            else:
                return None
        else:
            return None

    def get_candidate_from_index(self, index: QtCore.QModelIndex) -> DynamicPlotCandidate | None:
        """
        Get the pre-simulation candidate associated with a source-tree index.

        :param index: Source-model index coming from the dynamics device tree.
        :return: Candidate stored in the clicked leaf node, or ``None``.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.tree_model.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self.var_role)
                if isinstance(item_data, DynamicPlotCandidate):
                    return item_data
                else:
                    return None
            else:
                return None
        else:
            return None

    def get_var_from_index(self, index: QtCore.QModelIndex) -> Var | None:
        """
        Get the current variable associated with a clicked device-tree index.

        :param index: Source-model index coming from the dynamics device tree.
        :return: Current ``Var`` for compatibility with older callers.
        """
        series: DynamicResultSeries | None = self.get_series_from_index(index=index)
        if series is not None:
            return series.get_var()
        else:
            candidate: DynamicPlotCandidate | None = self.get_candidate_from_index(index=index)
            if candidate is not None:
                return candidate.get_var()
            else:
                return None

    def get_candidate_from_payload(self, payload: str) -> DynamicPlotCandidate | None:
        """
        Resolve one pre-simulation drag payload back into a unique candidate.

        :param payload: Serialized drag payload.
        :return: Matching candidate, or ``None``.
        """
        candidate_list: List[DynamicPlotCandidate | DynamicResultSeries]
        for candidate_list in self.series_by_var_uid.values():
            candidate_entry: DynamicPlotCandidate | DynamicResultSeries
            for candidate_entry in candidate_list:
                if isinstance(candidate_entry, DynamicPlotCandidate):
                    if candidate_entry.to_payload() == payload:
                        return candidate_entry
                    else:
                        pass
                else:
                    pass

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

    def get_plot_series_from_index(self, index: QtCore.QModelIndex) -> DynamicResultSeries | None:
        """
        Get the series represented by a plots-tree index.

        :param index: Index from the plots tree.
        :return: Series when the index points to a plotted child, otherwise ``None``.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.plots_model.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self.var_role)
                if isinstance(item_data, DynamicResultSeries):
                    return item_data
                else:
                    return None
            else:
                return None
        else:
            return None

    def get_plot_asset_entry_from_index(self, index: QtCore.QModelIndex) -> DynamicPlotEntry | None:
        """
        Get the persistent unresolved plot entry represented by a plots-tree index.

        :param index: Index from the plots tree.
        :return: Persistent plot entry when the index points to an unresolved child.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.plots_model.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self.var_role)
                if isinstance(item_data, DynamicPlotEntry):
                    return item_data
                else:
                    return None
            else:
                return None
        else:
            return None

    def get_plot_var_from_index(self, index: QtCore.QModelIndex) -> Var | None:
        """
        Get the current variable represented by a plots-tree index.

        :param index: Index from the plots tree.
        :return: Current ``Var`` for compatibility with older callers.
        """
        series: DynamicResultSeries | None = self.get_plot_series_from_index(index=index)
        if series is not None:
            return series.get_var()
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

            entry: DynamicResultSeries | DynamicPlotEntry | Var
            for entry in group.get_series():
                if isinstance(entry, DynamicResultSeries):
                    variable_item: QtGui.QStandardItem = _build_tree_item(
                        text=entry.get_plot_label(has_multiple_sources=self.has_multiple_sources())
                    )
                    variable_item.setData(entry, self.var_role)
                    group_item.appendRow(variable_item)
                elif isinstance(entry, DynamicPlotEntry):
                    unresolved_label: str = entry.curve_label
                    if unresolved_label == "":
                        unresolved_label = entry.variable_name
                    else:
                        pass

                    if unresolved_label == "":
                        unresolved_label = entry.name
                    else:
                        pass

                    if unresolved_label == "":
                        unresolved_label = "Unresolved curve"
                    else:
                        pass

                    unresolved_suffix: str = " [pending]"
                    if self.results is not None:
                        unresolved_suffix = " [missing]"
                    else:
                        pass

                    variable_item = _build_tree_item(text=unresolved_label + unresolved_suffix)
                    variable_item.setData(entry, self.var_role)
                    if unresolved_suffix == " [missing]":
                        variable_item.setForeground(QtGui.QBrush(QtGui.QColor("#d67b7b")))
                        variable_item.setToolTip("Persistent dynamic plot entry not found in the current results")
                    else:
                        variable_item.setForeground(QtGui.QBrush(QtGui.QColor("#a0a0a0")))
                        variable_item.setToolTip("Persistent dynamic plot entry waiting for simulation results")
                    group_item.appendRow(variable_item)
                elif isinstance(entry, Var):
                    variable_item = _build_tree_item(text=_get_var_label(variable=entry))
                    variable_item.setData(entry, self.var_role)
                    group_item.appendRow(variable_item)
                else:
                    pass

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
        if self.circuit is not None:
            self._get_or_create_asset_plot(group_name=name)
        else:
            pass

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
        if self.circuit is not None:
            plot_asset: DynamicPlot | None = self._find_matching_asset_plot(group_name=group_name)
            if plot_asset is not None:
                self.circuit.delete_dynamic_plot(obj=plot_asset)
            else:
                pass
        else:
            pass

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
        :param var_uid: Variable uid kept for compatibility with older callers.
        :return: ``True`` when the variable was inserted.
        """
        series_list: List[DynamicResultSeries] = self.series_by_var_uid.get(var_uid, list())
        if len(series_list) == 1:
            return self.add_series_to_group(group_name=group_name, series_key=series_list[0].get_key())
        else:
            return False

    def add_series_to_group(self, group_name: str, series_key: DynamicResultSeriesKey) -> bool:
        """
        Add one source-specific series to a plot group and refresh the plots tree.

        :param group_name: Target plot-group name.
        :param series_key: Stable identity of the plotted series.
        :return: ``True`` when the series was inserted.

        Using a source-specific key instead of a raw ``Var.uid`` allows one plot
        to contain multiple event-group instances of the same visible variable.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        variable: DynamicResultSeries | None = self._get_unique_series_for_key(series_key=series_key)
        if group is not None:
            if variable is not None:
                inserted: bool = group.add_var(variable=variable)
                if inserted:
                    self._append_asset_entry_for_series(group_name=group_name, series=variable)
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
        series_list: List[DynamicResultSeries] = self.series_by_var_uid.get(var_uid, list())
        if len(series_list) == 1:
            return self.remove_series_from_group(group_name=group_name, series_key=series_list[0].get_key())
        else:
            return False

    def remove_series_from_group(self, group_name: str, series_key: DynamicResultSeriesKey) -> bool:
        """
        Remove one source-specific series from a plot group and refresh the plots tree.

        :param group_name: Plot-group name.
        :param series_key: Stable series identity.
        :return: ``True`` when the series was removed.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        variable: DynamicResultSeries | None = self._get_unique_series_for_key(series_key=series_key)
        if group is not None:
            if variable is not None:
                removed: bool = group.remove_var(variable=variable)
                if removed:
                    self._delete_asset_entry_for_series(group_name=group_name, series=variable)
                    self.rebuild_plots_model()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def add_candidate_to_group(self, group_name: str, candidate: DynamicPlotCandidate) -> bool:
        """
        Add one pre-simulation candidate to a plot group and persist it.

        :param group_name: Target plot-group name.
        :param candidate: Candidate selected from the pre-simulation tree.
        :return: ``True`` when the candidate was inserted.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        if group is not None:
            asset_entry: DynamicPlotEntry | None = self._append_asset_entry_for_candidate(
                group_name=group_name,
                candidate=candidate,
            )
            if asset_entry is not None:
                inserted: bool = group.add_var(variable=asset_entry)
                if inserted:
                    self.rebuild_plots_model()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def remove_asset_entry_from_group(self, group_name: str, entry: DynamicPlotEntry) -> bool:
        """
        Remove one persistent unresolved entry from a plot group.

        :param group_name: Plot-group name.
        :param entry: Persistent unresolved plot entry.
        :return: ``True`` when the entry was removed.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        if group is not None:
            removed: bool = group.remove_var(variable=entry)
            if removed:
                if self.circuit is not None:
                    self.circuit.delete_dynamic_plot_entry(obj=entry)
                else:
                    pass
                self.rebuild_plots_model()
                return True
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
        selected_var: DynamicResultSeries | None = self.get_plot_series_from_index(index=index)
        if selected_var is not None:
            group_name: str | None = self.get_plot_group_name_from_index(index=index)
            if group_name is not None:
                return self.remove_series_from_group(group_name=group_name, series_key=selected_var.get_key())
            else:
                return False
        else:
            asset_entry: DynamicPlotEntry | None = self.get_plot_asset_entry_from_index(index=index)
            if asset_entry is not None:
                group_name: str | None = self.get_plot_group_name_from_index(index=index)
                if group_name is not None:
                    return self.remove_asset_entry_from_group(group_name=group_name, entry=asset_entry)
                else:
                    return False
            else:
                group_name = self.get_plot_group_name_from_index(index=index)
                if group_name is not None:
                    return self.delete_plot_group(group_name=group_name)
                else:
                    return False

    def has_multiple_sources(self) -> bool:
        """
        Check whether the current results object exposes more than one source.

        :return: ``True`` when multiple event-group sources are available.
        """
        return len(self.source_labels) > 1

    def plot_series(self, series: DynamicResultSeries) -> None:
        """
        Plot one source-specific series.

        :param series: Series to plot.
        :return: Nothing.
        """
        figure = plt.figure(figsize=(12, 8))
        axis = figure.add_subplot(111)
        x_values, y_values = self._get_series_plot_data(series=series)
        axis.plot(x_values, y_values, label=series.get_plot_label(has_multiple_sources=self.has_multiple_sources()))
        axis.legend()
        plt.show()

    def plot_var(self, var: Var, group_name: str) -> None:
        """
        Plot one variable for one RMS events group.

        :param var: Variable to plot.
        :param group_name: RMS events group name.
        :return: Nothing.
        """
        gr_idx: int = self.group_idx[group_name]
        self.results.plot_var(var=var, group_idx=gr_idx)

    def plot_group(self, plot_group_name: str) -> bool:
        """
        Plot all variables stored in one plot group.

        :param plot_group_name: Plot-group name selected by the user.
        :return: ``True`` when the plot group existed and was plotted.

        Each stored dynamic series already knows its event-group source, so the
        group plot no longer depends on any global event-group selector.
        """
        plot_group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=plot_group_name)
        if plot_group is not None:
            if self.results is None:
                return False
            else:
                pass

            variables: List[DynamicResultSeries | Var] = plot_group.get_series()
            if len(variables) > 0:
                figure = plt.figure(figsize=(12, 8))
                axis = figure.add_subplot(111)

                variable: DynamicResultSeries | DynamicPlotEntry | Var
                for variable in variables:
                    if isinstance(variable, DynamicResultSeries):
                        x_values, y_values = self._get_series_plot_data(series=variable)
                        label: str = variable.get_plot_label(has_multiple_sources=self.has_multiple_sources())
                    elif isinstance(variable, DynamicPlotEntry):
                        x_values = self.results.time_array if self.results is not None else None
                        y_values = None
                        label = variable.curve_label
                    elif isinstance(variable, Var):
                        x_values = self.results.time_array
                        # Legacy raw ``Var`` entries are still tolerated, but
                        # only when they resolve to exactly one current series.
                        compatible_series: List[DynamicResultSeries] = self.series_by_var_uid.get(variable.uid, list())
                        if len(compatible_series) == 1:
                            _, y_values = self._get_series_plot_data(series=compatible_series[0])
                            label = compatible_series[0].get_plot_label(
                                has_multiple_sources=self.has_multiple_sources()
                            )
                        else:
                            y_values = None
                    else:
                        y_values = None

                    if y_values is not None:
                        axis.plot(x_values, y_values, label=label)
                    else:
                        pass

                if len(axis.lines) > 0:
                    axis.legend()
                    axis.set_title(plot_group_name)
                    plt.show()
                    return True
                else:
                    plt.close(figure)
                    return False
            else:
                return False
        else:
            return False



    def plot_entry_from_index(self, index: QtCore.QModelIndex) -> bool:
        """
        Plot the selected plots-tree entry.

        :param index: Selected plots-tree index.
        :return: ``True`` when something was plotted.
        """
        selected_var: DynamicResultSeries | None = self.get_plot_series_from_index(index=index)
        if selected_var is not None:
            self.plot_series(series=selected_var)
            return True
        else:
            unresolved_entry: DynamicPlotEntry | None = self.get_plot_asset_entry_from_index(index=index)
            if unresolved_entry is not None:
                return False
            else:
                plot_group_name: str | None = self.get_plot_group_name_from_index(index=index)
                if plot_group_name is not None:
                    return self.plot_group(plot_group_name=plot_group_name)
                else:
                    return False


    def get_data_from_plot_index(self, index: QtCore.QModelIndex) -> ResultsModel | None:
        """
        Build the table model for one selected dynamic plot.

        :param index: Selected plots-tree index.
        :return: Results model for the selected dynamic plot, or ``None``.

        The table reconstruction uses the source-specific series already stored
        in the plot group, so it does not need any external event-group state.
        """
        if self.results is None:
            return None
        else:
            pass

        plot_group_name: str | None = self.get_plot_group_name_from_index(index=index)

        if plot_group_name is not None:

            plot_group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=plot_group_name)
            variables: List[DynamicResultSeries | Var] = plot_group.get_series()
            if len(variables) > 0:
                compatible_series: List[DynamicResultSeries] = list()
                variable: DynamicResultSeries | DynamicPlotEntry | Var
                for variable in variables:
                    if isinstance(variable, DynamicResultSeries):
                        compatible_series.append(variable)
                    elif isinstance(variable, DynamicPlotEntry):
                        pass
                    else:
                        series_list: List[DynamicResultSeries] = self.series_by_var_uid.get(variable.uid, list())
                        if len(series_list) == 1:
                            compatible_series.append(series_list[0])
                        else:
                            pass

                if len(compatible_series) == 0:
                    return None

                first_time: np.ndarray = np.asarray(self.results.time_array)
                series: DynamicResultSeries
                for series in compatible_series:
                    series_time, _ = self._get_series_plot_data(series=series)
                    if not np.array_equal(np.asarray(series_time), first_time):
                        return None

                data = np.empty((len(first_time), len(compatible_series)), dtype=float)
                columns: List[str] = list()

                for idx, series in enumerate(compatible_series):
                    _, y_values = self._get_series_plot_data(series=series)
                    data[:, idx] = y_values
                    columns.append(series.get_plot_label(has_multiple_sources=self.has_multiple_sources()))

                table = ResultsTable(
                    data=data,
                    index=first_time,
                    columns=np.array(columns, dtype=str),
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

    def _get_group_names(self, results: RmsResults | EmtResults) -> Sequence[str]:
        """
        Get the ordered event-group labels for the current results object.

        :param results: Current RMS or EMT results object.
        :return: Ordered event-group labels as exposed by the results object.
        """
        if type(results) == RmsResults:
            return [str(gr) for gr in results.rms_events_group_names]
        elif type(results) == EmtResults:
            return [str(gr) for gr in results.emt_events_group_names]
        else:
            raise Exception("Unsupported dynamics results type")

    def _get_group_idtags(self, results: RmsResults | EmtResults) -> Sequence[str]:
        """
        Get the ordered event-group idtags for the current results object.

        :param results: Current RMS or EMT results object.
        :return: Ordered event-group idtags as exposed by the results object.
        """
        if type(results) == RmsResults:
            return [str(gr) for gr in results.rms_events_group_idtags]
        else:
            if type(results) == EmtResults:
                return [str(gr) for gr in results.emt_events_group_idtags]
            else:
                raise Exception("Unsupported dynamics results type")

    def _build_source_id(self, results: RmsResults | EmtResults, group_idx: int) -> str:
        """
        Build a source identifier for one event-group position.

        :param results: Current RMS or EMT results object.
        :param group_idx: Event-group index within the results arrays.
        :return: Identifier scoped to the results family and group index.

        The source id follows the event-group label instead of the array
        position. This keeps plot restoration stable when a repeated simulation
        emits only a subset of groups or changes their order.
        """
        group_idtags: Sequence[str] = self._get_group_idtags(results=results)
        group_names: Sequence[str] = self._get_group_names(results=results)
        group_identity: str = str(group_idtags[group_idx])

        if group_identity == "":
            group_identity = str(group_names[group_idx])
        else:
            pass

        return str(results.study_results_type.value) + ":" + group_identity

    def _resolve_result_path_and_component_index(self, variable: Var) -> tuple[str, int]:
        """
        Resolve which result array and column index stores one variable.

        :param variable: Variable to resolve in the current results object.
        :return: Pair ``(result_path, component_index)``.

        EMT exposes both ``values`` and ``diff_values`` arrays, so the returned
        path becomes part of the dynamic-variable identity.
        """
        if type(self.results) == RmsResults:
            return "values", self.results.uid2idx[variable.uid]
        elif type(self.results) == EmtResults:
            if variable.uid in self.results.uid2idx_vars:
                return "values", self.results.uid2idx_vars[variable.uid]
            elif variable.uid in self.results.uid2idx_diff:
                return "diff_values", self.results.uid2idx_diff[variable.uid]
            else:
                raise ValueError("Variable with uid " + str(variable.uid) + " not found in EMT results.")
        else:
            raise Exception("Unsupported dynamics results type")

    def _variable_is_exported_in_current_results(self, variable: Var) -> bool:
        """
        Check whether one device variable is exported by the current results object.

        :param variable: Variable referenced by the per-device results tree.
        :return: ``True`` when the variable exists in one current results array.

        RMS device-variable maps can still contain declarative differential
        variables that are not exported into ``results.values``. The dynamic
        results tree must ignore those unresolved entries instead of crashing
        while building source-specific plot series.
        """
        if type(self.results) == RmsResults:
            return variable.uid in self.results.uid2idx
        else:
            if type(self.results) == EmtResults:
                return variable.uid in self.results.uid2idx_vars or variable.uid in self.results.uid2idx_diff
            else:
                raise Exception("Unsupported dynamics results type")

    def _build_exported_results_tree_data(self) -> Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]]:
        """
        Build the runtime device tree using only variables exported by the results.

        :return: Filtered device tree grouped by device type and device.
        """
        raw_tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]] = self.results.get_devices_dict_tree()
        filtered_tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]] = dict()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, List[Var]]
        for device_tpe, devices_data in raw_tree_data.items():
            filtered_devices: Dict[ALL_DEV_TYPES, List[Var]] = dict()

            device: ALL_DEV_TYPES
            variables: List[Var]
            for device, variables in devices_data.items():
                exported_variables: List[Var] = list()

                variable: Var
                for variable in variables:
                    if self._variable_is_exported_in_current_results(variable=variable):
                        exported_variables.append(variable)
                    else:
                        pass

                if len(exported_variables) > 0:
                    filtered_devices[device] = exported_variables
                else:
                    pass

            if len(filtered_devices) > 0:
                filtered_tree_data[device_tpe] = filtered_devices
            else:
                pass

        return filtered_tree_data

    def _refresh_results_state(self, results: RmsResults | EmtResults) -> None:
        """
        Rebuild source lookup maps and the device tree for the given results object.

        :param results: New RMS or EMT results object.
        :return: Nothing.

        This method derives the current universe of plottable series from the
        results tree. For every ``(device, variable, event-group)`` combination
        it creates a :class:`DynamicResultSeries` and indexes it both by exact
        key and by current ``Var.uid`` for compatibility.
        """
        self.results = results
        self.source_labels = list(self._get_group_names(results=self.results))
        self.group_idx = self._build_group_idx(results=self.results)
        self.tree_data = self._build_exported_results_tree_data()
        self.series_by_key = dict()
        self.series_by_var_uid = dict()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, List[Var]]
        for device_tpe, devices_data in self.tree_data.items():
            device: ALL_DEV_TYPES
            variables: List[Var]
            for device, variables in devices_data.items():
                device_label: str = _get_device_label(device=device)
                device_idtag: str = str(device.idtag)

                variable_index: int
                variable: Var
                for variable_index, variable in enumerate(variables):
                    result_path, component_index = self._resolve_result_path_and_component_index(variable=variable)
                    scoped_result_path: str = result_path + ":" + variable.name

                    group_idx: int
                    source_label: str
                    for group_idx, source_label in enumerate(self.source_labels):
                        # A distinct series is created per event group so plots
                        # can mix sources without losing the exact origin of each
                        # selected variable.
                        key: DynamicResultSeriesKey = DynamicResultSeriesKey(
                            simulation_type=self.results.study_results_type,
                            source_id=self._build_source_id(results=self.results, group_idx=group_idx),
                            device_type=device_tpe,
                            device_idtag=device_idtag,
                            result_path=scoped_result_path,
                            variable_index=variable_index,
                            component_index=component_index,
                        )
                        series: DynamicResultSeries = DynamicResultSeries(
                            key=key,
                            var=variable,
                            group_idx=group_idx,
                            source_label=source_label,
                            device_label=device_label,
                            variable_label=_get_var_label(variable=variable),
                        )
                        self.series_by_key.setdefault(key, list()).append(series)
                        self.series_by_var_uid.setdefault(variable.uid, list()).append(series)

        self.tree_model = build_dynamics_tree_model(
            tree_data=self.tree_data,
            var_role=self.var_role,
            mime_type=self.drag_mime_type,
            series_by_var_uid=self.series_by_var_uid,
            has_multiple_sources=self.has_multiple_sources(),
        )
        self.proxy_model.setSourceModel(self.tree_model)

    def _get_unique_series_for_key(self, series_key: DynamicResultSeriesKey) -> DynamicResultSeries | None:
        """
        Resolve one exact series key only when it maps to a unique current series.

        :param series_key: Stable plot-variable identity.
        :return: Matching current series, or ``None`` when missing or ambiguous.

        Ambiguous matches are pruned instead of guessed so repeated simulations
        cannot silently reconnect a plot entry to the wrong event-group series.
        """
        candidate_series: List[DynamicResultSeries] = self.series_by_key.get(series_key, list())
        if len(candidate_series) == 1:
            return candidate_series[0]
        else:
            return None

    def _get_series_plot_data(self, series: DynamicResultSeries) -> tuple[np.ndarray, np.ndarray]:
        """
        Get x/y arrays for one source-specific plotted series.
        """
        x_values = np.asarray(self.results.time_array)
        key: DynamicResultSeriesKey = series.get_key()
        group_idx: int = series.get_group_idx()

        result_path_prefix: str = key._result_path.split(":", 1)[0]

        if result_path_prefix == "values":
            y_values = np.asarray(self.results.values[:, key._component_index, group_idx])
        elif result_path_prefix == "diff_values":
            if isinstance(self.results, EmtResults):
                y_values = np.asarray(self.results.diff_values[:, key._component_index, group_idx])
            else:
                raise ValueError("Unsupported dynamic result path: " + key._result_path)
        else:
            raise ValueError("Unsupported dynamic result path: " + key._result_path)

        return x_values, y_values

    def _build_group_idx(self, results: RmsResults | EmtResults) -> Dict[str, int]:
        """
        Build the event-group-name to index mapping for the given results object.
        """
        return {group_name: i for i, group_name in enumerate(self._get_group_names(results=results))}

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

    def _snapshot_plot_groups(self) -> List[tuple[str, List[DynamicResultSeriesKey | tuple[str, str, str]]]]:
        """
        Snapshot current plot groups using stable plot-variable references.

        Legacy ``Var`` entries are converted best-effort to the old visible signature.

        :return: List of tuples ``(group_name, [series_key_or_legacy_signature, ...])``.

        ``DynamicResultSeriesKey`` is the preferred identity because it preserves
        the exact event group and exact duplicate variable instance. The legacy
        signature exists only to keep compatibility with older in-memory plot
        entries that still store raw ``Var`` objects.
        """
        variable_signature_by_uid: Dict[int, tuple[str, str, str]] = self._build_uid_to_variable_signature_index()
        snapshot: List[tuple[str, List[DynamicResultSeriesKey | tuple[str, str, str]]]] = list()

        group: DynamicsPlotGroup
        for group in self.plot_groups.get_groups():
            var_signatures: List[DynamicResultSeriesKey | tuple[str, str, str]] = list()

            variable: DynamicResultSeries | Var
            for variable in group.get_series():
                if isinstance(variable, DynamicResultSeries):
                    var_signatures.append(variable.get_key())
                elif isinstance(variable, Var):
                    var_signature: tuple[str, str, str] | None = variable_signature_by_uid.get(variable.uid, None)
                    if var_signature is not None:
                        var_signatures.append(var_signature)
                    else:
                        pass
                else:
                    pass

            snapshot.append((group.get_name(), var_signatures))

        return snapshot

    def _build_series_semantic_signature(self,
                                         series_key: DynamicResultSeriesKey) -> tuple[str, str, str, str, str]:
        """
        Build a per-series semantic signature that survives array reindexing.

        :param series_key: Exact plot-variable key.
        :return: Tuple describing the semantic identity of one plotted series.

        The signature intentionally omits variable and component indexes so a
        device model change can reorder arrays without breaking unrelated plot
        entries. Any non-unique semantic match is treated as ambiguous and
        therefore pruned.
        """
        return (
            str(series_key._simulation_type.value),
            str(series_key._source_id),
            str(series_key._device_type.value),
            str(series_key._device_idtag),
            str(series_key._result_path),
        )

    def _build_semantic_signature_to_series_index(self) -> Dict[tuple[str, str, str, str, str], List[DynamicResultSeries]]:
        """
        Build a lookup table from semantic series identity to current series candidates.

        :return: Dictionary mapping semantic signatures to matching current series.
        """
        series_by_signature: Dict[tuple[str, str, str, str, str], List[DynamicResultSeries]] = dict()

        series_key: DynamicResultSeriesKey
        current_series_list: List[DynamicResultSeries]
        for series_key, current_series_list in self.series_by_key.items():
            signature: tuple[str, str, str, str, str] = self._build_series_semantic_signature(series_key=series_key)
            stored_series_list: List[DynamicResultSeries] = series_by_signature.get(signature, list())
            stored_series_list.extend(current_series_list)
            series_by_signature[signature] = stored_series_list

        return series_by_signature

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
                                           snapshot: List[tuple[str, List[DynamicResultSeriesKey | tuple[str, str, str]]]]) -> None:
        """
        Restore plot groups from exact dynamic-result keys.

        Legacy visible signatures are restored only when they map to exactly one
        current source-specific series.

        :param snapshot: Plot-group snapshot created with ``_snapshot_plot_groups()``.
        :return: Nothing.

        Entries that no longer resolve in the new results are silently omitted.
        This is the pruning step that removes invalid plot variables after a
        repeated simulation.
        """
        restored_plot_groups: DynamicsPlotGroups = DynamicsPlotGroups()
        series_by_semantic_signature: Dict[tuple[str, str, str, str, str], List[DynamicResultSeries]] = (
            self._build_semantic_signature_to_series_index()
        )
        variable_by_signature: Dict[tuple[str, str, str], List[DynamicResultSeries]] = (
            self._build_variable_signature_to_series_index()
        )

        group_name: str
        var_signatures: List[DynamicResultSeriesKey | tuple[str, str, str]]
        for group_name, var_signatures in snapshot:
            created: bool = restored_plot_groups.create_group(name=group_name)

            if created:
                group: DynamicsPlotGroup | None = restored_plot_groups.get_group(name=group_name)

                if group is not None:
                    var_signature: DynamicResultSeriesKey | tuple[str, str, str]
                    for var_signature in var_signatures:
                        variable: DynamicResultSeries | None
                        if isinstance(var_signature, DynamicResultSeriesKey):
                            variable = self._get_unique_series_for_key(series_key=var_signature)
                            if variable is None:
                                semantic_signature: tuple[str, str, str, str, str] = (
                                    self._build_series_semantic_signature(series_key=var_signature)
                                )
                                candidate_series: List[DynamicResultSeries] = series_by_semantic_signature.get(
                                    semantic_signature,
                                    list(),
                                )
                                if len(candidate_series) == 1:
                                    variable = candidate_series[0]
                                else:
                                    variable = None
                            else:
                                pass
                        else:
                            # Legacy ``Var`` snapshots do not encode event-group
                            # identity, so ambiguous matches are discarded instead
                            # of guessing and restoring the wrong series.
                            candidate_series: List[DynamicResultSeries] = variable_by_signature.get(var_signature, list())
                            if len(candidate_series) == 1:
                                variable = candidate_series[0]
                            else:
                                variable = None

                        if variable is not None:
                            group.add_var(variable=variable)
                        else:
                            pass
                else:
                    pass
            else:
                pass

        self.plot_groups = restored_plot_groups

    def _build_uid_to_variable_signature_index(self) -> Dict[int, tuple[str, str, str]]:
        """
        Build a lookup table from current variable uid to stable device-variable signature.

        The result tree already stores the relationship between devices and variables.
        This method converts that tree into a lookup that can translate legacy
        plot-variable references from ``Var.uid`` to
        ``(device.idtag, device.name, variable.name)``.

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
                # The legacy signature supplements the stable device idtag with the
                # visible device name. This avoids matching a different visible
                # device after a rename, but it also means renames can prevent
                # legacy entries from being restored.
                device_idtag: str = str(device.idtag)
                device_name: str = str(device.name)

                variable: Var
                for variable in variables:
                    # The stable plot identity requires the same device idtag, the
                    # same device name, and the same variable name in the new results.
                    signature_by_uid[variable.uid] = (device_idtag, device_name, variable.name)

        return signature_by_uid

    def _build_variable_signature_to_series_index(self) -> Dict[tuple[str, str, str], List[DynamicResultSeries]]:
        """
        Build a lookup table from legacy visible signature to current source-specific series.

        :return: Dictionary mapping ``(device_idtag, device_name, variable_name)`` to candidate series.

        The value is a list because the legacy signature does not include
        event-group identity and cannot distinguish duplicate visible variables
        on its own.
        """
        variable_by_signature: Dict[tuple[str, str, str], List[DynamicResultSeries]] = dict()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, List[Var]]
        for device_tpe, devices_data in self.tree_data.items():
            del device_tpe

            device: ALL_DEV_TYPES
            variables: List[Var]
            for device, variables in devices_data.items():
                device_idtag: str = str(device.idtag)
                device_name: str = str(device.name)

                variable: Var
                for variable in variables:
                    signature: tuple[str, str, str] = (device_idtag, device_name, variable.name)
                    current_entries: List[DynamicResultSeries] = variable_by_signature.get(signature, list())
                    current_entries.extend(self.series_by_var_uid.get(variable.uid, list()))
                    variable_by_signature[signature] = current_entries

        return variable_by_signature

    def update_results(self, results: RmsResults | EmtResults) -> None:
        """
        Replace the underlying results object while preserving dynamic-plot definitions.

        This method assumes that vars, diff_vars and params are compatible with the
        current handler. Compatibility must be checked before calling it.

        :param results: New RMS/EMT results for the same study type.
        :return: Nothing.

        The restoration process is exact-key first. Any entry whose key no
        longer exists in the new results is dropped, which prunes stale plot
        variables after a rerun.
        """
        plot_groups_snapshot: List[tuple[str, List[DynamicResultSeriesKey | tuple[str, str, str]]]] = list()
        if self.circuit is None:
            plot_groups_snapshot = self._snapshot_plot_groups()
        else:
            pass

        self._refresh_results_state(results=results)

        if self.circuit is not None:
            self._reload_plot_groups_from_persistent_assets()
        else:
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
