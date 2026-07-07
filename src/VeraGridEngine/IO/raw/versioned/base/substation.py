# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol, Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.Devices as dev
from VeraGridEngine.IO.raw.psse_property import PsseProperty


class RawSubstation(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='IS', rawx_key='isub', class_type=int, description='Substation number ', min_value=1,
                     max_value=99999),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Substation name.',
                     max_chars=40),
        PsseProperty(property_name='LATI', rawx_key='lati', class_type=float, description='Substation latitude.',
                     min_value=-90, max_chars=90, unit=Unit.get_deg()),
        PsseProperty(property_name='LONG', rawx_key='long', class_type=float, description='Substation longitude.',
                     min_value=-180, max_chars=180, unit=Unit.get_deg()),
        PsseProperty(property_name='SGR', rawx_key='sgr', class_type=float,
                     description='Substation grounding DC resistance in ohms.', unit=Unit.get_ohm()),
    )

    def __init__(self):
        RawObject.__init__(self, "Substation")

        self.IS: int = 0
        self.NAME: str = ""
        self.LATI: float = 0.0
        self.LONG: float = 0.0
        self.SGR: float = 0.0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return str(self.IS)

