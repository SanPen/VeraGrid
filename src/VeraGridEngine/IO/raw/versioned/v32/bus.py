# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Any, List

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v31.bus import RawBusV31


class RawBusV32(RawBusV31):
    """PSSE v32 typed object inheriting v31."""

    def parse(self, data: List[List[Any]], version: int, logger: Logger):
        self.version = version
        (self.I, self.NAME, self.BASKV, self.IDE, self.AREA, self.ZONE,
         self.OWNER, self.VM, self.VA) = self.extend_or_curtail(data[0], 9)
        self.NAME = str(self.NAME)

    def get_raw_line(self, version: int):
        return self.format_raw_line(["I", "NAME", "BASKV", "IDE", "AREA", "ZONE",
                                     "OWNER", "VM", "VA"])
