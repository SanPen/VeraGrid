# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Any, Tuple

from VeraGridEngine import SubObjectType
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType


class EmtEvent(PointerDeviceParent):
    """
    Investment
    """
    __slots__ = (
        'parameter',
        'time',
        'value',
        '_group',
        'force_step_alignment'
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key='parameter', units='', tpe=SubObjectType.VarType,
                      definition='parameter that the event changes'),
        GCProp(key='time', units='', tpe=float,
                      definition='Time when the event occurs'),
        GCProp(key='value', units='', tpe=float,
                      definition='New value for the parameter'),
        GCProp(key='group', units='', tpe=DeviceType.EmtEventsGroupDevice, definition='RmsEvent group'),
        GCProp(key='force_step_alignment', units='', tpe=bool,
               definition='Force step alignment'),
    )

    def __init__(self,
                 device: EditableDevice | None = None,
                 parameter: Var = None,
                 time: float = None,
                 value: float = None,
                 group: EmtEventsGroup = None,
                 force_step_alignment: bool = False,
                 idtag: Union[str, None] = None,
                 name="EmtEvent",
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
                                     device_type=DeviceType.EmtEventDevice,
                                     comment=comment)


        self._group: EmtEventsGroup = group
        self.parameter: Any = parameter
        self.time: float = float(time) if time is not None else 0.0
        self.value: float = float(value) if value is not None else 0.0
        self.force_step_alignment: bool = bool(force_step_alignment)


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
