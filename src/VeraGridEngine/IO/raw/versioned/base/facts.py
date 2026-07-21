# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawFACTS(RawObject):

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Device name', max_chars=12),
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus from number', min_value=1, max_value=999997),
        PsseProperty(property_name='J', rawx_key='jbus', class_type=int, description='Bus to number', min_value=0, max_value=999997),
        PsseProperty(property_name='MODE', rawx_key='mode', class_type=int, description='Control mode', min_value=0, max_value=8),
        PsseProperty(property_name='PDES', rawx_key='pdes', class_type=float, description='Desired active power flow arriving at the "to" bus;', unit=Unit.get_mw()),
        PsseProperty(property_name='QDES', rawx_key='qdes', class_type=float, description='Desired reactive power flow arriving at the "to" bus', unit=Unit.get_mvar()),
        PsseProperty(property_name='VSET', rawx_key='vset', class_type=float, description='Voltage set point at the "from" bus', unit=Unit.get_pu()),
        PsseProperty(property_name='SHMX', rawx_key='shmx', class_type=float, description='Maximum shunt current at the "from" bus', unit=Unit.get_mva()),
        PsseProperty(property_name='TRMX', rawx_key='trmx', class_type=float, description='Maximum bridge active power transfer', unit=Unit.get_mw()),
        PsseProperty(property_name='VTMN', rawx_key='vtmn', class_type=float, description='Minimum voltage at the "to" bus', unit=Unit.get_pu()),
        PsseProperty(property_name='VTMX', rawx_key='vtmx', class_type=float, description='Maximum voltage at the "to" bus', unit=Unit.get_pu()),
        PsseProperty(property_name='VSMX', rawx_key='vsmx', class_type=float, description='Maximum series voltage', unit=Unit.get_pu()),
        PsseProperty(property_name='IMX', rawx_key='imx', class_type=int, description='Maximum series current. Zero for no series current limit', unit=Unit.get_mva()),
        PsseProperty(property_name='LINX', rawx_key='linx', class_type=float, description='Reactance of the series element used during power flow solutions', unit=Unit.get_pu()),
        PsseProperty(property_name='RMPCT', rawx_key='rmpct', class_type=float, description='Percentage of the total Mvar required to hold the voltage at the bus controlled by the shunt element', min_value=0.0, max_value=100.0, unit=Unit.get_percent()),
        PsseProperty(property_name='OWNER', rawx_key='owner', class_type=int, description='Owner number', min_value=0, max_value=999999),
        PsseProperty(property_name='SET1', rawx_key='set1', class_type=float, description='Set value 1 (see manual)'),
        PsseProperty(property_name='SET2', rawx_key='set2', class_type=float, description='Set value  (see manual)'),
        PsseProperty(property_name='VSREF', rawx_key='vsref', class_type=int, description='Series voltage reference code', min_value=0, max_value=1),
        PsseProperty(property_name='FCREG', rawx_key='fcreg', class_type=int, description='Bus number, or extended bus name enclosed in single quotes', min_value=0, max_value=1),
        PsseProperty(property_name='NREG', rawx_key='nreg', class_type=int, description='A node number of bus FCREG', min_value=0, max_value=1),
        PsseProperty(property_name='REMOT', rawx_key='remot', class_type=int, description='Remote bus number', min_value=0, max_value=999999),
        PsseProperty(property_name='MNAME', rawx_key='mname', class_type=str, description='device name'),
    )

    def __init__(self):
        RawObject.__init__(self, "FACTS")

        self._NAME: str = ""
        self._I: int = 0
        self._J: int = 0
        self._MODE: int = 1
        self._PDES: float = 0.0
        self._QDES: float = 0.0
        self._VSET: float = 0.0
        self._SHMX: float = 9999.0
        self._TRMX: float = 0.0
        self._VTMN: float = 0.9
        self._VTMX: float = 1.1
        self._VSMX: float = 1.0
        self._IMX: int = 0
        self._LINX: float = 0.05
        self._RMPCT: float = 100.0
        self._OWNER: int = 0
        self._SET1: float = 0.0
        self._SET2: float = 0.0
        self._VSREF: int = 0
        self._FCREG: int = 0
        self._NREG: int = 0
        self._REMOT: int = 0
        self._MNAME: str = ""

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
        return "{0}_{1}_1".format(self.I, self.J)

    def is_connected(self):
        return self.I > 0 and self.J > 0

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
    def J(self) -> int:
        return self._J

    @J.setter
    def J(self, value: int | str | None) -> None:
        self._J = coerce_psse_int(value=value, current_value=self._J)

    @property
    def MODE(self) -> int:
        return self._MODE

    @MODE.setter
    def MODE(self, value: int | str | None) -> None:
        self._MODE = coerce_psse_int(value=value, current_value=self._MODE)

    @property
    def PDES(self) -> float:
        return self._PDES

    @PDES.setter
    def PDES(self, value: float | int | str | None) -> None:
        self._PDES = coerce_psse_float(value=value, current_value=self._PDES)

    @property
    def QDES(self) -> float:
        return self._QDES

    @QDES.setter
    def QDES(self, value: float | int | str | None) -> None:
        self._QDES = coerce_psse_float(value=value, current_value=self._QDES)

    @property
    def VSET(self) -> float:
        return self._VSET

    @VSET.setter
    def VSET(self, value: float | int | str | None) -> None:
        self._VSET = coerce_psse_float(value=value, current_value=self._VSET)

    @property
    def SHMX(self) -> float:
        return self._SHMX

    @SHMX.setter
    def SHMX(self, value: float | int | str | None) -> None:
        self._SHMX = coerce_psse_float(value=value, current_value=self._SHMX)

    @property
    def TRMX(self) -> float:
        return self._TRMX

    @TRMX.setter
    def TRMX(self, value: float | int | str | None) -> None:
        self._TRMX = coerce_psse_float(value=value, current_value=self._TRMX)

    @property
    def VTMN(self) -> float:
        return self._VTMN

    @VTMN.setter
    def VTMN(self, value: float | int | str | None) -> None:
        self._VTMN = coerce_psse_float(value=value, current_value=self._VTMN)

    @property
    def VTMX(self) -> float:
        return self._VTMX

    @VTMX.setter
    def VTMX(self, value: float | int | str | None) -> None:
        self._VTMX = coerce_psse_float(value=value, current_value=self._VTMX)

    @property
    def VSMX(self) -> float:
        return self._VSMX

    @VSMX.setter
    def VSMX(self, value: float | int | str | None) -> None:
        self._VSMX = coerce_psse_float(value=value, current_value=self._VSMX)

    @property
    def IMX(self) -> int:
        return self._IMX

    @IMX.setter
    def IMX(self, value: int | str | None) -> None:
        self._IMX = coerce_psse_int(value=value, current_value=self._IMX)

    @property
    def LINX(self) -> float:
        return self._LINX

    @LINX.setter
    def LINX(self, value: float | int | str | None) -> None:
        self._LINX = coerce_psse_float(value=value, current_value=self._LINX)

    @property
    def RMPCT(self) -> float:
        return self._RMPCT

    @RMPCT.setter
    def RMPCT(self, value: float | int | str | None) -> None:
        self._RMPCT = coerce_psse_float(value=value, current_value=self._RMPCT)

    @property
    def OWNER(self) -> int:
        return self._OWNER

    @OWNER.setter
    def OWNER(self, value: int | str | None) -> None:
        self._OWNER = coerce_psse_int(value=value, current_value=self._OWNER)

    @property
    def SET1(self) -> float:
        return self._SET1

    @SET1.setter
    def SET1(self, value: float | int | str | None) -> None:
        self._SET1 = coerce_psse_float(value=value, current_value=self._SET1)

    @property
    def SET2(self) -> float:
        return self._SET2

    @SET2.setter
    def SET2(self, value: float | int | str | None) -> None:
        self._SET2 = coerce_psse_float(value=value, current_value=self._SET2)

    @property
    def VSREF(self) -> int:
        return self._VSREF

    @VSREF.setter
    def VSREF(self, value: int | str | None) -> None:
        self._VSREF = coerce_psse_int(value=value, current_value=self._VSREF)

    @property
    def FCREG(self) -> int:
        return self._FCREG

    @FCREG.setter
    def FCREG(self, value: int | str | None) -> None:
        self._FCREG = coerce_psse_int(value=value, current_value=self._FCREG)

    @property
    def NREG(self) -> int:
        return self._NREG

    @NREG.setter
    def NREG(self, value: int | str | None) -> None:
        self._NREG = coerce_psse_int(value=value, current_value=self._NREG)

    @property
    def REMOT(self) -> int:
        return self._REMOT

    @REMOT.setter
    def REMOT(self, value: int | str | None) -> None:
        self._REMOT = coerce_psse_int(value=value, current_value=self._REMOT)

    @property
    def MNAME(self) -> str:
        return self._MNAME

    @MNAME.setter
    def MNAME(self, value: str | int | float | None) -> None:
        self._MNAME = coerce_psse_str(value=value, current_value=self._MNAME)
