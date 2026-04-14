# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List, Dict
from VeraGridEngine.IO.iidm.devices.iidm_object import IidmObject
from VeraGridEngine.Devices.Substation.bus import Bus, Area


class IidmBus(IidmObject):
    def __init__(self, _id: str, area_number: int, status: str, nodes: List[int]):
        """

        :param _id:
        :param area_number:
        :param status:
        :param nodes:
        """
        super().__init__("Bus")
        self.id = _id
        self.area_number: int = area_number
        self.status: str = status
        self.nodes: List[int] = nodes

        self.register_property("id", str, description="Bus ID")
        self.register_property("area_number", str, description="Area number")
        self.register_property("status", str, description="Status")

    def to_veragrid(self, area_dict: Dict[int, Area]) -> Bus:
        """
        Convert
        """
        return Bus(
            name="",
            code=self.id,
            area=area_dict.get(self.area_number, None)
        )
