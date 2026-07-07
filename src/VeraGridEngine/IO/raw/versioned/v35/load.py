# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v34.load import RawLoadV34


class RawLoadV35(RawLoadV34):
    """PSSE v35 typed object inheriting v34."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        record = data[0]

        if len(record) == 18:
            (self.I, self.ID, self.STATUS, self.AREA, self.ZONE, self.PL, self.QL,
             self.IP, self.IQ, self.YP, self.YQ, self.OWNER, self.SCALE, self.INTRPT,
             self.DGENP, self.DGENQ, self.DGENM, self.LOADTYPE) = record
        elif len(record) == 17:
            (self.I, self.ID, self.STATUS, self.AREA, self.ZONE, self.PL, self.QL,
             self.IP, self.IQ, self.YP, self.YQ, self.OWNER, self.SCALE, self.INTRPT,
             self.DGENP, self.DGENQ, self.LOADTYPE) = record
        elif len(record) == 13:
            (self.I, self.ID, self.STATUS, self.AREA, self.ZONE, self.PL, self.QL,
             self.IP, self.IQ, self.YP, self.YQ, self.OWNER, _comment) = record
        else:
            raise Exception(
                "PSSe 35 load data came with {} elements and 18, 17 or 13 were expected".format(len(record))
            )

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "STATUS", "AREA", "ZONE", "PL", "QL",
                                     "IP", "IQ", "YP", "YQ", "OWNER", "SCALE", "INTRPT",
                                     "DGENP", "DGENQ", "DGENM", "LOADTYPE"])
