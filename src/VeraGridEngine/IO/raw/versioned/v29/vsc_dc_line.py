# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.vsc_dc_line import RawVscDCLine


class RawVscDCLineV29(RawVscDCLine):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        var = [self.O1, self.F1, self.O2, self.F2, self.O3, self.F3, self.O4, self.F4]
        self.NAME, self.MDC, self.RDC, *var = data[0]
        (self.IBUS1, self.TYPE1, self.MODE1, self.DCSET1, self.ACSET1, self.ALOSS1, self.BLOSS1, self.MINLOSS1,
         self.SMAX1, self.IMAX1, self.PWF1, self.MAXQ1, self.MINQ1, self.REMOT1, self.RMPCT1) = data[1]
        (self.IBUS2, self.TYPE2, self.MODE2, self.DCSET2, self.ACSET2, self.ALOSS2, self.BLOSS2, self.MINLOSS2,
         self.SMAX2, self.IMAX2, self.PWF2, self.MAXQ2, self.MINQ2, self.REMOT2, self.RMPCT2) = data[2]

    def get_raw_line(self, version):
        l0 = self.format_raw_line(["NAME", "MDC", "RDC", "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4"])
        l1 = self.format_raw_line(["IBUS1", "TYPE1", "MODE1", "DCSET1", "ACSET1",
                                   "ALOSS1", "BLOSS1", "MINLOSS1", "SMAX1", "IMAX1",
                                   "PWF1", "MAXQ1", "MINQ1", "REMOT1", "RMPCT1"])
        l2 = self.format_raw_line(["IBUS2", "TYPE2", "MODE2", "DCSET2", "ACSET2",
                                   "ALOSS2", "BLOSS2", "MINLOSS2", "SMAX2", "IMAX2",
                                   "PWF2", "MAXQ2", "MINQ2", "REMOT2", "RMPCT2"])
        return l0 + '\n' + l1 + '\n' + l2
