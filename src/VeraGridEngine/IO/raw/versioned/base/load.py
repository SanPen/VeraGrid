# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty


class RawLoad(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus number', min_value=1,
                     max_value=999997, max_chars=6),
        PsseProperty(property_name='ID', rawx_key='loadid', class_type=str, description='Load 2-character ID',
                     max_chars=2),
        PsseProperty(property_name='STATUS', rawx_key='stat', class_type=int, description='Status', min_value=0,
                     max_value=1),
        PsseProperty(property_name='AREA', rawx_key='area', class_type=int, description='Area number', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='ZONE', rawx_key='zone', class_type=int, description='Zone number', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='PL', rawx_key='pl', class_type=float, unit=Unit.get_mw(),
                     description='Active power load'),
        PsseProperty(property_name='QL', rawx_key='ql', class_type=float, unit=Unit.get_mvar(),
                     description='Reactive power load'),
        PsseProperty(property_name='IP', rawx_key='ip', class_type=float, unit=Unit.get_mw(),
                     description='Active current load @v=1 p.u.'),
        PsseProperty(property_name='IQ', rawx_key='iq', class_type=float, unit=Unit.get_mvar(),
                     description='Reactive current load @v=1 p.u.'),
        PsseProperty(property_name='YP', rawx_key='yp', class_type=float, unit=Unit.get_mw(),
                     description='Active admittance power load @v=1 p.u.'),
        PsseProperty(property_name='YQ', rawx_key='yq', class_type=float, unit=Unit.get_mvar(),
                     description='Reactive admittance power load @v=1 p.u.'),
        PsseProperty(property_name='OWNER', rawx_key='owner', class_type=int, description='Owner number', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='SCALE', rawx_key='scale', class_type=float, unit=Unit.get_pu(),
                     description='Load scaling flag of one for a scalable load and zero for a fixed load'),
        PsseProperty(property_name='INTRPT', rawx_key='intrpt', class_type=float,
                     description='Interruptible load flag.', min_value=0, max_value=1),
        PsseProperty(property_name='DGENP', rawx_key='dgenp', class_type=float, unit=Unit.get_mw(),
                     description='Distributed Generation active power component'),
        PsseProperty(property_name='DGENQ', rawx_key='dgenq', class_type=float, unit=Unit.get_mvar(),
                     description='Distributed Generation reactive power component'),
        PsseProperty(property_name='DGENM', rawx_key='dgenm', class_type=int,
                     description='Distributed generation mode 0:off, 1: on.', min_value=0, max_value=1),
        PsseProperty(property_name='LOADTYPE', rawx_key='loadtype', class_type=str, description='Load type',
                     max_chars=12),
    )

    def __init__(self):
        RawObject.__init__(self, "load")

        self.I = 0
        self.ID = '1'
        self.STATUS = 1
        self.AREA = 0
        self.ZONE = 0
        self.PL = 0
        self.QL = 0
        self.IP = 0
        self.IQ = 0
        self.YP = 0
        self.YQ = 0
        self.OWNER = 0
        self.SCALE = 0.0
        self.INTRPT = 0

        self.DGENP = 0
        self.DGENQ = 0
        self.DGENM = 0
        self.LOADTYPE = ''

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

    def get_seed(self):
        """
        Get the element PSSE Seed
        :return:
        """
        return "{0}_{1}".format(self.I, self.ID)

