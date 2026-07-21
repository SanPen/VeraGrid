# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawNode(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='ISUB', rawx_key='isub', class_type=int, description='Substation number',
                     min_value=1, max_value=99999),
        PsseProperty(property_name='NI', rawx_key='inode', class_type=int, description='Node number', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Node name.', max_chars=40),
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus number', min_value=1,
                     max_value=999997),
        PsseProperty(property_name='STATUS', rawx_key='stat', class_type=int,
                     description='Switch status, 1: closed, 0: open'),
        PsseProperty(property_name='VM', rawx_key='vm', class_type=float, description='Bus voltage magnitude',
                     unit=Unit.get_pu(), min_value=0.0, max_value=2.0),
        PsseProperty(property_name='VA', rawx_key='va', class_type=float, description='Bus voltage angle',
                     unit=Unit.get_deg(), min_value=0.0, max_value=360.0),
    )

    def __init__(self):
        RawObject.__init__(self, "node")

        self._ISUB: int = 0
        self._NI: int = 0
        self._NAME: str = ''
        self._I: int = 0
        self._STATUS: int = 0
        self._VM: float = 0.0
        self._VA: float = 0.0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return "{0}_{1}".format(self.ISUB, self.NI)

    @property
    def ISUB(self) -> int:
        return self._ISUB

    @ISUB.setter
    def ISUB(self, value: int | str | None) -> None:
        self._ISUB = coerce_psse_int(value=value, current_value=self._ISUB)

    @property
    def NI(self) -> int:
        return self._NI

    @NI.setter
    def NI(self, value: int | str | None) -> None:
        self._NI = coerce_psse_int(value=value, current_value=self._NI)

    @property
    def NAME(self) -> str:
        return self._NAME

    @NAME.setter
    def NAME(self, value: str | int | float | None) -> None:
        self._NAME = coerce_psse_str(value=value, current_value=self._NAME)

    @property
    def I(self) -> int:
        return self._I

    @I.setter
    def I(self, value: int | str | None) -> None:
        self._I = coerce_psse_int(value=value, current_value=self._I)

    @property
    def STATUS(self) -> int:
        return self._STATUS

    @STATUS.setter
    def STATUS(self, value: int | str | None) -> None:
        self._STATUS = coerce_psse_int(value=value, current_value=self._STATUS)

    @property
    def VM(self) -> float:
        return self._VM

    @VM.setter
    def VM(self, value: float | int | str | None) -> None:
        self._VM = coerce_psse_float(value=value, current_value=self._VM)

    @property
    def VA(self) -> float:
        return self._VA

    @VA.setter
    def VA(self, value: float | int | str | None) -> None:
        self._VA = coerce_psse_float(value=value, current_value=self._VA)
