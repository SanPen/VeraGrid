# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, Tuple
from VeraGridEngine.IO.raw.devices.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.devices.psse_property import PsseProperty


class RawZone(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='izone', class_type=int, description='Zone number', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='ZONAME', rawx_key='zoname', class_type=str, description='Zone name', max_chars=12),
    )

    def __init__(self):
        RawObject.__init__(self, "Zone")

        self.I = -1
        self.ZONAME = ''

    def parse(self, data: List[List[str | int | float]], version: int, logger: Logger):
        """

        :param data:
        :param version:
        :param logger:
        """

        if version >= 29:
            if len(data[0]) == 2:

                self.I, self.ZONAME = data[0]

                self.ZONAME = self.ZONAME.replace("'", "").strip()
            elif len(data[0]) == 1:

                self.I = data[0]
            else:
                logger.add_warning('Undefined number of Zone attributes',
                                   value=len(data[0]), expected_value=2)
        else:
            logger.add_warning('Zones not defined for version', str(version))

    def get_raw_line(self, version):

        if version >= 29:
            return self.format_raw_line(["I", "ZONAME"])
        else:
            raise Exception('Zone not defined for version', str(version))

    def get_id(self) -> str:
        return str(self.I)

    def get_seed(self):
        return "_ZN_{0}".format(self.get_id())
