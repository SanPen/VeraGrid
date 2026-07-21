# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawSwitchedShunt(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus number', min_value=1,
                     max_value=999997, max_chars=6),
        PsseProperty(property_name='ID', rawx_key='shntid', class_type=str, description='Load 2-character ID',
                     max_chars=2),
        PsseProperty(property_name='MODSW', rawx_key='modsw', class_type=int, description='Control mode', min_value=0,
                     max_value=6),
        PsseProperty(property_name='ADJM', rawx_key='adjm', class_type=int, description='Adjustment method',
                     min_value=0, max_value=1),
        PsseProperty(property_name='STAT', rawx_key='stat', class_type=int, description='Status', min_value=0,
                     max_value=1),
        PsseProperty(property_name='VSWHI', rawx_key='vswhi', class_type=float,
                     description='Controlled voltage upper limit', unit=Unit.get_pu()),
        PsseProperty(property_name='VSWLO', rawx_key='vswlo', class_type=float,
                     description='Controlled voltage upper limit', unit=Unit.get_pu()),
        PsseProperty(property_name='SWREG', rawx_key='swreg', class_type=int, description='Controlled voltage bus',
                     min_value=0, max_value=999997),
        PsseProperty(property_name='SWREM', rawx_key='swrem', class_type=int,
                     description='Controlled bus or plant bus for pre-35 switched shunt formats',
                     min_value=0, max_value=999997),
        PsseProperty(property_name='NREG', rawx_key='nreg', class_type=int,
                     description="Node number of bus IREG when IREG's bus is a substation", min_value=0,
                     max_value=999997),
        PsseProperty(property_name='RMPCT', rawx_key='rmpct', class_type=float,
                     description='Percent of the total Mvar required to hold the voltage at the control bus',
                     min_value=0, max_value=100.0, unit=Unit.get_percent()),
        PsseProperty(property_name='RMIDNT', rawx_key='rmidnt', class_type=str,
                     description='Controlled branch for VSC like operation'),
        PsseProperty(property_name='BINIT', rawx_key='binit', class_type=float,
                     description='Initial switched shunt admittance', unit=Unit.get_pu()),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str,
                     description='Switched shunt name', max_chars=12),
        PsseProperty(property_name='S{}'.format(0 + 1), rawx_key='s{}'.format(0 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(1 + 1), rawx_key='s{}'.format(1 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(2 + 1), rawx_key='s{}'.format(2 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(3 + 1), rawx_key='s{}'.format(3 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(4 + 1), rawx_key='s{}'.format(4 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(5 + 1), rawx_key='s{}'.format(5 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(6 + 1), rawx_key='s{}'.format(6 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(7 + 1), rawx_key='s{}'.format(7 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='N{}'.format(0 + 1), rawx_key='n{}'.format(0 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(1 + 1), rawx_key='n{}'.format(1 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(2 + 1), rawx_key='n{}'.format(2 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(3 + 1), rawx_key='n{}'.format(3 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(4 + 1), rawx_key='n{}'.format(4 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(5 + 1), rawx_key='n{}'.format(5 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(6 + 1), rawx_key='n{}'.format(6 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(7 + 1), rawx_key='n{}'.format(7 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='B{}'.format(0 + 1), rawx_key='b{}'.format(0 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(1 + 1), rawx_key='b{}'.format(1 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(2 + 1), rawx_key='b{}'.format(2 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(3 + 1), rawx_key='b{}'.format(3 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(4 + 1), rawx_key='b{}'.format(4 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(5 + 1), rawx_key='b{}'.format(5 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(6 + 1), rawx_key='b{}'.format(6 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(7 + 1), rawx_key='b{}'.format(7 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
    )

    def __init__(self):
        RawObject.__init__(self, "Switched shunt")

        self._I: int = 0
        self._ID: str = ''
        '''
        MODSW:
        0 - locked
        1 - discrete adjustment, local voltage control
        2 - continuous adjustment, local voltage control
        3 - discrete adjustment, local generator reactive power control (WTF?)
        4 - discrete adjustment, branch voltage control (see RMIDNT)
        5 - discrete adjustment, local admittance control (WTF?)
        6 - discrete adjustment, reactive power control for FACTS (see RMIDNT)
        '''
        self._MODSW: int = 0
        self._ADJM: int = 0
        self._STAT: int = 0
        self._VSWHI: float = 1.0
        self._VSWLO: float = 1.0
        self._SWREM: int = 0
        self._SWREG: int = 0
        self._NREG: int = 0
        self._RMPCT: float = 1.0
        self._RMIDNT: str = ''
        self._BINIT: float = 0.0
        self._NAME: str = ''

        self._S1: int = 0
        self._S2: int = 0
        self._S3: int = 0
        self._S4: int = 0
        self._S5: int = 0
        self._S6: int = 0
        self._S7: int = 0
        self._S8: int = 0

        self._N1: int = 0
        self._N2: int = 0
        self._N3: int = 0
        self._N4: int = 0
        self._N5: int = 0
        self._N6: int = 0
        self._N7: int = 0
        self._N8: int = 0

        self._B1: float = 0.0
        self._B2: float = 0.0
        self._B3: float = 0.0
        self._B4: float = 0.0
        self._B5: float = 0.0
        self._B6: float = 0.0
        self._B7: float = 0.0
        self._B8: float = 0.0

    def set_block_status(self, index: int, value: int) -> None:
        if index == 1:
            self.S1 = value
        elif index == 2:
            self.S2 = value
        elif index == 3:
            self.S3 = value
        elif index == 4:
            self.S4 = value
        elif index == 5:
            self.S5 = value
        elif index == 6:
            self.S6 = value
        elif index == 7:
            self.S7 = value
        else:
            self.S8 = value

    def get_block_status(self, index: int) -> int:
        if index == 1:
            return self.S1
        elif index == 2:
            return self.S2
        elif index == 3:
            return self.S3
        elif index == 4:
            return self.S4
        elif index == 5:
            return self.S5
        elif index == 6:
            return self.S6
        elif index == 7:
            return self.S7
        return self.S8

    def set_block_steps(self, index: int, value: int) -> None:
        if index == 1:
            self.N1 = value
        elif index == 2:
            self.N2 = value
        elif index == 3:
            self.N3 = value
        elif index == 4:
            self.N4 = value
        elif index == 5:
            self.N5 = value
        elif index == 6:
            self.N6 = value
        elif index == 7:
            self.N7 = value
        else:
            self.N8 = value

    def get_block_steps(self, index: int) -> int:
        if index == 1:
            return self.N1
        elif index == 2:
            return self.N2
        elif index == 3:
            return self.N3
        elif index == 4:
            return self.N4
        elif index == 5:
            return self.N5
        elif index == 6:
            return self.N6
        elif index == 7:
            return self.N7
        return self.N8

    def set_block_admittance(self, index: int, value: float) -> None:
        if index == 1:
            self.B1 = value
        elif index == 2:
            self.B2 = value
        elif index == 3:
            self.B3 = value
        elif index == 4:
            self.B4 = value
        elif index == 5:
            self.B5 = value
        elif index == 6:
            self.B6 = value
        elif index == 7:
            self.B7 = value
        else:
            self.B8 = value

    def get_block_admittance(self, index: int) -> float:
        if index == 1:
            return self.B1
        elif index == 2:
            return self.B2
        elif index == 3:
            return self.B3
        elif index == 4:
            return self.B4
        elif index == 5:
            return self.B5
        elif index == 6:
            return self.B6
        elif index == 7:
            return self.B7
        return self.B8

    def set_block(self, index: int, status: int, steps: int, admittance: float) -> None:
        self.set_block_status(index, status)
        self.set_block_steps(index, steps)
        self.set_block_admittance(index, admittance)

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
    def MODSW(self) -> int:
        return self._MODSW

    @MODSW.setter
    def MODSW(self, value: int | str | None) -> None:
        self._MODSW = coerce_psse_int(value=value, current_value=self._MODSW)

    @property
    def ADJM(self) -> int:
        return self._ADJM

    @ADJM.setter
    def ADJM(self, value: int | str | None) -> None:
        self._ADJM = coerce_psse_int(value=value, current_value=self._ADJM)

    @property
    def STAT(self) -> int:
        return self._STAT

    @STAT.setter
    def STAT(self, value: int | str | None) -> None:
        self._STAT = coerce_psse_int(value=value, current_value=self._STAT)

    @property
    def VSWHI(self) -> float:
        return self._VSWHI

    @VSWHI.setter
    def VSWHI(self, value: float | int | str | None) -> None:
        self._VSWHI = coerce_psse_float(value=value, current_value=self._VSWHI)

    @property
    def VSWLO(self) -> float:
        return self._VSWLO

    @VSWLO.setter
    def VSWLO(self, value: float | int | str | None) -> None:
        self._VSWLO = coerce_psse_float(value=value, current_value=self._VSWLO)

    @property
    def SWREG(self) -> int:
        return self._SWREG

    @SWREG.setter
    def SWREG(self, value: int | str | None) -> None:
        self._SWREG = coerce_psse_int(value=value, current_value=self._SWREG)

    @property
    def SWREM(self) -> int:
        return self._SWREM

    @SWREM.setter
    def SWREM(self, value: int | str | None) -> None:
        self._SWREM = coerce_psse_int(value=value, current_value=self._SWREM)

    @property
    def NREG(self) -> int:
        return self._NREG

    @NREG.setter
    def NREG(self, value: int | str | None) -> None:
        self._NREG = coerce_psse_int(value=value, current_value=self._NREG)

    @property
    def RMPCT(self) -> float:
        return self._RMPCT

    @RMPCT.setter
    def RMPCT(self, value: float | int | str | None) -> None:
        self._RMPCT = coerce_psse_float(value=value, current_value=self._RMPCT)

    @property
    def RMIDNT(self) -> str:
        return self._RMIDNT

    @RMIDNT.setter
    def RMIDNT(self, value: str | int | float | None) -> None:
        self._RMIDNT = coerce_psse_str(value=value, current_value=self._RMIDNT)

    @property
    def BINIT(self) -> float:
        return self._BINIT

    @BINIT.setter
    def BINIT(self, value: float | int | str | None) -> None:
        self._BINIT = coerce_psse_float(value=value, current_value=self._BINIT)

    @property
    def NAME(self) -> str:
        return self._NAME

    @NAME.setter
    def NAME(self, value: str | int | float | None) -> None:
        self._NAME = coerce_psse_str(value=value, current_value=self._NAME)

    @property
    def S1(self) -> int:
        return self._S1

    @S1.setter
    def S1(self, value: int | str | None) -> None:
        self._S1 = coerce_psse_int(value=value, current_value=self._S1)

    @property
    def S2(self) -> int:
        return self._S2

    @S2.setter
    def S2(self, value: int | str | None) -> None:
        self._S2 = coerce_psse_int(value=value, current_value=self._S2)

    @property
    def S3(self) -> int:
        return self._S3

    @S3.setter
    def S3(self, value: int | str | None) -> None:
        self._S3 = coerce_psse_int(value=value, current_value=self._S3)

    @property
    def S4(self) -> int:
        return self._S4

    @S4.setter
    def S4(self, value: int | str | None) -> None:
        self._S4 = coerce_psse_int(value=value, current_value=self._S4)

    @property
    def S5(self) -> int:
        return self._S5

    @S5.setter
    def S5(self, value: int | str | None) -> None:
        self._S5 = coerce_psse_int(value=value, current_value=self._S5)

    @property
    def S6(self) -> int:
        return self._S6

    @S6.setter
    def S6(self, value: int | str | None) -> None:
        self._S6 = coerce_psse_int(value=value, current_value=self._S6)

    @property
    def S7(self) -> int:
        return self._S7

    @S7.setter
    def S7(self, value: int | str | None) -> None:
        self._S7 = coerce_psse_int(value=value, current_value=self._S7)

    @property
    def S8(self) -> int:
        return self._S8

    @S8.setter
    def S8(self, value: int | str | None) -> None:
        self._S8 = coerce_psse_int(value=value, current_value=self._S8)

    @property
    def N1(self) -> int:
        return self._N1

    @N1.setter
    def N1(self, value: int | str | None) -> None:
        self._N1 = coerce_psse_int(value=value, current_value=self._N1)

    @property
    def N2(self) -> int:
        return self._N2

    @N2.setter
    def N2(self, value: int | str | None) -> None:
        self._N2 = coerce_psse_int(value=value, current_value=self._N2)

    @property
    def N3(self) -> int:
        return self._N3

    @N3.setter
    def N3(self, value: int | str | None) -> None:
        self._N3 = coerce_psse_int(value=value, current_value=self._N3)

    @property
    def N4(self) -> int:
        return self._N4

    @N4.setter
    def N4(self, value: int | str | None) -> None:
        self._N4 = coerce_psse_int(value=value, current_value=self._N4)

    @property
    def N5(self) -> int:
        return self._N5

    @N5.setter
    def N5(self, value: int | str | None) -> None:
        self._N5 = coerce_psse_int(value=value, current_value=self._N5)

    @property
    def N6(self) -> int:
        return self._N6

    @N6.setter
    def N6(self, value: int | str | None) -> None:
        self._N6 = coerce_psse_int(value=value, current_value=self._N6)

    @property
    def N7(self) -> int:
        return self._N7

    @N7.setter
    def N7(self, value: int | str | None) -> None:
        self._N7 = coerce_psse_int(value=value, current_value=self._N7)

    @property
    def N8(self) -> int:
        return self._N8

    @N8.setter
    def N8(self, value: int | str | None) -> None:
        self._N8 = coerce_psse_int(value=value, current_value=self._N8)

    @property
    def B1(self) -> float:
        return self._B1

    @B1.setter
    def B1(self, value: float | int | str | None) -> None:
        self._B1 = coerce_psse_float(value=value, current_value=self._B1)

    @property
    def B2(self) -> float:
        return self._B2

    @B2.setter
    def B2(self, value: float | int | str | None) -> None:
        self._B2 = coerce_psse_float(value=value, current_value=self._B2)

    @property
    def B3(self) -> float:
        return self._B3

    @B3.setter
    def B3(self, value: float | int | str | None) -> None:
        self._B3 = coerce_psse_float(value=value, current_value=self._B3)

    @property
    def B4(self) -> float:
        return self._B4

    @B4.setter
    def B4(self, value: float | int | str | None) -> None:
        self._B4 = coerce_psse_float(value=value, current_value=self._B4)

    @property
    def B5(self) -> float:
        return self._B5

    @B5.setter
    def B5(self, value: float | int | str | None) -> None:
        self._B5 = coerce_psse_float(value=value, current_value=self._B5)

    @property
    def B6(self) -> float:
        return self._B6

    @B6.setter
    def B6(self, value: float | int | str | None) -> None:
        self._B6 = coerce_psse_float(value=value, current_value=self._B6)

    @property
    def B7(self) -> float:
        return self._B7

    @B7.setter
    def B7(self, value: float | int | str | None) -> None:
        self._B7 = coerce_psse_float(value=value, current_value=self._B7)

    @property
    def B8(self) -> float:
        return self._B8

    @B8.setter
    def B8(self, value: float | int | str | None) -> None:
        self._B8 = coerce_psse_float(value=value, current_value=self._B8)
