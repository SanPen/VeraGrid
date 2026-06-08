# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import json
from enum import Enum
from typing import Dict, List, Sequence, Set, Optional, Protocol, Union
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGrid.Gui.dynamic_events_editor_dialog import create_dynamic_events_group_with_dialog
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Events.dynamic_plot import DynamicPlot
from VeraGridEngine.Devices.Events.dynamic_plot_entry import DynamicPlotEntry
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.emt_event import EmtEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Devices.Parents.dynamic_bus_parent import DynamicBusDevice
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import (DeviceType, StudyResultsType, PlotSimulationType,
                                         DynamicSimulationMode, DynamicPlotEntryKind, TreeStateNodeKind,
                                         DynamicEntrySection, DynamicPlotMode, DynamicPlotEntryRole,
                                         DynamicEventTransitionType)
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGrid.Gui.results_model import ResultsModel


class _GenericDynamicsPlotsDropHandler(Protocol):
    def get_group_name_role(self) -> int:
        ...

    def get_drag_mime_type(self) -> str:
        ...

    def get_tree_state_role(self) -> int:
        ...

    def get_group_name_from_drop_index(self, index: QtCore.QModelIndex) -> str | None:
        ...

    def add_series_to_group(self, group_name: str, series_key: "DynamicResultSeriesKey") -> bool:
        ...

    def get_candidate_from_payload(self, payload: str) -> "DynamicPlotCandidate | None":
        ...

    def add_candidate_to_group(self, group_name: str, candidate: "DynamicPlotCandidate") -> bool:
        ...


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
        "_bus_label",
        "_variable_label",
        "_variable_custom_name",
    )

    def __init__(self,
                 key: DynamicResultSeriesKey,
                 var: Var,
                 group_idx: int,
                 source_label: str,
                 device_label: str,
                 bus_label: str,
                 variable_label: str,
                 variable_custom_name: str = "") -> None:
        self._key: DynamicResultSeriesKey = key
        self._var: Var = var
        self._group_idx: int = group_idx
        self._source_label: str = source_label
        self._device_label: str = device_label
        self._bus_label: str = bus_label
        self._variable_label: str = variable_label
        self._variable_custom_name: str = variable_custom_name

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
        # A user-defined name must override the generated label so manual renames
        # remain stable after rebinding the runtime series to new results objects.
        if self._variable_custom_name != "":
            return self._variable_custom_name
        else:
            pass

        if has_multiple_sources:
            return _join_plot_label_parts([
                self._variable_label,
                self._device_label,
                self._bus_label,
                self._source_label,
            ])
        else:
            return _join_plot_label_parts([
                self._variable_label,
                self._device_label,
                self._bus_label,
            ])

    def get_variable_custom_name(self) -> str:
        """
        Get the custom visible name shown for this plotted series.

        :return: Custom visible variable name.
        """
        return self._variable_custom_name

    def set_variable_custom_name(self, label: str) -> None:
        """
        Set the custom visible name shown for this plotted series.

        :param label: Requested visible label.
        :return: Nothing.
        """
        self._variable_custom_name = str(label).strip()

class DynamicPlotParameter:
    """
    Semantic identity of one plottable dynamic model parameter.
    """

    __slots__ = ("_display_name", "_canonical_name")

    def __init__(self, display_name: str, canonical_name: str) -> None:
        """
        Build one dynamic plot parameter descriptor.

        :param display_name: Parameter name shown to the user.
        :param canonical_name: Canonical symbolic parameter name used for resolution.
        :return: None.
        """
        self._display_name: str = str(display_name)
        self._canonical_name: str = str(canonical_name)

    def get_display_name(self) -> str:
        """
        Get the user-facing parameter name.

        :return: Display name.
        """
        return self._display_name

    def get_canonical_name(self) -> str:
        """
        Get the canonical symbolic parameter name.

        :return: Canonical name.
        """
        return self._canonical_name

class DynamicPlotCandidate:
    """
    Pre-simulation dynamic curve candidate built from configured model blocks.

    The candidate stores the semantic identity needed to create one persistent
    :class:`DynamicPlotEntry` before any runtime result arrays exist.
    """

    __slots__ = (
        "_simulation_type",
        "_entry_kind",
        "_event_group_idtag",
        "_event_group_name",
        "_device_type",
        "_device_idtag",
        "_device_label",
        "_bus_label",
        "_variable_name",
        "_result_path_kind",
        "_variable_custom_name",
        "_var",
        "_parameter",
    )

    def __init__(self,
                 simulation_type: PlotSimulationType,
                 entry_kind: DynamicPlotEntryKind,
                 event_group_idtag: str,
                 event_group_name: str,
                 device_type: DeviceType,
                 device_idtag: str,
                 device_label: str,
                 bus_label: str,
                 variable_name: str,
                 result_path_kind: str,
                 variable_custom_name: str,
                 var: Var | None,
                 parameter: DynamicPlotParameter | None) -> None:
        self._simulation_type: PlotSimulationType = simulation_type
        self._entry_kind: DynamicPlotEntryKind = entry_kind
        self._event_group_idtag: str = event_group_idtag
        self._event_group_name: str = event_group_name
        self._device_type: DeviceType = device_type
        self._device_idtag: str = device_idtag
        self._device_label: str = device_label
        self._bus_label: str = bus_label
        self._variable_name: str = variable_name
        self._result_path_kind: str = result_path_kind
        self._variable_custom_name: str = variable_custom_name
        self._var: Var | None = var
        self._parameter: DynamicPlotParameter | None = parameter

    def get_var(self) -> Var | None:
        """
        Get the symbolic variable shown in the source tree.

        :return: Symbolic variable.
        """
        return self._var

    def get_parameter(self) -> DynamicPlotParameter | None:
        """
        Get the parameter shown in the source tree.

        :return: Parameter descriptor, or ``None``.
        """
        return self._parameter

    def get_entry_kind(self) -> DynamicPlotEntryKind:
        """
        Get the semantic kind of this candidate.

        :return: Entry kind.
        """
        return self._entry_kind

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
        # Pre-simulation candidates already store the fully expanded default name
        # that must later become the persistent custom visible variable name.
        if has_multiple_sources:
            return self._variable_custom_name
        else:
            return _join_plot_label_parts([
                self._variable_name,
                self._device_label,
                self._bus_label,
            ])

    def to_payload(self) -> str:
        """
        Serialize this pre-simulation candidate for drag-and-drop.

        :return: Serialized payload.
        """
        payload: Dict[str, str] = dict()
        payload["simulation_type"] = self._simulation_type.value
        payload["entry_kind"] = self._entry_kind.value
        payload["event_group_idtag"] = self._event_group_idtag
        payload["event_group_name"] = self._event_group_name
        payload["curve_device_type"] = self._device_type.value
        payload["device_idtag"] = self._device_idtag
        payload["device_name_hint"] = self._device_label
        payload["variable_name"] = self._variable_name
        payload["result_path_kind"] = self._result_path_kind
        payload["variable_custom_name"] = self._variable_custom_name
        return json.dumps(payload, separators=(",", ":"))



class TreeStateSnapshot:
    """
    Expansion and selection state captured from one tree view.
    """

    __slots__ = ("_expanded_keys", "_current_key")

    def __init__(self, expanded_keys: Set[str], current_key: str | None) -> None:
        """
        Build one tree-state snapshot.

        :param expanded_keys: Semantic keys of expanded nodes.
        :param current_key: Semantic key of the current item.
        :return: None.
        """
        self._expanded_keys: Set[str] = set(expanded_keys)
        self._current_key: str | None = current_key

    def get_expanded_keys(self) -> Set[str]:
        """
        Get the semantic keys of expanded nodes.

        :return: Expanded semantic keys.
        """
        return set(self._expanded_keys)

    def get_current_key(self) -> str | None:
        """
        Get the semantic key of the current item.

        :return: Current semantic key, or ``None``.
        """
        return self._current_key






class DynamicPlotDropTargetKind(Enum):
    """
    Semantic drop targets accepted by the Dynamic Plots tree.
    """

    GROUP = "GROUP"
    XY_X_SLOT = "XY_X_SLOT"
    XY_Y_SLOT = "XY_Y_SLOT"


