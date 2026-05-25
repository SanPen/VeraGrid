# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.owner import RawOwner


class RawOwnerV29(RawOwner):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        if len(data[0]) == 1:
            self.I = data[0]
        elif len(data[0]) == 2:
            self.I, self.OWNAME = data[0]
        else:
            self.try_parse(values=data[0])

        self.OWNAME = self.OWNAME.replace("'", "").strip()

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "OWNAME"])
