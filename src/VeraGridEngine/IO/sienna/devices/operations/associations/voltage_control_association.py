# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna VoltageControlAssociation schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_control_terminal import SiennaVoltageControlTerminal

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaVoltageControlAssociation(SiennaSchemaModel):
    """Expose every declared VoltageControlAssociation property through fixed slots."""

    __slots__ = ('control_id', 'entity_id', 'weight', 'terminal',)

    def __init__(self, control_id: int, entity_id: int, weight: float, terminal: SiennaVoltageControlTerminal) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.control_id: int = control_id
        self.entity_id: int = entity_id
        self.weight: float = weight
        self.terminal: SiennaVoltageControlTerminal = terminal


def parse_sienna_voltage_control_association(data: dict[str, Any]) -> SiennaVoltageControlAssociation:
    """Parse declared VoltageControlAssociation properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed VoltageControlAssociation object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_control_terminal import parse_sienna_voltage_control_terminal
    return SiennaVoltageControlAssociation(control_id=get_required_value(data, 'control_id', 'VoltageControlAssociation'), entity_id=get_required_value(data, 'entity_id', 'VoltageControlAssociation'), weight=data.get('weight', None), terminal=None if data.get('terminal', None) is None else parse_sienna_voltage_control_terminal(data.get('terminal', None)))

def sienna_voltage_control_association_to_json(value: SiennaVoltageControlAssociation) -> dict[str, Any]:
    """Write every VoltageControlAssociation slot to explicit schema property names.

    :param value: Typed VoltageControlAssociation object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.operations.common.voltage_control_terminal import sienna_voltage_control_terminal_to_json
    return {'control_id': value.control_id, 'entity_id': value.entity_id, 'weight': value.weight, 'terminal': None if value.terminal is None else sienna_voltage_control_terminal_to_json(value.terminal)}
