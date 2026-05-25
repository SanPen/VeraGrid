# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.inter_area import RawInterArea


class RawInterAreaV29(RawInterArea):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        if len(data[0]) == 5:
            self.I, self.ISW, self.PDES, self.PTOL, self.ARNAME = data[0]
        elif len(data[0]) == 4:
            self.I, self.ISW, self.ARNAME, self.PDES = data[0]
        else:
            logger.add_warning(f'Unrecognized number of inter-area arguments {len(data[0])}', str(version))
            self.try_parse(values=data[0])

        self.ARNAME = self.ARNAME.replace("'", "").strip()

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ISW", "PDES", "PTOL", "ARNAME"])
