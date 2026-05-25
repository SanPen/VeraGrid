# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_property import PsseProperty
from VeraGridEngine.IO.raw.versioned.v34.substation_switching_device import RawSubstationSwitchingDeviceV34
from VeraGridEngine.basic_structures import Logger


class RawSubstationSwitchingDeviceV35(RawSubstationSwitchingDeviceV34):
    """PSSE v35 substation switching device."""

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='CKT', rawx_key='swdid', class_type=str,
                     description='Switching device identifier', max_chars=2),
    )

    def __init__(self) -> None:
        """
        Build the v35 state.
        """
        RawSubstationSwitchingDeviceV34.__init__(self)
        self.CKT: str = '1'

    def parse(self, data, version, logger: Logger) -> None:
        """
        Parse the v35 RAW record.

        :param data: RAW payload.
        :param version: PSSE version.
        :param logger: Logger.
        :return: None
        """
        self.version = version
        record = self.extend_or_curtail(data[0], 11)
        (self.NI, self.NJ, self.CKT, self.NAME, self.TYPE, self.STATUS,
         self.NSTAT, self.X, self.RATE1, self.RATE2, self.RATE3) = record
        self.NAME = str(self.NAME).replace("'", '').strip()
        self.CKT = str(self.CKT).replace("'", '').strip()
        self.CKTID = self.CKT

    def get_raw_line(self, version: int) -> str:
        """
        Serialize the v35 RAW record.

        :param version: PSSE version.
        :return: RAW line.
        """
        return self.format_raw_line([
            'NI', 'NJ', 'CKT', 'NAME', 'TYPE', 'STATUS', 'NSTAT', 'X', 'RATE1', 'RATE2', 'RATE3'
        ])

    def get_circuit_id(self) -> str:
        """
        Return the v35 circuit identifier.

        :return: Circuit identifier.
        """
        return self.CKT
