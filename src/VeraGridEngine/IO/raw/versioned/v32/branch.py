# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v31.branch import RawBranchV31


class RawBranchV32(RawBranchV31):
    """PSSE v32 typed object inheriting v31."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.I, self.J, self.CKT, self.R, self.X, self.B, self.RATEA, self.RATEB, self.RATEC,
         self.GI, self.BI, self.GJ, self.BJ, self.ST, self.MET, self.LEN, *owners) = data[0]
        self.parse_ownership_fields(owners)

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "J", "CKT", "R", "X", "B",
                                     "RATEA", "RATEB", "RATEC", "GI", "BI", "GJ", "BJ",
                                     "ST", "MET", "LEN", "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4"])
