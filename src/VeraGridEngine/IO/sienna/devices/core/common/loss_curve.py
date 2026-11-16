# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna LossCurve schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.loss_value_curve import SiennaLossValueCurve
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import SiennaUnitSystem

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaLossCurve(SiennaSchemaModel):
    """Expose every declared LossCurve property through fixed slots."""

    __slots__ = ('power_units', 'value_curve',)

    def __init__(self, power_units: SiennaUnitSystem, value_curve: SiennaLossValueCurve) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.power_units: SiennaUnitSystem = power_units
        self.value_curve: SiennaLossValueCurve = value_curve


def parse_sienna_loss_curve(data: dict[str, Any]) -> SiennaLossCurve:
    """Parse declared LossCurve properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed LossCurve object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.loss_value_curve import parse_sienna_loss_value_curve
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import parse_sienna_unit_system
    return SiennaLossCurve(power_units=parse_sienna_unit_system(get_required_value(data, 'power_units', 'LossCurve')), value_curve=parse_sienna_loss_value_curve(get_required_value(data, 'value_curve', 'LossCurve')))

def sienna_loss_curve_to_json(value: SiennaLossCurve) -> dict[str, Any]:
    """Write every LossCurve slot to explicit schema property names.

    :param value: Typed LossCurve object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.loss_value_curve import sienna_loss_value_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.unit_system import sienna_unit_system_to_json
    return {'power_units': sienna_unit_system_to_json(value.power_units), 'value_curve': sienna_loss_value_curve_to_json(value.value_curve)}
