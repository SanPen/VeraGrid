# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.load import RawLoad


class RawLoadV29(RawLoad):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.I, self.ID, self.STATUS, self.AREA, self.ZONE, self.PL, self.QL,
         self.IP, self.IQ, self.YP, self.YQ, self.OWNER) = self.extend_or_curtail(data[0], 12)
        self.SCALE = 1.0

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "STATUS", "AREA", "ZONE",
                                     "PL", "QL", "IP", "IQ", "YP", "YQ", "OWNER"])
