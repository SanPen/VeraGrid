# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union
from VeraGridEngine.enumerations import DeviceType, BuildStatus
from VeraGridEngine.Devices.Parents.physical_device import PhysicalDevice
from VeraGridEngine.Devices.Substation.voltage_level import VoltageLevel


class BusBar(PhysicalDevice):
    __slots__ = (
        '_voltage_level',
    )

    def __init__(self,
                 name='BusBar',
                 idtag: Union[None, str] = None,
                 code: str = '',
                 voltage_level: VoltageLevel | None = None,
                 build_status: BuildStatus = BuildStatus.Commissioned) -> None:
        """
        Constructor
        :param name: Name of the bus bar
        :param idtag: unique identifier of the device
        :param code: secondary identifier
        :param voltage_level: VoltageLevel (optional)
        """
        PhysicalDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=DeviceType.BusBarDevice,
                                build_status=build_status)

        self._voltage_level: VoltageLevel | None = voltage_level
        self.register(key="voltage_level", tpe=DeviceType.BusDevice,
                      definition="Voltage level of this BusBar")

    @property
    def voltage_level(self) -> VoltageLevel | None:
        """
        Connectivity node getter
        :return: ConnectivityNode
        """
        return self._voltage_level

    @voltage_level.setter
    def voltage_level(self, val: VoltageLevel):
        """
        Connectivity node setter
        :param val: ConnectivityNode
        """
        if isinstance(val, VoltageLevel):
            self._voltage_level: VoltageLevel = val
        else:
            raise ValueError("Must be a VoltageLevel object")
