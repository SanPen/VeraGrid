# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol, Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.Devices as dev
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


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

        self._IS: int = 0
        self._NAME: str = ""
        self._LATI: float = 0.0
        self._LONG: float = 0.0
        self._SGR: float = 0.0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return str(self.IS)

    @property
    def IS(self) -> int:
        return self._IS

    @IS.setter
    def IS(self, value: int | str | None) -> None:
        self._IS = coerce_psse_int(value=value, current_value=self._IS)

    @property
    def NAME(self) -> str:
        return self._NAME

    @NAME.setter
    def NAME(self, value: str | int | float | None) -> None:
        self._NAME = coerce_psse_str(value=value, current_value=self._NAME)

    @property
    def LATI(self) -> float:
        return self._LATI

    @LATI.setter
    def LATI(self, value: float | int | str | None) -> None:
        self._LATI = coerce_psse_float(value=value, current_value=self._LATI)

    @property
    def LONG(self) -> float:
        return self._LONG

    @LONG.setter
    def LONG(self, value: float | int | str | None) -> None:
        self._LONG = coerce_psse_float(value=value, current_value=self._LONG)

    @property
    def SGR(self) -> float:
        return self._SGR

    @SGR.setter
    def SGR(self, value: float | int | str | None) -> None:
        self._SGR = coerce_psse_float(value=value, current_value=self._SGR)
