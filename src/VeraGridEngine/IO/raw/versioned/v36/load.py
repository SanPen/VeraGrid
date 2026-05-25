# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty
from VeraGridEngine.IO.raw.versioned.v35.load import RawLoadV35


class RawLoadV36(RawLoadV35):
    """PSSE v36 typed object inheriting v35."""

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Load name', max_chars=40),
    )

    def __init__(self):
        super().__init__()
        self.NAME = ""

    def parse(self, data, version, logger: Logger):
        self.version = version
        record = data[0]

        if len(record) >= 19:
            (self.I, self.ID, self.STATUS, self.AREA, self.ZONE, self.PL, self.QL,
             self.IP, self.IQ, self.YP, self.YQ, self.OWNER, self.SCALE, self.INTRPT,
             self.DGENP, self.DGENQ, self.DGENM, self.LOADTYPE, self.NAME) = self.extend_or_curtail(record, 19)
        elif len(record) == 18:
            super().parse(data, version, logger)
            self.NAME = ""
        else:
            raise Exception(
                "PSSe 36 load data came with {} elements and 19 or 18 were expected".format(len(record))
            )

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "STATUS", "AREA", "ZONE", "PL", "QL",
                                     "IP", "IQ", "YP", "YQ", "OWNER", "SCALE", "INTRPT",
                                     "DGENP", "DGENQ", "DGENM", "LOADTYPE", "NAME"])
