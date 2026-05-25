# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty


class RawMultiLineSection(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='From bus', min_value=1,
                     max_value=9999),
        PsseProperty(property_name='J', rawx_key='jbus', class_type=int, description='Bus to'),
        PsseProperty(property_name='ID', rawx_key='mslid', class_type=float, description='Multi section ID'),
        PsseProperty(property_name='MET', rawx_key='met', class_type=int, description='Metered flag'),
        PsseProperty(property_name=f'DUM{1}', rawx_key=f'dum{1}', class_type=int, description=f'Dummy bus {1}'),
        PsseProperty(property_name=f'DUM{2}', rawx_key=f'dum{2}', class_type=int, description=f'Dummy bus {2}'),
        PsseProperty(property_name=f'DUM{3}', rawx_key=f'dum{3}', class_type=int, description=f'Dummy bus {3}'),
        PsseProperty(property_name=f'DUM{4}', rawx_key=f'dum{4}', class_type=int, description=f'Dummy bus {4}'),
        PsseProperty(property_name=f'DUM{5}', rawx_key=f'dum{5}', class_type=int, description=f'Dummy bus {5}'),
        PsseProperty(property_name=f'DUM{6}', rawx_key=f'dum{6}', class_type=int, description=f'Dummy bus {6}'),
        PsseProperty(property_name=f'DUM{7}', rawx_key=f'dum{7}', class_type=int, description=f'Dummy bus {7}'),
        PsseProperty(property_name=f'DUM{8}', rawx_key=f'dum{8}', class_type=int, description=f'Dummy bus {8}'),
        PsseProperty(property_name=f'DUM{9}', rawx_key=f'dum{9}', class_type=int, description=f'Dummy bus {9}'),
    )

    def __init__(self):
        RawObject.__init__(self, "MultiLineSection")

        self.I: int = 0
        self.J: int = 0
        self.ID: str = ""
        self.MET: int = 1
        self.DUM1: int = 0
        self.DUM2: int = 0
        self.DUM3: int = 0
        self.DUM4: int = 0
        self.DUM5: int = 0
        self.DUM6: int = 0
        self.DUM7: int = 0
        self.DUM8: int = 0
        self.DUM9: int = 0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self) -> str:
        return str(self.I)

    def get_seed(self) -> str:
        return "_CA_{}".format(self.I)

