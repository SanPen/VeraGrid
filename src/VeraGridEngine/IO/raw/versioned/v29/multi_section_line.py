# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.multi_section_line import RawMultiLineSection


class RawMultiLineSectionV29(RawMultiLineSection):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        var = [self.DUM1, self.DUM2, self.DUM3, self.DUM4, self.DUM5, self.DUM6, self.DUM7, self.DUM8, self.DUM9]
        (self.I, self.J, self.ID, self.MET, *var) = data[0]

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "J", "ID", "MET",
                                     "DUM1", "DUM2", "DUM3",
                                     "DUM4", "DUM5", "DUM6",
                                     "DUM7", "DUM8", "DUM9"])
