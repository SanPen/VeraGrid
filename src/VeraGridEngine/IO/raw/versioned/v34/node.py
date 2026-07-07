# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v33.node import RawNodeV33


class RawNodeV34(RawNodeV33):
    """PSSE v34 typed object inheriting v33."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        if len(data[0]) == 6:
            self.NI, self.NAME, self.I, self.STATUS, self.VM, self.VA = data[0]
        elif len(data[0]) == 4:
            self.NI, self.NAME, self.I, self.STATUS = data[0]
            self.VM = 0.0
            self.VA = 0.0
        else:
            self.try_parse(values=data[0])

        self.NAME = self.NAME.replace("'", "").strip()

    def get_raw_line(self, version):
        return self.format_raw_line(["NI", "NAME", "I", "STATUS", "VM", "VA"])
