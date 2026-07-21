# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float, coerce_psse_int, coerce_psse_str
from VeraGridEngine.basic_structures import Logger


class RawSubstationSwitchingDevice(RawObject):
    """
    Base storage for PSSE substation switching devices.

    The version-specific children own the actual RAW field layouts.
    """

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='ISUB', rawx_key='isub', class_type=int,
                     description='Substation number', min_value=1, max_value=99999),
        PsseProperty(property_name='NI', rawx_key='inode', class_type=int,
                     description='From node number', min_value=1, max_value=999),
        PsseProperty(property_name='NJ', rawx_key='jnode', class_type=int,
                     description='To node number', min_value=1, max_value=999),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str,
                     description='Switching device name', max_chars=40),
        PsseProperty(property_name='TYPE', rawx_key='type', class_type=int,
                     description='Switching device type', min_value=1, max_value=3),
        PsseProperty(property_name='STATUS', rawx_key='stat', class_type=int,
                     description='Switching device status', min_value=0, max_value=2),
        PsseProperty(property_name='NSTAT', rawx_key='nstat', class_type=int,
                     description='Switching device normal status', min_value=0, max_value=2),
        PsseProperty(property_name='X', rawx_key='xpu', class_type=float,
                     description='Switching device reactance', unit=Unit.get_pu()),
    )

    def __init__(self) -> None:
        """
        Build the common station-switching-device state.
        """
        RawObject.__init__(self, 'Substation switching device')

        self._ISUB: int = 0
        self._NI: int = 0
        self._NJ: int = 0
        self._NAME: str = ''
        self._TYPE: int = 1
        self._STATUS: int = 1
        self._NSTAT: int = 1
        self._X: float = 0.0001

    def parse(self, data, version, logger: Logger) -> None:
        """
        Parse one RAW record.

        :param data: Version-specific record payload.
        :param version: PSSE version.
        :param logger: Logger.
        :return: None
        """
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version: int) -> str:
        """
        Serialize one RAW record.

        :param version: PSSE version.
        :return: RAW line.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_circuit_id(self) -> str:
        """
        Return the circuit identifier used by the version-specific child.

        :return: Circuit identifier.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_circuit_id must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        """
        Return a unique identifier inside the RAW circuit.

        :return: Identifier string.
        """
        return f"{self.ISUB}_{self.NI}_{self.NJ}_{self.get_circuit_id()}"

    @property
    def ISUB(self) -> int:
        return self._ISUB

    @ISUB.setter
    def ISUB(self, value: int | str | None) -> None:
        self._ISUB = coerce_psse_int(value=value, current_value=self._ISUB)

    @property
    def NI(self) -> int:
        return self._NI

    @NI.setter
    def NI(self, value: int | str | None) -> None:
        self._NI = coerce_psse_int(value=value, current_value=self._NI)

    @property
    def NJ(self) -> int:
        return self._NJ

    @NJ.setter
    def NJ(self, value: int | str | None) -> None:
        self._NJ = coerce_psse_int(value=value, current_value=self._NJ)

    @property
    def NAME(self) -> str:
        return self._NAME

    @NAME.setter
    def NAME(self, value: str | int | float | None) -> None:
        self._NAME = coerce_psse_str(value=value, current_value=self._NAME)

    @property
    def TYPE(self) -> int:
        return self._TYPE

    @TYPE.setter
    def TYPE(self, value: int | str | None) -> None:
        self._TYPE = coerce_psse_int(value=value, current_value=self._TYPE)

    @property
    def STATUS(self) -> int:
        return self._STATUS

    @STATUS.setter
    def STATUS(self, value: int | str | None) -> None:
        self._STATUS = coerce_psse_int(value=value, current_value=self._STATUS)

    @property
    def NSTAT(self) -> int:
        return self._NSTAT

    @NSTAT.setter
    def NSTAT(self, value: int | str | None) -> None:
        self._NSTAT = coerce_psse_int(value=value, current_value=self._NSTAT)

    @property
    def X(self) -> float:
        return self._X

    @X.setter
    def X(self, value: float | int | str | None) -> None:
        self._X = coerce_psse_float(value=value, current_value=self._X)
