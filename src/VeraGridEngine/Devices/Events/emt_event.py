# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Any, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, DynamicEventTransitionType, SubObjectType, PrpCat


class EmtEvent(PointerDeviceParent):
    """
    Investment
    """
    __slots__ = (
        'parameter',
        'time',
        '_end_time',
        'value',
        '_group',
        'force_step_alignment',
        '_transition_type',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='parameter',
            units='',
            tpe=SubObjectType.VarType,
            definition='parameter that the event changes',
            cat=[PrpCat.EMT],
        ),
        GCProp(
            prop_name='time',
            units='',
            tpe=float,
            definition='Time when the event occurs',
            cat=[PrpCat.EMT],
        ),
        GCProp(
            prop_name='end_time',
            units='',
            tpe=float,
            definition='End time used by ramp events',
            cat=[PrpCat.EMT],
        ),
        GCProp(
            prop_name='value',
            units='',
            tpe=float,
            definition='New value for the parameter',
            cat=[PrpCat.EMT],
        ),
        GCProp(
            prop_name='group',
            units='',
            tpe=DeviceType.EmtEventsGroupDevice,
            definition='EmtEvent group',
            cat=[PrpCat.EMT],
        ),
        GCProp(
            prop_name='force_step_alignment',
            units='',
            tpe=bool,
            definition='Force step alignment',
            cat=[PrpCat.EMT],
        ),
        GCProp(
            prop_name='transition_type',
            units='',
            tpe=DynamicEventTransitionType,
            definition='Transition profile for the event',
            cat=[PrpCat.EMT],
        ),
    )

    def __init__(self,
                 device: EditableDevice | None = None,
                 parameter: Var = None,
                 time: float = None,
                 end_time: float | None = None,
                 value: float = None,
                 group: EmtEventsGroup = None,
                 force_step_alignment: bool = False,
                 transition_type: DynamicEventTransitionType = DynamicEventTransitionType.Step,
                 idtag: Union[str, None] = None,
                 name="EmtEvent",
                 code='',

                 comment: str = ""):
        """
        Rms Event
        :param device: Some device to point at
        :param parameter: parameter
        :param time: time
        :param end_time: end time used by ramp events
        :param value: value
        :param force_step_alignment: Trigger time-step subdivision for this event (EMT)
        :param transition_type: Step or ramp transition profile
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
                                     device_type=DeviceType.EmtEventDevice,
                                     comment=comment)


        self._group: EmtEventsGroup = group
        self.parameter: Any = parameter
        self.time: float = float(time) if time is not None else 0.0
        self.end_time: float = float(end_time) if end_time is not None else self.time+1e-20
        self.value: float = float(value) if value is not None else 0.0
        self.force_step_alignment: bool = bool(force_step_alignment)
        self.transition_type: DynamicEventTransitionType = transition_type


    @property
    def group(self) -> EmtEventsGroup:
        """
        Group of events
        :return:
        """
        return self._group

    @group.setter
    def group(self, val: EmtEventsGroup):
        self._group = val

    @property
    def transition_type(self) -> DynamicEventTransitionType:
        """
        Get ``transition_type``.

        :return: Dynamic event transition type.
        """
        return self._transition_type

    @transition_type.setter
    def transition_type(self, val: DynamicEventTransitionType) -> None:
        """
        Set ``transition_type``.

        :param val: Value to assign.
        :return: None.
        """
        if isinstance(val, DynamicEventTransitionType):
            self._transition_type = val
        else:
            raise TypeError("transition_type must be DynamicEventTransitionType")

    @property
    def end_time(self) -> float | None:
        """
        Get ``end_time``.

        :return: Optional event end time.
        """
        return self._end_time

    @end_time.setter
    def end_time(self, val: float) -> None:
        """
        Set ``end_time``.

        :param val: Value to assign.
        :return: None.
        """

        self._end_time = float(val)
