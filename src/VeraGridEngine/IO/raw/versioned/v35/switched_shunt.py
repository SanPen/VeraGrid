# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v34.switched_shunt import RawSwitchedShuntV34


class RawSwitchedShuntV35(RawSwitchedShuntV34):
    """PSSE v35 typed object inheriting v34."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        field_values = data[0]
        (self.I, self.ID, self.MODSW, self.ADJM, self.STAT, self.VSWHI, self.VSWLO,
         self.SWREG, self.NREG, self.RMPCT, self.RMIDNT, self.BINIT, *dynamic_values) = field_values

        dynamic_values = self.extend_or_curtail(dynamic_values, 24)
        (self.S1, self.N1, self.B1, self.S2, self.N2, self.B2, self.S3, self.N3, self.B3,
         self.S4, self.N4, self.B4, self.S5, self.N5, self.B5, self.S6, self.N6, self.B6,
         self.S7, self.N7, self.B7, self.S8, self.N8, self.B8) = dynamic_values

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "MODSW", "ADJM", "STAT", "VSWHI", "VSWLO",
                                     "SWREG", "NREG", "RMPCT", "RMIDNT", "BINIT",
                                     "S1", "N1", "B1", "S2", "N2", "B2", "S3", "N3", "B3", "S4", "N4", "B4",
                                     "S5", "N5", "B5", "S6", "N6", "B6", "S7", "N7", "B7", "S8", "N8", "B8"])
