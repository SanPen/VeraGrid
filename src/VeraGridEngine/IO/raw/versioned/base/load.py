# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


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

        self._I: int = 0
        self._ID: str = '1'
        self._STATUS: int = 1
        self._AREA: int = 0
        self._ZONE: int = 0
        self._PL: float = 0.0
        self._QL: float = 0.0
        self._IP: float = 0.0
        self._IQ: float = 0.0
        self._YP: float = 0.0
        self._YQ: float = 0.0
        self._OWNER: int = 0
        self._SCALE: float = 0.0
        self._INTRPT: float = 0.0
        self._DGENP: float = 0.0
        self._DGENQ: float = 0.0
        self._DGENM: int = 0
        self._LOADTYPE: str = ''

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

    @property
    def I(self) -> int:
        return self._I

    @I.setter
    def I(self, value: int | str | None) -> None:
        self._I = coerce_psse_int(value=value, current_value=self._I)

    @property
    def ID(self) -> str:
        return self._ID

    @ID.setter
    def ID(self, value: str | int | float | None) -> None:
        self._ID = coerce_psse_str(value=value, current_value=self._ID)

    @property
    def STATUS(self) -> int:
        return self._STATUS

    @STATUS.setter
    def STATUS(self, value: int | str | None) -> None:
        self._STATUS = coerce_psse_int(value=value, current_value=self._STATUS)

    @property
    def AREA(self) -> int:
        return self._AREA

    @AREA.setter
    def AREA(self, value: int | str | None) -> None:
        self._AREA = coerce_psse_int(value=value, current_value=self._AREA)

    @property
    def ZONE(self) -> int:
        return self._ZONE

    @ZONE.setter
    def ZONE(self, value: int | str | None) -> None:
        self._ZONE = coerce_psse_int(value=value, current_value=self._ZONE)

    @property
    def PL(self) -> float:
        return self._PL

    @PL.setter
    def PL(self, value: float | int | str | None) -> None:
        self._PL = coerce_psse_float(value=value, current_value=self._PL)

    @property
    def QL(self) -> float:
        return self._QL

    @QL.setter
    def QL(self, value: float | int | str | None) -> None:
        self._QL = coerce_psse_float(value=value, current_value=self._QL)

    @property
    def IP(self) -> float:
        return self._IP

    @IP.setter
    def IP(self, value: float | int | str | None) -> None:
        self._IP = coerce_psse_float(value=value, current_value=self._IP)

    @property
    def IQ(self) -> float:
        return self._IQ

    @IQ.setter
    def IQ(self, value: float | int | str | None) -> None:
        self._IQ = coerce_psse_float(value=value, current_value=self._IQ)

    @property
    def YP(self) -> float:
        return self._YP

    @YP.setter
    def YP(self, value: float | int | str | None) -> None:
        self._YP = coerce_psse_float(value=value, current_value=self._YP)

    @property
    def YQ(self) -> float:
        return self._YQ

    @YQ.setter
    def YQ(self, value: float | int | str | None) -> None:
        self._YQ = coerce_psse_float(value=value, current_value=self._YQ)

    @property
    def OWNER(self) -> int:
        return self._OWNER

    @OWNER.setter
    def OWNER(self, value: int | str | None) -> None:
        self._OWNER = coerce_psse_int(value=value, current_value=self._OWNER)

    @property
    def SCALE(self) -> float:
        return self._SCALE

    @SCALE.setter
    def SCALE(self, value: float | int | str | None) -> None:
        self._SCALE = coerce_psse_float(value=value, current_value=self._SCALE)

    @property
    def INTRPT(self) -> float:
        return self._INTRPT

    @INTRPT.setter
    def INTRPT(self, value: float | int | str | None) -> None:
        self._INTRPT = coerce_psse_float(value=value, current_value=self._INTRPT)

    @property
    def DGENP(self) -> float:
        return self._DGENP

    @DGENP.setter
    def DGENP(self, value: float | int | str | None) -> None:
        self._DGENP = coerce_psse_float(value=value, current_value=self._DGENP)

    @property
    def DGENQ(self) -> float:
        return self._DGENQ

    @DGENQ.setter
    def DGENQ(self, value: float | int | str | None) -> None:
        self._DGENQ = coerce_psse_float(value=value, current_value=self._DGENQ)

    @property
    def DGENM(self) -> int:
        return self._DGENM

    @DGENM.setter
    def DGENM(self, value: int | str | None) -> None:
        self._DGENM = coerce_psse_int(value=value, current_value=self._DGENM)

    @property
    def LOADTYPE(self) -> str:
        return self._LOADTYPE

    @LOADTYPE.setter
    def LOADTYPE(self, value: str | int | float | None) -> None:
        self._LOADTYPE = coerce_psse_str(value=value, current_value=self._LOADTYPE)
