# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Union, Tuple

from VeraGridEngine.Devices.Parents.editable_device import DeviceType, GCProp
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Devices.Aggregation.market_units_group import MarketUnitsGroup
from VeraGridEngine.Devices.Aggregation.facility import Facility
from VeraGridEngine.enumerations import PrpCat


class MarketUnit(PointerDeviceParent):
    __slots__ = (
        'color',
        '_group',
        '_commissioning_date',
        '_decommissioning_date',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (

        GCProp(
            prop_name='group',
            units='',
            tpe=DeviceType.MarketUnitsGroupDevice,
            definition='Investment group',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='commissioning_date',
            units='',
            tpe=float,
            definition='Date when the investment is commissioned',
            cat=[PrpCat.INV],
            is_date=True
        ),
        GCProp(
            prop_name='decommissioning_date',
            units='',
            tpe=float,
            definition='Date when the investment is decommissioned',
            cat=[PrpCat.INV],
            is_date=True
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

    def __init__(self,
                 device: Facility | None = None,
                 idtag: Union[str, None] = None,
                 name='', code='',
                 color: str | None = None,
                 group: MarketUnitsGroup | None = None,
                 commissioning_date: float = 0,
                 decommissioning_date: float = 0,
                 comment: str = ""):
        """

        :param name:
        :param idtag:
        """
        PointerDeviceParent.__init__(self,
                                     idtag=idtag,
                                     device=device,
                                     code=code,
                                     name=name,
                                     device_type=DeviceType.MarketUnitDevice,
                                     comment=comment,
                                     pointer_dev_tpes=[DeviceType.FacilityDevice])

        self.color = color if color is not None else self.rnd_color()

        self._group: MarketUnitsGroup | None = group
        self._commissioning_date: float = commissioning_date
        self._decommissioning_date: float = decommissioning_date

    @property
    def group(self) -> MarketUnitsGroup | None:
        """
        Group of investments
        :return:
        """
        return self._group

    @group.setter
    def group(self, val: MarketUnitsGroup):
        self._group = val

    @property
    def commissioning_date(self) -> float:
        """
        Get ``status``.

        :return: bool
        """
        return self._commissioning_date

    @commissioning_date.setter
    def commissioning_date(self, val: float) -> None:
        """
        Set ``status``.

        :param val: Value to assign.
        :return: None
        """
        self._commissioning_date = val

    @property
    def decommissioning_date(self) -> float:
        """
        Get ``status``.

        :return: bool
        """
        return self._decommissioning_date

    @decommissioning_date.setter
    def decommissioning_date(self, val: float) -> None:
        """
        Set ``status``.

        :param val: Value to assign.
        :return: None
        """
        self._decommissioning_date = val
