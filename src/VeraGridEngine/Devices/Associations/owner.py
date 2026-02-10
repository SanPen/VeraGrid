# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0


from typing import Union
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType


class Owner(EditableDevice):
    __slots__ = ('address', 'color')

    def __init__(self, name: str = '',
                 code: str = '',
                 idtag: Union[str, None] = None,
                 color: Union[str, None] = None):
        """
        Technology
        :param name: name of the technology
        :param code: secondary id
        :param idtag: UUID code
        :param color: hexadecimal color string (i.e. #AA00FF)
        """
        EditableDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=DeviceType.Owner)

        self.address = ""

        self.color = color if color is not None else self.rnd_color()

        self.register(key='address', units='', tpe=str, definition='Owner address')
        self.register(key='color', units='', tpe=str, definition='Color to paint', is_color=True)
