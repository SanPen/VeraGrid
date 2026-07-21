# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List, Any, Tuple
from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawBus(RawObject):

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus number', min_value=1, max_value=999997, max_chars=6),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Bus name', max_chars=12),
        PsseProperty(property_name='BASKV', rawx_key='baskv', class_type=float, description='Bus base voltage', unit=Unit.get_kv(), min_value=0.0, format_rule='.4f'),
        PsseProperty(property_name='IDE', rawx_key='ide', class_type=int, description='Bus type (0:Disconnected, 1:PQ, 2:PV, 3:Slack)', min_value=1, max_value=4, max_chars=1),
        PsseProperty(property_name='AREA', rawx_key='area', class_type=int, description='Area number', min_value=1, max_value=9999),
        PsseProperty(property_name='ZONE', rawx_key='zone', class_type=int, description='Zone number', min_value=1, max_value=9999),
        PsseProperty(property_name='OWNER', rawx_key='owner', class_type=int, description='Owner number', min_value=1, max_value=9999),
        PsseProperty(property_name='VM', rawx_key='vm', class_type=float, description='Bus voltage magnitude', unit=Unit.get_pu(), min_value=0.0, max_value=2.0, format_rule='.5f'),
        PsseProperty(property_name='VA', rawx_key='va', class_type=float, description='Bus voltage angle', unit=Unit.get_deg(), min_value=0.0, max_value=360.0, format_rule='.4f'),
        PsseProperty(property_name='NVHI', rawx_key='nvhi', class_type=float, description='Normal voltage magnitude high limit', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='NVLO', rawx_key='nvlo', class_type=float, description='Normal voltage magnitude low limit', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='EVHI', rawx_key='evhi', class_type=float, description='Emergency voltage magnitude high limit', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='EVLO', rawx_key='evlo', class_type=float, description='Emergency voltage magnitude low limit', unit=Unit.get_pu(), format_rule='.5f'),
    )

    def __init__(self):
        RawObject.__init__(self, "Bus")

        self._I: int = 1
        self._NAME: str = ""
        self._BASKV: float = 0.0
        self._IDE: int = 1
        self._AREA: int = 0
        self._ZONE: int = 0
        self._OWNER: int = 1
        self._VM: float = 1.0
        self._VA: float = 0.0
        self._NVHI: float = 1.05
        self._NVLO: float = 0.95
        self._EVHI: float = 1.1
        self._EVLO: float = 0.9
        self.GL = 0.0
        self.BL = 0.0


    def parse(self, data: List[List[Any]], version: int, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version: int):
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
    def NAME(self) -> str:
        return self._NAME

    @NAME.setter
    def NAME(self, value: str | int | float | None) -> None:
        self._NAME = coerce_psse_str(value=value, current_value=self._NAME)

    @property
    def BASKV(self) -> float:
        return self._BASKV

    @BASKV.setter
    def BASKV(self, value: float | int | str | None) -> None:
        self._BASKV = coerce_psse_float(value=value, current_value=self._BASKV)

    @property
    def IDE(self) -> int:
        return self._IDE

    @IDE.setter
    def IDE(self, value: int | str | None) -> None:
        self._IDE = coerce_psse_int(value=value, current_value=self._IDE)

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
    def OWNER(self) -> int:
        return self._OWNER

    @OWNER.setter
    def OWNER(self, value: int | str | None) -> None:
        self._OWNER = coerce_psse_int(value=value, current_value=self._OWNER)

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

    @property
    def NVHI(self) -> float:
        return self._NVHI

    @NVHI.setter
    def NVHI(self, value: float | int | str | None) -> None:
        self._NVHI = coerce_psse_float(value=value, current_value=self._NVHI)

    @property
    def NVLO(self) -> float:
        return self._NVLO

    @NVLO.setter
    def NVLO(self, value: float | int | str | None) -> None:
        self._NVLO = coerce_psse_float(value=value, current_value=self._NVLO)

    @property
    def EVHI(self) -> float:
        return self._EVHI

    @EVHI.setter
    def EVHI(self, value: float | int | str | None) -> None:
        self._EVHI = coerce_psse_float(value=value, current_value=self._EVHI)

    @property
    def EVLO(self) -> float:
        return self._EVLO

    @EVLO.setter
    def EVLO(self, value: float | int | str | None) -> None:
        self._EVLO = coerce_psse_float(value=value, current_value=self._EVLO)
