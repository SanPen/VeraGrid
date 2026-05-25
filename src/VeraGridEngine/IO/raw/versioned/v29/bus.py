# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Any, List

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.bus import RawBus


class RawBusV29(RawBus):
    """PSSE v29 typed object."""

    def parse(self, data: List[List[Any]], version: int, logger: Logger):
        self.version = version
        (self.I, self.NAME, self.BASKV, self.IDE, self.GL, self.BL,
         self.AREA, self.ZONE, self.VM, self.VA, self.OWNER) = self.extend_or_curtail(data[0], 11)
        self.NAME = str(self.NAME)

    def get_raw_line(self, version: int):
        return self.format_raw_line(["I", "NAME", "BASKV", "IDE", "GL", "BL",
                                     "AREA", "ZONE", "VM", "VA", "OWNER"])
