# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.fixed_shunt import RawFixedShunt


class RawFixedShuntV29(RawFixedShunt):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        self.I, self.ID, self.STATUS, self.GL, self.BL = data[0]

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "STATUS", "GL", "BL"])
