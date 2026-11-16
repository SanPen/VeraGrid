# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna GenericOperationCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.hydro_generation_cost import SiennaHydroGenerationCost
    from VeraGridEngine.IO.sienna.devices.core.common.renewable_generation_cost import SiennaRenewableGenerationCost
    from VeraGridEngine.IO.sienna.devices.core.common.thermal_generation_cost import SiennaThermalGenerationCost

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaGenericOperationCost(SiennaSchemaModel):
    """Expose every declared GenericOperationCost property through fixed slots."""

    __slots__ = ('value',)

    def __init__(self, value: SiennaThermalGenerationCost | SiennaRenewableGenerationCost | SiennaHydroGenerationCost) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.value: SiennaThermalGenerationCost | SiennaRenewableGenerationCost | SiennaHydroGenerationCost = value


def parse_sienna_generic_operation_cost(data: dict[str, Any]) -> SiennaGenericOperationCost:
    """Parse declared GenericOperationCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed GenericOperationCost object.
    """
    return SiennaGenericOperationCost(value=data.get('value', None))


def sienna_generic_operation_cost_to_json(value: SiennaGenericOperationCost) -> dict[str, Any]:
    """Write every GenericOperationCost slot to explicit schema property names.

    :param value: Typed GenericOperationCost object.
    :return: JSON object with declared schema properties.
    """
    return {'value': value.value}