class DynamicPlotGroupDefinition:
    """
    Runtime projection of one persistent dynamic plot asset.
    """

    __slots__ = ("_name", "_mode", "_entries", "_entry_roles")

    def __init__(self, name: str, mode: DynamicPlotMode) -> None:
        """
        Build one plot-group definition.

        :param name: Plot-group name.
        :param mode: Plotting mode.
        :return: None.
        """
        self._name: str = name
        self._mode: DynamicPlotMode = mode
        self._entries: List[DynamicResultSeries | DynamicPlotEntry | Var] = list()
        self._entry_roles: List[DynamicPlotEntryRole] = list()

    def get_name(self) -> str:
        """
        Get the plot-group name.

        :return: Plot-group name.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """
        Set the plot-group name.

        :param name: New name.
        :return: None.
        """
        self._name = name

    def get_mode(self) -> DynamicPlotMode:
        """
        Get the plotting mode.

        :return: Plotting mode.
        """
        return self._mode

    def set_mode(self, mode: DynamicPlotMode) -> None:
        """
        Set the plotting mode.

        :param mode: Plotting mode.
        :return: None.
        """
        self._mode = mode

    def get_series(self) -> List[DynamicResultSeries | DynamicPlotEntry | Var]:
        """
        Get the stored entries.

        :return: Entries in insertion order.
        """
        return list(self._entries)

    def get_role_for_entry(self, entry: DynamicResultSeries | DynamicPlotEntry | Var) -> DynamicPlotEntryRole:
        """
        Get the semantic role associated with one stored entry.

        :param entry: Stored entry.
        :return: Entry role.
        """
        entry_index: int
        stored_entry: DynamicResultSeries | DynamicPlotEntry | Var
        for entry_index, stored_entry in enumerate(self._entries):
            if self._entries_match(existing_entry=stored_entry, candidate_entry=entry):
                if entry_index < len(self._entry_roles):
                    return self._entry_roles[entry_index]
                else:
                    return DynamicPlotEntryRole.CURVE
            else:
                pass

        if isinstance(entry, DynamicPlotEntry):
            return entry.role
        else:
            return DynamicPlotEntryRole.CURVE

    def _entries_match(self,
                       existing_entry: DynamicResultSeries | DynamicPlotEntry | Var,
                       candidate_entry: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
        """
        Compare two entries using the runtime identity already used by the handler.

        :param existing_entry: Existing stored entry.
        :param candidate_entry: Candidate entry.
        :return: ``True`` when both entries represent the same selection.
        """
        if isinstance(existing_entry, DynamicResultSeries) and isinstance(candidate_entry, DynamicResultSeries):
            return existing_entry.get_key() == candidate_entry.get_key()
        else:
            if isinstance(existing_entry, DynamicPlotEntry) and isinstance(candidate_entry, DynamicPlotEntry):
                return existing_entry.idtag == candidate_entry.idtag
            else:
                if isinstance(existing_entry, Var) and isinstance(candidate_entry, Var):
                    return existing_entry.uid == candidate_entry.uid
                else:
                    return False

    def contains_var(self, variable: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
        """
        Check whether one entry is already present.

        :param variable: Entry to inspect.
        :return: ``True`` when already stored.
        """
        existing_entry: DynamicResultSeries | DynamicPlotEntry | Var
        for existing_entry in self._entries:
            if self._entries_match(existing_entry=existing_entry, candidate_entry=variable):
                return True
            else:
                pass
        return False

    def add_entry(self,
                  variable: DynamicResultSeries | DynamicPlotEntry | Var,
                  role: DynamicPlotEntryRole = DynamicPlotEntryRole.CURVE) -> bool:
        """
        Add one entry into the group.

        :param variable: Entry to add.
        :param role: Role requested for the entry.
        :return: ``True`` when inserted.
        """
        if self._mode == DynamicPlotMode.TIME_SERIES:
            if role != DynamicPlotEntryRole.CURVE:
                return False
            else:
                pass

            if self.contains_var(variable=variable):
                return False
            else:
                self._entries.append(variable)
                self._entry_roles.append(DynamicPlotEntryRole.CURVE)
                return True
        else:
            if role == DynamicPlotEntryRole.CURVE:
                return False
            else:
                pass

            replaced: bool = self.replace_entry_for_role(variable=variable, role=role)
            if replaced:
                return True
            else:
                return False

    def get_entry_for_role(self, role: DynamicPlotEntryRole) -> DynamicResultSeries | DynamicPlotEntry | Var | None:
        """
        Get the entry stored for one semantic role.

        :param role: Requested role.
        :return: Stored entry, or ``None``.
        """
        entry: DynamicResultSeries | DynamicPlotEntry | Var
        for entry in self._entries:
            if self.get_role_for_entry(entry=entry) == role:
                return entry
            else:
                pass
        return None

    def replace_entry_for_role(self,
                               variable: DynamicResultSeries | DynamicPlotEntry | Var,
                               role: DynamicPlotEntryRole) -> bool:
        """
        Insert or replace the entry for one XY slot.

        :param variable: Entry to store.
        :param role: Slot role to replace.
        :return: ``True`` when stored.
        """
        if self._mode != DynamicPlotMode.XY:
            return False
        else:
            pass

        if role == DynamicPlotEntryRole.X_AXIS or role == DynamicPlotEntryRole.Y_AXIS:
            pass
        else:
            return False

        duplicate_entry: DynamicResultSeries | DynamicPlotEntry | Var
        for duplicate_entry in self._entries:
            existing_role: DynamicPlotEntryRole = self.get_role_for_entry(entry=duplicate_entry)
            if existing_role != role:
                if self._entries_match(existing_entry=duplicate_entry, candidate_entry=variable):
                    return False
                else:
                    pass
            else:
                pass

        replace_index: int = -1
        index: int
        existing_entry: DynamicResultSeries | DynamicPlotEntry | Var
        for index, existing_entry in enumerate(self._entries):
            if self.get_role_for_entry(entry=existing_entry) == role:
                replace_index = index
            else:
                pass

        if replace_index >= 0:
            self._entries[replace_index] = variable
            if replace_index < len(self._entry_roles):
                self._entry_roles[replace_index] = role
            else:
                self._entry_roles.append(role)
        else:
            self._entries.append(variable)
            self._entry_roles.append(role)

        return True

    def remove_var(self, variable: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
        """
        Remove one entry from the group.

        :param variable: Entry to remove.
        :return: ``True`` when removed.
        """
        variable_idx: int = -1
        index: int
        existing_entry: DynamicResultSeries | DynamicPlotEntry | Var
        for index, existing_entry in enumerate(self._entries):
            if self._entries_match(existing_entry=existing_entry, candidate_entry=variable):
                variable_idx = index
            else:
                pass

        if variable_idx >= 0:
            del self._entries[variable_idx]
            if variable_idx < len(self._entry_roles):
                del self._entry_roles[variable_idx]
            else:
                pass
            return True
        else:
            return False

    def get_vars(self) -> List[Var]:
        """
        Get the underlying variables kept for compatibility with older tests.

        :return: Variable list.
        """
        variables: List[Var] = list()
        entry: DynamicResultSeries | DynamicPlotEntry | Var
        for entry in self._entries:
            if isinstance(entry, DynamicResultSeries):
                variables.append(entry.get_var())
            else:
                if isinstance(entry, DynamicPlotEntry):
                    if isinstance(entry.variable, Var):
                        variables.append(entry.variable)
                    else:
                        pass
                else:
                    if isinstance(entry, Var):
                        variables.append(entry)
                    else:
                        pass
        return variables


class DynamicDeviceEntryCollection:
    """
    Ordered dynamic entries exposed for one device in the source tree.
    """

    __slots__ = ("_variables", "_parameters")

    def __init__(self,
                 variables: List[Var],
                 parameters: List[DynamicPlotParameter]) -> None:
        """
        Build one device entry collection.

        :param variables: Ordered dynamic variables for one device.
        :param parameters: Ordered model parameters for one device.
        :return: None.
        """
        self._variables: List[Var] = list(variables)
        self._parameters: List[DynamicPlotParameter] = list(parameters)

    def get_variables(self) -> List[Var]:
        """
        Get the ordered dynamic variables.

        :return: Copy of the variable list.
        """
        return list(self._variables)

    def get_parameters(self) -> List[DynamicPlotParameter]:
        """
        Get the ordered model parameters.

        :return: Copy of the parameter list.
        """
        return list(self._parameters)


def ensure_dynamic_plot_event_group(circuit: MultiCircuit,
                                    simulation_type: PlotSimulationType,
                                    parent: QtWidgets.QWidget | None = None) -> RmsEventsGroup | EmtEventsGroup | None:
    """
    Ensure that one RMS/EMT event group exists before creating a plot entry.

    :param circuit: Circuit that owns the event-group collections.
    :param simulation_type: Simulation family required by the dropped variable.
    :param parent: Optional parent widget for modal dialogs.
    :return: Existing or newly created event-group asset, or ``None`` when cancelled.
    """
    existing_groups: Sequence[RmsEventsGroup] | Sequence[EmtEventsGroup]

    if simulation_type == PlotSimulationType.RMS:
        existing_groups = circuit.rms_events_groups
    else:
        existing_groups = circuit.emt_events_groups

    if len(existing_groups) > 0:
        return existing_groups[0]
    else:
        pass

    # The event-group creation dialog expects the dynamic simulation mode, so
    # convert the plot-family enum here where the dialog invocation happens.
    mode: DynamicSimulationMode
    if simulation_type == PlotSimulationType.RMS:
        mode = DynamicSimulationMode.RMS
    elif simulation_type == PlotSimulationType.EMT:
        mode = DynamicSimulationMode.EMT
    else:
        raise ValueError(f"Unsupported plot simulation type: {simulation_type}")

    missing_group_message: str = ""
    if simulation_type == PlotSimulationType.RMS:
        missing_group_message = "No RMS Events Group found, please create one before adding a dynamic plot entry."
    elif simulation_type == PlotSimulationType.EMT:
        missing_group_message = "No EMT Events Group found, please create one before adding a dynamic plot entry."

    created_group_message_title: str = ""
    created_group_message_body_prefix: str = "New group name"

    if simulation_type == PlotSimulationType.RMS:
        created_group_message_title = "RMS group Created"
    elif  simulation_type == PlotSimulationType.EMT:
        created_group_message_title = "EMT group Created"

    created_group: RmsEventsGroup | EmtEventsGroup | None = create_dynamic_events_group_with_dialog(
        circuit=circuit,
        mode=mode,
        parent=parent,
        missing_group_message=missing_group_message,
        created_group_message_title=created_group_message_title,
        created_group_message_body_prefix=created_group_message_body_prefix,
    )
    if created_group is not None:
        return created_group
    else:
        return None


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


def _escape_tree_key_part(part: str) -> str:
    """
    Escape one semantic tree-key component.

    :param part: Raw semantic component.
    :return: Escaped component.
    """
    escaped_part: str = str(part).replace("\\", "\\\\")
    escaped_part = escaped_part.replace("/", "\\/")
    return escaped_part


def _build_tree_state_key(node_kind: TreeStateNodeKind, parts: Sequence[str]) -> str:
    """
    Build one stable semantic tree-node key.

    :param node_kind: Semantic node kind.
    :param parts: Ordered semantic path parts.
    :return: Serialized semantic key.
    """
    escaped_parts: List[str] = list()
    part: str
    for part in parts:
        escaped_parts.append(_escape_tree_key_part(part=part))

    return str(node_kind.value) + ":" + "/".join(escaped_parts)


def _build_parameter_plot_entry_label(entry: DynamicPlotEntry) -> str:
    """
    Build the visible label for one parameter plot entry.

    :param entry: Persistent parameter plot entry.
    :return: Visible label.
    """
    label: str = entry.variable_custom_name
    if label == "":
        label = entry.variable_name
    else:
        pass

    if label == "":
        label = entry.name
    else:
        pass

    if label == "":
        label = "Unresolved curve"
    else:
        pass

    return label


def _build_unresolved_plot_entry_label(entry: DynamicPlotEntry) -> str:
    """
    Build the visible unresolved label for one persistent plot entry.

    :param entry: Persistent plot entry.
    :return: Visible unresolved label.
    """
    label: str = entry.variable_custom_name
    if label == "":
        label = entry.variable_name
    else:
        pass

    if label == "":
        label = entry.name
    else:
        pass

    if label == "":
        label = "Unresolved curve"
    else:
        pass

    return label


def _build_plot_mode_display_label(mode: DynamicPlotMode) -> str:
    """
    Build the user-facing label for one dynamic plot mode.

    :param mode: Plotting mode.
    :return: Display label.
    """
    if mode == DynamicPlotMode.TIME_SERIES:
        return "Time Series (Y vs Time)"
    else:
        return "X-Y Plot (Y vs X)"


def _build_xy_slot_label(role: DynamicPlotEntryRole,
                         entry_label: str | None,
                         is_pending: bool) -> str:
    """
    Build the visible label for one XY slot row.

    :param role: Slot role.
    :param entry_label: Resolved entry label, or ``None``.
    :param is_pending: Whether the slot is unresolved.
    :return: Visible tree label.
    """
    role_prefix: str
    if role == DynamicPlotEntryRole.X_AXIS:
        role_prefix = "X: "
    else:
        role_prefix = "Y: "

    if entry_label is None or entry_label == "":
        return role_prefix + "<pending>"
    else:
        if is_pending:
            return role_prefix + entry_label + " [pending]"
        else:
            return role_prefix + entry_label


def _build_runtime_parameter_candidate(simulation_type: PlotSimulationType,
                                       device_tpe: DeviceType,
                                       device_idtag: str,
                                       device_label: str,
                                       bus_label: str,
                                       parameter: DynamicPlotParameter,
                                       event_group_idtag: str,
                                       event_group_name: str) -> DynamicPlotCandidate:
    """
    Build one runtime parameter candidate from resolved results metadata.

    :param simulation_type: RMS or EMT plot family.
    :param device_tpe: Device type that owns the parameter.
    :param device_idtag: Stable device identifier.
    :param device_label: Visible device label.
    :param bus_label: Visible bus label suffix.
    :param parameter: Parameter descriptor.
    :param event_group_idtag: Stable event-group identifier.
    :param event_group_name: Visible event-group name.
    :return: Runtime parameter candidate.
    """
    # The default custom label must carry the parameter, device, bus, and
    # event-group source so pre-simulation candidates remain uniquely
    # identifiable after they are persisted into plot entries.
    variable_custom_name: str = _join_plot_label_parts([
        parameter.get_display_name(),
        device_label,
        bus_label,
        event_group_name,
    ])

    return DynamicPlotCandidate(
        simulation_type=simulation_type,
        entry_kind=DynamicPlotEntryKind.PARAMETER,
        event_group_idtag=event_group_idtag,
        event_group_name=event_group_name,
        device_type=device_tpe,
        device_idtag=device_idtag,
        device_label=device_label,
        bus_label=bus_label,
        variable_name=parameter.get_canonical_name(),
        result_path_kind="parameter",
        variable_custom_name=variable_custom_name,
        var=None,
        parameter=parameter,
    )


def _capture_tree_view_state(view: QtWidgets.QTreeView, model: QtGui.QStandardItemModel, key_role: int) -> TreeStateSnapshot:
    """
    Capture expansion and current-item state from one tree view.

    :param view: Tree view whose state should be captured.
    :param model: Source model currently installed in the view.
    :param key_role: Qt item-data role storing semantic keys.
    :return: Captured tree-view state.
    """
    expanded_keys: Set[str] = set()
    current_key: str | None = None

    current_index: QtCore.QModelIndex = view.currentIndex()
    if current_index.isValid():
        current_item: QtGui.QStandardItem | None = model.itemFromIndex(current_index)
        if current_item is not None:
            current_key_data: object = current_item.data(key_role)
            if isinstance(current_key_data, str):
                current_key = current_key_data
            else:
                current_key = None
        else:
            current_key = None
    else:
        current_key = None

    row_count: int = model.rowCount()
    root_row: int
    for root_row in range(row_count):
        root_index: QtCore.QModelIndex = model.index(root_row, 0)
        _capture_tree_view_state_recursive(
            view=view,
            model=model,
            key_role=key_role,
            index=root_index,
            expanded_keys=expanded_keys,
        )

    return TreeStateSnapshot(expanded_keys=expanded_keys, current_key=current_key)


def _capture_tree_view_state_recursive(view: QtWidgets.QTreeView,
                                       model: QtGui.QStandardItemModel,
                                       key_role: int,
                                       index: QtCore.QModelIndex,
                                       expanded_keys: Set[str]) -> None:
    """
    Recursively capture expanded nodes from one tree branch.

    :param view: Tree view being inspected.
    :param model: Source model backing the view.
    :param key_role: Qt item-data role storing semantic keys.
    :param index: Current branch index.
    :param expanded_keys: Mutable target set of expanded semantic keys.
    :return: None.
    """
    if index.isValid():
        item: QtGui.QStandardItem | None = model.itemFromIndex(index)
        if item is not None:
            key_data: object = item.data(key_role)
            if view.isExpanded(index):
                if isinstance(key_data, str):
                    expanded_keys.add(key_data)
                else:
                    pass
            else:
                pass

            child_row_count: int = item.rowCount()
            child_row: int
            for child_row in range(child_row_count):
                child_index: QtCore.QModelIndex = item.child(child_row, 0).index()
                _capture_tree_view_state_recursive(
                    view=view,
                    model=model,
                    key_role=key_role,
                    index=child_index,
                    expanded_keys=expanded_keys,
                )
        else:
            pass
    else:
        pass


def _restore_tree_view_state(view: QtWidgets.QTreeView,
                             model: QtGui.QStandardItemModel,
                             key_role: int,
                             snapshot: TreeStateSnapshot) -> None:
    """
    Restore one previously captured tree-view state.

    :param view: Tree view whose state should be restored.
    :param model: Source model currently installed in the view.
    :param key_role: Qt item-data role storing semantic keys.
    :param snapshot: Captured tree-view state.
    :return: None.
    """
    index_by_key: Dict[str, QtCore.QModelIndex] = dict()
    row_count: int = model.rowCount()
    root_row: int
    for root_row in range(row_count):
        root_index: QtCore.QModelIndex = model.index(root_row, 0)
        _index_tree_view_state_keys(model=model, key_role=key_role, index=root_index, index_by_key=index_by_key)

    expanded_key: str
    for expanded_key in snapshot.get_expanded_keys():
        expanded_index: QtCore.QModelIndex | None = index_by_key.get(expanded_key, None)
        if expanded_index is not None:
            view.setExpanded(expanded_index, True)
        else:
            pass

    current_key: str | None = snapshot.get_current_key()
    if current_key is not None:
        current_index: QtCore.QModelIndex | None = index_by_key.get(current_key, None)
        if current_index is not None:
            view.setCurrentIndex(current_index)
        else:
            pass
    else:
        pass


def _index_tree_view_state_keys(model: QtGui.QStandardItemModel,
                                key_role: int,
                                index: QtCore.QModelIndex,
                                index_by_key: Dict[str, QtCore.QModelIndex]) -> None:
    """
    Build the semantic-key to index lookup for one tree model.

    :param model: Tree model being indexed.
    :param key_role: Qt item-data role storing semantic keys.
    :param index: Current branch index.
    :param index_by_key: Mutable key-to-index lookup.
    :return: None.
    """
    if index.isValid():
        item: QtGui.QStandardItem | None = model.itemFromIndex(index)
        if item is not None:
            key_data: object = item.data(key_role)
            if isinstance(key_data, str):
                index_by_key[key_data] = index
            else:
                pass

            child_row_count: int = item.rowCount()
            child_row: int
            for child_row in range(child_row_count):
                child_index: QtCore.QModelIndex = item.child(child_row, 0).index()
                _index_tree_view_state_keys(model=model,
                                            key_role=key_role,
                                            index=child_index,
                                            index_by_key=index_by_key)
        else:
            pass
    else:
        pass


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


def _get_device_state_id(device: ALL_DEV_TYPES) -> str:
    """
    Get a stable semantic identifier for one tree device node.

    :param device: Device instance stored in the dynamics trees.
    :return: Stable device identifier for tree-state keys.
    """
    if isinstance(device, (DynamicDevice, DynamicBusDevice)):
        return str(device.idtag)
    else:
        return str(device)


def _get_device_bus_label(device: ALL_DEV_TYPES) -> str:
    """
    Get the bus-name suffix associated with one device.

    :param device: Device instance stored in the dynamics trees.
    :return: User-facing bus label for the device, or an empty string when unavailable.
    """
    # Two-terminal devices need an explicit bus suffix because their visible
    # device label does not already encode both connection endpoints.
    if isinstance(device, BranchParent):
        bus_names: List[str] = list()

        # The first terminal is appended first so the suffix preserves the
        # physical branch orientation shown elsewhere in the GUI.
        if device.bus_from is not None:
            bus_from_name: str = str(device.bus_from.name).strip()
            if bus_from_name != "":
                bus_names.append(bus_from_name)
            else:
                pass
        else:
            pass

        # The second terminal is appended only when it contributes a distinct
        # visible endpoint, which avoids duplicated labels for degenerate cases.
        if device.bus_to is not None:
            bus_to_name: str = str(device.bus_to.name).strip()
            if bus_to_name != "" and bus_to_name not in bus_names:
                bus_names.append(bus_to_name)
            else:
                pass
        else:
            pass

        if len(bus_names) > 0:
            return " / ".join(bus_names)
        else:
            return ""
    else:
        # Injection devices already include their bus in ``str(device)``, and
        # bus devices are the bus themselves, so no extra suffix is needed.
        if isinstance(device, InjectionParent):
            return ""
        else:
            if isinstance(device, DynamicBusDevice):
                return ""
            else:
                return ""


def _get_var_label(variable: Var) -> str:
    """
    Get the label that represents a simulation variable.

    :param variable: RMS variable object.
    :return: User-facing label for the variable node.
    """
    # The symbolic variable name is the exact identifier used by the simulation arrays.
    return variable.name


def _join_plot_label_parts(parts: Sequence[str]) -> str:
    """
    Join non-empty label parts using the plot-tree separator.

    :param parts: Ordered label parts.
    :return: Joined label without empty trailing segments.
    """
    # Empty segments are removed first so optional pieces such as the bus suffix
    # do not leave dangling separators in the final visible label.
    kept_parts: List[str] = list()

    part: str
    for part in parts:
        clean_part: str = str(part).strip()
        if clean_part != "":
            kept_parts.append(clean_part)
        else:
            pass

    return " - ".join(kept_parts)


def _normalize_parameter_name(name: str) -> str:
    """
    Normalize one parameter name for tolerant matching.

    :param name: Raw parameter name.
    :return: Normalized parameter name.

    Some dynamic templates expose semantically identical parameters through
    slightly different symbolic names depending on the template family or the
    wrapper block. Normalizing the name allows the parameter plot resolver to
    match those aliases without changing the visible user-facing label.
    """
    normalized_name: str = str(name).strip().lower()
    normalized_name = normalized_name.replace("_", "")
    return normalized_name


def _parameter_name_matches(candidate_name: str, requested_name: str) -> bool:
    """
    Compare two parameter names using VeraGrid parameter alias rules.

    :param candidate_name: Name found in the live model block.
    :param requested_name: Name requested by the plot entry.
    :return: ``True`` when both names identify the same parameter.

    Dynamic parameter labels may differ between visible GUI aliases and the
    symbolic names kept inside templates. The resolver therefore accepts either
    direct normalized equality or the legacy display alias derived from the
    canonical symbolic name.
    """
    normalized_candidate_name: str = _normalize_parameter_name(candidate_name)
    normalized_requested_name: str = _normalize_parameter_name(requested_name)
    if normalized_candidate_name == normalized_requested_name:
        return True
    else:
        alias_name: str = _build_parameter_alias_name(candidate_name)
        normalized_alias_name: str = _normalize_parameter_name(alias_name)
        if normalized_alias_name == normalized_requested_name:
            return True
        else:
            # Some parameter entries still carry the visible source-tree label in
            # ``variable_custom_name`` while older fixtures or fallback paths may
            # store the canonical name in ``variable_name``. A final prefix match
            # keeps semantically identical simple names such as ``omega`` and
            # ``omega_ref`` aligned without introducing uid-based identity.
            if normalized_requested_name.startswith(normalized_candidate_name):
                return True
            else:
                if normalized_candidate_name.startswith(normalized_requested_name):
                    return True
                else:
                    return False


def _build_parameter_alias_name(parameter_name: str) -> str:
    """
    Build one user-facing parameter alias from a canonical symbolic name.

    :param parameter_name: Canonical symbolic parameter name.
    :return: Display alias used in the tree when a legacy UI alias exists.

    Some VeraGrid dynamic models historically expose load power-reference
    parameters with ``I`` inserted after the leading ``P``/``Q`` in the GUI.
    The plotting system keeps that visible label for continuity while storing
    the canonical symbolic name separately for later resolution.
    """
    clean_parameter_name: str = str(parameter_name)
    if clean_parameter_name == "Pl0":
        return "PI0"
    else:
        if clean_parameter_name == "Ql0":
            return "QI0"
        else:
            return clean_parameter_name


# def _build_parameter_canonical_name_from_display(parameter_name: str) -> str:
#     """
#     Build one canonical symbolic parameter name from a display alias.
#
#     :param parameter_name: User-facing parameter name.
#     :return: Canonical symbolic parameter name candidate.
#
#     This helper reverses the small set of legacy GUI aliases so entries loaded
#     from older projects or created through display labels still resolve against
#     the symbolic names stored inside model blocks and exported results maps.
#     """
#     clean_parameter_name: str = str(parameter_name)
#     if clean_parameter_name == "PI0":
#         return "Pl0"
#     else:
#         if clean_parameter_name == "QI0":
#             return "Ql0"
#         else:
#             return clean_parameter_name


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


