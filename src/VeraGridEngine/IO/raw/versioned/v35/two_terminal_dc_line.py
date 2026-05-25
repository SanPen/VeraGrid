# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v34.two_terminal_dc_line import RawTwoTerminalDCLineV34


class RawTwoTerminalDCLineV35(RawTwoTerminalDCLineV34):
    """PSSE v35 typed object inheriting v34."""

    def parse(self, data, version, logger: Logger):
        super().parse(data=data, version=version, logger=logger)

    def get_raw_line(self, version):
        l0 = self.format_raw_line(["NAME", "MDC", "RDC", "SETVL", "VSCHD", "VCMOD", "RCOMP",
                                   "DELTI", "METER", "DCVMIN", "CCCITMX", "CCCACC"])
        l1 = self.format_raw_line(["IPR", "NBR", "ANMXR", "ANMNR", "RCR", "XCR", "EBASR",
                                   "TRR", "TAPR", "TMXR", "TMNR", "STPR", "ICR", "NDR",
                                   "IFR", "ITR", "IDR", "XCAPR"])
        l2 = self.format_raw_line(["IPI", "NBI", "ANMXI", "ANMNI", "RCI", "XCI", "EBASI",
                                   "TRI", "TAPI", "TMXI", "TMNI", "STPI", "ICI", "NDI",
                                   "IFI", "ITI", "IDI", "XCAPI"])
        return l0 + '\n' + l1 + '\n' + l2
