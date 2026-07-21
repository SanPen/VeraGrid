# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, Tuple
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_int, coerce_psse_str


class RawZone(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='izone', class_type=int, description='Zone number', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='ZONAME', rawx_key='zoname', class_type=str, description='Zone name', max_chars=12),
    )

    def __init__(self):
        RawObject.__init__(self, "Zone")

        self._I: int = -1
        self._ZONAME: str = ''

    def parse(self, data: List[List[str | int | float]], version: int, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return str(self.I)

    def get_seed(self):
        return "_ZN_{0}".format(self.get_id())

    @property
    def I(self) -> int:
        return self._I

    @I.setter
    def I(self, value: int | str | None) -> None:
        self._I = coerce_psse_int(value=value, current_value=self._I)

    @property
    def ZONAME(self) -> str:
        return self._ZONAME

    @ZONAME.setter
    def ZONAME(self, value: str | int | float | None) -> None:
        self._ZONAME = coerce_psse_str(value=value, current_value=self._ZONAME)
