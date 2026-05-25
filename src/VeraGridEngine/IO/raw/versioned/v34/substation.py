# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v33.substation import RawSubstationV33


class RawSubstationV34(RawSubstationV33):
    """PSSE v34 typed object inheriting v33."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        if len(data[0]) == 5:
            self.IS, self.NAME, self.LATI, self.LONG, self.SGR = data[0]
        elif len(data[0]) == 4:
            self.IS, self.NAME, self.LATI, self.LONG = data[0]
        else:
            logger.add_warning('Substation line length could not be identified :/', value=",".join(map(str, data[0])))
            self.try_parse(values=data[0])

    def get_raw_line(self, version):
        return self.format_raw_line(["IS", "NAME", "LATI", "LONG", "SGR"])
