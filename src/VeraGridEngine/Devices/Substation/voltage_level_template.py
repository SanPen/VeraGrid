# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple

from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.enumerations import DeviceType, VoltageLevelTypes, PrpCat


class VoltageLevelTemplate(EditableDevice):

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='vl_type',
            units='',
            tpe=VoltageLevelTypes,
            definition='Voltage level type',
            editable=True,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='voltage',
            units='kV',
            tpe=float,
            definition='Voltage.',
            editable=True,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='n_bays',
            units='',
            tpe=int,
            definition='Number of bays or modules to add.',
            editable=True,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='add_disconnectors',
            units='',
            tpe=bool,
            definition='Add disconnectors additionally to the circuit breakers',
            editable=True,
            cat=[PrpCat.TP],
        ),
    )

    def __init__(self,
                 name='',
                 code='',
                 idtag: str | None = None,
                 device_type=DeviceType.GenericArea,
                 voltage: float = 10,
                 n_bays: int = 1):
        """

        :param name:
        :param code:
        :param idtag:
        :param device_type:
        :param voltage:
        :param n_bays:
        """
        EditableDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=device_type)

        self.vl_type: VoltageLevelTypes = VoltageLevelTypes.SingleBar
        self.voltage: float = voltage
        self.n_bays: int = n_bays
        self.add_disconnectors: bool = False

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def voltage(self) -> float:
        """
        Get ``voltage``.

        :return: float
        """
        return self._voltage

    @voltage.setter
    def voltage(self, val: float) -> None:
        """
        Set ``voltage``.

        :param val: Value to assign.
        :return: None
        """
        self._voltage = float(val)

    @property
    def n_bays(self) -> int:
        """
        Get ``n_bays``.

        :return: int
        """
        return self._n_bays

    @n_bays.setter
    def n_bays(self, val: int) -> None:
        """
        Set ``n_bays``.

        :param val: Value to assign.
        :return: None
        """
        self._n_bays = int(val)

    @property
    def add_disconnectors(self) -> bool:
        """
        Get ``add_disconnectors``.

        :return: bool
        """
        return self._add_disconnectors

    @add_disconnectors.setter
    def add_disconnectors(self, val: bool) -> None:
        """
        Set ``add_disconnectors``.

        :param val: Value to assign.
        :return: None
        """
        self._add_disconnectors = bool(val)




