# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v29.two_terminal_dc_line import RawTwoTerminalDCLineV29


class RawTwoTerminalDCLineV30(RawTwoTerminalDCLineV29):
    """PSSE v30 typed object inheriting v29."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.NAME, self.MDC, self.RDC, self.SETVL, self.VSCHD, self.VCMOD, self.RCOMP, self.DELTI, self.METER,
         self.DCVMIN, self.CCCITMX, self.CCCACC) = data[0]
        (self.IPR, self.NBR, self.ANMXR, self.ANMNR, self.RCR, self.XCR, self.EBASR, self.TRR, self.TAPR,
         self.TMXR, self.TMNR, self.STPR, self.ICR, self.IFR, self.ITR, self.IDR, self.XCAPR) = data[1]
        (self.IPI, self.NBI, self.ANMXI, self.ANMNI, self.RCI, self.XCI, self.EBASI, self.TRI, self.TAPI,
         self.TMXI, self.TMNI, self.STPI, self.ICI, self.IFI, self.ITI, self.IDI, self.XCAPI) = data[2]

    def get_raw_line(self, version):
        l0 = self.format_raw_line(["NAME", "MDC", "RDC", "SETVL", "VSCHD", "VCMOD", "RCOMP",
                                   "DELTI", "METER", "DCVMIN", "CCCITMX", "CCCACC"])
        l1 = self.format_raw_line(["IPR", "NBR", "ANMXR", "ANMNR", "RCR", "XCR", "EBASR",
                                   "TRR", "TAPR", "TMXR", "TMNR", "STPR", "ICR", "IFR",
                                   "ITR", "IDR", "XCAPR"])
        l2 = self.format_raw_line(["IPI", "NBI", "ANMXI", "ANMNI", "RCI", "XCI", "EBASI",
                                   "TRI", "TAPI", "TMXI", "TMNI", "STPI", "ICI", "IFI",
                                   "ITI", "IDI", "XCAPI"])
        return l0 + '\n' + l1 + '\n' + l2
