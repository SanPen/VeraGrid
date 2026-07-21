# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol, Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str


class RawTwoTerminalDCLine(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Line name', max_chars=12),
        PsseProperty(property_name='MDC', rawx_key='mdc', class_type=int,
                     description='Control mode: 0 for blocked, 1 for power, 2 for current.', min_value=0, max_value=2),
        PsseProperty(property_name='RDC', rawx_key='rdc', class_type=float, description='DC line resistance',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.ohm)),
        PsseProperty(property_name='SETVL', rawx_key='setvl', class_type=float, description='Sending power',
                     unit=Unit(UnitMultiplier.M, UnitSymbol.W)),
        PsseProperty(property_name='VSCHD', rawx_key='vschd', class_type=float, description='DC voltage',
                     unit=Unit(UnitMultiplier.k, UnitSymbol.V)),
        PsseProperty(property_name='VCMOD', rawx_key='vcmod', class_type=float, description='Mode switch dc voltage',
                     unit=Unit(UnitMultiplier.k, UnitSymbol.V)),
        PsseProperty(property_name='RCOMP', rawx_key='rcomp', class_type=float, description='Compounding resistance',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.ohm)),
        PsseProperty(property_name='DELTI', rawx_key='delti', class_type=float,
                     description='Margin entered in per unit of desired dc power',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.pu)),
        PsseProperty(property_name='METER', rawx_key='meter', class_type=str,
                     description='Metered end code of either R (for rectifier) or I (for inverter).'),
        PsseProperty(property_name='DCVMIN', rawx_key='dcvmin', class_type=float, description='Minimum dc voltage;',
                     unit=Unit(UnitMultiplier.k, UnitSymbol.V)),
        PsseProperty(property_name='CCCITMX', rawx_key='cccitmx', class_type=int,
                     description='Iteration limit for capacitor commutated two-terminal dc line Newton solution procedure.'),
        PsseProperty(property_name='CCCACC', rawx_key='cccacc', class_type=float,
                     description='Acceleration factor for capacitor commutated two-terminal dc line Newton solution procedure'),
        PsseProperty(property_name='IPR', rawx_key='ipr', class_type=int, description='Rectifier converter bus number',
                     min_value=0, max_value=999997, max_chars=6),
        PsseProperty(property_name='NBR', rawx_key='nbr', class_type=int,
                     description='Rectifier number of bridges in series'),
        PsseProperty(property_name='ANMXR', rawx_key='anmxr', class_type=float,
                     description='Rectifier nominal maximum rectifier firing angle',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.deg)),
        PsseProperty(property_name='ANMNR', rawx_key='anmnr', class_type=float,
                     description='Rectifier minimum steady-state rectifier firing angle',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.deg)),
        PsseProperty(property_name='RCR', rawx_key='rcr', class_type=float,
                     description='Rectifier commutating transformer resistance per bridge',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.ohm)),
        PsseProperty(property_name='XCR', rawx_key='xcr', class_type=float,
                     description='Rectifier commutating transformer reactance per bridge',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.ohm)),
        PsseProperty(property_name='EBASR', rawx_key='ebasr', class_type=float,
                     description='Rectifier primary base ac voltage', unit=Unit(UnitMultiplier.k, UnitSymbol.V)),
        PsseProperty(property_name='TRR', rawx_key='trr', class_type=float, description='Rectifier transformer ratio.'),
        PsseProperty(property_name='TAPR', rawx_key='tapr', class_type=float, description='Rectifier tap setting',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.pu)),
        PsseProperty(property_name='TMXR', rawx_key='tmxr', class_type=float,
                     description='Maximum rectifier tap setting.', unit=Unit(UnitMultiplier.none, UnitSymbol.pu)),
        PsseProperty(property_name='TMNR', rawx_key='tmnr', class_type=float,
                     description='Minimum rectifier tap setting', unit=Unit(UnitMultiplier.none, UnitSymbol.pu)),
        PsseProperty(property_name='STPR', rawx_key='stpr', class_type=float, description='Rectifier tap step;',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.pu), min_value=0, max_value=999999),
        PsseProperty(property_name='ICR', rawx_key='icr', class_type=int,
                     description='Bus number of the rectifier commutating bus', min_value=0, max_value=999999,
                     max_chars=6),
        PsseProperty(property_name='NDR', rawx_key='ndr', class_type=int, description='A node number of bus ICR',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='IFR', rawx_key='ifr', class_type=int, description='Winding 1 side from bus number',
                     max_chars=6),
        PsseProperty(property_name='ITR', rawx_key='itr', class_type=int, description='Winding 2 side to bus number',
                     max_chars=6),
        PsseProperty(property_name='IDR', rawx_key='idr', class_type=str,
                     description='Circuit identifier; the branch described by IFR, ITR, and IDR must have been entered as a two-winding transformer'),
        PsseProperty(property_name='XCAPR', rawx_key='xcapr', class_type=float,
                     description='Commutating capacitor reactance magnitude per bridge',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.ohm)),
        PsseProperty(property_name='IPI', rawx_key='ipi', class_type=int, description='Inverter converter bus number',
                     min_value=0, max_value=999997, max_chars=6),
        PsseProperty(property_name='NBI', rawx_key='nbi', class_type=int,
                     description='Inverter number of bridges in series'),
        PsseProperty(property_name='ANMXI', rawx_key='anmxi', class_type=float,
                     description='Inverter nominal maximum Inverter firing angle',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.deg)),
        PsseProperty(property_name='ANMNI', rawx_key='anmni', class_type=float,
                     description='Inverter minimum steady-state Inverter firing angle',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.deg)),
        PsseProperty(property_name='RCI', rawx_key='rci', class_type=float,
                     description='Inverter commutating transformer resistance per bridge',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.ohm)),
        PsseProperty(property_name='XCI', rawx_key='xci', class_type=float,
                     description='Inverter commutating transformer reactance per bridge',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.ohm)),
        PsseProperty(property_name='EBASI', rawx_key='ebasi', class_type=float,
                     description='Inverter primary base ac voltage', unit=Unit(UnitMultiplier.k, UnitSymbol.V)),
        PsseProperty(property_name='TRI', rawx_key='tri', class_type=float, description='Inverter transformer ratio.'),
        PsseProperty(property_name='TAPI', rawx_key='tapi', class_type=float, description='Inverter tap setting',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.pu)),
        PsseProperty(property_name='TMXI', rawx_key='tmxi', class_type=float,
                     description='Maximum Inverter tap setting.', unit=Unit(UnitMultiplier.none, UnitSymbol.pu)),
        PsseProperty(property_name='TMNI', rawx_key='tmni', class_type=float,
                     description='Minimum Inverter tap setting', unit=Unit(UnitMultiplier.none, UnitSymbol.pu)),
        PsseProperty(property_name='STPI', rawx_key='stpi', class_type=float, description='Inverter tap step;',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.pu), min_value=0, max_value=999999),
        PsseProperty(property_name='ICI', rawx_key='ici', class_type=int,
                     description='Bus number of the Inverter commutating bus', min_value=0, max_value=999999),
        PsseProperty(property_name='NDI', rawx_key='ndi', class_type=int, description='A node number of bus ICR',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='IFI', rawx_key='ifi', class_type=int, description='Winding 1 side from bus number'),
        PsseProperty(property_name='ITI', rawx_key='iti', class_type=int, description='Winding 2 side to bus number',
                     max_chars=6),
        PsseProperty(property_name='IDI', rawx_key='idi', class_type=str,
                     description='Circuit identifier; the branch described by IFR, ITR, and IDR must have been entered as a two-winding transformer'),
        PsseProperty(property_name='XCAPI', rawx_key='xcapi', class_type=float,
                     description='Commutating capacitor reactance magnitude per bridge',
                     unit=Unit(UnitMultiplier.none, UnitSymbol.ohm)),
    )

    def __init__(self):
        RawObject.__init__(self, "Two-terminal DC line")

        self._NAME: str = ""
        self._MDC: int = 0
        self._RDC: float = 0.0
        self._SETVL: float = 0.0
        self._VSCHD: float = 0.0
        self._VCMOD: float = 0.0
        self._RCOMP: float = 0.0
        self._DELTI: float = 0.0
        self._METER: str = "I"
        self._DCVMIN: float = 0.0
        self._CCCITMX: int = 20
        self._CCCACC: float = 1.0

        self._IPR: int = 0
        self._NBR: int = 0
        self._ANMXR: float = 0.0
        self._ANMNR: float = 0.0
        self._RCR: float = 0.0
        self._XCR: float = 0.0
        self._EBASR: float = 0.0
        self._TRR: float = 1.0
        self._TAPR: float = 0.0
        self._TMXR: float = 1.5
        self._TMNR: float = 0.51
        self._STPR: float = 0.00625
        self._ICR: int = 0
        self._NDR: int = 0
        self._IFR: int = 0
        self._ITR: int = 0
        self._IDR: str = '1'
        self._XCAPR: float = 0.0

        self._IPI: int = 0
        self._NBI: int = 0
        self._ANMXI: float = 0.0
        self._ANMNI: float = 0.0
        self._RCI: float = 0.0
        self._XCI: float = 0.0
        self._EBASI: float = 0.0
        self._TRI: float = 1.0
        self._TAPI: float = 0.0
        self._TMXI: float = 1.5
        self._TMNI: float = 0.51
        self._STPI: float = 0.00625
        self._ICI: int = 0
        self._NDI: int = 0
        self._IFI: int = 0
        self._ITI: int = 0
        self._IDI: str = '1'
        self._XCAPI: float = 0.0

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
        return "{0}_{1}_1".format(self.IPR, self.IPI)

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
    def SETVL(self) -> float:
        return self._SETVL

    @SETVL.setter
    def SETVL(self, value: float | int | str | None) -> None:
        self._SETVL = coerce_psse_float(value=value, current_value=self._SETVL)

    @property
    def VSCHD(self) -> float:
        return self._VSCHD

    @VSCHD.setter
    def VSCHD(self, value: float | int | str | None) -> None:
        self._VSCHD = coerce_psse_float(value=value, current_value=self._VSCHD)

    @property
    def VCMOD(self) -> float:
        return self._VCMOD

    @VCMOD.setter
    def VCMOD(self, value: float | int | str | None) -> None:
        self._VCMOD = coerce_psse_float(value=value, current_value=self._VCMOD)

    @property
    def RCOMP(self) -> float:
        return self._RCOMP

    @RCOMP.setter
    def RCOMP(self, value: float | int | str | None) -> None:
        self._RCOMP = coerce_psse_float(value=value, current_value=self._RCOMP)

    @property
    def DELTI(self) -> float:
        return self._DELTI

    @DELTI.setter
    def DELTI(self, value: float | int | str | None) -> None:
        self._DELTI = coerce_psse_float(value=value, current_value=self._DELTI)

    @property
    def METER(self) -> str:
        return self._METER

    @METER.setter
    def METER(self, value: str | int | float | None) -> None:
        self._METER = coerce_psse_str(value=value, current_value=self._METER)

    @property
    def DCVMIN(self) -> float:
        return self._DCVMIN

    @DCVMIN.setter
    def DCVMIN(self, value: float | int | str | None) -> None:
        self._DCVMIN = coerce_psse_float(value=value, current_value=self._DCVMIN)

    @property
    def CCCITMX(self) -> int:
        return self._CCCITMX

    @CCCITMX.setter
    def CCCITMX(self, value: int | str | None) -> None:
        self._CCCITMX = coerce_psse_int(value=value, current_value=self._CCCITMX)

    @property
    def CCCACC(self) -> float:
        return self._CCCACC

    @CCCACC.setter
    def CCCACC(self, value: float | int | str | None) -> None:
        self._CCCACC = coerce_psse_float(value=value, current_value=self._CCCACC)

    @property
    def IPR(self) -> int:
        return self._IPR

    @IPR.setter
    def IPR(self, value: int | str | None) -> None:
        self._IPR = coerce_psse_int(value=value, current_value=self._IPR)

    @property
    def NBR(self) -> int:
        return self._NBR

    @NBR.setter
    def NBR(self, value: int | str | None) -> None:
        self._NBR = coerce_psse_int(value=value, current_value=self._NBR)

    @property
    def ANMXR(self) -> float:
        return self._ANMXR

    @ANMXR.setter
    def ANMXR(self, value: float | int | str | None) -> None:
        self._ANMXR = coerce_psse_float(value=value, current_value=self._ANMXR)

    @property
    def ANMNR(self) -> float:
        return self._ANMNR

    @ANMNR.setter
    def ANMNR(self, value: float | int | str | None) -> None:
        self._ANMNR = coerce_psse_float(value=value, current_value=self._ANMNR)

    @property
    def RCR(self) -> float:
        return self._RCR

    @RCR.setter
    def RCR(self, value: float | int | str | None) -> None:
        self._RCR = coerce_psse_float(value=value, current_value=self._RCR)

    @property
    def XCR(self) -> float:
        return self._XCR

    @XCR.setter
    def XCR(self, value: float | int | str | None) -> None:
        self._XCR = coerce_psse_float(value=value, current_value=self._XCR)

    @property
    def EBASR(self) -> float:
        return self._EBASR

    @EBASR.setter
    def EBASR(self, value: float | int | str | None) -> None:
        self._EBASR = coerce_psse_float(value=value, current_value=self._EBASR)

    @property
    def TRR(self) -> float:
        return self._TRR

    @TRR.setter
    def TRR(self, value: float | int | str | None) -> None:
        self._TRR = coerce_psse_float(value=value, current_value=self._TRR)

    @property
    def TAPR(self) -> float:
        return self._TAPR

    @TAPR.setter
    def TAPR(self, value: float | int | str | None) -> None:
        self._TAPR = coerce_psse_float(value=value, current_value=self._TAPR)

    @property
    def TMXR(self) -> float:
        return self._TMXR

    @TMXR.setter
    def TMXR(self, value: float | int | str | None) -> None:
        self._TMXR = coerce_psse_float(value=value, current_value=self._TMXR)

    @property
    def TMNR(self) -> float:
        return self._TMNR

    @TMNR.setter
    def TMNR(self, value: float | int | str | None) -> None:
        self._TMNR = coerce_psse_float(value=value, current_value=self._TMNR)

    @property
    def STPR(self) -> float:
        return self._STPR

    @STPR.setter
    def STPR(self, value: float | int | str | None) -> None:
        self._STPR = coerce_psse_float(value=value, current_value=self._STPR)

    @property
    def ICR(self) -> int:
        return self._ICR

    @ICR.setter
    def ICR(self, value: int | str | None) -> None:
        self._ICR = coerce_psse_int(value=value, current_value=self._ICR)

    @property
    def NDR(self) -> int:
        return self._NDR

    @NDR.setter
    def NDR(self, value: int | str | None) -> None:
        self._NDR = coerce_psse_int(value=value, current_value=self._NDR)

    @property
    def IFR(self) -> int:
        return self._IFR

    @IFR.setter
    def IFR(self, value: int | str | None) -> None:
        self._IFR = coerce_psse_int(value=value, current_value=self._IFR)

    @property
    def ITR(self) -> int:
        return self._ITR

    @ITR.setter
    def ITR(self, value: int | str | None) -> None:
        self._ITR = coerce_psse_int(value=value, current_value=self._ITR)

    @property
    def IDR(self) -> str:
        return self._IDR

    @IDR.setter
    def IDR(self, value: str | int | float | None) -> None:
        self._IDR = coerce_psse_str(value=value, current_value=self._IDR)

    @property
    def XCAPR(self) -> float:
        return self._XCAPR

    @XCAPR.setter
    def XCAPR(self, value: float | int | str | None) -> None:
        self._XCAPR = coerce_psse_float(value=value, current_value=self._XCAPR)

    @property
    def IPI(self) -> int:
        return self._IPI

    @IPI.setter
    def IPI(self, value: int | str | None) -> None:
        self._IPI = coerce_psse_int(value=value, current_value=self._IPI)

    @property
    def NBI(self) -> int:
        return self._NBI

    @NBI.setter
    def NBI(self, value: int | str | None) -> None:
        self._NBI = coerce_psse_int(value=value, current_value=self._NBI)

    @property
    def ANMXI(self) -> float:
        return self._ANMXI

    @ANMXI.setter
    def ANMXI(self, value: float | int | str | None) -> None:
        self._ANMXI = coerce_psse_float(value=value, current_value=self._ANMXI)

    @property
    def ANMNI(self) -> float:
        return self._ANMNI

    @ANMNI.setter
    def ANMNI(self, value: float | int | str | None) -> None:
        self._ANMNI = coerce_psse_float(value=value, current_value=self._ANMNI)

    @property
    def RCI(self) -> float:
        return self._RCI

    @RCI.setter
    def RCI(self, value: float | int | str | None) -> None:
        self._RCI = coerce_psse_float(value=value, current_value=self._RCI)

    @property
    def XCI(self) -> float:
        return self._XCI

    @XCI.setter
    def XCI(self, value: float | int | str | None) -> None:
        self._XCI = coerce_psse_float(value=value, current_value=self._XCI)

    @property
    def EBASI(self) -> float:
        return self._EBASI

    @EBASI.setter
    def EBASI(self, value: float | int | str | None) -> None:
        self._EBASI = coerce_psse_float(value=value, current_value=self._EBASI)

    @property
    def TRI(self) -> float:
        return self._TRI

    @TRI.setter
    def TRI(self, value: float | int | str | None) -> None:
        self._TRI = coerce_psse_float(value=value, current_value=self._TRI)

    @property
    def TAPI(self) -> float:
        return self._TAPI

    @TAPI.setter
    def TAPI(self, value: float | int | str | None) -> None:
        self._TAPI = coerce_psse_float(value=value, current_value=self._TAPI)

    @property
    def TMXI(self) -> float:
        return self._TMXI

    @TMXI.setter
    def TMXI(self, value: float | int | str | None) -> None:
        self._TMXI = coerce_psse_float(value=value, current_value=self._TMXI)

    @property
    def TMNI(self) -> float:
        return self._TMNI

    @TMNI.setter
    def TMNI(self, value: float | int | str | None) -> None:
        self._TMNI = coerce_psse_float(value=value, current_value=self._TMNI)

    @property
    def STPI(self) -> float:
        return self._STPI

    @STPI.setter
    def STPI(self, value: float | int | str | None) -> None:
        self._STPI = coerce_psse_float(value=value, current_value=self._STPI)

    @property
    def ICI(self) -> int:
        return self._ICI

    @ICI.setter
    def ICI(self, value: int | str | None) -> None:
        self._ICI = coerce_psse_int(value=value, current_value=self._ICI)

    @property
    def NDI(self) -> int:
        return self._NDI

    @NDI.setter
    def NDI(self, value: int | str | None) -> None:
        self._NDI = coerce_psse_int(value=value, current_value=self._NDI)

    @property
    def IFI(self) -> int:
        return self._IFI

    @IFI.setter
    def IFI(self, value: int | str | None) -> None:
        self._IFI = coerce_psse_int(value=value, current_value=self._IFI)

    @property
    def ITI(self) -> int:
        return self._ITI

    @ITI.setter
    def ITI(self, value: int | str | None) -> None:
        self._ITI = coerce_psse_int(value=value, current_value=self._ITI)

    @property
    def IDI(self) -> str:
        return self._IDI

    @IDI.setter
    def IDI(self, value: str | int | float | None) -> None:
        self._IDI = coerce_psse_str(value=value, current_value=self._IDI)

    @property
    def XCAPI(self) -> float:
        return self._XCAPI

    @XCAPI.setter
    def XCAPI(self, value: float | int | str | None) -> None:
        self._XCAPI = coerce_psse_float(value=value, current_value=self._XCAPI)
