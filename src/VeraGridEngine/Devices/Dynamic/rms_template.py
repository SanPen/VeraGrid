# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple

from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType, SubObjectType
from VeraGridEngine.Devices.Parents.editable_device import GCProp


class RmsModelTemplate(PointerDeviceParent):
    """
    This class serves to give flexible access to either a template or a custom model
    """

    __slots__ = (
        '_block',
        '_device_type'
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp('block', units="p.u.", tpe=SubObjectType.DaeBlockType,
                      definition='DAE block', editable=False, display=False),
    )

    def __init__(self, idtag="", name: str = ""):
        super().__init__(name=name,
                         idtag=idtag,
                         code="",
                         device=None,
                         comment="",
                         device_type=DeviceType.RmsModelTemplateDevice)

        self.tpe: DeviceType = DeviceType.NoDevice
        self._block: Block = Block()


    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)  # bypass __init__
        memo[id(self)] = result

        # copy simple attributes
        result._tpe = self._tpe

        # deepcopy block safely
        result._block = self._block.deep_copy()

        return result

    @property
    def block(self):
        """

        :return:
        """
        return self._block

    @block.setter
    def block(self, obj: Block):
        self._block = obj