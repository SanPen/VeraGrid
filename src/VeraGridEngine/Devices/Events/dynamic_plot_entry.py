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
from VeraGridEngine.enumerations import DeviceType, SubObjectType, PrpCat


class DynamicPlotEntry(EditableDevice):
    """
    Dynamic plot event
    """
    __slots__ = (
        'variable',
        'plot',
        'group',
        'device'
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
    )

    def __init__(self,
                 variable: Var = None,
                 plot: DynamicPlot = None,
                 group: RmsEventsGroup = None,
                 device: Any = None,
                 idtag: Union[str, None] = None,
                 name="RmsEvent",
                 code='',
                 comment: str = ""):
        """
        Rms Event
        :param variable: parameter
        :param plot: Plot group
        :param group: RmsEventsGroup
        :param name: String. Event name
        :param code: String. Event code name
        :param group: RmsEventsGroup. RmsEvent group
        :param comment: Comment
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
