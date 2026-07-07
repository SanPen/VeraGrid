# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType, GCProp


class RmsEventsGroup(EditableDevice):
    """
    Rms Events Group (Used for both RMS and EMT dynamic events)
    """
    __slots__ = ()


    def __init__(self,
                 idtag: Union[str, None] = None,
                 name: str = "RmsEventsGroup",
                 comment: str = ""):
        """
        Rms events group
        :param idtag: Unique identifier
        :param name: group name
        :param comment: comment
        """

        EditableDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code='',
                                device_type=DeviceType.RmsEventsGroupDevice,
                                comment=comment)


