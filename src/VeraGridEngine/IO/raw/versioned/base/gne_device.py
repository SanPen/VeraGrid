# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawGneDevice(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='GNE device name', max_chars=12),
        PsseProperty(property_name='MODEL', rawx_key='model', class_type=str, description='BOSL model name', max_chars=12),
        PsseProperty(property_name='NTERM', rawx_key='nterm', class_type=int, description='Number of terminal buses'),
        PsseProperty(property_name='BUS1', rawx_key='bus1', class_type=int, description='First terminal bus'),
        PsseProperty(property_name='BUS2', rawx_key='bus2', class_type=int, description='Second terminal bus'),
        PsseProperty(property_name='NREAL', rawx_key='nreal', class_type=int, description='Number of floating-point inputs'),
        PsseProperty(property_name='NINTG', rawx_key='nintg', class_type=int, description='Number of integer inputs'),
        PsseProperty(property_name='NCHAR', rawx_key='nchar', class_type=int, description='Number of character inputs'),
        PsseProperty(property_name='STATUS', rawx_key='stat', class_type=int, description='Device status'),
        PsseProperty(property_name='OWNER', rawx_key='owner', class_type=int, description='Owner number'),
        PsseProperty(property_name='NMETR', rawx_key='nmetr', class_type=int, description='Non-metered end code'),
        PsseProperty(property_name='NMET', rawx_key='nmet', class_type=int, description='Non-metered end code'),
        *(PsseProperty(property_name=f'REAL{i}', rawx_key=f'real{i}', class_type=float,
                       description=f'Real input {i}') for i in range(1, 11)),
        *(PsseProperty(property_name=f'INTG{i}', rawx_key=f'intg{i}', class_type=int,
                       description=f'Integer input {i}') for i in range(1, 11)),
        *(PsseProperty(property_name=f'CHAR{i}', rawx_key=f'char{i}', class_type=str,
                       description=f'Character input {i}', max_chars=2) for i in range(1, 11)),
    )

    def __init__(self):
        RawObject.__init__(self, "GNE")

        self._NAME: str = ""
        self._MODEL: str = ""
        self._NTERM: int = 1
        self._BUS1: int = 0
        self._BUS2: int = 0
        self._NREAL: int = 0
        self._NINTG: int = 0
        self._NCHAR: int = 0
        self._STATUS: int = 1
        self._OWNER: int = 0
        self._NMETR: int = 0
        self._NMET: int = 0

        self._REAL1: float = 0.0
        self._REAL2: float = 0.0
        self._REAL3: float = 0.0
        self._REAL4: float = 0.0
        self._REAL5: float = 0.0
        self._REAL6: float = 0.0
        self._REAL7: float = 0.0
        self._REAL8: float = 0.0
        self._REAL9: float = 0.0
        self._REAL10: float = 0.0

        self._INTG1: int = 0
        self._INTG2: int = 0
        self._INTG3: int = 0
        self._INTG4: int = 0
        self._INTG5: int = 0
        self._INTG6: int = 0
        self._INTG7: int = 0
        self._INTG8: int = 0
        self._INTG9: int = 0
        self._INTG10: int = 0

        self._CHAR1: str = ''
        self._CHAR2: str = ''
        self._CHAR3: str = ''
        self._CHAR4: str = ''
        self._CHAR5: str = ''
        self._CHAR6: str = ''
        self._CHAR7: str = ''
        self._CHAR8: str = ''
        self._CHAR9: str = ''
        self._CHAR10: str = ''

    def set_real_value(self, index: int, value: float) -> None:
        if index == 1:
            self.REAL1 = value
        elif index == 2:
            self.REAL2 = value
        elif index == 3:
            self.REAL3 = value
        elif index == 4:
            self.REAL4 = value
        elif index == 5:
            self.REAL5 = value
        elif index == 6:
            self.REAL6 = value
        elif index == 7:
            self.REAL7 = value
        elif index == 8:
            self.REAL8 = value
        elif index == 9:
            self.REAL9 = value
        else:
            self.REAL10 = value

    def set_intg_value(self, index: int, value: int) -> None:
        if index == 1:
            self.INTG1 = value
        elif index == 2:
            self.INTG2 = value
        elif index == 3:
            self.INTG3 = value
        elif index == 4:
            self.INTG4 = value
        elif index == 5:
            self.INTG5 = value
        elif index == 6:
            self.INTG6 = value
        elif index == 7:
            self.INTG7 = value
        elif index == 8:
            self.INTG8 = value
        elif index == 9:
            self.INTG9 = value
        else:
            self.INTG10 = value

    def set_char_value(self, index: int, value: str) -> None:
        if index == 1:
            self.CHAR1 = value
        elif index == 2:
            self.CHAR2 = value
        elif index == 3:
            self.CHAR3 = value
        elif index == 4:
            self.CHAR4 = value
        elif index == 5:
            self.CHAR5 = value
        elif index == 6:
            self.CHAR6 = value
        elif index == 7:
            self.CHAR7 = value
        elif index == 8:
            self.CHAR8 = value
        elif index == 9:
            self.CHAR9 = value
        else:
            self.CHAR10 = value

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return self.NAME

    @property
    def NAME(self) -> str:
        return self._NAME

    @NAME.setter
    def NAME(self, value: str | int | float | None) -> None:
        self._NAME = coerce_psse_str(value=value, current_value=self._NAME)

    @property
    def MODEL(self) -> str:
        return self._MODEL

    @MODEL.setter
    def MODEL(self, value: str | int | float | None) -> None:
        self._MODEL = coerce_psse_str(value=value, current_value=self._MODEL)

    @property
    def NTERM(self) -> int:
        return self._NTERM

    @NTERM.setter
    def NTERM(self, value: int | str | None) -> None:
        self._NTERM = coerce_psse_int(value=value, current_value=self._NTERM)

    @property
    def BUS1(self) -> int:
        return self._BUS1

    @BUS1.setter
    def BUS1(self, value: int | str | None) -> None:
        self._BUS1 = coerce_psse_int(value=value, current_value=self._BUS1)

    @property
    def BUS2(self) -> int:
        return self._BUS2

    @BUS2.setter
    def BUS2(self, value: int | str | None) -> None:
        self._BUS2 = coerce_psse_int(value=value, current_value=self._BUS2)

    @property
    def NREAL(self) -> int:
        return self._NREAL

    @NREAL.setter
    def NREAL(self, value: int | str | None) -> None:
        self._NREAL = coerce_psse_int(value=value, current_value=self._NREAL)

    @property
    def NINTG(self) -> int:
        return self._NINTG

    @NINTG.setter
    def NINTG(self, value: int | str | None) -> None:
        self._NINTG = coerce_psse_int(value=value, current_value=self._NINTG)

    @property
    def NCHAR(self) -> int:
        return self._NCHAR

    @NCHAR.setter
    def NCHAR(self, value: int | str | None) -> None:
        self._NCHAR = coerce_psse_int(value=value, current_value=self._NCHAR)

    @property
    def STATUS(self) -> int:
        return self._STATUS

    @STATUS.setter
    def STATUS(self, value: int | str | None) -> None:
        self._STATUS = coerce_psse_int(value=value, current_value=self._STATUS)

    @property
    def OWNER(self) -> int:
        return self._OWNER

    @OWNER.setter
    def OWNER(self, value: int | str | None) -> None:
        self._OWNER = coerce_psse_int(value=value, current_value=self._OWNER)

    @property
    def NMETR(self) -> int:
        return self._NMETR

    @NMETR.setter
    def NMETR(self, value: int | str | None) -> None:
        self._NMETR = coerce_psse_int(value=value, current_value=self._NMETR)

    @property
    def NMET(self) -> int:
        return self._NMET

    @NMET.setter
    def NMET(self, value: int | str | None) -> None:
        self._NMET = coerce_psse_int(value=value, current_value=self._NMET)

    @property
    def REAL1(self) -> float:
        return self._REAL1

    @REAL1.setter
    def REAL1(self, value: float | int | str | None) -> None:
        self._REAL1 = coerce_psse_float(value=value, current_value=self._REAL1)

    @property
    def REAL2(self) -> float:
        return self._REAL2

    @REAL2.setter
    def REAL2(self, value: float | int | str | None) -> None:
        self._REAL2 = coerce_psse_float(value=value, current_value=self._REAL2)

    @property
    def REAL3(self) -> float:
        return self._REAL3

    @REAL3.setter
    def REAL3(self, value: float | int | str | None) -> None:
        self._REAL3 = coerce_psse_float(value=value, current_value=self._REAL3)

    @property
    def REAL4(self) -> float:
        return self._REAL4

    @REAL4.setter
    def REAL4(self, value: float | int | str | None) -> None:
        self._REAL4 = coerce_psse_float(value=value, current_value=self._REAL4)

    @property
    def REAL5(self) -> float:
        return self._REAL5

    @REAL5.setter
    def REAL5(self, value: float | int | str | None) -> None:
        self._REAL5 = coerce_psse_float(value=value, current_value=self._REAL5)

    @property
    def REAL6(self) -> float:
        return self._REAL6

    @REAL6.setter
    def REAL6(self, value: float | int | str | None) -> None:
        self._REAL6 = coerce_psse_float(value=value, current_value=self._REAL6)

    @property
    def REAL7(self) -> float:
        return self._REAL7

    @REAL7.setter
    def REAL7(self, value: float | int | str | None) -> None:
        self._REAL7 = coerce_psse_float(value=value, current_value=self._REAL7)

    @property
    def REAL8(self) -> float:
        return self._REAL8

    @REAL8.setter
    def REAL8(self, value: float | int | str | None) -> None:
        self._REAL8 = coerce_psse_float(value=value, current_value=self._REAL8)

    @property
    def REAL9(self) -> float:
        return self._REAL9

    @REAL9.setter
    def REAL9(self, value: float | int | str | None) -> None:
        self._REAL9 = coerce_psse_float(value=value, current_value=self._REAL9)

    @property
    def REAL10(self) -> float:
        return self._REAL10

    @REAL10.setter
    def REAL10(self, value: float | int | str | None) -> None:
        self._REAL10 = coerce_psse_float(value=value, current_value=self._REAL10)

    @property
    def INTG1(self) -> int:
        return self._INTG1

    @INTG1.setter
    def INTG1(self, value: int | str | None) -> None:
        self._INTG1 = coerce_psse_int(value=value, current_value=self._INTG1)

    @property
    def INTG2(self) -> int:
        return self._INTG2

    @INTG2.setter
    def INTG2(self, value: int | str | None) -> None:
        self._INTG2 = coerce_psse_int(value=value, current_value=self._INTG2)

    @property
    def INTG3(self) -> int:
        return self._INTG3

    @INTG3.setter
    def INTG3(self, value: int | str | None) -> None:
        self._INTG3 = coerce_psse_int(value=value, current_value=self._INTG3)

    @property
    def INTG4(self) -> int:
        return self._INTG4

    @INTG4.setter
    def INTG4(self, value: int | str | None) -> None:
        self._INTG4 = coerce_psse_int(value=value, current_value=self._INTG4)

    @property
    def INTG5(self) -> int:
        return self._INTG5

    @INTG5.setter
    def INTG5(self, value: int | str | None) -> None:
        self._INTG5 = coerce_psse_int(value=value, current_value=self._INTG5)

    @property
    def INTG6(self) -> int:
        return self._INTG6

    @INTG6.setter
    def INTG6(self, value: int | str | None) -> None:
        self._INTG6 = coerce_psse_int(value=value, current_value=self._INTG6)

    @property
    def INTG7(self) -> int:
        return self._INTG7

    @INTG7.setter
    def INTG7(self, value: int | str | None) -> None:
        self._INTG7 = coerce_psse_int(value=value, current_value=self._INTG7)

    @property
    def INTG8(self) -> int:
        return self._INTG8

    @INTG8.setter
    def INTG8(self, value: int | str | None) -> None:
        self._INTG8 = coerce_psse_int(value=value, current_value=self._INTG8)

    @property
    def INTG9(self) -> int:
        return self._INTG9

    @INTG9.setter
    def INTG9(self, value: int | str | None) -> None:
        self._INTG9 = coerce_psse_int(value=value, current_value=self._INTG9)

    @property
    def INTG10(self) -> int:
        return self._INTG10

    @INTG10.setter
    def INTG10(self, value: int | str | None) -> None:
        self._INTG10 = coerce_psse_int(value=value, current_value=self._INTG10)

    @property
    def CHAR1(self) -> str:
        return self._CHAR1

    @CHAR1.setter
    def CHAR1(self, value: str | int | float | None) -> None:
        self._CHAR1 = coerce_psse_str(value=value, current_value=self._CHAR1)

    @property
    def CHAR2(self) -> str:
        return self._CHAR2

    @CHAR2.setter
    def CHAR2(self, value: str | int | float | None) -> None:
        self._CHAR2 = coerce_psse_str(value=value, current_value=self._CHAR2)

    @property
    def CHAR3(self) -> str:
        return self._CHAR3

    @CHAR3.setter
    def CHAR3(self, value: str | int | float | None) -> None:
        self._CHAR3 = coerce_psse_str(value=value, current_value=self._CHAR3)

    @property
    def CHAR4(self) -> str:
        return self._CHAR4

    @CHAR4.setter
    def CHAR4(self, value: str | int | float | None) -> None:
        self._CHAR4 = coerce_psse_str(value=value, current_value=self._CHAR4)

    @property
    def CHAR5(self) -> str:
        return self._CHAR5

    @CHAR5.setter
    def CHAR5(self, value: str | int | float | None) -> None:
        self._CHAR5 = coerce_psse_str(value=value, current_value=self._CHAR5)

    @property
    def CHAR6(self) -> str:
        return self._CHAR6

    @CHAR6.setter
    def CHAR6(self, value: str | int | float | None) -> None:
        self._CHAR6 = coerce_psse_str(value=value, current_value=self._CHAR6)

    @property
    def CHAR7(self) -> str:
        return self._CHAR7

    @CHAR7.setter
    def CHAR7(self, value: str | int | float | None) -> None:
        self._CHAR7 = coerce_psse_str(value=value, current_value=self._CHAR7)

    @property
    def CHAR8(self) -> str:
        return self._CHAR8

    @CHAR8.setter
    def CHAR8(self, value: str | int | float | None) -> None:
        self._CHAR8 = coerce_psse_str(value=value, current_value=self._CHAR8)

    @property
    def CHAR9(self) -> str:
        return self._CHAR9

    @CHAR9.setter
    def CHAR9(self, value: str | int | float | None) -> None:
        self._CHAR9 = coerce_psse_str(value=value, current_value=self._CHAR9)

    @property
    def CHAR10(self) -> str:
        return self._CHAR10

    @CHAR10.setter
    def CHAR10(self, value: str | int | float | None) -> None:
        self._CHAR10 = coerce_psse_str(value=value, current_value=self._CHAR10)
