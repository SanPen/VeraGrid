# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CombinedCycleBlock schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.operations.common.combined_cycle_configuration import SiennaCombinedCycleConfiguration

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCombinedCycleBlock(SiennaSchemaModel):
    """Expose every declared CombinedCycleBlock property through fixed slots."""

    __slots__ = ('id', 'name', 'configuration', 'heat_recovery_to_steam_factor',)

    def __init__(self, id: int, name: str, configuration: SiennaCombinedCycleConfiguration, heat_recovery_to_steam_factor: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.name: str = name
        self.configuration: SiennaCombinedCycleConfiguration = configuration
        self.heat_recovery_to_steam_factor: float = heat_recovery_to_steam_factor


def parse_sienna_combined_cycle_block(data: dict[str, Any]) -> SiennaCombinedCycleBlock:
    """Parse declared CombinedCycleBlock properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed CombinedCycleBlock object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.operations.common.combined_cycle_configuration import parse_sienna_combined_cycle_configuration
    return SiennaCombinedCycleBlock(id=get_required_value(data, 'id', 'CombinedCycleBlock'), name=get_required_value(data, 'name', 'CombinedCycleBlock'), configuration=parse_sienna_combined_cycle_configuration(get_required_value(data, 'configuration', 'CombinedCycleBlock')), heat_recovery_to_steam_factor=data.get('heat_recovery_to_steam_factor', None))

def sienna_combined_cycle_block_to_json(value: SiennaCombinedCycleBlock) -> dict[str, Any]:
    """Write every CombinedCycleBlock slot to explicit schema property names.

    :param value: Typed CombinedCycleBlock object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.operations.common.combined_cycle_configuration import sienna_combined_cycle_configuration_to_json
    return {'id': value.id, 'name': value.name, 'configuration': sienna_combined_cycle_configuration_to_json(value.configuration), 'heat_recovery_to_steam_factor': value.heat_recovery_to_steam_factor}
