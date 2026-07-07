# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty


class RawInterArea(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='iarea', class_type=int, description='Area number', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='ISW', rawx_key='isw', class_type=int, description='Area slack bus number.'),
        PsseProperty(property_name='PDES', rawx_key='pdes', class_type=float,
                     description='Desired net interchange leaving the area.', unit=Unit.get_mw()),
        PsseProperty(property_name='PTOL', rawx_key='ptol', class_type=float,
                     description='Interchange tolerance bandwidth.', unit=Unit.get_mw()),
        PsseProperty(property_name='ARNAME', rawx_key='arname', class_type=str, description='Name.', max_chars=12),
    )

    def __init__(self):
        RawObject.__init__(self, "Inter area")

        self.I = -1
        self.ARNAME = ''
        self.ISW = 0
        self.PDES = 0
        self.PTOL = 0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return str(self.I)

