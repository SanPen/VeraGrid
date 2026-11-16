# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DynamicTemplateCategory, VarPowerFlowReferenceType


def block_declares_physical_device_contract(block: Block) -> bool:
    """Return whether a template root declares a physical network boundary.

    A physical template must be bindable to one network object. Native and
    GUI-authored and imported templates express that through canonical
    power-flow references. Persisted legacy terminal metadata does not define
    runtime device identity.

    :param block: Reusable template root block.
    :return: Whether the block can represent one complete physical device.
    """
    if len(block.external_mapping) > 0:
        return True
    else:
        pass

    interface_var: Var
    interface_var_reference: VarPowerFlowReferenceType | None
    for interface_var in block.in_vars:
        interface_var_reference = interface_var.ref
        if (
                interface_var_reference is not None
                and interface_var_reference is not VarPowerFlowReferenceType.NOTHING
        ):
            return True
        else:
            pass
    for interface_var in block.out_vars:
        interface_var_reference = interface_var.ref
        if (
                interface_var_reference is not None
                and interface_var_reference is not VarPowerFlowReferenceType.NOTHING
        ):
            return True
        else:
            pass
    return False


def classify_dynamic_template_block(block: Block) -> DynamicTemplateCategory:
    """Classify a reusable model from its canonical typed contracts.

    Physical-device templates expose a network boundary. Every remaining
    template is an internal control or computational component.

    :param block: Reusable template root block.
    :return: Typed template category.
    """
    if block_declares_physical_device_contract(block=block):
        return DynamicTemplateCategory.DEVICE
    else:
        pass

    return DynamicTemplateCategory.COMPONENT
