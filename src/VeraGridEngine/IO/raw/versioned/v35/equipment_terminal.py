# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.raw.versioned.v34.equipment_terminal import RawEquipmentTerminalV34
from VeraGridEngine.basic_structures import Logger


class RawEquipmentTerminalV35(RawEquipmentTerminalV34):
    """PSSE v35 equipment terminal."""

    def parse(self, data, version, logger: Logger) -> None:
        """
        Parse the v35 terminal record.

        :param data: RAW payload.
        :param version: PSSE version.
        :param logger: Logger.
        :return: None
        """
        RawEquipmentTerminalV34.parse(self, data, version, logger)
        if self.TYPE == 'S' and self.EQID == '':
            self.EQID = '1'
