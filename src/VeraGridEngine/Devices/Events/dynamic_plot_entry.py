# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Any, Tuple
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
        '_curve_label',
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
            prop_name='curve_label',
            units='',
            tpe=str,
            definition='Optional display label remembered for this curve.',
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
                  simulation_type: PlotSimulationType | str = PlotSimulationType.RMS,
                  event_group_idtag: str = "",
                  event_group_name: str = "",
                  curve_device_type: DeviceType = DeviceType.NoDevice,
                  device_idtag: str = "",
                  device_name_hint: str = "",
                  variable_name: str = "",
                  result_path_kind: str = "",
                  curve_label: str = "",
                  enabled: bool = True,
                  runtime_series_key_payload: str = "",
                  idtag: Union[str, None] = None,
                  name="RmsEvent",
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
        :param curve_label: Optional remembered display label.
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
        self._curve_label: str = str(curve_label)
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
    def simulation_type(self, val: PlotSimulationType | str) -> None:
        """
        Set the simulation family identifier.

        :param val: Simulation family identifier.
        :return: None.
        """
        if isinstance(val, PlotSimulationType):
            self._simulation_type = val
        else:
            if isinstance(val, str):
                self._simulation_type = PlotSimulationType(val)
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
    def curve_label(self) -> str:
        """
        Get the remembered display label.

        :return: Curve display label.
        """
        return self._curve_label

    @curve_label.setter
    def curve_label(self, val: str) -> None:
        """
        Set the remembered display label.

        :param val: Curve display label.
        :return: None.
        """
        self._curve_label = str(val)

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
