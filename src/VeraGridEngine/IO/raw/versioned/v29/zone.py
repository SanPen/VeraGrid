# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.zone import RawZone


class RawZoneV29(RawZone):
    """PSSE v29 typed object."""

    def parse(self, data: List[List[str | int | float]], version: int, logger: Logger):
        self.version = version
        if len(data[0]) == 2:
            self.I, self.ZONAME = data[0]
            self.ZONAME = str(self.ZONAME).replace("'", "").strip()
        elif len(data[0]) == 1:
            self.I = data[0]
        else:
            logger.add_warning('Undefined number of Zone attributes', value=len(data[0]), expected_value=2)

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ZONAME"])
