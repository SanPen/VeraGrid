# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna HydroStorageGenerationCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.hydro_generation_cost import SiennaHydroGenerationCost
    from VeraGridEngine.IO.sienna.devices.core.common.storage_cost import SiennaStorageCost

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaHydroStorageGenerationCost(SiennaSchemaModel):
    """Expose every declared HydroStorageGenerationCost property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: SiennaHydroGenerationCost | SiennaStorageCost) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: SiennaHydroGenerationCost | SiennaStorageCost = value


def parse_sienna_hydro_storage_generation_cost(data: dict[str, Any]) -> SiennaHydroStorageGenerationCost:
    """Parse declared HydroStorageGenerationCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed HydroStorageGenerationCost object.
    """
    return SiennaHydroStorageGenerationCost(value=data.get('value', None))


def sienna_hydro_storage_generation_cost_to_json(value: SiennaHydroStorageGenerationCost) -> dict[str, Any]:
    """Write every HydroStorageGenerationCost slot to explicit schema property names.

    :param value: Typed HydroStorageGenerationCost object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
