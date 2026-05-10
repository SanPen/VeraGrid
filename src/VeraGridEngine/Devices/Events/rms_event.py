# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Any, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, SubObjectType, PrpCat


class RmsEvent(PointerDeviceParent):
    """
    Investment
    """
    __slots__ = (
        'parameter',
        '_time',
        '_value',
        '_group',
        '_force_step_alignment',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='parameter',
            units='',
            tpe=SubObjectType.VarType,
            definition='parameter that the event changes',
            cat=[PrpCat.RMS],
        ),
        GCProp(
            prop_name='time',
            units='',
            tpe=float,
            definition='Time when the event occurs',
            cat=[PrpCat.RMS],
        ),
        GCProp(
            prop_name='value',
            units='',
            tpe=float,
            definition='New value for the parameter',
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
            prop_name='force_step_alignment',
            units='',
            tpe=bool,
            definition='Force step alignment',
            cat=[PrpCat.RMS],
        ),
    )

    def __init__(self,
                 device: EditableDevice | None = None,
                 parameter: Var = None,
                 time: float = None,
                 value: float = None,
                 group: RmsEventsGroup = None,
                 force_step_alignment: bool = False,
                 idtag: Union[str, None] = None,
                 name="RmsEvent",
                 code='',

                 comment: str = ""):
        """
        Rms Event
        :param device: Some device to point at
        :param parameter: parameter
        :param time: time
        :param value: value
        :param force_step_alignment: Trigger time-step subdivision for this event (EMT)
        :param idtag: String. Element unique identifier
        :param name: String. Event name
        :param code: String. Event code name
        :param group: RmsEventsGroup. RmsEvent group
        :param comment: Comment
        """

        PointerDeviceParent.__init__(self,
                                     idtag=idtag,
                                     device=device,
                                     code=code,
                                     name=name,
                                     device_type=DeviceType.RmsEventDevice,
                                     comment=comment)


        self._group: RmsEventsGroup = group
        self.parameter: Any = parameter
        self.time: float = float(time) if time is not None else 0.0
        self.value: float = float(value) if value is not None else 0.0
        self.force_step_alignment: bool = bool(force_step_alignment)


    @property
    def group(self) -> RmsEventsGroup:
        """
        Group of events
        :return:
        """
        return self._group

    @group.setter
    def group(self, val: RmsEventsGroup):
        self._group = val

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def time(self) -> float:
        """
        Get ``time``.

        :return: float
        """
        return self._time

    @time.setter
    def time(self, val: float) -> None:
        """
        Set ``time``.

        :param val: Value to assign.
        :return: None
        """
        self._time = float(val)

    @property
    def value(self) -> float:
        """
        Get ``value``.

        :return: float
        """
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        """
        Set ``value``.

        :param val: Value to assign.
        :return: None
        """
        self._value = float(val)

    @property
    def force_step_alignment(self) -> bool:
        """
        Get ``force_step_alignment``.

        :return: bool
        """
        return self._force_step_alignment

    @force_step_alignment.setter
    def force_step_alignment(self, val: bool) -> None:
        """
        Set ``force_step_alignment``.

        :param val: Value to assign.
        :return: None
        """
        self._force_step_alignment = bool(val)
