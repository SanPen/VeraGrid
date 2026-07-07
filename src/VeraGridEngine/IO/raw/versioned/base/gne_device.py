# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty


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

        self.NAME = ""
        self.MODEL = ""
        self.NTERM = 1
        self.BUS1 = 0
        self.BUS2 = 0
        self.NREAL = 0
        self.NINTG = 0
        self.NCHAR = 0
        self.STATUS = 1
        self.OWNER = 0
        self.NMETR = 0
        self.NMET = 0

        self.REAL1 = 0.0
        self.REAL2 = 0.0
        self.REAL3 = 0.0
        self.REAL4 = 0.0
        self.REAL5 = 0.0
        self.REAL6 = 0.0
        self.REAL7 = 0.0
        self.REAL8 = 0.0
        self.REAL9 = 0.0
        self.REAL10 = 0.0

        self.INTG1 = 0
        self.INTG2 = 0
        self.INTG3 = 0
        self.INTG4 = 0
        self.INTG5 = 0
        self.INTG6 = 0
        self.INTG7 = 0
        self.INTG8 = 0
        self.INTG9 = 0
        self.INTG10 = 0

        self.CHAR1 = ''
        self.CHAR2 = ''
        self.CHAR3 = ''
        self.CHAR4 = ''
        self.CHAR5 = ''
        self.CHAR6 = ''
        self.CHAR7 = ''
        self.CHAR8 = ''
        self.CHAR9 = ''
        self.CHAR10 = ''

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
