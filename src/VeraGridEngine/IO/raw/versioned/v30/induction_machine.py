# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v29.induction_machine import RawInductionMachineV29


class RawInductionMachineV30(RawInductionMachineV29):
    """PSSE v30 typed object inheriting v29."""

    def parse(self, data, version, logger: Logger):
        super().parse(data=data, version=version, logger=logger)

    def get_raw_line(self, version):
        return (
                self.format_raw_line(["I", "ID", "STAT", "SCODE", "DCODE", "AREA", "ZONE",
                                      "OWNER", "TCODE", "BCODE", "MBASE", "RATEKV"]) + "\n" +
                self.format_raw_line(["PCODE", "PSET", "H", "A", "B", "D", "E", "RA",
                                      "XA", "XM", "R1", "X1", "R2", "X2", "X3", "E1",
                                      "SE1", "E2", "SE2", "IA1", "IA2"]) + "\n" +
                self.format_raw_line(["XAMULT"])
        )
