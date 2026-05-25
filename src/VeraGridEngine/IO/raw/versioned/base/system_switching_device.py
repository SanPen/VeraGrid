# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty


class RawSystemSwitchingDevice(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='From bus number.', min_value=1,
                     max_value=999997),
        PsseProperty(property_name='J', rawx_key='jbus', class_type=int, description='From bus number.', min_value=1,
                     max_value=999997),
        PsseProperty(property_name='CKT', rawx_key='ckt', class_type=str, description='Owner number', max_chars=2),
        PsseProperty(property_name='CKTID', rawx_key='ckt', class_type=str,
                     description='Switching device identifier', max_chars=2),
        PsseProperty(property_name='X', rawx_key='xpu', class_type=float, description='Branch reactance'),
        PsseProperty(property_name='STATUS', rawx_key='stat', class_type=int,
                     description='Switch status, 1: closed, 0: open'),
        PsseProperty(property_name='NSTATUS', rawx_key='nstat', class_type=int,
                     description='Normal service status, 1 for normally open and 0 for normally close'),
        PsseProperty(property_name='METERED', rawx_key='met', class_type=int, description='Metered end'),
        PsseProperty(property_name='STYPE', rawx_key='stype', class_type=int,
                     description='Switching device type:\n1 - Generic connector\n2 - Circuit breaker\n3 - Disconnect switch'),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Device name', max_chars=12),
        *(PsseProperty(property_name='RATE{}'.format(i),
                       rawx_key='rate{}'.format(i),
                       class_type=float,
                       description='Rating power',
                       unit=Unit.get_mva()) for i in range(1, 13)),
    )

    def __init__(self):
        RawObject.__init__(self, "System switching device")

        self.I = 0
        self.J = 0
        self.CKT = ""
        self.X = 0.0
        self.RATE1 = 0.0
        self.RATE2 = 0.0
        self.RATE3 = 0.0
        self.RATE4 = 0.0
        self.RATE5 = 0.0
        self.RATE6 = 0.0
        self.RATE7 = 0.0
        self.RATE8 = 0.0
        self.RATE9 = 0.0
        self.RATE10 = 0.0
        self.RATE11 = 0.0
        self.RATE12 = 0.0
        self.STATUS = 1
        self.NSTATUS = 1
        self.METERED = 0
        self.STYPE = 1
        self.NAME = ""

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        """
        Get the element PSSE ID
        :return: 
        """
        return "{0}_{1}_{2}".format(self.I, self.J, self.CKT)

    @property
    def CKTID(self):
        return self.CKT

    @CKTID.setter
    def CKTID(self, value):
        self.CKT = value
