# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawMultiLineSection(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='From bus', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='J', rawx_key='jbus', class_type=int, description='Bus to'),
        PsseProperty(property_name='ID', rawx_key='mslid', class_type=float, description='Multi section ID'),
        PsseProperty(property_name='MET', rawx_key='met', class_type=int, description='Metered flag'),
        PsseProperty(property_name=f'DUM{1}', rawx_key=f'dum{1}', class_type=int, description=f'Dummy bus {1}'),
        PsseProperty(property_name=f'DUM{2}', rawx_key=f'dum{2}', class_type=int, description=f'Dummy bus {2}'),
        PsseProperty(property_name=f'DUM{3}', rawx_key=f'dum{3}', class_type=int, description=f'Dummy bus {3}'),
        PsseProperty(property_name=f'DUM{4}', rawx_key=f'dum{4}', class_type=int, description=f'Dummy bus {4}'),
        PsseProperty(property_name=f'DUM{5}', rawx_key=f'dum{5}', class_type=int, description=f'Dummy bus {5}'),
        PsseProperty(property_name=f'DUM{6}', rawx_key=f'dum{6}', class_type=int, description=f'Dummy bus {6}'),
        PsseProperty(property_name=f'DUM{7}', rawx_key=f'dum{7}', class_type=int, description=f'Dummy bus {7}'),
        PsseProperty(property_name=f'DUM{8}', rawx_key=f'dum{8}', class_type=int, description=f'Dummy bus {8}'),
        PsseProperty(property_name=f'DUM{9}', rawx_key=f'dum{9}', class_type=int, description=f'Dummy bus {9}'),
    )

    def __init__(self):
        RawObject.__init__(self, "MultiLineSection")

        self._I: int = 0
        self._J: int = 0
        self._ID: float = 0.0
        self._MET: int = 1
        self._DUM1: int = 0
        self._DUM2: int = 0
        self._DUM3: int = 0
        self._DUM4: int = 0
        self._DUM5: int = 0
        self._DUM6: int = 0
        self._DUM7: int = 0
        self._DUM8: int = 0
        self._DUM9: int = 0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return str(self.I)

    def get_seed(self) -> str:
        return "_CA_{}".format(self.I)

    @property
    def I(self) -> int:
        return self._I

    @I.setter
    def I(self, value: int | str | None) -> None:
        self._I = coerce_psse_int(value=value, current_value=self._I)

    @property
    def J(self) -> int:
        return self._J

    @J.setter
    def J(self, value: int | str | None) -> None:
        self._J = coerce_psse_int(value=value, current_value=self._J)

    @property
    def ID(self) -> float:
        return self._ID

    @ID.setter
    def ID(self, value: float | int | str | None) -> None:
        self._ID = coerce_psse_float(value=value, current_value=self._ID)

    @property
    def MET(self) -> int:
        return self._MET

    @MET.setter
    def MET(self, value: int | str | None) -> None:
        self._MET = coerce_psse_int(value=value, current_value=self._MET)

    @property
    def DUM1(self) -> int:
        return self._DUM1

    @DUM1.setter
    def DUM1(self, value: int | str | None) -> None:
        self._DUM1 = coerce_psse_int(value=value, current_value=self._DUM1)

    @property
    def DUM2(self) -> int:
        return self._DUM2

    @DUM2.setter
    def DUM2(self, value: int | str | None) -> None:
        self._DUM2 = coerce_psse_int(value=value, current_value=self._DUM2)

    @property
    def DUM3(self) -> int:
        return self._DUM3

    @DUM3.setter
    def DUM3(self, value: int | str | None) -> None:
        self._DUM3 = coerce_psse_int(value=value, current_value=self._DUM3)

    @property
    def DUM4(self) -> int:
        return self._DUM4

    @DUM4.setter
    def DUM4(self, value: int | str | None) -> None:
        self._DUM4 = coerce_psse_int(value=value, current_value=self._DUM4)

    @property
    def DUM5(self) -> int:
        return self._DUM5

    @DUM5.setter
    def DUM5(self, value: int | str | None) -> None:
        self._DUM5 = coerce_psse_int(value=value, current_value=self._DUM5)

    @property
    def DUM6(self) -> int:
        return self._DUM6

    @DUM6.setter
    def DUM6(self, value: int | str | None) -> None:
        self._DUM6 = coerce_psse_int(value=value, current_value=self._DUM6)

    @property
    def DUM7(self) -> int:
        return self._DUM7

    @DUM7.setter
    def DUM7(self, value: int | str | None) -> None:
        self._DUM7 = coerce_psse_int(value=value, current_value=self._DUM7)

    @property
    def DUM8(self) -> int:
        return self._DUM8

    @DUM8.setter
    def DUM8(self, value: int | str | None) -> None:
        self._DUM8 = coerce_psse_int(value=value, current_value=self._DUM8)

    @property
    def DUM9(self) -> int:
        return self._DUM9

    @DUM9.setter
    def DUM9(self, value: int | str | None) -> None:
        self._DUM9 = coerce_psse_int(value=value, current_value=self._DUM9)
