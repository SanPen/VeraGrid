# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union, Tuple
import numpy as np
from VeraGridEngine.Devices.Profiles import ProfileFloat
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType, GCProp, get_at, PrpCat


class Technology(EditableDevice):
    __slots__ = ('name2', 'name3', 'name4', 'color', '_reference_cost', '_reference_cost_prof')

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='reference_cost',
            units='Currency/MWh',
            tpe=float,
            definition='Reference cost for the technology',
            profile_name="reference_cost_prof",
            cat=[PrpCat.OPF]
        ),
        GCProp(
            prop_name='name2',
            units='',
            tpe=str,
            definition='Name 2 of the technology',
        ),
        GCProp(
            prop_name='name3',
            units='',
            tpe=str,
            definition='Name 3 of the technology',
        ),
        GCProp(
            prop_name='name4',
            units='',
            tpe=str,
            definition='Name 4 of the technology',
        ),
        GCProp(
            prop_name='color',
            units='',
            tpe=str,
            definition='Color to paint',
            is_color=True,
        ),
    )

    def __init__(self, name: str = '',
                 code: str = '',
                 idtag: Union[str, None] = None,
                 color: Union[str, None] = None,
                 reference_cost: float = 0):
        """
        Technology
        :param name: name of the technology
        :param code: secondary id
        :param idtag: UUID code
        :param color: hexadecimal color string (i.e. #AA00FF)
        :param reference_cost: Reference cost for the technology (currency/MWh)
        """
        EditableDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=DeviceType.Technology)

        self.name2 = ""
        self.name3 = ""
        self.name4 = ""

        self.color = color if color is not None else self.rnd_color()

        self._reference_cost = float(reference_cost)
        self._reference_cost_prof = ProfileFloat(default_value=self._reference_cost)

    @property
    def reference_cost(self) -> float:
        """
        Reference cost
        :return: float
        """
        return self._reference_cost

    @reference_cost.setter
    def reference_cost(self, val: float):
        if isinstance(val, float):
            self._reference_cost = val
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a _reference_cost')

    @property
    def reference_cost_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._reference_cost_prof

    @reference_cost_prof.setter
    def reference_cost_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._reference_cost_prof = val
        elif isinstance(val, np.ndarray):
            self._reference_cost_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a reference_cost_prof')

    def get_reference_cost_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.reference_cost, self.reference_cost_prof, t)