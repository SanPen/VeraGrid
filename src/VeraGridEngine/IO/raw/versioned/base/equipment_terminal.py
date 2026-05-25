# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.IO.raw.psse_property import PsseProperty
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

        self.ISUB: int = 0
        self.NI: int = 0
        self.TYPE: str = ''
        self.EQID: str = ''
        self.IBUS: int = 0
        self.JBUS: int = 0
        self.KBUS: int = 0

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
