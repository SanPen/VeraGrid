# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty
from VeraGridEngine.IO.raw.versioned.v35.fixed_shunt import RawFixedShuntV35


class RawFixedShuntV36(RawFixedShuntV35):
    """PSSE v36 typed object inheriting v35."""

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Fixed shunt name', max_chars=40),
    )

    def __init__(self):
        super().__init__()
        self.NAME = ""

    def parse(self, data, version, logger: Logger):
        self.version = version
        record = data[0]
        if len(record) >= 6:
            self.I, self.ID, self.STATUS, self.GL, self.BL, self.NAME = self.extend_or_curtail(record, 6)
        elif len(record) == 5:
            self.I, self.ID, self.STATUS, self.GL, self.BL = record
            self.NAME = ""
        else:
            logger.add_warning('Fixed shunt line length could not be identified :/', value=",".join(map(str, record)))
            self.try_parse(values=record)

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "STATUS", "GL", "BL", "NAME"])
