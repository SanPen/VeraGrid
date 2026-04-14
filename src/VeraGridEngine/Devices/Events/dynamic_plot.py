# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from typing import Union
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType


class DynamicPlot(EditableDevice):
    """
    Dynamic plot
    """
    __slots__ = (

    )

    def __init__(self,
                 idtag: Union[str, None] = None,
                 name: str = "EmtEventsGroup",
                 comment: str = ""):
        """
        Contingency group
        :param idtag: Unique identifier
        :param name: contingency group name
        :param comment: comment
        """

        EditableDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code='',
                                device_type=DeviceType.DynamicPlotGroupDevice,
                                comment=comment)
