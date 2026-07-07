# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v33.induction_machine import RawInductionMachineV33


class RawInductionMachineV34(RawInductionMachineV33):
    """PSSE v34 typed object inheriting v33."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        if len(data) == 1:
            (self.I, self.ID, self.STAT, self.SCODE, self.DCODE, self.AREA, self.ZONE, self.OWNER,
             self.TCODE, self.BCODE, self.MBASE, self.RATEKV,
             self.PCODE, self.PSET, self.H, self.A, self.B, self.D, self.E) = data[0]
        elif len(data) == 3:
            (self.I, self.ID, self.STAT, self.SCODE, self.DCODE, self.AREA, self.ZONE, self.OWNER,
             self.TCODE, self.BCODE, self.MBASE, self.RATEKV) = data[0]

            (self.PCODE, self.PSET, self.H, self.A, self.B, self.D, self.E,
             self.RA, self.XA, self.XM, self.R1,
             self.X1, self.R2, self.X2, self.X3,
             self.E1, self.SE1, self.E2, self.SE2,
             self.IA1, self.IA2) = data[1]

            self.XAMULT = data[2]
        else:
            logger.add_warning('Incorrect number of lines for Induction machine', str(len(data)))
