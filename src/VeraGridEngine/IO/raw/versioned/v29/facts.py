# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.facts import RawFACTS


class RawFACTSV29(RawFACTS):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        (self.NAME, self.I, self.J, self.MODE, self.PDES, self.QDES, self.VSET, self.SHMX,
         self.TRMX, self.VTMN, self.VTMX, self.VSMX, self.IMX, self.LINX, self.RMPCT, self.OWNER,
         self.SET1, self.SET2, self.VSREF, self.REMOT, self.MNAME) = data[0]

    def get_raw_line(self, version):
        return self.format_raw_line(["NAME", "I", "J", "MODE", "PDES", "QDES", "VSET",
                                     "SHMX", "TRMX", "VTMN", "VTMX", "VSMX", "IMX", "LINX",
                                     "RMPCT", "OWNER", "SET1", "SET2", "VSREF", "REMOT",
                                     "MNAME"])
