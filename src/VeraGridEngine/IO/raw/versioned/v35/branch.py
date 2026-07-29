# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v34.branch import RawBranchV34


class RawBranchV35(RawBranchV34):
    """PSSE v35 typed object inheriting v34."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        record = data[0]

        if len(record) >= 26:
            values = self.extend_or_curtail(record, 34)
            (self.I, self.J, self.CKT, self.R, self.X, self.B, self.NAME,
             self.RATE1, self.RATE2, self.RATE3, self.RATE4, self.RATE5, self.RATE6,
             self.RATE7, self.RATE8, self.RATE9, self.RATE10, self.RATE11, self.RATE12,
             self.GI, self.BI, self.GJ, self.BJ, self.ST, self.MET, self.LEN, *owners) = values
            self.parse_ownership_fields(owners)
        else:
            # Some v35 sources emit the short branch record without the optional NAME field.
            # Detect that layout first so ownership pairs stay aligned at the tail.
            has_name_field = len(record) >= 25 and isinstance(record[6], str)

            if has_name_field:
                values = self.extend_or_curtail(record, 25)
                (self.I, self.J, self.CKT, self.R, self.X, self.B, self.NAME,
                 self.RATE1, self.RATE2, self.RATE3, self.GI, self.BI, self.GJ, self.BJ,
                 self.ST, self.MET, self.LEN, *owners) = values
            else:
                values = self.extend_or_curtail(record, 24)
                self.NAME = ""
                (self.I, self.J, self.CKT, self.R, self.X, self.B,
                 self.RATE1, self.RATE2, self.RATE3, self.GI, self.BI, self.GJ, self.BJ,
                 self.ST, self.MET, self.LEN, *owners) = values
            self.parse_ownership_fields(owners)

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "J", "CKT", "R", "X", "B", "NAME",
                                     "RATE1", "RATE2", "RATE3", "RATE4", "RATE5", "RATE6",
                                     "RATE7", "RATE8", "RATE9", "RATE10", "RATE11", "RATE12",
                                     "GI", "BI", "GJ", "BJ", "ST", "MET", "LEN",
                                     "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4"])
