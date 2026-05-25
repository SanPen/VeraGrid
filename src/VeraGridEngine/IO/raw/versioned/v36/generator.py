# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty
from VeraGridEngine.IO.raw.versioned.v35.generator import RawGeneratorV35


class RawGeneratorV36(RawGeneratorV35):
    """PSSE v36 typed object inheriting v35."""

    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='DROOPNAME', rawx_key='droopname', class_type=str,
                     description='Voltage droop controller name', max_chars=40),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Machine name', max_chars=40),
    )

    def __init__(self):
        super().__init__()
        self.DROOPNAME = ""
        self.NAME = ""

    def parse(self, data, version, logger: Logger):
        self.version = version
        values = self.extend_or_curtail(data[0], 32)
        (self.I, self.ID, self.PG, self.QG, self.QT, self.QB, self.VS, self.IREG, self.NREG, self.MBASE,
         self.ZR, self.ZX, self.RT, self.XT, self.GTAP, self.STAT, self.RMPCT, self.PT, self.PB, self.BASLOD,
         self.O1, self.F1, self.O2, self.F2, self.O3, self.F3, self.O4, self.F4, self.WMOD, self.WPF,
         self.DROOPNAME, self.NAME) = values

    def get_raw_line(self, version):
        return self.format_raw_line(["I", "ID", "PG", "QG", "QT", "QB", "VS", "IREG", "NREG",
                                     "MBASE", "ZR", "ZX", "RT", "XT", "GTAP", "STAT",
                                     "RMPCT", "PT", "PB", "BASLOD", "O1", "F1", "O2", "F2", "O3", "F3",
                                     "O4", "F4", "WMOD", "WPF", "DROOPNAME", "NAME"])
