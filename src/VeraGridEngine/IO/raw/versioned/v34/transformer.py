# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v33.transformer import RawTransformerV33

HEADER_FIELDS_2W = [
    "I", "J", "K", "CKT", "CW", "CZ", "CM", "MAG1", "MAG2", "NMETR", "NAME", "STAT",
    "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4", "VECGRP",
]

HEADER_FIELDS_3W = [
    "I", "J", "K", "CKT", "CW", "CZ", "CM", "MAG1", "MAG2", "NMETR", "NAME", "STAT",
    "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4", "VECGRP", "ZCOD",
]

WINDING1_FIELDS = [
    "WINDV1", "NOMV1", "ANG1",
    "RATE1_1", "RATE1_2", "RATE1_3", "RATE1_4", "RATE1_5", "RATE1_6",
    "RATE1_7", "RATE1_8", "RATE1_9", "RATE1_10", "RATE1_11", "RATE1_12",
    "COD1", "CONT1", "RMA1", "RMI1", "VMA1", "VMI1", "NTP1", "TAB1", "CR1", "CX1", "CNXA1",
]

WINDING2_FIELDS = [
    "WINDV2", "NOMV2", "ANG2",
    "RATE2_1", "RATE2_2", "RATE2_3", "RATE2_4", "RATE2_5", "RATE2_6",
    "RATE2_7", "RATE2_8", "RATE2_9", "RATE2_10", "RATE2_11", "RATE2_12",
    "COD2", "CONT2", "RMA2", "RMI2", "VMA2", "VMI2", "NTP2", "TAB2", "CR2", "CX2", "CNXA2",
]

WINDING3_FIELDS = [
    "WINDV3", "NOMV3", "ANG3",
    "RATE3_1", "RATE3_2", "RATE3_3", "RATE3_4", "RATE3_5", "RATE3_6",
    "RATE3_7", "RATE3_8", "RATE3_9", "RATE3_10", "RATE3_11", "RATE3_12",
    "COD3", "CONT3", "RMA3", "RMI3", "VMA3", "VMI3", "NTP3", "TAB3", "CR3", "CX3", "CNXA3",
]


class RawTransformerV34(RawTransformerV33):
    """PSSE v34 typed object inheriting v33."""

    def parse(self, data, version, logger: Logger):
        self.version = version

        if len(data) == 4:
            self.windings = 2
            header_values = self.extend_or_curtail(data[0], 22)
            (self.I, self.J, self.K, self.CKT, self.CW, self.CZ, self.CM, self.MAG1, self.MAG2, self.NMETR,
             self.NAME, self.STAT, self.O1, self.F1, self.O2, self.F2, self.O3, self.F3, self.O4, self.F4,
             self.VECGRP, self.ZCOD) = header_values
            self.R1_2, self.X1_2, self.SBASE1_2 = self.extend_or_curtail(data[1], 3)
            if len(data[2]) >= 27:
                (self.WINDV1, self.NOMV1, self.ANG1,
                 self.RATE1_1, self.RATE1_2, self.RATE1_3, self.RATE1_4, self.RATE1_5, self.RATE1_6,
                 self.RATE1_7, self.RATE1_8, self.RATE1_9, self.RATE1_10, self.RATE1_11, self.RATE1_12,
                 self.COD1, self.CONT1, self.NODE1, self.RMA1, self.RMI1, self.VMA1, self.VMI1,
                 self.NTP1, self.TAB1, self.CR1, self.CX1, self.CNXA1) = self.extend_or_curtail(data[2], 27)
            else:
                self.NODE1 = 0
                (self.WINDV1, self.NOMV1, self.ANG1,
                 self.RATE1_1, self.RATE1_2, self.RATE1_3, self.RATE1_4, self.RATE1_5, self.RATE1_6,
                 self.RATE1_7, self.RATE1_8, self.RATE1_9, self.RATE1_10, self.RATE1_11, self.RATE1_12,
                 self.COD1, self.CONT1, self.RMA1, self.RMI1, self.VMA1, self.VMI1,
                 self.NTP1, self.TAB1, self.CR1, self.CX1, self.CNXA1) = self.extend_or_curtail(data[2], 26)
            self.WINDV2, self.NOMV2 = self.extend_or_curtail(data[3], 2)
        else:
            self.windings = 3
            (self.I, self.J, self.K, self.CKT, self.CW, self.CZ, self.CM, self.MAG1, self.MAG2, self.NMETR,
             self.NAME, self.STAT, self.O1, self.F1, self.O2, self.F2, self.O3, self.F3, self.O4, self.F4,
             self.VECGRP, self.ZCOD) = self.extend_or_curtail(data[0], 22)
            (self.R1_2, self.X1_2, self.SBASE1_2, self.R2_3, self.X2_3, self.SBASE2_3, self.R3_1, self.X3_1,
             self.SBASE3_1, self.VMSTAR, self.ANSTAR) = self.extend_or_curtail(data[1], 11)
            self._parse_winding_record_without_node(data[2], 1)
            self._parse_winding_record_without_node(data[3], 2)
            self._parse_winding_record_without_node(data[4], 3)

    def _parse_winding_record_without_node(self, record, index: int):
        if len(record) >= 27:
            values = self.extend_or_curtail(record, 27)
            for rate_number in range(12):
                self.set_numbered_winding_rating(index, rate_number + 1, values[3 + rate_number])
            self.set_winding_record(index, values[0], values[1], values[2], values[15], values[16], values[17],
                                    values[18], values[19], values[20], values[21], values[22], values[23],
                                    values[24], values[25], values[26])
            return

        values = self.extend_or_curtail(record, 26)
        for rate_number in range(12):
            self.set_numbered_winding_rating(index, rate_number + 1, values[3 + rate_number])
        self.set_winding_record(index, values[0], values[1], values[2], values[15], values[16], 0,
                                values[17], values[18], values[19], values[20], values[21], values[22],
                                values[23], values[24], values[25])

    def get_raw_line(self, version):
        if self.windings == 2:
            l0 = self.format_raw_line(HEADER_FIELDS_2W)
            l1 = self.format_raw_line(["R1_2", "X1_2", "SBASE1_2"])
            l2 = self.format_raw_line(WINDING1_FIELDS)
            l3 = self.format_raw_line(["WINDV2", "NOMV2"])
            return l0 + "\n" + l1 + "\n" + l2 + "\n" + l3
        if self.windings == 3:
            l0 = self.format_raw_line(HEADER_FIELDS_3W)
            l1 = self.format_raw_line(["R1_2", "X1_2", "SBASE1_2", "R2_3", "X2_3", "SBASE2_3",
                                       "R3_1", "X3_1", "SBASE3_1", "VMSTAR", "ANSTAR"])
            l2 = self.format_raw_line(WINDING1_FIELDS)
            l3 = self.format_raw_line(WINDING2_FIELDS)
            l4 = self.format_raw_line(WINDING3_FIELDS)
            return l0 + "\n" + l1 + "\n" + l2 + "\n" + l3 + "\n" + l4
        raise Exception("Wrong number of windings")
