# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawVscDCLine(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Device name', max_chars=12),
        PsseProperty(property_name='MDC', rawx_key='mdc', class_type=int,
                     description='Control mode:\n•  0 - for out-of-service\n•  1 - for in-service', min_value=0,
                     max_value=1),
        PsseProperty(property_name='RDC', rawx_key='rdc', class_type=float, description='The dc line resistance',
                     min_value=0, max_value=999999, unit=Unit.get_ohm()),
        PsseProperty(property_name='IBUS1', rawx_key='ibus1', class_type=int, description='Converter bus number, ',
                     min_value=0, max_value=999999, max_chars=6),
        PsseProperty(property_name='TYPE1', rawx_key='type1', class_type=int,
                     description='Code for the type of converter dc control:\n•  0 - for converter out-of-service\n•  1 - for dc voltage control\n•  2 -for MW control\nWhen both converters are in-service, exactly one converter of each VSC dc line must be TYPE 1.',
                     min_value=0, max_value=2),
        PsseProperty(property_name='MODE1', rawx_key='mode1', class_type=int,
                     description='Converter ac control mode:1 -> AC voltage control\n2 -> fixed AC power factor\n',
                     min_value=0, max_value=2),
        PsseProperty(property_name='DCSET1', rawx_key='dcset1', class_type=float,
                     description='Converter dc setpoint (see manual)', unit=Unit.get_mw()),
        PsseProperty(property_name='ACSET1', rawx_key='acset1', class_type=float,
                     description='Converter ac setpoint. 1-> AC voltage, 2-> power factor', unit=Unit.get_pu()),
        PsseProperty(property_name='ALOSS1', rawx_key='aloss1', class_type=float,
                     description='Losses constant coefficient: loss = ALOSS + (Idc * BLOSS)', unit=Unit.get_kw()),
        PsseProperty(property_name='BLOSS1', rawx_key='bloss1', class_type=float,
                     description='Losses proportional coefficient: loss = ALOSS + (Idc * BLOSS)', unit=Unit.get_kw(),
                     denominator_unit=Unit.get_a()),
        PsseProperty(property_name='MINLOSS1', rawx_key='minloss1', class_type=int,
                     description='Minimum converter losses', unit=Unit.get_kw()),
        PsseProperty(property_name='SMAX1', rawx_key='smax1', class_type=float, description='Converter MVA rating',
                     unit=Unit.get_mw()),
        PsseProperty(property_name='IMAX1', rawx_key='imax1', class_type=float,
                     description='Converter ac current rating', unit=Unit.get_a()),
        PsseProperty(property_name='PWF1', rawx_key='pwf1', class_type=float,
                     description='Power weighting factor fraction (see manual)', min_value=0.0, max_value=1.0),
        PsseProperty(property_name='MAXQ1', rawx_key='maxq1', class_type=float,
                     description='Reactive power upper limit (see manual)', unit=Unit.get_mvar()),
        PsseProperty(property_name='MINQ1', rawx_key='minq1', class_type=float,
                     description='Reactive power lower limit (see manual)', unit=Unit.get_mvar()),
        PsseProperty(property_name='REMOT1', rawx_key='remot1', class_type=int, description='Control bus (see manual)',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='VSREG1', rawx_key='vseg1', class_type=int, description='Control bus (see manual)',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='NREG1', rawx_key='nreg1', class_type=int, description='Control node (see manual)',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='RMPCT1', rawx_key='rmpct1', class_type=float,
                     description='Percent of the total Mvar required to hold the voltage at the bus controlled by IBUS (see manual)',
                     unit=Unit.get_percent()),
        PsseProperty(property_name='IBUS2', rawx_key='ibus2', class_type=int, description='Converter bus number',
                     min_value=0, max_value=999999, max_chars=6),
        PsseProperty(property_name='TYPE2', rawx_key='type2', class_type=int,
                     description='Converter ac control mode:0 -> out of service\n1 -> AC voltage control\n2 -> fixed AC power factor\n',
                     min_value=0, max_value=2),
        PsseProperty(property_name='MODE2', rawx_key='mode2', class_type=int,
                     description='Converter ac control mode:1 -> AC voltage control\n2 -> fixed AC power factor\n',
                     min_value=1, max_value=2),
        PsseProperty(property_name='DCSET2', rawx_key='dcset2', class_type=float,
                     description='Converter dc setpoint (see manual)', unit=Unit.get_mw()),
        PsseProperty(property_name='ACSET2', rawx_key='acset2', class_type=float,
                     description='Converter ac setpoint. 1-> AC voltage, 2-> power factor', unit=Unit.get_pu()),
        PsseProperty(property_name='ALOSS2', rawx_key='aloss2', class_type=float,
                     description='Losses constant coefficient: loss = ALOSS + (Idc * BLOSS)', unit=Unit.get_kw()),
        PsseProperty(property_name='BLOSS2', rawx_key='bloss2', class_type=float,
                     description='Losses proportional coefficient: loss = ALOSS + (Idc * BLOSS)', unit=Unit.get_kw(),
                     denominator_unit=Unit.get_a()),
        PsseProperty(property_name='MINLOSS2', rawx_key='minloss2', class_type=int,
                     description='Minimum converter losses', unit=Unit.get_kw()),
        PsseProperty(property_name='SMAX2', rawx_key='smax2', class_type=float, description='Converter MVA rating',
                     unit=Unit.get_mw()),
        PsseProperty(property_name='IMAX2', rawx_key='imax2', class_type=float,
                     description='Converter ac current rating', unit=Unit.get_a()),
        PsseProperty(property_name='PWF2', rawx_key='pwf2', class_type=float,
                     description='Power weighting factor fraction (see manual)'),
        PsseProperty(property_name='MAXQ2', rawx_key='maxq2', class_type=float,
                     description='Reactive power upper limit (see manual)', unit=Unit.get_mvar()),
        PsseProperty(property_name='MINQ2', rawx_key='minq2', class_type=float,
                     description='Reactive power lower limit (see manual)', unit=Unit.get_mvar()),
        PsseProperty(property_name='REMOT2', rawx_key='remot2', class_type=int, description='Control bus (see manual)',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='VSREG2', rawx_key='vseg2', class_type=int, description='Control bus (see manual)',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='NREG2', rawx_key='nreg2', class_type=int, description='Control node (see manual)',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='RMPCT2', rawx_key='rmpct2', class_type=float,
                     description='Percent of the total Mvar required to hold the voltage at the bus controlled by IBUS (see manual)',
                     unit=Unit.get_percent()),
        PsseProperty(property_name='O{}'.format(0 + 1), rawx_key='o{}'.format(0 + 1), class_type=int,
                     description='Owner number {}'.format(0 + 1), min_value=1, max_value=9999),
        PsseProperty(property_name='F{}'.format(0 + 1), rawx_key='f{}'.format(0 + 1), class_type=float,
                     description='Ownership fraction {}'.format(0 + 1), min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(1 + 1), rawx_key='o{}'.format(1 + 1), class_type=int,
                     description='Owner number {}'.format(1 + 1), min_value=1, max_value=9999),
        PsseProperty(property_name='F{}'.format(1 + 1), rawx_key='f{}'.format(1 + 1), class_type=float,
                     description='Ownership fraction {}'.format(1 + 1), min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(2 + 1), rawx_key='o{}'.format(2 + 1), class_type=int,
                     description='Owner number {}'.format(2 + 1), min_value=1, max_value=9999),
        PsseProperty(property_name='F{}'.format(2 + 1), rawx_key='f{}'.format(2 + 1), class_type=float,
                     description='Ownership fraction {}'.format(2 + 1), min_value=0.0, max_value=1.0),
        PsseProperty(property_name='O{}'.format(3 + 1), rawx_key='o{}'.format(3 + 1), class_type=int,
                     description='Owner number {}'.format(3 + 1), min_value=1, max_value=9999),
        PsseProperty(property_name='F{}'.format(3 + 1), rawx_key='f{}'.format(3 + 1), class_type=float,
                     description='Ownership fraction {}'.format(3 + 1), min_value=0.0, max_value=1.0),
    )

    def __init__(self):
        RawObject.__init__(self, "VSC DC line")

        self._O1: int = 0
        self._F1: float = 0.0
        self._O2: int = 0
        self._F2: float = 0.0
        self._O3: int = 0
        self._F3: float = 0.0
        self._O4: int = 0
        self._F4: float = 0.0

        self._NAME: str = ""
        self._MDC: int = 1
        self._RDC: float = 0.0

        self._IBUS1: int = 0
        self._TYPE1: int = 1
        self._MODE1: int = 1
        self._DCSET1: float = 0.0
        self._ACSET1: float = 1.0
        self._ALOSS1: float = 0.0
        self._BLOSS1: float = 0.0
        self._MINLOSS1: int = 0
        self._SMAX1: float = 0.0
        self._IMAX1: float = 0.0
        self._PWF1: float = 0.0
        self._MAXQ1: float = 0.0
        self._MINQ1: float = 0.0
        self._REMOT1: int = 0

        self._VSREG1: int = 0
        self._NREG1: int = 0
        self._RMPCT1: float = 0.0

        self._IBUS2: int = 0
        self._TYPE2: int = 0
        self._MODE2: int = 0
        self._DCSET2: float = 0.0
        self._ACSET2: float = 0.0
        self._ALOSS2: float = 0.0
        self._BLOSS2: float = 0.0
        self._MINLOSS2: int = 0
        self._SMAX2: float = 0.0
        self._IMAX2: float = 0.0
        self._PWF2: float = 0.0
        self._MAXQ2: float = 0.0
        self._MINQ2: float = 0.0
        self._REMOT2: int = 0
        self._VSREG2: int = 0
        self._NREG2: int = 0
        self._RMPCT2: float = 100.0

        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------

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
        return "{0}_{1}_1".format(self.IBUS1, self.IBUS2)

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
    def NAME(self) -> str:
        return self._NAME

    @NAME.setter
    def NAME(self, value: str | int | float | None) -> None:
        self._NAME = coerce_psse_str(value=value, current_value=self._NAME)

    @property
    def MDC(self) -> int:
        return self._MDC

    @MDC.setter
    def MDC(self, value: int | str | None) -> None:
        self._MDC = coerce_psse_int(value=value, current_value=self._MDC)

    @property
    def RDC(self) -> float:
        return self._RDC

    @RDC.setter
    def RDC(self, value: float | int | str | None) -> None:
        self._RDC = coerce_psse_float(value=value, current_value=self._RDC)

    @property
    def IBUS1(self) -> int:
        return self._IBUS1

    @IBUS1.setter
    def IBUS1(self, value: int | str | None) -> None:
        self._IBUS1 = coerce_psse_int(value=value, current_value=self._IBUS1)

    @property
    def TYPE1(self) -> int:
        return self._TYPE1

    @TYPE1.setter
    def TYPE1(self, value: int | str | None) -> None:
        self._TYPE1 = coerce_psse_int(value=value, current_value=self._TYPE1)

    @property
    def MODE1(self) -> int:
        return self._MODE1

    @MODE1.setter
    def MODE1(self, value: int | str | None) -> None:
        self._MODE1 = coerce_psse_int(value=value, current_value=self._MODE1)

    @property
    def DCSET1(self) -> float:
        return self._DCSET1

    @DCSET1.setter
    def DCSET1(self, value: float | int | str | None) -> None:
        self._DCSET1 = coerce_psse_float(value=value, current_value=self._DCSET1)

    @property
    def ACSET1(self) -> float:
        return self._ACSET1

    @ACSET1.setter
    def ACSET1(self, value: float | int | str | None) -> None:
        self._ACSET1 = coerce_psse_float(value=value, current_value=self._ACSET1)

    @property
    def ALOSS1(self) -> float:
        return self._ALOSS1

    @ALOSS1.setter
    def ALOSS1(self, value: float | int | str | None) -> None:
        self._ALOSS1 = coerce_psse_float(value=value, current_value=self._ALOSS1)

    @property
    def BLOSS1(self) -> float:
        return self._BLOSS1

    @BLOSS1.setter
    def BLOSS1(self, value: float | int | str | None) -> None:
        self._BLOSS1 = coerce_psse_float(value=value, current_value=self._BLOSS1)

    @property
    def MINLOSS1(self) -> int:
        return self._MINLOSS1

    @MINLOSS1.setter
    def MINLOSS1(self, value: int | str | None) -> None:
        self._MINLOSS1 = coerce_psse_int(value=value, current_value=self._MINLOSS1)

    @property
    def SMAX1(self) -> float:
        return self._SMAX1

    @SMAX1.setter
    def SMAX1(self, value: float | int | str | None) -> None:
        self._SMAX1 = coerce_psse_float(value=value, current_value=self._SMAX1)

    @property
    def IMAX1(self) -> float:
        return self._IMAX1

    @IMAX1.setter
    def IMAX1(self, value: float | int | str | None) -> None:
        self._IMAX1 = coerce_psse_float(value=value, current_value=self._IMAX1)

    @property
    def PWF1(self) -> float:
        return self._PWF1

    @PWF1.setter
    def PWF1(self, value: float | int | str | None) -> None:
        self._PWF1 = coerce_psse_float(value=value, current_value=self._PWF1)

    @property
    def MAXQ1(self) -> float:
        return self._MAXQ1

    @MAXQ1.setter
    def MAXQ1(self, value: float | int | str | None) -> None:
        self._MAXQ1 = coerce_psse_float(value=value, current_value=self._MAXQ1)

    @property
    def MINQ1(self) -> float:
        return self._MINQ1

    @MINQ1.setter
    def MINQ1(self, value: float | int | str | None) -> None:
        self._MINQ1 = coerce_psse_float(value=value, current_value=self._MINQ1)

    @property
    def REMOT1(self) -> int:
        return self._REMOT1

    @REMOT1.setter
    def REMOT1(self, value: int | str | None) -> None:
        self._REMOT1 = coerce_psse_int(value=value, current_value=self._REMOT1)

    @property
    def VSREG1(self) -> int:
        return self._VSREG1

    @VSREG1.setter
    def VSREG1(self, value: int | str | None) -> None:
        self._VSREG1 = coerce_psse_int(value=value, current_value=self._VSREG1)

    @property
    def NREG1(self) -> int:
        return self._NREG1

    @NREG1.setter
    def NREG1(self, value: int | str | None) -> None:
        self._NREG1 = coerce_psse_int(value=value, current_value=self._NREG1)

    @property
    def RMPCT1(self) -> float:
        return self._RMPCT1

    @RMPCT1.setter
    def RMPCT1(self, value: float | int | str | None) -> None:
        self._RMPCT1 = coerce_psse_float(value=value, current_value=self._RMPCT1)

    @property
    def IBUS2(self) -> int:
        return self._IBUS2

    @IBUS2.setter
    def IBUS2(self, value: int | str | None) -> None:
        self._IBUS2 = coerce_psse_int(value=value, current_value=self._IBUS2)

    @property
    def TYPE2(self) -> int:
        return self._TYPE2

    @TYPE2.setter
    def TYPE2(self, value: int | str | None) -> None:
        self._TYPE2 = coerce_psse_int(value=value, current_value=self._TYPE2)

    @property
    def MODE2(self) -> int:
        return self._MODE2

    @MODE2.setter
    def MODE2(self, value: int | str | None) -> None:
        self._MODE2 = coerce_psse_int(value=value, current_value=self._MODE2)

    @property
    def DCSET2(self) -> float:
        return self._DCSET2

    @DCSET2.setter
    def DCSET2(self, value: float | int | str | None) -> None:
        self._DCSET2 = coerce_psse_float(value=value, current_value=self._DCSET2)

    @property
    def ACSET2(self) -> float:
        return self._ACSET2

    @ACSET2.setter
    def ACSET2(self, value: float | int | str | None) -> None:
        self._ACSET2 = coerce_psse_float(value=value, current_value=self._ACSET2)

    @property
    def ALOSS2(self) -> float:
        return self._ALOSS2

    @ALOSS2.setter
    def ALOSS2(self, value: float | int | str | None) -> None:
        self._ALOSS2 = coerce_psse_float(value=value, current_value=self._ALOSS2)

    @property
    def BLOSS2(self) -> float:
        return self._BLOSS2

    @BLOSS2.setter
    def BLOSS2(self, value: float | int | str | None) -> None:
        self._BLOSS2 = coerce_psse_float(value=value, current_value=self._BLOSS2)

    @property
    def MINLOSS2(self) -> int:
        return self._MINLOSS2

    @MINLOSS2.setter
    def MINLOSS2(self, value: int | str | None) -> None:
        self._MINLOSS2 = coerce_psse_int(value=value, current_value=self._MINLOSS2)

    @property
    def SMAX2(self) -> float:
        return self._SMAX2

    @SMAX2.setter
    def SMAX2(self, value: float | int | str | None) -> None:
        self._SMAX2 = coerce_psse_float(value=value, current_value=self._SMAX2)

    @property
    def IMAX2(self) -> float:
        return self._IMAX2

    @IMAX2.setter
    def IMAX2(self, value: float | int | str | None) -> None:
        self._IMAX2 = coerce_psse_float(value=value, current_value=self._IMAX2)

    @property
    def PWF2(self) -> float:
        return self._PWF2

    @PWF2.setter
    def PWF2(self, value: float | int | str | None) -> None:
        self._PWF2 = coerce_psse_float(value=value, current_value=self._PWF2)

    @property
    def MAXQ2(self) -> float:
        return self._MAXQ2

    @MAXQ2.setter
    def MAXQ2(self, value: float | int | str | None) -> None:
        self._MAXQ2 = coerce_psse_float(value=value, current_value=self._MAXQ2)

    @property
    def MINQ2(self) -> float:
        return self._MINQ2

    @MINQ2.setter
    def MINQ2(self, value: float | int | str | None) -> None:
        self._MINQ2 = coerce_psse_float(value=value, current_value=self._MINQ2)

    @property
    def REMOT2(self) -> int:
        return self._REMOT2

    @REMOT2.setter
    def REMOT2(self, value: int | str | None) -> None:
        self._REMOT2 = coerce_psse_int(value=value, current_value=self._REMOT2)

    @property
    def VSREG2(self) -> int:
        return self._VSREG2

    @VSREG2.setter
    def VSREG2(self, value: int | str | None) -> None:
        self._VSREG2 = coerce_psse_int(value=value, current_value=self._VSREG2)

    @property
    def NREG2(self) -> int:
        return self._NREG2

    @NREG2.setter
    def NREG2(self, value: int | str | None) -> None:
        self._NREG2 = coerce_psse_int(value=value, current_value=self._NREG2)

    @property
    def RMPCT2(self) -> float:
        return self._RMPCT2

    @RMPCT2.setter
    def RMPCT2(self, value: float | int | str | None) -> None:
        self._RMPCT2 = coerce_psse_float(value=value, current_value=self._RMPCT2)
