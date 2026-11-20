# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.induction_machine import RawInductionMachine


class RawInductionMachineV29(RawInductionMachine):
    """PSSE v29 typed object."""
    __slots__ = ()

    def parse(self, data, version, logger: Logger):
        self.version = version
        if len(data) == 1:
            if len(data[0]) == 19:
                (self.I, self.ID, self.STAT, self.SCODE, self.DCODE, self.AREA, self.ZONE, self.OWNER,
                 self.TCODE, self.BCODE, self.MBASE, self.RATEKV,
                 self.PCODE, self.PSET, self.H, self.A, self.B, self.D, self.E) = data[0]
            else:
                (self.I, self.ID, self.STAT, self.SCODE, self.DCODE, self.AREA, self.ZONE, self.OWNER,
                 self.TCODE, self.BCODE, self.MBASE, self.RATEKV, self.PCODE, self.PSET, self.H,
                 self.A, self.B, self.D, self.E, self.RA, self.XA, self.XM, self.R1, self.X1,
                 self.R2, self.X2, self.X3, self.E1, self.SE1, self.E2, self.SE2, self.IA1,
                 self.IA2, self.XAMULT) = self.extend_or_curtail(data[0], 34)
        elif len(data) == 3:
            (self.I, self.ID, self.STAT, self.SCODE, self.DCODE, self.AREA, self.ZONE, self.OWNER,
             self.TCODE, self.BCODE, self.MBASE, self.RATEKV) = data[0]

            (self.PCODE, self.PSET, self.H, self.A, self.B, self.D, self.E,
             self.RA, self.XA, self.XM, self.R1,
             self.X1, self.R2, self.X2, self.X3,
             self.E1, self.SE1, self.E2, self.SE2,
             self.IA1, self.IA2) = data[1]

            self.XAMULT = data[2][0]
        else:
            logger.add_warning('Incorrect number of lines for Induction machine', str(len(data)))

    def get_raw_line(self, version):
        raise Exception('Induction machine not implemented for version ' + str(version))
