# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.raw.versioned.base.equipment_terminal import RawEquipmentTerminal
from VeraGridEngine.basic_structures import Logger


class RawEquipmentTerminalV34(RawEquipmentTerminal):
    """PSSE v34 equipment terminal."""

    def parse(self, data, version, logger: Logger) -> None:
        """
        Parse the v34 terminal record.

        :param data: RAW payload.
        :param version: PSSE version.
        :param logger: Logger.
        :return: None
        """
        self.version = version
        record = data[0]
        if len(record) == 4:
            self.IBUS, self.NI, self.TYPE, self.EQID = record
            self.JBUS = 0
            self.KBUS = 0
        elif len(record) == 5:
            self.IBUS, self.NI, self.TYPE, self.JBUS, self.EQID = record
            self.KBUS = 0
        elif len(record) == 6:
            self.IBUS, self.NI, self.TYPE, self.JBUS, self.KBUS, self.EQID = record
        elif len(record) == 3 and record[2] == 'S':
            self.IBUS, self.NI, self.TYPE = record
            self.EQID = '1'
            self.JBUS = 0
            self.KBUS = 0
        else:
            logger.add_warning('Equipment terminal line length could not be identified', value=','.join(map(str, record)))
            self.try_parse(values=record)

        self.TYPE = str(self.TYPE).replace("'", '').strip()
        self.EQID = str(self.EQID).replace("'", '').replace('"', '').strip()

    def get_raw_line(self, version: int) -> str:
        """
        Serialize the v34 terminal record.

        :param version: PSSE version.
        :return: RAW line.
        """
        if self.TYPE == 'B' or self.TYPE == '2':
            return self.format_raw_line(['IBUS', 'NI', 'TYPE', 'JBUS', 'EQID'])
        elif self.TYPE == '3':
            return self.format_raw_line(['IBUS', 'NI', 'TYPE', 'JBUS', 'KBUS', 'EQID'])
        elif self.TYPE == 'S':
            return self.format_raw_line(['IBUS', 'NI', 'TYPE'])
        else:
            return self.format_raw_line(['IBUS', 'NI', 'TYPE', 'EQID'])
