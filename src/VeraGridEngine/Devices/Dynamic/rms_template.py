# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Dict
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const
from VeraGridEngine.enumerations import DeviceType, SubObjectType


class RmsModelTemplate(PointerDeviceParent):
    """
    This class serves to give flexible access to either a template or a custom model
    """

    __slots__ = (
        '_block',
        '_device_type',
        '_init_values')

    def __init__(self, idtag="", name: str = ""):
        super().__init__(name=name,
                         idtag=idtag,
                         code="",
                         device=None,
                         comment="",
                         device_type=DeviceType.RmsModelTemplateDevice)

        self._block: Block = Block()
        self._init_values: Dict[Var, Const] = dict()

        self.register('block', units="p.u.", tpe=SubObjectType.DaeBlockType,
                      definition='DAE block', editable=False, display=False)

    @property
    def block(self):
        """

        :return:
        """
        return self._block

    @block.setter
    def block(self, obj: Block):
        self._block = obj

    @property
    def init_values(self):
        """

        :return:
        """
        return self._init_values

    @init_values.setter
    def init_values(self, obj: Dict[Var, Const]):
        self._init_values = obj
