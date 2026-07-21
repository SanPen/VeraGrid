# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


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

        self._I: int = -1
        self._ARNAME: str = ''
        self._ISW: int = 0
        self._PDES: float = 0.0
        self._PTOL: float = 0.0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return str(self.I)

    @property
    def I(self) -> int:
        return self._I

    @I.setter
    def I(self, value: int | str | None) -> None:
        self._I = coerce_psse_int(value=value, current_value=self._I)

    @property
    def ARNAME(self) -> str:
        return self._ARNAME

    @ARNAME.setter
    def ARNAME(self, value: str | int | float | None) -> None:
        self._ARNAME = coerce_psse_str(value=value, current_value=self._ARNAME)

    @property
    def ISW(self) -> int:
        return self._ISW

    @ISW.setter
    def ISW(self, value: int | str | None) -> None:
        self._ISW = coerce_psse_int(value=value, current_value=self._ISW)

    @property
    def PDES(self) -> float:
        return self._PDES

    @PDES.setter
    def PDES(self, value: float | int | str | None) -> None:
        self._PDES = coerce_psse_float(value=value, current_value=self._PDES)

    @property
    def PTOL(self) -> float:
        return self._PTOL

    @PTOL.setter
    def PTOL(self, value: float | int | str | None) -> None:
        self._PTOL = coerce_psse_float(value=value, current_value=self._PTOL)
