# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v33.branch import RawBranchV33


class RawBranchV34(RawBranchV33):
    """PSSE v34 typed object inheriting v33."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        var = [self.O1, self.F1, self.O2, self.F2, self.O3, self.F3, self.O4, self.F4]
        (self.I, self.J, self.CKT, self.R, self.X, self.B, self.NAME,
         self.RATE1, self.RATE2, self.RATE3, self.RATE4, self.RATE5, self.RATE6,
         self.RATE7, self.RATE8, self.RATE9, self.RATE10, self.RATE11, self.RATE12,
         self.GI, self.BI, self.GJ, self.BJ, self.ST, self.MET, self.LEN, *var) = data[0]

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "J", "CKT", "R", "X", "B", "NAME",
                                     "RATE1", "RATE2", "RATE3", "RATE4", "RATE5", "RATE6",
                                     "RATE7", "RATE8", "RATE9", "RATE10", "RATE11", "RATE12",
                                     "GI", "BI", "GJ", "BJ", "ST", "MET", "LEN",
                                     "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4"])
