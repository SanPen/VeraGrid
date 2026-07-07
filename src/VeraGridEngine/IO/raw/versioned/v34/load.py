# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v33.load import RawLoadV33


class RawLoadV34(RawLoadV33):
    """PSSE v34 typed object inheriting v33."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.I, self.ID, self.STATUS, self.AREA, self.ZONE, self.PL, self.QL,
         self.IP, self.IQ, self.YP, self.YQ, self.OWNER, self.SCALE,
         self.INTRPT, self.DGENP, self.DGENQ, self.DGENM) = self.extend_or_curtail(data[0], 17)

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "STATUS", "AREA", "ZONE", "PL", "QL",
                                     "IP", "IQ", "YP", "YQ", "OWNER", "SCALE", "INTRPT",
                                     "DGENP", "DGENQ", "DGENM"])
