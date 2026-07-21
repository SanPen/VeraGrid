# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol, Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawBranch(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Branch from bus number',
                     min_value=1, max_value=999997, max_chars=6),
        PsseProperty(property_name='J', rawx_key='jbus', class_type=int, description='Branch to bus number',
                     min_value=1, max_value=999997, max_chars=6),
        PsseProperty(property_name='CKT', rawx_key='ckt', class_type=str, description='Owner number', max_chars=2),
        PsseProperty(property_name='R', rawx_key='rpu', class_type=float, description='Branch resistance',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='X', rawx_key='xpu', class_type=float, description='Branch reactance',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='B', rawx_key='bpu', class_type=float, description='Branch shunt susceptance',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Branch name', max_chars=40),
        PsseProperty(property_name='RATEA', rawx_key='ratea', class_type=float,
                     description='Branch rating set A', unit=Unit(UnitMultiplier.M, UnitSymbol.VA)),
        PsseProperty(property_name='RATEB', rawx_key='rateb', class_type=float,
                     description='Branch rating set B', unit=Unit(UnitMultiplier.M, UnitSymbol.VA)),
        PsseProperty(property_name='RATEC', rawx_key='ratec', class_type=float,
                     description='Branch rating set C', unit=Unit(UnitMultiplier.M, UnitSymbol.VA)),
        PsseProperty(property_name='GI', rawx_key='gi', class_type=float,
                     description='Branch shunt conductance at the from side', unit=Unit.get_pu()),
        PsseProperty(property_name='BI', rawx_key='bi', class_type=float,
                     description='Branch shunt susceptance at the from side', unit=Unit.get_pu()),
        PsseProperty(property_name='GJ', rawx_key='gj', class_type=float,
                     description='Branch shunt condictance at the to side', unit=Unit.get_pu()),
        PsseProperty(property_name='BJ', rawx_key='bj', class_type=float,
                     description='Branch shunt susceptance at the to side', unit=Unit.get_pu()),
        PsseProperty(property_name='ST', rawx_key='stat', class_type=int, description='Branch status', min_value=0,
                     max_value=1),
        PsseProperty(property_name='MET', rawx_key='met', class_type=int,
                     description='Metered end flag, <=1: Bus from, >=2: bus to', min_value=0, max_value=999),
        PsseProperty(property_name='LEN', rawx_key='len', class_type=float, description='Line length',
                     unit=Unit.get_km()),
        PsseProperty(property_name='O{}'.format(0 + 1), rawx_key='o{}'.format(0 + 1), class_type=int,
                     description='Owner number', min_value=1, max_value=9999, max_chars=4),
        PsseProperty(property_name='F{}'.format(0 + 1), rawx_key='f{}'.format(0 + 1), class_type=float,
                     description='Ownership fraction', min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(1 + 1), rawx_key='o{}'.format(1 + 1), class_type=int,
                     description='Owner number', min_value=1, max_value=9999, max_chars=4),
        PsseProperty(property_name='F{}'.format(1 + 1), rawx_key='f{}'.format(1 + 1), class_type=float,
                     description='Ownership fraction', min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(2 + 1), rawx_key='o{}'.format(2 + 1), class_type=int,
                     description='Owner number', min_value=1, max_value=9999, max_chars=4),
        PsseProperty(property_name='F{}'.format(2 + 1), rawx_key='f{}'.format(2 + 1), class_type=float,
                     description='Ownership fraction', min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(3 + 1), rawx_key='o{}'.format(3 + 1), class_type=int,
                     description='Owner number', min_value=1, max_value=9999, max_chars=4),
        PsseProperty(property_name='F{}'.format(3 + 1), rawx_key='f{}'.format(3 + 1), class_type=float,
                     description='Ownership fraction', min_value=0.0, max_value=1.0),
        *(PsseProperty(property_name='RATE{}'.format(i),
                       rawx_key='rate{}'.format(i),
                       class_type=float,
                       description='Branch rating power',
                       unit=Unit(UnitMultiplier.M, UnitSymbol.VA)) for i in range(1, 13)),
    )

    def __init__(self) -> None:
        RawObject.__init__(self, "Branch")

        self._I: int = 0
        self._J: int = 0
        self._CKT: str = '1'
        self._R: float = 0.0
        self._X: float = 0.0
        self._B: float = 0.0

        self._NAME: str = ''

        # rates for newer versions (34 and above)
        self._RATE1: float = 0.0
        self._RATE2: float = 0.0
        self._RATE3: float = 0.0
        self._RATE4: float = 0.0
        self._RATE5: float = 0.0
        self._RATE6: float = 0.0
        self._RATE7: float = 0.0
        self._RATE8: float = 0.0
        self._RATE9: float = 0.0
        self._RATE10: float = 0.0
        self._RATE11: float = 0.0
        self._RATE12: float = 0.0

        self._GI: float = 0.0
        self._BI: float = 0.0
        self._GJ: float = 0.0
        self._BJ: float = 0.0
        self._ST: int = 1
        self._MET: int = 1
        self._LEN: float = 1.0

        self._O1: int = 1
        self._F1: float = 1.0
        self._O2: int = 0
        self._F2: float = 0.0
        self._O3: int = 0
        self._F3: float = 0.0
        self._O4: int = 0
        self._F4: float = 0.0

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
        return "{0}_{1}_{2}".format(self.I, self.J, self.CKT)

    def get_seed(self):
        return "_BR_{}".format(self.get_id())

    @property
    def I(self):
        return self._I

    @I.setter
    def I(self, value: int | str | None) -> None:
        self._I = coerce_psse_int(value=value, current_value=self._I)

    @property
    def J(self):
        return self._J

    @J.setter
    def J(self, value: int | str | None) -> None:
        self._J = coerce_psse_int(value=value, current_value=self._J)

    @property
    def CKT(self):
        return self._CKT

    @CKT.setter
    def CKT(self, value: str | int | float | None) -> None:
        self._CKT = coerce_psse_str(value=value, current_value=self._CKT)

    @property
    def R(self):
        return self._R

    @R.setter
    def R(self, value: float | int | str | None) -> None:
        self._R = coerce_psse_float(value=value, current_value=self._R)

    @property
    def X(self):
        return self._X

    @X.setter
    def X(self, value: float | int | str | None) -> None:
        self._X = coerce_psse_float(value=value, current_value=self._X)

    @property
    def B(self):
        return self._B

    @B.setter
    def B(self, value: float | int | str | None) -> None:
        self._B = coerce_psse_float(value=value, current_value=self._B)

    @property
    def NAME(self):
        return self._NAME

    @NAME.setter
    def NAME(self, value: str | int | float | None) -> None:
        self._NAME = coerce_psse_str(value=value, current_value=self._NAME)

    # Individual property methods for each RATE attribute
    @property
    def RATE1(self):
        return self._RATE1

    @RATE1.setter
    def RATE1(self, value: float | int | str | None) -> None:
        self._RATE1 = coerce_psse_float(value=value, current_value=self._RATE1)

    @property
    def RATE2(self):
        return self._RATE2

    @RATE2.setter
    def RATE2(self, value: float | int | str | None) -> None:
        self._RATE2 = coerce_psse_float(value=value, current_value=self._RATE2)

    @property
    def RATE3(self):
        return self._RATE3

    @RATE3.setter
    def RATE3(self, value: float | int | str | None) -> None:
        self._RATE3 = coerce_psse_float(value=value, current_value=self._RATE3)

    @property
    def RATEA(self):
        return self._RATE1

    @RATEA.setter
    def RATEA(self, value: float | int | str | None) -> None:
        self._RATE1 = coerce_psse_float(value=value, current_value=self._RATE1)

    @property
    def RATEB(self):
        return self._RATE2

    @RATEB.setter
    def RATEB(self, value: float | int | str | None) -> None:
        self._RATE2 = coerce_psse_float(value=value, current_value=self._RATE2)

    @property
    def RATEC(self):
        return self._RATE3

    @RATEC.setter
    def RATEC(self, value: float | int | str | None) -> None:
        self._RATE3 = coerce_psse_float(value=value, current_value=self._RATE3)

    @property
    def RATE4(self):
        return self._RATE4

    @RATE4.setter
    def RATE4(self, value: float | int | str | None) -> None:
        self._RATE4 = coerce_psse_float(value=value, current_value=self._RATE4)

    @property
    def RATE5(self):
        return self._RATE5

    @RATE5.setter
    def RATE5(self, value: float | int | str | None) -> None:
        self._RATE5 = coerce_psse_float(value=value, current_value=self._RATE5)

    @property
    def RATE6(self):
        return self._RATE6

    @RATE6.setter
    def RATE6(self, value: float | int | str | None) -> None:
        self._RATE6 = coerce_psse_float(value=value, current_value=self._RATE6)

    @property
    def RATE7(self):
        return self._RATE7

    @RATE7.setter
    def RATE7(self, value: float | int | str | None) -> None:
        self._RATE7 = coerce_psse_float(value=value, current_value=self._RATE7)

    @property
    def RATE8(self):
        return self._RATE8

    @RATE8.setter
    def RATE8(self, value: float | int | str | None) -> None:
        self._RATE8 = coerce_psse_float(value=value, current_value=self._RATE8)

    @property
    def RATE9(self):
        return self._RATE9

    @RATE9.setter
    def RATE9(self, value: float | int | str | None) -> None:
        self._RATE9 = coerce_psse_float(value=value, current_value=self._RATE9)

    @property
    def RATE10(self):
        return self._RATE10

    @RATE10.setter
    def RATE10(self, value: float | int | str | None) -> None:
        self._RATE10 = coerce_psse_float(value=value, current_value=self._RATE10)

    @property
    def RATE11(self):
        return self._RATE11

    @RATE11.setter
    def RATE11(self, value: float | int | str | None) -> None:
        self._RATE11 = coerce_psse_float(value=value, current_value=self._RATE11)

    @property
    def RATE12(self):
        return self._RATE12

    @RATE12.setter
    def RATE12(self, value: float | int | str | None) -> None:
        self._RATE12 = coerce_psse_float(value=value, current_value=self._RATE12)

    @property
    def GI(self):
        return self._GI

    @GI.setter
    def GI(self, value: float | int | str | None) -> None:
        self._GI = coerce_psse_float(value=value, current_value=self._GI)

    @property
    def BI(self):
        return self._BI

    @BI.setter
    def BI(self, value: float | int | str | None) -> None:
        self._BI = coerce_psse_float(value=value, current_value=self._BI)

    @property
    def GJ(self):
        return self._GJ

    @GJ.setter
    def GJ(self, value: float | int | str | None) -> None:
        self._GJ = coerce_psse_float(value=value, current_value=self._GJ)

    @property
    def BJ(self):
        return self._BJ

    @BJ.setter
    def BJ(self, value: float | int | str | None) -> None:
        self._BJ = coerce_psse_float(value=value, current_value=self._BJ)

    @property
    def ST(self):
        return self._ST

    @ST.setter
    def ST(self, value: int | str | None) -> None:
        self._ST = coerce_psse_int(value=value, current_value=self._ST)

    @property
    def MET(self):
        return self._MET

    @MET.setter
    def MET(self, value: int | str | None) -> None:
        self._MET = coerce_psse_int(value=value, current_value=self._MET)

    @property
    def LEN(self):
        return self._LEN

    @LEN.setter
    def LEN(self, value: float | int | str | None) -> None:
        self._LEN = coerce_psse_float(value=value, current_value=self._LEN)

    @property
    def O1(self):
        return self._O1

    @O1.setter
    def O1(self, value: int | str | None) -> None:
        self._O1 = coerce_psse_int(value=value, current_value=self._O1)

    @property
    def F1(self):
        return self._F1

    @F1.setter
    def F1(self, value: float | int | str | None) -> None:
        self._F1 = coerce_psse_float(value=value, current_value=self._F1)

    @property
    def O2(self):
        return self._O2

    @O2.setter
    def O2(self, value: int | str | None) -> None:
        self._O2 = coerce_psse_int(value=value, current_value=self._O2)

    @property
    def F2(self):
        return self._F2

    @F2.setter
    def F2(self, value: float | int | str | None) -> None:
        self._F2 = coerce_psse_float(value=value, current_value=self._F2)

    @property
    def O3(self):
        return self._O3

    @O3.setter
    def O3(self, value: int | str | None) -> None:
        self._O3 = coerce_psse_int(value=value, current_value=self._O3)

    @property
    def F3(self):
        return self._F3

    @F3.setter
    def F3(self, value: float | int | str | None) -> None:
        self._F3 = coerce_psse_float(value=value, current_value=self._F3)

    @property
    def O4(self):
        return self._O4

    @O4.setter
    def O4(self, value: int | str | None) -> None:
        self._O4 = coerce_psse_int(value=value, current_value=self._O4)

    @property
    def F4(self):
        return self._F4

    @F4.setter
    def F4(self, value: float | int | str | None) -> None:
        self._F4 = coerce_psse_float(value=value, current_value=self._F4)
