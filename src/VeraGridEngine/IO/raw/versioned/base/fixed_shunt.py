# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.Devices as dev
from VeraGridEngine.IO.raw.psse_property import PsseProperty


class RawFixedShunt(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus number', min_value=1,
                     max_value=999997, max_chars=6),
        PsseProperty(property_name='ID', rawx_key='shntid', class_type=str, description='2-character ID', max_chars=2),
        PsseProperty(property_name='STATUS', rawx_key='stat', class_type=int, description='Status', min_value=0,
                     max_value=1),
        PsseProperty(property_name='GL', rawx_key='gl', class_type=float, unit=Unit.get_mw(),
                     description='Active power load at v=1.0 p.u.'),
        PsseProperty(property_name='BL', rawx_key='bl', class_type=float, unit=Unit.get_mvar(),
                     description='Reactive power load at v=1.0 p.u.'),
    )

    def __init__(self):
        RawObject.__init__(self, "Fixed shunt")

        self.I = 0
        self.ID = ""
        self.STATUS = 1
        self.GL = 0.0
        self.BL = 0.0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self):
        """
        Get the element PSSE ID
        :return:
        """
        return "{0}_{1}".format(self.I, self.ID)

