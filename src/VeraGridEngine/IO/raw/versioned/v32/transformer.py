# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v31.transformer import RawTransformerV31

HEADER_FIELDS = [
    "I", "J", "K", "CKT", "CW", "CZ", "CM", "MAG1", "MAG2", "NMETR", "NAME", "STAT",
    "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4",
]

WINDING1_FIELDS = [
    "WINDV1", "NOMV1", "ANG1", "RATA1", "RATB1", "RATC1",
    "COD1", "CONT1", "RMA1", "RMI1", "VMA1", "VMI1", "NTP1", "TAB1", "CR1", "CX1", "CNXA1",
]

WINDING2_FIELDS = [
    "WINDV2", "NOMV2", "ANG2", "RATA2", "RATB2", "RATC2",
    "COD2", "CONT2", "RMA2", "RMI2", "VMA2", "VMI2", "NTP2", "TAB2", "CR2", "CX2", "CNXA2",
]

WINDING3_FIELDS = [
    "WINDV3", "NOMV3", "ANG3", "RATA3", "RATB3", "RATC3",
    "COD3", "CONT3", "RMA3", "RMI3", "VMA3", "VMI3", "NTP3", "TAB3", "CR3", "CX3", "CNXA3",
]


class RawTransformerV32(RawTransformerV31):
    """PSSE v32 typed object inheriting v31."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.I, self.J, self.K, self.CKT, self.CW, self.CZ, self.CM, self.MAG1, self.MAG2, self.NMETR,
         self.NAME, self.STAT, self.O1, self.F1, self.O2, self.F2, self.O3, self.F3, self.O4, self.F4) = (
            self.extend_or_curtail(data[0], 20)
        )

        if len(data[1]) == 3:
            self.windings = 2
            self.R1_2, self.X1_2, self.SBASE1_2 = data[1]
        elif len(data[1]) == 2:
            self.windings = 2
            self.R1_2, self.X1_2 = data[1]
            self.SBASE1_2 = 100.0
        else:
            self.windings = 3
            (self.R1_2, self.X1_2, self.SBASE1_2, self.R2_3, self.X2_3, self.SBASE2_3, self.R3_1,
             self.X3_1, self.SBASE3_1, self.VMSTAR, self.ANSTAR) = self.extend_or_curtail(data[1], 11)

        (self.WINDV1, self.NOMV1, self.ANG1, self.RATA1, self.RATB1, self.RATC1, self.COD1,
         self.CONT1, self.RMA1, self.RMI1, self.VMA1, self.VMI1, self.NTP1, self.TAB1,
         self.CR1, self.CX1, self.CNXA1) = self.extend_or_curtail(data[2], 17)

        if len(data[3]) == 2:
            self.windings = 2
            self.WINDV2, self.NOMV2 = self.extend_or_curtail(data[3], 2)
        else:
            self.windings = 3
            (self.WINDV2, self.NOMV2, self.ANG2, self.RATA2, self.RATB2, self.RATC2, self.COD2, self.CONT2,
             self.RMA2, self.RMI2, self.VMA2, self.VMI2, self.NTP2, self.TAB2, self.CR2, self.CX2, self.CNXA2,
             self.WINDV3, self.NOMV3, self.ANG3, self.RATA3, self.RATB3, self.RATC3, self.COD3, self.CONT3,
             self.RMA3, self.RMI3, self.VMA3, self.VMI3, self.NTP3, self.TAB3, self.CR3, self.CX3, self.CNXA3) = (
                self.extend_or_curtail(data[3], 34)
            )

    def get_raw_line(self, version):
        l0 = self.format_raw_line(HEADER_FIELDS)
        if self.windings == 2:
            l1 = self.format_raw_line(["R1_2", "X1_2", "SBASE1_2"])
            l2 = self.format_raw_line(WINDING1_FIELDS)
            l3 = self.format_raw_line(["WINDV2", "NOMV2"])
            return l0 + "\n" + l1 + "\n" + l2 + "\n" + l3
        if self.windings == 3:
            l1 = self.format_raw_line(["R1_2", "X1_2", "SBASE1_2", "R2_3", "X2_3", "SBASE2_3",
                                       "R3_1", "X3_1", "SBASE3_1", "VMSTAR", "ANSTAR"])
            l2 = self.format_raw_line(WINDING1_FIELDS)
            l3 = self.format_raw_line(WINDING2_FIELDS + WINDING3_FIELDS)
            return l0 + "\n" + l1 + "\n" + l2 + "\n" + l3
        raise Exception("Wrong number of windings")
