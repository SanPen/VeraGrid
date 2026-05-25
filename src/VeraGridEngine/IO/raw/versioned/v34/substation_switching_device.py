# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_property import PsseProperty
from VeraGridEngine.IO.raw.versioned.base.substation_switching_device import RawSubstationSwitchingDevice
from VeraGridEngine.basic_structures import Logger


class RawSubstationSwitchingDeviceV34(RawSubstationSwitchingDevice):
    """PSSE v34 substation switching device."""

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='CKTID', rawx_key='swdid', class_type=str,
                     description='Switching device identifier', max_chars=2),
        PsseProperty(property_name='RATE1', rawx_key='rate1', class_type=float,
                     description='Rating set 1'),
        PsseProperty(property_name='RATE2', rawx_key='rate2', class_type=float,
                     description='Rating set 2'),
        PsseProperty(property_name='RATE3', rawx_key='rate3', class_type=float,
                     description='Rating set 3'),
    )

    def __init__(self) -> None:
        """
        Build the v34 state.
        """
        RawSubstationSwitchingDevice.__init__(self)
        self.CKTID: str = '1'
        self.RATE1: float = 0.0
        self.RATE2: float = 0.0
        self.RATE3: float = 0.0

    def parse(self, data, version, logger: Logger) -> None:
        """
        Parse the v34 RAW record.

        :param data: RAW payload.
        :param version: PSSE version.
        :param logger: Logger.
        :return: None
        """
        self.version = version
        record = self.extend_or_curtail(data[0], 11)
        (self.NI, self.NJ, self.CKTID, self.NAME, self.TYPE, self.STATUS,
         self.NSTAT, self.X, self.RATE1, self.RATE2, self.RATE3) = record
        self.NAME = str(self.NAME).replace("'", '').strip()
        self.CKTID = str(self.CKTID).replace("'", '').strip()

    def get_raw_line(self, version: int) -> str:
        """
        Serialize the v34 RAW record.

        :param version: PSSE version.
        :return: RAW line.
        """
        return self.format_raw_line([
            'NI', 'NJ', 'CKTID', 'NAME', 'TYPE', 'STATUS', 'NSTAT', 'X', 'RATE1', 'RATE2', 'RATE3'
        ])

    def get_circuit_id(self) -> str:
        """
        Return the v34 circuit identifier.

        :return: Circuit identifier.
        """
        return self.CKTID
