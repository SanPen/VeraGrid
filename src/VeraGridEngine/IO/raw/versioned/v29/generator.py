# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.generator import RawGenerator


class RawGeneratorV29(RawGenerator):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        var = [self.O1, self.F1, self.O2, self.F2, self.O3, self.F3, self.O4, self.F4]
        (self.I, self.ID, self.PG, self.QG, self.QT, self.QB, self.VS, self.IREG, self.MBASE,
         self.ZR, self.ZX, self.RT, self.XT, self.GTAP, self.STAT, self.RMPCT, self.PT, self.PB, *var) = data[0]

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "PG", "QG", "QT", "QB", "VS", "IREG",
                                     "MBASE", "ZR", "ZX", "RT", "XT", "GTAP", "STAT",
                                     "RMPCT", "PT", "PB", "O1", "F1", "O2", "F2", "O3", "F3", "O4", "F4"])
