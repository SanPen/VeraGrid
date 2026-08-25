# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import copy
from typing import Any, Callable, Dict, Tuple
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Utils.Symbolic.block import Block, normalize_event_parameter_initialization
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const
from VeraGridEngine.enumerations import DeviceType, SubObjectType
from VeraGridEngine.Devices.Parents.editable_device import GCProp


class EmtLazyTemplateBuilder:
    """
    Typed wrapper used to materialize one EMT template lazily.
    """

    __slots__ = ("_builder", "_kwargs")

    def __init__(self, builder: Callable[..., "EmtModelTemplate"], kwargs: Dict[str, Any]) -> None:
        """
        Build the lazy template wrapper.

        :param builder: EMT template builder function.
        :param kwargs: Explicit builder keyword arguments.
        :return: None.
        """
        self._builder = builder
        self._kwargs = dict(kwargs)

    def build(self) -> "EmtModelTemplate":
        """
        Materialize the wrapped EMT template.

        :return: Materialized EMT template.
        """
        return self._builder(**self._kwargs)


class EmtModelTemplate(PointerDeviceParent):
    """
    This class serves to give flexible access to either a template or a custom model
    """

    __slots__ = (
        '_block',
        '_device_type',
        '_lazy_builder',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='block',
            units="",
            tpe=SubObjectType.DaeBlockType,
            definition='DAE block',
            editable=False,
            display=False,
        ),
        GCProp(
            prop_name='tpe',
            units="",
            tpe=DeviceType,
            definition='Device type',
            editable=True,
            display=True,
        ),
    )

    def __init__(self, idtag="", name: str = ""):
        super().__init__(name=name,
                         idtag=idtag,
                         code="",
                         device=None,
                         comment="",
                         device_type=DeviceType.EmtModelTemplateDevice)

        self._tpe: DeviceType = DeviceType.NoDevice
        self._block: Block = Block()
        self._lazy_builder: EmtLazyTemplateBuilder | None = None


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
        result.diff_changes = copy.deepcopy(self.diff_changes, memo)
        result._EditableDevice__auto_update_enabled = self._EditableDevice__auto_update_enabled

        result._device_idtag = self._device_idtag
        result._tpe = self._tpe
        result._device_name = self._device_name
        result._device = self._device

        result._block = copy.deepcopy(self._block, memo)
        result._lazy_builder = copy.deepcopy(self._lazy_builder, memo)

        return result

    @property
    def block(self) -> Block:
        """Materialize and return the normalized EMT symbolic block.

        :return: EMT symbolic block using one initialization source per event parameter.
        """
        if self._block.empty() and self._lazy_builder is not None:
            built_template: EmtModelTemplate = self._lazy_builder.build()
            self._block = built_template.block
            self._lazy_builder = None
        else:
            pass

        normalize_event_parameter_initialization(block=self._block)
        return self._block

    @block.setter
    def block(self, obj: Block) -> None:
        """Replace the EMT block and normalize legacy event initialization.

        :param obj: Complete symbolic block assigned to the template.
        :return: None.
        """
        self._lazy_builder = None
        self._block = obj
        normalize_event_parameter_initialization(block=self._block)

    def set_lazy_builder(self, builder: EmtLazyTemplateBuilder) -> None:
        """
        Register one lazy EMT template builder.

        :param builder: Lazy builder wrapper.
        :return: None.
        """
        self._lazy_builder = builder
