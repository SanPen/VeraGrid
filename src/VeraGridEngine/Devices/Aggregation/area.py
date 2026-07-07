# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Union, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType, GCProp
from VeraGridEngine.enumerations import PrpCat

class GenericAreaGroup(EditableDevice):
    __slots__ = (
        '_latitude',
        '_longitude',
        'color',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='longitude',
            units='deg',
            tpe=float,
            definition='longitude.',
            profile_name='',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='latitude',
            units='deg',
            tpe=float,
            definition='latitude.',
            profile_name='',
            cat=[PrpCat.TP],
        ),
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
                 device_type=DeviceType.GenericArea, latitude=0.0, longitude=0.0, color: str | None = None):
        """

        :param name:
        :param idtag:
        :param device_type:
        :param latitude:
        :param longitude:
        """
        EditableDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=device_type)

        self.latitude = float(latitude)
        self.longitude = float(longitude)

        self.color = color if color is not None else self.rnd_color()

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def longitude(self) -> float:
        """
        Get ``longitude``.

        :return: float
        """
        return self._longitude

    @longitude.setter
    def longitude(self, val: float) -> None:
        """
        Set ``longitude``.

        :param val: Value to assign.
        :return: None
        """
        self._longitude = float(val)

    @property
    def latitude(self) -> float:
        """
        Get ``latitude``.

        :return: float
        """
        return self._latitude

    @latitude.setter
    def latitude(self, val: float) -> None:
        """
        Set ``latitude``.

        :param val: Value to assign.
        :return: None
        """
        self._latitude = float(val)



class Area(GenericAreaGroup):

    def __init__(self, name: str = 'Area', idtag: Union[str, None] = None, code: str = '', latitude=0.0, longitude=0.0):
        """
        Area constructor
        :param name: name of the area
        :param idtag: UUID code
        :param latitude: latitude (deg)
        :param longitude: longutide (deg)
        """
        GenericAreaGroup.__init__(self,
                                  name=name,
                                  idtag=idtag,
                                  code=code,
                                  device_type=DeviceType.AreaDevice,
                                  latitude=latitude,
                                  longitude=longitude)
