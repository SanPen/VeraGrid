# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Union, Tuple
import numpy as np
from VeraGridEngine.Devices.Profiles import ProfileFloat
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType, GCProp
from VeraGridEngine.enumerations import PrpCat


class Fuel(EditableDevice):
    __slots__ = (
        '_cost',
        '_cost_prof',
        'color',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='cost',
            units='e/t',
            tpe=float,
            definition='Cost of fuel (e / ton)',
            profile_name='cost_prof',
        ),
        GCProp(
            prop_name='color',
            units='',
            tpe=str,
            definition='Color to paint',
            is_color=True,
            cat=[PrpCat.OPF],
        ),
    )

    def __init__(self, name='',
                 code='',
                 idtag: Union[str, None] = None,
                 cost: float = 0.0,
                 color: Union[str, None] = None):
        """
        Fuel
        :param name: name of the generator fuel
        :param code: secondary id
        :param idtag: UUID code
        :param cost: cost of the fuel per ton (e/t)
        :param color: hexadecimal color string (i.e. #AA00FF)
        """
        EditableDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=DeviceType.FuelDevice)

        self.cost = cost

        self._cost_prof = ProfileFloat(default_value=cost)

        self.color = color if color is not None else self.rnd_color()


    @property
    def cost_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._cost_prof

    @cost_prof.setter
    def cost_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._cost_prof = val
        elif isinstance(val, np.ndarray):
            self._cost_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a cost_prof')

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def cost(self) -> float:
        """
        Get ``cost``.

        :return: float
        """
        return self._cost

    @cost.setter
    def cost(self, val: float) -> None:
        """
        Set ``cost``.

        :param val: Value to assign.
        :return: None
        """
        self._cost = float(val)
