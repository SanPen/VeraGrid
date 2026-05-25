# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.raw.versioned.base.gne_device import RawGneDevice


class RawGneDeviceV29(RawGneDevice):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger):
        self.version = version

        header = data[0]
        if len(header) >= 8:
            self.NAME, self.MODEL, self.NTERM, self.BUS1, self.BUS2, self.NREAL, self.NINTG, self.NCHAR = (
                self.extend_or_curtail(header, 8)
            )
        elif len(header) >= 7:
            self.NAME, self.MODEL, self.NTERM, self.BUS1, self.NREAL, self.NINTG, self.NCHAR = (
                self.extend_or_curtail(header, 7)
            )
            self.BUS2 = 0
        else:
            logger.add_warning('Incorrect GNE header length', str(len(header)))
            self.try_parse(values=header)

        self.STATUS, self.OWNER, self.NMETR = self.extend_or_curtail(data[1], 3)
        self.NMET = self.NMETR

        for index, value in enumerate(self.extend_or_curtail(data[2], 10), start=1):
            self.set_real_value(index, value)
        for index, value in enumerate(self.extend_or_curtail(data[3], 10), start=1):
            self.set_intg_value(index, value)
        for index, value in enumerate(self.extend_or_curtail(data[4], 10), start=1):
            self.set_char_value(index, str(value))

    def get_raw_line(self, version):
        header_fields = ["NAME", "MODEL", "NTERM", "BUS1"]
        if self.NTERM >= 2:
            header_fields.append("BUS2")
        header_fields.extend(["NREAL", "NINTG", "NCHAR"])

        real_fields = [f"REAL{i}" for i in range(1, min(10, max(self.NREAL, 0)) + 1)]
        intg_fields = [f"INTG{i}" for i in range(1, min(10, max(self.NINTG, 0)) + 1)]
        char_fields = [f"CHAR{i}" for i in range(1, min(10, max(self.NCHAR, 0)) + 1)]

        return (
            self.format_raw_line(header_fields) + "\n" +
            self.format_raw_line(["STATUS", "OWNER", "NMETR"]) + "\n" +
            self.format_raw_line(real_fields) + "\n" +
            self.format_raw_line(intg_fields) + "\n" +
            self.format_raw_line(char_fields)
        )
