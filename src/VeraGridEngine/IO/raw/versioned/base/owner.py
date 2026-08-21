# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_int, coerce_psse_str


class RawOwner(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='iowner', class_type=int, description='Owner number', min_value=1,
                     max_value=9999, max_chars=4),
        PsseProperty(property_name='OWNAME', rawx_key='owname', class_type=str, description='Owner name', max_chars=12),
    )

    def __init__(self):
        RawObject.__init__(self, "Owner")

        self._I: int = -1
        self._OWNAME: str = ''

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return str(self.I)

    def get_seed(self):
        return "_OW_{0}".format(self.get_id())

    @property
    def I(self) -> int:
        return self._I

    @I.setter
    def I(self, value: int | str | None) -> None:
        self._I = coerce_psse_int(value=value, current_value=self._I)

    @property
    def OWNAME(self) -> str:
        return self._OWNAME

    @OWNAME.setter
    def OWNAME(self, value: str | int | float | None) -> None:
        self._OWNAME = coerce_psse_str(value=value, current_value=self._OWNAME)
