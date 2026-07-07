# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v29.vsc_dc_line import RawVscDCLineV29


class RawVscDCLineV30(RawVscDCLineV29):
    """PSSE v30 typed object inheriting v29."""

    def parse(self, data, version, logger: Logger):
        super().parse(data=data, version=version, logger=logger)

    def get_raw_line(self, version):
        return super().get_raw_line(version)
