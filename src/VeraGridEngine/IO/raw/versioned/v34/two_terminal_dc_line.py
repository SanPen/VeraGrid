# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v33.two_terminal_dc_line import RawTwoTerminalDCLineV33


class RawTwoTerminalDCLineV34(RawTwoTerminalDCLineV33):
    """PSSE v34 typed object inheriting v33."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.NAME, self.MDC, self.RDC, self.SETVL, self.VSCHD, self.VCMOD, self.RCOMP, self.DELTI, self.METER,
         self.DCVMIN, self.CCCITMX, self.CCCACC) = data[0]

        if len(data[1]) == 18:
            (self.IPR, self.NBR, self.ANMXR, self.ANMNR, self.RCR, self.XCR, self.EBASR, self.TRR, self.TAPR,
             self.TMXR, self.TMNR, self.STPR, self.ICR, self.NDR, self.IFR, self.ITR, self.IDR, self.XCAPR) = data[1]
        elif len(data[1]) == 17:
            (self.IPR, self.NBR, self.ANMXR, self.ANMNR, self.RCR, self.XCR, self.EBASR, self.TRR, self.TAPR,
             self.TMXR, self.TMNR, self.STPR, self.ICR, self.IFR, self.ITR, self.IDR, self.XCAPR) = data[1]
        else:
            self.try_parse2(data[1], prop_names=[
                "IPR", "NBR", "ANMXR", "ANMNR", "RCR", "XCR", "EBASR", "TRR", "TAPR",
                "TMXR", "TMNR", "STPR", "ICR", "NDR", "IFR", "ITR", "IDR", "XCAPR"
            ])

        if len(data[2]) == 18:
            (self.IPI, self.NBI, self.ANMXI, self.ANMNI, self.RCI, self.XCI, self.EBASI, self.TRI, self.TAPI,
             self.TMXI, self.TMNI, self.STPI, self.ICI, self.NDI, self.IFI, self.ITI, self.IDI, self.XCAPI) = data[2]
        elif len(data[2]) == 17:
            (self.IPI, self.NBI, self.ANMXI, self.ANMNI, self.RCI, self.XCI, self.EBASI, self.TRI, self.TAPI,
             self.TMXI, self.TMNI, self.STPI, self.ICI, self.IFI, self.ITI, self.IDI, self.XCAPI) = data[2]
        else:
            self.try_parse2(data[2], prop_names=[
                "IPI", "NBI", "ANMXI", "ANMNI", "RCI", "XCI", "EBASI", "TRI", "TAPI",
                "TMXI", "TMNI", "STPI", "ICI", "NDI", "IFI", "ITI", "IDI", "XCAPI"
            ])
