# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.transformer import RawTransformer

HEADER_FIELDS = [
    "I", "J", "K", "CKT", "CW", "CZ", "CM", "MAG1", "MAG2", "NMETR", "NAME", "STAT",
    "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4",
]

WINDING1_FIELDS = [
    "WINDV1", "NOMV1", "ANG1", "RATA1", "RATB1", "RATC1",
    "COD1", "CONT1", "RMA1", "RMI1", "VMA1", "VMI1", "NTP1", "TAB1", "CR1", "CX1",
]

WINDING2_FIELDS_3W = ["WINDV2", "NOMV2", "ANG2", "RATA2", "RATB2", "RATC2"]
WINDING3_FIELDS_3W = ["WINDV3", "NOMV3", "ANG3", "RATA3", "RATB3", "RATC3"]


class RawTransformerV29(RawTransformer):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.I, self.J, self.K, self.CKT, self.CW, self.CZ, self.CM, self.MAG1, self.MAG2, self.NMETR,
         self.NAME, self.STAT, self.O1, self.F1, self.O2, self.F2, self.O3, self.F3, self.O4, self.F4) = (
            self.extend_or_curtail(data[0], 20)
        )

        if len(data[1]) == 3:
            self.windings = 2
            self.R1_2, self.X1_2, self.SBASE1_2 = data[1]
            (self.WINDV1, self.NOMV1, self.ANG1, self.RATA1, self.RATB1, self.RATC1, self.COD1,
             self.CONT1, self.RMA1, self.RMI1, self.VMA1, self.VMI1, self.NTP1, self.TAB1,
             self.CR1, self.CX1) = self.extend_or_curtail(data[2], 16)
            self.WINDV2, self.NOMV2 = self.extend_or_curtail(data[3], 2)
        else:
            self.windings = 3
            (self.R1_2, self.X1_2, self.SBASE1_2, self.R2_3, self.X2_3, self.SBASE2_3, self.R3_1,
             self.X3_1, self.SBASE3_1, self.VMSTAR, self.ANSTAR) = self.extend_or_curtail(data[1], 11)
            (self.WINDV1, self.NOMV1, self.ANG1, self.RATA1, self.RATB1, self.RATC1, self.COD1,
             self.CONT1, self.RMA1, self.RMI1, self.VMA1, self.VMI1, self.NTP1, self.TAB1,
             self.CR1, self.CX1) = self.extend_or_curtail(data[2], 16)
            (self.WINDV2, self.NOMV2, self.ANG2, self.RATA2, self.RATB2, self.RATC2) = self.extend_or_curtail(data[3], 6)
            (self.WINDV3, self.NOMV3, self.ANG3, self.RATA3, self.RATB3, self.RATC3) = self.extend_or_curtail(data[4], 6)

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
            l3 = self.format_raw_line(WINDING2_FIELDS_3W)
            l4 = self.format_raw_line(WINDING3_FIELDS_3W)
            return l0 + "\n" + l1 + "\n" + l2 + "\n" + l3 + "\n" + l4
        raise Exception("Wrong number of windings")