def _build_relative_time_axis(time_array: np.ndarray | pd.DatetimeIndex) -> np.ndarray:
    """
    Build a relative floating-point time axis that starts at zero.

    :param time_array: Absolute simulation time samples.
    :return: Relative time samples in seconds as evenly spaced floats whenever the input is evenly spaced.

    The dynamic results drivers store simulation time as a datetime-like array.
    Matplotlib then formats those absolute timestamps as wall-clock values, which
    hides the simulation progression when the timestamps are anchored close to one
    day boundary. The plotting code only needs elapsed simulation time, so this
    helper converts every sample into seconds relative to the first sample.
    """
    # The plotting path requires a NumPy array so downstream code can pass the
    # x-axis directly to Matplotlib without any additional conversions.
    resolved_time_array: np.ndarray = np.asarray(time_array)

    # The result must preserve the original sample count so the x-axis always
    # stays aligned with every y-axis simulation sample.
    sample_count: int = int(len(resolved_time_array))
    relative_time_axis: np.ndarray = np.empty(sample_count, dtype=float)

    # The empty-array branch is explicit so the function stays total and avoids
    # indexing errors when a caller provides no samples.
    if sample_count == 0:
        return relative_time_axis
    else:
        pass

    # Datetime indexes expose their storage as integer nanoseconds through
    # ``asi8``. Converting to elapsed seconds here prevents Matplotlib from
    # showing a scientific-notation nanosecond axis such as ``1e9``.
    if isinstance(resolved_time_array, pd.DatetimeIndex):
        time_ns: np.ndarray = np.asarray(resolved_time_array.asi8, dtype=np.int64)
        relative_time_axis[:] = (time_ns - time_ns[0]) * 1e-9
    else:
        # NumPy datetime64 arrays can appear after generic array conversions.
        # They also encode timestamps in nanoseconds, so they must be normalized
        # through integer nanoseconds before converting to elapsed seconds.
        if np.issubdtype(resolved_time_array.dtype, np.datetime64):
            time_ns = resolved_time_array.astype("datetime64[ns]").astype(np.int64)
            relative_time_axis[:] = (time_ns - time_ns[0]) * 1e-9
        else:
            # Some tests and fallback code paths already use numeric arrays.
            # When those values are very large, they are almost certainly raw
            # nanoseconds from a converted datetime array, so they are scaled to
            # seconds after subtracting the first sample. Small values are kept
            # as seconds directly.
            numeric_time_array: np.ndarray = np.asarray(resolved_time_array, dtype=float)
            relative_time_axis[:] = numeric_time_array - float(numeric_time_array[0])

            if sample_count > 1:
                relative_span_seconds: float = float(relative_time_axis[-1])
                if relative_span_seconds > 1.0e6:
                    relative_time_axis[:] = relative_time_axis[:] * 1.0e-9
                else:
                    pass
            else:
                pass

    return relative_time_axis


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


def collect_dynamic_model_plot_parameters(model: Block) -> List[DynamicPlotParameter]:
    """
    Collect plottable parameters from one dynamic-model block hierarchy.

    :param model: Assigned dynamic model block.
    :return: Ordered plottable parameters without duplicated names.

    Parameters can be surfaced through ``api_obj_mapping`` or ``event_dict``.
    The UI must merge both sources while preserving deterministic order and
    without duplicating a parameter that appears in both structures.
    """
    ordered_parameters: List[DynamicPlotParameter] = list()
    seen_parameter_names: Set[str] = set()
    block_item: Block

    # ``api_obj_mapping`` values are the symbolic parameters tied to API-side
    # properties, so they are listed first to preserve the model's natural order.
    for block_item in model.get_all_blocks():
        mapped_parameter: Var | None
        for mapped_parameter in block_item.api_obj_mapping.values():
            if isinstance(mapped_parameter, Var):
                parameter_name: str = str(mapped_parameter.name)
                if parameter_name not in seen_parameter_names:
                    seen_parameter_names.add(parameter_name)
                    ordered_parameters.append(DynamicPlotParameter(
                        display_name=_build_parameter_alias_name(parameter_name),
                        canonical_name=parameter_name,
                    ))
                else:
                    pass
            else:
                pass

    # Some templates expose plottable static parameters directly in the block
    # parameter dictionary without mirroring them through ``api_obj_mapping``.
    # Those parameters must still appear in the source tree and plot workflow.
    for block_item in model.get_all_blocks():
        direct_parameter: Var
        for direct_parameter in block_item.parameters.keys():
            parameter_name = str(direct_parameter.name)
            if parameter_name not in seen_parameter_names:
                seen_parameter_names.add(parameter_name)
                ordered_parameters.append(DynamicPlotParameter(
                    display_name=_build_parameter_alias_name(parameter_name),
                    canonical_name=parameter_name,
                ))
            else:
                pass

    # ``event_dict`` keys identify parameters that can change due to events.
    # These are appended only when they were not already exposed by the API map.
    for block_item in model.get_all_blocks():
        event_parameter: Var
        for event_parameter in block_item.event_dict.keys():
            parameter_name = str(event_parameter.name)
            if parameter_name not in seen_parameter_names:
                seen_parameter_names.add(parameter_name)
                ordered_parameters.append(DynamicPlotParameter(
                    display_name=_build_parameter_alias_name(parameter_name),
                    canonical_name=parameter_name,
                ))
            else:
                pass

    return ordered_parameters


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


def _dynamic_event_time_sort_key(event_item: RmsEvent | EmtEvent) -> tuple[float, float]:
    """
    Build the chronological sort key for one dynamic event.

    :param event_item: RMS or EMT event.
    :return: Tuple containing start and end times.

    Event reconstruction must process the updates in deterministic temporal
    order. A dedicated key function keeps that ordering logic explicit and avoids
    embedding anonymous sorting logic inside the caller.
    """
    end_time_value: float
    if event_item.end_time is not None:
        end_time_value = float(event_item.end_time)
    else:
        end_time_value = float(event_item.time)

    return float(event_item.time), end_time_value


def _sort_dynamic_events_by_time(events: Sequence[RmsEvent | EmtEvent]) -> List[RmsEvent | EmtEvent]:
    """
    Sort dynamic events by start time and end time.

    :param events: Unordered dynamic events.
    :return: Sorted dynamic events.

    Parameter reconstruction must apply events in the same chronological order
    used by the simulation logic. Sorting by start time first, and then by end
    time, makes the event application stable and deterministic.
    """
    sorted_events: List[RmsEvent | EmtEvent] = sorted(
        events,
        key=_dynamic_event_time_sort_key,
    )
    return sorted_events


def _get_dynamic_event_parameter_name(event_item: RmsEvent | EmtEvent) -> str | None:
    """
    Resolve the canonical parameter name referenced by one dynamic event.

    :param event_item: RMS or EMT event.
    :return: Canonical parameter name, or ``None``.

    Dynamic events point to symbolic parameters through ``event.parameter``.
    The plotting layer needs the canonical symbolic name so it can compare the
    event target against the persistent plot entry parameter identity.
    """
    if isinstance(event_item.parameter, Var):
        return str(event_item.parameter.name)
    else:
        return None


def _dynamic_event_matches_parameter_entry(event_item: RmsEvent | EmtEvent,
                                           entry: DynamicPlotEntry) -> bool:
    """
    Check whether one dynamic event affects one parameter plot entry.

    :param event_item: RMS or EMT event.
    :param entry: Persistent parameter plot entry.
    :return: ``True`` when the event targets the plotted parameter.

    The reconstruction path must only consume events that belong to the same
    device and symbolic parameter selected in the plot entry. Matching is kept
    tolerant through the existing parameter alias rules.
    """
    parameter_name: str | None = _get_dynamic_event_parameter_name(event_item=event_item)
    if parameter_name is not None:
        if event_item.device is not None:
            event_device_idtag: str = str(event_item.device.idtag)
            if event_device_idtag == str(entry.device_idtag):
                return _parameter_name_matches(candidate_name=parameter_name,
                                               requested_name=str(entry.variable_name))
            else:
                return False
        else:
            return False
    else:
        return False


def _get_dynamic_events_for_plot_entry(circuit: MultiCircuit,
                                       entry: DynamicPlotEntry) -> List[RmsEvent | EmtEvent]:
    """
    Get the dynamic events that affect one parameter plot entry.

    :param circuit: Circuit that owns the dynamic event assets.
    :param entry: Persistent parameter plot entry.
    :return: Ordered matching events.

    Parameter plotting must follow only the events from the selected event
    group. The handler therefore resolves the matching group first and only then
    filters its events by device and parameter identity.
    """
    matching_events: List[RmsEvent | EmtEvent] = list()
    group_events: List[tuple[RmsEventsGroup | EmtEventsGroup, List[RmsEvent | EmtEvent]]] = list()

    if entry.simulation_type == PlotSimulationType.RMS:
        rms_group: RmsEventsGroup
        rms_events: List[RmsEvent]
        for rms_group, rms_events in circuit.get_rms_event_by_groups():
            group_events.append((rms_group, list(rms_events)))
    else:
        if entry.simulation_type == PlotSimulationType.EMT:
            emt_group: EmtEventsGroup
            emt_events: List[EmtEvent]
            for emt_group, emt_events in circuit.get_emt_event_by_groups():
                group_events.append((emt_group, list(emt_events)))
        else:
            pass

    group_item: RmsEventsGroup | EmtEventsGroup
    event_list: List[RmsEvent | EmtEvent]
    for group_item, event_list in group_events:
        matches_group_idtag: bool = str(group_item.idtag) == str(entry.event_group_idtag) and str(entry.event_group_idtag) != ""
        matches_group_name: bool = str(group_item.name) == str(entry.event_group_name) and str(entry.event_group_name) != ""

        if matches_group_idtag or matches_group_name:
            event_item: RmsEvent | EmtEvent
            for event_item in event_list:
                if _dynamic_event_matches_parameter_entry(event_item=event_item, entry=entry):
                    matching_events.append(event_item)
                else:
                    pass
        else:
            pass

    return _sort_dynamic_events_by_time(events=matching_events)


def _apply_step_event_to_parameter_series(time_axis: np.ndarray,
                                          y_values: np.ndarray,
                                          event_item: RmsEvent | EmtEvent) -> None:
    """
    Apply one step event to one parameter time series in place.

    :param time_axis: Relative simulation time axis.
    :param y_values: Mutable parameter values aligned with ``time_axis``.
    :param event_item: Dynamic event to apply.
    :return: None.

    A step event replaces the parameter value from the event time onward. The
    whole suffix must be updated so later events start from the correct already-
    modified trace.
    """
    event_time: float = float(event_item.time)
    event_value: float = float(event_item.value)
    affected_mask: np.ndarray = time_axis >= event_time
    y_values[affected_mask] = event_value


def _apply_ramp_event_to_parameter_series(time_axis: np.ndarray,
                                          y_values: np.ndarray,
                                          event_item: RmsEvent | EmtEvent) -> None:
    """
    Apply one ramp event to one parameter time series in place.

    :param time_axis: Relative simulation time axis.
    :param y_values: Mutable parameter values aligned with ``time_axis``.
    :param event_item: Dynamic event to apply.
    :return: None.

    A ramp event must preserve the parameter value before the ramp start, blend
    linearly toward the target during the ramp interval, and then hold the final
    value afterwards. Updating the array in place keeps the event composition
    simple and lets later events build on the already-applied earlier ones.
    """
    start_time: float = float(event_item.time)
    end_time: float | None = event_item.end_time

    if end_time is not None:
        if float(end_time) > start_time:
            pass
        else:
            _apply_step_event_to_parameter_series(time_axis=time_axis,
                                                  y_values=y_values,
                                                  event_item=event_item)
            return
    else:
        _apply_step_event_to_parameter_series(time_axis=time_axis,
                                              y_values=y_values,
                                              event_item=event_item)
        return

    resolved_end_time: float = float(end_time)
    pre_start_mask: np.ndarray = time_axis < start_time
    in_ramp_mask: np.ndarray = (time_axis >= start_time) & (time_axis < resolved_end_time)
    post_end_mask: np.ndarray = time_axis >= resolved_end_time

    if np.any(pre_start_mask):
        pass
    else:
        pass

    start_index_candidates: np.ndarray = np.nonzero(time_axis >= start_time)[0]
    start_value: float
    if len(start_index_candidates) > 0:
        start_index: int = int(start_index_candidates[0])
        start_value = float(y_values[start_index])
    else:
        if len(y_values) > 0:
            start_value = float(y_values[-1])
        else:
            start_value = float(event_item.value)

    if np.any(in_ramp_mask):
        ramp_times: np.ndarray = time_axis[in_ramp_mask]
        ramp_progress: np.ndarray = (ramp_times - start_time) / (resolved_end_time - start_time)
        y_values[in_ramp_mask] = start_value + ramp_progress * (float(event_item.value) - start_value)
    else:
        pass

    if np.any(post_end_mask):
        y_values[post_end_mask] = float(event_item.value)
    else:
        pass


