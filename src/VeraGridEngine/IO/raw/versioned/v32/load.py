# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v31.load import RawLoadV31


class RawLoadV32(RawLoadV31):
    """PSSE v32 typed object inheriting v31."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.I, self.ID, self.STATUS, self.AREA, self.ZONE, self.PL, self.QL,
         self.IP, self.IQ, self.YP, self.YQ, self.OWNER, self.SCALE) = self.extend_or_curtail(data[0], 13)

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "STATUS", "AREA", "ZONE", "PL", "QL",
                                     "IP", "IQ", "YP", "YQ", "OWNER", "SCALE"])
