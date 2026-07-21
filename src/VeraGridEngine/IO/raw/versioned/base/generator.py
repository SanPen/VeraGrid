# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawGenerator(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus number', min_value=1,
                     max_value=999997, max_chars=6),
        PsseProperty(property_name='ID', rawx_key='machid', class_type=str, description='2-character ID', max_chars=2),
        PsseProperty(property_name='PG', rawx_key='pg', class_type=float, description='Active power output',
                     unit=Unit.get_mw()),
        PsseProperty(property_name='QG', rawx_key='qg', class_type=float, description='Reactive power output',
                     unit=Unit.get_mvar()),
        PsseProperty(property_name='QT', rawx_key='qt', class_type=float,
                     description='Maximum generator reactive power output;', unit=Unit.get_mvar()),
        PsseProperty(property_name='QB', rawx_key='qb', class_type=float,
                     description='Minimum generator reactive power output', unit=Unit.get_mvar()),
        PsseProperty(property_name='VS', rawx_key='vs', class_type=float, description='Regulated voltage set point',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='IREG', rawx_key='ireg', class_type=int,
                     description='Regulation bus, zero to regulate its own bus', min_value=0, max_value=999997),
        PsseProperty(property_name='NREG', rawx_key='nreg', class_type=int,
                     description="Node number of bus IREG when IREG's bus is a substation", min_value=0,
                     max_value=999997),
        PsseProperty(property_name='MBASE', rawx_key='mbase', class_type=float, description='Nominal power',
                     unit=Unit.get_mva()),
        PsseProperty(property_name='ZR', rawx_key='zr', class_type=float,
                     description='Machine resistance in p.u. of MBASE', unit=Unit.get_pu()),
        PsseProperty(property_name='ZX', rawx_key='zx', class_type=float,
                     description='Machine reactance in p.u. of MBASE', unit=Unit.get_pu()),
        PsseProperty(property_name='RT', rawx_key='rt', class_type=float,
                     description='Step-up transformer resistance in p.u. of MBASE', unit=Unit.get_pu()),
        PsseProperty(property_name='XT', rawx_key='xt', class_type=float,
                     description='Step-up transformer reactance in p.u. of MBASE', unit=Unit.get_pu()),
        PsseProperty(property_name='GTAP', rawx_key='gtap', class_type=float,
                     description='Step-up transformer off-nominal turns ratio; entered in pu on a system base.',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='STAT', rawx_key='stat', class_type=int, description='Status', min_value=0,
                     max_value=1),
        PsseProperty(property_name='RMPCT', rawx_key='rmpct', class_type=float,
                     description='Percent of the total Mvar required to hold the voltage at the control bus',
                     min_value=0, max_value=100.0, unit=Unit.get_percent()),
        PsseProperty(property_name='PT', rawx_key='pt', class_type=float,
                     description='Maximum generator active power output;', unit=Unit.get_mw()),
        PsseProperty(property_name='PB', rawx_key='pb', class_type=float,
                     description='Minimum generator active power output', unit=Unit.get_mw()),
        PsseProperty(property_name='BASLOD', rawx_key='baslod', class_type=int, description='Base load flag',
                     min_value=0, max_value=2),
        PsseProperty(property_name='O{}'.format(0 + 1), rawx_key='o{}'.format(0 + 1), class_type=int,
                     description='Owner number', min_value=1, max_value=9999),
        PsseProperty(property_name='F{}'.format(0 + 1), rawx_key='f{}'.format(0 + 1), class_type=float,
                     description='Ownership fraction', min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(1 + 1), rawx_key='o{}'.format(1 + 1), class_type=int,
                     description='Owner number', min_value=1, max_value=9999),
        PsseProperty(property_name='F{}'.format(1 + 1), rawx_key='f{}'.format(1 + 1), class_type=float,
                     description='Ownership fraction', min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(2 + 1), rawx_key='o{}'.format(2 + 1), class_type=int,
                     description='Owner number', min_value=1, max_value=9999),
        PsseProperty(property_name='F{}'.format(2 + 1), rawx_key='f{}'.format(2 + 1), class_type=float,
                     description='Ownership fraction', min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(3 + 1), rawx_key='o{}'.format(3 + 1), class_type=int,
                     description='Owner number', min_value=1, max_value=9999),
        PsseProperty(property_name='F{}'.format(3 + 1), rawx_key='f{}'.format(3 + 1), class_type=float,
                     description='Ownership fraction', min_value=0.0, max_value=1.0),
        PsseProperty(property_name='WMOD', rawx_key='wmod', class_type=int, description='Machine control mode;',
                     min_value=0, max_value=4),
        PsseProperty(property_name='WPF', rawx_key='wpf', class_type=float, description='Power factor',
                     unit=Unit.get_pu()),
    )

    def __init__(self) -> None:
        RawObject.__init__(self, "Generator")

        self._I: int = 0
        self._ID: str = "0"
        self._PG: float = 0.0
        self._QG: float = 0.0
        self._QT: float = 9999.0
        self._QB: float = -9999.0
        self._VS: float = 1.0
        self._IREG: int = 0
        self._NREG: int = 0
        self._MBASE: float = 0.0
        self._ZR: float = 0.0
        self._ZX: float = 0.0
        self._RT: float = 0.0
        self._XT: float = 0.0
        self._GTAP: float = 0.0
        self._STAT: int = 0
        self._RMPCT: float = 100.0
        self._PT: float = 0.0
        self._PB: float = 0.0
        self._BASLOD: int = 0
        self._O1: int = 1
        self._F1: float = 1.0
        self._O2: int = 0
        self._F2: float = 1.0
        self._O3: int = 0
        self._F3: float = 1.0
        self._O4: int = 0
        self._F4: float = 1.0
        self._WMOD: int = 0
        self._WPF: float = 0.0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
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
    def PG(self) -> float:
        return self._PG

    @PG.setter
    def PG(self, value: float | int | str | None) -> None:
        self._PG = coerce_psse_float(value=value, current_value=self._PG)

    @property
    def QG(self) -> float:
        return self._QG

    @QG.setter
    def QG(self, value: float | int | str | None) -> None:
        self._QG = coerce_psse_float(value=value, current_value=self._QG)

    @property
    def QT(self) -> float:
        return self._QT

    @QT.setter
    def QT(self, value: float | int | str | None) -> None:
        self._QT = coerce_psse_float(value=value, current_value=self._QT)

    @property
    def QB(self) -> float:
        return self._QB

    @QB.setter
    def QB(self, value: float | int | str | None) -> None:
        self._QB = coerce_psse_float(value=value, current_value=self._QB)

    @property
    def VS(self) -> float:
        return self._VS

    @VS.setter
    def VS(self, value: float | int | str | None) -> None:
        self._VS = coerce_psse_float(value=value, current_value=self._VS)

    @property
    def IREG(self) -> int:
        return self._IREG

    @IREG.setter
    def IREG(self, value: int | str | None) -> None:
        self._IREG = coerce_psse_int(value=value, current_value=self._IREG)

    @property
    def NREG(self) -> int:
        return self._NREG

    @NREG.setter
    def NREG(self, value: int | str | None) -> None:
        self._NREG = coerce_psse_int(value=value, current_value=self._NREG)

    @property
    def MBASE(self) -> float:
        return self._MBASE

    @MBASE.setter
    def MBASE(self, value: float | int | str | None) -> None:
        self._MBASE = coerce_psse_float(value=value, current_value=self._MBASE)

    @property
    def ZR(self) -> float:
        return self._ZR

    @ZR.setter
    def ZR(self, value: float | int | str | None) -> None:
        self._ZR = coerce_psse_float(value=value, current_value=self._ZR)

    @property
    def ZX(self) -> float:
        return self._ZX

    @ZX.setter
    def ZX(self, value: float | int | str | None) -> None:
        self._ZX = coerce_psse_float(value=value, current_value=self._ZX)

    @property
    def RT(self) -> float:
        return self._RT

    @RT.setter
    def RT(self, value: float | int | str | None) -> None:
        self._RT = coerce_psse_float(value=value, current_value=self._RT)

    @property
    def XT(self) -> float:
        return self._XT

    @XT.setter
    def XT(self, value: float | int | str | None) -> None:
        self._XT = coerce_psse_float(value=value, current_value=self._XT)

    @property
    def GTAP(self) -> float:
        return self._GTAP

    @GTAP.setter
    def GTAP(self, value: float | int | str | None) -> None:
        self._GTAP = coerce_psse_float(value=value, current_value=self._GTAP)

    @property
    def STAT(self) -> int:
        return self._STAT

    @STAT.setter
    def STAT(self, value: int | str | None) -> None:
        self._STAT = coerce_psse_int(value=value, current_value=self._STAT)

    @property
    def RMPCT(self) -> float:
        return self._RMPCT

    @RMPCT.setter
    def RMPCT(self, value: float | int | str | None) -> None:
        self._RMPCT = coerce_psse_float(value=value, current_value=self._RMPCT)

    @property
    def PT(self) -> float:
        return self._PT

    @PT.setter
    def PT(self, value: float | int | str | None) -> None:
        self._PT = coerce_psse_float(value=value, current_value=self._PT)

    @property
    def PB(self) -> float:
        return self._PB

    @PB.setter
    def PB(self, value: float | int | str | None) -> None:
        self._PB = coerce_psse_float(value=value, current_value=self._PB)

    @property
    def BASLOD(self) -> int:
        return self._BASLOD

    @BASLOD.setter
    def BASLOD(self, value: int | str | None) -> None:
        self._BASLOD = coerce_psse_int(value=value, current_value=self._BASLOD)

    @property
    def O1(self) -> int:
        return self._O1

    @O1.setter
    def O1(self, value: int | str | None) -> None:
        self._O1 = coerce_psse_int(value=value, current_value=self._O1)

    @property
    def F1(self) -> float:
        return self._F1

    @F1.setter
    def F1(self, value: float | int | str | None) -> None:
        self._F1 = coerce_psse_float(value=value, current_value=self._F1)

    @property
    def O2(self) -> int:
        return self._O2

    @O2.setter
    def O2(self, value: int | str | None) -> None:
        self._O2 = coerce_psse_int(value=value, current_value=self._O2)

    @property
    def F2(self) -> float:
        return self._F2

    @F2.setter
    def F2(self, value: float | int | str | None) -> None:
        self._F2 = coerce_psse_float(value=value, current_value=self._F2)

    @property
    def O3(self) -> int:
        return self._O3

    @O3.setter
    def O3(self, value: int | str | None) -> None:
        self._O3 = coerce_psse_int(value=value, current_value=self._O3)

    @property
    def F3(self) -> float:
        return self._F3

    @F3.setter
    def F3(self, value: float | int | str | None) -> None:
        self._F3 = coerce_psse_float(value=value, current_value=self._F3)

    @property
    def O4(self) -> int:
        return self._O4

    @O4.setter
    def O4(self, value: int | str | None) -> None:
        self._O4 = coerce_psse_int(value=value, current_value=self._O4)

    @property
    def F4(self) -> float:
        return self._F4

    @F4.setter
    def F4(self, value: float | int | str | None) -> None:
        self._F4 = coerce_psse_float(value=value, current_value=self._F4)

    @property
    def WMOD(self) -> int:
        return self._WMOD

    @WMOD.setter
    def WMOD(self, value: int | str | None) -> None:
        self._WMOD = coerce_psse_int(value=value, current_value=self._WMOD)

    @property
    def WPF(self) -> float:
        return self._WPF

    @WPF.setter
    def WPF(self, value: float | int | str | None) -> None:
        self._WPF = coerce_psse_float(value=value, current_value=self._WPF)
