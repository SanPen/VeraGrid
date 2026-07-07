# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Union, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType, GCProp
from VeraGridEngine.enumerations import PrpCat

class MarketUnit(EditableDevice):
    __slots__ = (
        'color',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (

        GCProp(
            prop_name='color',
            units='',
            tpe=str,
            definition='Color to paint the element in the map diagram',
            is_color=True,
            cat=[PrpCat.TP],
        ),
    )

    def __init__(self, name='', code='', idtag: Union[str, None] = None,
                 color: str | None = None):
        """

        :param name:
        :param idtag:
        """
        EditableDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=DeviceType.MarketUnitDevice)

        self.color = color if color is not None else self.rnd_color()
