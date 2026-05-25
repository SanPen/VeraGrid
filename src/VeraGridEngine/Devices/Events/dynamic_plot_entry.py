# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Any, Tuple, List
# from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.Devices.Events.dynamic_plot import DynamicPlot
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, SubObjectType, PrpCat, PlotSimulationType


class DynamicPlotEntry(EditableDevice):
    """
    Persistent dynamic plot curve reference.

    The entry stores the semantic identity of one requested dynamic curve so it
    can exist before simulation results are available and can later be rebound to
    runtime result series. Stable identifiers such as event-group and device
    idtags are preferred over visible names.

    The legacy ``variable`` and ``group`` references are preserved as optional
    compatibility hints, but the canonical identity is the explicit semantic
    fields declared on this asset. Unresolved entries must remain stored in the
    project so later simulations can try to bind them again.
    """
    __slots__ = (
        'variable',
        'plot',
        'group',
        'device',
        '_simulation_type',
        '_event_group_idtag',
        '_event_group_name',
        '_curve_device_type',
        '_device_idtag',
        '_device_name_hint',
        '_variable_name',
        '_result_path_kind',
        '_variable_custom_name',
        '_enabled',
        '_runtime_series_key_payload',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='variable',
            units='',
            tpe=SubObjectType.VarType,
            definition='parameter that the event changes',
            cat=[PrpCat.RMS],
        ),
        GCProp(
            prop_name='plot',
            units='',
            tpe=DeviceType.DynamicPlotGroupDevice,
            definition='Plot group',
            cat=[PrpCat.RMS],
        ),
        GCProp(
            prop_name='group',
            units='',
            tpe=DeviceType.RmsEventsGroupDevice,
            definition='RmsEvent group',
            cat=[PrpCat.RMS],
        ),
        GCProp(
            prop_name='simulation_type',
            units='',
            tpe=PlotSimulationType,
            definition='Simulation family for this persistent curve reference.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='event_group_idtag',
            units='',
            tpe=str,
            definition='Stable event-group identifier preferred for result binding.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='event_group_name',
            units='',
            tpe=str,
            definition='Event-group visible name used as display text and fallback binding hint.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='curve_device_type',
            units='',
            tpe=DeviceType,
            definition='Device type that owns the referenced dynamic variable.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='device_idtag',
            units='',
            tpe=str,
            definition='Stable device identifier preferred for result binding.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='device_name_hint',
            units='',
            tpe=str,
            definition='Visible device-name hint used only for display and diagnostics.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='variable_name',
            units='',
            tpe=str,
            definition='Dynamic variable name requested by the user.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='result_path_kind',
            units='',
            tpe=str,
            definition='Result namespace such as values or diff_values.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='variable_custom_name',
            units='',
            tpe=str,
            definition='Optional custom visible name remembered for this variable.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='enabled',
            units='',
            tpe=bool,
            definition='Whether this persistent curve definition is enabled.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
        GCProp(
            prop_name='runtime_series_key_payload',
            units='',
            tpe=str,
            definition='Optional cached runtime series identity payload used as an exact binding hint.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
    )

    def __init__(self,
                  variable: Var = None,
                  plot: DynamicPlot = None,
                  group: RmsEventsGroup = None,
                  device: Any = None,
                  simulation_type: PlotSimulationType = PlotSimulationType.RMS,
                  event_group_idtag: str = "",
                  event_group_name: str = "",
                  curve_device_type: DeviceType = DeviceType.NoDevice,
                  device_idtag: str = "",
                  device_name_hint: str = "",
                  variable_name: str = "",
                  result_path_kind: str = "",
                  variable_custom_name: str = "",
                  enabled: bool = True,
                  runtime_series_key_payload: str = "",
                  idtag: Union[str, None] = None,
                  name: str = "RmsEvent",
                  code='',
                  comment: str = ""):
        """
        Build one persistent dynamic curve definition.

        :param variable: Legacy symbolic variable hint, when still available.
        :param plot: Persistent parent plot group.
        :param group: Legacy RMS event-group hint.
        :param device: Optional legacy device hint.
        :param simulation_type: Simulation family identifier.
        :param event_group_idtag: Stable event-group identifier.
        :param event_group_name: Visible event-group name.
        :param curve_device_type: Device type that owns the curve.
        :param device_idtag: Stable device identifier.
        :param device_name_hint: Visible device-name hint.
        :param variable_name: Variable name selected by the user.
        :param result_path_kind: Result namespace such as ``values`` or ``diff_values``.
        :param variable_custom_name: Optional remembered custom visible variable name.
        :param enabled: ``True`` when the curve is enabled.
        :param runtime_series_key_payload: Optional cached runtime exact-match payload.
        :param idtag: Persistent entry identifier.
        :param name: Entry name.
        :param code: Secondary code.
        :param comment: Optional user comment.
        :return: None.
        """

        EditableDevice.__init__(self,
                                idtag=idtag,
                                code=code,
                                name=name,
                                device_type=DeviceType.DynamicPlotEntry,
                                comment=comment)

        self.variable: Any = variable
        self.device: Any = device
        self.group: RmsEventsGroup = group
        self.plot: DynamicPlot = plot
        self._simulation_type: PlotSimulationType = PlotSimulationType.RMS
        self.simulation_type = simulation_type
        self._event_group_idtag: str = str(event_group_idtag)
        self._event_group_name: str = str(event_group_name)
        self._curve_device_type: DeviceType = (
            curve_device_type if isinstance(curve_device_type, DeviceType) else DeviceType.NoDevice
        )
        self._device_idtag: str = str(device_idtag)
        self._device_name_hint: str = str(device_name_hint)
        self._variable_name: str = str(variable_name)
        self._result_path_kind: str = str(result_path_kind)
        self._variable_custom_name: str = str(variable_custom_name)
        self._enabled: bool = bool(enabled)
        self._runtime_series_key_payload: str = str(runtime_series_key_payload)

    @property
    def simulation_type(self) -> PlotSimulationType:
        """
        Get the simulation family identifier.

        :return: Simulation family identifier.
        """
        return self._simulation_type

    @simulation_type.setter
    def simulation_type(self, val: PlotSimulationType) -> None:
        """
        Set the simulation family identifier.

        :param val: Simulation family identifier.
        :return: None.
        """
        if isinstance(val, PlotSimulationType):
            self._simulation_type = val
        else:
            raise ValueError("Unsupported plot simulation type")

    @property
    def event_group_idtag(self) -> str:
        """
        Get the stable event-group identifier.

        :return: Event-group idtag.
        """
        return self._event_group_idtag

    @event_group_idtag.setter
    def event_group_idtag(self, val: str) -> None:
        """
        Set the stable event-group identifier.

        :param val: Event-group idtag.
        :return: None.
        """
        self._event_group_idtag = str(val)

    @property
    def event_group_name(self) -> str:
        """
        Get the visible event-group name.

        :return: Event-group visible name.
        """
        return self._event_group_name

    @event_group_name.setter
    def event_group_name(self, val: str) -> None:
        """
        Set the visible event-group name.

        :param val: Event-group visible name.
        :return: None.
        """
        self._event_group_name = str(val)

    @property
    def curve_device_type(self) -> DeviceType:
        """
        Get the device type that owns the referenced variable.

        :return: Device type.
        """
        return self._curve_device_type

    @curve_device_type.setter
    def curve_device_type(self, val: DeviceType) -> None:
        """
        Set the device type that owns the referenced variable.

        :param val: Device type.
        :return: None.
        """
        if isinstance(val, DeviceType):
            self._curve_device_type = val
        else:
            self._curve_device_type = DeviceType.NoDevice

    @property
    def device_idtag(self) -> str:
        """
        Get the stable device identifier.

        :return: Device idtag.
        """
        return self._device_idtag

    @device_idtag.setter
    def device_idtag(self, val: str) -> None:
        """
        Set the stable device identifier.

        :param val: Device idtag.
        :return: None.
        """
        self._device_idtag = str(val)

    @property
    def device_name_hint(self) -> str:
        """
        Get the visible device-name hint.

        :return: Device-name hint.
        """
        return self._device_name_hint

    @device_name_hint.setter
    def device_name_hint(self, val: str) -> None:
        """
        Set the visible device-name hint.

        :param val: Device-name hint.
        :return: None.
        """
        self._device_name_hint = str(val)

    @property
    def variable_name(self) -> str:
        """
        Get the requested variable name.

        :return: Variable name.
        """
        return self._variable_name

    @variable_name.setter
    def variable_name(self, val: str) -> None:
        """
        Set the requested variable name.

        :param val: Variable name.
        :return: None.
        """
        self._variable_name = str(val)

    @property
    def result_path_kind(self) -> str:
        """
        Get the result namespace for this curve.

        :return: Result namespace identifier.
        """
        return self._result_path_kind

    @result_path_kind.setter
    def result_path_kind(self, val: str) -> None:
        """
        Set the result namespace for this curve.

        :param val: Result namespace identifier.
        :return: None.
        """
        self._result_path_kind = str(val)

    @property
    def variable_custom_name(self) -> str:
        """
        Get the remembered custom visible variable name.

        :return: Custom visible variable name.
        """
        return self._variable_custom_name

    @variable_custom_name.setter
    def variable_custom_name(self, val: str) -> None:
        """
        Set the remembered custom visible variable name.

        :param val: Custom visible variable name.
        :return: None.
        """
        self._variable_custom_name = str(val)

    @property
    def enabled(self) -> bool:
        """
        Get whether the curve is enabled.

        :return: ``True`` when enabled.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, val: bool) -> None:
        """
        Set whether the curve is enabled.

        :param val: Enabled state.
        :return: None.
        """
        self._enabled = bool(val)

    @property
    def runtime_series_key_payload(self) -> str:
        """
        Get the cached runtime exact-match payload.

        :return: Serialized runtime series key payload.
        """
        return self._runtime_series_key_payload

    @runtime_series_key_payload.setter
    def runtime_series_key_payload(self, val: str) -> None:
        """
        Set the cached runtime exact-match payload.

        :param val: Serialized runtime series key payload.
        :return: None.
        """
        self._runtime_series_key_payload = str(val)


def compare_dynamic_plots(dyn_plots1: List[DynamicPlot],
                          dyn_plots2: List[DynamicPlot],
                          dyn_plots1_entries: List[DynamicPlotEntry],
                          dyn_plots2_entries: List[DynamicPlotEntry]) -> bool:
    """
    Compare persistent dynamic plot groups and entries after a save/load cycle.

    The comparison validates both plot groups and their curve entries using the
    registered persistence schema. Entry-to-plot references are compared through
    the corresponding plot position so the check does not depend on Python object
    identity after reloading the file.

    :param dyn_plots1: Dynamic plot collection from the original grid.
    :param dyn_plots2: Dynamic plot collection from the reloaded grid.
    :param dyn_plots1_entries: Dynamic plot entry collection from the original grid.
    :param dyn_plots2_entries: Dynamic plot entry collection from the reloaded grid.
    :return: ``True`` when both persistent collections are exactly equal.
    """
    equal: bool = True
    plot_count1: int = len(dyn_plots1)
    plot_count2: int = len(dyn_plots2)
    entry_count1: int = len(dyn_plots1_entries)
    entry_count2: int = len(dyn_plots2_entries)

    # The plot collections must preserve their size and ordering because entries
    # refer back to plots through this stable serialized structure.
    if plot_count1 == plot_count2:
        plot_index: int
        for plot_index in range(plot_count1):
            plot1: DynamicPlot = dyn_plots1[plot_index]
            plot2: DynamicPlot = dyn_plots2[plot_index]

            # Comparing registered properties aligns the equality check with the
            # exact fields that the serializer persists into the project file.
            if not compare_dynamic_plot(plot1=plot1, plot2=plot2):
                equal = False
            else:
                pass
    else:
        equal = False

    # The entry collections must preserve both the per-entry payload and the link
    # to the owning persistent plot group.
    if entry_count1 == entry_count2:
        entry_index: int
        for entry_index in range(entry_count1):
            entry1: DynamicPlotEntry = dyn_plots1_entries[entry_index]
            entry2: DynamicPlotEntry = dyn_plots2_entries[entry_index]

            if not compare_dynamic_plot_entry(entry1=entry1,
                                              entry2=entry2,
                                              dyn_plots1=dyn_plots1,
                                              dyn_plots2=dyn_plots2):
                equal = False
            else:
                pass
    else:
        equal = False

    return equal


def compare_dynamic_plot(plot1: DynamicPlot, plot2: DynamicPlot) -> bool:
    """
    Compare two persistent dynamic plot groups.

    The plot comparison uses the saved headers and saved values because those are
    the fields that define the project persistence contract for the plot group.

    :param plot1: Original plot group.
    :param plot2: Reloaded plot group.
    :return: ``True`` when the two plot groups are equal.
    """
    headers1: List[str] = list(plot1.get_headers())
    headers2: List[str] = list(plot2.get_headers())
    values1: List[Any] = list(plot1.get_save_data())
    values2: List[Any] = list(plot2.get_save_data())
    equal: bool = True

    # The saved schema must match before individual fields can be trusted as a
    # meaningful equality comparison.
    if headers1 == headers2:
        header_index: int
        for header_index in range(len(headers1)):
            header_name: str = headers1[header_index]
            value1: Any = values1[header_index]
            value2: Any = values2[header_index]

            # The runtime merge-tracking object is not part of the serialized
            # payload, so it must not participate in the persistence comparison.
            if header_name != 'diff_changes':
                # Plot groups otherwise store only simple persistent values, so
                # direct equality keeps the logic easy to inspect.
                if value1 != value2:
                    equal = False
                else:
                    pass
            else:
                pass
    else:
        equal = False

    return equal


def compare_dynamic_plot_entry(entry1: DynamicPlotEntry,
                               entry2: DynamicPlotEntry,
                               dyn_plots1: List[DynamicPlot],
                               dyn_plots2: List[DynamicPlot]) -> bool:
    """
    Compare two persistent dynamic plot entries.

    The entry comparison checks all saved fields and also verifies that the two
    entries point to the corresponding plot position in their owning plot lists.
    This keeps the comparison exact without relying on Python object identity
    across two separately loaded grids.

    :param entry1: Original entry.
    :param entry2: Reloaded entry.
    :param dyn_plots1: Original plot collection.
    :param dyn_plots2: Reloaded plot collection.
    :return: ``True`` when the two entries are equal.
    """
    headers1: List[str] = list(entry1.get_headers())
    headers2: List[str] = list(entry2.get_headers())
    values1: List[Any] = list(entry1.get_save_data())
    values2: List[Any] = list(entry2.get_save_data())
    equal: bool = True
    plot_index1: int | None = None
    plot_index2: int | None = None

    # The saved field layout must be the same before any per-field comparison is valid.
    if headers1 == headers2:
        header_index: int
        for header_index in range(len(headers1)):
            header_name: str = headers1[header_index]
            value1: Any = values1[header_index]
            value2: Any = values2[header_index]

            # The runtime merge-tracking object is not part of the serialized
            # payload, so it must not participate in the persistence comparison.
            if header_name != 'diff_changes':
                # Entry plot references are checked with the explicit plot-index
                # logic below because the object itself belongs to a different
                # in-memory graph after reloading the file.
                if header_name != 'plot':
                    if value1 != value2:
                        equal = False
                    else:
                        pass
                else:
                    pass
            else:
                pass
    else:
        equal = False

    # The owning plot relation is part of the saved graph, therefore each entry
    # must resolve to the corresponding plot position in its own grid instance.
    if entry1.plot is not None:
        plot_list_index1: int
        for plot_list_index1 in range(len(dyn_plots1)):
            candidate_plot1: DynamicPlot = dyn_plots1[plot_list_index1]
            if candidate_plot1 is entry1.plot:
                plot_index1 = plot_list_index1
                break
            else:
                pass
    else:
        plot_index1 = None

    if entry2.plot is not None:
        plot_list_index2: int
        for plot_list_index2 in range(len(dyn_plots2)):
            candidate_plot2: DynamicPlot = dyn_plots2[plot_list_index2]
            if candidate_plot2 is entry2.plot:
                plot_index2 = plot_list_index2
                break
            else:
                pass
    else:
        plot_index2 = None

    if plot_index1 != plot_index2:
        equal = False
    else:
        pass

    return equal
