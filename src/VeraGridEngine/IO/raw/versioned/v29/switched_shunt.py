# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.switched_shunt import RawSwitchedShunt


class RawSwitchedShuntV29(RawSwitchedShunt):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        field_values = data[0]
        (self.I, self.MODSW, self.VSWHI, self.VSWLO,
         self.SWREM, self.RMPCT, self.RMIDNT, self.BINIT, *dynamic_values) = field_values

        dynamic_values = self.extend_or_curtail(dynamic_values, 16)
        (self.N1, self.B1, self.N2, self.B2, self.N3, self.B3, self.N4, self.B4,
         self.N5, self.B5, self.N6, self.B6, self.N7, self.B7, self.N8, self.B8) = dynamic_values

        for i in range(1, 9):
            if self.get_block_steps(i) != 0:
                self.set_block_status(i, 1)

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "MODSW", "VSWHI", "VSWLO",
                                     "SWREM", "RMPCT", "RMIDNT", "BINIT",
                                     "N1", "B1", "N2", "B2", "N3", "B3", "N4", "B4",
                                     "N5", "B5", "N6", "B6", "N7", "B7", "N8", "B8"])
