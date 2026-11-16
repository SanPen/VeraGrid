# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


from typing import Union, Tuple
import numpy as np
from VeraGridEngine.Devices.Profiles import ProfileFloat
from VeraGridEngine.Devices.Parents.editable_device import get_at, GCProp, PrpCat
from VeraGridEngine.Devices.Aggregation.area import GenericAreaGroup, DeviceType
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType


class Facility(GenericAreaGroup):
    """
    This is an aggregation of Injection devices
    """

    __slots__ = (
        '_Vset',
        '_Vset_prof',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='Vset',
            units='p.u.',
            tpe=float,
            definition='Voltage setpoint for controlled generators; positive-sequence magnitude in three-phase power flow.',
            profile_name='Vset_prof',
            cat=[PrpCat.PF],
            dyn_ref=ParamPowerFlowReferenceType.generator_vset_pu,
        ),
    )

    def __init__(self, name='', code='', idtag: Union[str, None] = None,
                 latitude=0.0, longitude=0.0,
                 Vset: float = 1.0):
        """
        Constructor
        :param name: Name
        :param code: Secondary code
        :param idtag: IdTag
        :param latitude: latitude (deg)
        :param longitude: longitude (deg)
        """
        GenericAreaGroup.__init__(self,
                                  name=name,
                                  idtag=idtag,
                                  code=code,
                                  device_type=DeviceType.FacilityDevice,
                                  latitude=latitude,
                                  longitude=longitude)

        # Voltage module set point (p.u.)
        self._Vset = float(Vset)

        # voltage set profile for this load in p.u.
        self._Vset_prof = ProfileFloat(default_value=self._Vset)

    @property
    def Vset(self) -> float:
        """
        Get ``Vset``.

        :return: float
        """
        return self._Vset

    @Vset.setter
    def Vset(self, val: float) -> None:
        """
        Set ``Vset``.

        :param val: Value to assign.
        :return: None
        """
        self._Vset = float(val)

    @property
    def Vset_prof(self) -> ProfileFloat:
        """
        Vset profile
        :return: Profile
        """
        return self._Vset_prof

    @Vset_prof.setter
    def Vset_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Vset_prof = val
        elif isinstance(val, np.ndarray):
            self._Vset_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Vset_prof')

    def get_Vset_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Vset, self.Vset_prof, t)
