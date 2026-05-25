# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.raw.versioned.v34.gne_device import RawGneDeviceV34


class RawGneDeviceV35(RawGneDeviceV34):
    """PSSE v35 typed object inheriting v34."""

    def parse(self, data, version, logger):
        super().parse(data=data, version=version, logger=logger)
        self.NMET = self.NMETR

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
            self.format_raw_line(["STATUS", "OWNER", "NMET"]) + "\n" +
            self.format_raw_line(real_fields) + "\n" +
            self.format_raw_line(intg_fields) + "\n" +
            self.format_raw_line(char_fields)
        )
