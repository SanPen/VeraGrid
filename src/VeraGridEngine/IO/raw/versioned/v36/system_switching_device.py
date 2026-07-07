# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty
from VeraGridEngine.IO.raw.versioned.v35.system_switching_device import RawSystemSwitchingDeviceV35


class RawSystemSwitchingDeviceV36(RawSystemSwitchingDeviceV35):
    """PSSE v36 typed object inheriting v35."""

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='RSETNAM', rawx_key='rsetnam', class_type=str,
                     description='Switching device rating set name', max_chars=40),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str,
                     description='System switching device name', max_chars=40),
    )

    def __init__(self):
        super().__init__()
        self.RSETNAM = ""
        self.NAME = ""

    def parse(self, data, version, logger: Logger):
        self.version = version
        record = data[0]
        if len(record) == 10:
            (self.I, self.J, self.CKT, self.X, self.RSETNAM, self.STATUS,
             self.NSTATUS, self.METERED, self.STYPE, self.NAME) = record
        else:
            logger.add_warning('Switch line length could not be identified :/', value=",".join(map(str, record)))
            self.try_parse(values=record)

        self.RSETNAM = str(self.RSETNAM).replace("'", "").strip()
        self.NAME = str(self.NAME).replace("'", "").strip()

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "J", "CKT", "X", "RSETNAM", "STATUS",
                                     "NSTATUS", "METERED", "STYPE", "NAME"])
