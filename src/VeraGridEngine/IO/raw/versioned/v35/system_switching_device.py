# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.v34.system_switching_device import RawSystemSwitchingDeviceV34


class RawSystemSwitchingDeviceV35(RawSystemSwitchingDeviceV34):
    """PSSE v35 typed object inheriting v34."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        record = data[0]
        if len(record) == 21:
            (self.I, self.J, self.CKT, self.X, self.RATE1, self.RATE2, self.RATE3, self.RATE4, self.RATE5,
             self.RATE6, self.RATE7, self.RATE8, self.RATE9, self.RATE10, self.RATE11, self.RATE12,
             self.STATUS, self.NSTATUS, self.METERED, self.STYPE, self.NAME) = record
        else:
            logger.add_warning('Switch line length could not be identified :/', value=",".join(map(str, record)))
            self.try_parse(values=record)

        self.NAME = self.NAME.replace("'", "").strip()
