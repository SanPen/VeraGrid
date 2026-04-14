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
        '_device_type',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp('block', units="", tpe=SubObjectType.DaeBlockType,
                      definition='DAE block', editable=False, display=False),
        GCProp('tpe', units="", tpe=DeviceType,
               definition='Device type', editable=True, display=True),
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
        result = cls.__new__(cls)
        memo[id(self)] = result

        result._idtag = self._idtag
        result._name = self._name
        result._code = self._code
        result._rdfid = self._rdfid
        result.device_type = self.device_type
        result.comment = self.comment
        result.action = self.action
        result.selected_to_merge = self.selected_to_merge
        result.diff_changes = self.diff_changes
        result._EditableDevice__auto_update_enabled = self._EditableDevice__auto_update_enabled

        result._device_idtag = self._device_idtag
        result._tpe = self._tpe
        result._device_name = self._device_name
        result._device = self._device

        result._block = self._block

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