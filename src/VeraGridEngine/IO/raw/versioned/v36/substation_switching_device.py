# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_property import PsseProperty
from VeraGridEngine.IO.raw.versioned.v35.substation_switching_device import RawSubstationSwitchingDeviceV35
from VeraGridEngine.basic_structures import Logger


class RawSubstationSwitchingDeviceV36(RawSubstationSwitchingDeviceV35):
    """PSSE v36 substation switching device."""

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='RSETNAM', rawx_key='rsetnam', class_type=str,
                     description='Rating set table name', max_chars=40),
    )

    def __init__(self) -> None:
        """
        Build the v36 state.
        """
        RawSubstationSwitchingDeviceV35.__init__(self)
        self.RSETNAM: str = ''

    def parse(self, data, version, logger: Logger) -> None:
        """
        Parse the v36 RAW record.

        :param data: RAW payload.
        :param version: PSSE version.
        :param logger: Logger.
        :return: None
        """
        self.version = version
        record = self.extend_or_curtail(data[0], 9)
        (self.NI, self.NJ, self.CKT, self.NAME, self.TYPE, self.STATUS,
         self.NSTAT, self.X, self.RSETNAM) = record
        self.NAME = str(self.NAME).replace("'", '').strip()
        self.CKT = str(self.CKT).replace("'", '').strip()
        self.CKTID = self.CKT
        self.RSETNAM = str(self.RSETNAM).replace("'", '').strip()
        self.RATE1 = 0.0
        self.RATE2 = 0.0
        self.RATE3 = 0.0

    def get_raw_line(self, version: int) -> str:
        """
        Serialize the v36 RAW record.

        :param version: PSSE version.
        :return: RAW line.
        """
        return self.format_raw_line([
            'NI', 'NJ', 'CKT', 'NAME', 'TYPE', 'STATUS', 'NSTAT', 'X', 'RSETNAM'
        ])
