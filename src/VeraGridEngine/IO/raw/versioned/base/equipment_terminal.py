# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_int, coerce_psse_str
from VeraGridEngine.basic_structures import Logger


class RawEquipmentTerminal(RawObject):
    """
    Base storage for PSSE substation equipment terminal records.
    """

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='ISUB', rawx_key='isub', class_type=int,
                     description='Substation number', min_value=1, max_value=99999),
        PsseProperty(property_name='NI', rawx_key='inode', class_type=int,
                     description='Node number', min_value=0, max_value=999),
        PsseProperty(property_name='TYPE', rawx_key='type', class_type=str,
                     description='Equipment terminal record type', max_chars=1),
        PsseProperty(property_name='EQID', rawx_key='eqid', class_type=str,
                     description='Equipment identifier', max_chars=40),
        PsseProperty(property_name='IBUS', rawx_key='ibus', class_type=int,
                     description='Primary bus number', min_value=1, max_value=999997),
        PsseProperty(property_name='JBUS', rawx_key='jbus', class_type=int,
                     description='Secondary bus number', min_value=0, max_value=999997),
        PsseProperty(property_name='KBUS', rawx_key='kbus', class_type=int,
                     description='Tertiary bus number', min_value=0, max_value=999997),
    )

    def __init__(self) -> None:
        """
        Build the common terminal state.
        """
        RawObject.__init__(self, 'Equipment terminal')

        self._ISUB: int = 0
        self._NI: int = 0
        self._TYPE: str = ''
        self._EQID: str = ''
        self._IBUS: int = 0
        self._JBUS: int = 0
        self._KBUS: int = 0

    def parse(self, data, version, logger: Logger) -> None:
        """
        Parse one RAW record.

        :param data: RAW payload.
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

    def get_id(self) -> str:
        """
        Return a unique terminal identifier.

        :return: Identifier string.
        """
        return f"{self.ISUB}_{self.NI}_{self.TYPE}_{self.EQID}_{self.IBUS}_{self.JBUS}_{self.KBUS}"

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
    def TYPE(self) -> str:
        return self._TYPE

    @TYPE.setter
    def TYPE(self, value: str | int | float | None) -> None:
        self._TYPE = coerce_psse_str(value=value, current_value=self._TYPE)

    @property
    def EQID(self) -> str:
        return self._EQID

    @EQID.setter
    def EQID(self, value: str | int | float | None) -> None:
        self._EQID = coerce_psse_str(value=value, current_value=self._EQID)

    @property
    def IBUS(self) -> int:
        return self._IBUS

    @IBUS.setter
    def IBUS(self, value: int | str | None) -> None:
        self._IBUS = coerce_psse_int(value=value, current_value=self._IBUS)

    @property
    def JBUS(self) -> int:
        return self._JBUS

    @JBUS.setter
    def JBUS(self, value: int | str | None) -> None:
        self._JBUS = coerce_psse_int(value=value, current_value=self._JBUS)

    @property
    def KBUS(self) -> int:
        return self._KBUS

    @KBUS.setter
    def KBUS(self, value: int | str | None) -> None:
        self._KBUS = coerce_psse_int(value=value, current_value=self._KBUS)
