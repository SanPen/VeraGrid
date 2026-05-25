# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.area import RawArea


class RawAreaV29(RawArea):
    """PSSE v29 typed object."""

    def parse(self, data: List[List[str | int | float]], version: int, logger: Logger):
        self.version = version
        self.I = -1
        self.ARNAME = ''

        if len(data[0]) == 5:
            self.I, self.ISW, self.PDES, self.PTOL, self.ARNAME = data[0]
        else:
            logger.add_warning('Undefined number of Area attributes', value=len(data[0]), expected_value=5)
            self.try_parse(values=data[0])

        self.ARNAME = str(self.ARNAME).replace("'", "").strip()

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ISW", "PDES", "PTOL", "ARNAME"])
