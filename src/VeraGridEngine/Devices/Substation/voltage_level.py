# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Tuple
from VeraGridEngine.enumerations import DeviceType, BuildStatus
from VeraGridEngine.Devices.Parents.physical_device import PhysicalDevice
from VeraGridEngine.Devices.Substation.substation import Substation
from VeraGridEngine.Devices.Parents.editable_device import GCProp


class VoltageLevel(PhysicalDevice):
    __slots__ = (
        '_Vnom',
        'substation',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key='Vnom', units='kV', tpe=float, definition='Nominal voltage'),
        GCProp(key="substation", tpe=DeviceType.SubstationDevice,
               definition="Substation of this Voltage level (optional)"),
    )

    def __init__(self, name='VoltageLevel',
                 idtag: Union[str, None] = None,
                 code: str = '',
                 Vnom: float = 1.0,
                 substation: Union[None, Substation] = None,
                 build_status: BuildStatus = BuildStatus.Commissioned):
        """
        Constructor
        :param name: Name
        :param idtag: UUID
        :param code: secondary ID
        :param Vnom: Nominal voltage in kV
        :param substation: Substation object (optional)
        """
        PhysicalDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=DeviceType.VoltageLevelDevice,
                                build_status=build_status)

        self.Vnom = float(Vnom)

        self.substation: Union[None, Substation] = substation

    @property
    def Vnom(self) -> float:
        """
        Get ``Vnom``.

        :return: float
        """
        return self._Vnom

    @Vnom.setter
    def Vnom(self, val: float) -> None:
        """
        Set ``Vnom``.

        :param val: Value to assign.
        :return: None
        """
        self._Vnom = float(val)