def _build_parameter_plot_data_from_events(circuit: MultiCircuit,
                                           entry: DynamicPlotEntry,
                                           time_axis: np.ndarray,
                                           base_value: float) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Build parameter plot arrays by replaying matching dynamic events.

    :param circuit: Circuit that owns the event assets.
    :param entry: Persistent parameter plot entry.
    :param time_axis: Relative simulation time axis.
    :param base_value: Initial parameter value before any event happens.
    :return: Plot arrays, or ``None`` when no matching events exist.

    The results containers only expose one scalar snapshot for parameters. When
    a parameter is changed by events, the GUI must rebuild the visible trace from
    the declarative event definitions so step and ramp transitions appear in the
    parameter plot.
    """
    matching_events: List[RmsEvent | EmtEvent] = _get_dynamic_events_for_plot_entry(circuit=circuit, entry=entry)
    if len(matching_events) > 0:
        y_values: np.ndarray = np.empty(len(time_axis), dtype=float)
        y_values[:] = float(base_value)

        event_item: RmsEvent | EmtEvent
        for event_item in matching_events:
            if event_item.transition_type == DynamicEventTransitionType.Step:
                _apply_step_event_to_parameter_series(time_axis=time_axis,
                                                      y_values=y_values,
                                                      event_item=event_item)
            else:
                if event_item.transition_type == DynamicEventTransitionType.Ramp:
                    _apply_ramp_event_to_parameter_series(time_axis=time_axis,
                                                          y_values=y_values,
                                                          event_item=event_item)
                else:
                    _apply_step_event_to_parameter_series(time_axis=time_axis,
                                                          y_values=y_values,
                                                          event_item=event_item)

        return time_axis, y_values
    else:
        return None


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
                                           simulation_type: PlotSimulationType | str) -> Dict[DeviceType, Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]]:
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

    tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]] = dict()

    device: ALL_DEV_TYPES
    for device in circuit.get_all_elements_iter():
        include_device: bool = isinstance(device, DynamicDevice)
        if isinstance(device, DynamicBusDevice):
            include_device = True
        else:
            pass

        if include_device:
            variables: List[Var] = list()
            parameters: List[DynamicPlotParameter] = list()

            model_block: Block = _get_pre_simulation_block(device=device, simulation_type=resolved_simulation_type)
            variables.extend(collect_dynamic_model_plot_variables(model=model_block,
                                                                  simulation_type=resolved_simulation_type))
            parameters.extend(collect_dynamic_model_plot_parameters(model=model_block))

            if len(variables) > 0 or len(parameters) > 0:
                devices_by_type: Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection] = tree_data.get(device.device_type, dict())
                devices_by_type[device] = DynamicDeviceEntryCollection(variables=variables, parameters=parameters)
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


def _get_runtime_parameter_scalar_from_block(model: Block,
                                             parameter_name: str) -> float | None:
    """
    Resolve one scalar parameter value from a dynamic-model block hierarchy.

    :param model: Dynamic model block hierarchy.
    :param parameter_name: Parameter name requested by the plot entry.
    :return: Scalar parameter value, or ``None`` when unavailable.

    The first implementation supports static scalar parameters only. A later
    extension can reconstruct event-dependent parameter evolution without
    changing the broader plotting workflow.
    """
    requested_parameter_name: str = _normalize_parameter_name(parameter_name)

    block_item: Block
    for block_item in model.get_all_blocks():
        mapped_parameter: Var | None
        for mapped_parameter in block_item.api_obj_mapping.values():
            if isinstance(mapped_parameter, Var):
                if _parameter_name_matches(candidate_name=str(mapped_parameter.name), requested_name=parameter_name):
                    mapped_value: object = block_item.parameters.get(mapped_parameter, None)
                    if isinstance(mapped_value, (int, float, np.integer, np.floating)):
                        return float(mapped_value)
                    else:
                        return None
                else:
                    pass
            else:
                pass

        direct_parameter: Var
        for direct_parameter in block_item.parameters.keys():
            if _parameter_name_matches(candidate_name=str(direct_parameter.name), requested_name=parameter_name):
                direct_value: object = block_item.parameters.get(direct_parameter, None)
                if isinstance(direct_value, (int, float, np.integer, np.floating)):
                    return float(direct_value)
                else:
                    if isinstance(direct_value, Const):
                        if isinstance(direct_value.value, (int, float, np.integer, np.floating)):
                            return float(direct_value.value)
                        else:
                            return None
                    else:
                        return None
            else:
                pass

        # Event parameters often carry the live scalar value directly in
        # ``event_dict`` as a ``Const``. This path is required for models such
        # as RMS loads where the parameter is not mirrored into ``parameters``.
        event_parameter: Var
        for event_parameter in block_item.event_dict.keys():
            if _parameter_name_matches(candidate_name=str(event_parameter.name), requested_name=parameter_name):
                event_value: object = block_item.event_dict.get(event_parameter, None)
                if isinstance(event_value, Const):
                    if isinstance(event_value.value, (int, float, np.integer, np.floating)):
                        return float(event_value.value)
                    else:
                        init_value: object = block_item.init_eqs.get(event_parameter, None)
                        if isinstance(init_value, Const):
                            if isinstance(init_value.value, (int, float, np.integer, np.floating)):
                                return float(init_value.value)
                            else:
                                return None
                        else:
                            return None
                else:
                    if isinstance(event_value, (int, float, np.integer, np.floating)):
                        return float(event_value)
                    else:
                        return None
            else:
                pass

        init_parameter: Var
        for init_parameter in block_item.init_eqs.keys():
            if _parameter_name_matches(candidate_name=str(init_parameter.name), requested_name=parameter_name):
                init_value = block_item.init_eqs.get(init_parameter, None)
                if isinstance(init_value, Const):
                    if isinstance(init_value.value, (int, float, np.integer, np.floating)):
                        return float(init_value.value)
                    else:
                        return None
                else:
                    return None
            else:
                pass

    return None




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


class DynamicsPlotGroup(DynamicPlotGroupDefinition):
    """
    Group of plot-variable references selected by the user.

    The group stores runtime resolved series when available and falls back to
    persistent unresolved plot entries when no matching results series exists.
    Legacy ``Var`` entries are still tolerated so older tests and callers keep
    working.
    """

    __slots__ = tuple()

    def __init__(self, name: str):
        """
        Build the plot group.

        :param name: Name shown in the plots tree.
        """
        DynamicPlotGroupDefinition.__init__(self, name=name, mode=DynamicPlotMode.TIME_SERIES)

    def get_name(self) -> str:
        """
        Get the plot-group name.

        :return: Plot-group name.
        """
        return DynamicPlotGroupDefinition.get_name(self)

    def set_name(self, name: str) -> None:
        """
        Set the plot-group name.

        :param name: New group name.
        :return: Nothing.
        """
        DynamicPlotGroupDefinition.set_name(self, name=name)

    def get_series(self) -> List[DynamicResultSeries | DynamicPlotEntry | Var]:
        """
        Get the stored plot-variable references.

        :return: Entries in insertion order.
        """
        return DynamicPlotGroupDefinition.get_series(self)

    def get_vars(self) -> List[Var]:
        """
        Get the current underlying variables stored in the group.

        :return: Variable list kept for compatibility with older tests and callers.
        """
        return DynamicPlotGroupDefinition.get_vars(self)

    def contains_var(self, variable: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
        """
        Check whether a series already belongs to the group.

        :param variable: Series to inspect.
        :return: ``True`` when the variable is already present.
        """
        return DynamicPlotGroupDefinition.contains_var(self, variable=variable)

    def add_var(self, variable: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
        """
        Add a variable to the group.

        :param variable: Variable to add.
        :return: ``True`` when the variable was inserted.
        """
        return DynamicPlotGroupDefinition.add_entry(self, variable=variable, role=DynamicPlotEntryRole.CURVE)

    def remove_var(self, variable: DynamicResultSeries | DynamicPlotEntry | Var) -> bool:
        """
        Remove a variable from the group.

        :param variable: Variable to remove.
        :return: ``True`` when the variable was present and removed.
        """
        return DynamicPlotGroupDefinition.remove_var(self, variable=variable)


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

    def create_group(self, name: str, mode: DynamicPlotMode = DynamicPlotMode.TIME_SERIES) -> bool:
        """
        Create a new plot group.

        :param name: Requested group name.
        :param mode: Plotting mode for the new group.
        :return: ``True`` when the group was created.
        """
        clean_name: str = name.strip()
        if clean_name == "":
            return False
        else:
            existing_group: DynamicsPlotGroup | None = self.get_group(name=clean_name)
            if existing_group is None:
                created_group: DynamicsPlotGroup = DynamicsPlotGroup(name=clean_name)
                created_group.set_mode(mode=mode)
                self._groups.append(created_group)
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

    __slots__ = ("_var_role", "_mime_type", "_state_key_role")

    def __init__(self, var_role: int, mime_type: str, state_key_role: int):
        """
        Build the source dynamics tree model.

        :param var_role: Qt role that stores the ``Var`` object in leaf nodes.
        :param mime_type: Mime type used during drag-and-drop.
        """
        QtGui.QStandardItemModel.__init__(self)
        self._var_role: int = var_role
        self._mime_type: str = mime_type
        self._state_key_role: int = state_key_role

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

    def __init__(self, handler: Union["DynamicsResultsHandler", _GenericDynamicsPlotsDropHandler]):
        """
        Build the plots tree model.

        :param handler: Dynamics-results handler that owns the plot-group state.
        """
        QtGui.QStandardItemModel.__init__(self)
        self._handler: Union["DynamicsResultsHandler", _GenericDynamicsPlotsDropHandler] = handler

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
                drop_target_role: int | None = None
                if isinstance(self._handler, DynamicsResultsHandler):
                    drop_target_role = self._handler.get_drop_target_role()
                else:
                    drop_target_role = None

                if drop_target_role is not None:
                    drop_target_data: object = item.data(drop_target_role)
                else:
                    drop_target_data = None
                if isinstance(group_name_data, str) or isinstance(drop_target_data, DynamicPlotDropTargetKind):
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

    def canDropMimeData(self,
                        data: QtCore.QMimeData,
                        action: QtCore.Qt.DropAction,
                        row: int,
                        column: int,
                        parent: QtCore.QModelIndex) -> bool:
        """
        Check whether one drag payload can be dropped on the requested target.

        :param data: Drag payload.
        :param action: Requested drop action.
        :param row: Drop row.
        :param column: Drop column.
        :param parent: Drop parent index.
        :return: ``True`` when the model can resolve a target plot group.
        """
        del row
        del column

        # Qt may offer the drop either on the group row itself or on a child
        # row underneath that group. Accepting both keeps the GUI behavior
        # stable across view styles and drop-indicator positions.
        if action == QtCore.Qt.DropAction.IgnoreAction:
            return True
        else:
            pass

        if data.hasFormat(self._handler.get_drag_mime_type()):
            if isinstance(self._handler, DynamicsResultsHandler):
                resolved_drop_group_name: str | None = self._handler.get_plot_group_name_from_index(index=parent)
            else:
                # Fallback handlers expose their own drop-index resolver.
                resolved_drop_group_name = self._handler.get_group_name_from_drop_index(index=parent)
            if resolved_drop_group_name is not None:
                return True
            else:
                return False
        else:
            return False

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
                if isinstance(self._handler, DynamicsResultsHandler):
                    group_name: str | None = self._handler.get_plot_group_name_from_index(index=parent)
                else:
                    group_name = self._handler.get_group_name_from_drop_index(index=parent)
                if group_name is not None:
                    if series_key is not None:
                        if isinstance(self._handler, DynamicsResultsHandler):
                            return self._handler.add_series_to_group_from_drop(group_name=group_name,
                                                                              series_key=series_key,
                                                                              drop_index=parent)
                        else:
                            return self._handler.add_series_to_group(group_name=group_name, series_key=series_key)
                    else:
                        candidate: DynamicPlotCandidate | None = self._handler.get_candidate_from_payload(payload=payload_text)
                        if candidate is not None:
                            if isinstance(self._handler, DynamicsResultsHandler):
                                return self._handler.add_candidate_to_group_from_drop(group_name=group_name,
                                                                                     candidate=candidate,
                                                                                     drop_index=parent)
                            else:
                                return self._handler.add_candidate_to_group(group_name=group_name, candidate=candidate)
                        else:
                            return False
                else:
                    return False
            else:
                return False


def build_dynamics_tree_model(tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]],
                              var_role: int,
                              mime_type: str,
                              state_key_role: int,
                              series_by_var_uid: Dict[int, List[DynamicResultSeries | DynamicPlotCandidate]],
                              candidates_by_parameter_name: Dict[str, List[DynamicPlotCandidate]],
                              has_multiple_sources: bool) -> DynamicsDeviceTreeModel:
    """
    Build the source tree-view model for RMS/EMT dynamics results.

    :param tree_data: Hierarchical dynamics tree grouped by device type and device.
    :param var_role: Qt item-data role used to store the ``Var`` instance in leaf nodes.
    :param mime_type: Mime type exported when dragging a variable.
    :param series_by_var_uid: Source-specific selectors grouped by current variable uid.
    :param candidates_by_parameter_name: Source-specific parameter selectors grouped by parameter name.
    :param has_multiple_sources: ``True`` when multiple event-group sources must be shown.
    :return: Source tree model ready to be assigned to a QTreeView.

    The tree uses the existing device hierarchy from the results object. When a
    variable exists in multiple event groups, the variable node gets one child
    per source-specific series so the drag payload can preserve the exact source
    selected by the user.
    """
    # The source model owns the full device hierarchy and the drag payload for variable leaves.
    model: DynamicsDeviceTreeModel = DynamicsDeviceTreeModel(var_role=var_role,
                                                             mime_type=mime_type,
                                                             state_key_role=state_key_role)
    model.setHorizontalHeaderLabels(["Dynamics results"])

    # The invisible root is Qt's insertion point for first-level tree nodes.
    root_item: QtGui.QStandardItem = model.invisibleRootItem()

    device_tpe: DeviceType
    devices_data: Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]
    for device_tpe, devices_data in tree_data.items():
        # The first level groups all devices by their type so the tree remains navigable.
        device_type_item: QtGui.QStandardItem = _build_tree_item(text=_get_device_type_label(device_tpe=device_tpe))
        device_type_item.setData(
            _build_tree_state_key(node_kind=TreeStateNodeKind.DEVICE_TYPE,
                                  parts=[str(device_tpe.value)]),
            state_key_role,
        )
        _set_item_icon(item=device_type_item, icon_key=_get_device_type_label(device_tpe=device_tpe))
        root_item.appendRow(device_type_item)

        device: ALL_DEV_TYPES
        entry_collection: DynamicDeviceEntryCollection
        for device, entry_collection in devices_data.items():
            # The second level groups the variables that belong to one physical device.
            device_item: QtGui.QStandardItem = _build_tree_item(text=_get_device_label(device=device))
            device_state_id: str = _get_device_state_id(device=device)
            device_item.setData(
                _build_tree_state_key(node_kind=TreeStateNodeKind.DEVICE,
                                      parts=[str(device_tpe.value), device_state_id]),
                state_key_role,
            )
            device_type_item.appendRow(device_item)

            variables_section_item: QtGui.QStandardItem = _build_tree_item(text=DynamicEntrySection.VARIABLES)
            parameters_section_item: QtGui.QStandardItem = _build_tree_item(text=DynamicEntrySection.PARAMETERS)
            variables_section_item.setData(
                _build_tree_state_key(node_kind=TreeStateNodeKind.SECTION,
                                      parts=[str(device_tpe.value), device_state_id, DynamicEntrySection.VARIABLES]),
                state_key_role,
            )
            parameters_section_item.setData(
                _build_tree_state_key(node_kind=TreeStateNodeKind.SECTION,
                                      parts=[str(device_tpe.value), device_state_id, DynamicEntrySection.PARAMETERS]),
                state_key_role,
            )
            device_item.appendRow(variables_section_item)
            device_item.appendRow(parameters_section_item)

            variable: Var
            for variable in entry_collection.get_variables():
                variable_item: QtGui.QStandardItem = _build_tree_item(text=_get_var_label(variable=variable))
                variable_item.setData(
                    _build_tree_state_key(node_kind=TreeStateNodeKind.VARIABLE,
                                          parts=[str(device_tpe.value), device_state_id, variable.name]),
                    state_key_role,
                )
                variables_section_item.appendRow(variable_item)

                series_list: List[DynamicResultSeries | DynamicPlotCandidate] = series_by_var_uid.get(variable.uid, list())
                if has_multiple_sources:
                    series: DynamicResultSeries | DynamicPlotCandidate
                    for series in series_list:
                        source_item: QtGui.QStandardItem = _build_tree_item(
                            text=series.get_tree_leaf_label(has_multiple_sources=True)
                        )
                        source_item.setData(
                            _build_tree_state_key(node_kind=TreeStateNodeKind.SOURCE,
                                                  parts=[str(device_tpe.value),
                                                         device_state_id,
                                                         variable.name,
                                                         series.get_tree_leaf_label(has_multiple_sources=True)]),
                            state_key_role,
                        )
                        source_item.setData(series, var_role)
                        variable_item.appendRow(source_item)
                elif len(series_list) > 0:
                    variable_item.setData(series_list[0], var_role)
                else:
                    pass

            parameter: DynamicPlotParameter
            for parameter in entry_collection.get_parameters():
                parameter_item: QtGui.QStandardItem = _build_tree_item(text=parameter.get_display_name())
                parameter_item.setData(
                    _build_tree_state_key(node_kind=TreeStateNodeKind.PARAMETER,
                                          parts=[str(device_tpe.value), device_state_id, parameter.get_canonical_name()]),
                    state_key_role,
                )
                parameters_section_item.appendRow(parameter_item)

                parameter_candidate_list: List[DynamicPlotCandidate] = candidates_by_parameter_name.get(parameter.get_display_name(), list())
                if has_multiple_sources:
                        parameter_candidate: DynamicPlotCandidate
                        for parameter_candidate in parameter_candidate_list:
                            source_item = _build_tree_item(text=parameter_candidate.get_tree_leaf_label(has_multiple_sources=True))
                            source_item.setData(
                                _build_tree_state_key(node_kind=TreeStateNodeKind.SOURCE,
                                                      parts=[str(device_tpe.value),
                                                             device_state_id,
                                                             parameter.get_canonical_name(),
                                                             parameter_candidate.get_tree_leaf_label(has_multiple_sources=True)]),
                                state_key_role,
                            )
                            source_item.setData(parameter_candidate, var_role)
                            parameter_item.appendRow(source_item)
                elif len(parameter_candidate_list) > 0:
                    parameter_item.setData(parameter_candidate_list[0], var_role)
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

    __slots__ = ("results", "circuit", "dialog_parent", "plot_simulation_type",
                  "pre_simulation_mode", "tree_data", "tree_model", "proxy_model", "plots_model", "group_idx",
                  "var_role", "group_name_role", "tree_state_role", "drag_mime_type", "drop_target_role", "entry_role_role", "plot_groups", "series_by_key",
                  "series_by_var_uid", "candidates_by_parameter_name", "source_labels", "_open_plot_dialogs")

    def __init__(self,
                 results: RmsResults | EmtResults | None,
                 circuit: MultiCircuit | None = None,
                 simulation_type: PlotSimulationType | str = PlotSimulationType.RMS,
                 dialog_parent: QtWidgets.QWidget | None = None):
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
        self.dialog_parent: QtWidgets.QWidget | None = dialog_parent
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
        self.tree_state_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 302
        self.drag_mime_type: str = "application/x-veragrid-dynamics-var"
        self.drop_target_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 303
        self.entry_role_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 304

        self.group_idx: Dict[str, int] = dict()
        self.tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]] = dict()
        self.tree_model: DynamicsDeviceTreeModel | None = None
        self.series_by_key: Dict[DynamicResultSeriesKey, List[DynamicResultSeries]] = dict()
        self.series_by_var_uid: Dict[int, List[DynamicResultSeries | DynamicPlotCandidate]] = dict()
        self.candidates_by_parameter_name: Dict[str, List[DynamicPlotCandidate]] = dict()
        self.source_labels: List[str] = list()

        # Open plot windows are kept referenced so they are not garbage collected
        # while still visible; entries are pruned when the user closes them.
        self._open_plot_dialogs: List[QtWidgets.QDialog] = list()

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

    def get_tree_state_role(self) -> int:
        """
        Get the Qt role used to store semantic tree-state keys.

        :return: Item-data role for tree-state semantic keys.
        """
        return self.tree_state_role

    def get_drop_target_role(self) -> int:
        """
        Get the Qt role used to store plot-tree drop-target semantics.

        :return: Item-data role for drop-target metadata.
        """
        return self.drop_target_role

    def get_entry_role_role(self) -> int:
        """
        Get the Qt role used to store dynamic plot entry roles.

        :return: Item-data role for entry-role metadata.
        """
        return self.entry_role_role

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

    def capture_plots_tree_state(self, view: QtWidgets.QTreeView | None) -> TreeStateSnapshot | None:
        """
        Capture the current plots-tree state from one attached tree view.

        :param view: Tree view currently showing the plots model.
        :return: Captured tree state, or ``None``.
        """
        if view is not None:
            return _capture_tree_view_state(view=view, model=self.plots_model, key_role=self.tree_state_role)
        else:
            return None

    def restore_plots_tree_state(self,
                                 view: QtWidgets.QTreeView | None,
                                 snapshot: TreeStateSnapshot | None) -> None:
        """
        Restore one captured plots-tree state into an attached tree view.

        :param view: Tree view currently showing the plots model.
        :param snapshot: Captured tree state.
        :return: None.
        """
        if view is not None:
            if snapshot is not None:
                _restore_tree_view_state(view=view,
                                         model=self.plots_model,
                                         key_role=self.tree_state_role,
                                         snapshot=snapshot)
            else:
                pass
        else:
            pass

    def _find_attached_plots_tree_view(self) -> QtWidgets.QTreeView | None:
        """
        Find the currently attached tree view that shows the plots model.

        :return: Attached plots tree view, or ``None``.
        """
        if self.dialog_parent is not None:
            attached_views: List[QtWidgets.QTreeView] = self.dialog_parent.findChildren(QtWidgets.QTreeView)
            attached_view: QtWidgets.QTreeView
            for attached_view in attached_views:
                if attached_view.model() is self.plots_model:
                    return attached_view
                else:
                    pass
            return None
        else:
            return None

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
                created_plot: DynamicPlot = DynamicPlot(name=group_name,
                                                        simulation_type=self.plot_simulation_type,
                                                        mode=DynamicPlotMode.TIME_SERIES)
                self.circuit.add_dynamic_plot(obj=created_plot)
                return created_plot
            else:
                return None

    def _get_asset_plot_mode(self, plot_asset: DynamicPlot) -> DynamicPlotMode:
        """
        Get the persisted plotting mode for one asset.

        :param plot_asset: Persistent plot asset.
        :return: Plotting mode.
        """
        return plot_asset.mode

    def _set_asset_plot_mode(self, plot_asset: DynamicPlot, mode: DynamicPlotMode) -> None:
        """
        Persist the plotting mode for one asset.

        :param plot_asset: Persistent plot asset.
        :param mode: Plotting mode.
        :return: None.
        """
        plot_asset.mode = mode

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

        return self._build_runtime_series_binding_signature_from_parts(
            simulation_type=self.plot_simulation_type,
            event_group_identity=event_group_identity,
            device_type=key._device_type,
            device_idtag=key._device_idtag,
            variable_name=series.get_variable_label(),
            result_path_kind=str(key._result_path.split(":", 1)[0]),
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

    def _build_runtime_series_binding_signature_from_parts(self,
                                                           simulation_type: PlotSimulationType,
                                                           event_group_identity: str,
                                                           device_type: DeviceType,
                                                           device_idtag: str,
                                                           variable_name: str,
                                                           result_path_kind: str) -> tuple[str, str, str, str, str, str]:
        """
        Build one semantic binding signature from explicit values.

        :param simulation_type: Simulation family identifier.
        :param event_group_identity: Event-group idtag or fallback name.
        :param device_type: Device type that owns the signal.
        :param device_idtag: Device identifier.
        :param variable_name: Variable name.
        :param result_path_kind: Result namespace identifier.
        :return: Binding signature used for semantic rebinding.
        """
        return (
            str(simulation_type.value),
            str(event_group_identity),
            str(device_type.value),
            str(device_idtag),
            str(variable_name),
            str(result_path_kind),
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

                # Pre-simulation persistent entries are keyed by the symbolic
                # variable name stored in the asset, while runtime rebinding may
                # only have the current results label available. Keeping both
                # names in the semantic index lets old and new assets rebind
                # without guessing or depending on runtime payload availability.
                runtime_variable_name: str = series.get_var().name
                if runtime_variable_name != series.get_variable_label():
                    alternate_signature: tuple[str, str, str, str, str, str] = (
                        self._build_runtime_series_binding_signature_from_parts(
                            simulation_type=self.plot_simulation_type,
                            event_group_identity=signature[1],
                            device_type=series.get_key()._device_type,
                            device_idtag=series.get_key()._device_idtag,
                            variable_name=runtime_variable_name,
                            result_path_kind=str(series.get_key()._result_path.split(":", 1)[0]),
                        )
                    )
                    alternate_candidates: List[DynamicResultSeries] = series_by_signature.get(alternate_signature, list())
                    alternate_candidates.append(series)
                    series_by_signature[alternate_signature] = alternate_candidates
                else:
                    pass

        return series_by_signature

    def _insert_reloaded_entry_into_group(self,
                                          group: DynamicsPlotGroup,
                                          entry: DynamicResultSeries | DynamicPlotEntry | Var,
                                          role: DynamicPlotEntryRole) -> None:
        """
        Insert one reloaded persistent entry into the runtime group while preserving XY roles.

        :param group: Runtime plot group being rebuilt.
        :param entry: Resolved runtime series or unresolved persistent entry.
        :param role: Persisted role assigned to the entry.
        :return: None.
        """
        if group.get_mode() == DynamicPlotMode.XY:
            target_role: DynamicPlotEntryRole = role
            if target_role == DynamicPlotEntryRole.CURVE:
                existing_x_entry: DynamicResultSeries | DynamicPlotEntry | Var | None = group.get_entry_for_role(role=DynamicPlotEntryRole.X_AXIS)
                if existing_x_entry is None:
                    target_role = DynamicPlotEntryRole.X_AXIS
                else:
                    target_role = DynamicPlotEntryRole.Y_AXIS
            else:
                pass

            group.replace_entry_for_role(variable=entry, role=target_role)
        else:
            group.add_var(variable=entry)

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

    def _build_candidate_with_event_group(self,
                                          candidate: DynamicPlotCandidate,
                                          group_asset: RmsEventsGroup | EmtEventsGroup) -> DynamicPlotCandidate:
        """
        Rebuild one candidate so it targets the provided event-group asset.

        :param candidate: Candidate produced from the pre-simulation tree metadata.
        :param group_asset: Existing or newly created event-group asset.
        :return: Candidate rebound to the selected event group.
        """
        # The dragged variable identity stays the same, but the persistent plot
        # entry must store the canonical group idtag/name from the circuit asset
        # that will own the future simulation case.
        updated_candidate: DynamicPlotCandidate = DynamicPlotCandidate(
            simulation_type=candidate._simulation_type,
            entry_kind=candidate.get_entry_kind(),
            event_group_idtag=str(group_asset.idtag),
            event_group_name=str(group_asset.name),
            device_type=candidate._device_type,
            device_idtag=candidate._device_idtag,
            device_label=candidate._device_label,
            bus_label=candidate._bus_label,
            variable_name=candidate._variable_name,
            result_path_kind=candidate._result_path_kind,
            variable_custom_name=_join_plot_label_parts([
                candidate._variable_name,
                candidate._device_label,
                candidate._bus_label,
                str(group_asset.name),
            ]),
            var=candidate.get_var(),
            parameter=candidate.get_parameter(),
        )
        return updated_candidate

    def _ensure_event_group_for_candidate(self,
                                          candidate: DynamicPlotCandidate) -> DynamicPlotCandidate | None:
        """
        Ensure that one event group exists for a pre-simulation drop candidate.

        :param candidate: Candidate selected from the pre-simulation source tree.
        :return: Candidate bound to a valid event-group asset, or ``None`` when cancelled.
        """
        if self.circuit is not None:
            group_asset: RmsEventsGroup | EmtEventsGroup | None = ensure_dynamic_plot_event_group(
                circuit=self.circuit,
                simulation_type=candidate._simulation_type,
                parent=self.dialog_parent,
            )
            if group_asset is not None:
                # Rebuilding the full pre-simulation source tree here collapses
                # the user's current tree expansion during the drag workflow.
                # The dropped candidate only needs the canonical event-group
                # identity, so the full source-tree refresh is deferred.
                return self._build_candidate_with_event_group(candidate=candidate, group_asset=group_asset)
            else:
                return None
        else:
            return None

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

    def _build_pre_simulation_candidate_index(self) -> tuple[Dict[int, List[DynamicPlotCandidate]], Dict[str, List[DynamicPlotCandidate]]]:
        """
        Build the draggable candidate index for the pre-simulation source tree.

        :return: Pair of candidate indexes grouped by variable uid and parameter name.
        """
        candidates_by_var_uid: Dict[int, List[DynamicPlotCandidate]] = dict()
        candidates_by_parameter_name: Dict[str, List[DynamicPlotCandidate]] = dict()
        group_assets: Sequence[RmsEventsGroup | EmtEventsGroup] = self._get_pre_simulation_group_assets()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]
        for device_tpe, devices_data in self.tree_data.items():
            device: ALL_DEV_TYPES
            entry_collection: DynamicDeviceEntryCollection
            for device, entry_collection in devices_data.items():
                if isinstance(device, (DynamicDevice, DynamicBusDevice)):
                    device_label: str = _get_device_label(device=device)
                    bus_label: str = _get_device_bus_label(device=device)
                    variable: Var
                    for variable in entry_collection.get_variables():
                        result_path_kind: str = self._get_pre_simulation_result_path_kind(device=device, variable=variable)
                        entries: List[DynamicPlotCandidate] = candidates_by_var_uid.get(variable.uid, list())
                        if len(group_assets) > 0:
                            group_asset: RmsEventsGroup | EmtEventsGroup
                            for group_asset in group_assets:
                                candidate: DynamicPlotCandidate = DynamicPlotCandidate(
                                    simulation_type=self.plot_simulation_type,
                                    entry_kind=DynamicPlotEntryKind.VARIABLE,
                                    event_group_idtag=str(group_asset.idtag),
                                    event_group_name=str(group_asset.name),
                                    device_type=device_tpe,
                                    device_idtag=str(device.idtag),
                                    device_label=device_label,
                                    bus_label=bus_label,
                                    variable_name=variable.name,
                                    result_path_kind=result_path_kind,
                                    variable_custom_name=_join_plot_label_parts([
                                        variable.name,
                                        device_label,
                                        bus_label,
                                        str(group_asset.name),
                                    ]),
                                    var=variable,
                                    parameter=None,
                                )
                                entries.append(candidate)
                        else:
                            # A placeholder candidate keeps the variable draggable
                            # before any event group exists. The drop path then
                            # creates the real RMS/EMT event group and rewrites
                            # this candidate with the canonical group identity.
                            candidate = DynamicPlotCandidate(
                                simulation_type=self.plot_simulation_type,
                                entry_kind=DynamicPlotEntryKind.VARIABLE,
                                event_group_idtag="",
                                event_group_name="",
                                device_type=device_tpe,
                                device_idtag=str(device.idtag),
                                device_label=device_label,
                                bus_label=bus_label,
                                variable_name=variable.name,
                                result_path_kind=result_path_kind,
                                variable_custom_name=_join_plot_label_parts([
                                    variable.name,
                                    device_label,
                                    bus_label,
                                ]),
                                var=variable,
                                parameter=None,
                            )
                            entries.append(candidate)
                        candidates_by_var_uid[variable.uid] = entries

                    parameter: DynamicPlotParameter
                    for parameter in entry_collection.get_parameters():
                        parameter_entries: List[DynamicPlotCandidate] = candidates_by_parameter_name.get(parameter.get_display_name(), list())
                        if len(group_assets) > 0:
                            for group_asset in group_assets:
                                parameter_candidate: DynamicPlotCandidate = _build_runtime_parameter_candidate(
                                    simulation_type=self.plot_simulation_type,
                                    device_tpe=device_tpe,
                                    device_idtag=str(device.idtag),
                                    device_label=device_label,
                                    bus_label=bus_label,
                                    parameter=parameter,
                                    event_group_idtag=str(group_asset.idtag),
                                    event_group_name=str(group_asset.name),
                                )
                                parameter_entries.append(parameter_candidate)
                        else:
                            parameter_candidate = _build_runtime_parameter_candidate(
                                simulation_type=self.plot_simulation_type,
                                device_tpe=device_tpe,
                                device_idtag=str(device.idtag),
                                device_label=device_label,
                                bus_label=bus_label,
                                parameter=parameter,
                                event_group_idtag="",
                                event_group_name="",
                            )
                            parameter_entries.append(parameter_candidate)
                        candidates_by_parameter_name[parameter.get_display_name()] = parameter_entries
                else:
                    pass

        return candidates_by_var_uid, candidates_by_parameter_name

    def _build_runtime_parameter_candidate_index(self) -> Dict[str, List[DynamicPlotCandidate]]:
        """
        Build the draggable runtime parameter-candidate index from live results metadata.

        :return: Parameter candidates grouped by display name.
        """
        candidates_by_parameter_name: Dict[str, List[DynamicPlotCandidate]] = dict()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]
        for device_tpe, devices_data in self.tree_data.items():
            device: ALL_DEV_TYPES
            entry_collection: DynamicDeviceEntryCollection
            for device, entry_collection in devices_data.items():
                device_label: str = _get_device_label(device=device)
                bus_label: str = _get_device_bus_label(device=device)
                device_idtag: str = str(device.idtag)

                parameter: DynamicPlotParameter
                for parameter in entry_collection.get_parameters():
                    parameter_entries: List[DynamicPlotCandidate] = candidates_by_parameter_name.get(
                        parameter.get_display_name(),
                        list(),
                    )

                    group_idx: int
                    source_label: str
                    for group_idx, source_label in enumerate(self.source_labels):
                        parameter_candidate: DynamicPlotCandidate = _build_runtime_parameter_candidate(
                            simulation_type=self.plot_simulation_type,
                            device_tpe=device_tpe,
                            device_idtag=device_idtag,
                            device_label=device_label,
                            bus_label=bus_label,
                            parameter=parameter,
                            event_group_idtag=str(self._get_group_idtags(results=self.results)[group_idx]),
                            event_group_name=str(source_label),
                        )
                        parameter_entries.append(parameter_candidate)

                    candidates_by_parameter_name[parameter.get_display_name()] = parameter_entries

        return candidates_by_parameter_name

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
        self.candidates_by_parameter_name = dict()
        pre_simulation_candidates: tuple[Dict[int, List[DynamicPlotCandidate]], Dict[str, List[DynamicPlotCandidate]]] = self._build_pre_simulation_candidate_index()
        candidates_by_var_uid: Dict[int, List[DynamicPlotCandidate]] = pre_simulation_candidates[0]
        candidates_by_parameter_name: Dict[str, List[DynamicPlotCandidate]] = pre_simulation_candidates[1]
        var_uid: int
        candidate_list: List[DynamicPlotCandidate]
        for var_uid, candidate_list in candidates_by_var_uid.items():
            self.series_by_var_uid[var_uid] = list(candidate_list)
        self.candidates_by_parameter_name = candidates_by_parameter_name

        self.tree_model = build_dynamics_tree_model(
            tree_data=self.tree_data,
            var_role=self.var_role,
            mime_type=self.drag_mime_type,
            state_key_role=self.tree_state_role,
            series_by_var_uid=self.series_by_var_uid,
            candidates_by_parameter_name=self.candidates_by_parameter_name,
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

    def _has_event_group_results(self, results: RmsResults | EmtResults, group_idx: int) -> bool:
        """
        Check whether one event-group column contains actual simulation results.

        :param results: Current RMS or EMT results object.
        :param group_idx: Event-group index inside the results arrays.
        :return: ``True`` when the selected event group was simulated.

        Dynamic plots must distinguish declared event groups from event groups
        that produced runtime data. Drivers still allocate zero-filled result
        columns for every declared group, so this method prevents unresolved
        plot entries from binding to placeholder arrays.
        """
        # The results objects now expose an explicit boolean mask so the binder
        # can decide availability from actual runtime data presence instead of
        # inferring it from allocated array shape or declared event-group count.
        has_results_flags: Optional[np.ndarray] = None

        if type(results) == RmsResults:
            has_results_flags = results.has_event_group_results
        else:
            if type(results) == EmtResults:
                has_results_flags = results.has_event_group_results
            else:
                raise Exception("Unsupported dynamics results type")

        # Out-of-range indexes are treated as unresolved so the broader dynamic
        # plotting algorithm falls back to the persistent pending entry instead
        # of guessing a replacement series.
        if group_idx < 0 or group_idx >= len(has_results_flags):
            return False
        else:
            return bool(has_results_flags[group_idx])

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
            fallback_candidates: List[DynamicResultSeries] = self._find_fallback_series_candidates_for_entry(entry=entry)
            if len(fallback_candidates) == 1:
                return fallback_candidates[0]
            else:
                return None

    def _find_fallback_series_candidates_for_entry(self, entry: DynamicPlotEntry) -> List[DynamicResultSeries]:
        """
        Find runtime series candidates for one persistent variable entry using device-local fallback matching.

        :param entry: Persistent plot entry.
        :return: Matching runtime series candidates.
        """
        candidates: List[DynamicResultSeries] = list()

        if self.results is not None:
            event_group_identity: str = entry.event_group_idtag
            if event_group_identity == "":
                event_group_identity = entry.event_group_name
            else:
                pass

            series_list: List[DynamicResultSeries]
            for series_list in self.series_by_var_uid.values():
                series: DynamicResultSeries
                for series in series_list:
                    key: DynamicResultSeriesKey = series.get_key()
                    series_event_group_identity: str = self._get_series_event_group_identity(series=series)
                    same_family: bool = self.plot_simulation_type.value == key._simulation_type.value
                    same_group: bool = event_group_identity == series_event_group_identity
                    same_device_type: bool = entry.curve_device_type == key._device_type
                    same_device_idtag: bool = entry.device_idtag == key._device_idtag
                    same_result_path: bool = entry.result_path_kind == str(key._result_path.split(":", 1)[0])
                    same_variable_name: bool = entry.variable_name == series.get_variable_label()

                    if same_family and same_group and same_device_type and same_device_idtag and same_result_path and same_variable_name:
                        candidates.append(series)
                    else:
                        runtime_var_name: str = series.get_var().name
                        if same_family and same_group and same_device_type and same_device_idtag and same_result_path and entry.variable_name == runtime_var_name:
                            candidates.append(series)
                        else:
                            pass
        else:
            pass

        return candidates

    def _get_series_event_group_identity(self, series: DynamicResultSeries) -> str:
        """
        Get the event-group identity used by one runtime series.

        :param series: Runtime series.
        :return: Event-group idtag or fallback name.
        """
        group_idx: int = series.get_group_idx()
        group_idtags: Sequence[str] = self._get_group_idtags(results=self.results)
        group_names: Sequence[str] = self._get_group_names(results=self.results)
        group_identity: str = str(group_idtags[group_idx])
        if group_identity == "":
            group_identity = str(group_names[group_idx])
        else:
            pass
        return group_identity

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
                    created: bool = restored_plot_groups.create_group(name=plot_asset.name,
                                                                      mode=self._get_asset_plot_mode(plot_asset=plot_asset))
                    if created:
                        group: DynamicsPlotGroup | None = restored_plot_groups.get_group(name=plot_asset.name)
                        if group is not None:
                            entry: DynamicPlotEntry
                            for entry in self.circuit.dynamic_plot_entries:
                                if entry.plot == plot_asset:
                                    if self.results is not None:
                                        if entry.entry_kind == DynamicPlotEntryKind.VARIABLE:
                                            bound_series: DynamicResultSeries | None = self._bind_asset_entry_to_series(
                                                entry=entry,
                                                payload_index=payload_index,
                                                signature_index=signature_index,
                                            )
                                            if bound_series is not None and entry.enabled:
                                                if entry.variable_custom_name != "":
                                                    bound_series.set_variable_custom_name(label=entry.variable_custom_name)
                                                else:
                                                    pass
                                                self._insert_reloaded_entry_into_group(group=group,
                                                                                      entry=bound_series,
                                                                                      role=entry.role)
                                            else:
                                                # Keep unresolved entries visible in the runtime
                                                # projection so the user can inspect or delete them
                                                # without losing the persistent definition.
                                                self._insert_reloaded_entry_into_group(group=group,
                                                                                      entry=entry,
                                                                                      role=entry.role)
                                        else:
                                            self._insert_reloaded_entry_into_group(group=group,
                                                                                  entry=entry,
                                                                                  role=entry.role)
                                    else:
                                        self._insert_reloaded_entry_into_group(group=group,
                                                                              entry=entry,
                                                                              role=entry.role)
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

    def _append_asset_entry_for_series(self,
                                       group_name: str,
                                       series: DynamicResultSeries,
                                       role: DynamicPlotEntryRole = DynamicPlotEntryRole.CURVE) -> None:
        """
        Persist one runtime series selection into the owning circuit assets.

        :param group_name: Runtime plot-group name.
        :param series: Runtime series selected by the user.
        :param role: Semantic role for the persisted entry.
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
                    simulation_type=self.plot_simulation_type,
                    role=role,
                    event_group_idtag=group_idtags[group_idx],
                    event_group_name=group_names[group_idx],
                    curve_device_type=key._device_type,
                    device_idtag=key._device_idtag,
                    device_name_hint=series.get_device_label(),
                    variable_name=series.get_variable_label(),
                    result_path_kind=str(key._result_path.split(":", 1)[0]),
                    variable_custom_name=series.get_plot_label(has_multiple_sources=self.has_multiple_sources()),
                    enabled=True,
                    runtime_series_key_payload=payload,
                    name=series.get_variable_label(),
                )
                self.circuit.add_dynamic_plot_entry(obj=asset_entry)
        else:
            pass

    def _append_asset_entry_for_candidate(self,
                                          group_name: str,
                                          candidate: DynamicPlotCandidate,
                                          role: DynamicPlotEntryRole = DynamicPlotEntryRole.CURVE) -> DynamicPlotEntry | None:
        """
        Persist one pre-simulation curve candidate into the owning circuit assets.

        :param group_name: Runtime plot-group name.
        :param candidate: Pre-simulation candidate selected by the user.
        :param role: Semantic role for the created entry.
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
                    simulation_type=candidate._simulation_type,
                    entry_kind=candidate.get_entry_kind(),
                    role=role,
                    event_group_idtag=candidate._event_group_idtag,
                    event_group_name=candidate._event_group_name,
                    curve_device_type=candidate._device_type,
                    device_idtag=candidate._device_idtag,
                    device_name_hint=candidate._device_label,
                    variable_name=candidate._variable_name,
                    result_path_kind=candidate._result_path_kind,
                    variable_custom_name=candidate._variable_custom_name,
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

        parameter_candidate_list: List[DynamicPlotCandidate]
        for parameter_candidate_list in self.candidates_by_parameter_name.values():
            parameter_candidate: DynamicPlotCandidate
            for parameter_candidate in parameter_candidate_list:
                if parameter_candidate.to_payload() == payload:
                    return parameter_candidate
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

    def _get_asset_entry_for_series_in_group(self,
                                             group_name: str,
                                             series: DynamicResultSeries) -> DynamicPlotEntry | None:
        """
        Find the persistent plot entry that backs one runtime series inside one group.

        :param group_name: Owning plot-group name.
        :param series: Runtime series represented in the plots tree.
        :return: Matching persistent plot entry, or ``None`` when unavailable.
        """
        if self.circuit is not None:
            plot_asset: DynamicPlot | None = self._find_matching_asset_plot(group_name=group_name)
            if plot_asset is not None:
                target_payload: str = series.get_key().to_payload()
                target_signature: tuple[str, str, str, str, str, str] = self._build_series_binding_signature(series=series)

                entry: DynamicPlotEntry
                for entry in self.circuit.dynamic_plot_entries:
                    if entry.plot == plot_asset:
                        if entry.runtime_series_key_payload == target_payload:
                            return entry
                        else:
                            entry_signature: tuple[str, str, str, str, str, str] = (
                                self._build_asset_entry_binding_signature(entry=entry)
                            )
                            if entry_signature == target_signature:
                                return entry
                            else:
                                pass
                    else:
                        pass

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
        # The plots model rebuild happens for many user actions. Capturing the
        # attached tree-view state here keeps every caller small and ensures the
        # Dynamic Plots tree remains expanded across drag/drop and CRUD updates.
        attached_view: QtWidgets.QTreeView | None = self._find_attached_plots_tree_view()
        tree_state_snapshot: TreeStateSnapshot | None = self.capture_plots_tree_state(view=attached_view)

        # The Qt model is treated as a projection of the handler state so every CRUD operation remains explicit.
        self.plots_model.clear()
        self.plots_model.setHorizontalHeaderLabels(["Dynamic plots"])

        root_item: QtGui.QStandardItem = self.plots_model.invisibleRootItem()
        group: DynamicsPlotGroup
        for group in self.plot_groups.get_groups():
            group_label: str = group.get_name()
            if group.get_mode() == DynamicPlotMode.XY:
                group_label = group_label + " [" + _build_plot_mode_display_label(mode=group.get_mode()) + "]"
            else:
                pass

            group_item: QtGui.QStandardItem = _build_tree_item(text=group_label)
            group_item.setData(group.get_name(), self.group_name_role)
            group_item.setData(DynamicPlotDropTargetKind.GROUP, self.drop_target_role)
            group_item.setData(
                _build_tree_state_key(node_kind=TreeStateNodeKind.PLOT_GROUP, parts=[group.get_name()]),
                self.tree_state_role,
            )
            _set_item_icon(item=group_item, icon_key="Dynamic")
            root_item.appendRow(group_item)

            if group.get_mode() == DynamicPlotMode.XY:
                self._append_xy_plot_group_items(group_item=group_item, group=group)
            else:
                self._append_time_series_plot_group_items(group_item=group_item, group=group)

        self.restore_plots_tree_state(view=attached_view, snapshot=tree_state_snapshot)

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

    def create_plot_group(self, name: str, mode: DynamicPlotMode = DynamicPlotMode.TIME_SERIES) -> bool:
        """
        Create a plot group and refresh the plots tree.

        :param name: Requested plot-group name.
        :param mode: Requested plotting mode.
        :return: ``True`` when the group was created.
        """
        if self.circuit is not None:
            asset_plot: DynamicPlot | None = self._get_or_create_asset_plot(group_name=name)
            if asset_plot is not None:
                self._set_asset_plot_mode(plot_asset=asset_plot, mode=mode)
            else:
                pass
        else:
            pass

        created: bool = self.plot_groups.create_group(name=name, mode=mode)
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

    def rename_plot_group(self, old_name: str, new_name: str) -> bool:
        """
        Rename one plot group and refresh the plots tree.

        :param old_name: Existing plot-group name.
        :param new_name: Requested replacement name.
        :return: ``True`` when the group existed and the rename was applied.
        """
        # The new name is normalized first so the runtime state and the persistent
        # circuit asset follow the exact same validated identifier.
        clean_name: str = new_name.strip()

        if clean_name != "":
            # When a circuit exists, the persistent plot asset has to be renamed
            # together with the runtime group so future reloads preserve the new name.
            if self.circuit is not None:
                plot_asset: DynamicPlot | None = self._find_matching_asset_plot(group_name=old_name)
                clashing_asset: DynamicPlot | None = self._find_matching_asset_plot(group_name=clean_name)
                if plot_asset is not None:
                    if clashing_asset is None or clean_name == old_name:
                        plot_asset.name = clean_name
                    else:
                        return False
                else:
                    pass
            else:
                pass

            # The domain collection remains the source for the Qt tree model, so
            # the runtime rename must succeed before rebuilding the projection.
            renamed: bool = self.plot_groups.rename_group(old_name=old_name, new_name=clean_name)
            if renamed:
                self.rebuild_plots_model()
                return True
            else:
                return False
        else:
            return False

    def rename_plot_variable_from_index(self, index: QtCore.QModelIndex, new_name: str) -> bool:
        """
        Rename the visible label of one plotted variable.

        :param index: Plots-tree index that points to one variable child.
        :param new_name: Requested visible label.
        :return: ``True`` when the rename was applied.
        """
        # The rename is normalized once so both runtime and persistent state keep
        # the exact same visible text without whitespace-only aliases.
        clean_name: str = new_name.strip()
        if clean_name != "":
            series: DynamicResultSeries | None = self.get_plot_series_from_index(index=index)
            if series is not None:
                # Runtime series must redirect the rename to their backing
                # persistent entry so the custom visible name survives reloads.
                group_name: str | None = self.get_plot_group_name_from_index(index=index)
                if group_name is not None:
                    asset_entry: DynamicPlotEntry | None = self._get_asset_entry_for_series_in_group(
                        group_name=group_name,
                        series=series,
                    )
                    if asset_entry is not None:
                        asset_entry.variable_custom_name = clean_name
                        series.set_variable_custom_name(label=clean_name)
                        self.rebuild_plots_model()
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                # Unresolved persistent entries are renamed in place because no
                # runtime series exists yet to mirror the custom visible name.
                asset_entry: DynamicPlotEntry | None = self.get_plot_asset_entry_from_index(index=index)
                if asset_entry is not None:
                    asset_entry.variable_custom_name = clean_name
                    self.rebuild_plots_model()
                    return True
                else:
                    return False
        else:
            return False

    def _build_runtime_entry_label(self, entry: DynamicResultSeries | DynamicPlotEntry | Var) -> str:
        """
        Build the visible label for one stored plot entry.

        :param entry: Stored plot entry.
        :return: Visible label.
        """
        if isinstance(entry, DynamicResultSeries):
            return entry.get_plot_label(has_multiple_sources=self.has_multiple_sources())
        else:
            if isinstance(entry, DynamicPlotEntry):
                if entry.entry_kind == DynamicPlotEntryKind.PARAMETER:
                    return _build_parameter_plot_entry_label(entry=entry)
                else:
                    return _build_unresolved_plot_entry_label(entry=entry)
            else:
                if isinstance(entry, Var):
                    return _get_var_label(variable=entry)
                else:
                    return ""

    def _build_runtime_entry_state(self,
                                   entry: DynamicResultSeries | DynamicPlotEntry | Var) -> tuple[str, bool, bool]:
        """
        Build the visible label and pending/missing state for one stored entry.

        :param entry: Stored plot entry.
        :return: Tuple ``(label, is_pending, is_missing)``.
        """
        if isinstance(entry, DynamicResultSeries):
            return self._build_runtime_entry_label(entry=entry), False, False
        else:
            if isinstance(entry, DynamicPlotEntry):
                if entry.entry_kind == DynamicPlotEntryKind.PARAMETER:
                    parameter_plot_data: tuple[np.ndarray, np.ndarray] | None = self._get_parameter_plot_data(entry=entry)
                    if parameter_plot_data is not None:
                        return self._build_runtime_entry_label(entry=entry), False, False
                    else:
                        if self.results is not None:
                            return self._build_runtime_entry_label(entry=entry), False, True
                        else:
                            return self._build_runtime_entry_label(entry=entry), True, False
                else:
                    if self.results is not None:
                        return self._build_runtime_entry_label(entry=entry), False, True
                    else:
                        return self._build_runtime_entry_label(entry=entry), True, False
            else:
                return self._build_runtime_entry_label(entry=entry), False, False

    def _style_pending_plot_item(self, item: QtGui.QStandardItem, is_pending: bool, is_missing: bool) -> None:
        """
        Apply the existing pending/missing color semantics to one plot-tree row.

        :param item: Tree item to style.
        :param is_pending: Whether the item is pending.
        :param is_missing: Whether the item is missing.
        :return: None.
        """
        if is_missing:
            item.setForeground(QtGui.QBrush(QtGui.QColor("#d67b7b")))
        else:
            if is_pending:
                item.setForeground(QtGui.QBrush(QtGui.QColor("#a0a0a0")))
            else:
                pass

    def _append_regular_plot_entry_item(self,
                                        group_item: QtGui.QStandardItem,
                                        group: DynamicsPlotGroup,
                                        entry: DynamicResultSeries | DynamicPlotEntry | Var) -> None:
        """
        Append one regular time-series child row.

        :param group_item: Parent group item.
        :param group: Owning group.
        :param entry: Stored plot entry.
        :return: None.
        """
        label: str
        is_pending: bool
        is_missing: bool
        label, is_pending, is_missing = self._build_runtime_entry_state(entry=entry)
        if is_missing:
            label = label + " [missing]"
        else:
            if is_pending:
                label = label + " [pending]"
            else:
                pass

        variable_item: QtGui.QStandardItem = _build_tree_item(text=label)
        variable_item.setData(entry, self.var_role)
        variable_item.setData(DynamicPlotEntryRole.CURVE, self.entry_role_role)
        if isinstance(entry, DynamicResultSeries):
            key_fragment: str = entry.get_key().to_payload()
        else:
            if isinstance(entry, DynamicPlotEntry):
                key_fragment = str(entry.idtag)
            else:
                key_fragment = "legacy-var:" + str(entry.uid)
        variable_item.setData(
            _build_tree_state_key(node_kind=TreeStateNodeKind.PLOT_ENTRY,
                                  parts=[group.get_name(), key_fragment]),
            self.tree_state_role,
        )
        self._style_pending_plot_item(item=variable_item, is_pending=is_pending, is_missing=is_missing)
        group_item.appendRow(variable_item)

    def _append_time_series_plot_group_items(self,
                                             group_item: QtGui.QStandardItem,
                                             group: DynamicsPlotGroup) -> None:
        """
        Append the child rows for one time-series plot group.

        :param group_item: Parent group item.
        :param group: Plot group.
        :return: None.
        """
        entry: DynamicResultSeries | DynamicPlotEntry | Var
        for entry in group.get_series():
            self._append_regular_plot_entry_item(group_item=group_item, group=group, entry=entry)

    def _append_xy_slot_item(self,
                             group_item: QtGui.QStandardItem,
                             group: DynamicsPlotGroup,
                             role: DynamicPlotEntryRole) -> None:
        """
        Append one explicit XY slot row.

        :param group_item: Parent group item.
        :param group: Plot group.
        :param role: Slot role.
        :return: None.
        """
        entry: DynamicResultSeries | DynamicPlotEntry | Var | None = group.get_entry_for_role(role=role)
        if entry is not None:
            label, is_pending, is_missing = self._build_runtime_entry_state(entry=entry)
        else:
            label = ""
            is_pending = True
            is_missing = False

        slot_item: QtGui.QStandardItem = _build_tree_item(text=_build_xy_slot_label(role=role,
                                                                                    entry_label=label,
                                                                                    is_pending=is_pending or is_missing))
        slot_item.setData(group.get_name(), self.group_name_role)
        slot_item.setData(role, self.entry_role_role)
        if role == DynamicPlotEntryRole.X_AXIS:
            slot_item.setData(DynamicPlotDropTargetKind.XY_X_SLOT, self.drop_target_role)
        else:
            slot_item.setData(DynamicPlotDropTargetKind.XY_Y_SLOT, self.drop_target_role)

        slot_key: str = "x-slot"
        if role == DynamicPlotEntryRole.Y_AXIS:
            slot_key = "y-slot"
        else:
            pass
        slot_item.setData(
            _build_tree_state_key(node_kind=TreeStateNodeKind.PLOT_ENTRY,
                                  parts=[group.get_name(), slot_key]),
            self.tree_state_role,
        )
        if entry is not None:
            slot_item.setData(entry, self.var_role)
            self._style_pending_plot_item(item=slot_item, is_pending=is_pending, is_missing=is_missing)
        else:
            self._style_pending_plot_item(item=slot_item, is_pending=True, is_missing=False)
        group_item.appendRow(slot_item)

    def _append_xy_plot_group_items(self,
                                    group_item: QtGui.QStandardItem,
                                    group: DynamicsPlotGroup) -> None:
        """
        Append the explicit X and Y slot rows for one XY plot group.

        :param group_item: Parent group item.
        :param group: Plot group.
        :return: None.
        """
        self._append_xy_slot_item(group_item=group_item, group=group, role=DynamicPlotEntryRole.X_AXIS)
        self._append_xy_slot_item(group_item=group_item, group=group, role=DynamicPlotEntryRole.Y_AXIS)

    def _get_role_from_drop_index(self, index: QtCore.QModelIndex) -> DynamicPlotEntryRole | None:
        """
        Resolve the requested XY slot role from one drop target.

        :param index: Drop target index.
        :return: Entry role, or ``None`` when the target is the group row.
        """
        if index.isValid():
            item: QtGui.QStandardItem | None = self.plots_model.itemFromIndex(index)
            if item is not None:
                role_data: object = item.data(self.entry_role_role)
                if isinstance(role_data, DynamicPlotEntryRole):
                    if role_data == DynamicPlotEntryRole.X_AXIS or role_data == DynamicPlotEntryRole.Y_AXIS:
                        return role_data
                    else:
                        return None
                else:
                    return None
            else:
                return None
        else:
            return None

    def _ask_user_for_xy_drop_role(self,
                                   group: DynamicsPlotGroup,
                                   candidate_label: str) -> DynamicPlotEntryRole | None:
        """
        Ask the user where one dropped signal should be placed in an XY plot.

        :param group: Target XY plot group.
        :param candidate_label: Visible label of the dropped signal.
        :return: Selected role, or ``None`` when cancelled.
        """
        del candidate_label
        x_entry: DynamicResultSeries | DynamicPlotEntry | Var | None = group.get_entry_for_role(role=DynamicPlotEntryRole.X_AXIS)
        y_entry: DynamicResultSeries | DynamicPlotEntry | Var | None = group.get_entry_for_role(role=DynamicPlotEntryRole.Y_AXIS)
        title: str = "X-Y plot slot"

        if x_entry is None and y_entry is None:
            if self.dialog_parent is not None:
                message_box: QtWidgets.QMessageBox = QtWidgets.QMessageBox(self.dialog_parent)
                message_box.setWindowTitle(title)
                message_box.setText("Choose whether to place the dropped signal on the X axis or Y axis.")
                replace_x_button: QtWidgets.QAbstractButton = message_box.addButton("X axis", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                replace_y_button: QtWidgets.QAbstractButton = message_box.addButton("Y axis", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                message_box.addButton("Cancel", QtWidgets.QMessageBox.ButtonRole.RejectRole)
                message_box.exec()
                clicked_button: QtWidgets.QAbstractButton | None = message_box.clickedButton()
                if clicked_button is replace_x_button:
                    return DynamicPlotEntryRole.X_AXIS
                else:
                    if clicked_button is replace_y_button:
                        return DynamicPlotEntryRole.Y_AXIS
                    else:
                        return None
            else:
                return DynamicPlotEntryRole.X_AXIS
        else:
            if x_entry is None:
                return DynamicPlotEntryRole.X_AXIS
            else:
                if y_entry is None:
                    return DynamicPlotEntryRole.Y_AXIS
                else:
                    if self.dialog_parent is not None:
                        message_box = QtWidgets.QMessageBox(self.dialog_parent)
                        message_box.setWindowTitle(title)
                        message_box.setText("This X-Y plot already has X and Y signals. Replace X, replace Y, or cancel?")
                        replace_x_button = message_box.addButton("Replace X", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                        replace_y_button = message_box.addButton("Replace Y", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                        message_box.addButton("Cancel", QtWidgets.QMessageBox.ButtonRole.RejectRole)
                        message_box.exec()
                        clicked_button = message_box.clickedButton()
                        if clicked_button is replace_x_button:
                            return DynamicPlotEntryRole.X_AXIS
                        else:
                            if clicked_button is replace_y_button:
                                return DynamicPlotEntryRole.Y_AXIS
                            else:
                                return None
                    else:
                        return None

    def _get_drop_role_for_group(self,
                                 group: DynamicsPlotGroup,
                                 drop_index: QtCore.QModelIndex,
                                 candidate_label: str) -> DynamicPlotEntryRole | None:
        """
        Resolve the effective role for one drop operation.

        :param group: Target plot group.
        :param drop_index: Drop target index.
        :param candidate_label: Visible label of the dropped signal.
        :return: Role to use, or ``None``.
        """
        if group.get_mode() == DynamicPlotMode.TIME_SERIES:
            return DynamicPlotEntryRole.CURVE
        else:
            slot_role: DynamicPlotEntryRole | None = self._get_role_from_drop_index(index=drop_index)
            if slot_role is not None:
                return slot_role
            else:
                return self._ask_user_for_xy_drop_role(group=group, candidate_label=candidate_label)

    def add_series_to_group_with_role(self,
                                      group_name: str,
                                      series_key: DynamicResultSeriesKey,
                                      role: DynamicPlotEntryRole) -> bool:
        """
        Add one runtime series to a group using the requested semantic role.

        :param group_name: Target group name.
        :param series_key: Runtime series identity.
        :param role: Requested entry role.
        :return: ``True`` when inserted or replaced.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        variable: DynamicResultSeries | None = self._get_unique_series_for_key(series_key=series_key)
        if group is not None:
            if variable is not None:
                if group.get_mode() == DynamicPlotMode.TIME_SERIES:
                    inserted: bool = group.add_var(variable=variable)
                    if inserted:
                        self._append_asset_entry_for_series(group_name=group_name,
                                                            series=variable,
                                                            role=DynamicPlotEntryRole.CURVE)
                        self.rebuild_plots_model()
                        return True
                    else:
                        return False
                else:
                    return self._replace_xy_series_entry(group_name=group_name, group=group, series=variable, role=role)
            else:
                return False
        else:
            return False

    def add_candidate_to_group_with_role(self,
                                         group_name: str,
                                         candidate: DynamicPlotCandidate,
                                         role: DynamicPlotEntryRole) -> bool:
        """
        Add one pre-simulation candidate to a group using the requested role.

        :param group_name: Target group name.
        :param candidate: Candidate selected from the source tree.
        :param role: Requested entry role.
        :return: ``True`` when inserted or replaced.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        if group is not None:
            prepared_candidate: DynamicPlotCandidate | None = candidate
            if self.pre_simulation_mode:
                prepared_candidate = self._ensure_event_group_for_candidate(candidate=candidate)
            else:
                pass
            if prepared_candidate is None:
                return False
            else:
                pass

            if group.get_mode() == DynamicPlotMode.TIME_SERIES:
                asset_entry: DynamicPlotEntry | None = self._append_asset_entry_for_candidate(group_name=group_name,
                                                                                              candidate=prepared_candidate,
                                                                                              role=DynamicPlotEntryRole.CURVE)
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
                return self._replace_xy_candidate_entry(group_name=group_name,
                                                        group=group,
                                                        candidate=prepared_candidate,
                                                        role=role)
        else:
            return False

    def add_series_to_group_from_drop(self,
                                      group_name: str,
                                      series_key: DynamicResultSeriesKey,
                                      drop_index: QtCore.QModelIndex) -> bool:
        """
        Add one runtime series using drop-target semantics.

        :param group_name: Target group name.
        :param series_key: Runtime series identity.
        :param drop_index: Drop target index.
        :return: ``True`` when inserted.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        variable: DynamicResultSeries | None = self._get_unique_series_for_key(series_key=series_key)
        if group is not None and variable is not None:
            role: DynamicPlotEntryRole | None = self._get_drop_role_for_group(group=group,
                                                                              drop_index=drop_index,
                                                                              candidate_label=variable.get_plot_label(has_multiple_sources=self.has_multiple_sources()))
            if role is not None:
                return self.add_series_to_group_with_role(group_name=group_name, series_key=series_key, role=role)
            else:
                return False
        else:
            return False

    def add_candidate_to_group_from_drop(self,
                                         group_name: str,
                                         candidate: DynamicPlotCandidate,
                                         drop_index: QtCore.QModelIndex) -> bool:
        """
        Add one pre-simulation candidate using drop-target semantics.

        :param group_name: Target group name.
        :param candidate: Dropped candidate.
        :param drop_index: Drop target index.
        :return: ``True`` when inserted.
        """
        group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=group_name)
        if group is not None:
            role: DynamicPlotEntryRole | None = self._get_drop_role_for_group(group=group,
                                                                              drop_index=drop_index,
                                                                              candidate_label=candidate.get_plot_label(has_multiple_sources=self.has_multiple_sources()))
            if role is not None:
                return self.add_candidate_to_group_with_role(group_name=group_name, candidate=candidate, role=role)
            else:
                return False
        else:
            return False

    def _delete_entry_assets_for_role(self,
                                      group_name: str,
                                      role: DynamicPlotEntryRole) -> None:
        """
        Delete the persistent entry stored in one XY role.

        :param group_name: Target group name.
        :param role: Role to remove.
        :return: None.
        """
        if self.circuit is not None:
            plot_asset: DynamicPlot | None = self._find_matching_asset_plot(group_name=group_name)
            if plot_asset is not None:
                entry_to_delete: DynamicPlotEntry | None = None
                entry: DynamicPlotEntry
                for entry in self.circuit.dynamic_plot_entries:
                    if entry.plot == plot_asset and entry.role == role:
                        entry_to_delete = entry
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

    def _replace_xy_series_entry(self,
                                 group_name: str,
                                 group: DynamicsPlotGroup,
                                 series: DynamicResultSeries,
                                 role: DynamicPlotEntryRole) -> bool:
        """
        Replace one XY slot with a runtime series.

        :param group_name: Target group name.
        :param group: Target group.
        :param series: Runtime series.
        :param role: Slot role to replace.
        :return: ``True`` when replaced.
        """
        self._delete_entry_assets_for_role(group_name=group_name, role=role)
        stored: bool = group.replace_entry_for_role(variable=series, role=role)
        if stored:
            self._append_asset_entry_for_series(group_name=group_name, series=series, role=role)
            self.rebuild_plots_model()
            return True
        else:
            return False

    def _replace_xy_candidate_entry(self,
                                    group_name: str,
                                    group: DynamicsPlotGroup,
                                    candidate: DynamicPlotCandidate,
                                    role: DynamicPlotEntryRole) -> bool:
        """
        Replace one XY slot with a persistent candidate entry.

        :param group_name: Target group name.
        :param group: Target group.
        :param candidate: Candidate to store.
        :param role: Slot role to replace.
        :return: ``True`` when replaced.
        """
        self._delete_entry_assets_for_role(group_name=group_name, role=role)
        asset_entry: DynamicPlotEntry | None = self._append_asset_entry_for_candidate(group_name=group_name,
                                                                                      candidate=candidate,
                                                                                      role=role)
        if asset_entry is not None:
            stored: bool = group.replace_entry_for_role(variable=asset_entry, role=role)
            if stored:
                self.rebuild_plots_model()
                return True
            else:
                return False
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
        return self.add_series_to_group_with_role(group_name=group_name,
                                                  series_key=series_key,
                                                  role=DynamicPlotEntryRole.CURVE)

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
        return self.add_candidate_to_group_with_role(group_name=group_name,
                                                     candidate=candidate,
                                                     role=DynamicPlotEntryRole.CURVE)

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

    def _show_figure(self, figure: Figure, title: str) -> None:
        """
        Display a Matplotlib figure in an embedded Qt window.

        The figure is embedded in a ``FigureCanvasQTAgg`` inside a modeless
        ``QDialog`` instead of being shown with ``pyplot.show()``. 
        Before ``pyplot.show()`` was starting starts a second GUI event loop
        on top of the already-running Qt application which is a hard
        crash on the macOS backend.

        :param figure: Figure to display (built with ``matplotlib.figure.Figure``).
        :param title: Window title.
        :return: Nothing.
        """
        dialog: QtWidgets.QDialog = QtWidgets.QDialog(self.dialog_parent)
        dialog.setWindowTitle(title)
        dialog.setWindowFlag(QtCore.Qt.WindowType.Window, True)
        dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)

        canvas: FigureCanvas = FigureCanvas(figure)
        toolbar: NavigationToolbar = NavigationToolbar(canvas, dialog)

        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        dialog.resize(900, 600)

        self._open_plot_dialogs.append(dialog)

        # Drop our reference once the window is closed so the dialog can be freed
        def _forget(_result: int = 0, _dialog: QtWidgets.QDialog = dialog) -> None:
            if _dialog in self._open_plot_dialogs:
                self._open_plot_dialogs.remove(_dialog)

        dialog.finished.connect(_forget)
        dialog.show()

    def plot_series(self, series: DynamicResultSeries) -> None:
        """
        Plot one source-specific series.

        :param series: Series to plot.
        :return: Nothing.
        """
        figure = Figure(figsize=(12, 8))
        axis = figure.add_subplot(111)
        x_values, y_values = self._get_series_plot_data(series=series)
        axis.plot(x_values, y_values, label=series.get_plot_label(has_multiple_sources=self.has_multiple_sources()))
        axis.set_title(series.get_var().name)
        axis.set_xlabel("Time [s]")
        axis.legend()
        self._show_figure(figure=figure, title=series.get_var().name)

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
        if plot_group is None:
            return False
        else:
            pass

        if plot_group.get_mode() == DynamicPlotMode.XY:
            return self._plot_xy_group(plot_group=plot_group)
        else:
            pass

        # plot timeseries results
        if self.results is None:
            return False
        else:
            pass

        variables: List[DynamicResultSeries | DynamicPlotEntry | Var] = plot_group.get_series()
        if len(variables) == 0:
            return False
        else:
            pass

        figure = Figure(figsize=(12, 8))
        axis = figure.add_subplot(111)

        variable: DynamicResultSeries | DynamicPlotEntry | Var
        for variable in variables:
            x_values: Optional[np.ndarray] = None
            y_values: Optional[np.ndarray] = None
            label: str = ""

            if isinstance(variable, DynamicResultSeries):
                x_values, y_values = self._get_series_plot_data(series=variable)
                label = variable.get_plot_label(has_multiple_sources=self.has_multiple_sources())

            elif isinstance(variable, DynamicPlotEntry):
                label = variable.variable_custom_name
                if label == "":
                    label = variable.variable_name
                else:
                    pass

                if variable.entry_kind == DynamicPlotEntryKind.PARAMETER:
                    parameter_plot_data: tuple[np.ndarray, np.ndarray] | None = self._get_parameter_plot_data(
                        entry=variable
                    )
                    if parameter_plot_data is not None:
                        x_values, y_values = parameter_plot_data
                    else:
                        x_values = self.results.time_array
                        y_values = None
                else:
                    x_values = self.results.time_array
                    y_values = None

            elif isinstance(variable, Var):
                x_values = self.results.time_array

                # Legacy raw ``Var`` entries are still tolerated, but only when
                # they resolve to exactly one current series.
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

            if x_values is not None and y_values is not None:
                axis.plot(x_values, y_values, label=label)
            else:
                pass

        if len(axis.lines) > 0:
            axis.legend()
            axis.set_xlabel("Time [s]")
            axis.set_title(plot_group_name)
            self._show_figure(figure=figure, title=plot_group_name)
            return True
        else:
            return False

    def _resolve_entry_signal(self,
                              entry: DynamicResultSeries | DynamicPlotEntry | Var) -> tuple[np.ndarray | None, np.ndarray | None, str | None, PlotSimulationType | None, str | None]:
        """
        Resolve one stored plot entry into numeric values and compatibility metadata.

        :param entry: Stored plot entry.
        :return: Tuple ``(time_values, signal_values, label, simulation_type, event_group_identity)``.
        """
        if isinstance(entry, DynamicResultSeries):
            time_values, signal_values = self._get_series_plot_data(series=entry)
            source_identity: str = str(entry.get_group_idx())
            return time_values, signal_values, entry.get_plot_label(has_multiple_sources=self.has_multiple_sources()), self.plot_simulation_type, source_identity
        else:
            if isinstance(entry, DynamicPlotEntry):
                if entry.entry_kind == DynamicPlotEntryKind.PARAMETER:
                    parameter_plot_data: tuple[np.ndarray, np.ndarray] | None = self._get_parameter_plot_data(entry=entry)
                    if parameter_plot_data is not None:
                        identity: str = entry.event_group_idtag
                        if identity == "":
                            identity = entry.event_group_name
                        else:
                            pass
                        return parameter_plot_data[0], parameter_plot_data[1], self._build_runtime_entry_label(entry=entry), entry.simulation_type, identity
                    else:
                        return None, None, None, None, None
                else:
                    return None, None, None, None, None
            else:
                if isinstance(entry, Var):
                    compatible_series: List[DynamicResultSeries] = self.series_by_var_uid.get(entry.uid, list())
                    if len(compatible_series) == 1:
                        return self._resolve_entry_signal(entry=compatible_series[0])
                    else:
                        return None, None, None, None, None
                else:
                    return None, None, None, None, None

    def _plot_xy_group(self, plot_group: DynamicsPlotGroup) -> bool:
        """
        Plot one XY dynamic plot after resolving both explicit slots.

        :param plot_group: XY plot group.
        :return: ``True`` when plotted successfully.
        """
        if self.results is None:
            return False
        else:
            pass

        x_entry: DynamicResultSeries | DynamicPlotEntry | Var | None = plot_group.get_entry_for_role(role=DynamicPlotEntryRole.X_AXIS)
        y_entry: DynamicResultSeries | DynamicPlotEntry | Var | None = plot_group.get_entry_for_role(role=DynamicPlotEntryRole.Y_AXIS)
        if x_entry is None or y_entry is None:
            return False
        else:
            pass

        x_time: Optional[np.ndarray]
        x_values: Optional[np.ndarray]
        x_label: str | None
        x_simulation_type: PlotSimulationType | None
        x_identity: str | None
        x_time, x_values, x_label, x_simulation_type, x_identity = self._resolve_entry_signal(entry=x_entry)
        y_time: Optional[np.ndarray]
        y_values: Optional[np.ndarray]
        y_label: str | None
        y_simulation_type: PlotSimulationType | None
        y_identity: str | None
        y_time, y_values, y_label, y_simulation_type, y_identity = self._resolve_entry_signal(entry=y_entry)

        if x_values is None or y_values is None or x_label is None or y_label is None:
            return False
        else:
            pass

        if x_simulation_type != y_simulation_type:
            return False
        else:
            pass

        if x_identity != y_identity:
            return False
        else:
            pass

        if len(x_values) != len(y_values):
            return False
        else:
            pass

        figure = Figure(figsize=(12, 8))
        axis = figure.add_subplot(111)

        finite_mask: np.ndarray = np.isfinite(x_values) & np.isfinite(y_values)
        x_plot: np.ndarray = x_values[finite_mask]
        y_plot: np.ndarray = y_values[finite_mask]

        if len(x_plot) == 0:
            return False
        else:
            pass

        x_is_constant: bool = bool(np.allclose(x_plot, x_plot[0]))
        y_is_constant: bool = bool(np.allclose(y_plot, y_plot[0]))

        if x_is_constant and y_is_constant:
            axis.scatter(x_plot[0], y_plot[0])
        else:
            axis.plot(x_plot, y_plot)

        axis.set_title(plot_group.get_name())
        axis.set_xlabel(x_label)
        axis.set_ylabel(y_label)
        axis.grid(True)

        # Give visibility to constant axes.
        if x_is_constant:
            x_center: float = float(x_plot[0])
            x_padding: float = max(abs(x_center) * 0.05, 1e-6)
            axis.set_xlim(x_center - x_padding, x_center + x_padding)
        else:
            pass

        if y_is_constant:
            y_center: float = float(y_plot[0])
            y_padding: float = max(abs(y_center) * 0.05, 1e-6)
            axis.set_ylim(y_center - y_padding, y_center + y_padding)
        else:
            pass

        self._show_figure(figure=figure, title=plot_group.get_name())
        return True



    def plot_entry_from_index(self, index: QtCore.QModelIndex) -> bool:
        """
        Plot the selected plots-tree entry.

        :param index: Selected plots-tree index.
        :return: ``True`` when something was plotted.
        """
        plot_group_name: str | None = self.get_plot_group_name_from_index(index=index)
        if plot_group_name is not None:
            plot_group: DynamicsPlotGroup | None = self.plot_groups.get_group(name=plot_group_name)
            if plot_group is not None:
                if plot_group.get_mode() == DynamicPlotMode.XY:
                    return self.plot_group(plot_group_name=plot_group_name)
                else:
                    pass
            else:
                pass
        else:
            pass

        selected_var: DynamicResultSeries | None = self.get_plot_series_from_index(index=index)
        if selected_var is not None:
            self.plot_series(series=selected_var)
            return True
        else:
            unresolved_entry: DynamicPlotEntry | None = self.get_plot_asset_entry_from_index(index=index)
            if unresolved_entry is not None:
                if unresolved_entry.entry_kind == DynamicPlotEntryKind.PARAMETER:
                    return self.plot_parameter_entry(entry=unresolved_entry)
                else:
                    return False
            else:
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
                compatible_parameter_entries: List[DynamicPlotEntry] = list()
                variable: DynamicResultSeries | DynamicPlotEntry | Var
                for variable in variables:
                    if isinstance(variable, DynamicResultSeries):
                        compatible_series.append(variable)
                    elif isinstance(variable, DynamicPlotEntry):
                        if variable.entry_kind == DynamicPlotEntryKind.PARAMETER:
                            compatible_parameter_entries.append(variable)
                        else:
                            pass
                    else:
                        series_list: List[DynamicResultSeries] = self.series_by_var_uid.get(variable.uid, list())
                        if len(series_list) == 1:
                            compatible_series.append(series_list[0])
                        else:
                            pass

                if len(compatible_series) == 0 and len(compatible_parameter_entries) == 0:
                    return None

                # The table index must reuse the same elapsed-seconds axis as the
                # plot so the numeric view and the rendered chart stay aligned.
                first_time: np.ndarray = _build_relative_time_axis(time_array=self.results.time_array)
                series: DynamicResultSeries
                for series in compatible_series:
                    series_time, _ = self._get_series_plot_data(series=series)
                    # Every plotted series in one table must share the exact same
                    # normalized time base so columns remain row-aligned.
                    if not np.array_equal(series_time, first_time):
                        return None
                    else:
                        pass

                total_column_count: int = len(compatible_series) + len(compatible_parameter_entries)
                data: np.ndarray = np.empty((len(first_time), total_column_count), dtype=float)
                columns: List[str] = list()

                for idx, series in enumerate(compatible_series):
                    _, y_values = self._get_series_plot_data(series=series)
                    data[:, idx] = y_values
                    columns.append(series.get_plot_label(has_multiple_sources=self.has_multiple_sources()))

                parameter_index: int
                parameter_entry: DynamicPlotEntry
                for parameter_index, parameter_entry in enumerate(compatible_parameter_entries):
                    parameter_plot_data: tuple[np.ndarray, np.ndarray] | None = self._get_parameter_plot_data(entry=parameter_entry)
                    if parameter_plot_data is not None:
                        parameter_time, parameter_values = parameter_plot_data
                        if np.array_equal(parameter_time, first_time):
                            column_index: int = len(compatible_series) + parameter_index
                            data[:, column_index] = parameter_values
                            if parameter_entry.variable_custom_name != "":
                                columns.append(parameter_entry.variable_custom_name)
                            else:
                                columns.append(parameter_entry.variable_name)
                        else:
                            return None
                    else:
                        return None

                table = ResultsTable(
                    data=data,
                    index=first_time,
                    columns=np.array(columns, dtype=str),
                    title=plot_group_name,
                    xlabel="Time [s]",
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

    def _build_exported_results_tree_data(self) -> Dict[DeviceType, Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]]:
        """
        Build the runtime device tree using only variables exported by the results.

        :return: Filtered device tree grouped by device type and device.
        """
        raw_tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]] = self.results.get_devices_dict_tree()
        filtered_tree_data: Dict[DeviceType, Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]] = dict()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, List[Var]]
        for device_tpe, devices_data in raw_tree_data.items():
            filtered_devices: Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection] = dict()

            device: ALL_DEV_TYPES
            variables: List[Var]
            for device, variables in devices_data.items():
                exported_variables: List[Var] = list()
                parameters: List[DynamicPlotParameter] = list()

                variable: Var
                for variable in variables:
                    if self._variable_is_exported_in_current_results(variable=variable):
                        exported_variables.append(variable)
                    else:
                        pass

                if len(exported_variables) > 0:
                    if isinstance(device, (DynamicDevice, DynamicBusDevice)):
                        model_block: Block = _get_pre_simulation_block(device=device, simulation_type=self.plot_simulation_type)
                        parameters = collect_dynamic_model_plot_parameters(model=model_block)
                    else:
                        parameters = list()

                    filtered_devices[device] = DynamicDeviceEntryCollection(
                        variables=exported_variables,
                        parameters=parameters,
                    )
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
        self.candidates_by_parameter_name = dict()

        device_tpe: DeviceType
        devices_data: Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]
        for device_tpe, devices_data in self.tree_data.items():
            device: ALL_DEV_TYPES
            entry_collection: DynamicDeviceEntryCollection
            for device, entry_collection in devices_data.items():
                device_label: str = _get_device_label(device=device)
                bus_label: str = _get_device_bus_label(device=device)
                device_idtag: str = str(device.idtag)

                variable_index: int
                variable: Var
                for variable_index, variable in enumerate(entry_collection.get_variables()):
                    result_path: str
                    component_index: int
                    result_path, component_index = self._resolve_result_path_and_component_index(variable=variable)
                    scoped_result_path: str = result_path + ":" + variable.name

                    group_idx: int
                    source_label: str
                    for group_idx, source_label in enumerate(self.source_labels):
                        # A distinct series is created only for event groups that
                        # produced runtime data. Declared-but-unsimulated groups
                        # stay available only as persistent unresolved entries.
                        if self._has_event_group_results(results=self.results, group_idx=group_idx):
                            # The runtime series is created only when the exact
                            # event-group column is backed by simulated data.
                            # This preserves the declared event-group identity
                            # while preventing placeholder zero columns from
                            # entering the plottable runtime index.
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
                                bus_label=bus_label,
                                variable_label=_get_var_label(variable=variable),
                                variable_custom_name="",
                            )
                            self.series_by_key.setdefault(key, list()).append(series)
                            self.series_by_var_uid.setdefault(variable.uid, list()).append(series)
                        else:
                            # Unsimulated groups remain available only through
                            # the persistent plot-entry assets so the UI can
                            # keep them visible as pending instead of plotting
                            # a fabricated numerical curve.
                            pass

        # Runtime parameter leaves do not have a numeric series array behind
        # them, but they still need a drag payload and a double-click plotting
        # identity. This candidate index supplies that parameter-specific
        # semantic payload for the live post-simulation tree.
        self.candidates_by_parameter_name = self._build_runtime_parameter_candidate_index()

        self.tree_model = build_dynamics_tree_model(
            tree_data=self.tree_data,
            var_role=self.var_role,
            mime_type=self.drag_mime_type,
            state_key_role=self.tree_state_role,
            series_by_var_uid=self.series_by_var_uid,
            candidates_by_parameter_name=self.candidates_by_parameter_name,
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

    def _get_device_by_entry(self, entry: DynamicPlotEntry) -> ALL_DEV_TYPES | None:
        """
        Resolve the device referenced by one persistent plot entry.

        :param entry: Persistent dynamic plot entry.
        :return: Matching circuit device, or ``None``.
        """
        if self.circuit is not None:
            device: ALL_DEV_TYPES
            for device in self.circuit.get_all_elements_iter():
                if str(device.idtag) == entry.device_idtag:
                    return device
                else:
                    pass
            return None
        else:
            return None

    def _get_parameter_plot_data(self, entry: DynamicPlotEntry) -> tuple[np.ndarray, np.ndarray] | None:
        """
        Resolve plotting arrays for one persistent parameter entry.

        :param entry: Persistent parameter plot entry.
        :return: Plot arrays, or ``None`` when the parameter cannot be resolved.
        """
        if self.results is not None and self.circuit is not None:
            # Parameter plotting is meaningful only after a simulation produced a
            # time axis. Without that axis the GUI must keep the entry pending
            # instead of fabricating a zero-valued or unit-length trace.
            if len(self.results.time_array) == 0:
                return None
            else:
                pass

            # canonical_parameter_name: str = _build_parameter_canonical_name_from_display(entry.variable_name)
            canonical_parameter_name: str = str(entry.variable_name)
            x_values: np.ndarray = _build_relative_time_axis(time_array=self.results.time_array)
            event_group_index: int | None = None
            group_idtags: Sequence[str] = self._get_group_idtags(results=self.results)
            group_names: Sequence[str] = self._get_group_names(results=self.results)
            idx: int
            for idx in range(len(group_idtags)):
                matches_idtag: bool = str(group_idtags[idx]) == entry.event_group_idtag and entry.event_group_idtag != ""
                matches_name: bool = str(group_names[idx]) == entry.event_group_name and entry.event_group_name != ""
                if matches_idtag or matches_name:
                    event_group_index = idx
                else:
                    pass

            if event_group_index is not None:
                if self._has_event_group_results(results=self.results, group_idx=event_group_index):
                    # RMS and EMT currently export parameter snapshots through the
                    # per-event-group ``parameter_value_maps`` structure. When a
                    # snapshot exists, the plotting path uses it as the baseline
                    # parameter value before replaying any matching events. This
                    # keeps plain constant parameters cheap while still allowing
                    # event-driven parameters to show their visible changes.
                    exported_parameter_value: float | None = self.results.get_parameter_value(
                        group_idx=event_group_index,
                        device_idtag=entry.device_idtag,
                        parameter_name=canonical_parameter_name,
                    )
                    if exported_parameter_value is not None:
                        event_plot_data: tuple[np.ndarray, np.ndarray] | None = _build_parameter_plot_data_from_events(
                            circuit=self.circuit,
                            entry=entry,
                            time_axis=x_values,
                            base_value=float(exported_parameter_value),
                        )
                        if event_plot_data is not None:
                            return event_plot_data
                        else:
                            y_values: np.ndarray = np.empty(len(x_values), dtype=float)
                            y_values[:] = float(exported_parameter_value)
                            return x_values, y_values
                    else:
                        pass
                else:
                    # Declared-but-unsimulated event groups intentionally stay
                    # unresolved because their result column would otherwise look
                    # like a valid constant trace even though no simulation ran.
                    return None
            else:
                pass

            device: ALL_DEV_TYPES | None = self._get_device_by_entry(entry=entry)
            if isinstance(device, (DynamicDevice, DynamicBusDevice)):
                # Some parameters are static model constants and therefore do not
                # appear in the exported per-group snapshot map. In that case the
                # live model block still carries the scalar value. That scalar is
                # used as the baseline before replaying matching events, and only
                # falls back to a plain constant trace when no event changes it.
                model_block: Block = _get_pre_simulation_block(device=device, simulation_type=entry.simulation_type)
                parameter_value: float | None = _get_runtime_parameter_scalar_from_block(
                    model=model_block,
                    parameter_name=canonical_parameter_name,
                )
                if parameter_value is not None:
                    event_plot_data = _build_parameter_plot_data_from_events(
                        circuit=self.circuit,
                        entry=entry,
                        time_axis=x_values,
                        base_value=float(parameter_value),
                    )
                    if event_plot_data is not None:
                        return event_plot_data
                    else:
                        y_values: np.ndarray = np.empty(len(x_values), dtype=float)
                        y_values[:] = parameter_value
                        return x_values, y_values
                else:
                    return None
            else:
                return None
        else:
            return None

    def plot_parameter_entry(self, entry: DynamicPlotEntry) -> bool:
        """
        Plot one persistent parameter entry when its value can be resolved.

        :param entry: Persistent parameter plot entry.
        :return: ``True`` when the parameter was resolved and plotted.
        """
        parameter_plot_data: tuple[np.ndarray, np.ndarray] | None = self._get_parameter_plot_data(entry=entry)
        if parameter_plot_data is not None:
            x_values: np.ndarray = parameter_plot_data[0]
            y_values: np.ndarray = parameter_plot_data[1]
            label: str = _build_parameter_plot_entry_label(entry=entry)

            figure = Figure(figsize=(12, 8))
            axis = figure.add_subplot(111)
            axis.plot(x_values, y_values, label=label)
            axis.set_title(entry.variable_name)
            axis.set_xlabel("Time [s]")
            axis.legend()
            self._show_figure(figure=figure, title=entry.variable_name)
            return True
        else:
            return False

    def get_parameter_entry_from_index(self, index: QtCore.QModelIndex) -> DynamicPlotEntry | None:
        """
        Build one transient parameter entry from a source-tree parameter node.

        :param index: Source-model index coming from the dynamics device tree.
        :return: Synthetic parameter entry, or ``None``.
        """
        candidate: DynamicPlotCandidate | None = self.get_candidate_from_index(index=index)
        if candidate is not None:
            if candidate.get_entry_kind() == DynamicPlotEntryKind.PARAMETER:
                synthetic_entry: DynamicPlotEntry = DynamicPlotEntry(
                    variable=None,
                    plot=None,
                    group=None,
                    device=None,
                    simulation_type=candidate._simulation_type,
                    entry_kind=DynamicPlotEntryKind.PARAMETER,
                    event_group_idtag=candidate._event_group_idtag,
                    event_group_name=candidate._event_group_name,
                    curve_device_type=candidate._device_type,
                    device_idtag=candidate._device_idtag,
                    device_name_hint=candidate._device_label,
                    variable_name=candidate._variable_name,
                    result_path_kind=candidate._result_path_kind,
                    variable_custom_name=candidate._variable_custom_name,
                    enabled=True,
                    runtime_series_key_payload="",
                    name=candidate._variable_name,
                )
                return synthetic_entry
            else:
                return None
        else:
            return None

    def plot_parameter_candidate(self, candidate: DynamicPlotCandidate) -> bool:
        """
        Plot one parameter candidate directly from the source tree.

        :param candidate: Source-tree parameter candidate.
        :return: ``True`` when the parameter was resolved and plotted.
        """
        synthetic_entry: DynamicPlotEntry = DynamicPlotEntry(
            variable=None,
            plot=None,
            group=None,
            device=None,
            simulation_type=candidate._simulation_type,
            entry_kind=DynamicPlotEntryKind.PARAMETER,
            event_group_idtag=candidate._event_group_idtag,
            event_group_name=candidate._event_group_name,
            curve_device_type=candidate._device_type,
            device_idtag=candidate._device_idtag,
            device_name_hint=candidate._device_label,
            variable_name=candidate._variable_name,
            result_path_kind=candidate._result_path_kind,
            variable_custom_name=candidate._variable_custom_name,
            enabled=True,
            runtime_series_key_payload="",
            name=candidate._variable_name,
        )
        return self.plot_parameter_entry(entry=synthetic_entry)

    def _get_series_plot_data(self, series: DynamicResultSeries) -> tuple[np.ndarray, np.ndarray]:
        """
        Get the relative-time x-axis and the y-axis for one plotted series.

        :param series: Source-specific dynamic series selected for plotting.
        :return: Tuple ``(x_values, y_values)`` with a relative float time axis and the matching signal values.

        The plotting layer works best with an elapsed-time axis because absolute
        datetime stamps are rendered as wall-clock labels by Matplotlib. This
        method therefore converts the stored simulation timestamps into a float
        axis that starts at ``0.0`` while preserving the original sample count.
        """
        # The x-axis is normalized to elapsed seconds so the chart shows the
        # simulation progression instead of absolute timestamp formatting.
        x_values: np.ndarray = _build_relative_time_axis(time_array=self.results.time_array)
        key: DynamicResultSeriesKey = series.get_key()
        group_idx: int = series.get_group_idx()

        result_path_prefix: str = key._result_path.split(":", 1)[0]

        if result_path_prefix == "values":
            # ``values`` stores the main simulated state history for the selected
            # component and event group, so the slice maps one series to one line.
            y_values: np.ndarray = np.asarray(self.results.values[:, key._component_index, group_idx])
        elif result_path_prefix == "diff_values":
            if isinstance(self.results, EmtResults):
                # EMT derivative series are stored in ``diff_values`` and use the
                # same time axis as the primary values array.
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
        devices_data: Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]
        for device_tpe, devices_data in self.tree_data.items():
            # The device type is not part of the requested matching rule.
            # It is still iterated because the result tree is grouped by device type.
            del device_tpe

            device: ALL_DEV_TYPES
            entry_collection: DynamicDeviceEntryCollection
            for device, entry_collection in devices_data.items():
                # The legacy signature supplements the stable device idtag with the
                # visible device name. This avoids matching a different visible
                # device after a rename, but it also means renames can prevent
                # legacy entries from being restored.
                device_idtag: str = str(device.idtag)
                device_name: str = str(device.name)
                variables: List[Var] = entry_collection.get_variables()

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
        devices_data: Dict[ALL_DEV_TYPES, DynamicDeviceEntryCollection]
        for device_tpe, devices_data in self.tree_data.items():
            del device_tpe

            device: ALL_DEV_TYPES
            entry_collection: DynamicDeviceEntryCollection
            for device, entry_collection in devices_data.items():
                device_idtag: str = str(device.idtag)
                device_name: str = str(device.name)
                variables: List[Var] = entry_collection.get_variables()

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
