# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Any, List

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v32.bus import RawBusV32


class RawBusV33(RawBusV32):
    """PSSE v33 typed object inheriting v32."""

    def parse(self, data: List[List[Any]], version: int, logger: Logger):
        self.version = version
        (self.I, self.NAME, self.BASKV, self.IDE, self.AREA, self.ZONE,
         self.OWNER, self.VM, self.VA, self.NVHI, self.NVLO, self.EVHI,
         self.EVLO) = self.extend_or_curtail(data[0], 13)
        self.NAME = str(self.NAME)

    def get_raw_line(self, version: int):
        return self.format_raw_line(["I", "NAME", "BASKV", "IDE", "AREA", "ZONE",
                                     "OWNER", "VM", "VA", "NVHI", "NVLO", "EVHI", "EVLO"])
